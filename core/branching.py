"""Branching logic for multiverse scenario exploration."""

from typing import Optional
import uuid

from .models import Event, CausalEdge, CausalChain, BranchGenerationResponse
from llm.base import BaseLLMClient
from prompts.causal_chain import SYSTEM_PROMPT, format_branch_prompt


class BranchManager:
    """Manages branching and alternative scenarios in causal chains."""

    def __init__(self, llm_client: BaseLLMClient):
        """Initialize the branch manager.

        Args:
            llm_client: The LLM client to use for generation
        """
        self.llm_client = llm_client

    def create_branch(
        self,
        chain: CausalChain,
        divergence_event_id: str,
        alternative_description: str,
        branch_name: Optional[str] = None
    ) -> CausalChain:
        """Create a branch in the causal chain at a divergence point.

        Args:
            chain: The original chain
            divergence_event_id: The event ID where the branch diverges
            alternative_description: Description of the alternative scenario
            branch_name: Optional name for the branch

        Returns:
            A new CausalChain representing the alternative branch
        """
        divergence_event = chain.get_event_by_id(divergence_event_id)
        if not divergence_event:
            raise ValueError(f"Event {divergence_event_id} not found in chain")

        # Build context
        chain_context = self._summarize_chain_to_point(chain, divergence_event_id)

        # Generate a new ID for the divergence event in the branch
        new_divergence_id = f"b_{str(uuid.uuid4())[:6]}"

        prompt = format_branch_prompt(
            chain_context=chain_context,
            original_event=divergence_event.description,
            alternative_description=alternative_description,
            divergence_id=new_divergence_id
        )

        response: BranchGenerationResponse = self.llm_client.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            output_type=BranchGenerationResponse,
        )

        # Create the branch chain
        branch_chain = CausalChain(
            root_event=chain.root_event,
            target_outcome=chain.target_outcome
        )

        # Copy events up to (but not including) the divergence point
        upstream_events = chain.get_upstream_events(divergence_event_id)
        upstream_ids = {e.id for e in upstream_events}

        for event in chain.events:
            if event.id in upstream_ids:
                branch_chain.add_event(event)

        # Copy edges between upstream events
        for edge in chain.edges:
            if edge.source_id in upstream_ids and edge.target_id in upstream_ids:
                branch_chain.add_edge(edge)

        # Add the divergence event from the structured response
        div_resp = response.divergence_event
        divergence_new_event = Event(
            id=new_divergence_id,
            description=div_resp.description,
            probability=div_resp.probability,
            financial_impact=div_resp.financial_impact,
            time_horizon=div_resp.time_horizon,
            is_tradeable=div_resp.is_tradeable,
            instruments=div_resp.instruments,
            sentiment=div_resp.sentiment,
        )
        branch_chain.add_event(divergence_new_event)

        # Add edge from last upstream event to divergence
        if upstream_events:
            # Find the edge that pointed to the original divergence event
            for edge in chain.edges:
                if edge.target_id == divergence_event_id and edge.source_id in upstream_ids:
                    branch_chain.add_edge(CausalEdge(
                        source_id=edge.source_id,
                        target_id=new_divergence_id,
                        strength=edge.strength,
                        reasoning=f"Alternative path: {edge.reasoning}"
                    ))
                    break

        # Add downstream events from the branch
        for event_resp in response.events:
            branch_chain.add_event(Event(
                id=event_resp.id,
                description=event_resp.description,
                probability=event_resp.probability,
                financial_impact=event_resp.financial_impact,
                time_horizon=event_resp.time_horizon,
                is_tradeable=event_resp.is_tradeable,
                instruments=event_resp.instruments,
                sentiment=event_resp.sentiment,
            ))

        # Add edges from the branch
        for edge_resp in response.edges:
            branch_chain.add_edge(CausalEdge(
                source_id=edge_resp.source_id,
                target_id=edge_resp.target_id,
                strength=edge_resp.strength,
                reasoning=edge_resp.reasoning,
            ))

        # Store the branch in the original chain
        branch_key = branch_name or f"branch_{divergence_event_id}_{str(uuid.uuid4())[:4]}"
        chain.branches[branch_key] = branch_chain

        return branch_chain

    def compare_branches(self, chain: CausalChain, branch_key: str) -> dict:
        """Compare a branch with the main chain.

        Args:
            chain: The main chain
            branch_key: The key of the branch to compare

        Returns:
            A dictionary with comparison metrics
        """
        if branch_key not in chain.branches:
            raise ValueError(f"Branch {branch_key} not found")

        branch = chain.branches[branch_key]

        # Compare tradeable opportunities
        main_tradeable = chain.get_tradeable_events()
        branch_tradeable = branch.get_tradeable_events()

        main_instruments = set()
        for e in main_tradeable:
            main_instruments.update(e.instruments)

        branch_instruments = set()
        for e in branch_tradeable:
            branch_instruments.update(e.instruments)

        # Calculate average sentiment
        def avg_sentiment(events):
            sentiment_map = {"bullish": 1, "neutral": 0, "bearish": -1}
            if not events:
                return 0
            return sum(sentiment_map.get(e.sentiment, 0) for e in events) / len(events)

        return {
            "main_chain": {
                "event_count": len(chain.events),
                "tradeable_count": len(main_tradeable),
                "instruments": list(main_instruments),
                "avg_sentiment": avg_sentiment(chain.events)
            },
            "branch": {
                "event_count": len(branch.events),
                "tradeable_count": len(branch_tradeable),
                "instruments": list(branch_instruments),
                "avg_sentiment": avg_sentiment(branch.events)
            },
            "unique_to_main": list(main_instruments - branch_instruments),
            "unique_to_branch": list(branch_instruments - main_instruments),
            "common_instruments": list(main_instruments & branch_instruments)
        }

    def list_branches(self, chain: CausalChain) -> list:
        """List all branches in a chain.

        Args:
            chain: The chain to inspect

        Returns:
            List of branch information dictionaries
        """
        branches = []
        for key, branch in chain.branches.items():
            root = branch.get_root_event()
            branches.append({
                "key": key,
                "event_count": len(branch.events),
                "root_description": root.description if root else "Unknown"
            })
        return branches

    def _summarize_chain_to_point(self, chain: CausalChain, up_to_event_id: str) -> str:
        """Summarize the chain up to a specific event."""
        lines = [f"Root Event: {chain.root_event}"]
        if chain.target_outcome:
            lines.append(f"Target Outcome: {chain.target_outcome}")

        # Get upstream events including the divergence point
        upstream = chain.get_upstream_events(up_to_event_id)
        upstream_ids = {e.id for e in upstream}
        upstream_ids.add(up_to_event_id)

        lines.append("\nEvents leading to divergence point:")
        for event in chain.events:
            if event.id in upstream_ids:
                lines.append(f"- [{event.id}] {event.description} (P={event.probability:.1%})")

        return "\n".join(lines)
