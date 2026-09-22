# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
make setup      # First-time setup: creates venv, installs deps, creates .env from template
make run        # Run the Streamlit app (installs deps if needed)
make dev        # Run with auto-reload on file save
make test       # Run pytest
make lint       # Run ruff linter
make clean      # Remove __pycache__ and .pyc files
make reset      # Remove venv entirely and start fresh
```

## Architecture

Catalyst is a Streamlit app that generates causal chains from hypothesized events using LLMs, visualizes them as interactive graphs, and synthesizes trading theses.

### Data Flow

1. User enters event hypothesis → `ChainGenerator.generate_initial_chain()`
2. LLM returns structured `ChainGenerationResponse` (events + edges)
3. Response converted to `CausalChain` model (nodes/edges for graph)
4. `render_causal_graph()` displays via streamlit-agraph with BFS-computed levels
5. User can extend, branch, or modify → regenerates downstream events

### Key Modules

- **`llm/base.py`**: Abstract `BaseLLMClient` with `generate()` method. Handles structured output via Pydantic models. Claude falls back to JSON-in-prompt parsing since Anthropic's OpenAI-compatible API doesn't support `response_format: json_schema`.

- **`core/chain_generator.py`**: Orchestrates LLM calls. `ChainGenerator` takes an `llm_client` and optional `enable_research` flag to include Tavily web search tools.

- **`core/models.py`**: Pydantic models for `Event`, `CausalEdge`, `CausalChain`, `TradingThesis`, and LLM response schemas (`ChainGenerationResponse`, etc.). Note: Avoid `ge`/`le` constraints on floats—they generate JSON schema properties unsupported by Anthropic.

- **`ui/graph_viz.py`**: Converts `CausalChain` to vis.js nodes/edges. Computes hierarchical levels via BFS from root for top-down layout.

### LLM Provider Handling

Claude uses `x-api-key` header (not Bearer auth) via OpenAI SDK's compatibility layer. The `ClaudeClient.supports_structured_output` returns `False`, triggering the JSON-prompt fallback in `BaseLLMClient.generate()`.

### Adding Tools

Tools are defined in `tools/web_search.py` using `@function_tool` decorator from openai-agents SDK. To add tools, append to `RESEARCH_TOOLS` list and they'll be available when research mode is enabled.
