"""Web search and research tools using Tavily API."""

import os
from typing import List, Optional
from pydantic import BaseModel, Field
from agents import function_tool

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False


class WebSearchResult(BaseModel):
    """A single web search result."""
    title: str
    url: str
    content: str
    score: float = 0.0


class WebSearchResponse(BaseModel):
    """Response from web search."""
    query: str
    results: List[WebSearchResult]


def _get_tavily_client() -> Optional["TavilyClient"]:
    """Get Tavily client if available and configured."""
    if not TAVILY_AVAILABLE:
        return None

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return None

    return TavilyClient(api_key=api_key)


@function_tool
def web_search(
    query: str,
    search_depth: str = "basic",
    max_results: int = 5,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
) -> str:
    """Search the web for current information relevant to financial analysis.

    Use this tool to:
    - Research recent news about geopolitical events, companies, or markets
    - Find current market conditions and economic data
    - Look up historical precedents for similar events
    - Verify facts about financial instruments or policies

    Args:
        query: The search query. Be specific and include relevant financial/market terms.
        search_depth: "basic" for quick search, "advanced" for more comprehensive results.
        max_results: Maximum number of results to return (1-10).
        include_domains: Optional list of domains to restrict search to (e.g., ["reuters.com", "bloomberg.com"]).
        exclude_domains: Optional list of domains to exclude from results.

    Returns:
        A formatted string with search results including titles, URLs, and content snippets.
    """
    client = _get_tavily_client()

    if not client:
        return (
            "Web search is not available. To enable it:\n"
            "1. Install tavily-python: pip install tavily-python\n"
            "2. Set TAVILY_API_KEY environment variable\n"
            "Continuing without web search results."
        )

    try:
        response = client.search(
            query=query,
            search_depth=search_depth,
            max_results=min(max_results, 10),
            include_domains=include_domains or [],
            exclude_domains=exclude_domains or [],
        )

        results = response.get("results", [])

        if not results:
            return f"No results found for query: {query}"

        formatted_results = [f"## Web Search Results for: {query}\n"]

        for i, result in enumerate(results, 1):
            formatted_results.append(
                f"### {i}. {result.get('title', 'No title')}\n"
                f"**URL:** {result.get('url', 'N/A')}\n"
                f"**Content:** {result.get('content', 'No content available')}\n"
            )

        return "\n".join(formatted_results)

    except Exception as e:
        return f"Web search failed: {str(e)}"


@function_tool
def extract_url_content(
    urls: List[str],
) -> str:
    """Extract and read the full content from specific URLs.

    Use this when you have specific URLs you want to read in full,
    such as articles, reports, or documentation pages.

    Args:
        urls: List of URLs to extract content from (max 5).

    Returns:
        The extracted content from each URL.
    """
    client = _get_tavily_client()

    if not client:
        return "URL extraction is not available. Set TAVILY_API_KEY to enable."

    try:
        response = client.extract(urls=urls[:5])

        results = response.get("results", [])

        if not results:
            return "No content could be extracted from the provided URLs."

        formatted_results = ["## Extracted Content\n"]

        for result in results:
            formatted_results.append(
                f"### {result.get('url', 'Unknown URL')}\n"
                f"{result.get('raw_content', 'No content available')[:3000]}...\n"
            )

        return "\n".join(formatted_results)

    except Exception as e:
        return f"URL extraction failed: {str(e)}"


@function_tool
def search_financial_news(
    topic: str,
    timeframe: str = "recent",
) -> str:
    """Search for financial news on a specific topic.

    This is a specialized search focused on financial and market news sources.

    Args:
        topic: The topic to search for (e.g., "oil prices", "Federal Reserve policy", "semiconductor shortage").
        timeframe: "recent" for last few days, "week" for past week, "month" for past month.

    Returns:
        Relevant financial news articles and summaries.
    """
    query = f"{topic} financial market impact news"

    financial_domains = [
        "reuters.com",
        "bloomberg.com",
        "ft.com",
        "wsj.com",
        "cnbc.com",
        "marketwatch.com",
        "economist.com",
    ]

    client = _get_tavily_client()

    if not client:
        return (
            "Financial news search is not available. To enable it:\n"
            "1. Install tavily-python: pip install tavily-python\n"
            "2. Set TAVILY_API_KEY environment variable"
        )

    try:
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_domains=financial_domains,
        )

        results = response.get("results", [])

        if not results:
            # Fall back to general search if no results from financial domains
            response = client.search(
                query=query,
                search_depth="basic",
                max_results=5,
            )
            results = response.get("results", [])

        if not results:
            return f"No financial news found for topic: {topic}"

        formatted_results = [f"## Financial News: {topic}\n"]

        for i, result in enumerate(results, 1):
            formatted_results.append(
                f"### {i}. {result.get('title', 'No title')}\n"
                f"**Source:** {result.get('url', 'N/A')}\n"
                f"**Summary:** {result.get('content', 'No content available')}\n"
            )

        return "\n".join(formatted_results)

    except Exception as e:
        return f"Financial news search failed: {str(e)}"


@function_tool
def get_market_context(
    instruments: List[str],
) -> str:
    """Get current market context for specific financial instruments.

    Use this to understand the current state of markets relevant to your analysis.

    Args:
        instruments: List of instrument tickers or names (e.g., ["CL=F", "SPY", "gold", "USD/EUR"]).

    Returns:
        Current market information and recent news for the specified instruments.
    """
    client = _get_tavily_client()

    if not client:
        return "Market context search is not available. Set TAVILY_API_KEY to enable."

    all_results = []

    for instrument in instruments[:5]:
        try:
            query = f"{instrument} stock price market news today"
            response = client.search(
                query=query,
                search_depth="basic",
                max_results=2,
            )

            results = response.get("results", [])
            if results:
                all_results.append(f"\n### {instrument.upper()}")
                for result in results:
                    all_results.append(
                        f"- {result.get('title', 'N/A')}: {result.get('content', '')[:200]}..."
                    )
        except Exception:
            all_results.append(f"\n### {instrument.upper()}\nNo data available")

    if not all_results:
        return "No market context found for the specified instruments."

    return "## Current Market Context\n" + "\n".join(all_results)


@function_tool
def deep_research(
    topic: str,
    focus: str = "financial_impact",
) -> str:
    """Conduct deep multi-source research on a topic.

    Use this for comprehensive research that requires synthesizing
    information from multiple sources. Best for complex topics
    where you need thorough background.

    Args:
        topic: The topic to research thoroughly.
        focus: Research focus - "financial_impact", "historical_precedent", "policy_analysis", or "market_dynamics".

    Returns:
        Comprehensive research findings with citations.
    """
    client = _get_tavily_client()

    if not client:
        return "Deep research is not available. Set TAVILY_API_KEY to enable."

    focus_queries = {
        "financial_impact": f"{topic} financial market impact analysis consequences",
        "historical_precedent": f"{topic} historical examples similar events past cases",
        "policy_analysis": f"{topic} government policy response regulation central bank",
        "market_dynamics": f"{topic} market dynamics supply demand trading implications",
    }

    query = focus_queries.get(focus, f"{topic} comprehensive analysis")

    try:
        # Use advanced search for deep research
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=10,
            include_answer=True,  # Get AI-synthesized answer
        )

        results = response.get("results", [])
        answer = response.get("answer", "")

        formatted = [f"## Deep Research: {topic}\n**Focus:** {focus}\n"]

        if answer:
            formatted.append(f"### Summary\n{answer}\n")

        formatted.append("### Sources\n")

        for i, result in enumerate(results[:7], 1):
            formatted.append(
                f"{i}. [{result.get('title', 'No title')}]({result.get('url', '')})\n"
                f"   {result.get('content', '')[:150]}...\n"
            )

        return "\n".join(formatted)

    except Exception as e:
        return f"Deep research failed: {str(e)}"


# List of all available tools for agents
RESEARCH_TOOLS = [
    web_search,
    extract_url_content,
    search_financial_news,
    get_market_context,
    deep_research,
]
