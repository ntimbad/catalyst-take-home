"""Trading thesis panel UI components."""

import streamlit as st

from core.models import TradingThesis, CausalChain


def render_thesis_panel(thesis: TradingThesis):
    """Render the trading thesis panel.

    Args:
        thesis: The trading thesis to display
    """
    st.header("Trading Thesis")

    # Direction indicator
    direction_colors = {
        "bullish": "green",
        "bearish": "red",
        "neutral": "orange"
    }
    direction_emojis = {
        "bullish": "",
        "bearish": "",
        "neutral": ""
    }

    color = direction_colors.get(thesis.direction, "gray")
    emoji = direction_emojis.get(thesis.direction, "")

    st.markdown(f"### {emoji} {thesis.direction.upper()}")

    # Summary
    st.markdown(f"**Summary:** {thesis.summary}")

    # Key metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Confidence", f"{thesis.confidence:.0%}")
    with col2:
        st.metric("Time Horizon", thesis.time_horizon.title())

    st.markdown("---")

    # Primary instruments
    st.markdown("### Primary Instruments")
    if thesis.primary_instruments:
        instrument_cols = st.columns(min(len(thesis.primary_instruments), 4))
        for i, instrument in enumerate(thesis.primary_instruments[:4]):
            with instrument_cols[i]:
                st.code(instrument)
        if len(thesis.primary_instruments) > 4:
            st.markdown(f"*...and {len(thesis.primary_instruments) - 4} more*")
    else:
        st.info("No specific instruments identified")

    # Entry triggers
    st.markdown("### Entry Triggers")
    if thesis.entry_triggers:
        for trigger in thesis.entry_triggers:
            st.markdown(f"- {trigger}")
    else:
        st.info("No specific entry triggers identified")

    # Risk factors
    st.markdown("### Risk Factors")
    if thesis.risk_factors:
        for risk in thesis.risk_factors:
            st.markdown(f"- {risk}")
    else:
        st.info("No specific risk factors identified")

    # Events to monitor
    st.markdown("### Key Events to Monitor")
    if thesis.key_events_to_monitor:
        for event in thesis.key_events_to_monitor:
            st.markdown(f"- {event}")
    else:
        st.info("No specific events to monitor identified")


def render_thesis_summary_card(thesis: TradingThesis):
    """Render a compact thesis summary card.

    Args:
        thesis: The trading thesis to display
    """
    direction_colors = {
        "bullish": "#22c55e",
        "bearish": "#ef4444",
        "neutral": "#eab308"
    }
    color = direction_colors.get(thesis.direction, "#6b7280")

    st.markdown(f"""
    <div style="
        border-left: 4px solid {color};
        padding: 10px 15px;
        background-color: #f8fafc;
        border-radius: 0 8px 8px 0;
        margin-bottom: 10px;
    ">
        <strong style="color: {color};">{thesis.direction.upper()}</strong> |
        Confidence: {thesis.confidence:.0%} |
        {thesis.time_horizon.title()}
        <br/>
        <small>{thesis.summary[:150]}{'...' if len(thesis.summary) > 150 else ''}</small>
    </div>
    """, unsafe_allow_html=True)


def render_chain_summary(chain: CausalChain):
    """Render a summary of the causal chain.

    Args:
        chain: The causal chain to summarize
    """
    st.markdown("### Chain Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Events", len(chain.events))

    with col2:
        tradeable = chain.get_tradeable_events()
        st.metric("Tradeable Events", len(tradeable))

    with col3:
        st.metric("Causal Links", len(chain.edges))

    # Collect all instruments
    all_instruments = set()
    for event in chain.events:
        all_instruments.update(event.instruments)

    if all_instruments:
        st.markdown("**All Instruments Mentioned:**")
        st.markdown(", ".join(sorted(all_instruments)))

    # Sentiment distribution
    sentiments = {"bullish": 0, "bearish": 0, "neutral": 0}
    for event in chain.events:
        sentiments[event.sentiment] = sentiments.get(event.sentiment, 0) + 1

    st.markdown("**Sentiment Distribution:**")
    sent_cols = st.columns(3)
    with sent_cols[0]:
        st.markdown(f"Bullish: {sentiments['bullish']}")
    with sent_cols[1]:
        st.markdown(f"Bearish: {sentiments['bearish']}")
    with sent_cols[2]:
        st.markdown(f"Neutral: {sentiments['neutral']}")


def render_branch_comparison(comparison: dict):
    """Render a comparison between main chain and a branch.

    Args:
        comparison: Comparison data from BranchManager.compare_branches()
    """
    st.markdown("### Branch Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Main Chain**")
        main = comparison["main_chain"]
        st.metric("Events", main["event_count"])
        st.metric("Tradeable", main["tradeable_count"])
        sentiment_label = "Bullish" if main["avg_sentiment"] > 0.2 else "Bearish" if main["avg_sentiment"] < -0.2 else "Neutral"
        st.metric("Avg Sentiment", sentiment_label)

    with col2:
        st.markdown("**Branch**")
        branch = comparison["branch"]
        st.metric("Events", branch["event_count"])
        st.metric("Tradeable", branch["tradeable_count"])
        sentiment_label = "Bullish" if branch["avg_sentiment"] > 0.2 else "Bearish" if branch["avg_sentiment"] < -0.2 else "Neutral"
        st.metric("Avg Sentiment", sentiment_label)

    st.markdown("---")

    if comparison["unique_to_main"]:
        st.markdown(f"**Instruments unique to main:** {', '.join(comparison['unique_to_main'])}")

    if comparison["unique_to_branch"]:
        st.markdown(f"**Instruments unique to branch:** {', '.join(comparison['unique_to_branch'])}")

    if comparison["common_instruments"]:
        st.markdown(f"**Common instruments:** {', '.join(comparison['common_instruments'])}")
