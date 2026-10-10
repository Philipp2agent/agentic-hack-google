#!/usr/bin/env python3
"""tools/live_demo_events.py - Emit Demo-Agenda events per docs/LIVE-EVENTS.md.

Simulates the voice session event sequence driving the live screen (/live)
without requiring an actual audio call. Can output JSON lines, save to
src/data/live_session.jsonl, or stream over WebSocket / HTTP.

Usage:
    python3 tools/live_demo_events.py [--delay SECONDS] [--out FILE] [--ws URL] [--http URL]
"""
import argparse
import asyncio
from datetime import datetime, timezone
import json
import sys
import time
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


def get_demo_events() -> list[dict]:
    """Return the sequential list of live events for the demo agenda."""
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
                "linked_to": "agenda-02"
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


def format_event(raw: dict) -> dict:
    return {
        "type": raw["type"],
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data": raw.get("data", {}),
    }


def send_http(url: str, event: dict) -> None:
    data = json.dumps(event).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except Exception as e:
        sys.stderr.write(f"HTTP POST to {url} failed: {e}\n")


async def run_events(args) -> None:
    events = get_demo_events()
    out_file = open(args.out, "w", encoding="utf-8") if args.out else None

    # Check for in-process bus
    bus_publish = None
    if not args.http and not args.ws:
        try:
            from src.live.bus import publish
            bus_publish = publish
        except ImportError:
            bus_publish = None

    try:
        for raw in events:
            ev = format_event(raw)
            line = json.dumps(ev)

            # 1. Output stdout
            print(line, flush=True)

            # 2. Write to session jsonl if requested
            if out_file:
                out_file.write(line + "\n")
                out_file.flush()

            # 3. In-process bus if available
            if bus_publish:
                try:
                    res = bus_publish(ev)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as e:
                    sys.stderr.write(f"In-process publish failed: {e}\n")

            # 4. HTTP POST if target url provided
            if args.http:
                send_http(args.http, ev)

            # Delay
            if args.delay > 0:
                await asyncio.sleep(args.delay)
    finally:
        if out_file:
            out_file.close()


def main():
    parser = argparse.ArgumentParser(description="Emit live demo events per docs/LIVE-EVENTS.md")
    parser.add_argument("--delay", type=float, default=0.0, help="Delay in seconds between events (default 0.0)")
    parser.add_argument("--out", type=str, default=None, help="Path to write JSONL events (e.g. src/data/live_session.jsonl)")
    parser.add_argument("--http", type=str, default=None, help="HTTP URL to POST events to")
    parser.add_argument("--ws", type=str, default=None, help="WebSocket URL to send events to")
    args = parser.parse_args()

    asyncio.run(run_events(args))


if __name__ == "__main__":
    main()
