"""
AI Recruiter Agent Microservice - Main Application.

FastAPI-based microservice for autonomous recruitment conversations
using LangGraph and Google Cloud Run deployment.

Author: AI Recruiter Development Team
Standards: Senior A++ Clean Code
"""

import os
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from data_model import (
    AgentState, CandidateProfile, WebhookMessage, AgentResponse,
    ConversationMessage
)
from graph import RecruiterAgent
from llm_chain import LLMService

# ============ Configuration ============

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
PORT = int(os.getenv("PORT", "8080"))
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# ============ In-Memory Session Store ============
# In production, use Redis or Cloud Memorystore

class SessionStore:
    """
    Simple in-memory session store.
    
    In production, replace with Redis, Cloud Memorystore, or Firestore
    for persistent and distributed session management.
    """
    
    def __init__(self):
        """Initialize session store."""
        self._sessions: Dict[str, AgentState] = {}
    
    def get(self, session_id: str) -> Optional[AgentState]:
        """
        Retrieve session state.
        
        Args:
            session_id: Session identifier
            
        Returns:
            AgentState or None if not found
        """
        return self._sessions.get(session_id)
    
    def set(self, session_id: str, state: AgentState) -> None:
        """
        Store session state.
        
        Args:
            session_id: Session identifier
            state: Agent state to store
        """
        self._sessions[session_id] = state
    
    def delete(self, session_id: str) -> None:
        """
        Delete session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def exists(self, session_id: str) -> bool:
        """
        Check if session exists.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session exists
        """
        return session_id in self._sessions


# ============ Global State ============

session_store = SessionStore()
llm_service: Optional[LLMService] = None


# ============ Lifespan Context Manager ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting AI Recruiter Agent Microservice...")
    logger.info(f"Environment: {ENVIRONMENT}")
    
    global llm_service
    
    try:
        # Initialize LLM service
        llm_service = LLMService()
        logger.info("LLM Service initialized successfully")
    except Exception as e:
        logger.warning(f"LLM Service initialization warning: {e}")
        logger.warning("Service will run with limited functionality")
    
    logger.info("Microservice ready to accept requests")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Recruiter Agent Microservice...")


# ============ FastAPI Application ============

app = FastAPI(
    title="AI Recruiter Agent Microservice",
    description="Autonomous recruitment conversation agent using LangGraph",
    version="1.0.0",
    lifespan=lifespan
)


# ============ Request/Response Models ============

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    timestamp: datetime


class ConversationStartRequest(BaseModel):
    """Request to start a new conversation."""
    candidate_id: str = Field(..., description="Candidate identifier")
    platform: str = Field(..., description="Platform (linkedin/unipile)")
    job_id: str = Field(default="senior_python_dev", description="Job identifier")
    company_id: str = Field(default="tech_innovators", description="Company identifier")
    candidate_name: Optional[str] = Field(None, description="Optional candidate name")


class ConversationStartResponse(BaseModel):
    """Response when starting a conversation."""
    session_id: str
    message: str
    status: str


class MessageRequest(BaseModel):
    """Request to process a message."""
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., description="Candidate message")


class MessageResponse(BaseModel):
    """Response after processing a message."""
    session_id: str
    agent_response: str
    conversation_ended: bool
    evaluation: Optional[Dict] = None


# ============ API Endpoints ============

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint for Cloud Run.
    
    Returns:
        Health status information
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment=ENVIRONMENT,
        timestamp=datetime.now()
    )


@app.get("/")
async def root():
    """
    Root endpoint with service information.
    
    Returns:
        Service information
    """
    return {
        "service": "AI Recruiter Agent Microservice",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "start_conversation": "/api/conversation/start",
            "send_message": "/api/conversation/message",
            "webhook": "/api/webhook"
        }
    }


@app.post("/api/conversation/start", response_model=ConversationStartResponse)
async def start_conversation(request: ConversationStartRequest) -> ConversationStartResponse:
    """
    Start a new recruitment conversation.
    
    Args:
        request: Conversation start request
        
    Returns:
        Session ID and initial greeting
        
    Raises:
        HTTPException: If conversation cannot be started
    """
    try:
        # Generate unique session ID
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        
        logger.info(
            f"Starting new conversation - Session: {session_id}, "
            f"Candidate: {request.candidate_id}, Job: {request.job_id}"
        )
        
        # Create candidate profile
        candidate = CandidateProfile(
            candidate_id=request.candidate_id,
            name=request.candidate_name,
            platform=request.platform
        )
        
        # Initialize agent state
        state = AgentState(
            session_id=session_id,
            candidate=candidate,
            current_node="recepcion_mensaje",
            conversation_stage="greeting"
        )
        
        # Create agent instance
        agent = RecruiterAgent(
            job_id=request.job_id,
            company_id=request.company_id,
            llm_service=llm_service
        )
        
        # Process initial state (will generate greeting)
        result_state = agent.process_message(state)
        
        # Store session
        session_store.set(session_id, result_state)
        
        logger.info(f"Conversation started successfully - Session: {session_id}")
        
        return ConversationStartResponse(
            session_id=session_id,
            message=result_state.agent_response,
            status="conversation_started"
        )
        
    except Exception as e:
        logger.error(f"Error starting conversation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start conversation: {str(e)}"
        )


@app.post("/api/conversation/message", response_model=MessageResponse)
async def process_message(request: MessageRequest) -> MessageResponse:
    """
    Process a message from the candidate.
    
    Args:
        request: Message request with session ID and message content
        
    Returns:
        Agent response and conversation status
        
    Raises:
        HTTPException: If session not found or processing fails
    """
    try:
        # Retrieve session
        state = session_store.get(request.session_id)
        
        if not state:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {request.session_id}"
            )
        
        if state.conversation_ended:
            return MessageResponse(
                session_id=request.session_id,
                agent_response="This conversation has already ended. Please start a new conversation.",
                conversation_ended=True,
                evaluation=state.evaluation.dict() if state.evaluation else None
            )
        
        logger.info(
            f"Processing message - Session: {request.session_id}, "
            f"Message: {request.message[:50]}..."
        )
        
        # Add candidate message to state
        candidate_msg = ConversationMessage(
            sender="candidate",
            content=request.message,
            platform=state.candidate.platform
        )
        state.messages.append(candidate_msg)
        state.last_message = request.message
        
        # Create agent instance
        agent = RecruiterAgent(
            job_id=state.job_offer.job_id if state.job_offer else "senior_python_dev",
            company_id="tech_innovators",
            llm_service=llm_service
        )
        
        # Process message through graph
        result_state = agent.process_message(state)
        
        # Update session
        session_store.set(request.session_id, result_state)
        
        # Prepare response
        response = MessageResponse(
            session_id=request.session_id,
            agent_response=result_state.agent_response,
            conversation_ended=result_state.conversation_ended,
            evaluation=result_state.evaluation.dict() if result_state.evaluation else None
        )
        
        logger.info(
            f"Message processed - Session: {request.session_id}, "
            f"Stage: {result_state.conversation_stage}, "
            f"Ended: {result_state.conversation_ended}"
        )
        
        # Clean up session if conversation ended
        if result_state.conversation_ended:
            logger.info(f"Conversation ended - Session: {request.session_id}")
            # Could archive to database here
            # session_store.delete(request.session_id)  # Uncomment to auto-delete
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@app.post("/api/webhook")
async def webhook_handler(
    webhook_message: WebhookMessage,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """
    Webhook endpoint for receiving messages from LinkedIn/Unipile.
    
    This endpoint simulates integration with messaging platforms.
    In production, this would:
    1. Verify webhook signature
    2. Process message asynchronously
    3. Send response back to platform
    
    Args:
        webhook_message: Incoming webhook message
        background_tasks: FastAPI background tasks
        
    Returns:
        Acknowledgment response
    """
    try:
        logger.info(
            f"Webhook received - Platform: {webhook_message.platform}, "
            f"Candidate: {webhook_message.candidate_id}"
        )
        
        # In production, process this asynchronously
        # background_tasks.add_task(process_webhook_message, webhook_message)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "received",
                "message_id": f"msg_{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)}
        )


@app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    """
    Get information about an active session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session information
        
    Raises:
        HTTPException: If session not found
    """
    state = session_store.get(session_id)
    
    if not state:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {session_id}"
        )
    
    return {
        "session_id": session_id,
        "conversation_stage": state.conversation_stage,
        "messages_count": len(state.messages),
        "conversation_ended": state.conversation_ended,
        "killer_questions_asked": len(state.killer_questions_asked),
        "killer_questions_total": len(state.killer_questions),
        "evaluation": state.evaluation.dict() if state.evaluation else None,
        "candidate": {
            "id": state.candidate.candidate_id if state.candidate else None,
            "name": state.candidate.name if state.candidate else None,
            "platform": state.candidate.platform if state.candidate else None
        }
    }


# ============ Error Handlers ============

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler.
    
    Args:
        request: Request that caused the exception
        exc: Exception that was raised
        
    Returns:
        Error response
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
            "path": str(request.url)
        }
    )


# ============ Main Entry Point ============

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on port {PORT}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        access_log=True
    )
