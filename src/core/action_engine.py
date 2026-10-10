"""Action Engine & Post-Call Decision Processor for DawnDispatch.

Transforms decisions recorded during voice triage into ActionExecution records
and provides tool functions for the Voice Agent and Web Dashboard.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.models import (
    ActionExecution,
    AgendaItem,
    DecisionRecord,
    DecisionType,
    load_actions,
    load_agenda,
    load_decisions,
    save_actions,
    save_decisions,
)


def log_decision(
    item_id: str,
    decision: str,
    notes: str = "",
    file_path: Path | str = "src/data/decisions.json",
) -> DecisionRecord:
    """Record a lead decision (APPROVE, REJECT, HOLD, AMEND) for an agenda item.

    Tool function callable by Voice Agent (gradbot).
    """
    normalized_decision = decision.strip().upper()
    valid_decisions: tuple[DecisionType, ...] = ("APPROVE", "REJECT", "HOLD", "AMEND")
    if normalized_decision not in valid_decisions:
        raise ValueError(
            f"Invalid decision '{decision}'. Must be one of: {', '.join(valid_decisions)}"
        )

    decisions = load_decisions(file_path)

    record = DecisionRecord(
        item_id=item_id,
        decision_type=normalized_decision,  # type: ignore[arg-type]
        voice_notes=notes,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        human_verified=True,
    )

    # Upsert record by item_id
    existing_idx = next((i for i, d in enumerate(decisions) if d.item_id == item_id), None)
    if existing_idx is not None:
        decisions[existing_idx] = record
    else:
        decisions.append(record)

    save_decisions(decisions, file_path)
    return record


def mark_irreversible_checkpoint(
    item_id: str,
    reason: str,
    actions_path: Path | str = "src/data/actions.json",
) -> ActionExecution:
    """Mark an action as irreversible and block it pending dashboard 1-click confirmation.

    Tool function callable by Voice Agent or Action Engine.
    """
    actions = load_actions(actions_path)

    existing_idx = next((i for i, a in enumerate(actions) if a.item_id == item_id), None)
    action_id = actions[existing_idx].action_id if existing_idx is not None else f"act-cp-{item_id}"
    action_type = f"CHECKPOINT_{item_id.upper().replace('-', '_')}"

    action = ActionExecution(
        action_id=action_id,
        item_id=item_id,
        action_type=action_type,
        status="BLOCKED_ON_CHECKPOINT",
        artifacts={
            "reason": reason,
            "pending_url": f"/dashboard/checkpoint/{item_id}",
            "blocked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    )

    if existing_idx is not None:
        actions[existing_idx] = action
    else:
        actions.append(action)

    save_actions(actions, actions_path)
    return action


def confirm_checkpoint(
    action_id_or_item_id: str,
    actions_path: Path | str = "src/data/actions.json",
    confirmed_by: str = "Lead Web Dashboard 1-Click",
) -> ActionExecution:
    """Confirm an irreversible checkpoint, transitioning status from BLOCKED_ON_CHECKPOINT to COMPLETED."""
    actions = load_actions(actions_path)

    target_idx = next(
        (
            i
            for i, a in enumerate(actions)
            if a.action_id == action_id_or_item_id or a.item_id == action_id_or_item_id
        ),
        None,
    )

    if target_idx is None:
        raise KeyError(f"No action found matching '{action_id_or_item_id}'")

    action = actions[target_idx]
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    artifacts = dict(action.artifacts)
    artifacts.update({
        "checkpoint_confirmed": True,
        "confirmed_by": confirmed_by,
        "confirmed_at": now_ts,
    })

    action.status = "COMPLETED"
    action.artifacts = artifacts
    actions[target_idx] = action

    save_actions(actions, actions_path)
    return action


def _generate_action_type(item: AgendaItem | None, default_id: str) -> str:
    if not item:
        return f"EXEC_{default_id.upper().replace('-', '_')}"
    cleaned = "".join(c if c.isalnum() else "_" for c in item.topic.upper())
    parts = [p for p in cleaned.split("_") if p][:4]
    return "_".join(parts) or f"ACTION_{default_id}"


def process_decisions(
    agenda_path: Path | str = "src/data/agenda.json",
    decisions_path: Path | str = "src/data/decisions.json",
    actions_path: Path | str = "src/data/actions.json",
) -> list[ActionExecution]:
    """Process decisions against agenda items and update action execution queue."""
    agenda_items = {item.item_id: item for item in load_agenda(agenda_path)}
    decisions = load_decisions(decisions_path)
    existing_actions = {a.item_id: a for a in load_actions(actions_path)}

    results: list[ActionExecution] = []
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for idx, dec in enumerate(decisions, start=101):
        agenda_item = agenda_items.get(dec.item_id)
        action_id = existing_actions[dec.item_id].action_id if dec.item_id in existing_actions else f"act-{idx}"
        action_type = _generate_action_type(agenda_item, dec.item_id)

        is_irrev = agenda_item.is_irreversible if agenda_item else False

        if dec.decision_type == "APPROVE":
            if is_irrev:
                # Retain existing confirmed status if human already approved via dashboard
                prev = existing_actions.get(dec.item_id)
                if prev and prev.status == "COMPLETED" and prev.artifacts.get("checkpoint_confirmed"):
                    status = "COMPLETED"
                    artifacts = prev.artifacts
                else:
                    status = "BLOCKED_ON_CHECKPOINT"
                    artifacts = {
                        "reason": "Irreversible action requires Web Dashboard 1-click confirmation",
                        "pending_url": f"/dashboard/checkpoint/{dec.item_id}",
                        "voice_notes": dec.voice_notes,
                    }
            else:
                status = "COMPLETED"
                artifacts = {
                    "execution_timestamp": now_iso,
                    "voice_notes": dec.voice_notes,
                    "dispatch_status": "Auto-dispatched upon morning commute approval",
                }
        elif dec.decision_type == "HOLD":
            status = "BLOCKED_ON_CHECKPOINT"
            artifacts = {
                "reason": "Lead placed item on hold during morning triage call",
                "pending_url": f"/dashboard/checkpoint/{dec.item_id}",
                "voice_notes": dec.voice_notes,
            }
        elif dec.decision_type == "REJECT":
            status = "PENDING"
            artifacts = {
                "status_reason": "Rejected by lead during morning triage",
                "voice_notes": dec.voice_notes,
            }
        elif dec.decision_type == "AMEND":
            status = "PENDING"
            artifacts = {
                "status_reason": "Amendment requested by lead",
                "voice_notes": dec.voice_notes,
            }
        else:
            status = "PENDING"
            artifacts = {"voice_notes": dec.voice_notes}

        action = ActionExecution(
            action_id=action_id,
            item_id=dec.item_id,
            action_type=action_type,
            status=status,  # type: ignore[arg-type]
            artifacts=artifacts,
        )
        results.append(action)

    save_actions(results, actions_path)
    return results


if __name__ == "__main__":
    actions = process_decisions()
    print(f"Processed {len(actions)} actions in src/data/actions.json:")
    for a in actions:
        print(f"  * [{a.status}] {a.action_id} ({a.item_id}): {a.action_type}")
        if a.status == "BLOCKED_ON_CHECKPOINT":
            print(f"    Checkpoint URL: {a.artifacts.get('pending_url')}")
