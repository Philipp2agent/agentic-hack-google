"""JSON state store for DawnDispatch (frozen by claude-02).

Single source of truth at runtime: src/data/state.json (git-ignored).
All three packages use these functions; none of them writes the file directly.
Thread-safe within one process (voice + dashboard run in the same uvicorn app).

CLI:  python -m src.core.state --reset   # copy state.example.json -> state.json
      python -m src.core.state --show    # print a short summary
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import tempfile
import threading

from src.core.models import (
    ActionExecution,
    ActionStatus,
    Artifact,
    DawnState,
    DecisionRecord,
    TranscriptTurn,
    now_iso,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "src" / "data"
EXAMPLE_PATH = DATA_DIR / "state.example.json"
STATE_PATH = pathlib.Path(os.environ.get("DAWN_STATE_PATH") or DATA_DIR / "state.json")

_lock = threading.RLock()


# --- load / save ----------------------------------------------------------------
def load() -> DawnState:
    """Load state.json; falls back to the example (without writing) when missing."""
    with _lock:
        path = STATE_PATH if STATE_PATH.exists() else EXAMPLE_PATH
        return DawnState.model_validate_json(path.read_text(encoding="utf-8"))


def save(state: DawnState) -> None:
    with _lock:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=STATE_PATH.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(state.model_dump_json(indent=2))
        os.replace(tmp, STATE_PATH)  # atomic on POSIX


def reset(from_path: pathlib.Path | None = None) -> DawnState:
    """Replace state.json with the example (or the given file)."""
    with _lock:
        src = from_path or EXAMPLE_PATH
        state = DawnState.model_validate_json(src.read_text(encoding="utf-8"))
        state.generated_at = now_iso()
        save(state)
        return state


def update(fn):
    """Run fn(state) under the lock and persist. Returns fn's result."""
    with _lock:
        state = load()
        result = fn(state)
        save(state)
        return result


# --- decisions / actions ------------------------------------------------------------
def add_decision(record: DecisionRecord) -> DecisionRecord:
    """Append a decision (latest decision per item wins when read)."""
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
    artifacts: list[Artifact] | None = None,
    checkpoint_reason: str | None = None,
) -> ActionExecution:
    def _do(state: DawnState):
        action = state.action(action_id)
        if action is None:
            raise KeyError(f"unknown action_id {action_id}")
        action.status = status
        action.updated_at = now_iso()
        if artifacts:
            action.artifacts.extend(artifacts)
        if checkpoint_reason is not None:
            action.checkpoint_reason = checkpoint_reason
        return action
    return update(_do)


def confirm_checkpoint(action_id: str) -> ActionExecution:
    """Human clicked the checkpoint: BLOCKED_ON_CHECKPOINT -> EXECUTING, decision verified.

    The caller (dashboard) then runs src.core.action_engine.execute_action(action_id)
    which moves it to COMPLETED/FAILED and attaches artifacts.
    """
    def _do(state: DawnState):
        action = state.action(action_id)
        if action is None:
            raise KeyError(f"unknown action_id {action_id}")
        if action.status != "BLOCKED_ON_CHECKPOINT":
            raise ValueError(f"action {action_id} is {action.status}, not BLOCKED_ON_CHECKPOINT")
        action.status = "EXECUTING"
        action.updated_at = now_iso()
        rec = latest_decision(state, action.item_id)
        if rec is not None:
            rec.human_verified = True
        action.artifacts.append(Artifact(kind="text", label="Human checkpoint", content=f"Confirmed on dashboard at {now_iso()}"))
        return action
    return update(_do)


# --- call ---------------------------------------------------------------------------
def start_call(language: str = "en", voice_id: str | None = None) -> None:
    def _do(state: DawnState):
        state.call.status = "live"
        state.call.started_at = now_iso()
        state.call.ended_at = None
        state.call.language = language
        state.call.voice_id = voice_id
        state.call.transcript = []
        state.call.briefing = []
        state.call.audio_url = None
    update(_do)


def append_turn(turn: TranscriptTurn) -> None:
    def _do(state: DawnState):
        state.call.transcript.append(turn)
    update(_do)


def end_call(briefing: list[str] | None = None, audio_url: str | None = None) -> None:
    def _do(state: DawnState):
        state.call.status = "ended"
        state.call.ended_at = now_iso()
        if briefing is not None:
            state.call.briefing = briefing
        if audio_url is not None:
            state.call.audio_url = audio_url
    update(_do)


# --- CLI ---------------------------------------------------------------------------------
def _summary(state: DawnState) -> str:
    blocked = [a for a in state.actions if a.status == "BLOCKED_ON_CHECKPOINT"]
    return (
        f"events={len(state.events)} agenda={len(state.agenda)} decisions={len(state.decisions)} "
        f"actions={len(state.actions)} blocked_on_checkpoint={len(blocked)} call={state.call.status}"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--reset", action="store_true", help="copy state.example.json to state.json")
    p.add_argument("--show", action="store_true", help="print a summary of the current state")
    p.add_argument("--json", action="store_true", help="print the full state as JSON")
    a = p.parse_args()
    if a.reset:
        print("RESET:", STATE_PATH, "<-", EXAMPLE_PATH)
        reset()
    st = load()
    if a.json:
        print(json.dumps(st.model_dump(), indent=2))
    else:
        print("STATE:", _summary(st))
