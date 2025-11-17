"""Pydantic models for API requests and responses."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# Student models
class StudentCreate(BaseModel):
    """Request model for creating a student."""
    user_id: str = Field(..., description="Unique user identifier")
    name: str = Field(..., min_length=1)
    email: Optional[str] = None
    background: Optional[str] = None
    learning_goals: Optional[str] = None
    learning_pace: str = Field(default="medium", pattern="^(slow|medium|fast)$")


class StudentResponse(BaseModel):
    """Response model for student data."""
    user_id: str
    name: str
    email: Optional[str]
    background: Optional[str]
    learning_goals: Optional[str]
    learning_pace: str
    created_at: datetime

    class Config:
        from_attributes = True


# Session models
class SessionStart(BaseModel):
    """Request model for starting a session."""
    user_id: str
    topic_id: Optional[str] = None
    session_type: str = Field(default="learning", pattern="^(learning|practice|assessment)$")
    goal: Optional[str] = None


class SessionResponse(BaseModel):
    """Response model for session data."""
    session_id: str
    user_id: str
    topic_id: Optional[str]
    started_at: datetime
    session_type: str
    goal: Optional[str]

    class Config:
        from_attributes = True


# Chat models
class ChatMessage(BaseModel):
    """Request model for chat messages."""
    user_id: str
    session_id: str
    message: str


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    session_id: str
    message: str
    agent_type: Optional[str]
    teaching_stage: Optional[str]
    understanding_score: Optional[float]
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None


# Progress models
class ProgressResponse(BaseModel):
    """Response model for student progress."""
    user_id: str
    topic_id: str
    status: str
    understanding_score: float
    attempts: int
    time_spent_minutes: int
    last_studied_at: Optional[datetime]
    mastered_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProgressSummary(BaseModel):
    """Summary of student progress across topics."""
    user_id: str
    total_topics: int
    mastered_count: int
    learning_count: int
    struggling_count: int
    overall_understanding: float
    mastered_topics: List[str]
    current_topic: Optional[str]


# Topic models
class TopicResponse(BaseModel):
    """Response model for topic data."""
    topic_id: str
    title: str
    description: Optional[str]
    difficulty: int
    estimated_time_hours: Optional[float]
    category: Optional[str]
    prerequisites: List[str] = []

    class Config:
        from_attributes = True


# Assessment models
class AssessmentSubmit(BaseModel):
    """Request model for submitting an assessment."""
    session_id: str
    user_id: str
    topic_id: Optional[str]
    question: str
    student_response: str


class AssessmentResponse(BaseModel):
    """Response model for assessment results."""
    understanding_score: Optional[float]
    correctness_score: Optional[float]
    depth_score: Optional[str]
    misconceptions_detected: List[Dict[str, str]]
    feedback: Optional[str]
    recommendation: Optional[str]


# Curriculum graph model
class CurriculumGraph(BaseModel):
    """Response model for curriculum graph."""
    topics: List[TopicResponse]
    prerequisites: List[Dict[str, Any]]


# Error response
class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
