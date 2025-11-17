"""Base agent class for all specialized agents."""

import json
from typing import Dict, Any
import google.generativeai as genai

from ..utils.config import settings
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class BaseAgent:
    """Base class for all agents."""

    def __init__(self, agent_name: str):
        """Initialize base agent."""
        self.agent_name = agent_name
        self.logger = logger.bind(agent=agent_name)

        # Configure Gemini
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

        self.logger.info(f"{agent_name} initialized")

    def invoke_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Invoke Gemini LLM with a prompt.

        Args:
            prompt: The prompt to send to the LLM
            temperature: Sampling temperature (0-1)

        Returns:
            The LLM's response text
        """
        try:
            self.logger.debug("Invoking LLM", prompt_length=len(prompt))

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=2048,
                )
            )

            result = response.text
            self.logger.debug("LLM response received", response_length=len(result))

            return result

        except Exception as e:
            self.logger.error("Error invoking LLM", error=str(e))
            raise

    def parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response.

        Handles cases where LLM includes extra text around JSON.
        """
        try:
            # Try direct parsing first
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
                return json.loads(json_str)
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
                return json.loads(json_str)
            else:
                # Try to find JSON object in text
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())

                self.logger.error("Could not parse JSON from response", response=response[:200])
                raise ValueError(f"Could not parse JSON from LLM response")

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke the agent. Must be implemented by subclasses.

        Args:
            state: The current agent state

        Returns:
            Updated state dictionary
        """
        raise NotImplementedError("Subclasses must implement invoke()")
