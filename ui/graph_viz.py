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

    nodes = []
    edges = []

    for event in chain.events:
        # Determine if this is the root event
        is_root = event == chain.events[0]

        # Create node
        node_color = get_sentiment_color(event.sentiment)
        node_size = get_node_size(event.probability)

        # Truncate description for display
        label = event.description[:50] + "..." if len(event.description) > 50 else event.description

        # Highlight selected node
        border_width = 3 if event.id == selected_event_id else 1
        border_color = "#3b82f6" if event.id == selected_event_id else node_color

        nodes.append(Node(
            id=event.id,
            label=label,
            size=node_size,
            color={
                "background": node_color,
                "border": border_color,
                "highlight": {
                    "background": node_color,
                    "border": "#3b82f6"
                }
            },
            borderWidth=border_width,
            shape="dot" if not is_root else "diamond",
            title=f"""
{event.description}

Probability: {event.probability:.0%}
Impact: {event.financial_impact}
Time: {event.time_horizon}
Tradeable: {'Yes' if event.is_tradeable else 'No'}
Instruments: {', '.join(event.instruments) if event.instruments else 'None'}
            """.strip(),
            font={"size": 12, "color": "#1f2937"}
        ))

    for edge in chain.edges:
        # Edge thickness based on causal strength
        width = 1 + edge.strength * 3

        edges.append(Edge(
            source=edge.source_id,
            target=edge.target_id,
            width=width,
            color="#9ca3af",
            title=edge.reasoning,
            arrows="to",
            smooth={"type": "cubicBezier"}
        ))

    config = Config(
        width="100%",
        height=height,
        directed=True,
        physics={
            "enabled": True,
            "hierarchicalRepulsion": {
                "centralGravity": 0.0,
                "springLength": 150,
                "springConstant": 0.01,
                "nodeDistance": 180
            },
            "solver": "hierarchicalRepulsion"
        },
        hierarchical={
            "enabled": True,
            "direction": "LR",  # Left to right
            "sortMethod": "directed",
            "levelSeparation": 200,
            "nodeSpacing": 100
        },
        interaction={
            "hover": True,
            "tooltipDelay": 100,
            "navigationButtons": True,
            "keyboard": True
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
