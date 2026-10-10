"""Knowledge Graph Engine for DawnDispatch (Before/After Graph Inferenz).

Constructs the pre-call knowledge graph (unresolved swarm state) and transforms
it into the post-call resolved graph based on voice decisions and action executions.
"""

from pathlib import Path
from typing import Sequence

from src.core.models import (
    ActionExecution,
    AgendaItem,
    DecisionRecord,
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    OvernightEvent,
    load_actions,
    load_agenda,
    load_decisions,
    load_events,
    load_knowledge_graph,
    save_knowledge_graph,
)


def build_knowledge_graph_before(
    events: Sequence[OvernightEvent],
    agenda: Sequence[AgendaItem],
) -> KnowledgeGraph:
    """Build the pre-call knowledge graph representing overnight open state."""
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    seen_agents: set[str] = set()

    for evt in events:
        # Agent Node
        agent_node_id = f"agent-{evt.agent_id}"
        if evt.agent_id not in seen_agents:
            seen_agents.add(evt.agent_id)
            nodes.append(
                GraphNode(
                    id=agent_node_id,
                    label=evt.agent_id,
                    type="agent",
                    status="ACTIVE",
                    details=f"Swarm agent: {evt.agent_id}",
                )
            )

        # Event Node
        status = "BLOCKED" if evt.severity == "ERROR" else ("UNRESOLVED" if evt.severity == "WARNING" else "OPEN")
        nodes.append(
            GraphNode(
                id=evt.id,
                label=evt.title[:50],
                type="event",
                status=status,
                details=evt.details,
                metadata={"severity": evt.severity, "source": evt.source},
            )
        )

        # Edge Agent -> Event
        edges.append(
            GraphEdge(
                source=agent_node_id,
                target=evt.id,
                relation="PRODUCED",
                status="PENDING",
            )
        )

    # Agenda Nodes & Edges
    for idx, item in enumerate(agenda):
        nodes.append(
            GraphNode(
                id=item.item_id,
                label=item.topic,
                type="agenda",
                status="PENDING_TRIAGE",
                details=item.question_for_lead,
                metadata={
                    "recommended_action": item.recommended_action,
                    "is_irreversible": item.is_irreversible,
                },
            )
        )

        # Connect corresponding event to agenda item if index matches or link first events
        if idx < len(events):
            edges.append(
                GraphEdge(
                    source=events[idx].id,
                    target=item.item_id,
                    relation="TRIGGERS",
                    status="PENDING",
                )
            )

    return KnowledgeGraph(stage="BEFORE", nodes=nodes, edges=edges)


def build_knowledge_graph_after(
    graph_before: KnowledgeGraph,
    decisions: Sequence[DecisionRecord],
    actions: Sequence[ActionExecution],
) -> KnowledgeGraph:
    """Build the post-call knowledge graph with resolved decisions and action cards."""
    # Deep copy nodes and edges
    nodes_map = {n.id: n.model_copy(deep=True) for n in graph_before.nodes}
    edges = [e.model_copy(deep=True) for e in graph_before.edges]

    # Resolve event nodes
    for node in nodes_map.values():
        if node.type == "event":
            node.status = "RESOLVED"

    # Process Decisions
    for dec in decisions:
        dec_node_id = f"dec-{dec.item_id}"
        nodes_map[dec_node_id] = GraphNode(
            id=dec_node_id,
            label=f"Decision: {dec.decision_type}",
            type="decision",
            status="RECORDED",
            details=dec.voice_notes,
            metadata={"human_verified": dec.human_verified, "timestamp": dec.timestamp},
        )

        if dec.item_id in nodes_map:
            agenda_node = nodes_map[dec.item_id]
            agenda_node.status = f"DECIDED_{dec.decision_type}"

            edges.append(
                GraphEdge(
                    source=dec.item_id,
                    target=dec_node_id,
                    relation="DECIDED_BY",
                    status="RESOLVED",
                )
            )

    # Process Actions
    for act in actions:
        act_node_id = act.action_id
        nodes_map[act_node_id] = GraphNode(
            id=act_node_id,
            label=act.action_type,
            type="action",
            status=act.status,
            details=str(act.artifacts.get("reason") or act.artifacts.get("dispatch_status") or act.status),
            metadata=act.artifacts,
        )

        dec_node_id = f"dec-{act.item_id}"
        source_id = dec_node_id if dec_node_id in nodes_map else act.item_id

        edges.append(
            GraphEdge(
                source=source_id,
                target=act_node_id,
                relation="DISPATCHES",
                status="RESOLVED" if act.status == "COMPLETED" else "BLOCKED",
            )
        )

    return KnowledgeGraph(
        stage="AFTER",
        nodes=list(nodes_map.values()),
        edges=edges,
    )


def generate_and_save_graph_before(
    events_path: Path | str = "src/data/overnight_events.json",
    agenda_path: Path | str = "src/data/agenda.json",
    output_path: Path | str = "src/data/knowledge_graph_before.json",
) -> KnowledgeGraph:
    """Generate and save the pre-call knowledge graph."""
    events = load_events(events_path)
    agenda = load_agenda(agenda_path)
    graph = build_knowledge_graph_before(events, agenda)
    save_knowledge_graph(graph, output_path)
    return graph


def generate_and_save_graph_after(
    graph_before_path: Path | str = "src/data/knowledge_graph_before.json",
    decisions_path: Path | str = "src/data/decisions.json",
    actions_path: Path | str = "src/data/actions.json",
    output_path: Path | str = "src/data/knowledge_graph_after.json",
) -> KnowledgeGraph:
    """Generate and save the post-call knowledge graph."""
    graph_before = load_knowledge_graph(graph_before_path)
    decisions = load_decisions(decisions_path)
    actions = load_actions(actions_path)
    graph = build_knowledge_graph_after(graph_before, decisions, actions)
    save_knowledge_graph(graph, output_path)
    return graph


if __name__ == "__main__":
    gb = generate_and_save_graph_before()
    ga = generate_and_save_graph_after()
    print(f"Graph BEFORE: {len(gb.nodes)} nodes, {len(gb.edges)} edges saved to src/data/knowledge_graph_before.json")
    print(f"Graph AFTER:  {len(ga.nodes)} nodes, {len(ga.edges)} edges saved to src/data/knowledge_graph_after.json")
