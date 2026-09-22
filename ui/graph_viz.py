"""Graph visualization components for causal chains."""

from typing import Optional, Callable
import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

from core.models import CausalChain, Event


def get_sentiment_color(sentiment: str) -> str:
    """Get color based on sentiment."""
    colors = {
        "bullish": "#22c55e",  # Green
        "bearish": "#ef4444",  # Red
        "neutral": "#eab308",  # Yellow
    }
    return colors.get(sentiment, "#6b7280")


def get_node_size(probability: float) -> int:
    """Get node size based on probability."""
    # Scale from 15 to 35 based on probability
    return int(15 + probability * 20)


def render_causal_graph(
    chain: CausalChain,
    selected_event_id: Optional[str] = None,
    height: int = 500
) -> Optional[str]:
    """Render an interactive causal chain graph.

    Args:
        chain: The causal chain to visualize
        selected_event_id: Currently selected event ID (for highlighting)
        height: Height of the graph in pixels

    Returns:
        The ID of the clicked node, if any
    """
    if not chain.events:
        st.info("No events in the chain yet. Generate a causal chain to visualize.")
        return None

    # Compute levels (distance from root) using BFS
    root_id = chain.events[0].id if chain.events else None
    levels = {root_id: 0}

    # Build adjacency list
    adjacency = {}
    for edge in chain.edges:
        if edge.source_id not in adjacency:
            adjacency[edge.source_id] = []
        adjacency[edge.source_id].append(edge.target_id)

    # BFS to compute levels
    queue = [root_id]
    while queue:
        current = queue.pop(0)
        current_level = levels.get(current, 0)
        for neighbor in adjacency.get(current, []):
            if neighbor not in levels:
                levels[neighbor] = current_level + 1
                queue.append(neighbor)

    # Group nodes by level and compute fixed positions
    level_groups = {}
    for event in chain.events:
        lvl = levels.get(event.id, 0)
        if lvl not in level_groups:
            level_groups[lvl] = []
        level_groups[lvl].append(event.id)

    # Compute fixed x,y positions for deterministic layout
    positions = {}
    level_separation = 150
    node_spacing = 250
    for lvl, node_ids in level_groups.items():
        y = lvl * level_separation
        total_width = (len(node_ids) - 1) * node_spacing
        start_x = -total_width / 2
        for i, node_id in enumerate(node_ids):
            positions[node_id] = (start_x + i * node_spacing, y)

    nodes = []
    edges = []

    for event in chain.events:
        # Determine if this is the root event
        is_root = event == chain.events[0]

        # Create node
        node_color = get_sentiment_color(event.sentiment)
        node_size = get_node_size(event.probability)

        # Very short label - just key words (max 25 chars)
        words = event.description.split()
        label = ""
        for word in words:
            if len(label) + len(word) + 1 <= 25:
                label += (" " + word) if label else word
            else:
                break
        if len(label) < len(event.description):
            label += "..."

        # Highlight selected node
        border_width = 4 if event.id == selected_event_id else 2
        border_color = "#3b82f6" if event.id == selected_event_id else "#ffffff"

        # Get fixed position for this node
        x, y = positions.get(event.id, (0, 0))

        nodes.append(Node(
            id=event.id,
            label=label,
            size=node_size,
            x=x,
            y=y,
            fixed=True,  # Prevent movement on re-render
            color={
                "background": node_color,
                "border": border_color,
                "highlight": {
                    "background": node_color,
                    "border": "#3b82f6"
                }
            },
            borderWidth=border_width,
            shape="box" if is_root else "ellipse",
            title=f"""
{event.description}

Probability: {event.probability:.0%}
Impact: {event.financial_impact}
Time: {event.time_horizon}
Tradeable: {'Yes' if event.is_tradeable else 'No'}
Instruments: {', '.join(event.instruments) if event.instruments else 'None'}
            """.strip(),
            font={"size": 11, "color": "#ffffff", "face": "arial", "bold": True}
        ))

    for edge in chain.edges:
        # Edge thickness based on causal strength
        width = 1 + edge.strength * 3

        edges.append(Edge(
            source=edge.source_id,
            target=edge.target_id,
            width=width,
            color="#64748b",
            title=edge.reasoning,
            arrows={"to": {"enabled": True, "scaleFactor": 0.8}},
            smooth={"type": "cubicBezier", "forceDirection": "vertical"}
        ))

    config = Config(
        width="100%",
        height=height,
        directed=True,
        physics={"enabled": False},
        hierarchical=False,  # Using fixed positions instead
        interaction={
            "hover": True,
            "tooltipDelay": 50,
            "navigationButtons": True,
            "keyboard": True,
            "zoomView": True,
            "dragNodes": False  # Nodes are fixed
        },
        edges={
            "smooth": {
                "type": "cubicBezier",
                "forceDirection": "vertical"
            }
        }
    )

    clicked_node = agraph(nodes=nodes, edges=edges, config=config)

    return clicked_node


def render_event_details(event: Event, chain: CausalChain):
    """Render detailed information about a selected event."""
    st.subheader(f"Event Details")

    # Event description
    st.markdown(f"**{event.description}**")

    # Metrics row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Probability", f"{event.probability:.0%}")
    with col2:
        sentiment_emoji = {"bullish": "+", "bearish": "-", "neutral": "~"}.get(event.sentiment, "~")
        st.metric("Sentiment", event.sentiment.title(), delta=sentiment_emoji)
    with col3:
        st.metric("Time Horizon", event.time_horizon.title())

    # Financial impact
    st.markdown(f"**Financial Impact:** {event.financial_impact}")

    # Tradeable info
    if event.is_tradeable:
        st.success("This event is tradeable")
        if event.instruments:
            st.markdown(f"**Instruments:** {', '.join(event.instruments)}")
    else:
        st.info("This event is not directly tradeable")

    # Causal connections
    st.markdown("---")
    st.markdown("**Causal Connections:**")

    incoming = chain.get_edges_to(event.id)
    outgoing = chain.get_edges_from(event.id)

    if incoming:
        st.markdown("*Caused by:*")
        for edge in incoming:
            source_event = chain.get_event_by_id(edge.source_id)
            if source_event:
                st.markdown(f"- {source_event.description[:60]}... (strength: {edge.strength:.0%})")

    if outgoing:
        st.markdown("*Leads to:*")
        for edge in outgoing:
            target_event = chain.get_event_by_id(edge.target_id)
            if target_event:
                st.markdown(f"- {target_event.description[:60]}... (strength: {edge.strength:.0%})")


def render_legend():
    """Render a legend for the graph colors."""
    st.markdown("### Legend")
    cols = st.columns(3)
    with cols[0]:
        st.markdown(f":green_circle: **Bullish**")
    with cols[1]:
        st.markdown(f":red_circle: **Bearish**")
    with cols[2]:
        st.markdown(f":yellow_circle: **Neutral**")
    st.caption("Node size indicates probability. Edge thickness indicates causal strength.")
