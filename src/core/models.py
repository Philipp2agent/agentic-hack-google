"""Data models for DawnDispatch core swarm, voice, and dashboard.

Defined according to docs/SCHNITTSTELLE.md and IDEE.md.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Literal
from pydantic import BaseModel, Field


SeverityType = Literal["INFO", "WARNING", "ERROR"]
DecisionType = Literal["APPROVE", "REJECT", "HOLD", "AMEND"]
ActionStatusType = Literal["PENDING", "EXECUTING", "COMPLETED", "BLOCKED_ON_CHECKPOINT"]
GraphStageType = Literal["BEFORE", "AFTER"]


class OvernightEvent(BaseModel):
    """Event from overnight swarm agent activity (git commits, PRs, agent logs)."""

    id: str = Field(description="Unique event ID, e.g. 'evt-001'")
    source: str = Field(description="Origin source, e.g. 'git commit 3cdd23d' or 'PR #4'")
    agent_id: str = Field(description="Executing agent ID, e.g. 'hack-bau1'")
    title: str = Field(description="Concise event title")
    details: str = Field(description="Detailed description of status or outcome")
    severity: SeverityType = Field(default="INFO", description="Event severity: INFO, WARNING, ERROR")
    proposed_action: str = Field(description="Proposed follow-up action")


class AgendaItem(BaseModel):
    """Discussion item synthesized for the morning voice call (max 3 items)."""

    item_id: str = Field(description="Unique agenda item ID, e.g. 'agenda-01'")
    topic: str = Field(description="Topic title")
    question_for_lead: str = Field(description="Crisp question for the lead during call")
    recommended_action: str = Field(description="Recommended action by system")
    is_irreversible: bool = Field(default=False, description="Whether action has irreversible impact")


class DecisionRecord(BaseModel):
    """Decision captured during voice call via log_decision tool."""

    item_id: str = Field(description="Referenced agenda item ID")
    decision_type: DecisionType = Field(description="Decision outcome: APPROVE, REJECT, HOLD, AMEND")
    voice_notes: str = Field(default="", description="Summary/notes from lead voice interaction")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        description="ISO-8601 UTC timestamp",
    )
    human_verified: bool = Field(default=True, description="Whether verified by human lead")


class ActionExecution(BaseModel):
    """Execution state of follow-up actions derived from decisions."""

    action_id: str = Field(description="Unique action ID, e.g. 'act-101'")
    item_id: str = Field(description="Referenced agenda item ID")
    action_type: str = Field(description="Action identifier / type code")
    status: ActionStatusType = Field(default="PENDING", description="Execution status")
    artifacts: dict[str, Any] = Field(default_factory=dict, description="Artifacts, logs, links, ports")


class GraphNode(BaseModel):
    """Node in the DawnDispatch Knowledge Graph."""

    id: str = Field(description="Unique node ID")
    label: str = Field(description="Display label")
    type: str = Field(description="Node type: agent, event, agenda, decision, action, resource")
    status: str = Field(default="UNRESOLVED", description="Node status, e.g. UNRESOLVED, BLOCKED, RESOLVED, COMPLETED")
    details: str = Field(default="", description="Detailed node description")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom node metadata")


class GraphEdge(BaseModel):
    """Directed edge in the DawnDispatch Knowledge Graph."""

    source: str = Field(description="Source node ID")
    target: str = Field(description="Target node ID")
    relation: str = Field(description="Edge relation: e.g. PRODUCED, TRIGGERS, DECIDED_BY, DISPATCHES")
    status: str = Field(default="PENDING", description="Edge status: PENDING, RESOLVED, BLOCKED")


class KnowledgeGraph(BaseModel):
    """Before/After Knowledge Graph for commute triage and dashboard visualization."""

    stage: GraphStageType = Field(default="BEFORE", description="Graph stage: BEFORE or AFTER call")
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        description="ISO-8601 UTC timestamp",
    )
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


def load_events(path: Path | str) -> list[OvernightEvent]:
    p = Path(path)
    if not p.exists():
        return []
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [OvernightEvent.model_validate(item) for item in data]


def save_events(events: list[OvernightEvent], path: Path | str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in events], f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_agenda(path: Path | str) -> list[AgendaItem]:
    p = Path(path)
    if not p.exists():
        return []
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [AgendaItem.model_validate(item) for item in data]


def save_agenda(agenda: list[AgendaItem], path: Path | str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in agenda], f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_decisions(path: Path | str) -> list[DecisionRecord]:
    p = Path(path)
    if not p.exists():
        return []
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [DecisionRecord.model_validate(item) for item in data]


def save_decisions(decisions: list[DecisionRecord], path: Path | str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in decisions], f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_actions(path: Path | str) -> list[ActionExecution]:
    p = Path(path)
    if not p.exists():
        return []
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [ActionExecution.model_validate(item) for item in data]


def save_actions(actions: list[ActionExecution], path: Path | str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in actions], f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_knowledge_graph(path: Path | str) -> KnowledgeGraph:
    p = Path(path)
    if not p.exists():
        return KnowledgeGraph()
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return KnowledgeGraph.model_validate(data)


def save_knowledge_graph(graph: KnowledgeGraph, path: Path | str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(graph.model_dump(), f, indent=2, ensure_ascii=False)
        f.write("\n")
