"""
LangGraph State Machine for AI Recruiter Agent.

This module defines the conversation flow graph using LangGraph,
with nodes for each conversation stage and conditional routing logic.
"""

from typing import Literal, Optional
import logging
from langgraph.graph import StateGraph, END
from data_model import AgentState, ConversationMessage
from services import DataService, EvaluationService, IntentClassificationService
from llm_chain import LLMService

logger = logging.getLogger(__name__)


class RecruiterAgent:
    """
    AI Recruiter Agent using LangGraph for conversation orchestration.
    
    This agent manages the entire recruitment conversation flow from
    greeting to evaluation, with intelligent routing between stages.
    """
    
    def __init__(
        self,
        job_id: str = "senior_python_dev",
        company_id: str = "tech_innovators",
        llm_service: Optional[LLMService] = None
    ):
        """
        Initialize the recruiter agent.
        
        Args:
            job_id: Job identifier for this conversation
            company_id: Company identifier
            llm_service: Optional LLM service instance
        """
        self.job_id = job_id
        self.company_id = company_id
        
        # Initialize services
        self.data_service = DataService()
        self.evaluation_service = EvaluationService()
        self.intent_service = IntentClassificationService()
        self.llm_service = llm_service or LLMService()
        
        # Load job and company data
        self.company_info = self.data_service.get_company_info(company_id)
        self.job_offer = self.data_service.get_job_offer(job_id)
        self.killer_questions = self.data_service.get_killer_questions(job_id)
        
        # Build the graph
        self.graph = self._build_graph()
        self.app = self.graph.compile()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine.
        
        Returns:
            Compiled StateGraph
        """
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("recepcion_mensaje", self._receive_message_node)
        workflow.add_node("analisis_intencion", self._analyze_intent_node)
        workflow.add_node("obtencion_datos", self._gather_data_node)
        workflow.add_node("killer_questions", self._killer_questions_node)
        workflow.add_node("respuestas_compania", self._company_response_node)
        workflow.add_node("evaluacion_final", self._final_evaluation_node)
        workflow.add_node("finalizar_chat", self._finalize_chat_node)
        
        # Set entry point
        workflow.set_entry_point("recepcion_mensaje")
        
        # Add edges with conditional routing
        workflow.add_conditional_edges(
            "recepcion_mensaje",
            self._route_after_reception,
            {
                "analisis_intencion": "analisis_intencion",
                "finalizar": END
            }
        )
        
        workflow.add_conditional_edges(
            "analisis_intencion",
            self._route_after_intent,
            {
                "killer_questions": "killer_questions",
                "respuestas_compania": "respuestas_compania",
                "obtencion_datos": "obtencion_datos",
                "evaluacion_final": "evaluacion_final",
                "finalizar": "finalizar_chat"
            }
        )
        
        workflow.add_edge("obtencion_datos", "analisis_intencion")
        workflow.add_edge("respuestas_compania", "analisis_intencion")
        
        workflow.add_conditional_edges(
            "killer_questions",
            self._route_after_killer_question,
            {
                "continue_questions": "analisis_intencion",
                "evaluate": "evaluacion_final"
            }
        )
        
        workflow.add_edge("evaluacion_final", "finalizar_chat")
        workflow.add_edge("finalizar_chat", END)
        
        return workflow
    
    # ============ Node Functions ============
    
    def _receive_message_node(self, state: AgentState) -> AgentState:
        """
        Node: Receive and process incoming message.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        logger.info(f"[recepcion_mensaje] Processing message: {state.last_message[:50]}...")
        
        # Initialize company and job info if not present
        if state.company_info is None:
            state.company_info = self.company_info
        if state.job_offer is None:
            state.job_offer = self.job_offer
        if not state.killer_questions:
            state.killer_questions = self.killer_questions
        
        # If first message (greeting stage), send greeting
        if state.conversation_stage == "greeting" and len(state.messages) == 0:
            greeting = self.llm_service.generate_greeting(state)
            state.agent_response = greeting
            state.conversation_stage = "information_gathering"
            
            # Add agent greeting to conversation
            agent_msg = ConversationMessage(
                sender="agent",
                content=greeting,
                platform=state.candidate.platform if state.candidate else "linkedin"
            )
            state.messages.append(agent_msg)
        
        state.current_node = "recepcion_mensaje"
        return state
    
    def _analyze_intent_node(self, state: AgentState) -> AgentState:
        """
        Node: Analyze candidate message intent.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with classified intent
        """
        logger.info(f"[analisis_intencion] Analyzing intent for: {state.last_message[:50]}...")
        
        # Classify intent
        intent = self.intent_service.classify_intent(state.last_message)
        state.intent = intent
        
        logger.info(f"[analisis_intencion] Detected intent: {intent}")
        
        # Extract any candidate information
        extracted_info = self.llm_service.extract_candidate_info(state.last_message)
        if extracted_info and state.candidate:
            if 'years_of_experience' in extracted_info:
                state.candidate.years_of_experience = extracted_info['years_of_experience']
            if 'skills' in extracted_info:
                state.candidate.skills.extend(extracted_info['skills'])
                # Remove duplicates
                state.candidate.skills = list(set(state.candidate.skills))
        
        state.current_node = "analisis_intencion"
        return state
    
    def _gather_data_node(self, state: AgentState) -> AgentState:
        """
        Node: Gather candidate information.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        logger.info("[obtencion_datos] Gathering candidate data...")
        
        # Generate response to gather more information
        context = """The candidate is providing information about themselves.
Acknowledge what they shared and ask a relevant follow-up question to learn more
about their experience or skills."""
        
        response = self.llm_service.generate_response(state, context)
        state.agent_response = response
        
        # Add to conversation
        agent_msg = ConversationMessage(
            sender="agent",
            content=response,
            platform=state.candidate.platform if state.candidate else "linkedin"
        )
        state.messages.append(agent_msg)
        
        state.current_node = "obtencion_datos"
        return state
    
    def _killer_questions_node(self, state: AgentState) -> AgentState:
        """
        Node: Ask killer questions for evaluation.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        logger.info("[killer_questions] Processing killer questions...")
        
        # Check if we have unanswered killer questions
        unanswered_questions = [
            q for q in state.killer_questions
            if q.question_id not in state.killer_questions_asked
        ]
        
        if unanswered_questions:
            # Ask the next killer question
            next_question = unanswered_questions[0]
            question_text = self.llm_service.generate_killer_question(state, next_question)
            
            state.agent_response = question_text
            state.killer_questions_asked.append(next_question.question_id)
            
            # Update conversation stage
            state.conversation_stage = "killer_questions"
            
            # Add to conversation
            agent_msg = ConversationMessage(
                sender="agent",
                content=question_text,
                platform=state.candidate.platform if state.candidate else "linkedin"
            )
            state.messages.append(agent_msg)
            
            logger.info(f"[killer_questions] Asked: {next_question.question_id}")
        else:
            # Store the answer to the last killer question
            if state.killer_questions_asked:
                last_question_id = state.killer_questions_asked[-1]
                state.killer_answers[last_question_id] = state.last_message
                logger.info(f"[killer_questions] Stored answer for: {last_question_id}")
        
        state.current_node = "killer_questions"
        return state
    
    def _company_response_node(self, state: AgentState) -> AgentState:
        """
        Node: Respond to company/job questions.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        logger.info(f"[respuestas_compania] Responding to {state.intent} question...")
        
        # Generate appropriate response based on intent
        if state.intent in ["ask_company", "ask_team"]:
            response = self.llm_service.generate_company_response(
                state,
                state.company_info
            )
        elif state.intent in ["ask_job", "ask_location"]:
            response = self.llm_service.generate_job_response(
                state,
                state.job_offer
            )
        else:
            response = self.llm_service.generate_response(state)
        
        state.agent_response = response
        state.conversation_stage = "company_questions"
        
        # Add to conversation
        agent_msg = ConversationMessage(
            sender="agent",
            content=response,
            platform=state.candidate.platform if state.candidate else "linkedin"
        )
        state.messages.append(agent_msg)
        
        state.current_node = "respuestas_compania"
        return state
    
    def _final_evaluation_node(self, state: AgentState) -> AgentState:
        """
        Node: Perform final candidate evaluation.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with evaluation
        """
        logger.info("[evaluacion_final] Evaluating candidate...")
        
        # Store the last answer if in killer questions stage
        if state.conversation_stage == "killer_questions" and state.killer_questions_asked:
            last_question_id = state.killer_questions_asked[-1]
            if last_question_id not in state.killer_answers:
                state.killer_answers[last_question_id] = state.last_message
        
        # Perform evaluation
        evaluation = self.evaluation_service.evaluate_candidate(
            state.killer_questions,
            state.killer_answers
        )
        state.evaluation = evaluation
        state.conversation_stage = "evaluation"
        
        logger.info(
            f"[evaluacion_final] Score: {evaluation.overall_score}%, "
            f"Suitability: {evaluation.suitability}"
        )
        
        state.current_node = "evaluacion_final"
        return state
    
    def _finalize_chat_node(self, state: AgentState) -> AgentState:
        """
        Node: Finalize conversation and send closing message.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        logger.info("[finalizar_chat] Finalizing conversation...")
        
        # Generate closing message
        closing_message = self.llm_service.generate_evaluation_summary(state)
        state.agent_response = closing_message
        state.conversation_ended = True
        state.conversation_stage = "closing"
        
        # Add to conversation
        agent_msg = ConversationMessage(
            sender="agent",
            content=closing_message,
            platform=state.candidate.platform if state.candidate else "linkedin"
        )
        state.messages.append(agent_msg)
        
        state.current_node = "finalizar_chat"
        return state
    
    # ============ Routing Functions ============
    
    def _route_after_reception(
        self,
        state: AgentState
    ) -> Literal["analisis_intencion", "finalizar"]:
        """
        Route after message reception.
        
        Args:
            state: Current agent state
            
        Returns:
            Next node name
        """
        if state.conversation_ended:
            return "finalizar"
        
        # If it's the greeting, we already handled it, move to next message
        if state.conversation_stage == "information_gathering" and len(state.messages) == 1:
            # Wait for candidate response
            return "finalizar"
        
        return "analisis_intencion"
    
    def _route_after_intent(
        self,
        state: AgentState
    ) -> Literal[
        "killer_questions",
        "respuestas_compania",
        "obtencion_datos",
        "evaluacion_final",
        "finalizar"
    ]:
        """
        Route based on detected intent.
        
        Args:
            state: Current agent state
            
        Returns:
            Next node name
        """
        # Check if candidate wants to end conversation
        if state.intent == "end_conversation":
            # Do evaluation before ending if we have some answers
            if state.killer_answers:
                return "evaluacion_final"
            return "finalizar"
        
        # If we're in killer questions stage and haven't asked all questions
        if state.conversation_stage == "killer_questions":
            # Store the answer
            if state.killer_questions_asked and state.last_message:
                last_q_id = state.killer_questions_asked[-1]
                if last_q_id not in state.killer_answers:
                    state.killer_answers[last_q_id] = state.last_message
            
            # Check if more questions to ask
            remaining = [
                q for q in state.killer_questions
                if q.question_id not in state.killer_questions_asked
            ]
            
            if remaining:
                return "killer_questions"
            else:
                return "evaluacion_final"
        
        # Route based on intent
        if state.intent in ["ask_company", "ask_job", "ask_team", "ask_location"]:
            return "respuestas_compania"
        
        if state.intent == "provide_info":
            return "obtencion_datos"
        
        # After some information gathering, start killer questions
        if len(state.messages) >= 4 and not state.killer_questions_asked:
            return "killer_questions"
        
        # Default to gathering more data
        return "obtencion_datos"
    
    def _route_after_killer_question(
        self,
        state: AgentState
    ) -> Literal["continue_questions", "evaluate"]:
        """
        Route after asking a killer question.
        
        Args:
            state: Current agent state
            
        Returns:
            Next node name
        """
        # Check if all questions have been asked
        all_asked = all(
            q.question_id in state.killer_questions_asked
            for q in state.killer_questions
        )
        
        if all_asked:
            return "evaluate"
        
        return "continue_questions"
    
    # ============ Public Methods ============
    
    def process_message(self, state: AgentState) -> AgentState:
        """
        Process a candidate message through the graph.
        
        Args:
            state: Current agent state with new message
            
        Returns:
            Updated state after processing
        """
        try:
            # Run the graph
            result = self.app.invoke(state)
            return result
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            state.needs_human_intervention = True
            state.agent_response = (
                "I apologize, but I'm having some technical difficulties. "
                "A human recruiter will reach out to you shortly."
            )
            return state
