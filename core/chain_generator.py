"""Chain generator for creating causal chains using LLMs."""

from typing import Optional, List, Any

from .models import (
    Event,
    CausalEdge,
    CausalChain,
    TradingThesis,
    ChainGenerationResponse,
    ChainExtensionResponse,
)
from llm.base import BaseLLMClient
from prompts.causal_chain import (
    SYSTEM_PROMPT,
    format_chain_generation_prompt,
    format_extend_prompt,
    format_thesis_prompt,
)


# Research-enabled system prompt
RESEARCH_SYSTEM_PROMPT = """You are an expert financial analyst and geopolitical strategist specializing in causal reasoning and scenario analysis.

You have access to web search tools to research current events, market conditions, and historical precedents. USE THESE TOOLS to ground your analysis in real-world data.

Your role is to:
1. Research the hypothesized event using web search to understand current context
2. Analyze potential downstream consequences based on real market dynamics
3. Identify causal chains that lead to tradeable market opportunities
4. Assess probabilities and time horizons grounded in historical precedents

When analyzing an event:
- First, search for recent news and context about the event or similar situations
- Look up current market conditions for relevant instruments
- Find historical precedents to calibrate your probability estimates

Think systematically about second and third-order effects, always considering:
- Direct market impacts (commodities, currencies, equities)
- Supply chain disruptions
- Policy responses (central banks, governments)
- Investor sentiment and positioning
- Historical precedents (USE WEB SEARCH to find these)

Be specific about financial instruments when identifying tradeable opportunities."""


class ChainGenerator:
    """Generates and manages causal chains using LLM."""

    def __init__(self, llm_client: BaseLLMClient, enable_research: bool = False):
        """Initialize the chain generator.

        Args:
            llm_client: The LLM client to use for generation
            enable_research: Whether to enable web search tools for research
        """
        self.llm_client = llm_client
        self.enable_research = enable_research
        self._tools: List[Any] = []

        if enable_research:
            try:
                from tools.web_search import RESEARCH_TOOLS
                self._tools = RESEARCH_TOOLS
            except ImportError:
                pass

    def _get_system_prompt(self) -> str:
        """Get the appropriate system prompt based on research mode."""
        if self.enable_research and self._tools:
            return RESEARCH_SYSTEM_PROMPT
        return SYSTEM_PROMPT

    def generate_initial_chain(self, event: str, target_outcome: Optional[str] = None) -> CausalChain:
        """Generate an initial causal chain from a hypothesized event.

        Args:
            event: The initial event/hypothesis
            target_outcome: Optional target outcome to evaluate path towards

        Returns:
            A CausalChain with events and causal edges
        """
        prompt = format_chain_generation_prompt(event, target_outcome)

        response: ChainGenerationResponse = self.llm_client.generate(
            system_prompt=self._get_system_prompt(),
            user_prompt=prompt,
            output_type=ChainGenerationResponse,
            tools=self._tools if self.enable_research else None,
        )

        # Build the chain from the structured response
        chain = CausalChain(
            root_event=event,
            target_outcome=target_outcome
        )

        # Convert EventResponse to Event
        for event_resp in response.events:
            chain.add_event(Event(
                id=event_resp.id,
                description=event_resp.description,
                probability=event_resp.probability,
                financial_impact=event_resp.financial_impact,
                time_horizon=event_resp.time_horizon,
                is_tradeable=event_resp.is_tradeable,
                instruments=event_resp.instruments,
                sentiment=event_resp.sentiment,
            ))

        # Convert EdgeResponse to CausalEdge
        for edge_resp in response.edges:
            chain.add_edge(CausalEdge(
                source_id=edge_resp.source_id,
                target_id=edge_resp.target_id,
                strength=edge_resp.strength,
                reasoning=edge_resp.reasoning,
            ))

        return chain

    def extend_chain(self, chain: CausalChain, from_event_id: str) -> CausalChain:
        """Extend a chain from a specific event.

        Args:
            chain: The existing chain
            from_event_id: The event ID to extend from

        Returns:
            The extended chain
        """
        from_event = chain.get_event_by_id(from_event_id)
        if not from_event:
            raise ValueError(f"Event {from_event_id} not found in chain")

        # Build context summary
        chain_context = self._summarize_chain(chain)

        prompt = format_extend_prompt(
            chain_context=chain_context,
            from_event_id=from_event_id,
            from_event_description=from_event.description
        )

        response: ChainExtensionResponse = self.llm_client.generate(
            system_prompt=self._get_system_prompt(),
            user_prompt=prompt,
            output_type=ChainExtensionResponse,
            tools=self._tools if self.enable_research else None,
        )

        # Add new events
        for event_resp in response.events:
            chain.add_event(Event(
                id=event_resp.id,
                description=event_resp.description,
                probability=event_resp.probability,
                financial_impact=event_resp.financial_impact,
                time_horizon=event_resp.time_horizon,
                is_tradeable=event_resp.is_tradeable,
                instruments=event_resp.instruments,
                sentiment=event_resp.sentiment,
            ))

        # Add new edges
        for edge_resp in response.edges:
            chain.add_edge(CausalEdge(
                source_id=edge_resp.source_id,
                target_id=edge_resp.target_id,
                strength=edge_resp.strength,
                reasoning=edge_resp.reasoning,
            ))

        return chain

    def regenerate_downstream(self, chain: CausalChain, from_event_id: str, new_description: str) -> CausalChain:
        """Modify an event and regenerate all downstream events.

        Args:
            chain: The existing chain
            from_event_id: The event ID to modify
            new_description: The new description for the event

        Returns:
            A new chain with regenerated downstream events
        """
        # Get the event and its downstream events
        event = chain.get_event_by_id(from_event_id)
        if not event:
            raise ValueError(f"Event {from_event_id} not found in chain")

        downstream = chain.get_downstream_events(from_event_id)
        downstream_ids = {e.id for e in downstream}

        # Create a new chain with events up to and including the modified event
        new_chain = CausalChain(
            root_event=chain.root_event,
            target_outcome=chain.target_outcome
        )

        # Copy events that are not downstream
        for e in chain.events:
            if e.id not in downstream_ids:
                if e.id == from_event_id:
                    # Modify this event
                    new_chain.add_event(Event(
                        id=e.id,
                        description=new_description,
                        probability=e.probability,
                        financial_impact=e.financial_impact,
                        time_horizon=e.time_horizon,
                        is_tradeable=e.is_tradeable,
                        instruments=e.instruments,
                        sentiment=e.sentiment
                    ))
                else:
                    new_chain.add_event(e)

        # Copy edges that don't involve downstream events
        for edge in chain.edges:
            if edge.source_id not in downstream_ids and edge.target_id not in downstream_ids:
                new_chain.add_edge(edge)

        # Now extend from the modified event
        return self.extend_chain(new_chain, from_event_id)

    def generate_thesis(self, chain: CausalChain) -> TradingThesis:
        """Generate a trading thesis from a causal chain.

        Args:
            chain: The causal chain to analyze

        Returns:
            A TradingThesis object
        """
        chain_summary = self._summarize_chain(chain)
        tradeable_events = self._summarize_tradeable_events(chain)

        prompt = format_thesis_prompt(chain_summary, tradeable_events)

        thesis: TradingThesis = self.llm_client.generate(
            system_prompt=self._get_system_prompt(),
            user_prompt=prompt,
            output_type=TradingThesis,
            tools=self._tools if self.enable_research else None,
        )

        return thesis

    def _summarize_chain(self, chain: CausalChain) -> str:
        """Create a text summary of a chain for context."""
        lines = [f"Root Event: {chain.root_event}"]
        if chain.target_outcome:
            lines.append(f"Target Outcome: {chain.target_outcome}")
        lines.append("\nEvents:")

        for event in chain.events:
            lines.append(f"- [{event.id}] {event.description} (P={event.probability:.1%}, {event.time_horizon})")

        lines.append("\nCausal Links:")
        for edge in chain.edges:
            lines.append(f"- {edge.source_id} -> {edge.target_id}: {edge.reasoning} (strength={edge.strength:.1%})")

        return "\n".join(lines)

    def _summarize_tradeable_events(self, chain: CausalChain) -> str:
        """Summarize tradeable events in the chain."""
        tradeable = chain.get_tradeable_events()
        if not tradeable:
            return "No directly tradeable events identified."

        lines = []
        for event in tradeable:
            instruments = ", ".join(event.instruments) if event.instruments else "No specific instruments"
            lines.append(f"- {event.description}")
            lines.append(f"  Instruments: {instruments}")
            lines.append(f"  Sentiment: {event.sentiment}, Time: {event.time_horizon}")

        return "\n".join(lines)
