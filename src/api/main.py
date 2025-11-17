"""FastAPI application for Socratic Learning Companion."""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import uuid
from datetime import datetime

from .models import (
    StudentCreate, StudentResponse,
    SessionStart, SessionResponse,
    ChatMessage, ChatResponse,
    ProgressResponse, ProgressSummary,
    TopicResponse, CurriculumGraph,
    AssessmentSubmit, AssessmentResponse,
    ErrorResponse
)
from ..database.db_manager import get_db_manager
from ..agents.graph import get_learning_graph
from ..utils.config import settings
from ..utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Socratic Learning Companion for Algorithms - Multi-agent system teaching through questions"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize managers
db_manager = get_db_manager()
learning_graph = None  # Lazy loaded


def get_graph():
    """Get or create learning graph instance."""
    global learning_graph
    if learning_graph is None:
        learning_graph = get_learning_graph()
    return learning_graph


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


# Student endpoints
@app.post("/api/student/register", response_model=StudentResponse)
async def register_student(student: StudentCreate):
    """Register a new student."""
    try:
        # Validate user_id
        if not student.user_id or student.user_id.strip() == "":
            raise HTTPException(status_code=422, detail="user_id cannot be empty")

        logger.info("Registering student", user_id=student.user_id)

        # Check if student already exists
        existing = db_manager.get_student(student.user_id)
        if existing:
            raise HTTPException(status_code=400, detail="Student already exists")

        # Create student
        db_student = db_manager.create_student(
            user_id=student.user_id,
            name=student.name,
            email=student.email,
            background=student.background,
            learning_goals=student.learning_goals,
            learning_pace=student.learning_pace
        )

        logger.info("Student registered", user_id=student.user_id)

        # Convert to dict to avoid DetachedInstanceError
        return StudentResponse(
            user_id=db_student.user_id,
            name=db_student.name,
            email=db_student.email,
            background=db_student.background,
            learning_goals=db_student.learning_goals,
            learning_pace=db_student.learning_pace,
            created_at=db_student.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error registering student", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/student/{user_id}", response_model=StudentResponse)
async def get_student(user_id: str):
    """Get student information."""
    try:
        # Use session context to avoid DetachedInstanceError
        with db_manager.get_session() as session:
            from ..database.models import Student
            student = session.query(Student).filter(Student.user_id == user_id).first()

            if not student:
                raise HTTPException(status_code=404, detail="Student not found")

            # Access attributes within session
            return StudentResponse(
                user_id=student.user_id,
                name=student.name,
                email=student.email,
                background=student.background,
                learning_goals=student.learning_goals,
                learning_pace=student.learning_pace,
                created_at=student.created_at
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting student", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Session endpoints
@app.post("/api/session/start", response_model=SessionResponse)
async def start_session(session_start: SessionStart):
    """Start a new learning session."""
    try:
        session_id = str(uuid.uuid4())

        logger.info("Starting session", user_id=session_start.user_id, session_id=session_id)

        # Verify student exists
        student = db_manager.get_student(session_start.user_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        # Create session
        session = db_manager.create_session(
            session_id=session_id,
            user_id=session_start.user_id,
            topic_id=session_start.topic_id,
            session_type=session_start.session_type,
            goal=session_start.goal
        )

        logger.info("Session started", session_id=session_id)

        # Convert to dict to avoid DetachedInstanceError
        return SessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            topic_id=session.topic_id,
            session_type=session.session_type,
            goal=session.goal,
            started_at=session.started_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error starting session", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Chat endpoint (REST)
@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Process a chat message through the multi-agent system."""
    try:
        logger.info("Processing chat message", user_id=message.user_id, session_id=message.session_id)

        # Get student progress
        progress = db_manager.get_student_progress(message.user_id)
        mastered_topics = [p.topic_id for p in progress if p.status == "mastered"]

        # Get active misconceptions
        misconceptions = db_manager.get_active_misconceptions(message.user_id)

        # Build initial state
        state = {
            "user_id": message.user_id,
            "session_id": message.session_id,
            "current_topic_id": None,  # Will be set by curriculum planner
            "messages": [
                {"role": "user", "content": message.message}
            ],
            "student_background": None,
            "mastered_topics": mastered_topics,
            "understanding_score": 0.0,
            "active_misconceptions": [
                {"type": m.misconception_type, "description": m.description}
                for m in misconceptions
            ],
            "learning_pace": "medium",
            "retrieved_chunks": [],
            "teaching_stage": "exploration",
            "socratic_depth": 0,
            "next_agent": "orchestrator",
            "agent_reasoning": None,
            "orchestrator_output": None,
            "curriculum_planner_output": None,
            "tutor_output": None,
            "problem_generator_output": None,
            "assessor_output": None
        }

        # Invoke learning graph
        graph = get_graph()
        final_state = graph.invoke(state)

        # Extract response
        assistant_messages = [msg for msg in final_state.get("messages", []) if msg.get("role") == "assistant"]
        if assistant_messages:
            last_message = assistant_messages[-1]
            response_text = last_message.get("content", "")
            agent_type = last_message.get("agent_type")
        else:
            response_text = "I'm here to help you learn. What would you like to explore?"
            agent_type = None

        # Save conversation to database
        db_manager.add_message(
            session_id=message.session_id,
            user_id=message.user_id,
            role="user",
            content=message.message,
            agent_type="user"
        )

        db_manager.add_message(
            session_id=message.session_id,
            user_id=message.user_id,
            role="assistant",
            content=response_text,
            agent_type=agent_type
        )

        return ChatResponse(
            session_id=message.session_id,
            message=response_text,
            agent_type=agent_type,
            teaching_stage=final_state.get("teaching_stage"),
            understanding_score=final_state.get("understanding_score"),
            retrieved_chunks=final_state.get("retrieved_chunks")
        )

    except Exception as e:
        logger.error("Error processing chat", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Progress endpoints
@app.get("/api/student/{user_id}/progress", response_model=ProgressSummary)
async def get_student_progress(user_id: str):
    """Get student's learning progress summary."""
    try:
        progress_records = db_manager.get_student_progress(user_id)

        mastered = [p for p in progress_records if p.status == "mastered"]
        learning = [p for p in progress_records if p.status == "learning"]
        struggling = [p for p in progress_records if p.status == "struggling"]

        # Calculate overall understanding
        if progress_records:
            overall_understanding = sum(p.understanding_score for p in progress_records) / len(progress_records)
        else:
            overall_understanding = 0.0

        # Get current topic (last studied)
        current_topic = None
        if progress_records:
            latest = max(progress_records, key=lambda p: p.last_studied_at or datetime.min)
            if latest.status == "learning":
                current_topic = latest.topic_id

        return ProgressSummary(
            user_id=user_id,
            total_topics=len(progress_records),
            mastered_count=len(mastered),
            learning_count=len(learning),
            struggling_count=len(struggling),
            overall_understanding=overall_understanding,
            mastered_topics=[p.topic_id for p in mastered],
            current_topic=current_topic
        )

    except Exception as e:
        logger.error("Error getting progress", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Topic endpoints
@app.get("/api/curriculum/graph", response_model=CurriculumGraph)
async def get_curriculum_graph():
    """Get the full curriculum graph with prerequisites."""
    try:
        # Use session context to avoid DetachedInstanceError
        with db_manager.get_session() as session:
            from ..database.models import Topic, TopicPrerequisite

            # Get all topics
            topics_list = []
            for category in ["fundamentals", "data_structures", "algorithms", "complexity"]:
                category_topics = session.query(Topic).filter(Topic.category == category).all()
                topics_list.extend(category_topics)

            # Build topic responses and prerequisites within session
            topic_responses = []
            prerequisites = []

            for topic in topics_list:
                # Get prerequisites for this topic
                prereq_records = session.query(TopicPrerequisite).filter(
                    TopicPrerequisite.topic_id == topic.topic_id
                ).all()

                prereq_ids = []
                for prereq_rec in prereq_records:
                    prereq_ids.append(prereq_rec.prerequisite_id)
                    prerequisites.append({
                        "topic_id": topic.topic_id,
                        "prerequisite_id": prereq_rec.prerequisite_id
                    })

                # Build topic response
                topic_responses.append(TopicResponse(
                    topic_id=topic.topic_id,
                    title=topic.title,
                    description=topic.description,
                    difficulty=topic.difficulty,
                    estimated_time_hours=topic.estimated_time_hours,
                    category=topic.category,
                    prerequisites=prereq_ids
                ))

            return CurriculumGraph(
                topics=topic_responses,
                prerequisites=prerequisites
            )

    except Exception as e:
        logger.error("Error getting curriculum graph", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/topic/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: str):
    """Get topic details."""
    try:
        with db_manager.get_session() as session:
            from ..database.models import Topic, TopicPrerequisite
            topic = session.query(Topic).filter(Topic.topic_id == topic_id).first()

            if not topic:
                raise HTTPException(status_code=404, detail="Topic not found")

            # Get prerequisites within session
            prereq_records = session.query(TopicPrerequisite).filter(
                TopicPrerequisite.topic_id == topic_id
            ).all()
            prereq_ids = [p.prerequisite_id for p in prereq_records]

            return TopicResponse(
                topic_id=topic.topic_id,
                title=topic.title,
                description=topic.description,
                difficulty=topic.difficulty,
                estimated_time_hours=topic.estimated_time_hours,
                category=topic.category,
                prerequisites=prereq_ids
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting topic", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat/{user_id}/{session_id}")
async def websocket_chat(websocket: WebSocket, user_id: str, session_id: str):
    """WebSocket endpoint for real-time Socratic dialogue."""
    await websocket.accept()
    logger.info("WebSocket connected", user_id=user_id, session_id=session_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            logger.info("WebSocket message received", message_preview=data[:50])

            # Process through chat endpoint logic
            try:
                # Build message
                message = ChatMessage(
                    user_id=user_id,
                    session_id=session_id,
                    message=data
                )

                # Process (reuse chat logic)
                response = await chat(message)

                # Send response back
                await websocket.send_json({
                    "message": response.message,
                    "agent_type": response.agent_type,
                    "teaching_stage": response.teaching_stage,
                    "understanding_score": response.understanding_score
                })

            except Exception as e:
                logger.error("Error processing WebSocket message", error=str(e))
                await websocket.send_json({
                    "error": str(e),
                    "message": "Sorry, I encountered an error processing your message."
                })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", user_id=user_id, session_id=session_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
