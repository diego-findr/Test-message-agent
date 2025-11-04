# 🔄 Flujo de Conversación del AI Recruiter Agent

Este documento visualiza el flujo completo de una conversación típica con el agente recruiter.

---

## 📊 Diagrama de Estados LangGraph

```
                           [START]
                              │
                              ▼
                    ┌──────────────────┐
                    │ recepcion_mensaje│
                    │   (Entry Point)  │
                    └──────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            conversation_ended?    message received
                    │                   │
                    ▼                   ▼
                  [END]       ┌──────────────────┐
                              │ analisis_intencion│
                              │ (Intent Classify) │
                              └──────────────────┘
                                      │
                        ┌─────────────┼─────────────┐
                        │             │             │
                   intent: end   intent: ask   intent: provide
                        │             │             │
                        ▼             ▼             ▼
                 ┌───────────┐  ┌───────────┐  ┌───────────┐
                 │evaluacion_│  │respuestas_│  │obtencion_ │
                 │  final    │  │ compania  │  │  datos    │
                 └───────────┘  └───────────┘  └───────────┘
                        │             │             │
                        │         ┌───┴─────────────┘
                        │         │
                        ▼         ▼
              Ready to evaluate?  More questions?
                        │             │
                        │             ▼
                        │    ┌──────────────────┐
                        │    │ killer_questions │
                        │    │  (Screening)     │
                        │    └──────────────────┘
                        │             │
                        │      ┌──────┴──────┐
                        │      │             │
                        │  All answered?  More to ask?
                        │      │             │
                        ◄──────┘             │
                        │                    │
                        ▼                    │
                 ┌───────────┐              │
                 │evaluacion_│              │
                 │  final    │◄─────────────┘
                 └───────────┘
                        │
                        ▼
                 ┌───────────┐
                 │finalizar_ │
                 │   chat    │
                 └───────────┘
                        │
                        ▼
                     [END]
```

---

## 💬 Ejemplo de Conversación Completa

### Paso 1: Inicio (Greeting)

```
[ESTADO: greeting]
[NODO: recepcion_mensaje]

🤖 AI Recruiter:
"Hi! I'm an AI Recruiter from Tech Innovators Inc. I'm reaching 
out about our Senior Python Developer position. Do you have a 
few minutes to chat about this opportunity?"

📊 Estado:
- conversation_stage: "greeting" → "information_gathering"
- messages: 1
```

---

### Paso 2: Engagement del Candidato

```
[ESTADO: information_gathering]
[NODO: recepcion_mensaje → analisis_intencion → obtencion_datos]

👤 Candidato:
"Hi! Yes, I'd be interested to learn more."

🔍 Análisis:
- Intent: "general_inquiry"
- Route: obtencion_datos

🤖 AI Recruiter:
"Great to hear! Could you tell me a bit about your background 
and experience with Python development?"

📊 Estado:
- intent: "general_inquiry"
- messages: 3
```

---

### Paso 3: Candidato Comparte Experiencia

```
[ESTADO: information_gathering]
[NODO: recepcion_mensaje → analisis_intencion → obtencion_datos]

👤 Candidato:
"I have 6 years of professional Python development experience. 
I've worked extensively with FastAPI and Django to build 
scalable microservices. I'm also experienced with Docker 
and Kubernetes."

🔍 Análisis:
- Intent: "provide_info"
- Extracted Info:
  * years_of_experience: 6
  * skills: ["Python", "FastAPI", "Django", "Docker", "Kubernetes"]

🤖 AI Recruiter:
"That's impressive experience! The microservices architecture 
expertise is exactly what we're looking for. Let me ask you 
a few specific questions about the role..."

📊 Estado:
- candidate.years_of_experience: 6
- candidate.skills: [5 items]
- messages: 5
- Next: killer_questions
```

---

### Paso 4: Killer Question #1 - Microservices

```
[ESTADO: killer_questions]
[NODO: recepcion_mensaje → analisis_intencion → killer_questions]

🤖 AI Recruiter:
"Have you designed and built microservices architectures before? 
Can you describe a project where you implemented this?"

👤 Candidato:
"Yes! In my last role, I designed and built a microservices 
architecture for an e-commerce platform. We used Docker containers, 
deployed on Kubernetes, with API Gateway for routing. The system 
handled over 10,000 requests per second and scaled horizontally."

🔍 Evaluación:
- Question ID: "microservices"
- Keywords Match: ["microservices", "docker", "kubernetes", "api", "scalable"]
- Match Ratio: 5/6 = 83%
- Score: 83% * 0.25 * 100 = 20.75 points

📊 Estado:
- killer_questions_asked: ["microservices"]
- killer_answers: {"microservices": "..."}
- messages: 7
```

---

### Paso 5: Killer Question #2 - Cloud

```
[ESTADO: killer_questions]

🤖 AI Recruiter:
"What's your experience with cloud platforms like GCP, AWS, 
or Azure? Which services have you worked with?"

👤 Candidato:
"I have extensive experience with both GCP and AWS. On GCP, 
I've worked with Cloud Run, GKE, and BigQuery. On AWS, I've 
used Lambda, ECS, and RDS. I've also set up CI/CD pipelines."

🔍 Evaluación:
- Question ID: "cloud_experience"
- Keywords Match: ["gcp", "aws", "cloud run", "kubernetes", "deployment"]
- Match Ratio: 5/7 = 71%
- Score: 71% * 0.25 * 100 = 17.75 points

📊 Estado:
- killer_questions_asked: ["microservices", "cloud_experience"]
- Total Score so far: 38.5 points
```

---

### Paso 6: Killer Question #3 - Availability

```
[ESTADO: killer_questions]

🤖 AI Recruiter:
"When would you be available to start if we move forward 
with an offer?"

👤 Candidato:
"I can start in 2 weeks after giving proper notice to my 
current employer."

🔍 Evaluación:
- Question ID: "availability"
- Keywords Match: ["2 weeks", "notice", "available"]
- Match Ratio: 3/5 = 60%
- Score: 60% * 0.2 * 100 = 12 points

📊 Estado:
- All killer questions answered: 3/3
- Total Accumulated Score: 50.25 points
- Ready for final evaluation
```

---

### Paso 7: Evaluación Final

```
[ESTADO: evaluation]
[NODO: evaluacion_final]

🧮 Cálculo Final:
- Total Score: 50.25
- Max Possible Score: 70 (sum of weights * 100)
- Overall Percentage: 50.25 / 70 * 100 = 71.8%

📊 Evaluación:
{
  "overall_score": 71.8,
  "suitability": "high",
  "killer_questions_answered": 3,
  "killer_questions_total": 3,
  "strengths": [
    "Strong answer to: microservices",
    "Strong answer to: cloud_experience"
  ],
  "concerns": [],
  "recommendation": "Strong candidate. Recommend advancing to 
                     technical interview."
}
```

---

### Paso 8: Cierre de Conversación

```
[ESTADO: closing]
[NODO: finalizar_chat]

🤖 AI Recruiter:
"Thank you so much for taking the time to chat with me today! 
Based on our conversation, I think you'd be a great fit for 
this role. Our team will review your profile and reach out 
within 2-3 business days to schedule the next interview. 
Looking forward to continuing the conversation!"

📊 Estado Final:
- conversation_ended: true
- conversation_stage: "closing"
- messages: 11
- evaluation: { overall_score: 71.8, suitability: "high" }

[END]
```

---

## 🔀 Rutas Alternativas

### Ruta 1: Candidato Pregunta Sobre la Empresa

```
👤 Candidato: "Can you tell me more about your company culture?"

🔍 Análisis:
- Intent: "ask_company"
- Route: respuestas_compania

🤖 AI Recruiter:
"We foster innovation, collaboration, and continuous learning. 
Our culture emphasizes work-life balance and professional growth. 
We have flexible remote work policy and offer generous benefits 
including unlimited PTO and annual learning budget of $3,000."

→ Vuelve a analisis_intencion para siguiente pregunta
```

### Ruta 2: Candidato Pregunta Sobre el Trabajo

```
👤 Candidato: "What would be my main responsibilities?"

🔍 Análisis:
- Intent: "ask_job"
- Route: respuestas_compania

🤖 AI Recruiter:
"You'll work on building scalable microservices and ML pipelines 
using modern Python frameworks. The role involves architecting 
cloud-native solutions, mentoring junior developers, and 
collaborating with cross-functional teams."

→ Vuelve a analisis_intencion
```

### Ruta 3: Candidato Termina Temprano

```
👤 Candidato: "Thank you, but I'm not interested at this time."

🔍 Análisis:
- Intent: "end_conversation"
- Route: evaluacion_final (si hay respuestas) o finalizar_chat

🤖 AI Recruiter:
"Thank you for your interest and for taking the time to speak 
with me today. We'll keep your information on file for future 
opportunities. Best of luck in your job search!"

→ [END]
```

---

## 📈 Métricas de Evaluación

### Sistema de Scoring

```
Score Calculation:
─────────────────
For each killer question:
  1. Extract keywords from answer
  2. Calculate match_ratio = matched_keywords / total_keywords
  3. question_score = match_ratio * weight * 100
  
Total Score = Σ(question_scores)
Max Score = Σ(weights * 100)

Overall Percentage = (Total Score / Max Score) * 100

Suitability Classification:
  - >= 70%: "high"    → Advance to technical interview
  - 40-69%: "medium"  → Phone screen recommended
  - < 40%:  "low"     → Not a strong match
```

### Ejemplo de Cálculo

```
Question 1 (weight: 0.3):
  - Match: 5/6 keywords
  - Score: (5/6) * 0.3 * 100 = 25 points

Question 2 (weight: 0.25):
  - Match: 4/7 keywords
  - Score: (4/7) * 0.25 * 100 = 14.3 points

Question 3 (weight: 0.25):
  - Match: 3/5 keywords
  - Score: (3/5) * 0.25 * 100 = 15 points

Question 4 (weight: 0.2):
  - Match: 2/4 keywords
  - Score: (2/4) * 0.2 * 100 = 10 points

Total: 64.3 / 100 points = 64.3%
Suitability: "medium"
```

---

## 🎯 Estados del Sistema

| Estado | Descripción | Duración Típica |
|--------|-------------|-----------------|
| **greeting** | Saludo inicial | 1 mensaje |
| **information_gathering** | Recopilación de datos | 2-4 mensajes |
| **killer_questions** | Preguntas de filtrado | 3-5 mensajes |
| **company_questions** | Respuestas sobre empresa/rol | Variable |
| **evaluation** | Scoring del candidato | Automático |
| **closing** | Cierre de conversación | 1 mensaje |

---

## 🔄 Flujo de Datos en el Grafo

```python
# Entrada en cada nodo
Input: AgentState
  ├─ session_id: str
  ├─ messages: List[ConversationMessage]
  ├─ last_message: str
  ├─ candidate: CandidateProfile
  ├─ conversation_stage: str
  └─ ...

# Procesamiento
[Node Logic]
  1. Analizar estado actual
  2. Ejecutar lógica específica
  3. Llamar a servicios (LLM, Data, Evaluation)
  4. Generar respuesta
  5. Actualizar estado

# Salida
Output: AgentState (modificado)
  ├─ agent_response: str (nuevo)
  ├─ conversation_stage: str (actualizado)
  ├─ messages: List (con nuevo mensaje)
  └─ ...

# Routing
[Conditional Edge]
  Evaluar estado → Determinar siguiente nodo
```

---

## 💡 Notas de Diseño

### Idempotencia
- Cada nodo puede ejecutarse múltiples veces sin efectos secundarios
- Estado es inmutable dentro de cada nodo
- Todas las modificaciones retornan nuevo estado

### Extensibilidad
- Nuevos nodos: Añadir función + registrar en grafo
- Nuevas intenciones: Actualizar `IntentClassificationService`
- Nuevas preguntas: Modificar `DataService.killer_questions`

### Resilencia
- Manejo de errores en cada nodo
- Fallback a respuestas genéricas si LLM falla
- Flag `needs_human_intervention` para escalación

---

**Última actualización**: 2024-11-04  
**Versión**: 1.0.0
