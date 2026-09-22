# Catalyst: Causal Chain Explorer

A Streamlit-based tool that generates and visualizes causal chains from hypothesized events, helping identify trading opportunities through scenario analysis.

## Features

- **Causal Chain Generation**: Enter a hypothesized event and generate downstream consequences using LLMs
- **Interactive Graph Visualization**: Explore causal relationships with color-coded sentiment and probability-scaled nodes
- **Trading Thesis Synthesis**: Generate actionable trading theses with specific instruments and entry triggers
- **Branching Scenarios**: Create "what if" alternative branches to explore different outcomes
- **Web Research Integration**: Optional Tavily-powered research to ground analysis in current events
- **Multi-LLM Support**: Switch between Claude and OpenAI

## Quick Start

```bash
# Setup (creates venv, installs deps, creates .env)
make setup

# Edit .env with your API keys
vim .env

# Run the app
make run
```

The app will be available at http://localhost:8501

## Configuration

Copy `.env.example` to `.env` and set:

- `ANTHROPIC_API_KEY` - Required for Claude
- `OPENAI_API_KEY` - Required for OpenAI
- `TAVILY_API_KEY` - Optional, enables web research
- `DEFAULT_LLM_PROVIDER` - `claude` or `openai`

## Usage

1. Enter a hypothesized event (e.g., "Strait of Hormuz closes due to military conflict")
2. Optionally specify a target outcome to trace paths toward
3. Click "Generate Causal Chain"
4. Explore the graph - click nodes for details
5. Extend chains, create branches, or generate trading theses

## Example Events

- "Federal Reserve announces surprise 100bp rate cut"
- "Major semiconductor fab in Taiwan goes offline"
- "EU passes comprehensive AI regulation"
- "OPEC announces 2M barrel/day production cut"
