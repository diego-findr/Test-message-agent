"""
Microservicio de Agente Recruiter de IA (AIR)

Este módulo implementa un agente conversacional autónomo utilizando LangGraph
para orquestar conversaciones con candidatos a través de plataformas de mensajería,
evaluar su idoneidad y proporcionar información sobre la compañía y ofertas de trabajo.

Autor: Senior A++ Engineer
Versión: 1.0.0
"""

import json
import os
import logging
from typing import TypedDict, List, Dict, Optional, Literal, Annotated
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# 1. DEFINICIÓN DEL ESTADO DEL AGENTE (Pydantic)
# ============================================================================


class Platform(str, Enum):
    """Enum para identificar las plataformas de mensajería."""
    LINKEDIN = "linkedin"
    UNIPILE = "unipile"


class SuitabilityScore(str, Enum):
    """Enum para la puntuación de idoneidad del candidato."""
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class CandidateInfo(BaseModel):
    """Modelo de datos del candidato."""
    nombre: Optional[str] = None
    rol_actual: Optional[str] = None
    experiencia_anos: Optional[int] = None
    ubicacion: Optional[str] = None
    linkedin_url: Optional[str] = None


class CompanyInfo(BaseModel):
    """Modelo de información de la compañía."""
    nombre: str
    mision: str
    cultura: str
    beneficios: List[str]
    valores: List[str]


class JobOffer(BaseModel):
    """Modelo de información de la oferta de trabajo."""
    titulo: str
    salario_min: float
    salario_max: float
    moneda: str
    ubicacion: str
    requisitos: List[str]
    responsabilidades: List[str]
    tipo_contrato: str


class KillerQuestion(BaseModel):
    """Modelo para las preguntas críticas."""
    pregunta: str
    respuesta_candidato: Optional[str] = None
    peso: float = Field(default=1.0, ge=0.0, le=1.0)
    evaluacion: Optional[str] = None


class ConversationState(TypedDict):
    """
    Estado del grafo de conversación.
    
    Utiliza TypedDict para mantener compatibilidad con LangGraph mientras
    aprovecha la validación de tipos de Python.
    """
    # Información del mensaje entrante
    mensaje_entrante: str
    plataforma: Platform
    candidato_id: str
    timestamp: str
    
    # Información del candidato (extraída durante la conversación)
    candidato_info: Dict
    
    # Información de la compañía y oferta (cargada desde RAG)
    company_info: Optional[Dict]
    job_offer: Optional[Dict]
    
    # Análisis de intención
    intencion: Optional[str]
    confianza_intencion: Optional[float]
    
    # Estado de killer questions
    killer_questions: List[Dict]
    pregunta_actual_indice: int
    esperando_respuesta_killer: bool
    
    # Respuestas del agente
    respuesta_agente: str
    mensajes_conversacion: Annotated[List, add_messages]
    
    # Evaluación final
    puntuacion_idoneidad: Optional[SuitabilityScore]
    razones_evaluacion: List[str]
    
    # Control de flujo
    estado_actual: str
    finalizado: bool


# ============================================================================
# 2. SERVICIOS Y DATOS SIMULADOS (RAG)
# ============================================================================


class DataService:
    """
    Servicio para simular acceso a datos de compañía y ofertas.
    
    En producción, este servicio se conectaría a una base de datos real
    o sistema de almacenamiento.
    """
    
    def __init__(self) -> None:
        """Inicializa el servicio con datos simulados."""
        self._company_data: Dict = {
            "nombre": "TechInnovate Solutions",
            "mision": "Transformar el futuro mediante soluciones tecnológicas innovadoras que empoderan a las empresas y mejoran la vida de las personas.",
            "cultura": "Cultura de innovación continua, colaboración interdisciplinaria y desarrollo profesional. Fomentamos la creatividad, la diversidad y el equilibrio trabajo-vida.",
            "beneficios": [
                "Seguro médico premium completo",
                "Plan de retiro 401(k) con match del 6%",
                "Vacaciones ilimitadas con políticas responsables",
                "Presupuesto anual de $5,000 para desarrollo profesional",
                "Work from home flexible",
                "Equidad en la compañía",
                "Bonos por desempeño trimestrales"
            ],
            "valores": [
                "Innovación",
                "Integridad",
                "Colaboración",
                "Excelencia",
                "Diversidad e Inclusión"
            ]
        }
        
        self._job_offers: Dict[str, Dict] = {
            "senior_software_engineer": {
                "titulo": "Senior Software Engineer",
                "salario_min": 120000.0,
                "salario_max": 180000.0,
                "moneda": "USD",
                "ubicacion": "Remoto (PST/EST)",
                "requisitos": [
                    "5+ años de experiencia en desarrollo de software",
                    "Experiencia con Python, JavaScript/TypeScript",
                    "Conocimiento de arquitecturas de microservicios",
                    "Experiencia con cloud (GCP, AWS, o Azure)",
                    "Inglés fluido (escrito y hablado)"
                ],
                "responsabilidades": [
                    "Diseñar e implementar sistemas escalables",
                    "Colaborar con equipos cross-functional",
                    "Mentorear desarrolladores junior",
                    "Participar en code reviews y arquitectura técnica"
                ],
                "tipo_contrato": "Tiempo completo"
            },
            "data_scientist": {
                "titulo": "Data Scientist",
                "salario_min": 110000.0,
                "salario_max": 160000.0,
                "moneda": "USD",
                "ubicacion": "Híbrido (San Francisco)",
                "requisitos": [
                    "3+ años de experiencia en ciencia de datos",
                    "Experiencia con ML/DL (TensorFlow, PyTorch)",
                    "Dominio de Python y SQL",
                    "Experiencia con análisis estadístico",
                    "Portfolio de proyectos ML"
                ],
                "responsabilidades": [
                    "Desarrollar modelos predictivos",
                    "Analizar grandes volúmenes de datos",
                    "Colaborar con equipos de producto",
                    "Presentar insights a stakeholders"
                ],
                "tipo_contrato": "Tiempo completo"
            }
        }
        
        self._killer_questions_by_role: Dict[str, List[Dict]] = {
            "senior_software_engineer": [
                {
                    "pregunta": "¿Cuál es tu experiencia con arquitecturas de microservicios? ¿Puedes describir un proyecto donde hayas diseñado o mantenido un sistema distribuido?",
                    "peso": 0.3
                },
                {
                    "pregunta": "¿Tienes experiencia liderando proyectos técnicos o mentoreando desarrolladores? ¿Cómo abordas la mentoría?",
                    "peso": 0.25
                },
                {
                    "pregunta": "¿Qué tecnologías de cloud computing has utilizado en producción? ¿Puedes describir tu experiencia con contenedores y orquestación?",
                    "peso": 0.25
                },
                {
                    "pregunta": "¿Estás disponible para trabajar en horario PST/EST? ¿Tienes experiencia trabajando en equipos distribuidos internacionalmente?",
                    "peso": 0.2
                }
            ],
            "data_scientist": [
                {
                    "pregunta": "¿Puedes describir un proyecto de machine learning completo que hayas desarrollado desde la concepción hasta el despliegue?",
                    "peso": 0.35
                },
                {
                    "pregunta": "¿Qué frameworks de deep learning has utilizado en producción? ¿Puedes explicar cuándo usarías TensorFlow vs PyTorch?",
                    "peso": 0.3
                },
                {
                    "pregunta": "¿Tienes experiencia trabajando con equipos de producto para definir métricas y KPIs? ¿Cómo comunicas insights técnicos a no-técnicos?",
                    "peso": 0.2
                },
                {
                    "pregunta": "¿Estarías disponible para trabajar en formato híbrido en San Francisco?",
                    "peso": 0.15
                }
            ]
        }
    
    def get_company_info(self) -> CompanyInfo:
        """
        Obtiene la información de la compañía.
        
        Returns:
            CompanyInfo: Información completa de la compañía.
        """
        return CompanyInfo(**self._company_data)
    
    def get_job_offer(self, role_key: str) -> Optional[JobOffer]:
        """
        Obtiene la información de una oferta de trabajo por clave.
        
        Args:
            role_key: Clave identificadora del rol (ej. 'senior_software_engineer').
            
        Returns:
            JobOffer si existe, None en caso contrario.
        """
        if role_key in self._job_offers:
            return JobOffer(**self._job_offers[role_key])
        return None
    
    def get_killer_questions(self, role_key: str) -> List[KillerQuestion]:
        """
        Obtiene las killer questions para un rol específico.
        
        Args:
            role_key: Clave identificadora del rol.
            
        Returns:
            Lista de KillerQuestion para el rol.
        """
        if role_key in self._killer_questions_by_role:
            return [
                KillerQuestion(**q) for q in self._killer_questions_by_role[role_key]
            ]
        return []


class LLMService:
    """
    Servicio para interactuar con el modelo de lenguaje.
    
    Utiliza Google Gemini como modelo LLM para análisis y generación de respuestas.
    """
    
    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Inicializa el servicio LLM.
        
        Args:
            api_key: API key de Google Gemini. Si es None, intenta obtenerla de env.
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "dummy-key")
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=self.api_key,
                temperature=0.7
            )
        except Exception as e:
            logger.warning(f"No se pudo inicializar Gemini. Usando placeholder: {e}")
            self.llm = None
    
    def analyze_intention(self, message: str, conversation_history: List) -> Dict[str, any]:
        """
        Analiza la intención del mensaje del candidato.
        
        Args:
            message: Mensaje del candidato.
            conversation_history: Historial de mensajes previos.
            
        Returns:
            Dict con 'intencion' y 'confianza'.
        """
        if not self.llm:
            # Fallback si no hay LLM disponible
            message_lower = message.lower()
            if any(word in message_lower for word in ["hola", "hi", "hello", "buenos"]):
                return {"intencion": "saludo", "confianza": 0.9}
            elif any(word in message_lower for word in ["informacion", "info", "details", "detalles"]):
                return {"intencion": "solicitar_informacion", "confianza": 0.85}
            elif any(word in message_lower for word in ["aplicar", "apply", "interesado", "interested"]):
                return {"intencion": "aplicar", "confianza": 0.9}
            else:
                return {"intencion": "general", "confianza": 0.6}
        
        try:
            system_prompt = """Eres un asistente que analiza la intención de mensajes de candidatos.
            Clasifica la intención en una de estas categorías:
            - saludo: El candidato está saludando o iniciando conversación
            - solicitar_informacion: El candidato pide información sobre la compañía u oferta
            - aplicar: El candidato expresa interés en aplicar
            - responder_pregunta: El candidato está respondiendo a una pregunta del agente
            - general: Otras intenciones
            
            Responde SOLO con un JSON válido: {"intencion": "...", "confianza": 0.0-1.0}"""
            
            messages = [
                SystemMessage(content=system_prompt),
                *conversation_history[-3:],  # Últimos 3 mensajes para contexto
                HumanMessage(content=f"Analiza la intención de este mensaje: {message}")
            ]
            
            response = self.llm.invoke(messages)
            # Intentar parsear JSON de la respuesta
            content = response.content
            if "{" in content and "}" in content:
                import re
                json_match = re.search(r'\{[^}]+\}', content)
                if json_match:
                    result = json.loads(json_match.group())
                    return {"intencion": result.get("intencion", "general"), 
                           "confianza": float(result.get("confianza", 0.6))}
            
            return {"intencion": "general", "confianza": 0.6}
        except Exception as e:
            logger.error(f"Error analizando intención: {e}")
            return {"intencion": "general", "confianza": 0.5}
    
    def extract_candidate_info(self, message: str, conversation_history: List) -> Dict[str, any]:
        """
        Extrae información del candidato del mensaje y contexto.
        
        Args:
            message: Mensaje del candidato.
            conversation_history: Historial de conversación.
            
        Returns:
            Dict con información extraída del candidato.
        """
        # Implementación simplificada - en producción usaría NER o prompting estructurado
        info = {}
        
        # Detectar nombre (simplificado)
        if not info.get("nombre"):
            # Buscar patrones como "Soy [nombre]" o "Mi nombre es [nombre]"
            import re
            patterns = [
                r"(?:soy|mi nombre es|me llamo|i'm|my name is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
                r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
            ]
            for pattern in patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    info["nombre"] = match.group(1).strip()
                    break
        
        # Detectar rol actual
        roles = ["software engineer", "developer", "data scientist", "ingeniero", "desarrollador"]
        message_lower = message.lower()
        for role in roles:
            if role in message_lower:
                info["rol_actual"] = role
                break
        
        return info
    
    def generate_response(
        self,
        intention: str,
        state: ConversationState,
        company_info: Optional[CompanyInfo] = None,
        job_offer: Optional[JobOffer] = None
    ) -> str:
        """
        Genera una respuesta del agente basada en la intención y el estado.
        
        Args:
            intention: Intención detectada del candidato.
            state: Estado actual de la conversación.
            company_info: Información de la compañía.
            job_offer: Información de la oferta.
            
        Returns:
            Respuesta generada por el agente.
        """
        if not self.llm:
            # Respuestas de fallback
            if intention == "saludo":
                return "¡Hola! Soy el Agente Recruiter de IA de TechInnovate Solutions. Estoy aquí para ayudarte a conocer más sobre nuestra compañía y las oportunidades disponibles. ¿En qué puedo ayudarte hoy?"
            elif intention == "solicitar_informacion":
                if company_info:
                    return f"Hola! {company_info.nombre} es una compañía enfocada en {company_info.mision}. Nuestra cultura se basa en {company_info.cultura}. ¿Te gustaría saber más sobre alguna oferta específica?"
                return "Con gusto te proporciono información. ¿Sobre qué te gustaría saber más: la compañía o alguna oferta específica?"
            elif intention == "aplicar":
                return "¡Excelente! Me encantaría conocerte mejor. ¿Podrías contarme un poco sobre tu experiencia y el rol que te interesa?"
            else:
                return "Entiendo. ¿En qué más puedo ayudarte?"
        
        try:
            system_prompt = f"""Eres un agente recruiter profesional y amigable de {company_info.nombre if company_info else 'TechInnovate Solutions'}.
            Tu objetivo es:
            1. Mantener conversaciones naturales y empáticas con candidatos
            2. Proporcionar información precisa sobre la compañía y ofertas
            3. Evaluar la idoneidad de los candidatos mediante preguntas estratégicas
            4. Ser profesional pero accesible
            
            Información de la compañía:
            {json.dumps(company_info.dict() if company_info else {}, indent=2, ensure_ascii=False)}
            
            Información de la oferta:
            {json.dumps(job_offer.dict() if job_offer else {}, indent=2, ensure_ascii=False)}
            
            Responde de manera natural, en español, y adapta tu tono según la intención del candidato."""
            
            messages = [
                SystemMessage(content=system_prompt),
                *state.get("mensajes_conversacion", [])[-5:],
                HumanMessage(content=f"Intención detectada: {intention}. Mensaje del candidato: {state.get('mensaje_entrante', '')}")
            ]
            
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            return "Gracias por tu mensaje. ¿En qué más puedo ayudarte?"
    
    def evaluate_killer_question_response(
        self,
        question: KillerQuestion,
        response: str,
        job_offer: JobOffer
    ) -> Dict[str, any]:
        """
        Evalúa la respuesta del candidato a una killer question.
        
        Args:
            question: La killer question realizada.
            response: Respuesta del candidato.
            job_offer: Información de la oferta para contexto.
            
        Returns:
            Dict con evaluación y puntuación.
        """
        if not self.llm:
            # Evaluación simplificada basada en palabras clave
            response_lower = response.lower()
            positive_indicators = ["sí", "yes", "tengo", "i have", "experiencia", "experience"]
            score = sum(1 for word in positive_indicators if word in response_lower) / len(positive_indicators)
            return {
                "evaluacion": "positiva" if score > 0.5 else "neutra",
                "puntuacion": score
            }
        
        try:
            system_prompt = f"""Eres un evaluador de respuestas de candidatos.
            Evalúa la respuesta del candidato a esta pregunta crítica:
            "{question.pregunta}"
            
            Contexto de la oferta:
            {json.dumps(job_offer.dict(), indent=2, ensure_ascii=False)}
            
            Responde con un JSON: {{"evaluacion": "positiva/neutra/negativa", "puntuacion": 0.0-1.0, "razon": "breve explicación"}}"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Respuesta del candidato: {response}")
            ]
            
            response_llm = self.llm.invoke(messages)
            content = response_llm.content
            
            # Parsear JSON de la respuesta
            import re
            json_match = re.search(r'\{[^}]+\}', content)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "evaluacion": result.get("evaluacion", "neutra"),
                    "puntuacion": float(result.get("puntuacion", 0.5)),
                    "razon": result.get("razon", "")
                }
            
            return {"evaluacion": "neutra", "puntuacion": 0.5, "razon": "No se pudo evaluar"}
        except Exception as e:
            logger.error(f"Error evaluando respuesta: {e}")
            return {"evaluacion": "neutra", "puntuacion": 0.5, "razon": "Error en evaluación"}


# ============================================================================
# 3. DECLARACIÓN DE NODOS (Funciones de Python)
# ============================================================================


def recepcion_mensaje(state: ConversationState) -> ConversationState:
    """
    Nodo inicial: Recibe y procesa el mensaje entrante.
    
    Args:
        state: Estado actual de la conversación.
        
    Returns:
        Estado actualizado con el mensaje procesado.
    """
    logger.info(f"Recibiendo mensaje de {state.get('plataforma')}: {state.get('mensaje_entrante')}")
    
    # Agregar mensaje del humano al historial
    mensajes = state.get("mensajes_conversacion", [])
    mensajes.append(HumanMessage(content=state.get("mensaje_entrante", "")))
    
    state["mensajes_conversacion"] = mensajes
    state["estado_actual"] = "analisis_intencion"
    
    return state


def analisis_intencion(state: ConversationState, llm_service: LLMService) -> ConversationState:
    """
    Nodo de análisis: Determina la intención del mensaje del candidato.
    
    Args:
        state: Estado actual de la conversación.
        llm_service: Servicio LLM para análisis.
        
    Returns:
        Estado actualizado con la intención detectada.
    """
    logger.info("Analizando intención del mensaje")
    
    mensaje = state.get("mensaje_entrante", "")
    historial = state.get("mensajes_conversacion", [])
    
    try:
        analisis = llm_service.analyze_intention(mensaje, historial)
        state["intencion"] = analisis.get("intencion", "general")
        state["confianza_intencion"] = analisis.get("confianza", 0.5)
        
        logger.info(f"Intención detectada: {state['intencion']} (confianza: {state['confianza_intencion']})")
    except Exception as e:
        logger.error(f"Error en análisis de intención: {e}")
        state["intencion"] = "general"
        state["confianza_intencion"] = 0.5
    
    state["estado_actual"] = "obtencion_datos"
    return state


def obtencion_datos(state: ConversationState, data_service: DataService, llm_service: LLMService) -> ConversationState:
    """
    Nodo de obtención: Extrae información del candidato y carga datos de compañía/oferta.
    
    Args:
        state: Estado actual de la conversación.
        data_service: Servicio de datos para RAG.
        llm_service: Servicio LLM para extracción.
        
    Returns:
        Estado actualizado con datos obtenidos.
    """
    logger.info("Obteniendo datos del candidato y contexto")
    
    try:
        # Extraer información del candidato
        mensaje = state.get("mensaje_entrante", "")
        historial = state.get("mensajes_conversacion", [])
        candidato_info_actual = state.get("candidato_info", {})
        
        info_extraida = llm_service.extract_candidate_info(mensaje, historial)
        candidato_info_actual.update(info_extraida)
        state["candidato_info"] = candidato_info_actual
        
        # Cargar información de compañía (si no está cargada)
        if not state.get("company_info"):
            company_info = data_service.get_company_info()
            state["company_info"] = company_info.dict()
        
        # Determinar rol de interés y cargar oferta correspondiente
        # Simplificado: buscar keywords o usar rol por defecto
        rol_interes = "senior_software_engineer"  # Por defecto
        candidato_info_lower = json.dumps(candidato_info_actual).lower()
        if "data" in candidato_info_lower or "scientist" in candidato_info_lower:
            rol_interes = "data_scientist"
        
        if not state.get("job_offer"):
            job_offer = data_service.get_job_offer(rol_interes)
            if job_offer:
                state["job_offer"] = job_offer.dict()
        
        logger.info(f"Datos obtenidos - Candidato: {candidato_info_actual}, Rol: {rol_interes}")
    except Exception as e:
        logger.error(f"Error obteniendo datos: {e}")
    
    # Decidir siguiente nodo basado en intención
    intencion = state.get("intencion", "general")
    if intencion in ["aplicar", "responder_pregunta"] and state.get("job_offer"):
        state["estado_actual"] = "killer_questions"
    else:
        state["estado_actual"] = "respuestas_compañia"
    
    return state


def killer_questions(state: ConversationState, data_service: DataService, llm_service: LLMService) -> ConversationState:
    """
    Nodo de killer questions: Gestiona la secuencia de preguntas críticas.
    
    Args:
        state: Estado actual de la conversación.
        data_service: Servicio de datos para obtener preguntas.
        llm_service: Servicio LLM para evaluación.
        
    Returns:
        Estado actualizado con preguntas y respuestas.
    """
    logger.info("Procesando killer questions")
    
    try:
        killer_questions_list = state.get("killer_questions", [])
        pregunta_actual_indice = state.get("pregunta_actual_indice", 0)
        esperando_respuesta = state.get("esperando_respuesta_killer", False)
        
        # Si estamos esperando respuesta, evaluarla
        if esperando_respuesta and pregunta_actual_indice < len(killer_questions_list):
            pregunta_actual = KillerQuestion(**killer_questions_list[pregunta_actual_indice])
            respuesta_candidato = state.get("mensaje_entrante", "")
            
            job_offer_dict = state.get("job_offer", {})
            if job_offer_dict:
                job_offer = JobOffer(**job_offer_dict)
                evaluacion = llm_service.evaluate_killer_question_response(
                    pregunta_actual, respuesta_candidato, job_offer
                )
                
                killer_questions_list[pregunta_actual_indice]["respuesta_candidato"] = respuesta_candidato
                killer_questions_list[pregunta_actual_indice]["evaluacion"] = evaluacion.get("evaluacion")
                pregunta_actual_indice += 1
        
        # Si no hay preguntas inicializadas, cargarlas
        if not killer_questions_list:
            rol_interes = "senior_software_engineer"
            if state.get("job_offer", {}).get("titulo", "").lower().startswith("data"):
                rol_interes = "data_scientist"
            
            preguntas = data_service.get_killer_questions(rol_interes)
            killer_questions_list = [q.dict() for q in preguntas]
            state["killer_questions"] = killer_questions_list
            pregunta_actual_indice = 0
        
        # Si hay más preguntas, hacer la siguiente
        if pregunta_actual_indice < len(killer_questions_list):
            pregunta_actual = KillerQuestion(**killer_questions_list[pregunta_actual_indice])
            state["respuesta_agente"] = f"Perfecto. Tengo una pregunta importante para conocerte mejor:\n\n{pregunta_actual.pregunta}"
            state["pregunta_actual_indice"] = pregunta_actual_indice
            state["esperando_respuesta_killer"] = True
            state["estado_actual"] = "killer_questions"  # Permanecer en este nodo
        else:
            # Todas las preguntas completadas
            state["esperando_respuesta_killer"] = False
            state["estado_actual"] = "evaluacion_final"
        
        state["killer_questions"] = killer_questions_list
    except Exception as e:
        logger.error(f"Error en killer questions: {e}")
        state["estado_actual"] = "evaluacion_final"
    
    return state


def respuestas_compañia(state: ConversationState, llm_service: LLMService) -> ConversationState:
    """
    Nodo de respuestas: Genera respuestas informativas sobre la compañía/oferta.
    
    Args:
        state: Estado actual de la conversación.
        llm_service: Servicio LLM para generación.
        
    Returns:
        Estado actualizado con respuesta generada.
    """
    logger.info("Generando respuesta sobre compañía/oferta")
    
    try:
        company_info_dict = state.get("company_info")
        job_offer_dict = state.get("job_offer")
        
        company_info = CompanyInfo(**company_info_dict) if company_info_dict else None
        job_offer = JobOffer(**job_offer_dict) if job_offer_dict else None
        
        intencion = state.get("intencion", "general")
        respuesta = llm_service.generate_response(intencion, state, company_info, job_offer)
        
        state["respuesta_agente"] = respuesta
        
        # Si la intención es aplicar, pasar a killer questions
        if intencion == "aplicar" and job_offer:
            state["estado_actual"] = "killer_questions"
        else:
            state["estado_actual"] = "finalizar_chat"
    except Exception as e:
        logger.error(f"Error generando respuesta: {e}")
        state["respuesta_agente"] = "Gracias por tu interés. ¿Hay algo más en lo que pueda ayudarte?"
        state["estado_actual"] = "finalizar_chat"
    
    return state


def evaluacion_final(state: ConversationState, llm_service: LLMService) -> ConversationState:
    """
    Nodo de evaluación: Calcula la puntuación final de idoneidad del candidato.
    
    Args:
        state: Estado actual de la conversación.
        llm_service: Servicio LLM para evaluación final.
        
    Returns:
        Estado actualizado con evaluación final.
    """
    logger.info("Realizando evaluación final")
    
    try:
        killer_questions_list = state.get("killer_questions", [])
        razones = []
        puntuacion_total = 0.0
        peso_total = 0.0
        
        for q_dict in killer_questions_list:
            pregunta = KillerQuestion(**q_dict)
            evaluacion = pregunta.evaluacion
            peso = pregunta.peso
            
            if evaluacion == "positiva":
                puntuacion_pregunta = 1.0
            elif evaluacion == "neutra":
                puntuacion_pregunta = 0.5
            else:
                puntuacion_pregunta = 0.2
            
            puntuacion_total += puntuacion_pregunta * peso
            peso_total += peso
            
            razones.append(f"Pregunta sobre '{pregunta.pregunta[:50]}...': {evaluacion}")
        
        if peso_total > 0:
            puntuacion_normalizada = puntuacion_total / peso_total
        else:
            puntuacion_normalizada = 0.5
        
        # Determinar nivel de idoneidad
        if puntuacion_normalizada >= 0.7:
            puntuacion_idoneidad = SuitabilityScore.ALTA
        elif puntuacion_normalizada >= 0.4:
            puntuacion_idoneidad = SuitabilityScore.MEDIA
        else:
            puntuacion_idoneidad = SuitabilityScore.BAJA
        
        state["puntuacion_idoneidad"] = puntuacion_idoneidad.value
        state["razones_evaluacion"] = razones
        
        # Generar mensaje final
        mensaje_final = f"Gracias por compartir tus respuestas. "
        if puntuacion_idoneidad == SuitabilityScore.ALTA:
            mensaje_final += "Tu perfil parece muy alineado con lo que buscamos. Nuestro equipo de recursos humanos se pondrá en contacto contigo pronto."
        elif puntuacion_idoneidad == SuitabilityScore.MEDIA:
            mensaje_final += "Tu perfil tiene aspectos interesantes. Revisaremos tu información y te contactaremos si hay una buena fit."
        else:
            mensaje_final += "Agradecemos tu interés. Actualmente estamos buscando un perfil con características específicas, pero te deseamos éxito en tu búsqueda."
        
        state["respuesta_agente"] = mensaje_final
        logger.info(f"Evaluación completada: {puntuacion_idoneidad.value} (puntuación: {puntuacion_normalizada:.2f})")
    except Exception as e:
        logger.error(f"Error en evaluación final: {e}")
        state["puntuacion_idoneidad"] = SuitabilityScore.MEDIA.value
        state["razones_evaluacion"] = ["Error en evaluación automática"]
        state["respuesta_agente"] = "Gracias por tu tiempo. Revisaremos tu información."
    
    state["estado_actual"] = "finalizar_chat"
    return state


def finalizar_chat(state: ConversationState) -> ConversationState:
    """
    Nodo final: Finaliza la conversación y prepara la respuesta final.
    
    Args:
        state: Estado actual de la conversación.
        
    Returns:
        Estado finalizado.
    """
    logger.info("Finalizando conversación")
    
    # Agregar respuesta del agente al historial
    mensajes = state.get("mensajes_conversacion", [])
    respuesta = state.get("respuesta_agente", "Gracias por tu tiempo.")
    mensajes.append(AIMessage(content=respuesta))
    state["mensajes_conversacion"] = mensajes
    
    state["finalizado"] = True
    state["estado_actual"] = "finalizado"
    
    return state


# ============================================================================
# 4. CONSTRUCCIÓN DEL GRAFO (LangGraph StateGraph)
# ============================================================================


def create_recruiter_graph(
    data_service: DataService,
    llm_service: LLMService
) -> StateGraph:
    """
    Construye y retorna el grafo de LangGraph para el agente recruiter.
    
    Args:
        data_service: Servicio de datos para RAG.
        llm_service: Servicio LLM.
        
    Returns:
        StateGraph configurado y compilado.
    """
    # Crear el grafo
    workflow = StateGraph(ConversationState)
    
    # Agregar nodos
    workflow.add_node("recepcion_mensaje", recepcion_mensaje)
    workflow.add_node("analisis_intencion", lambda s: analisis_intencion(s, llm_service))
    workflow.add_node("obtencion_datos", lambda s: obtencion_datos(s, data_service, llm_service))
    workflow.add_node("killer_questions", lambda s: killer_questions(s, data_service, llm_service))
    workflow.add_node("respuestas_compañia", lambda s: respuestas_compañia(s, llm_service))
    workflow.add_node("evaluacion_final", lambda s: evaluacion_final(s, llm_service))
    workflow.add_node("finalizar_chat", finalizar_chat)
    
    # Definir flujo de entrada
    workflow.set_entry_point("recepcion_mensaje")
    
    # Definir transiciones
    workflow.add_edge("recepcion_mensaje", "analisis_intencion")
    workflow.add_edge("analisis_intencion", "obtencion_datos")
    
    # Flujo condicional desde obtencion_datos
    def route_after_data(state: ConversationState) -> str:
        """Rutea después de obtener datos basado en intención y estado."""
        estado_actual = state.get("estado_actual", "")
        if estado_actual == "killer_questions":
            return "killer_questions"
        else:
            return "respuestas_compañia"
    
    workflow.add_conditional_edges(
        "obtencion_datos",
        route_after_data,
        {
            "killer_questions": "killer_questions",
            "respuestas_compañia": "respuestas_compañia"
        }
    )
    
    # Flujo condicional desde killer_questions
    def route_after_killer(state: ConversationState) -> str:
        """Rutea después de killer questions."""
        estado_actual = state.get("estado_actual", "")
        if estado_actual == "killer_questions":
            return "killer_questions"  # Repetir si hay más preguntas
        elif estado_actual == "evaluacion_final":
            return "evaluacion_final"
        else:
            return "finalizar_chat"
    
    workflow.add_conditional_edges(
        "killer_questions",
        route_after_killer,
        {
            "killer_questions": "killer_questions",
            "evaluacion_final": "evaluacion_final",
            "finalizar_chat": "finalizar_chat"
        }
    )
    
    # Flujo condicional desde respuestas_compañia
    def route_after_responses(state: ConversationState) -> str:
        """Rutea después de respuestas."""
        estado_actual = state.get("estado_actual", "")
        if estado_actual == "killer_questions":
            return "killer_questions"
        else:
            return "finalizar_chat"
    
    workflow.add_conditional_edges(
        "respuestas_compañia",
        route_after_responses,
        {
            "killer_questions": "killer_questions",
            "finalizar_chat": "finalizar_chat"
        }
    )
    
    # Flujos finales
    workflow.add_edge("evaluacion_final", "finalizar_chat")
    workflow.add_edge("finalizar_chat", END)
    
    return workflow.compile()


# ============================================================================
# 5. API FASTAPI PARA CLOUD RUN
# ============================================================================


app = FastAPI(
    title="AIR - Agente Recruiter de IA",
    description="Microservicio de agente conversacional para reclutamiento",
    version="1.0.0"
)

# Inicializar servicios (singleton)
_data_service = DataService()
_llm_service = LLMService()
_recruiter_graph = create_recruiter_graph(_data_service, _llm_service)


class WebhookRequest(BaseModel):
    """Modelo para requests de webhook."""
    mensaje: str = Field(..., description="Mensaje del candidato")
    plataforma: Platform = Field(..., description="Plataforma de origen")
    candidato_id: str = Field(..., description="ID único del candidato")
    metadata: Optional[Dict] = Field(default=None, description="Metadata adicional")


@app.get("/")
async def root():
    """Endpoint de health check."""
    return {
        "status": "healthy",
        "service": "AIR - Agente Recruiter de IA",
        "version": "1.0.0"
    }


@app.post("/webhook/message")
async def receive_message(request: WebhookRequest):
    """
    Endpoint para recibir mensajes de plataformas externas (LinkedIn, Unipile).
    
    Args:
        request: Request con mensaje y metadata.
        
    Returns:
        Respuesta del agente y estado de la conversación.
    """
    try:
        # Crear estado inicial
        initial_state: ConversationState = {
            "mensaje_entrante": request.mensaje,
            "plataforma": request.plataforma,
            "candidato_id": request.candidato_id,
            "timestamp": datetime.utcnow().isoformat(),
            "candidato_info": {},
            "company_info": None,
            "job_offer": None,
            "intencion": None,
            "confianza_intencion": None,
            "killer_questions": [],
            "pregunta_actual_indice": 0,
            "esperando_respuesta_killer": False,
            "respuesta_agente": "",
            "mensajes_conversacion": [],
            "puntuacion_idoneidad": None,
            "razones_evaluacion": [],
            "estado_actual": "recepcion_mensaje",
            "finalizado": False
        }
        
        # Ejecutar el grafo
        final_state = _recruiter_graph.invoke(initial_state)
        
        # Preparar respuesta
        response_data = {
            "respuesta": final_state.get("respuesta_agente", ""),
            "estado": final_state.get("estado_actual", ""),
            "finalizado": final_state.get("finalizado", False),
            "candidato_info": final_state.get("candidato_info", {}),
            "puntuacion_idoneidad": final_state.get("puntuacion_idoneidad"),
            "timestamp": final_state.get("timestamp")
        }
        
        return JSONResponse(content=response_data, status_code=200)
    
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@app.get("/health")
async def health_check():
    """Endpoint de health check detallado."""
    return {
        "status": "healthy",
        "llm_available": _llm_service.llm is not None,
        "data_service_ready": True
    }


# ============================================================================
# 6. EJEMPLO DE EJECUCIÓN (Simulación de Conversación)
# ============================================================================


def simulate_conversation():
    """
    Simula una conversación completa de inicio a fin.
    
    Este ejemplo demuestra el flujo completo del agente desde el saludo
    inicial hasta la evaluación final del candidato.
    """
    print("\n" + "="*80)
    print("SIMULACIÓN DE CONVERSACIÓN - AGENTE RECRUITER IA")
    print("="*80 + "\n")
    
    # Inicializar servicios
    data_service = DataService()
    llm_service = LLMService()
    graph = create_recruiter_graph(data_service, llm_service)
    
    # Simular mensajes secuenciales
    mensajes_simulados = [
        {
            "mensaje": "Hola, estoy interesado en conocer más sobre las oportunidades",
            "plataforma": Platform.LINKEDIN,
            "candidato_id": "candidate_001"
        },
        {
            "mensaje": "Me interesa la posición de Senior Software Engineer",
            "plataforma": Platform.LINKEDIN,
            "candidato_id": "candidate_001"
        },
        {
            "mensaje": "Sí, tengo 7 años de experiencia con microservicios y he liderado varios proyectos",
            "plataforma": Platform.LINKEDIN,
            "candidato_id": "candidate_001"
        },
        {
            "mensaje": "He mentoreado a 3 desarrolladores junior y he participado en code reviews regulares",
            "plataforma": Platform.LINKEDIN,
            "candidato_id": "candidate_001"
        },
        {
            "mensaje": "Sí, trabajo con Docker, Kubernetes y teng experiencia en GCP y AWS",
            "plataforma": Platform.LINKEDIN,
            "candidato_id": "candidate_001"
        },
        {
            "mensaje": "Sí, estoy disponible para trabajar en horario PST y tengo experiencia con equipos distribuidos",
            "plataforma": Platform.LINKEDIN,
            "candidato_id": "candidate_001"
        }
    ]
    
    estado_actual: Optional[ConversationState] = None
    
    for i, msg_simulado in enumerate(mensajes_simulados, 1):
        print(f"\n--- Mensaje {i} ---")
        print(f"Candidato: {msg_simulado['mensaje']}\n")
        
        # Crear o actualizar estado
        if estado_actual is None:
            estado_actual = {
                "mensaje_entrante": msg_simulado["mensaje"],
                "plataforma": msg_simulado["plataforma"],
                "candidato_id": msg_simulado["candidato_id"],
                "timestamp": datetime.utcnow().isoformat(),
                "candidato_info": {},
                "company_info": None,
                "job_offer": None,
                "intencion": None,
                "confianza_intencion": None,
                "killer_questions": [],
                "pregunta_actual_indice": 0,
                "esperando_respuesta_killer": False,
                "respuesta_agente": "",
                "mensajes_conversacion": [],
                "puntuacion_idoneidad": None,
                "razones_evaluacion": [],
                "estado_actual": "recepcion_mensaje",
                "finalizado": False
            }
        else:
            estado_actual["mensaje_entrante"] = msg_simulado["mensaje"]
            estado_actual["finalizado"] = False
        
        # Ejecutar grafo
        estado_actual = graph.invoke(estado_actual)
        
        # Mostrar respuesta
        respuesta = estado_actual.get("respuesta_agente", "")
        print(f"Agente: {respuesta}")
        
        # Mostrar estado interno (debug)
        estado_nodo = estado_actual.get("estado_actual", "")
        intencion = estado_actual.get("intencion", "N/A")
        print(f"\n[Estado: {estado_nodo}, Intención: {intencion}]")
        
        if estado_actual.get("finalizado"):
            print("\n--- Conversación Finalizada ---")
            puntuacion = estado_actual.get("puntuacion_idoneidad", "N/A")
            print(f"Puntuación de Idoneidad: {puntuacion}")
            razones = estado_actual.get("razones_evaluacion", [])
            if razones:
                print("\nRazones de Evaluación:")
                for razon in razones:
                    print(f"  - {razon}")
            break
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    import sys
    
    # Si se ejecuta con argumento "simulate", ejecutar simulación
    if len(sys.argv) > 1 and sys.argv[1] == "simulate":
        simulate_conversation()
    else:
        # Ejecutar servidor FastAPI para Cloud Run
        port = int(os.getenv("PORT", 8080))
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
