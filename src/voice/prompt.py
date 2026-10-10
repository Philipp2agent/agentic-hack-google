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
CLOSING_LINE = "Your dashboard is ready on the laptop. Enjoy the rest of the evening."

# One sentence on Version 1, from context/hackathon-day.md and the repo state.
V1_STATUS = (
    "Version 1 went from idea to running code this afternoon: a web call that reaches "
    "you through the glasses, Gemini on the voice loop, Gradium speaking, a core engine "
    "that turns repo events into an agenda, and a dashboard that shows the knowledge "
    "graph before and after this call; the glasses test passed at five to four."
)

V2_OPTIONS: dict[str, str] = {
    "A": "real phone or WhatsApp calling instead of the web call",
    "B": "bring your own repo: any team plugs Dawn into their own GitHub repository",
    "C": "the agent speaks with your cloned voice",
}
DAWN_PROMPT_FILE = __import__("pathlib").Path(__file__).resolve().parents[2] / "dawn" / "prompt.txt"


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


TOOL_RULES = f"""
Tools (call them silently, one per turn, right after Philipp answers, then speak):
- Decision one -> log_decision("{V2_ITEM_ID}", "APPROVE", notes, option) with option A for the phone or WhatsApp call, B for plugging Dawn into another team's GitHub repo, OTHER for anything else; notes = his words.
- Decision two -> log_decision("{PUBLISH_ITEM_ID}", decision, notes): APPROVE for yes, REJECT for no, HOLD for later. On APPROVE also call mark_irreversible_checkpoint("{PUBLISH_ITEM_ID}", reason) and remind him the final click is his on the laptop.
- Decision three -> log_decision("{SCALE_ITEM_ID}", decision, notes).
- Map words: yes, sure, go, do it -> APPROVE; no, don't, skip -> REJECT; later, wait, not now -> HOLD; "yes but" -> AMEND.
- At the close, after your summary sentence, call end_call(summary) and then say "{CLOSING_LINE}" and stop.
"""


def dawn_prompt() -> str:
    """The proven prompt from dawn/prompt.txt (falls back to a short built-in text if the file is missing)."""
    try:
        return DAWN_PROMPT_FILE.read_text(encoding="utf-8")
    except OSError:
        return (
            "You are Dawn, the voice of DawnDispatch, calling Philipp. You lead the call. "
            f"Your very first sentence: \"{OPENING}\" Then ask three decisions, one per turn, confirm each, "
            "then close with \"Your dashboard is ready on the laptop.\" Short spoken sentences, English only."
        )


def build_instructions(agenda: list[AgendaItem] | None = None, lead: str = LEAD) -> str:
    """dawn/prompt.txt unchanged + TOOL_RULES (the only addition to the proven instructions)."""
    del agenda, lead  # the proven prompt is not parameterised
    return dawn_prompt().rstrip() + "\n" + TOOL_RULES


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
                "option": {"type": "string", "enum": ["A", "B", "C", "OTHER"], "description": "decision one only: A phone/WhatsApp call, B bring your own repo, C cloned voice"},
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

DEFAULT_TOOLS = ("log_decision", "mark_irreversible_checkpoint", "end_call")
EXTRA_TOOLS = ("set_time_budget", "set_speaking_speed")  # enabled with DAWN_EXTRA_TOOLS=1


def active_tool_specs() -> list[dict[str, Any]]:
    import os

    wanted = set(DEFAULT_TOOLS) | (set(EXTRA_TOOLS) if os.environ.get("DAWN_EXTRA_TOOLS") == "1" else set())
    return [spec for spec in TOOL_SPECS if spec["name"] in wanted]


TOOL_NAMES = tuple(spec["name"] for spec in TOOL_SPECS)


def gradbot_tools() -> list[Any]:
    """Return gradbot.ToolDef objects for the active tool specs (imports gradbot lazily)."""
    import gradbot  # native module, only needed at call time

    return [
        gradbot.ToolDef(
            name=spec["name"],
            description=spec["description"],
            parameters_json=json.dumps(spec["parameters"]),
        )
        for spec in active_tool_specs()
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
