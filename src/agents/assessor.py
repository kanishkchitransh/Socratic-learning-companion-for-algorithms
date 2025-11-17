"""Assessor Agent - Evaluates student understanding and identifies misconceptions."""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from .prompts import format_assessor_prompt
from ..database.chroma_manager import get_chroma_manager
from ..database.db_manager import get_db_manager


class AssessorAgent(BaseAgent):
    """
    Assessor Agent evaluates student responses.

    Responsibilities:
    - Evaluate correctness and depth of responses
    - Identify misconceptions (conceptual, procedural, notation)
    - Determine understanding level
    - Update student progress in database
    - Provide constructive feedback
    - Recommend next steps
    """

    def __init__(self):
        """Initialize assessor agent."""
        super().__init__("Assessor")
        self.chroma_manager = get_chroma_manager()
        self.db_manager = get_db_manager()

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess student's response.

        Args:
            state: Current agent state

        Returns:
            Updated state with assessor_output and updated student progress
        """
        self.logger.info("Assessor invoked")

        # Get student's response
        student_response = self._get_last_user_message(state)
        if not student_response:
            self.logger.warning("No student response to assess")
            state["next_agent"] = "tutor"
            return state

        # Get the question that was asked
        question = self._get_last_assistant_message(state)

        try:
            # Retrieve correct concepts for comparison
            retrieved_context = self._retrieve_correct_concepts(student_response, state)

            # Build conversation history
            conversation_history = self._format_conversation_history(state)

            # Format prompt
            prompt = format_assessor_prompt(
                question=question,
                student_response=student_response,
                retrieved_context=retrieved_context,
                conversation_history=conversation_history
            )

            # Get assessment from LLM
            response = self.invoke_llm(prompt, temperature=0.3)
            assessment = self.parse_json_response(response)

            understanding_score = assessment.get("understanding_score", 0.5)
            correctness_score = assessment.get("correctness_score", 0.5)
            depth_score = assessment.get("depth_score", "surface")
            misconceptions = assessment.get("misconceptions_detected", [])
            recommendation = assessment.get("recommendation", "continue")

            self.logger.info(
                "Assessment complete",
                understanding=understanding_score,
                correctness=correctness_score,
                depth=depth_score,
                misconceptions_count=len(misconceptions)
            )

            # Update student progress
            self._update_student_progress(state, assessment)

            # Record misconceptions
            if misconceptions:
                self._record_misconceptions(state, misconceptions)

            # Update state
            state["understanding_score"] = understanding_score
            state["assessor_output"] = assessment

            # Determine next agent based on recommendation
            if recommendation == "advance":
                state["next_agent"] = "curriculum_planner"  # Move to next topic
            elif recommendation == "clarify":
                state["next_agent"] = "tutor"  # Ask clarifying questions
            elif recommendation == "reteach":
                state["teaching_stage"] = "exploration"  # Restart from beginning
                state["socratic_depth"] = 0
                state["next_agent"] = "tutor"
            else:  # continue
                state["next_agent"] = "tutor"  # Continue dialogue

            return state

        except Exception as e:
            self.logger.error("Error in assessor", error=str(e))
            state["assessor_output"] = {"error": str(e)}
            state["next_agent"] = "tutor"
            return state

    def _get_last_user_message(self, state: Dict[str, Any]) -> str:
        """Get last message from user."""
        messages = state.get("messages", [])
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return ""

    def _get_last_assistant_message(self, state: Dict[str, Any]) -> str:
        """Get last message from assistant."""
        messages = state.get("messages", [])
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                return msg.get("content", "")
        return ""

    def _retrieve_correct_concepts(self, student_response: str, state: Dict[str, Any]) -> str:
        """Retrieve correct concepts from textbook for comparison."""
        try:
            results = self.chroma_manager.hybrid_search(
                collection_name="textbook_chunks",
                query_text=student_response,
                metadata_filters={},
                n_results=2
            )

            if not results:
                return "No reference material found."

            formatted = []
            for chunk in results:
                content = chunk.get("document", "")
                formatted.append(content)

            return "\n\n".join(formatted)

        except Exception as e:
            self.logger.warning("Error retrieving context", error=str(e))
            return "Reference material unavailable."

    def _format_conversation_history(self, state: Dict[str, Any]) -> str:
        """Format conversation history."""
        messages = state.get("messages", [])
        recent = messages[-5:] if len(messages) > 5 else messages

        formatted = []
        for msg in recent:
            role = msg.get("role", "")
            content = msg.get("content", "")
            formatted.append(f"{role.upper()}: {content[:200]}")

        return "\n".join(formatted)

    def _update_student_progress(self, state: Dict[str, Any], assessment: Dict[str, Any]):
        """Update student progress in database."""
        user_id = state.get("user_id")
        topic_id = state.get("current_topic_id")

        if not user_id or not topic_id:
            return

        try:
            understanding_score = assessment.get("understanding_score", 0.5)
            recommendation = assessment.get("recommendation", "continue")

            # Determine status
            if understanding_score >= 0.8 and recommendation == "advance":
                status = "mastered"
            elif understanding_score < 0.4:
                status = "struggling"
            else:
                status = "learning"

            self.db_manager.update_progress(
                user_id=user_id,
                topic_id=topic_id,
                status=status,
                understanding_score=understanding_score,
                time_spent_minutes=5  # Approximate time for this interaction
            )

            self.logger.info(
                "Progress updated",
                user_id=user_id,
                topic_id=topic_id,
                status=status,
                score=understanding_score
            )

        except Exception as e:
            self.logger.error("Error updating progress", error=str(e))

    def _record_misconceptions(self, state: Dict[str, Any], misconceptions: List[Dict[str, str]]):
        """Record misconceptions in database."""
        user_id = state.get("user_id")
        topic_id = state.get("current_topic_id")

        if not user_id:
            return

        try:
            for misconception in misconceptions:
                self.db_manager.add_misconception(
                    user_id=user_id,
                    topic_id=topic_id,
                    misconception_type=misconception.get("type", "conceptual"),
                    description=misconception.get("description", ""),
                    incorrect_belief=misconception.get("incorrect_belief"),
                    correct_concept=misconception.get("correct_concept")
                )

            self.logger.info(
                "Misconceptions recorded",
                user_id=user_id,
                count=len(misconceptions)
            )

        except Exception as e:
            self.logger.error("Error recording misconceptions", error=str(e))
