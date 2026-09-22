"""Prompt templates for causal chain generation."""

SYSTEM_PROMPT = """You are an expert financial analyst and geopolitical strategist specializing in causal reasoning and scenario analysis. Your role is to:

1. Analyze hypothesized events and their potential downstream consequences
2. Identify causal chains that lead to tradeable market opportunities
3. Assess probabilities and time horizons for each step in the causal chain
4. Consider multiple scenarios and alternative paths

You think systematically about second and third-order effects, always considering:
- Direct market impacts (commodities, currencies, equities)
- Supply chain disruptions
- Policy responses (central banks, governments)
- Investor sentiment and positioning
- Historical precedents

Be specific about financial instruments when identifying tradeable opportunities."""

CHAIN_GENERATION_PROMPT = """Given the following hypothesized event, generate a causal chain of 5-7 downstream events that would logically follow.

**Initial Event:** {event}

{target_section}

For each event in the chain:
- Assign a unique ID (e1, e2, e3, etc.) starting with e1 for the initial event
- Provide a clear, specific description
- Estimate probability (0-1) that it occurs given upstream events
- Describe the financial/market impact
- Specify time horizon: "immediate" (hours), "days" (1-7 days), "weeks" (1-8 weeks), or "months" (2-12 months)
- Determine if it's directly tradeable with financial instruments
- List specific instruments if tradeable (tickers like SPY, CL=F, GLD, etc.)
- Assess market sentiment: "bullish", "bearish", or "neutral"

For each causal link between events:
- Specify source and target event IDs
- Rate causal strength (0-1)
- Explain why this causal relationship exists

Think step by step about the causal chain, ensuring each link is logically sound and probabilities reflect genuine uncertainty."""

EXTEND_CHAIN_PROMPT = """You are extending an existing causal chain from a specific event.

**Original Chain Context:**
{chain_context}

**Extend from this event:**
Event ID: {from_event_id}
Description: {from_event_description}

Generate 3-5 additional downstream events that follow from this specific event. These should be new events not already in the chain.

For each new event:
- Use unique IDs that don't conflict with existing ones (e.g., e_ext1, e_ext2, etc.)
- Follow the same format: description, probability, financial impact, time horizon, tradeability, instruments, sentiment

Create causal edges connecting from the source event ({from_event_id}) to your new events, and between your new events as appropriate."""

BRANCH_GENERATION_PROMPT = """You are creating an alternative scenario branch in a causal chain.

**Original Chain:**
{chain_context}

**Divergence Point:**
Original Event: {original_event}

**Alternative Scenario:**
Instead of the original event, assume: {alternative_description}

Generate a new causal chain that follows from this alternative:

1. Create a divergence_event representing the alternative scenario at the divergence point
   - Use ID: {divergence_id}
   - Describe how this differs from the original

2. Generate 4-6 downstream events showing how this alternative plays out differently
   - Use unique IDs (e.g., b1, b2, etc.)
   - Show how outcomes differ from the main chain

3. Create causal links between all events in this branch"""

THESIS_GENERATION_PROMPT = """Based on the following causal chain analysis, synthesize a trading thesis.

**Causal Chain:**
{chain_summary}

**Tradeable Events in Chain:**
{tradeable_events}

Generate a comprehensive trading thesis:

1. **Summary**: A 2-3 sentence overview of the investment thesis
2. **Direction**: Overall market direction (bullish, bearish, or neutral)
3. **Primary Instruments**: Prioritized list of instruments to trade (be specific with tickers)
4. **Entry Triggers**: Specific observable events that would confirm the thesis
5. **Risk Factors**: What could invalidate the thesis
6. **Time Horizon**: Expected holding period (immediate, days, weeks, or months)
7. **Confidence**: Your confidence level (0-1) in this thesis
8. **Key Events to Monitor**: Upcoming events or data releases to watch"""


def format_chain_generation_prompt(event: str, target_outcome: str = None) -> str:
    """Format the chain generation prompt with the given event."""
    target_section = ""
    if target_outcome:
        target_section = f"""**Target Outcome to Evaluate:** {target_outcome}

As you build the chain, consider whether and how the initial event could lead to this target outcome. If a path exists, make sure to include it. If the path is unlikely or doesn't exist, explain why in the chain structure."""

    return CHAIN_GENERATION_PROMPT.format(event=event, target_section=target_section)


def format_extend_prompt(chain_context: str, from_event_id: str, from_event_description: str) -> str:
    """Format the extend chain prompt."""
    return EXTEND_CHAIN_PROMPT.format(
        chain_context=chain_context,
        from_event_id=from_event_id,
        from_event_description=from_event_description
    )


def format_branch_prompt(chain_context: str, original_event: str, alternative_description: str, divergence_id: str) -> str:
    """Format the branch generation prompt."""
    return BRANCH_GENERATION_PROMPT.format(
        chain_context=chain_context,
        original_event=original_event,
        alternative_description=alternative_description,
        divergence_id=divergence_id
    )


def format_thesis_prompt(chain_summary: str, tradeable_events: str) -> str:
    """Format the thesis generation prompt."""
    return THESIS_GENERATION_PROMPT.format(
        chain_summary=chain_summary,
        tradeable_events=tradeable_events
    )
