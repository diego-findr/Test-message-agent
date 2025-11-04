# Test-message-agent

Prompt

Microservicio de Agente Recruiter de IA (AIR)
Objetivo General
Desarrollar un Microservicio de Agente Recruiter de IA (AIR) en Python, utilizando LangGraph y desplegable en Google Cloud Run, que sea capaz de mantener conversaciones autónomas y dinámicas con candidatos a través de plataformas de mensajería (LinkedIn, Unipile), evaluar su idoneidad, y proporcionar información precisa sobre la compañía y la oferta de trabajo. El código debe adherirse a los estándares de un programador Senior A++ (Clean Code, modularidad, pruebas unitarias).
Especificaciones Funcionales Clave
• 1. Integración de Plataformas (Nodos de Entrada/Salida):
• El Agente debe recibir mensajes entrantes de LinkedIn y Unipile (simular la recepción a través de un webhook o un listener asíncrono).
• Debe ser capaz de enviar respuestas formateadas de vuelta a estas plataformas.
• 2. Ciclo de Conversación y Flujo de LangGraph:
• El flujo debe ser orquestado por LangGraph para manejar estados, transiciones y lógica condicional.
• Estados Mínimos Requeridos: recepcion_mensaje, analisis_intencion, obtencion_datos, killer_questions, respuestas_compañia, evaluacion_final, finalizar_chat.
• 3. Extracción de Información y Personalización (RAG):
• El Agente debe ser capaz de consultar una fuente de datos simulada (ej. un diccionario o un archivo JSON en el código, simulando una base de datos de la compañía/oferta) para obtener:
• Datos del Candidato (nombre, rol actual, experiencia).
• Información sobre la Compañía (misión, cultura, beneficios).
• Detalles de la Oferta de Trabajo (salario, ubicación, requisitos).
• 4. Evaluación y Filtro (Killer Questions):
• Implementar un nodo de lógica condicional que dispare una secuencia de "Killer Questions" predefinidas basadas en el rol.
• El Agente debe analizar las respuestas del candidato y asignar una puntuación de idoneidad (ej. Baja, Media, Alta).
Especificaciones Técnicas y de Calidad
• Lenguaje y Frameworks:
• Python 3.10+
• LangGraph (para la orquestación del state-machine).
• LangChain (para los tools y el uso del modelo de lenguaje).
• Pydantic (para la definición estricta de los esquemas de State y Data).
• Modelo de Lenguaje (LLM): Utilizar un placeholder para un modelo de la familia Gemini (ej. ChatGemini).
• Arquitectura:
• Microservicio Modular: Separación clara de responsabilidades (ej. módulos para llm_chain.py, graph.py, services.py, data_model.py).
• Google Cloud Run: La solución debe estar contenida en un main.py ejecutable y venir con un Dockerfile simple para el despliegue.
• Estándares de Calidad (Senior A++):
• Uso de Type Hinting exhaustivo.
• Inclusión de docstrings informativos (estilo Google o Numpy).
• Manejo de errores robusto (uso de try...except).
• Código idempotente y orientado a objetos (OOP) donde sea apropiado.
• Diseño del Graph State de LangGraph utilizando TypedDict o Pydantic.
Estructura de la Respuesta Esperada
El resultado debe ser un único archivo de código (main.py) con comentarios claros que expliquen:
1. La Definición del Estado del Agente (Pydantic).
2. La Declaración de Nodos (funciones de Python).
3. La Construcción del Grafo (LangGraph StateGraph).
4. El Ejemplo de Ejecución (simulando una conversación de inicio a fin).
Conclusión y Tono
El objetivo es un código que no solo funcione, sino que sea un ejemplo de arquitectura de microservicio basada en agentes que un equipo de ingenieros podría llevar a producción.