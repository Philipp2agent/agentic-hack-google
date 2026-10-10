"""dawn/bridge.py: sample call-log lines become live events (docs/LIVE-EVENTS.md), no network, no keys."""
from __future__ import annotations

import io
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from dawn import bridge

ACCEPT_LINE = 'INFO:     (\'192.168.1.20\', 51234) - "WebSocket /ws/chat" [accepted]'
OPEN_LINE = "INFO:     connection open"
USER_LINE = '2026-10-10T16:12:03.117Z  INFO gradbot::session: event=UserText { user_text: "Sixty seconds, keep it fast." }'
AGENT_LINE = '2026-10-10T16:12:04.002Z  INFO gradbot::session: event=AgentText { agent_text: "Got it, fast it is." }'
CLOSE_LINE = "INFO:     connection closed"
OPENING = "Morning Alex, the parser landed last night and all tests are green."


class FakeClock:
    def __init__(self, t: float = 1000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t


class BridgeTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.calls: list[tuple[str, list[str]]] = []

        def classify(text, history):
            self.calls.append((text, list(history)))
            return [{"type": "speed_changed", "data": {"speed": 1.3, "reason": "sixty seconds"}},
                    {"type": "decision", "data": {"item_id": "agenda-01", "decision": "APPROVE", "summary": "go"}},
                    {"type": "v2_idea", "data": {"id": "x", "title": "third one is dropped", "linked_to": []}}]

        self.bridge = bridge.Bridge(OPENING, classify=classify, clock=self.clock)

    def test_websocket_accept_resets_and_starts_the_call(self):
        self.assertEqual(self.bridge.feed(ACCEPT_LINE), [
            {"type": "reset", "data": {}},
            {"type": "call_started", "data": {"opening": OPENING}},
        ])
        self.assertEqual(self.bridge.feed(OPEN_LINE), [])

    def test_user_text_becomes_user_said_after_it_settles(self):
        self.bridge.feed(ACCEPT_LINE)
        self.assertEqual(self.bridge.feed(USER_LINE), [])          # nothing yet: the turn may continue
        self.assertEqual(self.bridge.feed(AGENT_LINE), [])         # agent text is not a user turn
        self.clock.t += 0.5
        self.assertEqual(self.bridge.tick(), [])                   # still within the settle window
        self.clock.t += 1.0
        events = self.bridge.tick()
        self.assertEqual(events[0], {"type": "user_said", "data": {"text": "Sixty seconds, keep it fast."}})
        self.assertEqual([e["type"] for e in events[1:]], ["speed_changed", "decision"])  # at most two classified
        self.assertEqual(self.calls, [("Sixty seconds, keep it fast.", ["Sixty seconds, keep it fast."])])
        self.assertEqual(self.bridge.tick(), [])                   # flushed once

    def test_newer_user_text_replaces_the_pending_turn(self):
        self.bridge.feed(USER_LINE)
        self.clock.t += 0.6
        self.bridge.feed(USER_LINE.replace("Sixty seconds, keep it fast.", "Sixty seconds, keep it fast. Start with the release."))
        self.clock.t += 1.3
        events = self.bridge.tick()
        self.assertEqual(events[0]["data"]["text"], "Sixty seconds, keep it fast. Start with the release.")

    def test_empty_user_text_is_ignored(self):
        self.assertEqual(self.bridge.feed('... user_text: "   " ...'), [])
        self.clock.t += 5
        self.assertEqual(self.bridge.tick(), [])

    def test_connection_closed_ends_the_call_with_duration(self):
        self.bridge.feed(ACCEPT_LINE)
        self.clock.t += 61.7
        self.assertEqual(self.bridge.feed(CLOSE_LINE), [
            {"type": "call_ended", "data": {"duration_s": 61}},
            {"type": "brief_ready", "data": {}},
        ])
        self.assertEqual(self.bridge.feed(CLOSE_LINE), [])         # no call running: nothing to end

    def test_classifier_failure_still_emits_user_said(self):
        def boom(text, history):
            raise RuntimeError("quota")

        b = bridge.Bridge(OPENING, classify=boom, clock=self.clock)
        b.feed(USER_LINE)
        self.clock.t += 2
        with mock.patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(b.tick(), [{"type": "user_said", "data": {"text": "Sixty seconds, keep it fast."}}])

    def test_malformed_classifier_output_is_dropped(self):
        b = bridge.Bridge(OPENING, classify=lambda t, h: ["nope", {"data": {}}, {"type": "", "data": {}},
                                                           {"type": "decision", "data": "not a dict"}], clock=self.clock)
        b.feed(USER_LINE)
        self.clock.t += 2
        events = b.tick()
        self.assertEqual([e["type"] for e in events], ["user_said"])

    def test_full_sample_log_in_order(self):
        lines = [ACCEPT_LINE, OPEN_LINE, USER_LINE, AGENT_LINE, CLOSE_LINE]
        out = []
        for line in lines:
            out += self.bridge.feed(line)
        self.clock.t += 2
        out += self.bridge.tick()
        self.assertEqual([e["type"] for e in out],
                         ["reset", "call_started", "call_ended", "brief_ready", "user_said", "speed_changed", "decision"])
        for ev in out:
            self.assertIsInstance(ev["data"], dict)


class HelpersTest(unittest.TestCase):
    def test_load_opening_is_last_non_empty_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "prompt.txt"
            p.write_text("rules\n\nBRIEFING\nstuff\n\nOPENING\n" + OPENING + "\n\n", encoding="utf-8")
            self.assertEqual(bridge.load_opening(p), OPENING)
            self.assertEqual(bridge.load_opening(pathlib.Path(tmp) / "missing.txt"), "")

    def test_extract_json_from_prose_and_fences(self):
        raw = 'Sure! ```json\n{"events": [{"type": "decision", "data": {"item_id": "a"}}]}\n```'
        self.assertEqual(bridge.extract_json(raw)["events"][0]["type"], "decision")
        self.assertEqual(bridge.extract_json("no json here"), {})
        self.assertEqual(bridge.extract_json("{broken"), {})

    def test_make_classifier_parses_gemini_reply(self):
        reply = {"choices": [{"message": {"content": 'Here you go: {"events": [{"type": "decision", "data": {"item_id": "agenda-02", "decision": "APPROVE", "summary": "ship it"}}]}'}}]}
        captured = {}

        def fake_urlopen(req, timeout=0):
            captured["url"] = req.full_url
            captured["body"] = json.loads(req.data)
            captured["auth"] = req.get_header("Authorization")
            return io.BytesIO(json.dumps(reply).encode())

        env = {"GEMINI_API_KEY": "k-test", "LLM_BASE_URL": "https://example.test/v1/"}
        with mock.patch.dict(os.environ, env, clear=True), mock.patch("urllib.request.urlopen", fake_urlopen):
            classify = bridge.make_classifier(prompt="BRIEFING\nx\nOPENING\ny", agenda=[{"item_id": "agenda-02"}])
            events = classify("ship it", ["ship it"])
        self.assertEqual(events, [{"type": "decision", "data": {"item_id": "agenda-02", "decision": "APPROVE", "summary": "ship it"}}])
        self.assertEqual(captured["url"], "https://example.test/v1/chat/completions")
        self.assertEqual(captured["auth"], "Bearer k-test")
        self.assertEqual(captured["body"]["model"], bridge.DEFAULT_MODEL)
        self.assertIn("agenda-02", captured["body"]["messages"][0]["content"])

    def test_make_classifier_needs_a_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                bridge.make_classifier(prompt="x", agenda=[])

    def test_emit_posts_reset_and_events(self):
        posted = []
        with mock.patch.object(bridge, "post", side_effect=lambda live, path, payload=None: posted.append((path, payload)) or True), \
             mock.patch("sys.stdout", new_callable=io.StringIO):
            bridge.emit("http://live", {"type": "reset", "data": {}})
            bridge.emit("http://live", {"type": "user_said", "data": {"text": "hi"}})
        self.assertEqual(posted, [("/api/live/reset", None), ("/api/live/event", {"type": "user_said", "data": {"text": "hi"}})])


if __name__ == "__main__":
    unittest.main()
