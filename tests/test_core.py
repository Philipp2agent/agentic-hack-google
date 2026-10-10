"""Comprehensive Unit & Integration Tests for DawnDispatch Core."""

import json
import os
from pathlib import Path
import tempfile
import unittest

from src.core.models import (
    ActionExecution,
    AgendaItem,
    DecisionRecord,
    OvernightEvent,
    load_actions,
    load_agenda,
    load_decisions,
    load_events,
    save_actions,
    save_agenda,
    save_decisions,
    save_events,
)
from src.core.repo_events import (
    collect_repo_events,
    aggregate_and_save,
    parse_git_commits,
)
from src.core.agenda_synth import (
    synthesize_agenda,
    synthesize_agenda_fallback,
    synthesize_agenda_with_gemini,
)
from src.core.action_engine import (
    confirm_checkpoint,
    log_decision,
    mark_irreversible_checkpoint,
    process_decisions,
)
from src.core.graph_engine import (
    build_knowledge_graph_before,
    build_knowledge_graph_after,
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
        )
        self.assertEqual(dec.decision_type, "APPROVE")
        self.assertTrue(dec.human_verified)
        self.assertTrue(dec.timestamp.endswith("Z"))

    def test_action_execution_validation(self):
        act = ActionExecution(
            action_id="act-101",
            item_id="agenda-01",
            action_type="DEPLOY_VOICE",
            status="COMPLETED",
            artifacts={"port": 8090},
        )
        self.assertEqual(act.status, "COMPLETED")
        self.assertEqual(act.artifacts["port"], 8090)

    def test_file_io_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            evts = [
                OvernightEvent(
                    id="evt-001",
                    source="git commit 1234567",
                    agent_id="hack-bau1",
                    title="Test event",
                    details="Details here",
                    severity="INFO",
                    proposed_action="Action here",
                )
            ]
            p = Path(tmpdir) / "events.json"
            save_events(evts, p)
            loaded = load_events(p)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].id, "evt-001")


class TestRepoEvents(unittest.TestCase):
    """Test repo event aggregation from git and files."""

    def test_parse_git_commits(self):
        events = parse_git_commits(".", limit=5)
        self.assertIsInstance(events, list)
        self.assertGreater(len(events), 0)
        for e in events:
            self.assertTrue(e.id.startswith("evt-"))
            self.assertIn(e.severity, ("INFO", "WARNING", "ERROR"))
            self.assertTrue(len(e.title) > 0)

    def test_collect_repo_events(self):
        events = collect_repo_events(".", limit=5)
        self.assertGreaterEqual(len(events), 3)
        self.assertEqual(events[0].id, "evt-001")


class TestAgendaSynthesis(unittest.TestCase):
    """Test agenda synthesis with fallback and Gemini."""

    def setUp(self):
        self.sample_events = [
            OvernightEvent(
                id="evt-001",
                source="git commit abc",
                agent_id="hack-chef",
                title="Wipe database and purge cache",
                details="Destructive database purge and cache reset required",
                severity="WARNING",
                proposed_action="Purge database state before live demo",
            ),
            OvernightEvent(
                id="evt-002",
                source="git commit def",
                agent_id="hack-bau1",
                title="Add models and core logic",
                details="Core pipeline complete",
                severity="INFO",
                proposed_action="Proceed with review",
            ),
        ]

    def test_fallback_synthesis(self):
        agenda = synthesize_agenda_fallback(self.sample_events)
        self.assertLessEqual(len(agenda), 3)
        self.assertGreater(len(agenda), 0)
        # First item has wipe/purge keyword so it must be marked irreversible
        self.assertTrue(agenda[0].is_irreversible)
        self.assertEqual(agenda[0].item_id, "agenda-01")

    def test_gemini_synthesis_if_key_available(self):
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_COMPAT_API_KEY")
        if not key:
            self.skipTest("No GEMINI_API_KEY set; skipping live Gemini API call")
        agenda = synthesize_agenda_with_gemini(self.sample_events, api_key=key)
        self.assertLessEqual(len(agenda), 3)
        self.assertGreater(len(agenda), 0)
        for item in agenda:
            self.assertTrue(item.item_id.startswith("agenda-"))
            self.assertTrue(len(item.topic) > 0)
            self.assertTrue(len(item.question_for_lead) > 0)
            self.assertIsInstance(item.is_irreversible, bool)


class TestActionEngine(unittest.TestCase):
    """Test decisions recording, checkpoints, and action execution."""

    def test_log_decision_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dec_file = Path(tmpdir) / "decisions.json"
            act_file = Path(tmpdir) / "actions.json"
            agenda_file = Path(tmpdir) / "agenda.json"

            # Create test agenda: 1 reversible, 1 irreversible
            agenda = [
                AgendaItem(
                    item_id="agenda-01",
                    topic="Deploy Service",
                    question_for_lead="Deploy?",
                    recommended_action="APPROVE",
                    is_irreversible=False,
                ),
                AgendaItem(
                    item_id="agenda-02",
                    topic="Wipe Database",
                    question_for_lead="Wipe?",
                    recommended_action="APPROVE",
                    is_irreversible=True,
                ),
            ]
            save_agenda(agenda, agenda_file)

            # Log decisions
            log_decision("agenda-01", "APPROVE", "Lead approved reversible deploy", file_path=dec_file)
            log_decision("agenda-02", "APPROVE", "Lead approved database wipe", file_path=dec_file)

            # Process decisions
            actions = process_decisions(
                agenda_path=agenda_file,
                decisions_path=dec_file,
                actions_path=act_file,
            )

            self.assertEqual(len(actions), 2)

            # agenda-01 was reversible -> COMPLETED
            a1 = next(a for a in actions if a.item_id == "agenda-01")
            self.assertEqual(a1.status, "COMPLETED")

            # agenda-02 was irreversible -> BLOCKED_ON_CHECKPOINT
            a2 = next(a for a in actions if a.item_id == "agenda-02")
            self.assertEqual(a2.status, "BLOCKED_ON_CHECKPOINT")
            self.assertIn("pending_url", a2.artifacts)

            # Confirm checkpoint
            confirmed = confirm_checkpoint(a2.action_id, actions_path=act_file)
            self.assertEqual(confirmed.status, "COMPLETED")
            self.assertTrue(confirmed.artifacts.get("checkpoint_confirmed"))


class TestEndToEndPipeline(unittest.TestCase):
    """Full integration test: Repo -> Events -> Agenda -> Decisions -> Actions."""

    def test_full_pipeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = Path(tmpdir) / "overnight_events.json"
            agenda_file = Path(tmpdir) / "agenda.json"
            decisions_file = Path(tmpdir) / "decisions.json"
            actions_file = Path(tmpdir) / "actions.json"

            # 1. Aggregate events
            events = aggregate_and_save(repo_dir=".", output_path=events_file, limit=4)
            self.assertTrue(events_file.exists())
            loaded_events = load_events(events_file)
            self.assertEqual(len(events), len(loaded_events))

            # 2. Synthesize agenda
            agenda = synthesize_agenda(loaded_events)
            save_agenda(agenda, agenda_file)
            self.assertTrue(agenda_file.exists())
            loaded_agenda = load_agenda(agenda_file)
            self.assertLessEqual(len(loaded_agenda), 3)

            # 3. Simulate lead voice decisions
            for item in loaded_agenda:
                decision_type = "APPROVE"
                log_decision(
                    item.item_id,
                    decision_type,
                    f"Voice decision for {item.topic}",
                    file_path=decisions_file,
                )

            # 4. Process actions
            actions = process_decisions(
                agenda_path=agenda_file,
                decisions_path=decisions_file,
                actions_path=actions_file,
            )
            self.assertTrue(actions_file.exists())
            loaded_actions = load_actions(actions_file)
            self.assertEqual(len(actions), len(loaded_actions))

            for a in loaded_actions:
                self.assertIn(a.status, ("COMPLETED", "BLOCKED_ON_CHECKPOINT", "PENDING"))


if __name__ == "__main__":
    unittest.main()


class TestKnowledgeGraphEngine(unittest.TestCase):
    """Test before and after knowledge graph creation and transitions."""

    def test_graph_before_and_after_lifecycle(self):
        events = [
            OvernightEvent(
                id="evt-001",
                source="git commit abc1",
                agent_id="hack-bau1",
                title="Service code pushed",
                details="Commit details",
                severity="INFO",
                proposed_action="Proceed",
            )
        ]
        agenda = [
            AgendaItem(
                item_id="agenda-01",
                topic="Deploy Service",
                question_for_lead="Deploy now?",
                recommended_action="APPROVE",
                is_irreversible=False,
            )
        ]
        gb = build_knowledge_graph_before(events, agenda)
        self.assertEqual(gb.stage, "BEFORE")
        self.assertGreaterEqual(len(gb.nodes), 2)
        self.assertGreaterEqual(len(gb.edges), 1)

        decisions = [
            DecisionRecord(
                item_id="agenda-01",
                decision_type="APPROVE",
                voice_notes="Lead confirmed",
            )
        ]
        actions = [
            ActionExecution(
                action_id="act-101",
                item_id="agenda-01",
                action_type="DEPLOY",
                status="COMPLETED",
                artifacts={},
            )
        ]
        ga = build_knowledge_graph_after(gb, decisions, actions)
        self.assertEqual(ga.stage, "AFTER")
        self.assertGreater(len(ga.nodes), len(gb.nodes))
        action_node = next(n for n in ga.nodes if n.id == "act-101")
        self.assertEqual(action_node.status, "COMPLETED")
