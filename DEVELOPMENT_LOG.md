# Catalyst Development Log

## Session Summary

Built a **Causal Chain Explorer** - a Streamlit app that uses LLMs to generate and visualize causal chains from hypothesized events, helping identify trading opportunities.

---

## Implementation Steps

### 1. Project Setup & Core Architecture
- Created project structure: `core/`, `llm/`, `ui/`, `tools/`, `prompts/`
- Implemented Pydantic data models (`Event`, `CausalEdge`, `CausalChain`, `TradingThesis`)
- Built LLM abstraction layer supporting both Claude and OpenAI via OpenAI Agents SDK

### 2. LLM Integration Challenges & Solutions

**Problem**: Anthropic's OpenAI-compatible API doesn't support `response_format: json_schema` for structured output.

**Solution**: Added fallback in `BaseLLMClient` that:
- Detects provider capability via `supports_structured_output` property
- For Claude: Embeds JSON schema in prompt, parses response manually
- For OpenAI: Uses native structured output

**Problem**: Pydantic `Field(ge=0.0, le=1.0)` constraints generate unsupported JSON schema properties.

**Solution**: Removed constraints, moved validation info to field descriptions.

### 3. Graph Visualization

**Tech**: `streamlit-agraph` (vis.js wrapper)

**Features implemented**:
- Color-coded nodes by sentiment (green=bullish, red=bearish, yellow=neutral)
- Node size scaled by probability
- Hierarchical top-down layout
- BFS-computed levels for proper ordering

**Problem**: Graph rearranged on every click due to Streamlit re-renders.

**Solution**: Computed deterministic x,y positions from BFS levels, set `fixed=True` on nodes.

### 4. Additional Features
- Web research tools via Tavily API integration
- Branch creation for "what-if" scenarios
- Trading thesis generation
- Makefile for easy setup/run

---

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| OpenAI Agents SDK | Unified interface for Claude + OpenAI with tool support |
| Pydantic models | Type safety + automatic JSON schema generation |
| Fixed graph positions | Prevents jarring re-layouts on interaction |
| JSON fallback for Claude | Anthropic compatibility layer limitations |

---

## Files Created/Modified

```
catalyst/
├── app.py                 # Streamlit main app
├── core/
│   ├── models.py          # Pydantic data models
│   ├── chain_generator.py # LLM orchestration
│   └── branching.py       # Alternative scenario branches
├── llm/
│   ├── base.py            # Abstract client + JSON fallback
│   ├── claude_client.py   # Anthropic via OpenAI compat
│   └── openai_client.py   # OpenAI GPT
├── ui/
│   ├── graph_viz.py       # vis.js graph rendering
│   └── thesis_panel.py    # Trading thesis display
├── tools/
│   └── web_search.py      # Tavily research tools
├── prompts/
│   └── causal_chain.py    # LLM prompt templates
├── Makefile               # Build/run commands
├── README.md              # User documentation
└── CLAUDE.md              # AI assistant guidance
```

---

## Run Instructions

```bash
make setup    # Creates venv, installs deps, creates .env
# Edit .env with API keys
make run      # Starts app at http://localhost:8501
```
