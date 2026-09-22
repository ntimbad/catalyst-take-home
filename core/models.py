"""Data models for the Causal Chain Explorer."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class Event(BaseModel):
    """Represents a single event node in the causal chain."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str
    probability: float = Field(description="Confidence level between 0.0 and 1.0")
    financial_impact: str = Field(description="Brief description of market impact")
    time_horizon: str = Field(description="immediate, days, weeks, or months")
    is_tradeable: bool = Field(default=False, description="Can this be directly traded on?")
    instruments: List[str] = Field(default_factory=list, description="Relevant tickers/instruments")
    sentiment: str = Field(default="neutral", description="bullish, bearish, or neutral")

    def __hash__(self):
        return hash(self.id)


class CausalEdge(BaseModel):
    """Represents a causal relationship between two events."""

    source_id: str
    target_id: str
    strength: float = Field(description="Causal strength between 0.0 and 1.0")
    reasoning: str = Field(description="Why this causal link exists")


class CausalChain(BaseModel):
    """Represents a complete causal chain with events and edges."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    root_event: str = Field(description="Original hypothesis/event description")
    target_outcome: Optional[str] = Field(default=None, description="Optional target outcome to reach")
    events: List[Event] = Field(default_factory=list)
    edges: List[CausalEdge] = Field(default_factory=list)
    branches: Dict[str, "CausalChain"] = Field(default_factory=dict, description="Alternative universes keyed by divergence point")

    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """Get an event by its ID."""
        for event in self.events:
            if event.id == event_id:
                return event
        return None

    def get_root_event(self) -> Optional[Event]:
        """Get the root event (first event in the chain)."""
        if self.events:
            return self.events[0]
        return None

    def get_downstream_events(self, event_id: str) -> List[Event]:
        """Get all events that are downstream from a given event."""
        downstream_ids = set()
        to_process = [event_id]

        while to_process:
            current_id = to_process.pop(0)
            for edge in self.edges:
                if edge.source_id == current_id and edge.target_id not in downstream_ids:
                    downstream_ids.add(edge.target_id)
                    to_process.append(edge.target_id)

        return [e for e in self.events if e.id in downstream_ids]

    def get_upstream_events(self, event_id: str) -> List[Event]:
        """Get all events that are upstream from a given event."""
        upstream_ids = set()
        to_process = [event_id]

        while to_process:
            current_id = to_process.pop(0)
            for edge in self.edges:
                if edge.target_id == current_id and edge.source_id not in upstream_ids:
                    upstream_ids.add(edge.source_id)
                    to_process.append(edge.source_id)

        return [e for e in self.events if e.id in upstream_ids]

    def get_edges_from(self, event_id: str) -> List[CausalEdge]:
        """Get all edges originating from an event."""
        return [e for e in self.edges if e.source_id == event_id]

    def get_edges_to(self, event_id: str) -> List[CausalEdge]:
        """Get all edges pointing to an event."""
        return [e for e in self.edges if e.target_id == event_id]

    def add_event(self, event: Event) -> None:
        """Add an event to the chain."""
        self.events.append(event)

    def add_edge(self, edge: CausalEdge) -> None:
        """Add an edge to the chain."""
        self.edges.append(edge)

    def remove_event(self, event_id: str) -> None:
        """Remove an event and its associated edges."""
        self.events = [e for e in self.events if e.id != event_id]
        self.edges = [e for e in self.edges if e.source_id != event_id and e.target_id != event_id]

    def get_tradeable_events(self) -> List[Event]:
        """Get all tradeable events in the chain."""
        return [e for e in self.events if e.is_tradeable]

    def to_networkx(self):
        """Convert to NetworkX graph for visualization."""
        import networkx as nx

        G = nx.DiGraph()

        for event in self.events:
            G.add_node(
                event.id,
                description=event.description,
                probability=event.probability,
                financial_impact=event.financial_impact,
                time_horizon=event.time_horizon,
                is_tradeable=event.is_tradeable,
                instruments=event.instruments,
                sentiment=event.sentiment,
            )

        for edge in self.edges:
            G.add_edge(
                edge.source_id,
                edge.target_id,
                strength=edge.strength,
                reasoning=edge.reasoning,
            )

        return G


class TradingThesis(BaseModel):
    """Represents a synthesized trading thesis from a causal chain."""

    summary: str = Field(description="High-level thesis summary")
    direction: str = Field(description="bullish, bearish, or neutral")
    primary_instruments: List[str] = Field(default_factory=list)
    entry_triggers: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    time_horizon: str = Field(description="Expected holding period")
    confidence: float = Field(description="Confidence level, value between 0.0 and 1.0")
    key_events_to_monitor: List[str] = Field(default_factory=list)


# LLM Response Models for Structured Output

class EventResponse(BaseModel):
    """Event as returned by LLM (without default id generation)."""

    id: str = Field(description="Unique identifier for this event, e.g. e1, e2, etc.")
    description: str = Field(description="Clear description of the event")
    probability: float = Field(description="Probability this occurs given upstream events, value between 0.0 and 1.0")
    financial_impact: str = Field(description="Brief description of market/financial impact")
    time_horizon: str = Field(description="When this occurs: immediate, days, weeks, or months")
    is_tradeable: bool = Field(description="Can this be directly traded on with financial instruments?")
    instruments: List[str] = Field(default_factory=list, description="Relevant tickers/instruments if tradeable")
    sentiment: str = Field(description="Market sentiment: bullish, bearish, or neutral")


class EdgeResponse(BaseModel):
    """Causal edge as returned by LLM."""

    source_id: str = Field(description="ID of the source event")
    target_id: str = Field(description="ID of the target event")
    strength: float = Field(description="Causal strength, value between 0.0 and 1.0")
    reasoning: str = Field(description="Why this causal link exists")


class ChainGenerationResponse(BaseModel):
    """Response model for initial chain generation."""

    events: List[EventResponse] = Field(description="List of events in the causal chain, starting with the initial event")
    edges: List[EdgeResponse] = Field(description="Causal links between events")


class ChainExtensionResponse(BaseModel):
    """Response model for extending a chain from a specific event."""

    events: List[EventResponse] = Field(description="New downstream events to add")
    edges: List[EdgeResponse] = Field(description="Causal links for the new events")


class BranchGenerationResponse(BaseModel):
    """Response model for creating an alternative branch."""

    divergence_event: EventResponse = Field(description="The alternative event at the divergence point")
    events: List[EventResponse] = Field(description="Downstream events following the alternative")
    edges: List[EdgeResponse] = Field(description="Causal links in the alternative branch")
