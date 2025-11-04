# AIR - Microservicio de Agente Recruiter de IA

Microservicio desarrollado en Python utilizando LangGraph y LangChain para mantener conversaciones autónomas con candidatos a través de plataformas de mensajería (LinkedIn, Unipile), evaluar su idoneidad y proporcionar información sobre la compañía y ofertas de trabajo.

## 🚀 Características

- **Orquestación con LangGraph**: Flujo de estados gestionado mediante StateGraph
- **Integración Multi-plataforma**: Soporte para LinkedIn y Unipile (simulado)
- **RAG Simulado**: Sistema de recuperación de información sobre compañía y ofertas
- **Killer Questions**: Sistema de evaluación mediante preguntas críticas
- **Evaluación Automática**: Cálculo de puntuación de idoneidad (Baja/Media/Alta)
- **API REST**: Endpoints FastAPI listos para Cloud Run
- **Código de Calidad Senior A++**: Type hints, docstrings, manejo de errores robusto

## 📋 Requisitos

- Python 3.10+
- Google API Key (para Gemini) - Opcional, tiene fallback
- Docker (para despliegue en Cloud Run)

## 🛠️ Instalación Local

1. Clonar el repositorio
2. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno (opcional):
```bash
cp .env.example .env
# Editar .env y agregar GOOGLE_API_KEY
```

## 🏃 Ejecución

### Modo Servidor (API REST)
```bash
python main.py
```

El servidor se iniciará en `http://0.0.0.0:8080`

### Modo Simulación
```bash
python main.py simulate
```

Ejecuta una conversación simulada completa mostrando el flujo del agente.

## 📡 API Endpoints

### Health Check
```bash
GET /
GET /health
```

### Recibir Mensaje (Webhook)
```bash
POST /webhook/message
Content-Type: application/json

{
  "mensaje": "Hola, estoy interesado en aplicar",
  "plataforma": "linkedin",
  "candidato_id": "candidate_001",
  "metadata": {}
}
```

**Respuesta:**
```json
{
  "respuesta": "¡Hola! Soy el Agente Recruiter...",
  "estado": "killer_questions",
  "finalizado": false,
  "candidato_info": {...},
  "puntuacion_idoneidad": null,
  "timestamp": "2024-01-01T12:00:00"
}
```

## 🐳 Despliegue en Google Cloud Run

1. **Construir imagen Docker:**
```bash
docker build -t gcr.io/PROJECT_ID/air-recruiter .
```

2. **Subir a Google Container Registry:**
```bash
docker push gcr.io/PROJECT_ID/air-recruiter
```

3. **Desplegar en Cloud Run:**
```bash
gcloud run deploy air-recruiter \
  --image gcr.io/PROJECT_ID/air-recruiter \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=your-api-key
```

O usar el Cloud Console para configuración visual.

## 🏗️ Arquitectura

### Estados del Grafo (LangGraph)

1. **recepcion_mensaje**: Recibe y procesa mensaje entrante
2. **analisis_intencion**: Analiza la intención del candidato (LLM)
3. **obtencion_datos**: Extrae info del candidato y carga datos RAG
4. **killer_questions**: Gestiona secuencia de preguntas críticas
5. **respuestas_compañia**: Genera respuestas informativas
6. **evaluacion_final**: Calcula puntuación de idoneidad
7. **finalizar_chat**: Finaliza conversación

### Componentes Principales

- **ConversationState (TypedDict)**: Estado del grafo
- **DataService**: Servicio RAG simulado (compañía/ofertas)
- **LLMService**: Interfaz con Google Gemini
- **Nodos LangGraph**: Funciones que procesan cada estado
- **FastAPI App**: API REST para Cloud Run

## 📝 Especificaciones Técnicas

### Lenguaje y Frameworks
- Python 3.10+
- LangGraph (orquestación)
- LangChain (tools y LLM)
- Pydantic (validación de esquemas)
- FastAPI (API REST)
- Google Gemini (LLM)

### Estándares de Calidad
- ✅ Type Hinting exhaustivo
- ✅ Docstrings estilo Google
- ✅ Manejo de errores robusto
- ✅ Código modular y OOP
- ✅ Diseño con TypedDict/Pydantic

## 🧪 Pruebas

Ejecutar simulación de conversación:
```bash
python main.py simulate
```

Esto ejecuta un flujo completo desde saludo hasta evaluación final.

## 📚 Estructura del Código

El archivo `main.py` contiene toda la lógica organizada en secciones:

1. **Definición del Estado**: Modelos Pydantic y TypedDict
2. **Servicios**: DataService (RAG) y LLMService (Gemini)
3. **Nodos**: Funciones de procesamiento para cada estado
4. **Construcción del Grafo**: Configuración de LangGraph
5. **API FastAPI**: Endpoints para Cloud Run
6. **Simulación**: Ejemplo de ejecución completa

## 🔧 Configuración

### Variables de Entorno

- `GOOGLE_API_KEY`: API key de Google Gemini (opcional, tiene fallback)
- `PORT`: Puerto del servidor (default: 8080, Cloud Run lo configura)

### Datos Simulados

Los datos de compañía y ofertas están hardcodeados en `DataService`. En producción, reemplazar con conexión a base de datos real.

## 📄 Licencia

Este proyecto es un ejemplo de arquitectura de microservicio basada en agentes.

---

## 📖 Especificaciones Originales

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