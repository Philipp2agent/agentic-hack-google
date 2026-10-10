"""Unit and integration tests for DawnDispatch Voice Pipeline & Call Screen."""

import json
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from src.voice.app import app
from src.voice.gradium_client import (
    build_system_instructions,
    extract_decisions_from_turns,
    save_call_transcript,
)
from src.core.models import AgendaItem, save_agenda, load_decisions, load_actions


class TestVoicePipeline(unittest.TestCase):
    """Test Gradium client instructions and transcript processing."""

    def test_build_system_instructions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agenda_p = Path(tmpdir) / "agenda.json"
            items = [
                AgendaItem(
                    item_id="agenda-01",
                    topic="PR #4 Staging Migration",
                    question_for_lead="Approve staging migration for PR #4? Yes or no?",
                    recommended_action="APPROVE",
                    is_irreversible=False,
                )
            ]
            save_agenda(items, agenda_p)

            prompt = build_system_instructions(agenda_path=agenda_p)
            self.assertIn("Good morning Philipp. Swarm overnight triage ready", prompt)
            self.assertIn("Approve staging migration for PR #4?", prompt)
            self.assertIn("Captured. Knowledge graph updated", prompt)

    def test_extract_decisions_from_turns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agenda_p = Path(tmpdir) / "agenda.json"
            items = [
                AgendaItem(
                    item_id="agenda-01",
                    topic="Deploy Staging",
                    question_for_lead="Deploy?",
                    recommended_action="APPROVE",
                    is_irreversible=False,
                ),
                AgendaItem(
                    item_id="agenda-02",
                    topic="Purge DB",
                    question_for_lead="Purge?",
                    recommended_action="APPROVE",
                    is_irreversible=True,
                ),
            ]
            save_agenda(items, agenda_p)

            turns = [
                {"speaker": "agent", "text": "How much time do you have?"},
                {"speaker": "user", "text": "Got 60 seconds"},
                {"speaker": "agent", "text": "Deploy staging?"},
                {"speaker": "user", "text": "Yes, approve it"},
                {"speaker": "agent", "text": "Purge database?"},
                {"speaker": "user", "text": "Hold on that until I see the dashboard"},
            ]

            decisions = extract_decisions_from_turns(turns, agenda_path=agenda_p)
            self.assertEqual(len(decisions), 2)
            self.assertEqual(decisions[0].decision_type, "APPROVE")
            self.assertEqual(decisions[1].decision_type, "HOLD")

    def test_save_call_transcript_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agenda_p = Path(tmpdir) / "agenda.json"
            dec_p = Path(tmpdir) / "decisions.json"
            act_p = Path(tmpdir) / "actions.json"
            trans_p = Path(tmpdir) / "transcript.json"

            items = [
                AgendaItem(
                    item_id="agenda-01",
                    topic="Deploy WebSocket",
                    question_for_lead="Deploy?",
                    recommended_action="APPROVE",
                    is_irreversible=False,
                )
            ]
            save_agenda(items, agenda_p)

            payload = {
                "call_id": "test-call-001",
                "caller": "DawnDispatch Voice Agent",
                "callee": "Philipp (Meta Ray-Ban)",
                "duration_seconds": 45,
                "turns": [
                    {"speaker": "agent", "text": "How much time?"},
                    {"speaker": "user", "text": "1 minute"},
                    {"speaker": "agent", "text": "Deploy websocket?"},
                    {"speaker": "user", "text": "Yes"},
                ],
            }

            saved = save_call_transcript(
                payload,
                output_path=trans_p,
                decisions_path=dec_p,
                actions_path=act_p,
                agenda_path=agenda_p,
            )

            self.assertTrue(trans_p.exists())
            self.assertEqual(saved["call_id"], "test-call-001")
            self.assertEqual(len(saved["decisions_captured"]), 1)

            # Check decisions and actions written
            decisions = load_decisions(dec_p)
            self.assertEqual(len(decisions), 1)
            self.assertEqual(decisions[0].decision_type, "APPROVE")

            actions = load_actions(act_p)
            self.assertEqual(len(actions), 1)
            self.assertEqual(actions[0].status, "COMPLETED")


class TestVoiceAppAPI(unittest.TestCase):
    """Test FastAPI routes and static delivery."""

    def setUp(self):
        self.client = TestClient(app)

    def test_call_html_endpoint(self):
        res = self.client.get("/call")
        self.assertEqual(res.status_code, 200)
        html = res.text
        self.assertIn("DawnDispatch", html)
        self.assertIn("Ray-Ban", html)
        self.assertIn("Answer", html)
        self.assertIn("screen-incoming", html)
        self.assertIn("screen-active", html)
        self.assertIn("screen-ended", html)

    def test_root_redirect(self):
        res = self.client.get("/", follow_redirects=False)
        self.assertEqual(res.status_code, 307)
        self.assertEqual(res.headers["location"], "/call")

    def test_agenda_api(self):
        res = self.client.get("/api/agenda")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)

    def test_end_call_api(self):
        payload = {
            "call_id": "test-call-api-999",
            "duration_seconds": 52,
            "turns": [
                {"speaker": "agent", "text": "Good morning"},
                {"speaker": "user", "text": "Yes, approve PR"},
            ],
            "decisions_captured": [
                {
                    "item_id": "agenda-01",
                    "decision_type": "APPROVE",
                    "voice_notes": "API test approval",
                }
            ],
        }
        res = self.client.post("/api/end_call", json=payload)
        self.assertEqual(res.status_code, 200)
        resp_data = res.json()
        self.assertTrue(resp_data.get("success"))

        # Verify get_transcript returns it
        get_res = self.client.get("/api/transcript")
        self.assertEqual(get_res.status_code, 200)
        t_data = get_res.json()
        self.assertEqual(t_data.get("call_id"), "test-call-api-999")


if __name__ == "__main__":
    unittest.main()
