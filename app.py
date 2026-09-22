"""Catalyst: Causal Chain Explorer - Main Streamlit Application."""

import os
import streamlit as st
from dotenv import load_dotenv

from core.models import CausalChain, TradingThesis
from core.chain_generator import ChainGenerator
from core.branching import BranchManager
from llm.claude_client import ClaudeClient
from llm.openai_client import OpenAIClient
from ui.graph_viz import render_causal_graph, render_event_details, render_legend
from ui.thesis_panel import render_thesis_panel, render_chain_summary

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Catalyst: Causal Chain Explorer",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "chain" not in st.session_state:
    st.session_state.chain = None
if "selected_event_id" not in st.session_state:
    st.session_state.selected_event_id = None
if "thesis" not in st.session_state:
    st.session_state.thesis = None
if "llm_provider" not in st.session_state:
    st.session_state.llm_provider = os.getenv("DEFAULT_LLM_PROVIDER", "claude")
if "enable_research" not in st.session_state:
    st.session_state.enable_research = os.getenv("ENABLE_RESEARCH", "false").lower() == "true"
if "chain_history" not in st.session_state:
    st.session_state.chain_history = []


def get_llm_client():
    """Get the appropriate LLM client based on settings."""
    provider = st.session_state.llm_provider
    try:
        if provider == "claude":
            return ClaudeClient()
        else:
            return OpenAIClient()
    except ValueError as e:
        st.error(f"Failed to initialize {provider} client: {e}")
        st.info("Please set the appropriate API key in your environment or .env file.")
        return None


def check_research_available() -> bool:
    """Check if research tools are available."""
    tavily_key = os.getenv("TAVILY_API_KEY")
    return bool(tavily_key)


def main():
    """Main application entry point."""
    # Sidebar
    with st.sidebar:
        st.title("Catalyst")
        st.caption("Causal Chain Explorer")

        st.markdown("---")

        # LLM Provider selection
        st.subheader("Settings")
        provider = st.radio(
            "LLM Provider",
            ["claude", "openai"],
            index=0 if st.session_state.llm_provider == "claude" else 1,
            key="provider_radio"
        )
        if provider != st.session_state.llm_provider:
            st.session_state.llm_provider = provider

        # Research mode toggle
        research_available = check_research_available()
        enable_research = st.toggle(
            "Enable Web Research",
            value=st.session_state.enable_research and research_available,
            disabled=not research_available,
            help="Use web search to ground analysis in current events and market data"
        )
        st.session_state.enable_research = enable_research

        if not research_available:
            st.caption("Set TAVILY_API_KEY to enable research")
        elif enable_research:
            st.caption("Agent will search the web for context")

        st.markdown("---")

        # Chain info
        if st.session_state.chain:
            render_chain_summary(st.session_state.chain)

            st.markdown("---")

            # Branch management
            st.subheader("Branches")
            branches = list(st.session_state.chain.branches.keys())
            if branches:
                selected_branch = st.selectbox("View Branch", ["Main Chain"] + branches)
                if selected_branch != "Main Chain":
                    if st.button("Switch to Branch"):
                        # Store current as a branch and switch
                        st.session_state.chain = st.session_state.chain.branches[selected_branch]
                        st.rerun()
            else:
                st.caption("No alternative branches yet")

        st.markdown("---")
        render_legend()

    # Main content
    st.title("Causal Chain Explorer")

    # Input section
    with st.expander("Generate New Chain", expanded=st.session_state.chain is None):
        col1, col2 = st.columns([2, 1])

        with col1:
            event_input = st.text_area(
                "Hypothesized Event",
                placeholder="e.g., 'Strait of Hormuz closes due to military conflict'",
                help="Enter the initial event or catalyst to analyze"
            )

        with col2:
            target_outcome = st.text_input(
                "Target Outcome (Optional)",
                placeholder="e.g., 'Oil prices spike 50%'",
                help="Optional: Specify an outcome to trace path towards"
            )

        research_status = " (with web research)" if st.session_state.enable_research else ""
        if st.button("Generate Causal Chain", type="primary", disabled=not event_input):
            llm_client = get_llm_client()
            if llm_client:
                spinner_msg = f"Generating causal chain using {st.session_state.llm_provider.title()}{research_status}..."
                with st.spinner(spinner_msg):
                    try:
                        generator = ChainGenerator(
                            llm_client,
                            enable_research=st.session_state.enable_research
                        )
                        chain = generator.generate_initial_chain(
                            event_input,
                            target_outcome if target_outcome else None
                        )
                        st.session_state.chain = chain
                        st.session_state.selected_event_id = None
                        st.session_state.thesis = None
                        st.session_state.chain_history.append(chain.model_dump())
                        st.success("Causal chain generated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating chain: {e}")

    # Display chain if exists
    if st.session_state.chain:
        chain = st.session_state.chain

        # Main layout: Graph + Details panel
        graph_col, details_col = st.columns([2, 1])

        with graph_col:
            st.subheader("Causal Chain Visualization")
            clicked = render_causal_graph(
                chain,
                selected_event_id=st.session_state.selected_event_id,
                height=500
            )

            if clicked and clicked != st.session_state.selected_event_id:
                st.session_state.selected_event_id = clicked
                st.rerun()

        with details_col:
            # Event details
            if st.session_state.selected_event_id:
                event = chain.get_event_by_id(st.session_state.selected_event_id)
                if event:
                    render_event_details(event, chain)

                    st.markdown("---")

                    # Actions for selected event
                    st.subheader("Actions")

                    # Extend chain
                    if st.button("Extend from this event"):
                        llm_client = get_llm_client()
                        if llm_client:
                            with st.spinner("Extending chain..."):
                                try:
                                    generator = ChainGenerator(
                                        llm_client,
                                        enable_research=st.session_state.enable_research
                                    )
                                    chain = generator.extend_chain(chain, event.id)
                                    st.session_state.chain = chain
                                    st.success("Chain extended!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error extending chain: {e}")

                    # Create branch
                    st.markdown("**Create Alternative Branch:**")
                    alternative = st.text_input(
                        "Alternative scenario",
                        placeholder="What if instead...",
                        key="branch_input"
                    )
                    if st.button("Create Branch", disabled=not alternative):
                        llm_client = get_llm_client()
                        if llm_client:
                            with st.spinner("Creating alternative branch..."):
                                try:
                                    branch_mgr = BranchManager(llm_client)
                                    branch = branch_mgr.create_branch(
                                        chain,
                                        event.id,
                                        alternative
                                    )
                                    st.session_state.chain = chain  # Updated with branch
                                    st.success("Branch created!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error creating branch: {e}")

                    # Modify event
                    st.markdown("**Modify Event:**")
                    modified_desc = st.text_area(
                        "New description",
                        value=event.description,
                        key="modify_input"
                    )
                    if st.button("Regenerate Downstream", disabled=modified_desc == event.description):
                        llm_client = get_llm_client()
                        if llm_client:
                            with st.spinner("Regenerating downstream events..."):
                                try:
                                    generator = ChainGenerator(
                                        llm_client,
                                        enable_research=st.session_state.enable_research
                                    )
                                    chain = generator.regenerate_downstream(
                                        chain,
                                        event.id,
                                        modified_desc
                                    )
                                    st.session_state.chain = chain
                                    st.success("Downstream regenerated!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error regenerating: {e}")
            else:
                st.info("Click on a node in the graph to see details and actions.")

        # Trading thesis section
        st.markdown("---")

        thesis_col1, thesis_col2 = st.columns([1, 2])

        with thesis_col1:
            if st.button("Generate Trading Thesis", type="secondary"):
                llm_client = get_llm_client()
                if llm_client:
                    with st.spinner("Synthesizing trading thesis..."):
                        try:
                            generator = ChainGenerator(
                                llm_client,
                                enable_research=st.session_state.enable_research
                            )
                            thesis = generator.generate_thesis(chain)
                            st.session_state.thesis = thesis
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error generating thesis: {e}")

        with thesis_col2:
            if st.session_state.thesis:
                render_thesis_panel(st.session_state.thesis)

    else:
        # Empty state
        st.markdown("""
        ### Welcome to Catalyst

        Enter a hypothesized event above to generate a causal chain of downstream events
        and explore trading opportunities.

        **Example events to try:**
        - "Strait of Hormuz closes due to military conflict"
        - "Federal Reserve announces surprise 100bp rate cut"
        - "Major semiconductor fab in Taiwan goes offline"
        - "EU passes comprehensive AI regulation"
        """)


if __name__ == "__main__":
    main()
