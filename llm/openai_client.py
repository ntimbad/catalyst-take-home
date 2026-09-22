"""OpenAI LLM client using OpenAI Agents SDK."""

import os
from typing import Optional

from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel

from .base import BaseLLMClient


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT client using OpenAI Agents SDK."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo-preview"):
        """Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key. If not provided, uses OPENAI_API_KEY env var.
            model: Model to use (default: gpt-4-turbo-preview)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.model = model
        self._openai_client = AsyncOpenAI(api_key=self.api_key)

    def _get_model(self) -> OpenAIChatCompletionsModel:
        """Get the OpenAI model configuration.

        Returns:
            Configured OpenAIChatCompletionsModel instance
        """
        return OpenAIChatCompletionsModel(
            model=self.model,
            openai_client=self._openai_client
        )

    def get_model_name(self) -> str:
        """Get the name of the model being used."""
        return f"OpenAI ({self.model})"
