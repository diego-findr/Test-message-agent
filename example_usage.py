"""
Example Usage of AI Recruiter Agent Microservice.

This script demonstrates a complete conversation flow from start to finish,
showcasing all major features of the agent.
"""

import logging
from datetime import datetime

from data_model import AgentState, CandidateProfile, ConversationMessage
from graph import RecruiterAgent
from llm_chain import LLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_separator():
    """Print visual separator."""
    print("\n" + "="*80 + "\n")


def print_message(sender: str, message: str):
    """
    Print formatted message.
    
    Args:
        sender: Message sender (Agent or Candidate)
        message: Message content
    """
    print(f"[{sender}]: {message}")


def simulate_conversation():
    """
    Simulate a complete recruitment conversation.
    
    This example demonstrates:
    1. Conversation initialization
    2. Information gathering
    3. Killer questions
    4. Company questions
    5. Final evaluation
    """
    print_separator()
    print("🤖 AI RECRUITER AGENT - CONVERSATION SIMULATION")
    print_separator()
    
    # Initialize the agent
    logger.info("Initializing AI Recruiter Agent...")
    llm_service = LLMService()
    agent = RecruiterAgent(
        job_id="senior_python_dev",
        company_id="tech_innovators",
        llm_service=llm_service
    )
    
    # Create candidate profile
    candidate = CandidateProfile(
        candidate_id="candidate_12345",
        name="Sarah Johnson",
        platform="linkedin"
    )
    
    # Initialize conversation state
    state = AgentState(
        session_id="demo_session_001",
        candidate=candidate,
        current_node="recepcion_mensaje",
        conversation_stage="greeting"
    )
    
    print("📝 Candidate Profile:")
    print(f"   Name: {candidate.name}")
    print(f"   ID: {candidate.candidate_id}")
    print(f"   Platform: {candidate.platform}")
    print_separator()
    
    # Step 1: Initial greeting
    print("STEP 1: INITIAL GREETING")
    print("-" * 80)
    
    state = agent.process_message(state)
    print_message("AI Recruiter", state.agent_response)
    print_separator()
    
    # Step 2: Candidate responds positively
    print("STEP 2: CANDIDATE ENGAGEMENT")
    print("-" * 80)
    
    candidate_msg1 = "Hi! Yes, I'd love to learn more about this opportunity."
    print_message("Candidate", candidate_msg1)
    
    state.messages.append(ConversationMessage(
        sender="candidate",
        content=candidate_msg1,
        platform="linkedin"
    ))
    state.last_message = candidate_msg1
    
    state = agent.process_message(state)
    print_message("AI Recruiter", state.agent_response)
    print_separator()
    
    # Step 3: Candidate provides experience
    print("STEP 3: INFORMATION SHARING")
    print("-" * 80)
    
    candidate_msg2 = (
        "I have 6 years of professional Python development experience. "
        "I've worked extensively with FastAPI, Django, and Flask to build "
        "scalable microservices. I'm also experienced with Docker and Kubernetes."
    )
    print_message("Candidate", candidate_msg2)
    
    state.messages.append(ConversationMessage(
        sender="candidate",
        content=candidate_msg2,
        platform="linkedin"
    ))
    state.last_message = candidate_msg2
    
    state = agent.process_message(state)
    print_message("AI Recruiter", state.agent_response)
    print_separator()
    
    # Step 4: Answer killer question about microservices
    print("STEP 4: KILLER QUESTION - MICROSERVICES")
    print("-" * 80)
    
    candidate_msg3 = (
        "Yes, absolutely! In my last role, I designed and built a microservices "
        "architecture for an e-commerce platform. We used Docker containers, "
        "deployed on Kubernetes, with API Gateway for routing. The system handled "
        "over 10,000 requests per second and scaled horizontally based on load."
    )
    print_message("Candidate", candidate_msg3)
    
    state.messages.append(ConversationMessage(
        sender="candidate",
        content=candidate_msg3,
        platform="linkedin"
    ))
    state.last_message = candidate_msg3
    
    state = agent.process_message(state)
    print_message("AI Recruiter", state.agent_response)
    print_separator()
    
    # Step 5: Answer killer question about cloud
    print("STEP 5: KILLER QUESTION - CLOUD EXPERIENCE")
    print("-" * 80)
    
    candidate_msg4 = (
        "I have extensive experience with both GCP and AWS. On GCP, I've worked with "
        "Cloud Run, Cloud Functions, GKE, and BigQuery. On AWS, I've used Lambda, "
        "ECS, RDS, and S3. I've also set up CI/CD pipelines using Cloud Build and "
        "GitHub Actions for automated deployments."
    )
    print_message("Candidate", candidate_msg4)
    
    state.messages.append(ConversationMessage(
        sender="candidate",
        content=candidate_msg4,
        platform="linkedin"
    ))
    state.last_message = candidate_msg4
    
    state = agent.process_message(state)
    print_message("AI Recruiter", state.agent_response)
    print_separator()
    
    # Step 6: Answer availability question
    print("STEP 6: KILLER QUESTION - AVAILABILITY")
    print("-" * 80)
    
    candidate_msg5 = "I can start in 2 weeks after giving proper notice to my current employer."
    print_message("Candidate", candidate_msg5)
    
    state.messages.append(ConversationMessage(
        sender="candidate",
        content=candidate_msg5,
        platform="linkedin"
    ))
    state.last_message = candidate_msg5
    
    state = agent.process_message(state)
    print_message("AI Recruiter", state.agent_response)
    print_separator()
    
    # Display final evaluation
    print("📊 FINAL EVALUATION RESULTS")
    print("-" * 80)
    
    if state.evaluation:
        eval_result = state.evaluation
        print(f"Overall Score: {eval_result.overall_score}%")
        print(f"Suitability: {eval_result.suitability.upper()}")
        print(f"Questions Answered: {eval_result.killer_questions_answered}/{eval_result.killer_questions_total}")
        print(f"\nStrengths:")
        for strength in eval_result.strengths:
            print(f"  ✓ {strength}")
        
        if eval_result.concerns:
            print(f"\nConcerns:")
            for concern in eval_result.concerns:
                print(f"  ⚠ {concern}")
        
        print(f"\nRecommendation: {eval_result.recommendation}")
    
    print_separator()
    
    # Display conversation summary
    print("📝 CONVERSATION SUMMARY")
    print("-" * 80)
    print(f"Session ID: {state.session_id}")
    print(f"Total Messages: {len(state.messages)}")
    print(f"Conversation Stage: {state.conversation_stage}")
    print(f"Conversation Ended: {state.conversation_ended}")
    print(f"Duration: Simulated")
    
    print_separator()
    print("✅ SIMULATION COMPLETED")
    print_separator()


def demonstrate_api_usage():
    """
    Demonstrate API usage with example requests.
    """
    print_separator()
    print("🌐 API USAGE EXAMPLES")
    print_separator()
    
    print("1. START A CONVERSATION")
    print("-" * 80)
    print("POST /api/conversation/start")
    print("Content-Type: application/json")
    print()
    print("Request Body:")
    print('''{
    "candidate_id": "linkedin_12345",
    "platform": "linkedin",
    "job_id": "senior_python_dev",
    "company_id": "tech_innovators",
    "candidate_name": "John Doe"
}''')
    print()
    print("Response:")
    print('''{
    "session_id": "session_abc123",
    "message": "Hi! I'm an AI Recruiter from Tech Innovators Inc...",
    "status": "conversation_started"
}''')
    print_separator()
    
    print("2. SEND A MESSAGE")
    print("-" * 80)
    print("POST /api/conversation/message")
    print("Content-Type: application/json")
    print()
    print("Request Body:")
    print('''{
    "session_id": "session_abc123",
    "message": "I have 5 years of Python experience with FastAPI and Django"
}''')
    print()
    print("Response:")
    print('''{
    "session_id": "session_abc123",
    "agent_response": "That's great to hear! Can you tell me about...",
    "conversation_ended": false,
    "evaluation": null
}''')
    print_separator()
    
    print("3. CHECK SESSION INFO")
    print("-" * 80)
    print("GET /api/session/{session_id}")
    print()
    print("Response:")
    print('''{
    "session_id": "session_abc123",
    "conversation_stage": "killer_questions",
    "messages_count": 6,
    "conversation_ended": false,
    "killer_questions_asked": 2,
    "killer_questions_total": 4,
    "evaluation": null,
    "candidate": {
        "id": "linkedin_12345",
        "name": "John Doe",
        "platform": "linkedin"
    }
}''')
    print_separator()


def main():
    """Main execution function."""
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*20 + "AI RECRUITER AGENT MICROSERVICE" + " "*27 + "║")
    print("║" + " "*27 + "EXAMPLE USAGE" + " "*38 + "║")
    print("╚" + "═"*78 + "╝")
    print()
    
    try:
        # Run conversation simulation
        simulate_conversation()
        
        # Show API examples
        demonstrate_api_usage()
        
        print("\n✨ All examples completed successfully!")
        print()
        print("To run the microservice:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Set environment variables (copy .env.example to .env)")
        print("  3. Run server: python main.py")
        print("  4. Access API at: http://localhost:8080")
        print()
        print("To run tests:")
        print("  pytest test_microservice.py -v --cov")
        print()
        print("To deploy to Google Cloud Run:")
        print("  ./deploy.sh your-project-id us-central1")
        print()
        
    except Exception as e:
        logger.error(f"Error in example execution: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
