"""Contract smoke test (claude-02): models + state store + example fixture.

Run:  python -m unittest tests.test_contract -v
"""
import os
import pathlib
import tempfile
import unittest

_tmp = tempfile.mkdtemp()
os.environ["DAWN_STATE_PATH"] = str(pathlib.Path(_tmp) / "state.json")

from src.core import state  # noqa: E402
from src.core.models import (  # noqa: E402
    IRREVERSIBLE_ACTION_TYPES,
    ActionExecution,
    DawnState,
    DecisionRecord,
    TranscriptTurn,
)


class ContractTest(unittest.TestCase):
    def setUp(self):
        state.reset()

    def test_example_fixture_validates(self):
        st = DawnState.model_validate_json(state.EXAMPLE_PATH.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(st.agenda), 3)
        self.assertTrue(any(a.is_irreversible for a in st.agenda), "demo needs one irreversible item")
        for item in st.agenda:
            if item.is_irreversible:
                self.assertIn(item.action_type, IRREVERSIBLE_ACTION_TYPES)

    def test_decision_action_checkpoint_roundtrip(self):
        st = state.load()
        item = next(a for a in st.agenda if a.is_irreversible)
        rec = state.add_decision(DecisionRecord(item_id=item.item_id, decision_type="APPROVE", voice_notes="go"))
        act = state.add_action(
            ActionExecution(item_id=item.item_id, action_type=item.action_type, status="BLOCKED_ON_CHECKPOINT")
        )
        st = state.load()
        self.assertEqual(state.latest_decision(st, item.item_id).decision_id, rec.decision_id)
        self.assertFalse(st.decisions[-1].human_verified)
        state.confirm_checkpoint(act.action_id)
        st = state.load()
        self.assertEqual(st.action(act.action_id).status, "EXECUTING")
        self.assertTrue(state.latest_decision(st, item.item_id).human_verified)
        state.set_action_status(act.action_id, "COMPLETED")
        self.assertEqual(state.load().action(act.action_id).status, "COMPLETED")
        with self.assertRaises(ValueError):
            state.confirm_checkpoint(act.action_id)

    def test_call_lifecycle(self):
        state.start_call(language="en", voice_id="v1")
        state.append_turn(TranscriptTurn(role="agent", text="Good morning Philipp.", t_s=0.5, turn_idx=0))
        state.append_turn(TranscriptTurn(role="user", text="Approve.", t_s=4.0))
        state.end_call(briefing=["a", "b", "c"])
        call = state.load().call
        self.assertEqual(call.status, "ended")
        self.assertEqual(len(call.transcript), 2)
        self.assertEqual(call.briefing, ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
