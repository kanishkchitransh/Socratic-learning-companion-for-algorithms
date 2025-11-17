"""Database manager for SQLite operations."""

from contextlib import contextmanager
from typing import Generator, Optional, List, Dict, Any

from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import (
    Base,
    Student,
    Topic,
    TopicPrerequisite,
    StudentProgress,
    Conversation,
    Misconception,
    Assessment,
    Session as SessionModel,
)
from ..utils.config import settings
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manager for SQLite database operations."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager."""
        self.database_url = database_url or settings.database_url

        # Create engine with proper configuration
        if self.database_url.startswith("sqlite"):
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=settings.debug,
            )
        else:
            self.engine = create_engine(self.database_url, echo=settings.debug)

        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        logger.info("Database manager initialized", database_url=self.database_url)

    def create_tables(self) -> None:
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")

    def drop_tables(self) -> None:
        """Drop all tables (use with caution!)."""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session context manager."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            session.close()

    # Student operations
    def create_student(
        self,
        user_id: str,
        name: str,
        email: Optional[str] = None,
        background: Optional[str] = None,
        learning_goals: Optional[str] = None,
        learning_pace: str = "medium",
    ) -> Student:
        """Create a new student."""
        with self.get_session() as session:
            student = Student(
                user_id=user_id,
                name=name,
                email=email,
                background=background,
                learning_goals=learning_goals,
                learning_pace=learning_pace,
            )
            session.add(student)
            session.flush()
            session.refresh(student)
            session.expunge(student)  # Detach object from session
            logger.info("Student created", user_id=user_id, name=name)
            return student

    def get_student(self, user_id: str) -> Optional[Student]:
        """Get student by ID."""
        with self.get_session() as session:
            return session.query(Student).filter(Student.user_id == user_id).first()

    # Topic operations
    def create_topic(
        self,
        topic_id: str,
        title: str,
        description: Optional[str] = None,
        difficulty: int = 1,
        estimated_time_hours: Optional[float] = None,
        category: Optional[str] = None,
        keywords: Optional[str] = None,
    ) -> Topic:
        """Create a new topic."""
        with self.get_session() as session:
            topic = Topic(
                topic_id=topic_id,
                title=title,
                description=description,
                difficulty=difficulty,
                estimated_time_hours=estimated_time_hours,
                category=category,
                keywords=keywords,
            )
            session.add(topic)
            session.flush()
            session.refresh(topic)
            session.expunge(topic)  # Detach object from session
            logger.info("Topic created", topic_id=topic_id, title=title)
            return topic

    def add_prerequisite(
        self, topic_id: str, prerequisite_id: str, strength: str = "required"
    ) -> TopicPrerequisite:
        """Add a prerequisite relationship."""
        with self.get_session() as session:
            prereq = TopicPrerequisite(
                topic_id=topic_id,
                prerequisite_id=prerequisite_id,
                strength=strength,
            )
            session.add(prereq)
            session.flush()
            session.refresh(prereq)
            session.expunge(prereq)  # Detach object from session
            logger.info(
                "Prerequisite added",
                topic_id=topic_id,
                prerequisite_id=prerequisite_id,
                strength=strength,
            )
            return prereq

    def get_topic_prerequisites(self, topic_id: str) -> List[Topic]:
        """Get all prerequisites for a topic."""
        with self.get_session() as session:
            prereqs = (
                session.query(Topic)
                .join(TopicPrerequisite, Topic.topic_id == TopicPrerequisite.prerequisite_id)
                .filter(TopicPrerequisite.topic_id == topic_id)
                .all()
            )
            return prereqs

    def get_topics_by_category(self, category: str) -> List[Topic]:
        """Get all topics in a category."""
        with self.get_session() as session:
            return session.query(Topic).filter(Topic.category == category).all()

    # Student Progress operations
    def update_progress(
        self,
        user_id: str,
        topic_id: str,
        status: Optional[str] = None,
        understanding_score: Optional[float] = None,
        time_spent_minutes: Optional[int] = None,
    ) -> StudentProgress:
        """Update student progress on a topic."""
        with self.get_session() as session:
            progress = (
                session.query(StudentProgress)
                .filter(
                    and_(
                        StudentProgress.user_id == user_id,
                        StudentProgress.topic_id == topic_id,
                    )
                )
                .first()
            )

            if not progress:
                progress = StudentProgress(
                    user_id=user_id,
                    topic_id=topic_id,
                    status="not_started",
                    understanding_score=0.0,
                    attempts=0,
                    time_spent_minutes=0
                )
                session.add(progress)

            if status:
                progress.status = status
            if understanding_score is not None:
                progress.understanding_score = understanding_score
            if time_spent_minutes is not None:
                # Handle None values with or 0
                progress.time_spent_minutes = (progress.time_spent_minutes or 0) + time_spent_minutes

            # Handle None values with or 0
            progress.attempts = (progress.attempts or 0) + 1

            from datetime import datetime
            progress.last_studied_at = datetime.utcnow()

            if status == "mastered":
                progress.mastered_at = datetime.utcnow()

            session.flush()
            session.refresh(progress)
            session.expunge(progress)  # Detach object from session
            logger.info(
                "Progress updated",
                user_id=user_id,
                topic_id=topic_id,
                status=status,
                score=understanding_score,
            )
            return progress

    def get_student_progress(self, user_id: str) -> List[StudentProgress]:
        """Get all progress for a student."""
        with self.get_session() as session:
            return (
                session.query(StudentProgress)
                .filter(StudentProgress.user_id == user_id)
                .all()
            )

    def get_mastered_topics(self, user_id: str) -> List[str]:
        """Get list of mastered topic IDs for a student."""
        with self.get_session() as session:
            progress = (
                session.query(StudentProgress.topic_id)
                .filter(
                    and_(
                        StudentProgress.user_id == user_id,
                        StudentProgress.status == "mastered",
                    )
                )
                .all()
            )
            return [p.topic_id for p in progress]

    # Conversation operations
    def add_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        topic_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Conversation:
        """Add a message to conversation history."""
        with self.get_session() as session_db:
            message = Conversation(
                session_id=session_id,
                user_id=user_id,
                topic_id=topic_id,
                role=role,
                content=content,
                agent_type=agent_type,
                message_metadata=metadata,
            )
            session_db.add(message)
            session_db.flush()
            session_db.refresh(message)
            session_db.expunge(message)  # Detach object from session
            return message

    def get_conversation_history(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[Conversation]:
        """Get conversation history for a session."""
        with self.get_session() as session:
            query = (
                session.query(Conversation)
                .filter(Conversation.session_id == session_id)
                .order_by(Conversation.timestamp.asc())
            )
            if limit:
                query = query.limit(limit)
            return query.all()

    # Misconception operations
    def add_misconception(
        self,
        user_id: str,
        misconception_type: str,
        description: str,
        topic_id: Optional[str] = None,
        incorrect_belief: Optional[str] = None,
        correct_concept: Optional[str] = None,
    ) -> Misconception:
        """Record a new misconception."""
        with self.get_session() as session:
            misconception = Misconception(
                user_id=user_id,
                topic_id=topic_id,
                misconception_type=misconception_type,
                description=description,
                incorrect_belief=incorrect_belief,
                correct_concept=correct_concept,
            )
            session.add(misconception)
            session.flush()
            session.refresh(misconception)
            session.expunge(misconception)  # Detach object from session
            logger.info(
                "Misconception recorded",
                user_id=user_id,
                type=misconception_type,
                description=description,
            )
            return misconception

    def get_active_misconceptions(self, user_id: str) -> List[Misconception]:
        """Get unresolved misconceptions for a student."""
        with self.get_session() as session:
            return (
                session.query(Misconception)
                .filter(
                    and_(
                        Misconception.user_id == user_id,
                        Misconception.resolved == False,
                    )
                )
                .all()
            )

    # Session operations
    def create_session(
        self,
        session_id: str,
        user_id: str,
        topic_id: Optional[str] = None,
        session_type: str = "learning",
        goal: Optional[str] = None,
    ) -> SessionModel:
        """Create a new learning session."""
        with self.get_session() as session_db:
            session_obj = SessionModel(
                session_id=session_id,
                user_id=user_id,
                topic_id=topic_id,
                session_type=session_type,
                goal=goal,
            )
            session_db.add(session_obj)
            session_db.flush()
            session_db.refresh(session_obj)
            session_db.expunge(session_obj)  # Detach object from session
            logger.info("Session created", session_id=session_id, user_id=user_id)
            return session_obj

    def initialize_curriculum(self) -> None:
        """Initialize the curriculum with topics from Kleinberg-Tardos."""
        topics_data = [
            {
                "topic_id": "intro_algorithms",
                "title": "Introduction to Algorithms",
                "description": "Basic concepts, stable matching, Gale-Shapley algorithm",
                "difficulty": 1,
                "category": "fundamentals",
                "estimated_time_hours": 3.0,
            },
            {
                "topic_id": "algorithm_analysis",
                "title": "Algorithm Analysis",
                "description": "Computational tractability, asymptotic notation, survey of common functions",
                "difficulty": 2,
                "category": "fundamentals",
                "estimated_time_hours": 4.0,
            },
            {
                "topic_id": "graphs",
                "title": "Graphs",
                "description": "Basic definitions, graph connectivity, trees, traversal (BFS, DFS)",
                "difficulty": 2,
                "category": "data_structures",
                "estimated_time_hours": 5.0,
            },
            {
                "topic_id": "greedy_algorithms",
                "title": "Greedy Algorithms",
                "description": "Interval scheduling, Huffman codes, minimum spanning trees",
                "difficulty": 3,
                "category": "algorithms",
                "estimated_time_hours": 6.0,
            },
            {
                "topic_id": "divide_conquer",
                "title": "Divide and Conquer",
                "description": "Mergesort, recurrence relations, integer multiplication, matrix multiplication",
                "difficulty": 3,
                "category": "algorithms",
                "estimated_time_hours": 5.0,
            },
            {
                "topic_id": "dynamic_programming",
                "title": "Dynamic Programming",
                "description": "Weighted interval scheduling, segmented least squares, subset sum, sequence alignment",
                "difficulty": 4,
                "category": "algorithms",
                "estimated_time_hours": 8.0,
            },
            {
                "topic_id": "network_flow",
                "title": "Network Flow",
                "description": "Max-flow min-cut theorem, Ford-Fulkerson algorithm, bipartite matching",
                "difficulty": 4,
                "category": "algorithms",
                "estimated_time_hours": 7.0,
            },
            {
                "topic_id": "np_completeness",
                "title": "NP and Computational Intractability",
                "description": "P, NP, NP-complete problems, reductions",
                "difficulty": 5,
                "category": "complexity",
                "estimated_time_hours": 6.0,
            },
        ]

        # Create topics
        with self.get_session() as session:
            for topic_data in topics_data:
                existing = session.query(Topic).filter(Topic.topic_id == topic_data["topic_id"]).first()
                if not existing:
                    topic = Topic(**topic_data)
                    session.add(topic)

        # Define prerequisites
        prerequisites = [
            ("algorithm_analysis", "intro_algorithms", "required"),
            ("graphs", "algorithm_analysis", "required"),
            ("greedy_algorithms", "graphs", "required"),
            ("divide_conquer", "algorithm_analysis", "required"),
            ("dynamic_programming", "greedy_algorithms", "recommended"),
            ("dynamic_programming", "divide_conquer", "recommended"),
            ("network_flow", "graphs", "required"),
            ("network_flow", "greedy_algorithms", "recommended"),
            ("np_completeness", "algorithm_analysis", "required"),
            ("np_completeness", "dynamic_programming", "recommended"),
        ]

        with self.get_session() as session:
            for topic_id, prereq_id, strength in prerequisites:
                existing = (
                    session.query(TopicPrerequisite)
                    .filter(
                        and_(
                            TopicPrerequisite.topic_id == topic_id,
                            TopicPrerequisite.prerequisite_id == prereq_id,
                        )
                    )
                    .first()
                )
                if not existing:
                    prereq = TopicPrerequisite(
                        topic_id=topic_id,
                        prerequisite_id=prereq_id,
                        strength=strength,
                    )
                    session.add(prereq)

        logger.info("Curriculum initialized with topics and prerequisites")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get or create database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
