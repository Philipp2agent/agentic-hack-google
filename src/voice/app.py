"""FastAPI Voice Server for DawnDispatch.

Provides the mobile incoming call screen (/call), WebSocket audio streaming
via Gradium & gradbot, quick-fire agenda dispatching, and transcript persistence.
"""

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.core.models import load_agenda
from src.voice.gradium_client import (
    DEFAULT_VOICE_ID,
    build_system_instructions,
    save_call_transcript,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
PROJECT_ROOT = BASE_DIR.parent.parent

app = FastAPI(title="DawnDispatch Voice Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount bundled js-audio from gradbot if present
try:
    import gradbot
    import gradbot.routes
    if hasattr(gradbot.routes, "_JS_AUDIO_DIR") and Path(gradbot.routes._JS_AUDIO_DIR).exists():
        app.mount("/static/js", StaticFiles(directory=gradbot.routes._JS_AUDIO_DIR), name="bundled_js")
except Exception:
    pass

# Mount voice static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="voice_static")

# Mount assets directory if available
assets_dir = PROJECT_ROOT / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/")
async def root():
    """Redirect home to mobile call screen."""
    return RedirectResponse(url="/call")


@app.get("/call")
async def call_screen():
    """Serve the mobile call simulation interface."""
    call_html = STATIC_DIR / "call.html"
    if not call_html.exists():
        return JSONResponse({"error": "call.html not found"}, status_code=404)
    return FileResponse(call_html)


@app.get("/api/agenda")
async def get_agenda():
    """Return synthesized overnight agenda items for the call."""
    agenda_file = PROJECT_ROOT / "src" / "data" / "agenda.json"
    items = load_agenda(agenda_file)
    return JSONResponse([it.model_dump() for it in items])


@app.get("/api/transcript")
async def get_transcript():
    """Return the latest call transcript."""
    t_file = PROJECT_ROOT / "src" / "data" / "transcript.json"
    if not t_file.exists():
        return JSONResponse({"status": "NO_CALL_RECORDED", "turns": []})
    with open(t_file, "r", encoding="utf-8") as f:
        return JSONResponse(json.load(f))


@app.post("/api/end_call")
async def end_call(payload: dict[str, Any]):
    """Persist the call transcript, update decisions, and sync dashboard actions."""
    agenda_path = PROJECT_ROOT / "src" / "data" / "agenda.json"
    decisions_path = PROJECT_ROOT / "src" / "data" / "decisions.json"
    actions_path = PROJECT_ROOT / "src" / "data" / "actions.json"
    transcript_path = PROJECT_ROOT / "src" / "data" / "transcript.json"

    saved = save_call_transcript(
        transcript_payload=payload,
        output_path=transcript_path,
        decisions_path=decisions_path,
        actions_path=actions_path,
        agenda_path=agenda_path,
    )
    return JSONResponse({"success": True, "transcript": saved})


@app.websocket("/ws/call")
async def websocket_call_endpoint(websocket: WebSocket):
    """WebSocket endpoint handling rapid quick-fire voice/text interaction."""
    await websocket.accept()

    agenda_path = PROJECT_ROOT / "src" / "data" / "agenda.json"
    agenda_items = load_agenda(agenda_path)
    agenda_dicts = [it.model_dump() for it in agenda_items]

    # Send initial greeting
    greeting = "Good morning Philipp. Swarm overnight triage ready. How much time do you have?"
    await websocket.send_json({
        "type": "agent_speech",
        "phase": "greeting",
        "text": greeting,
        "expect": "duration",
    })

    current_q_idx = -1
    turns = [{"speaker": "agent", "text": greeting, "timestamp": "00:02"}]
    decisions: list[dict[str, Any]] = []

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "user_response":
                user_text = data.get("text", "").strip()
                turns.append({"speaker": "user", "text": user_text, "timestamp": data.get("timestamp", "")})

                if current_q_idx == -1:
                    # User specified time, e.g., "60 seconds" -> start Quick Fire
                    current_q_idx = 0
                    if agenda_dicts:
                        first_q = agenda_dicts[0]
                        prompt_text = f"Rapid fire. 1: {first_q['question_for_lead']} Yes or no?"
                        turns.append({"speaker": "agent", "text": prompt_text, "timestamp": "00:10"})
                        await websocket.send_json({
                            "type": "agent_speech",
                            "phase": "quick_fire",
                            "item_id": first_q["item_id"],
                            "index": 1,
                            "total": len(agenda_dicts),
                            "text": prompt_text,
                            "question": first_q["question_for_lead"],
                            "is_irreversible": first_q.get("is_irreversible", False),
                        })
                    else:
                        conclude = "Captured. Knowledge graph updated. See you at your desk."
                        await websocket.send_json({"type": "call_ended", "text": conclude})
                        break
                else:
                    # Evaluate decision for question current_q_idx
                    answered_item = agenda_dicts[current_q_idx]
                    lower_text = user_text.lower()

                    if any(w in lower_text for w in ("no", "reject", "deny")):
                        dec_type = "REJECT"
                    elif any(w in lower_text for w in ("hold", "wait", "checkpoint")):
                        dec_type = "HOLD"
                    else:
                        dec_type = "APPROVE"

                    decisions.append({
                        "item_id": answered_item["item_id"],
                        "decision_type": dec_type,
                        "voice_notes": f"Decided '{user_text}' during quick-fire call",
                    })

                    current_q_idx += 1
                    if current_q_idx < len(agenda_dicts):
                        next_q = agenda_dicts[current_q_idx]
                        prompt_text = f"Recorded. {current_q_idx + 1}: {next_q['question_for_lead']} Yes or no?"
                        turns.append({"speaker": "agent", "text": prompt_text, "timestamp": "00:25"})
                        await websocket.send_json({
                            "type": "agent_speech",
                            "phase": "quick_fire",
                            "item_id": next_q["item_id"],
                            "index": current_q_idx + 1,
                            "total": len(agenda_dicts),
                            "text": prompt_text,
                            "question": next_q["question_for_lead"],
                            "is_irreversible": next_q.get("is_irreversible", False),
                        })
                    else:
                        conclude = "Captured. Knowledge graph updated. See you at your desk."
                        turns.append({"speaker": "agent", "text": conclude, "timestamp": "00:54"})

                        # Automatically trigger transcript and dashboard sync
                        save_call_transcript(
                            transcript_payload={
                                "turns": turns,
                                "decisions_captured": decisions,
                                "duration_seconds": 58,
                            },
                            output_path=PROJECT_ROOT / "src" / "data" / "transcript.json",
                            decisions_path=PROJECT_ROOT / "src" / "data" / "decisions.json",
                            actions_path=PROJECT_ROOT / "src" / "data" / "actions.json",
                            agenda_path=agenda_path,
                        )

                        await websocket.send_json({
                            "type": "call_ended",
                            "text": conclude,
                            "decisions": decisions,
                        })
                        break

            elif msg_type == "hangup":
                save_call_transcript(
                    transcript_payload={
                        "turns": turns,
                        "decisions_captured": decisions,
                        "duration_seconds": 35,
                    },
                    output_path=PROJECT_ROOT / "src" / "data" / "transcript.json",
                    decisions_path=PROJECT_ROOT / "src" / "data" / "decisions.json",
                    actions_path=PROJECT_ROOT / "src" / "data" / "actions.json",
                    agenda_path=agenda_path,
                )
                await websocket.send_json({"type": "call_ended", "reason": "user_hangup"})
                break

    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("VOICE_PORT", 8090))
    print(f"Starting DawnDispatch Voice Service on http://0.0.0.0:{port}/call")
    uvicorn.run(app, host="0.0.0.0", port=port)
