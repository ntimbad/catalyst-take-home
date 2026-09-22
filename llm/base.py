"""Base class and utilities for LLM clients using OpenAI Agents SDK."""

from abc import ABC, abstractmethod
from typing import Type, TypeVar, Optional, List, Any

from pydantic import BaseModel
from agents import Agent, Runner, OpenAIChatCompletionsModel


T = TypeVar("T", bound=BaseModel)


class BaseLLMClient(ABC):
    """Abstract base class for LLM integrations using Agents SDK."""

    @abstractmethod
    def _get_model(self) -> OpenAIChatCompletionsModel:
        """Get the model configuration for the agent.

        Returns:
            Configured OpenAIChatCompletionsModel instance
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name of the model being used."""
        pass

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        output_type: Optional[Type[T]] = None,
        tools: Optional[List[Any]] = None,
    ) -> T | str:
        """Generate a response from the LLM using the Agents SDK.

        Args:
            system_prompt: The system prompt to set context
            user_prompt: The user's prompt/query
            output_type: Optional Pydantic model class for structured output
            tools: Optional list of tools the agent can use

        Returns:
            If output_type is provided, returns an instance of that model.
            Otherwise returns the raw string response.
        """
        agent = Agent(
            name="CausalChainAnalyst",
            instructions=system_prompt,
            model=self._get_model(),
            output_type=output_type,
            tools=tools or [],
        )

        result = Runner.run_sync(agent, user_prompt)

        return result.final_output
