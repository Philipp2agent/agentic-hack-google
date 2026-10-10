#!/usr/bin/env python3
"""Send the demo agenda (docs/LIVE-EVENTS.md) as an event sequence to the live screen.

Lets you show /live without a phone call. Python standard library only.

  python3 tools/live_demo_events.py                       # real-time pacing (~60 s), waits up to 20 s for the laptop click
  python3 tools/live_demo_events.py --fast                # 4x faster, waits 4 s for the click, then approves itself
  python3 tools/live_demo_events.py --instant --wait-click 0
  python3 tools/live_demo_events.py --base-url http://127.0.0.1:8090 --no-reset

Every contract event type is emitted once at least: call_started, time_budget, speed_changed, agenda_item,
user_said, decision, checkpoint, checkpoint_resolved (by click or auto), v2_idea, participants_scaled,
call_ended, brief_ready.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

EVENT_TYPES = (
    "call_started",
    "time_budget",
    "speed_changed",
    "agenda_item",
    "user_said",
    "decision",
    "checkpoint",
    "checkpoint_resolved",
    "v2_idea",
    "participants_scaled",
    "call_ended",
    "brief_ready",
)


def format_event(raw: dict) -> dict:
    from datetime import datetime, timezone
    return {
        "type": raw["type"],
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": raw.get("data", {}),
    }


def get_demo_events() -> list[dict]:
    return [
        {
            "type": "call_started",
            "data": {
                "opening": "Good morning Philipp. Overnight your agents kept building DawnDispatch. I have four things for you. How much time do you have?"
            },
        },
        {
            "type": "user_said",
            "data": {
                "text": "Morning! I have about 60 seconds walking down to the office."
            },
        },
        {
            "type": "time_budget",
            "data": {
                "seconds": 60
            },
        },
        {
            "type": "user_said",
            "data": {
                "text": "Keep it fast, I am in a bit of a hurry."
            },
        },
        {
            "type": "speed_changed",
            "data": {
                "speed": 1.25,
                "reason": "User indicated hurry during walk"
            },
        },
        {
            "type": "agenda_item",
            "data": {
                "item_id": "agenda-01",
                "title": "Status Version 1 Review",
                "index": 1,
                "total": 4,
            },
        },
        {
            "type": "user_said",
            "data": {
                "text": "Status looks solid, nothing to flag."
            },
        },
        {
            "type": "decision",
            "data": {
                "item_id": "agenda-01",
                "decision": "APPROVE",
                "summary": "V1 baseline acknowledged, no blockers flagged"
            },
        },
        {
            "type": "agenda_item",
            "data": {
                "item_id": "agenda-02",
                "title": "Decision Version 2 Roadmap",
                "index": 2,
                "total": 4,
            },
        },
        {
            "type": "user_said",
            "data": {
                "text": "Let's go with option A: real phone and WhatsApp calling."
            },
        },
        {
            "type": "decision",
            "data": {
                "item_id": "agenda-02",
                "decision": "APPROVE",
                "summary": "Selected Option A: Real Phone or WhatsApp Calling"
            },
        },
        {
            "type": "v2_idea",
            "data": {
                "id": "idea-v2-telephony",
                "title": "Real Telephony & WhatsApp Audio Integration",
                "linked_to": ["agenda-02"]
            },
        },
        {
            "type": "agenda_item",
            "data": {
                "item_id": "agenda-03",
                "title": "Irreversible Submission Checkpoint",
                "index": 3,
                "total": 4,
            },
        },
        {
            "type": "user_said",
            "data": {
                "text": "Make repo public and submit, wait for my desk checkpoint confirmation."
            },
        },
        {
            "type": "checkpoint",
            "data": {
                "item_id": "agenda-03",
                "action": "PUBLIC_RELEASE_AND_SUBMIT",
                "reason": "Irreversible repository public release & hackathon submission requires 1-click confirmation"
            },
        },
        {
            "type": "checkpoint_resolved",
            "data": {
                "item_id": "agenda-03",
                "approved": True
            },
        },
        {
            "type": "agenda_item",
            "data": {
                "item_id": "agenda-04",
                "title": "Scale to All Hackathon Teams",
                "index": 4,
                "total": 4,
            },
        },
        {
            "type": "user_said",
            "data": {
                "text": "Yes, offer the morning triage call to every team at the hackathon!"
            },
        },
        {
            "type": "participants_scaled",
            "data": {
                "count": 42,
                "label": "42 Hackathon Teams Onboarded to Morning Triage Network"
            },
        },
        {
            "type": "user_said",
            "data": {
                "text": "Thanks, that is all. Ending call."
            },
        },
        {
            "type": "call_ended",
            "data": {
                "duration_s": 58
            },
        },
        {
            "type": "brief_ready",
            "data": {},
        },
    ]


OPENING = (
    "Good morning Philipp. Overnight your agents kept building DawnDispatch. "
    "I have four things for you. How much time do you have?"
)

# (delay_before_s, type, data) - delays are scaled by --fast / --instant
SCRIPT: list[tuple[float, str, dict]] = [
    (0.0, "call_started", {"opening": OPENING}),
    (5.0, "user_said", {"text": "Sixty seconds, I am almost at the office."}),
    (1.0, "time_budget", {"seconds": 60}),
    (0.8, "speed_changed", {"speed": 1.35, "reason": "sixty seconds, walking fast"}),
    (1.5, "agenda_item", {"item_id": "agenda-01", "title": "Status: Version 1 built today", "index": 1, "total": 4}),
    (4.0, "user_said", {"text": "Looks good. Nothing to flag."}),
    (1.0, "decision", {"item_id": "agenda-01", "decision": "APPROVE", "summary": "Version 1 accepted as today's milestone"}),
    (2.0, "agenda_item", {"item_id": "agenda-02", "title": "Decision: what becomes Version 2", "index": 2, "total": 4}),
    (4.5, "user_said", {"text": "Option C, my cloned voice. And the night shift should start the call."}),
    (1.0, "decision", {"item_id": "agenda-02", "decision": "AMEND", "summary": "Version 2: cloned voice, started by the night shift"}),
    (0.8, "v2_idea", {"id": "v2-cloned-voice", "title": "Cloned voice of the user", "linked_to": ["agenda-02"]}),
    (1.4, "v2_idea", {"id": "v2-night-shift", "title": "Night shift starts the call", "linked_to": ["agenda-02", "agent-hack-chef"]}),
    (2.0, "agenda_item", {"item_id": "agenda-03", "title": "Irreversible: make the repo public and submit", "index": 3, "total": 4}),
    (4.0, "user_said", {"text": "Yes. Go public and submit."}),
    (1.0, "checkpoint", {"item_id": "agenda-03", "action": "Make the repo public and submit to the hackathon",
                         "reason": "irreversible: code and history become public"}),
    # <- the script waits here for the click on the laptop (POST /api/live/checkpoint/agenda-03)
    (2.0, "agenda_item", {"item_id": "agenda-04", "title": "Scale: offer the morning call to every team", "index": 4, "total": 4}),
    (4.0, "user_said", {"text": "Yes, offer it to everyone."}),
    (1.0, "decision", {"item_id": "agenda-04", "decision": "APPROVE", "summary": "Morning call offered to all hackathon teams"}),
    (1.0, "participants_scaled", {"count": 42, "label": "teams at the hackathon"}),
    (4.0, "user_said", {"text": "That is all. Thanks, see you at the desk."}),
    (1.5, "call_ended", {}),  # duration_s is filled from the wall clock
    (2.5, "brief_ready", {}),
]


def call(base: str, method: str, path: str, body: dict | list | None = None, timeout: float = 10.0):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def checkpoint_resolved(base: str, item_id: str) -> bool:
    state = call(base, "GET", "/api/live/state")
    return any(e.get("type") == "checkpoint_resolved" and e.get("data", {}).get("item_id") == item_id for e in state.get("events", []))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base-url", default="http://127.0.0.1:8000", help="server with the live router (default: %(default)s)")
    p.add_argument("--fast", action="store_true", help="4x faster pacing, 4 s click wait")
    p.add_argument("--instant", action="store_true", help="no pacing at all (tests)")
    p.add_argument("--wait-click", type=float, default=None, help="seconds to wait for the laptop click before auto-approving (default 20, --fast 4)")
    p.add_argument("--no-reset", action="store_true", help="do not POST /api/live/reset first")
    p.add_argument("--count", type=int, default=42, help="participants_scaled count (default %(default)s)")
    a = p.parse_args(argv)

    base = a.base_url.rstrip("/")
    scale = 0.0 if a.instant else 0.25 if a.fast else 1.0
    wait_click = a.wait_click if a.wait_click is not None else (0.0 if a.instant else 4.0 if a.fast else 20.0)

    try:
        if not a.no_reset:
            call(base, "POST", "/api/live/reset")
            print("reset   /api/live/reset")
        started = time.monotonic()
        for delay, etype, data in SCRIPT:
            if delay * scale > 0:
                time.sleep(delay * scale)
            payload = dict(data)
            if etype == "participants_scaled":
                payload["count"] = a.count
            if etype == "call_ended":
                payload["duration_s"] = round(time.monotonic() - started, 1)
            call(base, "POST", "/api/live/event", {"type": etype, "data": payload})
            print(f"{time.monotonic() - started:6.1f}s  {etype:20s} {json.dumps(payload, ensure_ascii=False)[:90]}")
            if etype == "checkpoint":
                item_id = payload["item_id"]
                deadline = time.monotonic() + wait_click
                clicked = False
                while time.monotonic() < deadline:
                    if checkpoint_resolved(base, item_id):
                        clicked = True
                        break
                    time.sleep(0.5)
                if clicked:
                    print(f"{time.monotonic() - started:6.1f}s  checkpoint_resolved  (clicked on the laptop)")
                else:
                    call(base, "POST", f"/api/live/checkpoint/{item_id}", {"approved": True})
                    print(f"{time.monotonic() - started:6.1f}s  checkpoint_resolved  (auto-approved after {wait_click:.0f}s)")
        state = call(base, "GET", "/api/live/state")
        types = sorted({e.get("type") for e in state.get("events", [])})
        print(f"done: {state.get('count')} events, types: {', '.join(types)}")
        return 0
    except urllib.error.URLError as exc:
        print(f"ERROR: cannot reach {base}: {exc}", file=sys.stderr)
        print("start the server first, e.g.  uvicorn src.live.app:app --port 8000", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
