"""DawnDispatch data contract (frozen by claude-02, see docs/ARCHITEKTUR.md section 2).

Field names, enum values and the JSON layout are the interface between
src/core (hack-bau1), src/voice (hack-bau2) and src/dashboard (hack-bau3).
Rule: extend with optional fields, never rename or remove anything.
Only hack-bau1 edits this file; everyone else imports it.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

# --- vocabularies ------------------------------------------------------------
EventSource = Literal["git_commit", "pull_request", "agent_log", "board", "asset", "manual"]
Severity = Literal["info", "low", "medium", "high", "critical"]
DecisionType = Literal["APPROVE", "REJECT", "HOLD", "AMEND"]
DecisionSource = Literal["voice_tool", "post_call", "dashboard"]
ActionStatus = Literal["PENDING", "EXECUTING", "COMPLETED", "BLOCKED_ON_CHECKPOINT", "FAILED"]
ArtifactKind = Literal["diff", "commit", "link", "log", "file", "text"]
CallStatus = Literal["idle", "live", "ended"]
TurnRole = Literal["agent", "user", "tool"]

# Recommended action_type vocabulary. Kept as plain str in the models so a new
# type needs no contract change; the action engine (hack-bau1) implements them.
ACTION_TYPES = (
    "MERGE_BRANCH",    # reversible: merge an agent branch into main (artifact: diff stat)
    "DISPATCH_AGENT",  # reversible: write a task file for an agent (artifact: file)
    "RUN_TESTS",       # reversible: run the test suite (artifact: log)
    "UPDATE_BUDGET",   # reversible: change a quota/budget value (artifact: text)
    "NOTE",            # reversible: record a note only
    "DELETE_FILES",    # IRREVERSIBLE: delete files from the repo
    "TAG_RELEASE",     # IRREVERSIBLE: tag / publish a release
    "PUBLISH_ASSET",   # IRREVERSIBLE: publish an asset publicly
)
IRREVERSIBLE_ACTION_TYPES = frozenset({"DELETE_FILES", "TAG_RELEASE", "PUBLISH_ASSET"})


def now_iso() -> str:
    """UTC timestamp, ISO 8601, second precision (the only timestamp format in the state)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# --- core records -----------------------------------------------------------
class OvernightEvent(BaseModel):
    """One thing that happened in the repo / agent swarm overnight."""

    id: str
    source: EventSource
    agent_id: str  # hack-bau1, hack-visual, hack-chef, claude-cloud, philipp, ...
    title: str
    details: str = ""
    severity: Severity = "info"
    proposed_action: str = ""
    timestamp: str = Field(default_factory=now_iso)
    ref: str | None = None  # commit sha, PR url, file path


class AgendaItem(BaseModel):
    """One question the morning call asks the lead (max 3 per call)."""

    item_id: str
    topic: str
    question_for_lead: str
    recommended_action: str
    is_irreversible: bool = False
    action_type: str = "NOTE"  # see ACTION_TYPES
    event_ids: list[str] = Field(default_factory=list)
    priority: int = 1  # 1 = asked first


class DecisionRecord(BaseModel):
    """A decision the lead made (by voice, post-call extraction or dashboard)."""

    decision_id: str = Field(default_factory=lambda: new_id("dec"))
    item_id: str
    decision_type: DecisionType
    voice_notes: str = ""
    timestamp: str = Field(default_factory=now_iso)
    human_verified: bool = False  # True once confirmed by a dashboard click
    source: DecisionSource = "voice_tool"


class Artifact(BaseModel):
    kind: ArtifactKind = "text"
    label: str
    content: str = ""  # diff text, log output, note
    url: str | None = None  # commit / PR / file link


class ActionExecution(BaseModel):
    """Downstream work derived from a decision. Irreversible ones wait on a checkpoint."""

    action_id: str = Field(default_factory=lambda: new_id("act"))
    item_id: str
    action_type: str  # see ACTION_TYPES
    status: ActionStatus = "PENDING"
    description: str = ""
    artifacts: list[Artifact] = Field(default_factory=list)
    checkpoint_reason: str | None = None  # why a human click is required
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


# --- call ----------------------------------------------------------------------
class TranscriptTurn(BaseModel):
    role: TurnRole
    text: str
    t_s: float | None = None  # seconds since call start (gradbot stop_s)
    turn_idx: int | None = None


class CallRecord(BaseModel):
    status: CallStatus = "idle"
    started_at: str | None = None
    ended_at: str | None = None
    language: str = "en"
    voice_id: str | None = None
    transcript: list[TranscriptTurn] = Field(default_factory=list)
    audio_url: str | None = None  # e.g. /data/audio/last_call.wav (optional)
    briefing: list[str] = Field(default_factory=list)  # 3-bullet standup summary


# --- whole state -----------------------------------------------------------------
class DawnState(BaseModel):
    """Everything the system knows; persisted as src/data/state.json."""

    version: int = 1
    generated_at: str = Field(default_factory=now_iso)
    events: list[OvernightEvent] = Field(default_factory=list)
    agenda: list[AgendaItem] = Field(default_factory=list)
    decisions: list[DecisionRecord] = Field(default_factory=list)
    actions: list[ActionExecution] = Field(default_factory=list)
    call: CallRecord = Field(default_factory=CallRecord)
    meta: dict[str, str] = Field(default_factory=dict)  # free-form: gemini interaction ids, budgets, checkpoint reasons

    def item(self, item_id: str) -> AgendaItem | None:
        return next((a for a in self.agenda if a.item_id == item_id), None)

    def action(self, action_id: str) -> ActionExecution | None:
        return next((a for a in self.actions if a.action_id == action_id), None)
