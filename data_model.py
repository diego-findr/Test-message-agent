"""
Data Models for AI Recruiter Agent Microservice.

This module defines all Pydantic models for type-safe data handling,
including the LangGraph state, candidate information, company data,
and job offer details.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class CandidateProfile(BaseModel):
    """Candidate information extracted from conversation."""
    
    candidate_id: str = Field(..., description="Unique identifier for the candidate")
    name: Optional[str] = Field(None, description="Candidate's full name")
    current_role: Optional[str] = Field(None, description="Current job position")
    years_of_experience: Optional[int] = Field(None, description="Total years of professional experience")
    skills: List[str] = Field(default_factory=list, description="List of candidate skills")
    location: Optional[str] = Field(None, description="Candidate's location")
    linkedin_profile: Optional[str] = Field(None, description="LinkedIn profile URL")
    platform: Literal["linkedin", "unipile"] = Field(..., description="Source platform")


class CompanyInfo(BaseModel):
    """Company information for candidate queries."""
    
    company_name: str = Field(..., description="Company name")
    mission: str = Field(..., description="Company mission statement")
    culture: str = Field(..., description="Company culture description")
    benefits: List[str] = Field(default_factory=list, description="Company benefits")
    size: str = Field(..., description="Company size (e.g., '100-500 employees')")
    industry: str = Field(..., description="Industry sector")
    website: str = Field(..., description="Company website URL")


class JobOffer(BaseModel):
    """Job offer details."""
    
    job_id: str = Field(..., description="Unique job identifier")
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Job description")
    requirements: List[str] = Field(default_factory=list, description="Required qualifications")
    nice_to_have: List[str] = Field(default_factory=list, description="Preferred qualifications")
    salary_range: str = Field(..., description="Salary range")
    location: str = Field(..., description="Job location")
    remote_policy: str = Field(..., description="Remote work policy")
    team_size: int = Field(..., description="Size of the team")


class KillerQuestion(BaseModel):
    """Killer question configuration."""
    
    question_id: str = Field(..., description="Unique question identifier")
    question: str = Field(..., description="Question text")
    expected_keywords: List[str] = Field(default_factory=list, description="Keywords for positive evaluation")
    weight: float = Field(1.0, ge=0.0, le=1.0, description="Question weight in final score")
    required: bool = Field(True, description="Whether this question is mandatory")


class ConversationMessage(BaseModel):
    """Individual message in the conversation."""
    
    timestamp: datetime = Field(default_factory=datetime.now)
    sender: Literal["candidate", "agent"] = Field(..., description="Message sender")
    content: str = Field(..., description="Message content")
    platform: Literal["linkedin", "unipile"] = Field(..., description="Platform origin")


class EvaluationResult(BaseModel):
    """Candidate evaluation result."""
    
    overall_score: float = Field(0.0, ge=0.0, le=100.0, description="Overall candidate score")
    suitability: Literal["low", "medium", "high"] = Field(..., description="Candidate suitability level")
    killer_questions_answered: int = Field(0, description="Number of killer questions answered")
    killer_questions_total: int = Field(0, description="Total killer questions")
    strengths: List[str] = Field(default_factory=list, description="Candidate strengths")
    concerns: List[str] = Field(default_factory=list, description="Potential concerns")
    recommendation: str = Field("", description="Recruiter recommendation")


class AgentState(BaseModel):
    """
    LangGraph State for AI Recruiter Agent.
    
    This state tracks the entire conversation flow and all relevant
    information collected during the recruitment process.
    """
    
    # Session information
    session_id: str = Field(..., description="Unique session identifier")
    current_node: str = Field("recepcion_mensaje", description="Current graph node")
    
    # Communication
    messages: List[ConversationMessage] = Field(default_factory=list, description="Conversation history")
    last_message: str = Field("", description="Last message from candidate")
    agent_response: str = Field("", description="Generated agent response")
    
    # Candidate data
    candidate: Optional[CandidateProfile] = Field(None, description="Candidate profile")
    
    # Context data
    company_info: Optional[CompanyInfo] = Field(None, description="Company information")
    job_offer: Optional[JobOffer] = Field(None, description="Job offer details")
    
    # Conversation flow
    intent: Optional[str] = Field(None, description="Detected user intent")
    conversation_stage: Literal[
        "greeting",
        "information_gathering",
        "killer_questions",
        "company_questions",
        "evaluation",
        "closing"
    ] = Field("greeting", description="Current conversation stage")
    
    # Killer questions
    killer_questions: List[KillerQuestion] = Field(default_factory=list, description="Killer questions for role")
    killer_questions_asked: List[str] = Field(default_factory=list, description="IDs of asked killer questions")
    killer_answers: Dict[str, str] = Field(default_factory=dict, description="Answers to killer questions")
    
    # Evaluation
    evaluation: Optional[EvaluationResult] = Field(None, description="Candidate evaluation")
    
    # Control flags
    conversation_ended: bool = Field(False, description="Whether conversation has ended")
    needs_human_intervention: bool = Field(False, description="Flag for human recruiter escalation")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True


class WebhookMessage(BaseModel):
    """Incoming webhook message from LinkedIn or Unipile."""
    
    platform: Literal["linkedin", "unipile"] = Field(..., description="Source platform")
    candidate_id: str = Field(..., description="Candidate identifier")
    message: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional platform metadata")


class AgentResponse(BaseModel):
    """Outgoing response to be sent to platform."""
    
    platform: Literal["linkedin", "unipile"] = Field(..., description="Target platform")
    candidate_id: str = Field(..., description="Candidate identifier")
    message: str = Field(..., description="Response message")
    session_id: str = Field(..., description="Session identifier")
    should_continue: bool = Field(True, description="Whether conversation should continue")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
