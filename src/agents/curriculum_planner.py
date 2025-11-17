"""Curriculum Planner Agent - Recommends next topic based on prerequisites."""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from .prompts import format_curriculum_planner_prompt
from ..database.db_manager import get_db_manager


class CurriculumPlannerAgent(BaseAgent):
    """
    Curriculum Planner Agent recommends the next topic to study.

    Responsibilities:
    - Query topic graph and prerequisites from database
    - Check student's mastered topics
    - Recommend appropriate next topic
    - Assess difficulty and readiness
    """

    def __init__(self):
        """Initialize curriculum planner agent."""
        super().__init__("CurriculumPlanner")
        self.db_manager = get_db_manager()

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend next topic based on student progress and prerequisites.

        Args:
            state: Current agent state

        Returns:
            Updated state with curriculum_planner_output and recommended topic
        """
        self.logger.info("Curriculum planner invoked")

        user_id = state.get("user_id")
        if not user_id:
            self.logger.error("No user_id in state")
            return state

        # Get curriculum graph
        curriculum_graph = self._build_curriculum_graph()

        # Get student's progress
        mastered_topics = state.get("mastered_topics", [])
        struggling_topics = self._get_struggling_topics(user_id)

        # Format prompt
        prompt = format_curriculum_planner_prompt(
            curriculum_graph=curriculum_graph,
            mastered_topics=mastered_topics,
            struggling_topics=struggling_topics,
            learning_pace=state.get("learning_pace", "medium"),
            understanding_score=state.get("understanding_score", 0.0)
        )

        try:
            response = self.invoke_llm(prompt, temperature=0.3)
            recommendation = self.parse_json_response(response)

            recommended_topic_id = recommendation.get("recommended_topic_id")
            rationale = recommendation.get("rationale", "")

            self.logger.info(
                "Topic recommended",
                topic_id=recommended_topic_id,
                rationale=rationale
            )

            # Update state
            state["current_topic_id"] = recommended_topic_id
            state["curriculum_planner_output"] = recommendation
            state["next_agent"] = "tutor"  # Move to tutor to start teaching

            return state

        except Exception as e:
            self.logger.error("Error in curriculum planner", error=str(e))
            state["curriculum_planner_output"] = {"error": str(e)}
            state["next_agent"] = "tutor"  # Fallback
            return state

    def _build_curriculum_graph(self) -> str:
        """Build a text representation of the curriculum graph."""
        topics = self.db_manager.get_topics_by_category("fundamentals")
        topics += self.db_manager.get_topics_by_category("data_structures")
        topics += self.db_manager.get_topics_by_category("algorithms")
        topics += self.db_manager.get_topics_by_category("complexity")

        graph_lines = []
        for topic in topics:
            prereqs = self.db_manager.get_topic_prerequisites(topic.topic_id)
            prereq_ids = [p.topic_id for p in prereqs]

            graph_lines.append(
                f"- {topic.title} (ID: {topic.topic_id}, Difficulty: {topic.difficulty}, "
                f"Prerequisites: {', '.join(prereq_ids) if prereq_ids else 'None'})"
            )

        return "\n".join(graph_lines)

    def _get_struggling_topics(self, user_id: str) -> List[str]:
        """Get topics the student is struggling with."""
        progress_records = self.db_manager.get_student_progress(user_id)
        struggling = []

        for progress in progress_records:
            if progress.status == "struggling":
                struggling.append(progress.topic_id)

        return struggling
