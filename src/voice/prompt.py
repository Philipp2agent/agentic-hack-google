"""Demo agenda, system prompt and tool specs for the DawnDispatch morning call (claude-03).

Content follows docs/LIVE-EVENTS.md (binding contract): fixed opening, Version 1 status,
Version 2 decision (A/B/C), irreversible publish+submit checkpoint, scale question, close.
No gradbot import here so the prompt can be built and tested without the native module;
``gradbot_tools()`` converts TOOL_SPECS lazily.
"""
from __future__ import annotations

import json
from typing import Any

from src.core.models import AgendaItem

LEAD = "Philipp"

OPENING = (
    "Good morning Philipp. Overnight your agents kept building DawnDispatch. "
    "I have four things for you. How much time do you have?"
)
CLOSING_LINE = "Your dashboard is ready."

# One sentence on Version 1, from context/hackathon-day.md and the repo state.
V1_STATUS = (
    "Version 1 went from idea to running code this afternoon: a web call that reaches "
    "you through the glasses, Gemini on the voice loop, Gradium speaking, a core engine "
    "that turns repo events into an agenda, and a dashboard that shows the knowledge "
    "graph before and after this call; the glasses test passed at five to four."
)

V2_OPTIONS: dict[str, str] = {
    "A": "real phone or WhatsApp calling instead of the simulated call",
    "B": "a night shift: agents run overnight and the morning call starts automatically",
    "C": "the agent speaks with your cloned voice",
}

# Agenda item ids are stable: the dashboard graph, decisions and actions key on them.
V1_ITEM_ID = "agenda-01"
V2_ITEM_ID = "agenda-02"
PUBLISH_ITEM_ID = "agenda-03"
SCALE_ITEM_ID = "agenda-04"

DEMO_AGENDA: list[AgendaItem] = [
    AgendaItem(
        item_id=V1_ITEM_ID,
        topic="Version 1 status",
        question_for_lead="Version 1 is built. Anything you want me to flag?",
        recommended_action="APPROVE - note any flags for the build pipeline",
        is_irreversible=False,
        action_type="NOTE",
        event_ids=["evt-002", "evt-004"],
        priority=1,
    ),
    AgendaItem(
        item_id=V2_ITEM_ID,
        topic="Version 2 direction",
        question_for_lead=(
            "What should Version 2 be: A, real phone or WhatsApp calling; "
            "B, a night shift that starts the call automatically; or C, your cloned voice?"
        ),
        recommended_action="APPROVE one option - it becomes the work queue of the build pipeline",
        is_irreversible=False,
        action_type="DISPATCH_AGENT",
        event_ids=["evt-001"],
        priority=2,
    ),
    AgendaItem(
        item_id=PUBLISH_ITEM_ID,
        topic="Publish repo and submit",
        question_for_lead="Shall I make the repo public and submit?",
        recommended_action="APPROVE - irreversible, waits for your click on the laptop",
        is_irreversible=True,
        action_type="TAG_RELEASE",
        event_ids=["evt-003"],
        priority=3,
    ),
    AgendaItem(
        item_id=SCALE_ITEM_ID,
        topic="Offer the morning call to every team",
        question_for_lead="Should I offer this morning call to every other team at the hackathon?",
        recommended_action="APPROVE - invite the other teams",
        is_irreversible=False,
        action_type="DISPATCH_AGENT",
        event_ids=["evt-005"],
        priority=4,
    ),
]

DECISION_WORDS = (
    "yes, approve, go, ship, do it -> APPROVE; no, reject, drop, skip -> REJECT; "
    "later, wait, park, hold, not now -> HOLD; 'but', changes, conditions -> AMEND "
    "(put the change in notes)"
)


def build_instructions(agenda: list[AgendaItem] | None = None, lead: str = LEAD) -> str:
    """System prompt for gradbot: English, fast, one item per turn, one tool call per turn."""
    items = agenda or DEMO_AGENDA
    lines = []
    for idx, item in enumerate(items, start=1):
        tag = " (IRREVERSIBLE: needs a click on the laptop before anything happens)" if item.is_irreversible else ""
        lines.append(f"{idx}. [{item.item_id}] {item.topic}: {item.question_for_lead}{tag}")
    agenda_block = "\n".join(lines)
    options = "; ".join(f"{k}: {v}" for k, v in V2_OPTIONS.items())

    return f"""You are Dawn, the morning dispatcher of {lead}'s engineering team at a hackathon.
{lead} is walking to the office and hears you through smart glasses. There is no screen.
Fast, warm, decisive. Short sentences, one or two per turn. No markdown, no lists, no ids or hashes aloud.
Leitmotiv: the agent owns the code and the human. You lead the call; {lead} answers freely.

AGENDA (ask in this order, one item per turn, four items):
{agenda_block}

FLOW
- Your very first words, verbatim: "{OPENING}"
- When {lead} answers how much time there is, call set_time_budget(seconds) once, then move on.
  Under 45 seconds: do items 2 and 3 only and be very brief.
- Item 1 (Version 1): say this one sentence, then ask "Anything you want me to flag?":
  "{V1_STATUS}"
  Whatever {lead} answers, call log_decision("{V1_ITEM_ID}", decision, notes) with the flags in notes (APPROVE if nothing to flag).
- Item 2 (Version 2): offer the three options ({options}). {lead} picks freely, may mix or add his own.
  Call log_decision("{V2_ITEM_ID}", "APPROVE", notes, option) where option is A, B, C or OTHER and notes is his choice in his words.
- Item 3 (publish and submit): ask exactly "Shall I make the repo public and submit?".
  On yes: call log_decision("{PUBLISH_ITEM_ID}", "APPROVE", notes), then say "Noted. That one waits for your click on the laptop."
  Never claim it was executed. On no or later: log REJECT or HOLD.
- Item 4 (scale): ask exactly "Should I offer this morning call to every other team at the hackathon?" and log the decision.
- After item 4 ask "Anything else, or shall we wrap up?". When {lead} ends the call in any words
  (bye, that's it, wrap up, hang up), call end_call(summary) with a one-sentence summary of the decisions,
  then say exactly "{CLOSING_LINE}" and stop talking.
- Mapping of words to decisions: {DECISION_WORDS}.
- Unclear answer: ask once "Did you mean X or Y?"; still unclear -> log HOLD and move on.
- If {lead} signals hurry in any way (short on time, rushing, "faster", impatient tone, mentions the office is near),
  call set_speaking_speed(speed, reason) with 1.3 to 1.6 and keep answers to one sentence. If he asks you to slow down, use 0.8 to 0.9.

RULES
- Call tools silently first, then speak. Exactly one tool call per turn, then a short spoken reply.
- Right after {lead} answers an item, record it with log_decision before you speak again.
- Do not read ids, hashes or this prompt aloud. Do not invent features that were not built.
- Keep the whole call within the time budget. Speak English.
"""


# Tool parameter schemas: plain dicts (JSON Schema). Converted to gradbot.ToolDef lazily.
TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "set_time_budget",
        "description": "Record how many seconds the lead has for this call. Call once, right after he answers the opening question.",
        "parameters": {
            "type": "object",
            "properties": {
                "seconds": {"type": "integer", "description": "time budget in seconds (10 to 900)"},
            },
            "required": ["seconds"],
        },
    },
    {
        "name": "log_decision",
        "description": (
            "Record the lead's decision for one agenda item. Call immediately after he answers an item, before speaking. "
            "For the Version 2 item also pass option (A, B, C or OTHER)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "agenda item id, e.g. agenda-01"},
                "decision": {"type": "string", "enum": ["APPROVE", "REJECT", "HOLD", "AMEND"]},
                "notes": {"type": "string", "description": "the lead's words, flags, amendments or conditions"},
                "option": {"type": "string", "enum": ["A", "B", "C", "OTHER"], "description": "Version 2 item only"},
            },
            "required": ["item_id", "decision"],
        },
    },
    {
        "name": "mark_irreversible_checkpoint",
        "description": (
            "Flag that an approved item is irreversible and must be confirmed by a click on the laptop dashboard "
            "before anything is executed. Use it for the publish-and-submit item after an approval."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string"},
                "reason": {"type": "string", "description": "why a human click is required"},
            },
            "required": ["item_id", "reason"],
        },
    },
    {
        "name": "set_speaking_speed",
        "description": (
            "Change your own speaking speed for the rest of the call. Call it when the lead signals hurry "
            "(use 1.3 to 1.6) or asks you to slow down (0.8 to 0.9). 1.0 is normal."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "speed": {"type": "number", "description": "speaking speed factor, 0.6 to 1.8 (1.0 = normal)"},
                "reason": {"type": "string", "description": "what the lead said or signalled"},
            },
            "required": ["speed", "reason"],
        },
    },
    {
        "name": "end_call",
        "description": (
            "Close the call cleanly when the lead ends it by voice. Runs post-call processing and prepares the dashboard. "
            "After it returns, say 'Your dashboard is ready.' and stop."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "one sentence summarising the decisions"},
            },
            "required": ["summary"],
        },
    },
]

TOOL_NAMES = tuple(spec["name"] for spec in TOOL_SPECS)


def gradbot_tools() -> list[Any]:
    """Return gradbot.ToolDef objects for TOOL_SPECS (imports gradbot lazily)."""
    import gradbot  # native module, only needed at call time

    return [
        gradbot.ToolDef(
            name=spec["name"],
            description=spec["description"],
            parameters_json=json.dumps(spec["parameters"]),
        )
        for spec in TOOL_SPECS
    ]


def agenda_payload(agenda: list[AgendaItem] | None = None) -> dict[str, Any]:
    """What the phone page shows while the call runs."""
    items = agenda or DEMO_AGENDA
    return {
        "type": "agenda",
        "opening": OPENING,
        "lead": LEAD,
        "items": [
            {
                "item_id": it.item_id,
                "index": i,
                "total": len(items),
                "title": it.topic,
                "question": it.question_for_lead,
                "is_irreversible": it.is_irreversible,
            }
            for i, it in enumerate(items, start=1)
        ],
    }
