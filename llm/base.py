"""Base class and utilities for LLM clients using OpenAI Agents SDK."""

import json
import re
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Optional, List, Any

from pydantic import BaseModel
from agents import Agent, Runner, OpenAIChatCompletionsModel


T = TypeVar("T", bound=BaseModel)


class BaseLLMClient(ABC):
    """Abstract base class for LLM integrations using Agents SDK."""

    @property
    def supports_structured_output(self) -> bool:
        """Whether this provider supports native structured output (response_format: json_schema).

        Override this in subclasses that don't support it (e.g., Anthropic via OpenAI compat).
        """
        return True

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

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that may contain markdown code blocks."""
        # Try to extract from code block first
        json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
        if json_match:
            return json_match.group(1).strip()

        # Try to find raw JSON object
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            return brace_match.group(0)

        return text.strip()

    def _build_json_prompt(self, base_prompt: str, output_type: Type[T]) -> str:
        """Build a prompt that asks for JSON output matching the schema."""
        schema = output_type.model_json_schema()
        schema_str = json.dumps(schema, indent=2)

        return f"""{base_prompt}

IMPORTANT: You must respond with valid JSON that matches this schema:
```json
{schema_str}
```

Respond ONLY with the JSON object, no additional text."""

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
        # If provider doesn't support native structured output, handle via JSON in prompt
        if output_type and not self.supports_structured_output:
            modified_prompt = self._build_json_prompt(user_prompt, output_type)

            agent = Agent(
                name="CausalChainAnalyst",
                instructions=system_prompt,
                model=self._get_model(),
                output_type=None,  # Don't use native structured output
                tools=tools or [],
            )

            result = Runner.run_sync(agent, modified_prompt)

            # Parse the JSON response
            json_str = self._extract_json(result.final_output)
            data = json.loads(json_str)
            return output_type.model_validate(data)

        # Use native structured output
        agent = Agent(
            name="CausalChainAnalyst",
            instructions=system_prompt,
            model=self._get_model(),
            output_type=output_type,
            tools=tools or [],
        )

        result = Runner.run_sync(agent, user_prompt)

        return result.final_output
