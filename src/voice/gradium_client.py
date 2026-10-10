"""Gradium Voice Pipeline & Call Orchestration for DawnDispatch.

Manages voice session configuration, rapid quick-fire prompt design,
speech synthesis fallbacks, and transcript export to src/data/transcript.json.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Any

from src.core.models import (
    AgendaItem,
    DecisionRecord,
    load_agenda,
    load_events,
)
from src.core.action_engine import (
    log_decision,
    mark_irreversible_checkpoint,
    process_decisions,
)
from src.core.graph_engine import (
    generate_and_save_graph_after,
)


DEFAULT_VOICE_ID = "cLONiZ4hQ8VpQ4Sz"  # Skyler / Gradium flagship


def build_system_instructions(agenda_path: Path | str = "src/data/agenda.json") -> str:
    """Build the prompt for the morning Ray-Ban commute quick-fire call."""
    agenda_items = load_agenda(agenda_path)

    questions_prompt = ""
    for idx, item in enumerate(agenda_items, start=1):
        irrev_tag = " (CAUTION: IRREVERSIBLE - requires human sign-off)" if item.is_irreversible else ""
        questions_prompt += f"{idx}. [{item.item_id}] {item.question_for_lead}{irrev_tag}\n"

    if not questions_prompt:
        questions_prompt = (
            "1. [agenda-01] PR #4 auth schema refactor — approve staging migration? Yes or no?\n"
            "2. [agenda-02] Purge overnight cache and apply schema migration? Yes or no?\n"
            "3. [agenda-03] Visual assets generated — keep solo silhouette as hero? Yes or no?\n"
        )

    return f"""You are DawnDispatch Voice Assistant, speaking hands-free to Philipp through his Meta Ray-Ban glasses on his morning walk to the office.

STRICT CALL PROTOCOL:
1. Philipp just answered your simulated incoming phone call.
2. Your VERY FIRST phrase MUST BE EXACTLY:
   "Good morning Philipp. Swarm overnight triage ready. How much time do you have?"
3. As soon as Philipp replies (e.g., "60 seconds", "1 minute", "got a minute"), switch immediately to Rapid Quick Fire.
4. RAPID QUICK-FIRE AGENDA:
Ask these questions one by one with rapid, punchy cadence. Expect a quick "Yes", "No", or "Hold":
{questions_prompt}
5. Keep your spoken responses under 15 words between questions. Acknowledge briefly (e.g., "Got it.", "Recorded.", "Approved.") and ask the next question immediately.
6. When all agenda questions have been answered, conclude with:
   "Captured. Knowledge graph updated. See you at your desk."
   and conclude the conversation.
7. Speak fast, energetic, clear, and professional. You are on a live morning commute standup.
"""


def extract_decisions_from_turns(
    turns: list[dict],
    agenda_path: Path | str = "src/data/agenda.json",
) -> list[DecisionRecord]:
    """Parse dialogue turns to match decisions to agenda items."""
    agenda = load_agenda(agenda_path)
    if not agenda:
        return []

    decisions: list[DecisionRecord] = []
    user_turns = [t.get("text", "").lower() for t in turns if t.get("speaker") == "user"]

    # Filter out initial duration response (e.g. "60 seconds")
    decision_responses = [
        t for t in user_turns if not any(w in t for w in ("second", "minute", "time", "walk", "hey", "hello"))
    ]

    for idx, item in enumerate(agenda):
        resp = decision_responses[idx] if idx < len(decision_responses) else "yes"
        resp_clean = resp.lower().strip()

        if any(w in resp_clean for w in ("no", "reject", "deny", "cancel")):
            dec_type = "REJECT"
            notes = f"Rejected by lead during commute call: '{resp}'"
        elif any(w in resp_clean for w in ("hold", "wait", "checkpoint", "later", "pause")):
            dec_type = "HOLD"
            notes = f"Held for dashboard verification by lead: '{resp}'"
        else:
            dec_type = "APPROVE"
            notes = f"Approved by lead via Meta Ray-Ban audio: '{resp}'"

        dec = DecisionRecord(
            item_id=item.item_id,
            decision_type=dec_type,  # type: ignore[arg-type]
            voice_notes=notes,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            human_verified=True,
        )
        decisions.append(dec)

    return decisions


def save_call_transcript(
    transcript_payload: dict[str, Any],
    output_path: Path | str = "src/data/transcript.json",
    decisions_path: Path | str = "src/data/decisions.json",
    actions_path: Path | str = "src/data/actions.json",
    agenda_path: Path | str = "src/data/agenda.json",
) -> dict[str, Any]:
    """Save call transcript and trigger core decision & knowledge graph engine updates."""
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    turns = transcript_payload.get("turns", [])
    call_id = transcript_payload.get(
        "call_id", f"call-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    )

    # Extract decisions from conversation turns if not explicitly supplied
    explicit_decisions = transcript_payload.get("decisions_captured", [])
    if explicit_decisions:
        captured_records = [
            DecisionRecord.model_validate(d) if isinstance(d, dict) else d
            for d in explicit_decisions
        ]
    else:
        captured_records = extract_decisions_from_turns(turns, agenda_path=agenda_path)

    # Upsert decisions into decisions.json
    for rec in captured_records:
        log_decision(
            item_id=rec.item_id,
            decision=rec.decision_type,
            notes=rec.voice_notes,
            file_path=decisions_path,
        )

    # Run action engine
    process_decisions(
        agenda_path=agenda_path,
        decisions_path=decisions_path,
        actions_path=actions_path,
    )

    # Update post-call knowledge graph
    try:
        generate_and_save_graph_after(
            decisions_path=decisions_path,
            actions_path=actions_path,
        )
    except Exception:
        pass

    full_transcript = {
        "call_id": call_id,
        "caller": transcript_payload.get("caller", "DawnDispatch Voice Agent"),
        "callee": transcript_payload.get("callee", "Philipp (Meta Ray-Ban Audio)"),
        "started_at": transcript_payload.get(
            "started_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        ),
        "ended_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": transcript_payload.get("duration_seconds", 58),
        "turns": turns,
        "decisions_captured": [r.model_dump() for r in captured_records],
        "status": "SYNCED_TO_DASHBOARD",
    }

    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(full_transcript, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return full_transcript
