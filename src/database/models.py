"""SQLAlchemy models for the Socratic Learning Companion."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    Boolean,
    JSON,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Student(Base):
    """Student profile and learning preferences."""

    __tablename__ = "students"

    user_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    background = Column(Text, nullable=True)  # JSON: prior knowledge, courses taken
    learning_goals = Column(Text, nullable=True)  # What they want to learn
    learning_pace = Column(String(20), default="medium")  # slow/medium/fast
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    progress = relationship("StudentProgress", back_populates="student")
    conversations = relationship("Conversation", back_populates="student")
    misconceptions = relationship("Misconception", back_populates="student")
    sessions = relationship("Session", back_populates="student")


class Topic(Base):
    """Curriculum topics with prerequisites."""

    __tablename__ = "topics"

    topic_id = Column(String(50), primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(Integer, default=1)  # 1-5 scale
    estimated_time_hours = Column(Float, nullable=True)
    category = Column(String(50), nullable=True)  # e.g., "sorting", "graphs", "dynamic_programming"
    keywords = Column(Text, nullable=True)  # JSON list of keywords
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prerequisites = relationship(
        "TopicPrerequisite",
        foreign_keys="TopicPrerequisite.topic_id",
        back_populates="topic"
    )
    required_for = relationship(
        "TopicPrerequisite",
        foreign_keys="TopicPrerequisite.prerequisite_id",
        back_populates="prerequisite"
    )
    progress = relationship("StudentProgress", back_populates="topic")


class TopicPrerequisite(Base):
    """Prerequisites relationships between topics."""

    __tablename__ = "topic_prerequisites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(String(50), ForeignKey("topics.topic_id"), nullable=False)
    prerequisite_id = Column(String(50), ForeignKey("topics.topic_id"), nullable=False)
    strength = Column(String(20), default="required")  # required/recommended/optional

    # Relationships
    topic = relationship("Topic", foreign_keys=[topic_id], back_populates="prerequisites")
    prerequisite = relationship("Topic", foreign_keys=[prerequisite_id], back_populates="required_for")

    __table_args__ = (
        Index("idx_topic_prereq", "topic_id", "prerequisite_id"),
    )


class StudentProgress(Base):
    """Student progress on topics."""

    __tablename__ = "student_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("students.user_id"), nullable=False)
    topic_id = Column(String(50), ForeignKey("topics.topic_id"), nullable=False)
    status = Column(String(20), default="not_started")  # not_started/learning/struggling/mastered
    understanding_score = Column(Float, default=0.0)  # 0-1 scale
    attempts = Column(Integer, default=0)
    time_spent_minutes = Column(Integer, default=0)
    last_studied_at = Column(DateTime, nullable=True)
    mastered_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)  # JSON: specific concepts mastered/struggling

    # Relationships
    student = relationship("Student", back_populates="progress")
    topic = relationship("Topic", back_populates="progress")

    __table_args__ = (
        Index("idx_user_topic", "user_id", "topic_id"),
        Index("idx_user_status", "user_id", "status"),
    )


class Conversation(Base):
    """Full conversation history."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey("sessions.session_id"), nullable=False)
    user_id = Column(String(50), ForeignKey("students.user_id"), nullable=False)
    topic_id = Column(String(50), ForeignKey("topics.topic_id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    role = Column(String(20), nullable=False)  # user/assistant/system
    content = Column(Text, nullable=False)
    agent_type = Column(String(50), nullable=True)  # orchestrator/tutor/assessor/etc
    message_metadata = Column(JSON, nullable=True)  # Additional context (retrieved chunks, reasoning, etc.)

    # Relationships
    student = relationship("Student", back_populates="conversations")
    session = relationship("Session", back_populates="messages")

    __table_args__ = (
        Index("idx_session_timestamp", "session_id", "timestamp"),
        Index("idx_user_timestamp", "user_id", "timestamp"),
    )


class Misconception(Base):
    """Tracked misconceptions with correction attempts."""

    __tablename__ = "misconceptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("students.user_id"), nullable=False)
    topic_id = Column(String(50), ForeignKey("topics.topic_id"), nullable=True)
    misconception_type = Column(String(50), nullable=False)  # conceptual/procedural/notation
    description = Column(Text, nullable=False)
    incorrect_belief = Column(Text, nullable=True)
    correct_concept = Column(Text, nullable=True)
    first_detected_at = Column(DateTime, default=datetime.utcnow)
    last_detected_at = Column(DateTime, default=datetime.utcnow)
    correction_attempts = Column(Integer, default=0)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="misconceptions")

    __table_args__ = (
        Index("idx_user_misconception", "user_id", "resolved"),
    )


class Assessment(Base):
    """Student responses and evaluations."""

    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey("sessions.session_id"), nullable=False)
    user_id = Column(String(50), ForeignKey("students.user_id"), nullable=False)
    topic_id = Column(String(50), ForeignKey("topics.topic_id"), nullable=True)
    question = Column(Text, nullable=False)
    student_response = Column(Text, nullable=False)
    understanding_score = Column(Float, nullable=True)  # 0-1 scale
    correctness_score = Column(Float, nullable=True)  # 0-1 scale
    depth_score = Column(Float, nullable=True)  # surface/intermediate/deep
    misconceptions_detected = Column(JSON, nullable=True)  # List of detected misconceptions
    feedback = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("Session", back_populates="assessments")

    __table_args__ = (
        Index("idx_user_assessment", "user_id", "timestamp"),
        Index("idx_session_assessment", "session_id", "timestamp"),
    )


class Session(Base):
    """Learning session metadata."""

    __tablename__ = "sessions"

    session_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("students.user_id"), nullable=False)
    topic_id = Column(String(50), ForeignKey("topics.topic_id"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    session_type = Column(String(20), default="learning")  # learning/practice/assessment
    goal = Column(Text, nullable=True)
    outcome = Column(Text, nullable=True)  # Summary of what was learned

    # Relationships
    student = relationship("Student", back_populates="sessions")
    messages = relationship("Conversation", back_populates="session")
    assessments = relationship("Assessment", back_populates="session")

    __table_args__ = (
        Index("idx_user_session", "user_id", "started_at"),
    )
