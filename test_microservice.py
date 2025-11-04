"""
Unit Tests for AI Recruiter Agent Microservice.

Comprehensive test suite covering data models, services, and API endpoints.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from data_model import (
    CandidateProfile, CompanyInfo, JobOffer, KillerQuestion,
    EvaluationResult, AgentState, WebhookMessage
)
from services import DataService, EvaluationService, IntentClassificationService
from main import app


# ============ Fixtures ============

@pytest.fixture
def test_client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def data_service():
    """Create DataService instance."""
    return DataService()


@pytest.fixture
def evaluation_service():
    """Create EvaluationService instance."""
    return EvaluationService()


@pytest.fixture
def intent_service():
    """Create IntentClassificationService instance."""
    return IntentClassificationService()


@pytest.fixture
def sample_candidate():
    """Create sample candidate profile."""
    return CandidateProfile(
        candidate_id="test_candidate_123",
        name="John Doe",
        current_role="Software Engineer",
        years_of_experience=5,
        skills=["Python", "FastAPI", "Docker"],
        location="San Francisco",
        platform="linkedin"
    )


@pytest.fixture
def sample_killer_questions():
    """Create sample killer questions."""
    return [
        KillerQuestion(
            question_id="exp",
            question="How many years of Python experience do you have?",
            expected_keywords=["5 years", "python", "experience"],
            weight=0.5,
            required=True
        ),
        KillerQuestion(
            question_id="cloud",
            question="What's your experience with cloud platforms?",
            expected_keywords=["aws", "gcp", "azure", "cloud"],
            weight=0.5,
            required=True
        )
    ]


# ============ Data Model Tests ============

class TestDataModels:
    """Test suite for Pydantic data models."""
    
    def test_candidate_profile_creation(self, sample_candidate):
        """Test CandidateProfile model creation."""
        assert sample_candidate.candidate_id == "test_candidate_123"
        assert sample_candidate.name == "John Doe"
        assert sample_candidate.years_of_experience == 5
        assert "Python" in sample_candidate.skills
    
    def test_company_info_validation(self):
        """Test CompanyInfo model validation."""
        company = CompanyInfo(
            company_name="Tech Corp",
            mission="Innovate",
            culture="Collaborative",
            benefits=["Health insurance", "401k"],
            size="50-100",
            industry="Technology",
            website="https://techcorp.com"
        )
        assert company.company_name == "Tech Corp"
        assert len(company.benefits) == 2
    
    def test_killer_question_weight_validation(self):
        """Test KillerQuestion weight constraints."""
        # Valid weight
        q1 = KillerQuestion(
            question_id="q1",
            question="Test?",
            expected_keywords=["test"],
            weight=0.5,
            required=True
        )
        assert q1.weight == 0.5
        
        # Weight out of range should fail
        with pytest.raises(Exception):
            KillerQuestion(
                question_id="q2",
                question="Test?",
                expected_keywords=["test"],
                weight=1.5,  # Invalid: > 1.0
                required=True
            )
    
    def test_agent_state_initialization(self, sample_candidate):
        """Test AgentState initialization."""
        state = AgentState(
            session_id="test_session",
            candidate=sample_candidate,
            conversation_stage="greeting"
        )
        assert state.session_id == "test_session"
        assert state.conversation_stage == "greeting"
        assert state.conversation_ended is False
        assert len(state.messages) == 0


# ============ Service Tests ============

class TestDataService:
    """Test suite for DataService."""
    
    def test_get_company_info(self, data_service):
        """Test company info retrieval."""
        company = data_service.get_company_info("tech_innovators")
        assert company is not None
        assert company.company_name == "Tech Innovators Inc."
        assert len(company.benefits) > 0
    
    def test_get_job_offer(self, data_service):
        """Test job offer retrieval."""
        job = data_service.get_job_offer("senior_python_dev")
        assert job is not None
        assert job.title == "Senior Python Developer"
        assert job.job_id == "senior_python_dev"
        assert len(job.requirements) > 0
    
    def test_get_killer_questions(self, data_service):
        """Test killer questions retrieval."""
        questions = data_service.get_killer_questions("senior_python_dev")
        assert len(questions) > 0
        assert all(isinstance(q, KillerQuestion) for q in questions)
        assert all(q.weight > 0 for q in questions)
    
    def test_get_nonexistent_job(self, data_service):
        """Test retrieval of non-existent job."""
        job = data_service.get_job_offer("nonexistent_job")
        assert job is None


class TestEvaluationService:
    """Test suite for EvaluationService."""
    
    def test_evaluate_perfect_candidate(
        self,
        evaluation_service,
        sample_killer_questions
    ):
        """Test evaluation with perfect answers."""
        answers = {
            "exp": "I have 5 years of Python experience working on production systems",
            "cloud": "I've worked extensively with AWS and GCP for cloud deployments"
        }
        
        result = evaluation_service.evaluate_candidate(
            sample_killer_questions,
            answers
        )
        
        assert result.overall_score > 60
        assert result.suitability in ["medium", "high"]
        assert result.killer_questions_answered == 2
        assert len(result.strengths) > 0
    
    def test_evaluate_weak_candidate(
        self,
        evaluation_service,
        sample_killer_questions
    ):
        """Test evaluation with weak answers."""
        answers = {
            "exp": "I just started learning",
            "cloud": "Never used it"
        }
        
        result = evaluation_service.evaluate_candidate(
            sample_killer_questions,
            answers
        )
        
        assert result.overall_score < 50
        assert result.suitability in ["low", "medium"]
    
    def test_evaluate_partial_answers(
        self,
        evaluation_service,
        sample_killer_questions
    ):
        """Test evaluation with incomplete answers."""
        answers = {
            "exp": "I have 5 years of Python experience"
            # Missing 'cloud' answer
        }
        
        result = evaluation_service.evaluate_candidate(
            sample_killer_questions,
            answers
        )
        
        assert result.killer_questions_answered == 1
        assert result.killer_questions_total == 2
        assert len(result.concerns) > 0


class TestIntentClassificationService:
    """Test suite for IntentClassificationService."""
    
    def test_classify_company_intent(self, intent_service):
        """Test classification of company-related questions."""
        message = "Can you tell me more about your company culture?"
        intent = intent_service.classify_intent(message)
        assert intent == "ask_company"
    
    def test_classify_job_intent(self, intent_service):
        """Test classification of job-related questions."""
        message = "What are the main responsibilities of this role?"
        intent = intent_service.classify_intent(message)
        assert intent == "ask_job"
    
    def test_classify_provide_info_intent(self, intent_service):
        """Test classification of information provision."""
        message = "I have 5 years of experience with Python and Django"
        intent = intent_service.classify_intent(message)
        assert intent == "provide_info"
    
    def test_classify_end_intent(self, intent_service):
        """Test classification of conversation ending."""
        message = "Thank you, goodbye!"
        intent = intent_service.classify_intent(message)
        assert intent == "end_conversation"


# ============ API Tests ============

class TestAPIEndpoints:
    """Test suite for FastAPI endpoints."""
    
    def test_health_endpoint(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "endpoints" in data
    
    def test_start_conversation(self, test_client):
        """Test conversation start endpoint."""
        request_data = {
            "candidate_id": "test_123",
            "platform": "linkedin",
            "job_id": "senior_python_dev",
            "candidate_name": "Jane Smith"
        }
        
        response = test_client.post("/api/conversation/start", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "message" in data
        assert data["status"] == "conversation_started"
    
    def test_process_message(self, test_client):
        """Test message processing endpoint."""
        # First start a conversation
        start_request = {
            "candidate_id": "test_123",
            "platform": "linkedin",
            "job_id": "senior_python_dev"
        }
        start_response = test_client.post(
            "/api/conversation/start",
            json=start_request
        )
        session_id = start_response.json()["session_id"]
        
        # Then send a message
        message_request = {
            "session_id": session_id,
            "message": "I have 5 years of Python experience"
        }
        response = test_client.post(
            "/api/conversation/message",
            json=message_request
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "agent_response" in data
        assert "conversation_ended" in data
    
    def test_get_session_info(self, test_client):
        """Test session info retrieval."""
        # Start a conversation
        start_request = {
            "candidate_id": "test_123",
            "platform": "linkedin"
        }
        start_response = test_client.post(
            "/api/conversation/start",
            json=start_request
        )
        session_id = start_response.json()["session_id"]
        
        # Get session info
        response = test_client.get(f"/api/session/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "conversation_stage" in data
    
    def test_webhook_endpoint(self, test_client):
        """Test webhook endpoint."""
        webhook_data = {
            "platform": "linkedin",
            "candidate_id": "test_456",
            "message": "Hello, I'm interested in the position",
            "timestamp": datetime.now().isoformat(),
            "metadata": {}
        }
        
        response = test_client.post("/api/webhook", json=webhook_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
    
    def test_invalid_session(self, test_client):
        """Test message to invalid session."""
        message_request = {
            "session_id": "invalid_session_id",
            "message": "Hello"
        }
        response = test_client.post(
            "/api/conversation/message",
            json=message_request
        )
        assert response.status_code == 404


# ============ Integration Tests ============

class TestConversationFlow:
    """Integration tests for full conversation flow."""
    
    def test_complete_conversation_flow(self, test_client):
        """Test a complete conversation from start to finish."""
        # 1. Start conversation
        start_request = {
            "candidate_id": "integration_test",
            "platform": "linkedin",
            "job_id": "senior_python_dev"
        }
        start_response = test_client.post(
            "/api/conversation/start",
            json=start_request
        )
        assert start_response.status_code == 200
        session_id = start_response.json()["session_id"]
        
        # 2. Candidate provides information
        msg1 = {
            "session_id": session_id,
            "message": "I have 7 years of Python experience and worked with FastAPI"
        }
        response1 = test_client.post("/api/conversation/message", json=msg1)
        assert response1.status_code == 200
        
        # 3. Answer a question
        msg2 = {
            "session_id": session_id,
            "message": "I've worked with AWS, GCP, and deployed many microservices"
        }
        response2 = test_client.post("/api/conversation/message", json=msg2)
        assert response2.status_code == 200
        
        # 4. Check session info
        session_info = test_client.get(f"/api/session/{session_id}")
        assert session_info.status_code == 200
        data = session_info.json()
        assert data["messages_count"] >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.", "--cov-report=html"])
