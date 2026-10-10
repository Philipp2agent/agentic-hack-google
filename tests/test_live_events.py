"""Test live events contract compliance (docs/LIVE-EVENTS.md).

Validates event schemas, required types, demo agenda sequence,
and tools/live_demo_events.py event generation.
"""
import json
import unittest
from datetime import datetime

from tools.live_demo_events import get_demo_events, format_event, EVENT_TYPES


class LiveEventsContractTest(unittest.TestCase):
    """Test docs/LIVE-EVENTS.md event format and types."""

    EXPECTED_TYPES = {
        "call_started": {"opening"},
        "time_budget": {"seconds"},
        "speed_changed": {"speed", "reason"},
        "agenda_item": {"item_id", "title", "index", "total"},
        "user_said": {"text"},
        "decision": {"item_id", "decision", "summary"},
        "checkpoint": {"item_id", "action", "reason"},
        "checkpoint_resolved": {"item_id", "approved"},
        "v2_idea": {"id", "title", "linked_to"},
        "participants_scaled": {"count", "label"},
        "call_ended": {"duration_s"},
        "brief_ready": set(),
    }

    def test_all_12_types_documented_are_present(self):
        """Verify all 12 event types from docs/LIVE-EVENTS.md exist."""
        for ev_type in self.EXPECTED_TYPES:
            self.assertIn(ev_type, EVENT_TYPES)

    def test_demo_events_format_and_timestamps(self):
        """Verify formatted events conform to {"type", "ts", "data"} schema."""
        raw_events = get_demo_events()
        self.assertGreater(len(raw_events), 0)

        for raw in raw_events:
            ev = format_event(raw)
            self.assertIn("type", ev)
            self.assertIn("ts", ev)
            self.assertIn("data", ev)
            self.assertIn(ev["type"], self.EXPECTED_TYPES)

            # Validate ISO timestamp
            dt = datetime.fromisoformat(ev["ts"].replace("Z", "+00:00"))
            self.assertIsNotNone(dt)

            # Check expected keys in data
            required_keys = self.EXPECTED_TYPES[ev["type"]]
            for k in required_keys:
                self.assertIn(k, ev["data"], f"Missing {k} in {ev['type']} data")

    def test_demo_agenda_flow_completeness(self):
        """Verify the full 6-step demo agenda from docs/LIVE-EVENTS.md is present."""
        raw_events = get_demo_events()
        types_in_flow = [e["type"] for e in raw_events]

        # 1. Opening
        self.assertEqual(types_in_flow[0], "call_started")
        opening_text = raw_events[0]["data"]["opening"]
        self.assertIn("Good morning Philipp", opening_text)
        self.assertIn("four things", opening_text)

        # Time budget & speed
        self.assertIn("time_budget", types_in_flow)
        self.assertIn("speed_changed", types_in_flow)

        # 2. Status v1
        self.assertTrue(any(e["type"] == "agenda_item" and e["data"]["index"] == 1 for e in raw_events))

        # 3. Decision v2 with v2_idea
        self.assertIn("v2_idea", types_in_flow)

        # 4. Irreversible checkpoint
        self.assertIn("checkpoint", types_in_flow)
        self.assertIn("checkpoint_resolved", types_in_flow)

        # 5. Scale participants
        self.assertIn("participants_scaled", types_in_flow)

        # 6. Call ended & brief ready
        self.assertIn("call_ended", types_in_flow)
        self.assertIn("brief_ready", types_in_flow)


if __name__ == "__main__":
    unittest.main()
