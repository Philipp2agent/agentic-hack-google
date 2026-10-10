"""Comprehensive Unit & Integration Tests for DawnDispatch Core (gemini-01).

Runs offline on isolated temp DAWN_DATA_DIR without external network or API keys.
"""

import json
import os
import pathlib
import shutil
import tempfile
import unittest

from src.core import state
from src.core.models import (
    ActionExecution,
    AgendaItem,
    DecisionRecord,
    OvernightEvent,
    load_events,
    save_events,
)
from src.core.repo_events import collect_events
from src.core.action_engine import (
    execute_action,
    on_decision,
    process_post_call,
    synthesize_agenda,
)
from src.core.graph import build_graph
from src.core.agenda import (
    DEFAULT_AGENDA_ITEMS,
    SLOGAN,
    TOPICS_V1_TO_V2,
    V1_SUMMARY,
    V2_SUMMARY,
    format_quickfire_summary,
    get_agenda,
    get_quickfire_catalog,
    get_v2_agenda,
    sync_agenda_file,
)


class TestCoreModels(unittest.TestCase):
    """Test data model schemas and file I/O."""

    def test_overnight_event_validation(self):
        evt = OvernightEvent(
            id="evt-001",
            source="git commit abc1234",
            agent_id="hack-bau1",
            title="Core module built",
            details="All unit tests passed",
            severity="INFO",
            proposed_action="Proceed to integration",
        )
        self.assertEqual(evt.id, "evt-001")
        self.assertEqual(evt.severity, "INFO")

    def test_agenda_item_validation(self):
        item = AgendaItem(
            item_id="agenda-01",
            topic="Deploy Streaming Service",
            question_for_lead="Deploy service now?",
            recommended_action="APPROVE - latency ok",
            is_irreversible=False,
        )
        self.assertEqual(item.item_id, "agenda-01")
        self.assertFalse(item.is_irreversible)

    def test_decision_record_validation(self):
        dec = DecisionRecord(
            item_id="agenda-01",
            decision_type="APPROVE",
            voice_notes="Approved via Ray-Ban headset",
            human_verified=True,
        )
        self.assertEqual(dec.decision_type, "APPROVE")
        self.assertTrue(dec.human_verified)
        self.assertTrue(dec.timestamp.endswith("Z"))

    def test_action_execution_validation(self):
        act = ActionExecution(
            action_id="act-101",
            item_id="agenda-01",
            action_type="DEPLOY",
            status="COMPLETED",
            artifacts={"port": 8090},
        )
        self.assertEqual(act.status, "COMPLETED")
        self.assertEqual(act.artifacts["port"], 8090)


class TestGemini01AcceptanceCriteria(unittest.TestCase):
    """Explicit tests for criteria (a)-(e) in auftraege/gemini-01.md."""

    _tmp: pathlib.Path | None = None
    _orig_env: str | None = None

    @classmethod
    def setUpClass(cls):
        cls._orig_env = os.environ.get("DAWN_DATA_DIR")
        cls._tmp = pathlib.Path(tempfile.mkdtemp())
        os.environ["DAWN_DATA_DIR"] = str(cls._tmp)

    @classmethod
    def tearDownClass(cls):
        if cls._orig_env is not None:
            os.environ["DAWN_DATA_DIR"] = cls._orig_env
        else:
            os.environ.pop("DAWN_DATA_DIR", None)
        if cls._tmp and cls._tmp.exists():
            shutil.rmtree(cls._tmp, ignore_errors=True)

    def setUp(self):
        if self._tmp:
            for f in self._tmp.glob("*.json"):
                f.unlink()
        state.reset()

    def test_a_collect_events_returns_at_least_5_events(self):
        """(a) collect_events liefert >= 5 gueltige Events."""
        events = collect_events(state.REPO_ROOT)
        self.assertIsInstance(events, list)
        self.assertGreaterEqual(len(events), 5)
        for e in events:
            self.assertTrue(e.id.startswith("evt-"))
            self.assertIn(e.severity, ("INFO", "WARNING", "ERROR"))
            self.assertTrue(len(e.title) > 0)
            self.assertTrue(len(e.source) > 0)

    def test_b_on_decision_reversible_and_irreversible(self):
        """(b) on_decision: irreversibel -> BLOCKED_ON_CHECKPOINT, reversibel -> COMPLETED mit >= 1 Artefakt."""
        rev_item = AgendaItem(
            item_id="agenda-01",
            topic="Run contract tests",
            question_for_lead="Run tests?",
            recommended_action="APPROVE",
            is_irreversible=False,
            action_type="DISPATCH_AGENT",
        )
        irrev_item = AgendaItem(
            item_id="agenda-02",
            topic="Purge database",
            question_for_lead="Purge db?",
            recommended_action="APPROVE",
            is_irreversible=True,
            action_type="DELETE_FILES",
        )
        state.set_inputs(agenda=[rev_item, irrev_item])

        # 1. Reversible APPROVE
        d1 = DecisionRecord(item_id="agenda-01", decision_type="APPROVE", voice_notes="proceed")
        state.add_decision(d1)
        actions1 = on_decision(d1)
        self.assertEqual(len(actions1), 1)
        self.assertEqual(actions1[0].status, "COMPLETED")
        self.assertGreaterEqual(len(actions1[0].artifacts), 1)

        # 2. Irreversible APPROVE -> BLOCKED_ON_CHECKPOINT
        d2 = DecisionRecord(item_id="agenda-02", decision_type="APPROVE", voice_notes="caution")
        state.add_decision(d2)
        actions2 = on_decision(d2)
        self.assertEqual(len(actions2), 1)
        self.assertEqual(actions2[0].status, "BLOCKED_ON_CHECKPOINT")
        self.assertIn("pending_url", actions2[0].artifacts)
        self.assertTrue(actions2[0].checkpoint_reason)

    def test_c_confirm_checkpoint_executes_action(self):
        """(c) nach state.confirm_checkpoint setzt execute_action COMPLETED."""
        irrev_item = AgendaItem(
            item_id="agenda-02",
            topic="Purge obsolete branch",
            question_for_lead="Purge branch?",
            recommended_action="APPROVE",
            is_irreversible=True,
            action_type="DELETE_FILES",
        )
        state.set_inputs(agenda=[irrev_item])
        d = DecisionRecord(item_id="agenda-02", decision_type="APPROVE", voice_notes="verified")
        state.add_decision(d)
        actions = on_decision(d)
        act = actions[0]
        self.assertEqual(act.status, "BLOCKED_ON_CHECKPOINT")

        # Confirm checkpoint in state
        state.confirm_checkpoint(act.action_id)
        # Execute action
        executed = execute_action(act.action_id)
        self.assertEqual(executed.status, "COMPLETED")
        self.assertIn("commit", executed.artifacts)

    def test_d_process_post_call_offline_briefing(self):
        """(d) process_post_call ohne Schluessel -> 3 Briefing-Zeilen."""
        item = AgendaItem(
            item_id="agenda-01",
            topic="Morning check",
            question_for_lead="Ok?",
            recommended_action="APPROVE",
            is_irreversible=False,
            action_type="NOTE",
        )
        state.set_inputs(agenda=[item])
        call = process_post_call()
        self.assertEqual(call.status, "ended")
        self.assertEqual(len(call.briefing), 3)
        for b in call.briefing:
            self.assertIsInstance(b, str)
            self.assertTrue(len(b) > 0)

    def test_e_build_graph_after_has_decision_nodes_and_edges(self):
        """(e) build_graph(..., 'after') hat fuer jede Decision einen Knoten und agenda->decision-Kante."""
        item = AgendaItem(
            item_id="agenda-01",
            topic="Merge PR",
            question_for_lead="Merge PR?",
            recommended_action="APPROVE",
            is_irreversible=False,
            action_type="MERGE_BRANCH",
        )
        state.set_inputs(agenda=[item])
        dec = DecisionRecord(item_id="agenda-01", decision_type="APPROVE", voice_notes="approved")
        state.add_decision(dec)
        on_decision(dec)

        st = state.load()
        graph = build_graph(st, phase="after")
        self.assertEqual(graph.phase, "after")

        # Check node exists
        node_ids = {n.id for n in graph.nodes}
        self.assertIn(dec.decision_id, node_ids)

        # Check agenda -> decision edge exists
        edge_pairs = {(e.source, e.target) for e in graph.edges}
        self.assertIn(("agenda-01", dec.decision_id), edge_pairs)


class TestAgendaV2Catalog(unittest.TestCase):
    """Test Agenda v1 -> v2 Schnellfeuer questions, slogan, and topics."""

    def test_v2_agenda_structure(self):
        items = get_v2_agenda()
        self.assertEqual(len(items), 4, "Agenda must contain exactly 4 quick-fire items per docs/LIVE-EVENTS.md")
        expected_ids = ["agenda-01", "agenda-02", "agenda-03", "agenda-04"]
        for idx, (item, exp_id) in enumerate(zip(items, expected_ids), start=1):
            self.assertEqual(item.item_id, exp_id)
            self.assertEqual(item.priority, idx)
            self.assertTrue(len(item.topic) > 0)
            self.assertTrue(len(item.question_for_lead) > 0)
            self.assertTrue(len(item.recommended_action) > 0)

    def test_v2_agenda_topics_and_slogan(self):
        # Verify slogan
        self.assertEqual(SLOGAN, "The agent owns the code and the human")

        # Verify all four required sprint themes and slogan are covered
        all_text = " ".join(
            f"{it.topic} {it.question_for_lead} {it.recommended_action}"
            for it in DEFAULT_AGENDA_ITEMS
        )
        self.assertIn("The agent owns the code and the human", all_text)
        self.assertIn("WhatsApp Calling", all_text)
        self.assertIn("Night Shift", all_text)
        self.assertIn("Voice", all_text)
        self.assertIn("Build Pipeline", all_text)

        # Verify topics constant
        self.assertEqual(len(TOPICS_V1_TO_V2), 4)

    def test_v2_agenda_irreversibility(self):
        items = get_v2_agenda()
        irrev_items = [it for it in items if it.is_irreversible]
        self.assertEqual(len(irrev_items), 1, "Exactly one item must be irreversible for human checkpoint demo")
        self.assertEqual(irrev_items[0].item_id, "agenda-03")
        self.assertEqual(irrev_items[0].action_type, "DEPLOY")

    def test_v2_quickfire_questions(self):
        items = get_v2_agenda()
        for it in items:
            self.assertTrue(it.question_for_lead.endswith("?"))
            word_count = len(it.question_for_lead.split())
            self.assertLessEqual(word_count, 35)

    def test_quickfire_catalog(self):
        cat = get_quickfire_catalog()
        self.assertEqual(len(cat), 4)
        for entry in cat:
            self.assertIn("item_id", entry)
            self.assertIn("question", entry)
            self.assertIn("recommended", entry)
            self.assertIn("is_irreversible", entry)

    def test_quickfire_summary_formatting(self):
        summary = format_quickfire_summary()
        self.assertIn("DawnDispatch Schnellfeuer Agenda", summary)
        self.assertIn(SLOGAN, summary)
        for topic in TOPICS_V1_TO_V2:
            self.assertIn(topic, summary)

    def test_agenda_file_sync(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = pathlib.Path(tmpdir) / "agenda.json"
            items = sync_agenda_file(output_path=out_file)
            self.assertEqual(len(items), 4)
            self.assertTrue(out_file.exists())
            loaded = get_agenda(agenda_path=out_file)
            self.assertEqual(len(loaded), 4)
            self.assertEqual(loaded[0].item_id, "agenda-01")
            self.assertEqual(loaded[2].item_id, "agenda-03")
            self.assertTrue(loaded[2].is_irreversible)


if __name__ == "__main__":
    unittest.main()
