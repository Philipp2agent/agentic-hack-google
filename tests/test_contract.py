"""Contract smoke test (claude-02): models + state store + committed seeds.

Run:  python -m unittest tests.test_contract -v
"""
import os
import pathlib
import shutil
import tempfile
import unittest

_tmp = pathlib.Path(tempfile.mkdtemp())
os.environ["DAWN_DATA_DIR"] = str(_tmp)  # never touch the committed seeds

from src.core import state  # noqa: E402
from src.core.models import (  # noqa: E402
    ActionExecution,
    AgendaItem,
    DawnState,
    DecisionRecord,
    KnowledgeGraph,
    OvernightEvent,
    TranscriptTurn,
)

SEED_DIR = state.DEFAULT_DATA_DIR


def _seed_tmp():
    for name in ("overnight_events.json", "agenda.json", "decisions.json", "actions.json"):
        src = SEED_DIR / name
        if src.exists():
            shutil.copy(src, _tmp / name)


class ContractTest(unittest.TestCase):
    def setUp(self):
        for f in _tmp.glob("*.json"):
            f.unlink()
        _seed_tmp()
        state.reset()

    @unittest.skipUnless((SEED_DIR / "agenda.json").exists(), "seeds not merged yet")
    def test_committed_seeds_validate(self):
        st = state.load()
        self.assertGreaterEqual(len(st.events), 1)
        self.assertGreaterEqual(len(st.agenda), 1)
        self.assertTrue(any(a.is_irreversible for a in st.agenda), "demo needs one irreversible item")
        # SCHNITTSTELLE.md seeds must round-trip through the models unchanged in meaning
        for a in st.agenda:
            self.assertRegex(a.item_id, r"^agenda-\d+$")
        for e in st.events:
            self.assertIn(e.severity, ("INFO", "WARNING", "ERROR"))

    def test_decision_action_checkpoint_roundtrip(self):
        state.set_inputs(agenda=[AgendaItem(item_id="agenda-02", topic="t", question_for_lead="q",
                                            recommended_action="r", is_irreversible=True, action_type="DELETE_FILES")])
        rec = state.add_decision(DecisionRecord(item_id="agenda-02", decision_type="APPROVE", voice_notes="go"))
        act = state.add_action(ActionExecution(item_id="agenda-02", action_type="DELETE_FILES",
                                               status="BLOCKED_ON_CHECKPOINT", checkpoint_reason="irreversible"))
        st = state.load()
        self.assertEqual(state.latest_decision(st, "agenda-02").decision_id, rec.decision_id)
        self.assertFalse(st.decisions[-1].human_verified)
        state.confirm_checkpoint(act.action_id)
        st = state.load()
        self.assertEqual(st.action(act.action_id).status, "EXECUTING")
        self.assertTrue(state.latest_decision(st, "agenda-02").human_verified)
        state.set_action_status(act.action_id, "COMPLETED", artifacts={"commit": "abc1234", "log": "ok"})
        done = state.load().action(act.action_id)
        self.assertEqual(done.status, "COMPLETED")
        self.assertEqual(done.artifacts["commit"], "abc1234")
        with self.assertRaises(ValueError):
            state.confirm_checkpoint(act.action_id)
        self.assertTrue((_tmp / "actions.json").exists())

    def test_call_lifecycle_and_graph_models(self):
        state.start_call(language="en", voice_id="v1")
        state.set_time_budget(60)
        state.append_turn(TranscriptTurn(role="agent", text="Morning Philipp. How much time do you have?", t_s=0.5, turn_idx=0))
        state.append_turn(TranscriptTurn(role="user", text="Got 60 seconds.", t_s=4.0))
        state.end_call(briefing=["a", "b", "c"])
        call = state.load().call
        self.assertEqual((call.status, call.time_budget_s, len(call.transcript), call.briefing), ("ended", 60, 2, ["a", "b", "c"]))
        g = KnowledgeGraph(phase="before", nodes=[{"id": "agenda-01", "label": "x", "kind": "agenda", "status": "open"}],
                           edges=[{"source": "hack-bau1", "target": "agenda-01"}])
        self.assertEqual(g.nodes[0].status, "open")

    def test_seed_shapes_from_schnittstelle(self):
        # exact shapes from docs/SCHNITTSTELLE.md must validate without extra fields
        OvernightEvent(id="evt-001", source="git commit 3cdd23d", agent_id="hack-bau1", title="t",
                       details="d", severity="WARNING", proposed_action="p")
        ActionExecution(action_id="act-102", item_id="agenda-02", action_type="PURGE_STATE_AND_MIGRATE",
                        status="BLOCKED_ON_CHECKPOINT", artifacts={"reason": "x", "pending_url": "/dashboard/checkpoint/agenda-02"})
        DawnState()


if __name__ == "__main__":
    unittest.main()
