"""DawnDispatch data contract (claude-02; supersedes nothing, formalises docs/SCHNITTSTELLE.md).

Field names, enum values and the JSON files under src/data/ are the interface between
src/core (hack-bau1), src/voice (hack-bau2) and src/dashboard (hack-bau3).
Rule: extend with optional fields, never rename or remove anything.
Only hack-bau1 edits this file; everyone else imports it.

Compatibility with docs/SCHNITTSTELLE.md and the seeds in src/data/*.json:
- OvernightEvent.source is free text ("git commit 3cdd23d", "PR #4"), severity INFO|WARNING|ERROR.
- AgendaItem adds optional action_type / event_ids / priority (defaults, so seeds validate).
- DecisionRecord adds decision_id / source (defaults).
- ActionExecution.artifacts is a free JSON object; recommended keys in ARTIFACT_KEYS.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

# --- vocabularies ------------------------------------------------------------
Severity = Literal["INFO", "WARNING", "ERROR"]
DecisionType = Literal["APPROVE", "REJECT", "HOLD", "AMEND"]
DecisionSource = Literal["voice_tool", "post_call", "dashboard"]
ActionStatus = Literal["PENDING", "EXECUTING", "COMPLETED", "BLOCKED_ON_CHECKPOINT", "FAILED"]
CallStatus = Literal["idle", "ringing", "live", "ended"]
TurnRole = Literal["agent", "user", "tool"]
GraphPhase = Literal["before", "after"]
NodeKind = Literal["agent", "event", "agenda", "decision", "action", "checkpoint"]
NodeStatus = Literal["open", "blocked", "resolved", "info"]

# Recommended action_type vocabulary (plain str in the model: seeds use their own names,
# e.g. DEPLOY_VOICE_SERVICE). Irreversibility is decided by AgendaItem.is_irreversible.
ACTION_TYPES = (
    "MERGE_BRANCH",    # reversible: preview merge of an agent branch (artifact: diff)
    "DISPATCH_AGENT",  # reversible: write a task file for an agent (artifact: file)
    "RUN_TESTS",       # reversible: run the test suite (artifact: log)
    "UPDATE_BUDGET",   # reversible: change a quota/budget value (artifact: note)
    "NOTE",            # reversible: record a note only
    "DELETE_FILES",    # irreversible: delete files from the repo
    "TAG_RELEASE",     # irreversible: tag / publish a release
    "PUBLISH_ASSET",   # irreversible: publish an asset publicly
    "DEPLOY",          # irreversible: deploy to a shared environment
)
IRREVERSIBLE_ACTION_TYPES = frozenset({"DELETE_FILES", "TAG_RELEASE", "PUBLISH_ASSET", "DEPLOY"})

# Recommended keys inside ActionExecution.artifacts (all optional, all strings unless noted):
ARTIFACT_KEYS = (
    "diff",         # unified diff or diff --stat text (dashboard renders in <pre>)
    "log",          # command output / logs
    "logs",         # alias used by the seeds
    "commit",       # commit sha
    "url",          # link (PR, commit, file)
    "file",         # repo-relative path written by the action
    "note",         # free text
    "reason",       # why the action is blocked / failed
    "pending_url",  # dashboard route of the checkpoint
    "port",         # int, from the seeds
)


def now_iso() -> str:
    """UTC timestamp, ISO 8601, second precision."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# --- core records (src/data/overnight_events.json, agenda.json, decisions.json, actions.json) ---
class OvernightEvent(BaseModel):
    """One thing that happened in the repo / agent swarm overnight."""

    id: str  # evt-001
    source: str  # free text: "git commit 3cdd23d", "PR #4", "agent log / STAND.md update"
    agent_id: str  # hack-bau1, hack-visual, hack-chef, claude-cloud, philipp
    title: str
    details: str = ""
    severity: Severity = "INFO"
    proposed_action: str = ""
    timestamp: str | None = None
    ref: str | None = None  # commit sha, PR url, file path (machine-readable form of source)


class AgendaItem(BaseModel):
    """One question the morning call asks the lead (max 3 per call)."""

    item_id: str  # agenda-01
    topic: str
    question_for_lead: str
    recommended_action: str
    is_irreversible: bool = False  # authoritative for the human checkpoint
    action_type: str = "NOTE"  # see ACTION_TYPES (hint for the action engine)
    event_ids: list[str] = Field(default_factory=list)
    priority: int = 1  # 1 = asked first


class DecisionRecord(BaseModel):
    """A decision the lead made (by voice, post-call extraction or dashboard)."""

    item_id: str
    decision_type: DecisionType
    voice_notes: str = ""
    timestamp: str = Field(default_factory=now_iso)
    human_verified: bool = False  # True once confirmed by a dashboard click
    decision_id: str = Field(default_factory=lambda: new_id("dec"))
    source: DecisionSource = "voice_tool"


class ActionExecution(BaseModel):
    """Downstream work derived from a decision. Irreversible ones wait on a checkpoint."""

    action_id: str = Field(default_factory=lambda: new_id("act"))  # act-101
    item_id: str
    action_type: str  # see ACTION_TYPES
    status: ActionStatus = "PENDING"
    artifacts: dict[str, Any] = Field(default_factory=dict)  # see ARTIFACT_KEYS
    description: str = ""
    checkpoint_reason: str | None = None  # why a human click is required
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


# --- call (src/data/call.json) -------------------------------------------------
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
    time_budget_s: int | None = None  # answer to "How much time do you have?"
    transcript: list[TranscriptTurn] = Field(default_factory=list)
    audio_url: str | None = None  # e.g. /data/audio/last_call.wav (optional)
    briefing: list[str] = Field(default_factory=list)  # 3-bullet standup summary


# --- knowledge graph (derived view, GET /api/graph?phase=before|after) ---------------
class GraphNode(BaseModel):
    id: str  # same id as the underlying record (agent name, evt-001, agenda-01, dec-.., act-..)
    label: str
    kind: NodeKind
    status: NodeStatus = "info"  # open=yellow/red, blocked=amber, resolved=green, info=grey
    data: dict[str, Any] = Field(default_factory=dict)  # severity, decision_type, action status, ...


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str = ""


class KnowledgeGraph(BaseModel):
    phase: GraphPhase
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    generated_at: str = Field(default_factory=now_iso)


# --- whole state (in-memory aggregate of the files under src/data/) ----------------
class DawnState(BaseModel):
    generated_at: str = Field(default_factory=now_iso)
    events: list[OvernightEvent] = Field(default_factory=list)
    agenda: list[AgendaItem] = Field(default_factory=list)
    decisions: list[DecisionRecord] = Field(default_factory=list)
    actions: list[ActionExecution] = Field(default_factory=list)
    call: CallRecord = Field(default_factory=CallRecord)
    meta: dict[str, Any] = Field(default_factory=dict)  # interaction ids, budgets, checkpoint reasons

    def item(self, item_id: str) -> AgendaItem | None:
        return next((a for a in self.agenda if a.item_id == item_id), None)

    def action(self, action_id: str) -> ActionExecution | None:
        return next((a for a in self.actions if a.action_id == action_id), None)
