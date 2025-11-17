"""Agent state management for LangGraph."""

from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass


class AgentState(TypedDict):
    """State shared between agents in the LangGraph workflow."""

    # Session information
    user_id: str
    session_id: str
    current_topic_id: Optional[str]

    # Conversation
    messages: List[Dict[str, str]]  # List of {role, content, agent_type}

    # Student model
    student_background: Optional[str]
    mastered_topics: List[str]
    understanding_score: float  # 0-1 scale
    active_misconceptions: List[Dict[str, Any]]
    learning_pace: str  # slow/medium/fast

    # Context
    retrieved_chunks: List[Dict[str, Any]]

    # Teaching state
    teaching_stage: str  # exploration/reasoning/synthesis/assessment
    socratic_depth: int  # How many questions deep in Socratic dialogue

    # Routing
    next_agent: str  # Which agent to invoke next
    agent_reasoning: Optional[str]  # Why routing to this agent

    # Agent outputs
    orchestrator_output: Optional[Dict[str, Any]]
    curriculum_planner_output: Optional[Dict[str, Any]]
    tutor_output: Optional[Dict[str, Any]]
    problem_generator_output: Optional[Dict[str, Any]]
    assessor_output: Optional[Dict[str, Any]]


@dataclass
class StudentModel:
    """Student learning model."""
    user_id: str
    background: Optional[str]
    learning_goals: Optional[str]
    learning_pace: str
    mastered_topics: List[str]
    struggling_topics: List[str]
    understanding_score: float
    misconceptions: List[Dict[str, Any]]


@dataclass
class RetrievalContext:
    """Context retrieved from vector database."""
    chunks: List[Dict[str, Any]]
    query: str
    relevance_scores: List[float]
    sources: List[str]


@dataclass
class SocraticQuestion:
    """A Socratic question with metadata."""
    question: str
    question_type: str  # exploration/clarification/reasoning/synthesis
    expected_concepts: List[str]
    hints: List[str]
    depth: int  # How deep in dialogue tree


@dataclass
class AssessmentResult:
    """Result of student response assessment."""
    understanding_score: float  # 0-1 scale
    correctness_score: float  # 0-1 scale
    depth_score: str  # surface/intermediate/deep
    misconceptions_detected: List[Dict[str, str]]
    feedback: str
    recommendation: str  # continue/clarify/reteach/advance
