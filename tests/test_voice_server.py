"""Voice tool handlers and post-call processing (claude-03) with fakes - no gradbot session, no network.

DAWN_DATA_DIR points at a temp copy of the seeds so src/data stays untouched.
"""
from __future__ import annotations

import asyncio
import json
import os
import pathlib
import shutil
import tempfile
import unittest

from src.core import state
from src.core.models import load_actions, load_decisions
from src.voice import postcall, prompt, server

SEED_DIR = state.DEFAULT_DATA_DIR


class FakeHandle:
    def __init__(self, name, args):
        self.name, self.args, self.results, self.errors = name, args, [], []

    async def send_json(self, obj):
        self.results.append(obj)

    async def send(self, s):
        self.results.append(json.loads(s))

    async def send_error(self, msg):
        self.errors.append(msg)


class FakeWS:
    def __init__(self):
        self.sent, self.closed = [], False

    async def send_json(self, payload, *a, **k):
        self.sent.append(payload)

    async def close(self):
        self.closed = True


class FakeInput:
    def __init__(self):
        self.configs = []

    async def send_config(self, cfg):
        self.configs.append(cfg)


def run(coro):
    return asyncio.run(coro)


class VoiceServerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        for name in ("overnight_events.json", "agenda.json", "knowledge_graph_before.json"):
            if (SEED_DIR / name).exists():
                shutil.copy(SEED_DIR / name, self.tmp / name)
        self._old = os.environ.get("DAWN_DATA_DIR")
        os.environ["DAWN_DATA_DIR"] = str(self.tmp)
        os.environ["DAWN_TEAM_COUNT"] = "7"
        self.bus_events = []

        async def fake_publish(event):
            self.bus_events.append(event)

        self._old_bus = server._bus_publish
        server._bus_publish = fake_publish
        self.ws = FakeWS()
        self.inp = FakeInput()
        self.session = server.CallSession(self.ws)

    def tearDown(self):
        server._bus_publish = self._old_bus
        if self._old is None:
            os.environ.pop("DAWN_DATA_DIR", None)
        else:
            os.environ["DAWN_DATA_DIR"] = self._old
        os.environ.pop("DAWN_TEAM_COUNT", None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def call(self, name, **args):
        h = FakeHandle(name, args)
        run(self.session.on_tool_call(h, self.inp, self.ws))
        return h

    def types(self):
        return [e["type"] for e in self.bus_events]

    def test_prompt_contains_contract_lines_and_tools(self):
        text = prompt.build_instructions()
        self.assertIn("public", text)
        self.assertIn("other teams", text)
        self.assertIn(prompt.CLOSING_LINE, text)
        self.assertEqual(set(prompt.TOOL_NAMES), {"set_time_budget", "log_decision", "mark_irreversible_checkpoint", "set_speaking_speed", "end_call"})
        self.assertEqual({s["name"] for s in prompt.active_tool_specs()}, {"log_decision", "mark_irreversible_checkpoint", "end_call"})
        self.assertIn("Hey Philipp, it's Dawn", text)  # dawn/prompt.txt is the base
        self.assertIn("log_decision", text)
        for spec in prompt.TOOL_SPECS:
            json.dumps(spec["parameters"])  # valid JSON schema payload

    def test_start_emits_call_started_and_agenda(self):
        run(self.session.start())
        self.assertEqual(self.types(), ["call_started", "agenda_item"])
        self.assertIn("Dawn", self.bus_events[0]["data"]["opening"])
        self.assertEqual(self.ws.sent[0]["type"], "agenda")
        self.assertEqual(len(self.ws.sent[0]["items"]), 4)
        self.assertEqual(state.load().call.status, "live")
        self.assertTrue((self.tmp / "knowledge_graph_before.json").exists())

    def test_full_demo_flow_through_tools(self):
        run(self.session.start())
        h = self.call("set_time_budget", seconds=60)
        self.assertEqual(h.results[-1]["next_item_id"], "agenda-01")
        self.assertEqual(state.load().call.time_budget_s, 60)

        run(self.session.record_turn("user", 1, "nothing to flag", 5.0))
        h = self.call("log_decision", item_id="agenda-01", decision="APPROVE", notes="nothing to flag")
        self.assertEqual(h.results[-1]["next_item_id"], "agenda-02")

        h = self.call("log_decision", item_id="agenda-02", decision="APPROVE", notes="night shift", option="B")
        self.assertEqual(h.results[-1]["next_item_id"], "agenda-03")
        self.assertEqual(state.load().meta.get("v2_option"), "B")

        h = self.call("set_speaking_speed", speed=1.5, reason="in a hurry")
        self.assertEqual(h.results[-1]["speed"], 1.5)
        self.assertEqual(len(self.inp.configs), 1)

        h = self.call("log_decision", item_id="agenda-03", decision="APPROVE", notes="yes, but I click it")
        self.assertEqual(h.results[-1]["checkpoint"], "BLOCKED_ON_CHECKPOINT")
        actions = {a.item_id: a for a in load_actions(self.tmp / "actions.json")}
        self.assertEqual(actions["agenda-03"].status, "BLOCKED_ON_CHECKPOINT")
        self.assertEqual(actions["agenda-01"].status, "COMPLETED")

        h = self.call("mark_irreversible_checkpoint", item_id="agenda-03", reason="public repo")
        self.assertEqual(h.results[-1]["checkpoint"], "BLOCKED_ON_CHECKPOINT")
        self.assertEqual(self.types().count("checkpoint"), 1, "checkpoint event emitted once")

        h = self.call("log_decision", item_id="agenda-04", decision="APPROVE", notes="offer it")
        self.assertIsNone(h.results[-1]["next_item_id"])

        h = self.call("end_call", summary="v2 is the night shift; publish waits for the click")
        self.assertEqual(h.results[-1]["say"], prompt.CLOSING_LINE)
        self.assertTrue(self.session.ended)

        types = self.types()
        for t in ("call_started", "time_budget", "agenda_item", "user_said", "decision", "v2_idea",
                  "speed_changed", "checkpoint", "participants_scaled", "call_ended", "brief_ready"):
            self.assertIn(t, types, t)
        self.assertEqual(types.count("agenda_item"), 3)  # decisions one to three (agenda-02..04)
        scaled = next(e for e in self.bus_events if e["type"] == "participants_scaled")
        self.assertEqual(scaled["data"]["count"], 7)
        for e in self.bus_events:
            self.assertEqual(set(e), {"type", "ts", "data"})

        # post-call artefacts
        self.assertTrue((self.tmp / "knowledge_graph_after.json").exists())
        self.assertTrue((self.tmp / "transcript.json").exists())
        transcript = json.loads((self.tmp / "transcript.json").read_text())
        self.assertTrue(any(t["speaker"] == "Philipp" and "nothing to flag" in t["text"] for t in transcript["turns"]))
        st = state.load()
        self.assertEqual(st.call.status, "ended")
        self.assertEqual(len(st.call.briefing), 3)
        self.assertEqual(len(load_decisions(self.tmp / "decisions.json")), 4)
        graph = json.loads((self.tmp / "knowledge_graph_after.json").read_text())
        self.assertTrue(any(n["id"] == "dec-agenda-03" for n in graph["nodes"]))
        # the phone page got every event too
        self.assertIn("brief_ready", [m.get("type") for m in self.ws.sent])
        # idempotent
        run(self.session.finish())
        self.assertEqual(types.count("call_ended"), 1)

    def test_invalid_tool_arguments(self):
        run(self.session.start())
        h = self.call("log_decision", item_id="agenda-99", decision="APPROVE")
        self.assertTrue(h.errors)
        h = self.call("log_decision", item_id="agenda-01", decision="MAYBE")
        self.assertTrue(h.errors)
        h = self.call("nope")
        self.assertTrue(h.errors)

    def test_hangup_without_end_call_runs_post_call(self):
        run(self.session.start())
        self.call("set_time_budget", seconds=30)
        self.call("log_decision", item_id="agenda-02", decision="APPROVE", notes="phone", option="A")
        run(self.session.finish(None, reason="hangup"))
        self.assertIn("call_ended", self.types())
        self.assertIn("brief_ready", self.types())
        self.assertTrue((self.tmp / "knowledge_graph_after.json").exists())

    def test_speed_mapping(self):
        self.assertEqual(server.speed_to_padding(1.0), 0.0)
        self.assertLess(server.speed_to_padding(1.5), 0.0)
        self.assertGreater(server.speed_to_padding(0.8), 0.0)
        self.assertEqual(server.clamp_speed(5), 1.8)

    def test_postcall_module_standalone(self):
        result = postcall.process_post_call("standalone", 42)
        self.assertEqual(len(result["briefing"]), 3)
        self.assertTrue((self.tmp / "actions.json").exists())


if __name__ == "__main__":
    unittest.main()
