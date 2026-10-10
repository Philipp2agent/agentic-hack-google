"""Post-call processing for DawnDispatch (claude-03).

``process_post_call()`` is idempotent and only calls into src/core:
  decisions.json -> actions.json (action_engine.process_decisions)
  checkpoint reasons recorded during the call are re-applied to the blocked actions
  knowledge_graph_before.json + decisions + actions -> knowledge_graph_after.json
  call.json transcript -> transcript.json (the shape src/dashboard reads)
  call.json gets status=ended and a 3-bullet briefing
All paths come from src.core.state.data_dir() (override with DAWN_DATA_DIR in tests).
"""
from __future__ import annotations

import pathlib
from typing import Any

from src.core import state
from src.core.action_engine import mark_irreversible_checkpoint, on_decision
from src.core.graph_engine import generate_and_save_graph_after, generate_and_save_graph_before
from src.core.models import AgendaItem, load_agenda, now_iso, save_agenda
from src.voice.prompt import DEMO_AGENDA, PUBLISH_ITEM_ID, SCALE_ITEM_ID, V2_ITEM_ID, V2_OPTIONS

CHECKPOINT_META_PREFIX = "checkpoint_reason:"


def paths() -> dict[str, pathlib.Path]:
    d = state.data_dir()
    return {
        "events": d / "overnight_events.json",
        "agenda": d / "agenda.json",
        "decisions": d / "decisions.json",
        "actions": d / "actions.json",
        "graph_before": d / "knowledge_graph_before.json",
        "graph_after": d / "knowledge_graph_after.json",
        "transcript": d / "transcript.json",
    }


def ensure_demo_agenda() -> list[AgendaItem]:
    """Seed agenda.json with the LIVE-EVENTS demo agenda unless a 4-item agenda is already there."""
    p = paths()
    items = load_agenda(p["agenda"])
    wanted = {it.item_id for it in DEMO_AGENDA}
    if {it.item_id for it in items} >= wanted:
        return items
    save_agenda(DEMO_AGENDA, p["agenda"])
    return list(DEMO_AGENDA)


def refresh_graph_before() -> int:
    """Regenerate knowledge_graph_before.json from events + agenda. Returns node count."""
    p = paths()
    graph = generate_and_save_graph_before(p["events"], p["agenda"], p["graph_before"])
    return len(graph.nodes)


def set_checkpoint_reason(item_id: str, reason: str) -> dict[str, Any]:
    """Block the action for item_id on a human checkpoint with the given reason (idempotent, via src/core)."""
    state.set_meta(CHECKPOINT_META_PREFIX + item_id, reason)
    action = mark_irreversible_checkpoint(item_id, reason)
    return action.model_dump()


def _ensure_actions_for_decisions() -> int:
    """Every recorded decision gets its action through the core seam on_decision (idempotent per item)."""
    st = state.load()
    created = 0
    for item_id in {d.item_id for d in st.decisions}:
        rec = state.latest_decision(st, item_id)
        if rec is not None and not any(a.item_id == item_id for a in st.actions):
            on_decision(rec)
            created += 1
    return created


def _mirror_checkpoint_reasons() -> None:
    """Dashboard cards read artifacts.reason; keep it in sync with checkpoint_reason."""
    def _do(st):
        for act in st.actions:
            if act.status == "BLOCKED_ON_CHECKPOINT":
                reason = st.meta.get(CHECKPOINT_META_PREFIX + act.item_id) or act.checkpoint_reason
                if reason:
                    act.checkpoint_reason = reason
                    act.artifacts["reason"] = reason
                act.artifacts.setdefault("pending_url", f"/dashboard/checkpoint/{act.item_id}")
    state.update(_do)


def _speaker(role: str) -> str:
    return {"agent": "DawnDispatch", "user": "Philipp", "tool": "tool"}.get(role, role)


def _mmss(t: float | None) -> str:
    if t is None:
        return ""
    t = int(max(0, t))
    return f"{t // 60:02d}:{t % 60:02d}"


def build_briefing(st) -> list[str]:
    """Three bullets for the dashboard / live screen (deterministic, no LLM)."""
    by_item = {}
    for rec in st.decisions:
        by_item[rec.item_id] = rec  # last one wins
    v2 = by_item.get(V2_ITEM_ID)
    publish = by_item.get(PUBLISH_ITEM_ID)
    scale = by_item.get(SCALE_ITEM_ID)
    blocked = [a for a in st.actions if a.status == "BLOCKED_ON_CHECKPOINT"]

    v2_text = "Version 2: not decided yet."
    if v2 is not None:
        opt = (st.meta.get("v2_option") or "").upper()
        label = V2_OPTIONS.get(opt)
        v2_text = f"Version 2: {label}." if label else f"Version 2: {v2.voice_notes or v2.decision_type}."
    if publish is None:
        pub_text = "Publish and submit: not decided yet."
    elif publish.decision_type == "APPROVE":
        pub_text = "Publish and submit: approved by voice, waiting for your click on the laptop." if blocked else "Publish and submit: confirmed."
    else:
        pub_text = f"Publish and submit: {publish.decision_type.lower()}."
    scale_text = "Scale: offer the call to every team." if scale and scale.decision_type == "APPROVE" else "Scale: stays with this team for now."
    return [v2_text, pub_text, scale_text]


def write_transcript(st, duration_s: int | None, summary: str | None) -> dict[str, Any]:
    p = paths()
    turns = []
    for i, t in enumerate(st.call.transcript, start=1):
        turns.append({
            "index": i,
            "time": _mmss(t.t_s),
            "speaker": _speaker(t.role),
            "text": t.text,
            "tag": "Agent" if t.role == "agent" else "Lead",
            "audio_marker_ms": int(t.t_s * 1000) if t.t_s is not None else None,
        })
    payload = {
        "call_id": f"call-{(st.call.started_at or now_iso()).replace(':', '').replace('-', '')[:15]}",
        "call_title": "Morning call: Version 1 to Version 2",
        "channel": "Web call, audio through smart glasses",
        "lead": "Philipp",
        "agent": "DawnDispatch",
        "duration_seconds": duration_s if duration_s is not None else 0,
        "started_at": st.call.started_at,
        "ended_at": st.call.ended_at or now_iso(),
        "time_budget_s": st.call.time_budget_s,
        "summary": summary or "",
        "turns": turns,
        "decisions_captured": [d.model_dump() for d in st.decisions],
    }
    import json

    p["transcript"].parent.mkdir(parents=True, exist_ok=True)
    with open(p["transcript"], "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return payload


def process_post_call(summary: str | None = None, duration_s: int | None = None) -> dict[str, Any]:
    """decisions -> actions -> graph after -> transcript -> call ended + briefing. Idempotent."""
    p = paths()
    ensure_demo_agenda()
    if not p["graph_before"].exists():
        refresh_graph_before()
    _ensure_actions_for_decisions()
    _mirror_checkpoint_reasons()
    graph = generate_and_save_graph_after(p["graph_before"], p["decisions"], p["actions"], p["graph_after"])
    st = state.load()
    briefing = build_briefing(st)
    if summary:
        state.set_meta("call_summary", summary)
    state.end_call(briefing=briefing)
    st = state.load()
    transcript = write_transcript(st, duration_s, summary)
    blocked = [a for a in st.actions if a.status == "BLOCKED_ON_CHECKPOINT"]
    return {
        "actions": len(st.actions),
        "blocked_on_checkpoint": [a.item_id for a in blocked],
        "graph_after_nodes": len(graph.nodes),
        "briefing": briefing,
        "transcript_turns": len(transcript["turns"]),
        "paths": {k: str(v) for k, v in p.items()},
    }


if __name__ == "__main__":
    import json as _json

    print(_json.dumps(process_post_call(), indent=2))
