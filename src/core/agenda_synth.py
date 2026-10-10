"""Morning Commute Agenda Synthesizer for DawnDispatch.

Synthesizes overnight swarm events into max 3 concise agenda items for the
lead's morning walk (via Meta Ray-Ban audio call). Uses Gemini 3.8 Flash
with structured outputs, with deterministic fallback when offline.
"""

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.core.models import AgendaItem, OvernightEvent, save_agenda, load_events


class AgendaResponseSchema(BaseModel):
    """Schema wrapper for structured output generation."""
    items: list[AgendaItem] = Field(description="Max 3 concise agenda items for audio triage")


_IRREVERSIBLE_KEYWORDS = ("wipe", "purge", "reset", "delete", "destroy", "drop", "schema migration", "production deploy")


def synthesize_agenda_fallback(events: list[OvernightEvent]) -> list[AgendaItem]:
    """Deterministic fallback synthesis when Gemini API is unavailable."""
    if not events:
        return [
            AgendaItem(
                item_id="agenda-01",
                topic="Swarm Status Verification",
                question_for_lead="All overnight pipelines idle. Proceed with daily sprint kickoff?",
                recommended_action="APPROVE - start active build phase",
                is_irreversible=False,
            )
        ]

    # Prioritize WARNING / ERROR first
    sorted_events = sorted(
        events,
        key=lambda e: (0 if e.severity == "ERROR" else (1 if e.severity == "WARNING" else 2)),
    )

    agenda_items: list[AgendaItem] = []
    for idx, e in enumerate(sorted_events[:3], start=1):
        item_id = f"agenda-{idx:02d}"
        topic = e.title[:60]
        text_for_irreversibility = f"{e.title} {e.details} {e.proposed_action}".lower()
        is_irreversible = any(k in text_for_irreversibility for k in _IRREVERSIBLE_KEYWORDS)

        if e.severity == "WARNING" or e.severity == "ERROR":
            question = f"{e.title}? Confirm proposed action: {e.proposed_action}"
            rec = f"APPROVE with caution: {e.proposed_action}"
        else:
            question = f"{e.title}: Proceed with follow-up action?"
            rec = f"APPROVE - {e.proposed_action}"

        agenda_items.append(
            AgendaItem(
                item_id=item_id,
                topic=topic,
                question_for_lead=question,
                recommended_action=rec,
                is_irreversible=is_irreversible,
            )
        )

    return agenda_items


def synthesize_agenda_with_gemini(
    events: list[OvernightEvent],
    api_key: str | None = None,
    model: str = "gemini-3.8-flash",
) -> list[AgendaItem]:
    """Synthesize agenda items using Gemini 3.8 Flash."""
    from google import genai

    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_COMPAT_API_KEY")
    if not key:
        raise ValueError("No Gemini API key available in parameters or environment")

    client = genai.Client(api_key=key)

    events_summary = json.dumps([e.model_dump() for e in events], indent=2)

    prompt = f"""You are the Morning Commute Dispatch Synthesizer for DawnDispatch.
The user is walking during their morning commute wearing Meta Ray-Ban glasses and having a concise 90-second voice call.

Overnight Swarm Events:
{events_summary}

Task:
Synthesize the events into at most 3 crisp, high-priority AgendaItems.
Rules:
1. Exactly 1 to 3 items (never more than 3).
2. 'item_id' format must be 'agenda-01', 'agenda-02', etc.
3. 'topic': Short headline (3 to 7 words).
4. 'question_for_lead': Direct question that can be answered during a voice call (e.g. 'Deploy voice streaming backend to port 8090 for smartphone connection?').
5. 'recommended_action': Crisp recommendation (e.g. 'APPROVE - latency under 350ms' or 'APPROVE - sign-off required for irreversible wipe').
6. 'is_irreversible': Set to true ONLY IF the action is destructive or irreversible (e.g. state purge, database wipe, production schema migration, port takeover). Otherwise false.
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": AgendaResponseSchema,
        },
    )

    data = json.loads(response.text)
    items = [AgendaItem.model_validate(it) for it in data.get("items", [])]
    return items[:3]


def synthesize_agenda(
    events: list[OvernightEvent],
    api_key: str | None = None,
    model: str = "gemini-3.8-flash",
) -> list[AgendaItem]:
    """Synthesize agenda items from overnight events, using Gemini with robust fallback."""
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_COMPAT_API_KEY")
    if key:
        try:
            items = synthesize_agenda_with_gemini(events, api_key=key, model=model)
            if items:
                return items
        except Exception as e:
            # Fall back cleanly
            pass
    return synthesize_agenda_fallback(events)


def synthesize_and_save(
    events_path: Path | str = "src/data/overnight_events.json",
    output_path: Path | str = "src/data/agenda.json",
    api_key: str | None = None,
    model: str = "gemini-3.8-flash",
) -> list[AgendaItem]:
    """Load events, synthesize agenda, and save to output file."""
    events = load_events(events_path)
    agenda = synthesize_agenda(events, api_key=api_key, model=model)
    save_agenda(agenda, output_path)
    return agenda


if __name__ == "__main__":
    items = synthesize_and_save()
    print(f"Synthesized {len(items)} agenda items to src/data/agenda.json:")
    for it in items:
        irrev = " [IRREVERSIBLE]" if it.is_irreversible else ""
        print(f"  * {it.item_id}: {it.topic}{irrev}")
        print(f"    Q: {it.question_for_lead}")
        print(f"    Rec: {it.recommended_action}")
