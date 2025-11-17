"""LangGraph workflow for multi-agent orchestration."""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from .state import AgentState
from .orchestrator import OrchestratorAgent
from .curriculum_planner import CurriculumPlannerAgent
from .tutor import TutorAgent
from .problem_generator import ProblemGeneratorAgent
from .assessor import AssessorAgent
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class SocraticLearningGraph:
    """
    LangGraph workflow for the Socratic Learning Companion.

    Flow:
    1. User message -> Orchestrator (routes to specialist)
    2. Curriculum Planner (if needed) -> Tutor
    3. Tutor (Socratic questions) -> Assessor
    4. Assessor (evaluate) -> [Tutor/Curriculum Planner/Problem Generator]
    5. Problem Generator -> Assessor
    """

    def __init__(self):
        """Initialize the learning graph."""
        self.logger = logger.bind(component="LearningGraph")

        # Initialize agents
        self.orchestrator = OrchestratorAgent()
        self.curriculum_planner = CurriculumPlannerAgent()
        self.tutor = TutorAgent()
        self.problem_generator = ProblemGeneratorAgent()
        self.assessor = AssessorAgent()

        # Build graph
        self.graph = self._build_graph()

        self.logger.info("Learning graph initialized")

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph."""
        # Create state graph
        workflow = StateGraph(AgentState)

        # Add agent nodes
        workflow.add_node("orchestrator", self._orchestrator_node)
        workflow.add_node("curriculum_planner", self._curriculum_planner_node)
        workflow.add_node("tutor", self._tutor_node)
        workflow.add_node("problem_generator", self._problem_generator_node)
        workflow.add_node("assessor", self._assessor_node)

        # Set entry point
        workflow.set_entry_point("orchestrator")

        # Add conditional edges based on next_agent routing
        workflow.add_conditional_edges(
            "orchestrator",
            self._route_from_orchestrator,
            {
                "curriculum_planner": "curriculum_planner",
                "tutor": "tutor",
                "problem_generator": "problem_generator",
                "assessor": "assessor",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "curriculum_planner",
            self._route_from_curriculum_planner,
            {
                "tutor": "tutor",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "tutor",
            self._route_from_tutor,
            {
                "assessor": "assessor",
                "curriculum_planner": "curriculum_planner",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "problem_generator",
            self._route_from_problem_generator,
            {
                "assessor": "assessor",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "assessor",
            self._route_from_assessor,
            {
                "tutor": "tutor",
                "curriculum_planner": "curriculum_planner",
                "problem_generator": "problem_generator",
                "end": END
            }
        )

        return workflow.compile()

    # Agent node functions
    def _orchestrator_node(self, state: AgentState) -> AgentState:
        """Orchestrator agent node."""
        self.logger.info("Executing orchestrator node")
        return self.orchestrator.invoke(state)

    def _curriculum_planner_node(self, state: AgentState) -> AgentState:
        """Curriculum planner agent node."""
        self.logger.info("Executing curriculum planner node")
        return self.curriculum_planner.invoke(state)

    def _tutor_node(self, state: AgentState) -> AgentState:
        """Tutor agent node."""
        self.logger.info("Executing tutor node")
        return self.tutor.invoke(state)

    def _problem_generator_node(self, state: AgentState) -> AgentState:
        """Problem generator agent node."""
        self.logger.info("Executing problem generator node")
        return self.problem_generator.invoke(state)

    def _assessor_node(self, state: AgentState) -> AgentState:
        """Assessor agent node."""
        self.logger.info("Executing assessor node")
        return self.assessor.invoke(state)

    # Routing functions
    def _route_from_orchestrator(self, state: AgentState) -> str:
        """Route from orchestrator based on next_agent."""
        next_agent = state.get("next_agent", "tutor")
        self.logger.info("Routing from orchestrator", next_agent=next_agent)
        return next_agent if next_agent != "end" else "end"

    def _route_from_curriculum_planner(self, state: AgentState) -> str:
        """Route from curriculum planner."""
        next_agent = state.get("next_agent", "tutor")
        self.logger.info("Routing from curriculum planner", next_agent=next_agent)
        return next_agent if next_agent != "end" else "end"

    def _route_from_tutor(self, state: AgentState) -> str:
        """Route from tutor."""
        next_agent = state.get("next_agent", "assessor")
        self.logger.info("Routing from tutor", next_agent=next_agent)
        return next_agent if next_agent != "end" else "end"

    def _route_from_problem_generator(self, state: AgentState) -> str:
        """Route from problem generator."""
        next_agent = state.get("next_agent", "assessor")
        self.logger.info("Routing from problem generator", next_agent=next_agent)
        return next_agent if next_agent != "end" else "end"

    def _route_from_assessor(self, state: AgentState) -> str:
        """Route from assessor."""
        next_agent = state.get("next_agent", "tutor")
        self.logger.info("Routing from assessor", next_agent=next_agent)
        return next_agent if next_agent != "end" else "end"

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke the learning graph with an initial state.

        Args:
            state: Initial state dictionary

        Returns:
            Final state after graph execution
        """
        self.logger.info("Invoking learning graph")

        try:
            # Execute graph
            final_state = self.graph.invoke(state)

            self.logger.info("Graph execution complete")
            return final_state

        except Exception as e:
            self.logger.error("Error in graph execution", error=str(e))
            raise


# Global graph instance
_learning_graph = None


def get_learning_graph() -> SocraticLearningGraph:
    """Get or create the learning graph instance."""
    global _learning_graph
    if _learning_graph is None:
        _learning_graph = SocraticLearningGraph()
    return _learning_graph
