"""
LLM Chain Configuration and Prompts.

This module handles all interactions with the Language Model,
including prompt templates and response generation.
"""

from typing import Dict, Any, Optional, List
import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from data_model import (
    AgentState, CompanyInfo, JobOffer, KillerQuestion,
    ConversationMessage
)

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for LLM interactions.
    
    Manages prompt templates and LLM calls for different conversation
    stages in the recruitment process.
    """
    
    def __init__(self, model_name: str = "gemini-1.5-flash", temperature: float = 0.7):
        """
        Initialize LLM service.
        
        Args:
            model_name: Gemini model name
            temperature: LLM temperature for response generation
        """
        self.model_name = model_name
        self.temperature = temperature
        
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                convert_system_message_to_human=True
            )
        except Exception as e:
            logger.warning(f"Could not initialize Gemini model: {e}. Using mock LLM.")
            # For development/testing without API key
            self.llm = None
        
        self.output_parser = StrOutputParser()
    
    def _format_conversation_history(
        self, 
        messages: List[ConversationMessage], 
        max_messages: int = 5
    ) -> str:
        """
        Format conversation history for context.
        
        Args:
            messages: List of conversation messages
            max_messages: Maximum number of recent messages to include
            
        Returns:
            Formatted conversation history string
        """
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
        
        history = []
        for msg in recent_messages:
            sender = "Candidate" if msg.sender == "candidate" else "AI Recruiter"
            history.append(f"{sender}: {msg.content}")
        
        return "\n".join(history) if history else "No previous conversation."
    
    def generate_greeting(self, state: AgentState) -> str:
        """
        Generate initial greeting message.
        
        Args:
            state: Current agent state
            
        Returns:
            Greeting message string
        """
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an AI Recruiter for {company_name}. 
Your role is to have a friendly, professional conversation with candidates.

Generate a warm, welcoming greeting that:
1. Introduces yourself as an AI recruiter
2. Mentions you're reaching out about the {job_title} position
3. Asks if they have a few minutes to chat
4. Keeps it brief and friendly (2-3 sentences max)

Tone: Professional but warm and conversational."""),
            ("human", "Generate the greeting message.")
        ])
        
        company_name = state.company_info.company_name if state.company_info else "our company"
        job_title = state.job_offer.title if state.job_offer else "this position"
        
        if self.llm:
            chain = prompt_template | self.llm | self.output_parser
            try:
                response = chain.invoke({
                    "company_name": company_name,
                    "job_title": job_title
                })
                return response
            except Exception as e:
                logger.error(f"Error generating greeting: {e}")
        
        # Fallback greeting
        return (
            f"Hi! I'm an AI Recruiter from {company_name}. "
            f"I'm reaching out about our {job_title} position. "
            "Do you have a few minutes to chat about this opportunity?"
        )
    
    def generate_response(
        self,
        state: AgentState,
        context: Optional[str] = None
    ) -> str:
        """
        Generate contextual response based on conversation state.
        
        Args:
            state: Current agent state
            context: Additional context for response generation
            
        Returns:
            Generated response string
        """
        conversation_history = self._format_conversation_history(state.messages)
        
        system_prompt = f"""You are an AI Recruiter for {state.company_info.company_name if state.company_info else 'our company'}.

Your responsibilities:
- Engage candidates in friendly, professional conversations
- Answer questions about the company, role, and benefits
- Gather information about candidate qualifications
- Ask relevant follow-up questions
- Be concise and conversational (2-4 sentences typically)

Current conversation stage: {state.conversation_stage}
Candidate's last message: {state.last_message}

{context if context else ''}

Generate an appropriate, natural response."""
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{last_message}")
        ])
        
        if self.llm:
            chain = prompt_template | self.llm | self.output_parser
            try:
                response = chain.invoke({
                    "last_message": state.last_message,
                    "conversation_history": conversation_history
                })
                return response
            except Exception as e:
                logger.error(f"Error generating response: {e}")
        
        # Fallback response
        return "Thank you for your response. Could you tell me more about your experience?"
    
    def generate_company_response(
        self,
        state: AgentState,
        company_info: CompanyInfo
    ) -> str:
        """
        Generate response to company-related questions.
        
        Args:
            state: Current agent state
            company_info: Company information
            
        Returns:
            Generated response about the company
        """
        context = f"""
Company Information:
- Name: {company_info.company_name}
- Mission: {company_info.mission}
- Culture: {company_info.culture}
- Industry: {company_info.industry}
- Size: {company_info.size}
- Benefits: {', '.join(company_info.benefits[:5])}

Use this information to answer the candidate's question about the company.
Be enthusiastic but authentic. Keep response to 3-4 sentences."""
        
        return self.generate_response(state, context)
    
    def generate_job_response(
        self,
        state: AgentState,
        job_offer: JobOffer
    ) -> str:
        """
        Generate response to job-related questions.
        
        Args:
            state: Current agent state
            job_offer: Job offer details
            
        Returns:
            Generated response about the job
        """
        context = f"""
Job Information:
- Title: {job_offer.title}
- Description: {job_offer.description}
- Location: {job_offer.location}
- Remote Policy: {job_offer.remote_policy}
- Salary Range: {job_offer.salary_range}
- Key Requirements: {', '.join(job_offer.requirements[:3])}
- Team Size: {job_offer.team_size}

Use this information to answer the candidate's question about the role.
Be clear and helpful. Keep response to 3-4 sentences."""
        
        return self.generate_response(state, context)
    
    def generate_killer_question(
        self,
        state: AgentState,
        question: KillerQuestion
    ) -> str:
        """
        Generate a natural-sounding killer question.
        
        Args:
            state: Current agent state
            question: Killer question to ask
            
        Returns:
            Naturally phrased question
        """
        conversation_history = self._format_conversation_history(state.messages)
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an AI Recruiter conducting a screening conversation.

You need to ask this question: {question}

Rephrase it to sound natural and conversational based on the flow of the conversation.
Keep it friendly but professional. Output ONLY the question, nothing else."""),
            ("human", "Conversation so far:\n{conversation_history}\n\nGenerate the question.")
        ])
        
        if self.llm:
            chain = prompt_template | self.llm | self.output_parser
            try:
                response = chain.invoke({
                    "question": question.question,
                    "conversation_history": conversation_history
                })
                return response
            except Exception as e:
                logger.error(f"Error generating killer question: {e}")
        
        # Fallback to original question
        return question.question
    
    def extract_candidate_info(self, message: str) -> Dict[str, Any]:
        """
        Extract candidate information from their message.
        
        Args:
            message: Candidate message
            
        Returns:
            Dictionary with extracted information
        """
        # This is a simplified extraction
        # In production, use NER or structured output from LLM
        
        extracted = {}
        message_lower = message.lower()
        
        # Extract years of experience
        import re
        years_match = re.search(r'(\d+)\s*(?:years?|yrs?)', message_lower)
        if years_match:
            extracted['years_of_experience'] = int(years_match.group(1))
        
        # Extract skills (simple keyword matching)
        skill_keywords = [
            'python', 'java', 'javascript', 'typescript', 'go', 'rust',
            'react', 'vue', 'angular', 'django', 'flask', 'fastapi',
            'docker', 'kubernetes', 'aws', 'gcp', 'azure',
            'sql', 'postgresql', 'mongodb', 'redis',
            'machine learning', 'ai', 'ml', 'nlp', 'computer vision'
        ]
        
        found_skills = [skill for skill in skill_keywords if skill in message_lower]
        if found_skills:
            extracted['skills'] = found_skills
        
        return extracted
    
    def generate_evaluation_summary(
        self,
        state: AgentState
    ) -> str:
        """
        Generate a friendly closing message with evaluation summary.
        
        Args:
            state: Current agent state with evaluation
            
        Returns:
            Closing message string
        """
        if not state.evaluation:
            return "Thank you for your time today! We'll be in touch soon with next steps."
        
        eval_result = state.evaluation
        
        if eval_result.suitability == "high":
            message = (
                "Thank you so much for taking the time to chat with me today! "
                "Based on our conversation, I think you'd be a great fit for this role. "
                "Our team will review your profile and reach out within 2-3 business days "
                "to schedule the next interview. Looking forward to continuing the conversation!"
            )
        elif eval_result.suitability == "medium":
            message = (
                "Thank you for the conversation today! "
                "I'd like to have a member of our recruiting team do a quick follow-up call "
                "to discuss your background in more detail. "
                "Someone will reach out to you within the next week. Thanks again!"
            )
        else:
            message = (
                "Thank you for your interest and for taking the time to speak with me today. "
                "While this particular role might not be the perfect fit right now, "
                "we'll keep your information on file for future opportunities. "
                "Best of luck in your job search!"
            )
        
        return message
