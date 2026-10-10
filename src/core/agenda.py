"""DawnDispatch Agenda Engine & Schnellfeuer Triage Catalog (v1 -> v2).

Defines the morning commute quick-fire agenda transitioning Version 1
(built today: simulated web call on Meta Ray-Ban glasses, before/after graph)
into Version 2 (WhatsApp Calling, autonome Night Shift, Voice Clone, Build Pipeline).

Core Leitsatz: 'The agent owns the code and the human.'
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence

from src.core import state
from src.core.models import AgendaItem, load_agenda, save_agenda

SLOGAN = "The agent owns the code and the human"

TOPICS_V1_TO_V2 = (
    "WhatsApp Calling",
    "autonome Night Shift",
    "Voice Clone",
    "Build Pipeline",
)

V1_SUMMARY = (
    "Version 1 built today: simulated web incoming call via HTTPS tunnel, "
    "audio through Meta Ray-Ban smart glasses via Bluetooth, Gradium low-latency voice, "
    "and interactive Before/After Knowledge Graph with 1-click human checkpoints."
)

V2_SUMMARY = (
    "Version 2 roadmap: native WhatsApp Business Calling, autonomous overnight agent "
    "night shift, cloned user voice, autonomous build pipeline ('The agent owns the code and the human'), "
    "and 1-click public repo submission."
)

DEFAULT_AGENDA_ITEMS: list[AgendaItem] = [
    AgendaItem(
        item_id="agenda-01",
        topic="Status Version 1: Today's Swarm Build (Ray-Ban & Web Call)",
        question_for_lead="Version 1 was built today: simulated web call on Ray-Ban glasses, low-latency audio, before/after graph. Anything you want me to flag?",
        recommended_action="APPROVE - Lock in Version 1 hackathon baseline and proceed to Version 2 triage",
        is_irreversible=False,
        action_type="NOTE",
        event_ids=["evt-005", "evt-006", "evt-008"],
        priority=1,
    ),
    AgendaItem(
        item_id="agenda-02",
        topic="Decision Version 2: Autonomous Build Pipeline & Roadmap Options",
        question_for_lead="The agent owns the code and the human: which Version 2 feature should the autonomous build pipeline prioritize — Option A WhatsApp Calling, Option B autonomous Night Shift, or Option C cloned Voice?",
        recommended_action="APPROVE - Select Version 2 priority candidate and dispatch to autonomous build pipeline ('The agent owns the code and the human')",
        is_irreversible=False,
        action_type="DISPATCH_AGENT",
        event_ids=["evt-001", "evt-007"],
        priority=2,
    ),
    AgendaItem(
        item_id="agenda-03",
        topic="Version 2 Checkpoint: Autonomous Main Commit & Public Repo Submission",
        question_for_lead="Shall I enable autonomous main commits and make the repo public for 19:00 hackathon submission?",
        recommended_action="APPROVE with Human Checkpoint - Irreversible autonomous write access and public release requires desk sign-off",
        is_irreversible=True,
        action_type="DEPLOY",
        event_ids=["evt-009", "evt-010"],
        priority=3,
    ),
    AgendaItem(
        item_id="agenda-04",
        topic="Scale: Hackathon Swarm Expansion & Multi-Team Commute Calls",
        question_for_lead="Should I scale the autonomous morning commute call to every other team at the hackathon?",
        recommended_action="APPROVE - Expand autonomous triage swarm to all 42 hackathon teams",
        is_irreversible=False,
        action_type="UPDATE_BUDGET",
        event_ids=["evt-002", "evt-003", "evt-004"],
        priority=4,
    ),
]


def get_v2_agenda() -> list[AgendaItem]:
    """Return a fresh copy of the canonical v1->v2 AgendaItems."""
    return [item.model_copy() for item in DEFAULT_AGENDA_ITEMS]


def get_agenda(agenda_path: Path | str | None = None) -> list[AgendaItem]:
    """Get active agenda from path, state, or fallback to canonical v2 agenda."""
    if agenda_path:
        p = Path(agenda_path)
        if p.exists():
            return load_agenda(p)
    st = state.load()
    if st.agenda:
        return st.agenda
    default_p = state.data_dir() / "agenda.json"
    if default_p.exists():
        return load_agenda(default_p)
    return get_v2_agenda()


def get_quickfire_catalog() -> list[dict[str, Any]]:
    """Return structured rapid quick-fire question catalog for the commute voice call."""
    return [
        {
            "item_id": item.item_id,
            "topic": item.topic,
            "question": item.question_for_lead,
            "recommended": item.recommended_action,
            "is_irreversible": item.is_irreversible,
            "action_type": item.action_type,
            "priority": item.priority,
        }
        for item in DEFAULT_AGENDA_ITEMS
    ]


def format_quickfire_summary() -> str:
    """Format human-readable summary of the v1->v2 quick-fire agenda."""
    lines = [
        "=== DawnDispatch Schnellfeuer Agenda (v1 -> v2) ===",
        f"Leitsatz: {SLOGAN}",
        f"Themen: {', '.join(TOPICS_V1_TO_V2)}",
        "",
    ]
    for item in DEFAULT_AGENDA_ITEMS:
        flag = " [IRREVERSIBLE / HUMAN CHECKPOINT]" if item.is_irreversible else ""
        lines.append(f"{item.priority}. [{item.item_id}] {item.topic}{flag}")
        lines.append(f"   Frage: {item.question_for_lead}")
        lines.append(f"   Empfehlung: {item.recommended_action}")
        lines.append("")
    return "\n".join(lines)


def sync_agenda_file(output_path: Path | str = "src/data/agenda.json") -> list[AgendaItem]:
    """Write canonical v1->v2 agenda items to disk."""
    items = get_v2_agenda()
    save_agenda(items, output_path)
    return items


if __name__ == "__main__":
    print(format_quickfire_summary())
