"""Tests for WhatsApp Voice Telephony Adapter & TwiML Endpoints."""

import unittest
from fastapi.testclient import TestClient

from src.voice.app import app
from src.voice.whatsapp_adapter import (
    WhatsAppConfig,
    generate_twiml_stream,
)


class TestWhatsAppTelephony(unittest.TestCase):
    """Test WhatsApp configuration, TwiML generation, and API endpoints."""

    def setUp(self):
        self.client = TestClient(app)

    def test_generate_twiml_stream(self):
        url = "wss://test.example.com/api/whatsapp/media-stream"
        params = {"caller": "Philipp", "channel": "whatsapp_voice"}
        xml = generate_twiml_stream(url, params)

        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', xml)
        self.assertIn('<Response>', xml)
        self.assertIn('<Connect>', xml)
        self.assertIn(f'<Stream url="{url}">', xml)
        self.assertIn('<Parameter name="caller" value="Philipp" />', xml)
        self.assertIn('<Parameter name="channel" value="whatsapp_voice" />', xml)

    def test_whatsapp_config_defaults(self):
        cfg = WhatsAppConfig.from_env()
        self.assertIsInstance(cfg.enabled, bool)
        self.assertIn("whatsapp:", cfg.twilio_whatsapp_number)
        self.assertIn("whatsapp:", cfg.lead_whatsapp_number)
        self.assertTrue(cfg.ws_stream_url.endswith("/api/whatsapp/media-stream"))

    def test_incoming_webhook_endpoint(self):
        form_data = {
            "CallSid": "CA1234567890abcdef",
            "From": "whatsapp:+41791234567",
            "To": "whatsapp:+14155238886",
        }
        res = self.client.post("/api/whatsapp/incoming", data=form_data)
        self.assertEqual(res.status_code, 200)
        self.assertIn("xml", res.headers.get("content-type", ""))
        self.assertIn("<Response>", res.text)
        self.assertIn("<Stream", res.text)
        self.assertIn("whatsapp_voice", res.text)

    def test_status_callback_endpoint(self):
        status_data = {
            "CallSid": "CA1234567890abcdef",
            "CallStatus": "in-progress",
            "CallDuration": "45",
        }
        res = self.client.post("/api/whatsapp/status", data=status_data)
        self.assertEqual(res.status_code, 200)
        json_data = res.json()
        self.assertEqual(json_data.get("status"), "recorded")
        self.assertEqual(json_data.get("call_status"), "in-progress")

    def test_config_endpoint(self):
        res = self.client.get("/api/whatsapp/config")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("enabled", data)
        self.assertIn("has_credentials", data)
        self.assertIn("twilio_whatsapp_number", data)
        self.assertIn("lead_whatsapp_number_masked", data)
        self.assertIn("ws_stream_url", data)

    def test_outbound_call_simulation(self):
        # Without Twilio credentials, triggers safe simulation
        res = self.client.post("/api/whatsapp/call", json={})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("mode"), "simulation")
        self.assertEqual(data.get("status"), "queued")
        self.assertIn("whatsapp:", data.get("to", ""))


if __name__ == "__main__":
    unittest.main()
