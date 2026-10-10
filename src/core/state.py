"""State store for DawnDispatch over the JSON files in src/data/ (claude-02).

Files (layout from docs/SCHNITTSTELLE.md, each a JSON list unless noted):
  overnight_events.json  inputs, written by src/core/repo_events.py (hack-bau1)
  agenda.json            inputs, written by src/core/action_engine.py (hack-bau1)
  decisions.json         appended by the voice tools / post-call processor
  actions.json           written by the action engine, confirmed by the dashboard
  call.json              CallRecord object (transcript, briefing, time budget)
  meta.json              free dict (gemini interaction ids, budgets, checkpoint reasons)

Everyone reads/writes through these functions, never the files directly.
Thread-safe within one process (voice + dashboard run in one uvicorn app).
Tests MUST point DAWN_DATA_DIR at a temp directory (see tests/test_contract.py),
otherwise they dirty the committed seeds.

CLI:  python -m src.core.state --show | --json
      python -m src.core.state --reset   # clear decisions/actions/call/meta (keeps events + agenda)
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import tempfile
import threading
from typing import Any, Callable

from src.core.models import (
    ActionExecution,
    ActionStatus,
    AgendaItem,
    CallRecord,
    DawnState,
    DecisionRecord,
    OvernightEvent,
    TranscriptTurn,
    now_iso,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "src" / "data"

_lock = threading.RLock()


def data_dir() -> pathlib.Path:
    return pathlib.Path(os.environ.get("DAWN_DATA_DIR") or DEFAULT_DATA_DIR)


FILES = {
    "events": "overnight_events.json",
    "agenda": "agenda.json",
    "decisions": "decisions.json",
    "actions": "actions.json",
    "call": "call.json",
    "meta": "meta.json",
}


def _read(name: str, default: Any) -> Any:
    path = data_dir() / FILES[name]
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    return json.loads(text) if text else default


def _write(name: str, payload: Any) -> None:
    d = data_dir()
    d.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, d / FILES[name])  # atomic on POSIX


# --- load / save -------------------------------------------------------------------
def load() -> DawnState:
    with _lock:
        return DawnState(
            events=[OvernightEvent.model_validate(x) for x in _read("events", [])],
            agenda=[AgendaItem.model_validate(x) for x in _read("agenda", [])],
            decisions=[DecisionRecord.model_validate(x) for x in _read("decisions", [])],
            actions=[ActionExecution.model_validate(x) for x in _read("actions", [])],
            call=CallRecord.model_validate(_read("call", {})),
            meta=_read("meta", {}),
        )


def save(state: DawnState, *, inputs: bool = False) -> None:
    """Persist decisions/actions/call/meta; with inputs=True also events + agenda."""
    with _lock:
        if inputs:
            _write("events", [e.model_dump() for e in state.events])
            _write("agenda", [a.model_dump() for a in state.agenda])
        _write("decisions", [d.model_dump() for d in state.decisions])
        _write("actions", [a.model_dump() for a in state.actions])
        _write("call", state.call.model_dump())
        _write("meta", state.meta)


def reset() -> DawnState:
    """Demo reset: no decisions, no actions, idle call, empty meta. Events + agenda stay."""
    with _lock:
        state = load()
        state.decisions, state.actions, state.call, state.meta = [], [], CallRecord(), {}
        save(state)
        return state


def update(fn: Callable[[DawnState], Any], *, inputs: bool = False) -> Any:
    """Run fn(state) under the lock and persist. Returns fn's result."""
    with _lock:
        state = load()
        result = fn(state)
        save(state, inputs=inputs)
        return result


def set_inputs(events: list[OvernightEvent] | None = None, agenda: list[AgendaItem] | None = None) -> None:
    """Used by the action engine after aggregation / synthesis."""
    def _do(state: DawnState):
        if events is not None:
            state.events = events
        if agenda is not None:
            state.agenda = sorted(agenda, key=lambda a: a.priority)
    update(_do, inputs=True)


# --- decisions / actions ----------------------------------------------------------------
def add_decision(record: DecisionRecord) -> DecisionRecord:
    """Append a decision (the latest decision per item wins when read)."""
    def _do(state: DawnState):
        state.decisions.append(record)
        return record
    return update(_do)


def latest_decision(state: DawnState, item_id: str) -> DecisionRecord | None:
    for rec in reversed(state.decisions):
        if rec.item_id == item_id:
            return rec
    return None


def add_action(action: ActionExecution) -> ActionExecution:
    def _do(state: DawnState):
        state.actions.append(action)
        return action
    return update(_do)


def set_action_status(
    action_id: str,
    status: ActionStatus,
    artifacts: dict[str, Any] | None = None,
    checkpoint_reason: str | None = None,
) -> ActionExecution:
    def _do(state: DawnState):
        action = state.action(action_id)
        if action is None:
            raise KeyError(f"unknown action_id {action_id}")
        action.status = status
        action.updated_at = now_iso()
        if artifacts:
            action.artifacts.update(artifacts)
        if checkpoint_reason is not None:
            action.checkpoint_reason = checkpoint_reason
        return action
    return update(_do)


def confirm_checkpoint(action_id: str) -> ActionExecution:
    """Human clicked: BLOCKED_ON_CHECKPOINT -> EXECUTING, latest decision human_verified.

    The caller (dashboard) then runs src.core.action_engine.execute_action(action_id),
    which moves it to COMPLETED/FAILED and fills artifacts.
    """
    def _do(state: DawnState):
        action = state.action(action_id)
        if action is None:
            raise KeyError(f"unknown action_id {action_id}")
        if action.status != "BLOCKED_ON_CHECKPOINT":
            raise ValueError(f"action {action_id} is {action.status}, not BLOCKED_ON_CHECKPOINT")
        action.status = "EXECUTING"
        action.updated_at = now_iso()
        action.artifacts["confirmed_at"] = now_iso()
        rec = latest_decision(state, action.item_id)
        if rec is not None:
            rec.human_verified = True
        return action
    return update(_do)


def set_meta(key: str, value: Any) -> None:
    update(lambda s: s.meta.__setitem__(key, value))


# --- call -------------------------------------------------------------------------------
def start_call(language: str = "en", voice_id: str | None = None) -> None:
    def _do(state: DawnState):
        state.call = CallRecord(status="live", started_at=now_iso(), language=language, voice_id=voice_id)
    update(_do)


def set_time_budget(seconds: int) -> None:
    update(lambda s: setattr(s.call, "time_budget_s", int(seconds)))


def append_turn(turn: TranscriptTurn) -> None:
    update(lambda s: s.call.transcript.append(turn))


def end_call(briefing: list[str] | None = None, audio_url: str | None = None) -> None:
    def _do(state: DawnState):
        state.call.status = "ended"
        state.call.ended_at = now_iso()
        if briefing is not None:
            state.call.briefing = briefing
        if audio_url is not None:
            state.call.audio_url = audio_url
    update(_do)


# --- CLI ------------------------------------------------------------------------------------
def summary(state: DawnState) -> str:
    blocked = [a for a in state.actions if a.status == "BLOCKED_ON_CHECKPOINT"]
    return (
        f"events={len(state.events)} agenda={len(state.agenda)} decisions={len(state.decisions)} "
        f"actions={len(state.actions)} blocked_on_checkpoint={len(blocked)} call={state.call.status}"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--reset", action="store_true", help="clear decisions/actions/call/meta (keeps events + agenda)")
    p.add_argument("--show", action="store_true", help="print a one-line summary")
    p.add_argument("--json", action="store_true", help="print the full state as JSON")
    a = p.parse_args()
    if a.reset:
        print("RESET:", data_dir())
        reset()
    st = load()
    print(json.dumps(st.model_dump(), indent=2) if a.json else "STATE: " + summary(st))
