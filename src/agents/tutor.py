"""Tutor Agent - Conducts Socratic dialogue to teach algorithms."""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from .prompts import format_tutor_prompt
from ..database.chroma_manager import get_chroma_manager
from ..database.db_manager import get_db_manager


class TutorAgent(BaseAgent):
    """
    Tutor Agent uses the Socratic method to teach algorithms.

    CRITICAL RULES:
    1. NEVER explain directly first
    2. ALWAYS ask questions to probe understanding
    3. Guide students to discover concepts
    4. Use student's reasoning to build knowledge
    5. Break complex concepts into smaller questions

    Responsibilities:
    - Retrieve relevant content from vector database
    - Ask Socratic questions
    - Guide through exploration -> reasoning -> synthesis
    - Handle proofs step-by-step
    - Never give answers directly
    """

    def __init__(self):
        """Initialize tutor agent."""
        super().__init__("Tutor")
        self.chroma_manager = get_chroma_manager()
        self.db_manager = get_db_manager()

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate next Socratic question for the student.

        Args:
            state: Current agent state

        Returns:
            Updated state with tutor_output and next question
        """
        self.logger.info("Tutor invoked")

        # Get current topic
        topic_id = state.get("current_topic_id")
        if not topic_id:
            # Need topic first
            self.logger.info("No topic set, routing to curriculum planner")
            state["next_agent"] = "curriculum_planner"
            return state

        # Get topic details
        try:
            topic = self._get_topic_details(topic_id)
            if not topic:
                self.logger.error("Topic not found", topic_id=topic_id)
                state["next_agent"] = "curriculum_planner"
                return state

            # Get student's last response
            student_response = self._get_last_user_message(state)

            # Retrieve relevant content
            retrieved_chunks = self._retrieve_relevant_content(
                topic_id, student_response, state
            )

            # Build conversation history
            conversation_history = self._format_conversation_history(state)

            # Get teaching stage and depth
            teaching_stage = state.get("teaching_stage", "exploration")
            socratic_depth = state.get("socratic_depth", 0)

            # Format chunks for prompt
            chunks_text = self._format_chunks(retrieved_chunks)

            # Format prompt
            prompt = format_tutor_prompt(
                topic_title=topic["title"],
                topic_description=topic["description"],
                retrieved_chunks=chunks_text,
                conversation_history=conversation_history,
                teaching_stage=teaching_stage,
                socratic_depth=socratic_depth,
                student_response=student_response
            )

            # Generate Socratic question
            response = self.invoke_llm(prompt, temperature=0.7)
            tutor_response = self.parse_json_response(response)

            question = tutor_response.get("question", "")
            new_teaching_stage = tutor_response.get("teaching_stage", teaching_stage)
            new_depth = tutor_response.get("depth", socratic_depth)

            self.logger.info(
                "Socratic question generated",
                stage=new_teaching_stage,
                depth=new_depth,
                question_preview=question[:100]
            )

            # Add tutor's question to messages
            messages = state.get("messages", [])
            messages.append({
                "role": "assistant",
                "content": question,
                "agent_type": "tutor"
            })

            # Update state
            state["messages"] = messages
            state["teaching_stage"] = new_teaching_stage
            state["socratic_depth"] = new_depth
            state["tutor_output"] = tutor_response
            state["retrieved_chunks"] = retrieved_chunks
            state["next_agent"] = "assessor"  # Assess student's next response

            return state

        except Exception as e:
            self.logger.error("Error in tutor", error=str(e))

            # Provide fallback question
            fallback_question = "What are your thoughts on this topic? What would you like to explore?"
            messages = state.get("messages", [])
            messages.append({
                "role": "assistant",
                "content": fallback_question,
                "agent_type": "tutor"
            })

            state["messages"] = messages
            state["tutor_output"] = {"error": str(e), "question": fallback_question}
            state["next_agent"] = "assessor"

            return state

    def _get_topic_details(self, topic_id: str) -> Dict[str, str]:
        """Get topic details from database."""
        with self.db_manager.get_session() as session:
            from ..database.models import Topic
            topic = session.query(Topic).filter(Topic.topic_id == topic_id).first()

            if topic:
                return {
                    "title": topic.title,
                    "description": topic.description or "",
                    "difficulty": topic.difficulty
                }

        return None

    def _get_last_user_message(self, state: Dict[str, Any]) -> str:
        """Extract last user message from state."""
        messages = state.get("messages", [])

        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")

        return "I'm ready to learn."

    def _retrieve_relevant_content(
        self, topic_id: str, query: str, state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant content from vector database."""
        try:
            # Use hybrid search with topic filtering
            results = self.chroma_manager.hybrid_search(
                collection_name="textbook_chunks",
                query_text=query,
                metadata_filters={},  # Could add topic-specific filters
                n_results=3
            )

            self.logger.info("Retrieved content", count=len(results))
            return results

        except Exception as e:
            self.logger.warning("Error retrieving content", error=str(e))
            return []

    def _format_conversation_history(self, state: Dict[str, Any]) -> str:
        """Format recent conversation history."""
        messages = state.get("messages", [])
        recent = messages[-5:] if len(messages) > 5 else messages

        formatted = []
        for msg in recent:
            role = msg.get("role", "")
            content = msg.get("content", "")
            formatted.append(f"{role.upper()}: {content}")

        return "\n".join(formatted)

    def _format_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks for prompt."""
        if not chunks:
            return "No relevant content retrieved from textbook."

        formatted = []
        for i, chunk in enumerate(chunks, 1):
            content = chunk.get("document", "")
            metadata = chunk.get("metadata", {})
            section = metadata.get("section_title", "Unknown section")

            formatted.append(f"[Chunk {i} - {section}]\n{content}\n")

        return "\n".join(formatted)
