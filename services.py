"""
Services Module for AI Recruiter Agent.

This module provides business logic services including RAG-like data retrieval,
candidate evaluation, and killer questions management.
"""

from typing import Dict, List, Optional
import logging
from data_model import (
    CandidateProfile, CompanyInfo, JobOffer, KillerQuestion,
    EvaluationResult
)

logger = logging.getLogger(__name__)


class DataService:
    """
    Service for retrieving company, job, and candidate data.
    
    Simulates a RAG (Retrieval-Augmented Generation) system with
    in-memory data storage. In production, this would connect to
    a vector database or traditional database.
    """
    
    def __init__(self):
        """Initialize the data service with mock data."""
        self._company_data = self._load_company_data()
        self._job_offers = self._load_job_offers()
        self._killer_questions_db = self._load_killer_questions()
    
    def _load_company_data(self) -> Dict[str, CompanyInfo]:
        """Load company information."""
        return {
            "tech_innovators": CompanyInfo(
                company_name="Tech Innovators Inc.",
                mission="Transform businesses through cutting-edge AI and cloud solutions",
                culture="We foster innovation, collaboration, and continuous learning. "
                        "Our culture emphasizes work-life balance and professional growth.",
                benefits=[
                    "Competitive salary and equity options",
                    "Flexible remote work policy",
                    "Health insurance (medical, dental, vision)",
                    "Annual learning budget of $3,000",
                    "Unlimited PTO policy",
                    "Parental leave: 16 weeks",
                    "Home office stipend",
                    "Annual company retreats"
                ],
                size="150-200 employees",
                industry="Technology / AI Solutions",
                website="https://techinnovators.example.com"
            )
        }
    
    def _load_job_offers(self) -> Dict[str, JobOffer]:
        """Load job offer details."""
        return {
            "senior_python_dev": JobOffer(
                job_id="senior_python_dev",
                title="Senior Python Developer",
                description="We're looking for a Senior Python Developer to join our AI Platform team. "
                           "You'll work on building scalable microservices and ML pipelines using modern Python frameworks.",
                requirements=[
                    "5+ years of Python development experience",
                    "Strong experience with FastAPI, Django, or Flask",
                    "Experience with cloud platforms (GCP, AWS, or Azure)",
                    "Proficiency in containerization (Docker, Kubernetes)",
                    "Strong understanding of microservices architecture",
                    "Experience with SQL and NoSQL databases",
                    "Excellent problem-solving skills"
                ],
                nice_to_have=[
                    "Experience with LangChain or LangGraph",
                    "Machine Learning/AI experience",
                    "Experience with CI/CD pipelines",
                    "Contributions to open-source projects",
                    "Experience with event-driven architectures"
                ],
                salary_range="$120,000 - $160,000 USD + equity",
                location="Remote (US/Europe) or Hybrid in San Francisco",
                remote_policy="Remote-first with optional office access",
                team_size=8
            ),
            "ml_engineer": JobOffer(
                job_id="ml_engineer",
                title="Machine Learning Engineer",
                description="Join our ML team to build and deploy production ML models that power our AI products.",
                requirements=[
                    "3+ years of ML engineering experience",
                    "Strong Python and ML frameworks (PyTorch, TensorFlow)",
                    "Experience deploying ML models to production",
                    "Understanding of MLOps practices",
                    "Experience with cloud ML platforms"
                ],
                nice_to_have=[
                    "Experience with LLMs and NLP",
                    "Research publications",
                    "Experience with A/B testing"
                ],
                salary_range="$130,000 - $180,000 USD + equity",
                location="Remote (Global)",
                remote_policy="Fully remote",
                team_size=6
            )
        }
    
    def _load_killer_questions(self) -> Dict[str, List[KillerQuestion]]:
        """Load killer questions by job role."""
        return {
            "senior_python_dev": [
                KillerQuestion(
                    question_id="python_exp",
                    question="Could you tell me about your experience with Python? "
                             "How many years have you worked with it professionally?",
                    expected_keywords=["5 years", "senior", "lead", "architect", "production", "scale"],
                    weight=0.3,
                    required=True
                ),
                KillerQuestion(
                    question_id="microservices",
                    question="Have you designed and built microservices architectures before? "
                             "Can you describe a project where you implemented this?",
                    expected_keywords=["microservices", "docker", "kubernetes", "api", "distributed", "scalable"],
                    weight=0.25,
                    required=True
                ),
                KillerQuestion(
                    question_id="cloud_experience",
                    question="What's your experience with cloud platforms like GCP, AWS, or Azure? "
                             "Which services have you worked with?",
                    expected_keywords=["gcp", "aws", "azure", "cloud run", "lambda", "kubernetes", "deployment"],
                    weight=0.25,
                    required=True
                ),
                KillerQuestion(
                    question_id="availability",
                    question="When would you be available to start if we move forward with an offer?",
                    expected_keywords=["immediately", "2 weeks", "notice", "available", "month"],
                    weight=0.2,
                    required=True
                )
            ],
            "ml_engineer": [
                KillerQuestion(
                    question_id="ml_experience",
                    question="Tell me about your ML engineering experience. "
                             "What types of models have you deployed to production?",
                    expected_keywords=["production", "deploy", "mlops", "model", "pytorch", "tensorflow"],
                    weight=0.35,
                    required=True
                ),
                KillerQuestion(
                    question_id="frameworks",
                    question="Which ML frameworks are you most comfortable with and why?",
                    expected_keywords=["pytorch", "tensorflow", "scikit", "keras", "transformers"],
                    weight=0.3,
                    required=True
                ),
                KillerQuestion(
                    question_id="availability",
                    question="When would you be available to start?",
                    expected_keywords=["immediately", "2 weeks", "notice", "available"],
                    weight=0.35,
                    required=True
                )
            ]
        }
    
    def get_company_info(self, company_id: str = "tech_innovators") -> Optional[CompanyInfo]:
        """
        Retrieve company information.
        
        Args:
            company_id: Company identifier
            
        Returns:
            CompanyInfo object or None if not found
        """
        return self._company_data.get(company_id)
    
    def get_job_offer(self, job_id: str) -> Optional[JobOffer]:
        """
        Retrieve job offer details.
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobOffer object or None if not found
        """
        return self._job_offers.get(job_id)
    
    def get_killer_questions(self, job_id: str) -> List[KillerQuestion]:
        """
        Retrieve killer questions for a specific job role.
        
        Args:
            job_id: Job identifier
            
        Returns:
            List of KillerQuestion objects
        """
        return self._killer_questions_db.get(job_id, [])
    
    def get_all_job_ids(self) -> List[str]:
        """Get all available job IDs."""
        return list(self._job_offers.keys())


class EvaluationService:
    """
    Service for evaluating candidate suitability.
    
    Analyzes candidate responses to killer questions and provides
    a comprehensive evaluation with scoring.
    """
    
    def __init__(self):
        """Initialize evaluation service."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def evaluate_candidate(
        self,
        killer_questions: List[KillerQuestion],
        killer_answers: Dict[str, str]
    ) -> EvaluationResult:
        """
        Evaluate candidate based on killer questions answers.
        
        Args:
            killer_questions: List of killer questions
            killer_answers: Dict mapping question_id to candidate answer
            
        Returns:
            EvaluationResult with scoring and recommendation
        """
        total_score = 0.0
        max_score = 0.0
        strengths = []
        concerns = []
        
        answered_count = len(killer_answers)
        total_questions = len(killer_questions)
        
        for question in killer_questions:
            max_score += question.weight * 100
            
            if question.question_id not in killer_answers:
                if question.required:
                    concerns.append(f"Did not answer required question: {question.question_id}")
                continue
            
            answer = killer_answers[question.question_id].lower()
            
            # Simple keyword matching for evaluation
            keyword_matches = sum(
                1 for keyword in question.expected_keywords 
                if keyword.lower() in answer
            )
            
            if keyword_matches > 0:
                # Score based on keyword match ratio
                match_ratio = keyword_matches / len(question.expected_keywords)
                question_score = match_ratio * question.weight * 100
                total_score += question_score
                
                if match_ratio > 0.5:
                    strengths.append(f"Strong answer to: {question.question_id}")
            else:
                if question.required:
                    concerns.append(f"Weak answer to required question: {question.question_id}")
        
        # Calculate final percentage
        overall_score = (total_score / max_score * 100) if max_score > 0 else 0.0
        
        # Determine suitability
        if overall_score >= 70:
            suitability = "high"
            recommendation = "Strong candidate. Recommend advancing to technical interview."
        elif overall_score >= 40:
            suitability = "medium"
            recommendation = "Potential candidate. Consider for phone screen to clarify concerns."
        else:
            suitability = "low"
            recommendation = "Not a strong match for this role at this time."
        
        # Add completion concern if not all questions answered
        if answered_count < total_questions:
            concerns.append(f"Answered {answered_count}/{total_questions} questions")
        
        return EvaluationResult(
            overall_score=round(overall_score, 2),
            suitability=suitability,
            killer_questions_answered=answered_count,
            killer_questions_total=total_questions,
            strengths=strengths,
            concerns=concerns,
            recommendation=recommendation
        )


class IntentClassificationService:
    """
    Service for classifying user intents.
    
    Determines what the candidate is asking about or what action
    they want to take.
    """
    
    INTENT_KEYWORDS = {
        "ask_company": ["company", "culture", "mission", "values", "benefits", "perks"],
        "ask_job": ["job", "role", "position", "responsibilities", "requirements", "salary"],
        "ask_team": ["team", "colleagues", "manager", "working with"],
        "ask_location": ["location", "remote", "office", "where", "timezone"],
        "provide_info": ["i am", "i have", "i work", "my experience", "i've been"],
        "answer_question": ["yes", "no", "sure", "absolutely", "correct"],
        "end_conversation": ["goodbye", "bye", "thank you", "thanks", "not interested"],
    }
    
    def classify_intent(self, message: str) -> str:
        """
        Classify the intent of a candidate message.
        
        Args:
            message: Candidate message
            
        Returns:
            Intent classification string
        """
        message_lower = message.lower()
        
        intent_scores = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)
        
        return "general_inquiry"
