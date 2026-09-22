# Catalyst: Causal Chain Explorer - MVP Plan

> This plan was created before implementation to guide development.

## Overview
Build a Streamlit-based tool that generates and visualizes causal chains from hypothesized events, allowing users to explore "multiverse" scenarios and derive trading theses.

## Technology Decisions

| Component | Choice | Alternatives Considered | Rationale |
|-----------|--------|------------------------|-----------|
| **Frontend** | Streamlit | Gradio, Flask+React, Dash | Rapid prototyping, built-in state management, native Python, excellent for data apps |
| **LLM Framework** | OpenAI Agents SDK | LangChain, direct API calls, LlamaIndex | Lightweight, native tool support, clean abstraction for multi-provider |
| **LLM Providers** | Claude + OpenAI | Gemini, local models | Best reasoning capabilities for causal analysis, easy API access |
| **Data Validation** | Pydantic v2 | dataclasses, attrs, TypedDict | Automatic JSON schema generation, runtime validation, IDE support |
| **Graph Visualization** | streamlit-agraph (vis.js) | PyVis, Graphviz, D3.js, Cytoscape | Native Streamlit integration, interactive, good hierarchical layouts |
| **Graph Library** | NetworkX | igraph, graph-tool | Python-native, simple API, sufficient for DAG operations |
| **Web Research** | Tavily API | SerpAPI, Google Search API, Bing | Built for AI agents, structured results, good free tier |
| **Config Management** | python-dotenv | environs, dynaconf | Simple, widely adopted, sufficient for API keys |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                        │
│  ┌─────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ Event Input │  │ Graph Visualizer │  │ Thesis Panel   │  │
│  └─────────────┘  └──────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Core Engine                              │
│  ┌──────────────────┐  ┌─────────────────┐                  │
│  │ Chain Generator  │  │ Branch Manager  │                  │
│  └──────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM Abstraction Layer                     │
│  ┌────────────────┐        ┌────────────────┐               │
│  │ Claude Client  │        │ OpenAI Client  │               │
│  └────────────────┘        └────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

```
catalyst/
├── app.py                    # Streamlit main app
├── core/
│   ├── __init__.py
│   ├── chain_generator.py    # LLM-powered causal chain generation
│   ├── models.py             # Data models (Event, CausalEdge, Chain)
│   └── branching.py          # Multiverse branching logic
├── llm/
│   ├── __init__.py
│   ├── base.py               # Abstract LLM interface
│   ├── claude_client.py      # Anthropic Claude integration
│   └── openai_client.py      # OpenAI GPT integration
├── ui/
│   ├── __init__.py
│   ├── graph_viz.py          # Graph visualization components
│   └── thesis_panel.py       # Trading thesis generation UI
├── prompts/
│   └── causal_chain.py       # Prompt templates
├── requirements.txt
└── .env.example
```

## Data Models

### Event Node
```python
class Event:
    id: str
    description: str
    probability: float          # 0-1 confidence
    financial_impact: str       # Brief description of market impact
    time_horizon: str           # "immediate", "days", "weeks", "months"
    is_tradeable: bool          # Can this be directly traded on?
    instruments: List[str]      # Relevant tickers/instruments
```

### Causal Edge
```python
class CausalEdge:
    source_id: str
    target_id: str
    strength: float             # 0-1 causal strength
    reasoning: str              # Why this causal link exists
```

### Causal Chain
```python
class CausalChain:
    root_event: str             # Original hypothesis
    events: List[Event]
    edges: List[CausalEdge]
    branches: Dict[str, 'CausalChain']  # Alternative universes
```

## Implementation Steps

### Step 1: Project Setup
- Create directory structure
- Set up requirements.txt (streamlit, anthropic, openai, networkx, pyvis, pydantic)
- Create .env.example with API key placeholders

### Step 2: Data Models (`core/models.py`)
- Define Event, CausalEdge, CausalChain dataclasses using Pydantic
- JSON serialization methods for LLM communication

### Step 3: LLM Abstraction Layer
- `llm/base.py`: Abstract base class with `generate_chain()` method
- `llm/claude_client.py`: Claude implementation
- `llm/openai_client.py`: OpenAI implementation

### Step 4: Prompt Engineering (`prompts/causal_chain.py`)
- System prompt establishing financial analyst persona
- Few-shot examples of causal chains
- Output format specification (structured JSON)
- Prompts for: initial chain, branch generation, thesis synthesis

### Step 5: Chain Generator (`core/chain_generator.py`)
- `generate_initial_chain(event: str) -> CausalChain`
- `extend_chain(chain: CausalChain, from_event_id: str) -> CausalChain`
- `modify_event(chain: CausalChain, event_id: str, new_description: str) -> CausalChain`

### Step 6: Graph Visualization (`ui/graph_viz.py`)
- Use `streamlit-agraph` for interactive graphs
- Color coding: green (bullish), red (bearish), yellow (neutral)
- Node size based on probability
- Edge thickness based on causal strength
- Click handlers for node selection

### Step 7: Branching Logic (`core/branching.py`)
- `create_branch(chain: CausalChain, divergence_point: str, alternative: str) -> CausalChain`
- Store branches with reference to divergence point
- Comparison view between branches

### Step 8: Trading Thesis Panel (`ui/thesis_panel.py`)
- Synthesize chain into actionable thesis
- List specific instruments to trade
- Risk factors from chain analysis
- Time horizons for positions

### Step 9: Main App (`app.py`)
- Streamlit layout with sidebar for settings
- Main area: graph visualization
- Right panel: thesis and event details
- Session state for chain history

## Key Features for MVP

### Must Have
1. **Event Input**: Text field for initial event, optional "target outcome" field
2. **Chain Generation**: Generate 5-7 downstream events with causal links
3. **Interactive Graph**: Visualize chain, click nodes for details
4. **Branch Creation**: Modify any event, regenerate downstream
5. **LLM Toggle**: Switch between Claude and GPT-4
6. **Trading Thesis**: Generate summary of tradeable opportunities

### Nice to Have (Post-MVP)
- Save/load chains
- Compare multiple branches side-by-side
- Probability calibration
- Export to PDF/markdown
- Web research integration

## Verification Plan
1. Run `streamlit run app.py` and verify app loads
2. Enter sample event (e.g., "Strait of Hormuz opens")
3. Verify chain generates with valid structure
4. Click a node and verify details display
5. Modify an event and verify downstream regenerates
6. Toggle LLM provider and verify both work
7. Generate trading thesis and verify coherent output

## Design Principles

1. **Provider Agnostic**: Abstract LLM layer allows switching between Claude/OpenAI without code changes
2. **Structured Output**: Use Pydantic models for type-safe LLM responses, not string parsing
3. **Deterministic Layout**: Fixed graph positions prevent jarring re-renders on interaction
4. **Graceful Degradation**: Web research is optional; app works without Tavily API key
5. **Minimal Dependencies**: Avoid heavy frameworks; prefer lightweight, focused libraries

## Dependencies
```
streamlit>=1.28.0
openai-agents>=0.0.3
openai>=1.3.0
pydantic>=2.0.0
streamlit-agraph>=0.0.45
python-dotenv>=1.0.0
networkx>=3.0
tavily-python>=0.3.0
```
