"""End-to-end wiring of /ws/chat with a fake gradbot.run (no Gradium, no Gemini, no network).

Exercises: start message -> on_start (state reset + call_started) -> transcript proxy (agent/user text)
-> tool call through gradbot.websocket.handle_session -> stop -> post-call on hangup.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import tempfile
import unittest

try:
    import gradbot  # noqa: F401
    import gradbot.websocket as gws
except Exception:  # pragma: no cover
    gws = None

from fastapi.testclient import TestClient

from src.core import state
from src.voice import server

SEED_DIR = state.DEFAULT_DATA_DIR


class _Msg:
    """Minimal stand-in for gradbot.MsgOut (attributes read by gradbot.schemas.from_msg)."""

    def __init__(self, msg_type, **kw):
        self.msg_type = msg_type
        self.text = kw.get("text")
        self.start_s = kw.get("start_s")
        self.stop_s = kw.get("stop_s")
        self.turn_idx = kw.get("turn_idx")
        self.interrupted = kw.get("interrupted", False)
        self.event = None
        self.data = kw.get("data")
        self.tool_call = kw.get("tool_call")
        self.tool_call_handle = kw.get("tool_call_handle")


class _ToolCall:
    def __init__(self, name, args):
        self.call_id, self.tool_name, self.args_json = "c1", name, json.dumps(args)


class _ToolHandle:
    def __init__(self):
        self.results, self.errors = [], []

    async def send(self, s):
        self.results.append(json.loads(s))

    async def send_error(self, m):
        self.errors.append(m)


class _Input:
    def __init__(self):
        self.audio, self.configs, self.closed = [], [], False

    async def send_audio(self, b):
        self.audio.append(b)

    async def send_config(self, c):
        self.configs.append(c)

    async def close(self):
        self.closed = True


class _Output:
    def __init__(self, msgs):
        self._msgs = list(msgs)

    async def receive(self):
        if self._msgs:
            return self._msgs.pop(0)
        import asyncio

        await asyncio.sleep(2.0)  # give the background tool task time, then end like a finished session
        return None


@unittest.skipIf(gws is None, "gradbot not installed")
class WsChatWiringTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        for name in ("overnight_events.json", "agenda.json", "knowledge_graph_before.json"):
            if (SEED_DIR / name).exists():
                shutil.copy(SEED_DIR / name, self.tmp / name)
        self._old_env = os.environ.get("DAWN_DATA_DIR")
        os.environ["DAWN_DATA_DIR"] = str(self.tmp)
        self.tool_handle = _ToolHandle()
        self.inp = _Input()
        msgs = [
            _Msg("tts_text", text="Good morning Philipp.", turn_idx=0, stop_s=1.0),
            _Msg("tts_text", text="How much time do you have?", turn_idx=0, stop_s=2.0),
            _Msg("stt_text", text="about a minute", turn_idx=1, stop_s=4.0),
            _Msg("tool_call", tool_call=_ToolCall("set_time_budget", {"seconds": 60}), tool_call_handle=self.tool_handle),
            _Msg("audio", data=b"\x00\x01", start_s=4.5, stop_s=5.0, turn_idx=2),
        ]
        self._real_run = gws.gradbot.run

        async def fake_run(**kwargs):
            self.run_kwargs = kwargs
            return self.inp, _Output(msgs)

        gws.gradbot.run = fake_run
        self.events = []

        async def fake_publish(ev):
            self.events.append(ev)

        self._old_bus = server._bus_publish
        server._bus_publish = fake_publish

    def tearDown(self):
        gws.gradbot.run = self._real_run
        server._bus_publish = self._old_bus
        if self._old_env is None:
            os.environ.pop("DAWN_DATA_DIR", None)
        else:
            os.environ["DAWN_DATA_DIR"] = self._old_env
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_session_roundtrip(self):
        from src.app import app

        import concurrent.futures

        client = TestClient(app)
        received = []
        with client.websocket_connect("/ws/chat") as ws:
            ws.send_json({"type": "start", "language": "en", "lead": "Philipp"})
            # agenda, call_started, agent_text x2, user_text, user_said, audio_timing + bytes, then the
            # tool task (runs in the background) sends time_budget + agenda_item
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                for _ in range(14):
                    try:
                        msg = pool.submit(ws.receive).result(timeout=8)
                    except Exception:
                        break
                    received.append(msg)
                    if "text" in msg and json.loads(msg["text"]).get("type") == "agenda_item":
                        break
            ws.send_json({"type": "stop"})

        texts = [json.loads(m["text"]) for m in received if "text" in m]
        types = [t.get("type") for t in texts]
        self.assertEqual(types[0], "agenda")
        self.assertIn("call_started", types)
        self.assertIn("agent_text", types)
        self.assertIn("user_text", types)
        self.assertIn("time_budget", types)
        self.assertIn("agenda_item", types)
        self.assertTrue(any("bytes" in m for m in received), "audio bytes forwarded")
        self.assertEqual(self.tool_handle.results[0]["seconds"], 60)
        self.assertEqual(self.run_kwargs["session_config"].assistant_speaks_first, True)
        self.assertTrue(self.inp.closed)

        # hangup -> post-call ran: transcript has both speakers, state ended
        st = state.load()
        self.assertEqual(st.call.status, "ended")
        self.assertEqual(st.call.time_budget_s, 60)
        roles = [t.role for t in st.call.transcript]
        self.assertIn("agent", roles)
        self.assertIn("user", roles)
        self.assertIn("call_ended", [e["type"] for e in self.events])
        self.assertTrue((self.tmp / "knowledge_graph_after.json").exists())
        self.assertTrue((self.tmp / "transcript.json").exists())


if __name__ == "__main__":
    unittest.main()
