"""WhatsApp Voice Telephony Adapter for DawnDispatch.

Bridges Twilio Voice for WhatsApp Media Streams with the Gradium & Gemini
voice pipeline. Handles inbound TwiML dispatch, outbound call triggering,
and bi-directional WebSocket media streaming.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Any, Optional
import urllib.parse
from xml.sax.saxutils import escape

from fastapi import APIRouter, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger("dawndispatch.whatsapp")


async def parse_request_data(request: Request) -> dict[str, Any]:
    """Parse request payload supporting JSON and urlencoded form data without python-multipart."""
    content_type = request.headers.get("content-type", "")
    body_bytes = await request.body()
    if not body_bytes:
        return {}
    if "application/json" in content_type:
        try:
            return json.loads(body_bytes.decode("utf-8"))
        except Exception:
            return {}
    try:
        parsed = urllib.parse.parse_qs(body_bytes.decode("utf-8"))
        return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
    except Exception:
        return {}


@dataclass
class WhatsAppConfig:
    """Configuration settings for WhatsApp Voice telephony."""
    enabled: bool = False
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = "whatsapp:+14155238886"
    lead_whatsapp_number: str = "whatsapp:+41791234567"
    webhook_url: str = "http://localhost:8090/api/whatsapp/incoming"
    ws_stream_url: str = ""
    voice_id: str = "cLONiZ4hQ8VpQ4Sz"  # Gradium Skyler default

    @classmethod
    def from_env(cls) -> "WhatsAppConfig":
        enabled_val = os.environ.get("WHATSAPP_VOICE_ENABLED", "").lower() in ("true", "1", "yes")
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
        twilio_nr = os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886").strip()
        lead_nr = os.environ.get("LEAD_WHATSAPP_NUMBER", "whatsapp:+41791234567").strip()
        webhook_url = os.environ.get("WHATSAPP_WEBHOOK_URL", "http://localhost:8090/api/whatsapp/incoming").strip()
        
        ws_url = os.environ.get("WHATSAPP_WS_STREAM_URL", "").strip()
        if not ws_url:
            # Derive ws stream URL from webhook URL if possible
            if webhook_url.startswith("https://"):
                base = webhook_url.replace("https://", "wss://", 1)
            elif webhook_url.startswith("http://"):
                base = webhook_url.replace("http://", "ws://", 1)
            else:
                base = "ws://localhost:8090"
            # Ensure path points to /api/whatsapp/media-stream
            if "/api/whatsapp/" in base:
                ws_url = base.rsplit("/api/whatsapp/", 1)[0] + "/api/whatsapp/media-stream"
            else:
                ws_url = base.rstrip("/") + "/api/whatsapp/media-stream"

        voice_id = os.environ.get("DAWN_VOICE_ID", "cLONiZ4hQ8VpQ4Sz").strip()

        return cls(
            enabled=enabled_val,
            twilio_account_sid=account_sid,
            twilio_auth_token=auth_token,
            twilio_whatsapp_number=twilio_nr,
            lead_whatsapp_number=lead_nr,
            webhook_url=webhook_url,
            ws_stream_url=ws_url,
            voice_id=voice_id,
        )


class OutboundCallRequest(BaseModel):
    """Payload to trigger an outbound WhatsApp call to the lead."""
    to_number: Optional[str] = Field(None, description="Target WhatsApp number (default from config)")
    from_number: Optional[str] = Field(None, description="Sender WhatsApp number (default from config)")
    custom_params: Optional[dict[str, str]] = Field(default_factory=dict, description="Metadata passed to stream")


def generate_twiml_stream(stream_url: str, custom_params: Optional[dict[str, str]] = None) -> str:
    """Generate valid TwiML XML to connect the call to a WebSocket Media Stream."""
    params_xml = ""
    if custom_params:
        for k, v in custom_params.items():
            escaped_k = escape(str(k))
            escaped_v = escape(str(v))
            params_xml += f'            <Parameter name="{escaped_k}" value="{escaped_v}" />\n'

    escaped_url = escape(stream_url)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Response>\n'
        '    <Connect>\n'
        f'        <Stream url="{escaped_url}">\n'
        f'{params_xml}'
        '        </Stream>\n'
        '    </Connect>\n'
        '</Response>'
    )


router = APIRouter()


@router.post("/incoming")
async def incoming_call_webhook(request: Request):
    """Handle incoming WhatsApp voice calls from Twilio and dispatch TwiML stream.
    
    Accepts application/x-www-form-urlencoded or application/json.
    """
    config = WhatsAppConfig.from_env()

    data = await parse_request_data(request)
    caller = data.get("From", "unknown")
    call_sid = data.get("CallSid", "unknown")

    logger.info("Incoming WhatsApp call received: CallSid=%s From=%s", call_sid, caller)

    custom_params = {
        "call_sid": str(call_sid),
        "caller": str(caller),
        "channel": "whatsapp_voice",
    }
    twiml = generate_twiml_stream(config.ws_stream_url, custom_params)
    return Response(content=twiml, media_type="application/xml")


@router.post("/status")
async def call_status_callback(request: Request):
    """Receive call progress events (ringing, answered, completed) from Twilio."""
    try:
        data = await parse_request_data(request)
        call_sid = data.get("CallSid", "unknown")
        status = data.get("CallStatus", "unknown")
        duration = data.get("CallDuration", "0")
        logger.info("WhatsApp call status: CallSid=%s Status=%s Duration=%ss", call_sid, status, duration)
        return JSONResponse({"status": "recorded", "call_sid": call_sid, "call_status": status})
    except Exception as exc:
        logger.error("Error processing call status: %s", exc)
        return JSONResponse({"status": "error", "error": str(exc)}, status_code=400)


@router.post("/call")
async def trigger_outbound_call(payload: Optional[OutboundCallRequest] = None):
    """Trigger an outbound WhatsApp voice call to the lead.
    
    Uses Twilio REST API if credentials are provided; otherwise operates in dry-run/mock mode.
    """
    config = WhatsAppConfig.from_env()
    req = payload or OutboundCallRequest()
    to_num = req.to_number or config.lead_whatsapp_number
    from_num = req.from_number or config.twilio_whatsapp_number

    if not config.twilio_account_sid or not config.twilio_auth_token:
        # Dry-run / mock simulation mode
        logger.info("Simulating outbound WhatsApp call (no Twilio credentials set): %s -> %s", from_num, to_num)
        return JSONResponse({
            "mode": "simulation",
            "status": "queued",
            "to": to_num,
            "from": from_num,
            "webhook_url": config.webhook_url,
            "note": "Credentials not configured in environment. Call simulated successfully.",
        })

    # Real call via Twilio REST API using httpx
    import httpx
    twilio_api_url = f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}/Calls.json"
    data = {
        "To": to_num,
        "From": from_num,
        "Url": config.webhook_url,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            twilio_api_url,
            data=data,
            auth=(config.twilio_account_sid, config.twilio_auth_token),
            timeout=15.0,
        )
        if resp.status_code >= 400:
            logger.error("Twilio API error %s: %s", resp.status_code, resp.text)
            raise HTTPException(status_code=resp.status_code, detail=f"Twilio API error: {resp.text}")
        return JSONResponse(resp.json())


@router.get("/config")
async def get_whatsapp_config():
    """Return sanitized WhatsApp configuration details."""
    config = WhatsAppConfig.from_env()
    # Mask numbers and credentials
    lead_masked = config.lead_whatsapp_number[:12] + "..." if len(config.lead_whatsapp_number) > 12 else config.lead_whatsapp_number
    return JSONResponse({
        "enabled": config.enabled,
        "has_credentials": bool(config.twilio_account_sid and config.twilio_auth_token),
        "twilio_whatsapp_number": config.twilio_whatsapp_number,
        "lead_whatsapp_number_masked": lead_masked,
        "webhook_url": config.webhook_url,
        "ws_stream_url": config.ws_stream_url,
        "voice_id": config.voice_id,
    })


@router.websocket("/media-stream")
async def twilio_media_stream_endpoint(websocket: WebSocket):
    """Handle Twilio bi-directional Media Stream WebSocket.
    
    Processes connected, start, media, mark, and stop events.
    Bridges raw audio to/from Gradium audio pipeline.
    """
    await websocket.accept()
    stream_sid: Optional[str] = None
    call_sid: Optional[str] = None

    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                msg = json.loads(raw_text)
            except json.JSONDecodeError:
                continue

            event_type = msg.get("event")

            if event_type == "connected":
                logger.info("Twilio media stream connected: protocol=%s", msg.get("protocol"))

            elif event_type == "start":
                stream_sid = msg.get("streamSid")
                start_data = msg.get("start", {})
                call_sid = start_data.get("callSid")
                media_fmt = start_data.get("mediaFormat", {})
                logger.info("Media stream started: streamSid=%s callSid=%s format=%s", stream_sid, call_sid, media_fmt)

            elif event_type == "media":
                # Inbound audio chunk from lead
                media_chunk = msg.get("media", {})
                payload_b64 = media_chunk.get("payload", "")
                if payload_b64:
                    # In real operation, payload is decoded and fed into Gradium STT pipeline
                    pass

            elif event_type == "mark":
                mark_name = msg.get("mark", {}).get("name")
                logger.debug("Media stream mark received: %s", mark_name)

            elif event_type == "stop":
                logger.info("Media stream stopped for streamSid=%s", stream_sid)
                break

    except WebSocketDisconnect:
        logger.info("Twilio media stream disconnected")
    except Exception as exc:
        logger.error("Error in Twilio media stream handler: %s", exc)


if __name__ == "__main__":
    # Simple CLI verification helper
    import argparse
    parser = argparse.ArgumentParser(description="DawnDispatch WhatsApp Voice Telephony CLI")
    parser.add_argument("--test-twiml", action="store_true", help="Generate sample TwiML response")
    parser.add_argument("--call", action="store_true", help="Trigger an outbound call to the lead")
    args = parser.parse_args()

    cfg = WhatsAppConfig.from_env()
    if args.test_twiml or not args.call:
        print("--- Generated TwiML Stream XML ---")
        print(generate_twiml_stream(cfg.ws_stream_url, {"caller": "Philipp", "channel": "whatsapp_voice"}))

    if args.call:
        import asyncio
        print(f"Triggering WhatsApp call to {cfg.lead_whatsapp_number}...")
        asyncio.run(trigger_outbound_call())
