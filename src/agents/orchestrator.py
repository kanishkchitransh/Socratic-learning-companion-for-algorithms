"""Orchestrator Agent - Routes user messages to appropriate specialists."""

from typing import Dict, Any
from .base_agent import BaseAgent
from .prompts import format_orchestrator_prompt


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent routes user messages to the appropriate specialist.

    Responsibilities:
    - Parse user intent
    - Determine which agent should handle the message
    - Maintain conversation coherence
    - Provide context to the next agent
    """

    def __init__(self):
        """Initialize orchestrator agent."""
        super().__init__("Orchestrator")

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route user message to appropriate agent.

        Args:
            state: Current agent state

        Returns:
            Updated state with next_agent and orchestrator_output
        """
        self.logger.info("Orchestrator invoked")

        # Get last user message
        messages = state.get("messages", [])
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            self.logger.warning("No user message found in state")
            state["next_agent"] = "tutor"  # Default to tutor
            return state

        # Build context
        context = self._build_context(state)

        # Format prompt
        prompt = format_orchestrator_prompt(
            context=context,
            mastered_topics=state.get("mastered_topics", []),
            understanding_score=state.get("understanding_score", 0.0),
            misconceptions=state.get("active_misconceptions", []),
            user_message=user_message
        )

        # Get routing decision from LLM
        try:
            response = self.invoke_llm(prompt, temperature=0.3)
            routing_decision = self.parse_json_response(response)

            next_agent = routing_decision.get("next_agent", "tutor")
            reasoning = routing_decision.get("reasoning", "")

            self.logger.info(
                "Routing decision made",
                next_agent=next_agent,
                reasoning=reasoning
            )

            # Update state
            state["next_agent"] = next_agent
            state["agent_reasoning"] = reasoning
            state["orchestrator_output"] = routing_decision

            return state

        except Exception as e:
            self.logger.error("Error in orchestrator", error=str(e))
            # Fallback to tutor
            state["next_agent"] = "tutor"
            state["agent_reasoning"] = f"Error in routing: {str(e)}, defaulting to tutor"
            return state

    def _build_context(self, state: Dict[str, Any]) -> str:
        """Build context summary from state."""
        messages = state.get("messages", [])
        recent_messages = messages[-5:] if len(messages) > 5 else messages

        context_parts = []

        if state.get("current_topic_id"):
            context_parts.append(f"Current topic: {state['current_topic_id']}")

        context_parts.append(f"Recent messages: {len(recent_messages)}")

        if state.get("teaching_stage"):
            context_parts.append(f"Teaching stage: {state['teaching_stage']}")

        return " | ".join(context_parts)
