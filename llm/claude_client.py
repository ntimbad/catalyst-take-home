"""Claude (Anthropic) LLM client using OpenAI Agents SDK."""

import os
from typing import Optional

from agents import AsyncOpenAI, OpenAIChatCompletionsModel

from .base import BaseLLMClient


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude client using OpenAI Agents SDK with Anthropic's OpenAI-compatible endpoint."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        """Initialize the Claude client.

        Args:
            api_key: Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.
            model: Model to use (default: claude-sonnet-4-20250514)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.model = model
        self._openai_client = AsyncOpenAI(
            base_url="https://api.anthropic.com/v1/",
            api_key=self.api_key,
        )

    def _get_model(self) -> OpenAIChatCompletionsModel:
        """Get the Claude model configuration.

        Returns:
            Configured OpenAIChatCompletionsModel instance
        """
        return OpenAIChatCompletionsModel(
            model=self.model,
            openai_client=self._openai_client
        )

    def get_model_name(self) -> str:
        """Get the name of the model being used."""
        return f"Claude ({self.model})"
