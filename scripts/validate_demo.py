#!/usr/bin/env python3
"""scripts/validate_demo.py - Automated End-to-End System Validator for DawnDispatch.

Performs local checks for:
1. Committed seed data & JSON schema validation (overnight_events, agenda, decisions, actions, graphs).
2. Core action engine, state store consistency, and irreversible checkpoint lifecycle.
3. FastAPI endpoints (/call, /dashboard, /api/graph/before, /api/graph/after, /api/actions, /api/health).
4. WebSocket route availability (/ws/call).
5. Live demo events contract adherence (12 event types per docs/LIVE-EVENTS.md).

Usage:
    python scripts/validate_demo.py
    Exit code: 0 on all checks passed, 1 on any failure.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Color helpers
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


class ValidationSuite:
    def __init__(self) -> None:
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors: list[str] = []

    def check(self, name: str, condition: bool, details: str = "") -> None:
        self.total += 1
        if condition:
            self.passed += 1
            print(f"  {GREEN}✔ [PASS]{RESET} {name}")
        else:
            self.failed += 1
            msg = f"  {RED}✘ [FAIL]{RESET} {name}"
            if details:
                msg += f" - {details}"
            print(msg)
            self.errors.append(f"{name}: {details}")

    def section(self, title: str) -> None:
        print(f"\n{BOLD}{CYAN}=== {title} ==={RESET}")


def validate_seeds(suite: ValidationSuite) -> None:
    suite.section("1. Seed Data & Schema Validation")
    data_dir = PROJECT_ROOT / "src" / "data"

    # 1. Overnight Events
    evts_file = data_dir / "overnight_events.json"
    suite.check("overnight_events.json exists", evts_file.exists())
    if evts_file.exists():
        from src.core.models import load_events
        evts = load_events(evts_file)
        suite.check("overnight_events has >= 5 events", len(evts) >= 5, f"count={len(evts)}")
        severities = {e.severity for e in evts}
        suite.check("overnight_events severities valid", severities.issubset({"INFO", "WARNING", "ERROR"}))
        suite.check("overnight_events ids start with evt-", all(e.id.startswith("evt-") for e in evts))

    # 2. Agenda Items
    agenda_file = data_dir / "agenda.json"
    suite.check("agenda.json exists", agenda_file.exists())
    if agenda_file.exists():
        from src.core.models import load_agenda
        agenda = load_agenda(agenda_file)
        suite.check("agenda has 3 to 4 items", 3 <= len(agenda) <= 4, f"count={len(agenda)}")
        irrev_items = [it for it in agenda if it.is_irreversible]
        suite.check("agenda has exactly one irreversible item", len(irrev_items) == 1, f"found={len(irrev_items)}")
        suite.check("agenda items have questions ending with '?'", all(it.question_for_lead.endswith("?") for it in agenda))

    # 3. Decisions
    dec_file = data_dir / "decisions.json"
    suite.check("decisions.json exists", dec_file.exists())
    if dec_file.exists():
        from src.core.models import load_decisions
        decs = load_decisions(dec_file)
        suite.check("decisions records valid", len(decs) >= 1)
        valid_types = {"APPROVE", "REJECT", "HOLD", "AMEND"}
        suite.check("decisions have valid decision_type", all(d.decision_type in valid_types for d in decs))

    # 4. Actions
    act_file = data_dir / "actions.json"
    suite.check("actions.json exists", act_file.exists())
    if act_file.exists():
        from src.core.models import load_actions
        acts = load_actions(act_file)
        suite.check("actions records valid", len(acts) >= 1)
        valid_statuses = {"PENDING", "EXECUTING", "COMPLETED", "BLOCKED_ON_CHECKPOINT", "FAILED"}
        suite.check("actions have valid status", all(a.status in valid_statuses for a in acts))

    # 5. Knowledge Graphs (Before / After)
    gb_file = data_dir / "knowledge_graph_before.json"
    ga_file = data_dir / "knowledge_graph_after.json"
    suite.check("knowledge_graph_before.json exists", gb_file.exists())
    suite.check("knowledge_graph_after.json exists", ga_file.exists())
    if gb_file.exists() and ga_file.exists():
        from src.core.models import load_knowledge_graph
        gb = load_knowledge_graph(gb_file)
        ga = load_knowledge_graph(ga_file)
        suite.check("graph_before has nodes and edges", len(gb.nodes) > 0 and len(gb.edges) > 0)
        suite.check("graph_after has nodes and edges", len(ga.nodes) > 0 and len(ga.edges) > 0)
        suite.check("graph_before phase is before", gb.phase == "before")
        suite.check("graph_after phase is after", ga.phase.lower() == "after" or ga.stage.lower() == "after")


def validate_checkpoint_flow(suite: ValidationSuite) -> None:
    suite.section("2. Core Engine & Checkpoint Lifecycle Flow")
    from src.core.action_engine import on_decision, execute_action
    from src.core.models import AgendaItem, DecisionRecord, ActionExecution
    from src.core import state

    with tempfile.TemporaryDirectory() as tmpdir:
        orig_env = os.environ.get("DAWN_DATA_DIR")
        os.environ["DAWN_DATA_DIR"] = tmpdir
        try:
            state.reset()
            # Setup 1 reversible item and 1 irreversible item
            rev_item = AgendaItem(
                item_id="agenda-01",
                topic="Review V1 Status",
                question_for_lead="Confirm V1 baseline? Yes or no?",
                recommended_action="APPROVE",
                is_irreversible=False,
                action_type="NOTE",
                priority=1,
            )
            irrev_item = AgendaItem(
                item_id="agenda-02",
                topic="Publish Repo & Submit",
                question_for_lead="Enable public repo and submit? Yes or no?",
                recommended_action="APPROVE",
                is_irreversible=True,
                action_type="DEPLOY",
                priority=2,
            )
            state.set_inputs(agenda=[rev_item, irrev_item])

            # 1. Reversible decision executes immediately
            d1 = DecisionRecord(item_id="agenda-01", decision_type="APPROVE", voice_notes="Confirmed by lead")
            state.add_decision(d1)
            acts1 = on_decision(d1)
            suite.check("reversible decision creates action", len(acts1) == 1)
            suite.check("reversible action completed immediately", acts1[0].status == "COMPLETED")

            # 2. Irreversible decision transitions to BLOCKED_ON_CHECKPOINT
            d2 = DecisionRecord(item_id="agenda-02", decision_type="APPROVE", voice_notes="Proceed with caution")
            state.add_decision(d2)
            acts2 = on_decision(d2)
            suite.check("irreversible decision creates action", len(acts2) == 1)
            suite.check("irreversible action status is BLOCKED_ON_CHECKPOINT", acts2[0].status == "BLOCKED_ON_CHECKPOINT")
            suite.check("irreversible action has pending_url artifact", "pending_url" in acts2[0].artifacts)
            suite.check("irreversible action has checkpoint_reason", bool(acts2[0].checkpoint_reason))

            # 3. 1-Click desktop checkpoint confirmation
            act_id = acts2[0].action_id
            state.confirm_checkpoint(act_id)
            st = state.load()
            confirmed_act = st.action(act_id)
            suite.check("confirm_checkpoint sets EXECUTING", confirmed_act is not None and confirmed_act.status == "EXECUTING")

            # 4. Execute action transitions to COMPLETED
            executed = execute_action(act_id)
            suite.check("execute_action finishes as COMPLETED", executed.status == "COMPLETED")
            suite.check("completed action contains artifacts", len(executed.artifacts) > 0)
        finally:
            if orig_env is not None:
                os.environ["DAWN_DATA_DIR"] = orig_env
            else:
                os.environ.pop("DAWN_DATA_DIR", None)


def validate_api_endpoints(suite: ValidationSuite) -> None:
    suite.section("3. FastAPI HTTP & Static Endpoints")
    from starlette.testclient import TestClient
    from src.dashboard.app import app as dash_app
    from src.voice.app import app as voice_app
    from src.app import app as main_app

    # 1. Desktop Dashboard Endpoints
    dash_client = TestClient(dash_app)
    r_dash = dash_client.get("/dashboard")
    suite.check("GET /dashboard returns HTTP 200", r_dash.status_code == 200)
    suite.check("GET /dashboard serves HTML interface", "<!DOCTYPE html>" in r_dash.text or "<html" in r_dash.text)

    r_before = dash_client.get("/api/graph/before")
    suite.check("GET /api/graph/before returns HTTP 200", r_before.status_code == 200)
    suite.check("GET /api/graph/before returns nodes & edges", "nodes" in r_before.json() and "edges" in r_before.json())

    r_after = dash_client.get("/api/graph/after")
    suite.check("GET /api/graph/after returns HTTP 200", r_after.status_code == 200)
    suite.check("GET /api/graph/after returns nodes & edges", "nodes" in r_after.json() and "edges" in r_after.json())

    r_actions = dash_client.get("/api/actions")
    suite.check("GET /api/actions returns HTTP 200", r_actions.status_code == 200)
    suite.check("GET /api/actions returns list", isinstance(r_actions.json(), list))

    r_health = dash_client.get("/api/health")
    suite.check("GET /api/health (dashboard) returns HTTP 200", r_health.status_code == 200)
    suite.check("GET /api/health returns status ok", r_health.json().get("status") == "ok")

    # 2. Voice Backend Endpoints
    voice_client = TestClient(voice_app)
    r_call = voice_client.get("/call")
    suite.check("GET /call returns HTTP 200", r_call.status_code == 200)
    suite.check("GET /call serves call HTML interface", "DawnDispatch" in r_call.text)

    r_agenda = voice_client.get("/api/agenda")
    suite.check("GET /api/agenda (voice) returns HTTP 200", r_agenda.status_code == 200)
    suite.check("GET /api/agenda returns list", isinstance(r_agenda.json(), list))

    r_trans = voice_client.get("/api/transcript")
    suite.check("GET /api/transcript returns HTTP 200", r_trans.status_code == 200)

    # 3. Main Unified Entrypoint
    main_client = TestClient(main_app)
    r_main_health = main_client.get("/api/health")
    suite.check("GET /api/health (unified app) returns HTTP 200", r_main_health.status_code == 200)
    r_root = main_client.get("/", follow_redirects=False)
    suite.check("GET / redirects to /dashboard", r_root.status_code in (302, 307) and "/dashboard" in r_root.headers.get("location", ""))


def validate_websocket_and_live_events(suite: ValidationSuite) -> None:
    suite.section("4. WebSocket Routes & Live Events Simulator")
    from src.voice.app import app as voice_app
    from tools.live_demo_events import get_demo_events, format_event, EVENT_TYPES

    # 1. WebSocket Route Detection
    ws_routes = [r.path for r in voice_app.routes if type(r).__name__ == "APIWebSocketRoute"]
    suite.check("WebSocket route /ws/call exists in voice app", "/ws/call" in ws_routes, f"routes={ws_routes}")

    # 2. Live Demo Event Types Compliance (12 events per docs/LIVE-EVENTS.md)
    expected_types = {
        "call_started", "time_budget", "speed_changed", "agenda_item",
        "user_said", "decision", "checkpoint", "checkpoint_resolved",
        "v2_idea", "participants_scaled", "call_ended", "brief_ready"
    }
    suite.check("All 12 live event types are registered", expected_types.issubset(set(EVENT_TYPES)))

    # 3. Live Demo Flow Verification
    demo_events = get_demo_events()
    suite.check("get_demo_events returns structured event list", len(demo_events) >= 10)
    event_sequence = [e["type"] for e in demo_events]
    suite.check("Event sequence starts with call_started", event_sequence[0] == "call_started")
    suite.check("Event sequence contains time_budget", "time_budget" in event_sequence)
    suite.check("Event sequence contains speed_changed", "speed_changed" in event_sequence)
    suite.check("Event sequence contains checkpoint & resolution", "checkpoint" in event_sequence and "checkpoint_resolved" in event_sequence)
    suite.check("Event sequence contains participants_scaled", "participants_scaled" in event_sequence)
    suite.check("Event sequence ends with call_ended and brief_ready", event_sequence[-2] == "call_ended" and event_sequence[-1] == "brief_ready")


def main() -> int:
    start_time = time.time()
    print(f"{BOLD}DawnDispatch Live Demo Validation & Pre-Flight Check{RESET}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())}")
    print(f"Root: {PROJECT_ROOT}")

    suite = ValidationSuite()
    try:
        validate_seeds(suite)
        validate_checkpoint_flow(suite)
        validate_api_endpoints(suite)
        validate_websocket_and_live_events(suite)
    except Exception as exc:
        print(f"\n{RED}UNCAUGHT EXCEPTION during validation: {exc}{RESET}")
        import traceback
        traceback.print_exc()
        return 1

    elapsed = time.time() - start_time
    print(f"\n{BOLD}{CYAN}=== Summary ==={RESET}")
    print(f"Total Checks: {suite.total}")
    print(f"Passed:       {GREEN}{suite.passed}{RESET}")
    print(f"Failed:       {RED if suite.failed > 0 else GREEN}{suite.failed}{RESET}")
    print(f"Duration:     {elapsed:.2f} s")

    if suite.failed == 0:
        print(f"\n{GREEN}{BOLD}✔ ALL PRE-FLIGHT DEMO CHECKS PASSED. READY FOR WALKTHROUGH & VIDEO RECORDING!{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{BOLD}✘ {suite.failed} CHECK(S) FAILED. Please review the errors above.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
