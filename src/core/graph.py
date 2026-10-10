"""Knowledge Graph generator for DawnDispatch (gemini-01).

Derives deterministic KnowledgeGraph instances for "before" and "after" phases
according to docs/ARCHITEKTUR.md Section 2.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from src.core.models import (
    DawnState,
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    save_knowledge_graph,
)
from src.core import state


def build_graph(state_obj: DawnState | None = None, phase: str = "before") -> KnowledgeGraph:
    """Build a deterministic KnowledgeGraph from state for phase "before" or "after"."""
    st = state_obj or state.load()
    p = phase.lower()

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    seen_agents: set[str] = set()

    # 1. Agents and Events
    for e in st.events[:12]:
        agent_nid = f"agent-{e.agent_id}"
        if e.agent_id not in seen_agents:
            seen_agents.add(e.agent_id)
            nodes.append(
                GraphNode(
                    id=agent_nid,
                    label=e.agent_id,
                    kind="agent",
                    status="info",
                    data={"role": e.agent_id},
                )
            )

        evt_status = "blocked" if e.severity == "ERROR" else ("open" if e.severity == "WARNING" else "info")
        if p == "after":
            evt_status = "resolved"

        nodes.append(
            GraphNode(
                id=e.id,
                label=e.title[:45],
                kind="event",
                status=evt_status,
                data={"severity": e.severity, "source": e.source, "ref": e.ref},
            )
        )
        edges.append(
            GraphEdge(
                source=agent_nid,
                target=e.id,
                label="PRODUCED",
                relation="PRODUCED",
                status="RESOLVED" if p == "after" else "PENDING",
            )
        )

    # 2. Agenda Items
    decisions_by_item = {d.item_id: d for d in st.decisions}
    actions_by_item = {a.item_id: a for a in st.actions}

    for idx, a in enumerate(st.agenda):
        if p == "before":
            agenda_status = "blocked" if a.is_irreversible else "open"
        else:
            agenda_status = "resolved" if a.item_id in decisions_by_item else "open"

        nodes.append(
            GraphNode(
                id=a.item_id,
                label=a.topic,
                kind="agenda",
                status=agenda_status,
                data={
                    "is_irreversible": a.is_irreversible,
                    "question": a.question_for_lead,
                    "recommended_action": a.recommended_action,
                    "action_type": a.action_type,
                    "priority": a.priority,
                },
            )
        )

        connected_events = a.event_ids if a.event_ids else ([st.events[idx].id] if idx < len(st.events) else [])
        for e_id in connected_events:
            edges.append(
                GraphEdge(
                    source=e_id,
                    target=a.item_id,
                    label="TRIGGERS",
                    relation="TRIGGERS",
                    status="RESOLVED" if p == "after" else "PENDING",
                )
            )

    # 3. Post-call additions (phase == "after")
    if p == "after":
        for d in st.decisions:
            dec_status = "resolved" if d.decision_type == "APPROVE" else ("blocked" if d.decision_type == "HOLD" else "open")
            nodes.append(
                GraphNode(
                    id=d.decision_id,
                    label=f"Decision: {d.decision_type}",
                    kind="decision",
                    status=dec_status,
                    data={
                        "item_id": d.item_id,
                        "decision_type": d.decision_type,
                        "voice_notes": d.voice_notes,
                        "human_verified": d.human_verified,
                        "source": d.source,
                    },
                )
            )
            edges.append(
                GraphEdge(
                    source=d.item_id,
                    target=d.decision_id,
                    label="DECIDED_BY",
                    relation="DECIDED_BY",
                    status="RESOLVED",
                )
            )

            act = actions_by_item.get(d.item_id)
            if act:
                act_status = "blocked" if act.status == "BLOCKED_ON_CHECKPOINT" else ("resolved" if act.status == "COMPLETED" else "open")
                kind = "checkpoint" if act.status == "BLOCKED_ON_CHECKPOINT" else "action"
                nodes.append(
                    GraphNode(
                        id=act.action_id,
                        label=act.action_type,
                        kind=kind,
                        status=act_status,
                        data={
                            "item_id": act.item_id,
                            "status": act.status,
                            "checkpoint_reason": act.checkpoint_reason,
                            "artifacts": act.artifacts,
                        },
                    )
                )
                edges.append(
                    GraphEdge(
                        source=d.decision_id,
                        target=act.action_id,
                        label="DISPATCHES",
                        relation="DISPATCHES",
                        status="RESOLVED" if act.status == "COMPLETED" else "BLOCKED",
                    )
                )

    return KnowledgeGraph(
        phase="after" if p == "after" else "before",
        stage="AFTER" if p == "after" else "BEFORE",
        nodes=nodes,
        edges=edges,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Knowledge Graph for before/after commute call.")
    parser.add_argument("--phase", choices=["before", "after"], default="before", help="Phase of call")
    parser.add_argument("--out", default=None, help="Output JSON path")
    args = parser.parse_args()

    g = build_graph(phase=args.phase)
    out_path = Path(args.out) if args.out else (state.data_dir() / f"knowledge_graph_{args.phase}.json")
    save_knowledge_graph(g, out_path)
    print(f"Graph '{args.phase}' written to {out_path}: {len(g.nodes)} nodes, {len(g.edges)} edges")


if __name__ == "__main__":
    main()
