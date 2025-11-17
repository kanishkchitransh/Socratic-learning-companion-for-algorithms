"""Problem Generator Agent - Creates practice problems for algorithms."""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from .prompts import format_problem_generator_prompt
from ..database.chroma_manager import get_chroma_manager
from ..database.db_manager import get_db_manager


class ProblemGeneratorAgent(BaseAgent):
    """
    Problem Generator Agent creates practice problems.

    Focuses on:
    - Proof problems
    - Complexity analysis
    - Correctness arguments
    - Mathematical reasoning

    Responsibilities:
    - Generate problems matching student level
    - Provide progressive hints
    - Create solution outlines
    - Include LaTeX notation
    """

    def __init__(self):
        """Initialize problem generator agent."""
        super().__init__("ProblemGenerator")
        self.chroma_manager = get_chroma_manager()
        self.db_manager = get_db_manager()

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a practice problem for the student.

        Args:
            state: Current agent state

        Returns:
            Updated state with problem_generator_output
        """
        self.logger.info("Problem generator invoked")

        # Get current topic
        topic_id = state.get("current_topic_id")
        if not topic_id:
            self.logger.error("No topic set")
            state["next_agent"] = "curriculum_planner"
            return state

        try:
            # Get topic details
            topic = self._get_topic_details(topic_id)
            if not topic:
                self.logger.error("Topic not found", topic_id=topic_id)
                state["next_agent"] = "tutor"
                return state

            # Retrieve example problems from textbook
            retrieved_examples = self._retrieve_example_problems(topic_id)

            # Get student's current level
            understanding_score = state.get("understanding_score", 0.5)
            difficulty = self._determine_difficulty(understanding_score, topic["difficulty"])

            # Format prompt
            prompt = format_problem_generator_prompt(
                topic_title=topic["title"],
                difficulty=difficulty,
                understanding_score=understanding_score,
                retrieved_examples=retrieved_examples
            )

            # Generate problem
            response = self.invoke_llm(prompt, temperature=0.8)
            problem = self.parse_json_response(response)

            problem_statement = problem.get("problem_statement", "")

            self.logger.info(
                "Problem generated",
                difficulty=difficulty,
                problem_type=problem.get("problem_type"),
                statement_preview=problem_statement[:100]
            )

            # Add problem to messages
            messages = state.get("messages", [])
            messages.append({
                "role": "assistant",
                "content": f"Here's a practice problem:\n\n{problem_statement}",
                "agent_type": "problem_generator"
            })

            # Update state
            state["messages"] = messages
            state["problem_generator_output"] = problem
            state["next_agent"] = "assessor"  # Assess student's solution

            return state

        except Exception as e:
            self.logger.error("Error in problem generator", error=str(e))
            state["problem_generator_output"] = {"error": str(e)}
            state["next_agent"] = "tutor"
            return state

    def _get_topic_details(self, topic_id: str) -> Dict[str, Any]:
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

    def _retrieve_example_problems(self, topic_id: str) -> str:
        """Retrieve example problems from textbook."""
        try:
            results = self.chroma_manager.hybrid_search(
                collection_name="textbook_chunks",
                query_text="example problem exercise",
                metadata_filters={"chunk_type": "exercise"},
                n_results=2
            )

            if not results:
                return "No example problems found."

            formatted = []
            for i, chunk in enumerate(results, 1):
                content = chunk.get("document", "")
                formatted.append(f"[Example {i}]\n{content}\n")

            return "\n".join(formatted)

        except Exception as e:
            self.logger.warning("Error retrieving examples", error=str(e))
            return "No example problems available."

    def _determine_difficulty(self, understanding_score: float, topic_difficulty: int) -> int:
        """Determine appropriate problem difficulty."""
        # Base difficulty on topic difficulty
        if understanding_score >= 0.8:
            # Student is doing well, challenge them
            return min(5, topic_difficulty + 1)
        elif understanding_score >= 0.6:
            # Match topic difficulty
            return topic_difficulty
        else:
            # Student struggling, make it easier
            return max(1, topic_difficulty - 1)
