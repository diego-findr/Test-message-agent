# 🚀 Guía de Inicio Rápido - AI Recruiter Agent

Esta guía te permite empezar a usar el microservicio en **menos de 5 minutos**.

## Opción 1: Ejecución Local (Desarrollo)

### Paso 1: Instalar Dependencias

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 2: Configurar Variables de Entorno

```bash
# Copiar template de configuración
cp .env.example .env

# Editar .env y añadir tu API key de Google
# GOOGLE_API_KEY=tu_clave_aqui
```

### Paso 3: Ejecutar el Ejemplo

```bash
# Usando el script helper
./run_example.sh

# O directamente
python example_usage.py
```

### Paso 4: Ejecutar el Servidor

```bash
# Opción 1: Script directo
python main.py

# Opción 2: Con uvicorn (recomendado para desarrollo)
uvicorn main:app --reload --port 8080

# Opción 3: Usando Makefile
make run
```

El servidor estará disponible en: **http://localhost:8080**

### Paso 5: Probar el API

```bash
# Health check
curl http://localhost:8080/health

# Iniciar conversación
curl -X POST http://localhost:8080/api/conversation/start \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_id": "test_123",
    "platform": "linkedin",
    "job_id": "senior_python_dev",
    "candidate_name": "John Doe"
  }'

# Respuesta te dará un session_id, úsalo para enviar mensajes
curl -X POST http://localhost:8080/api/conversation/message \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "TU_SESSION_ID_AQUI",
    "message": "Hola, tengo 5 años de experiencia con Python"
  }'
```

---

## Opción 2: Ejecución con Docker

### Paso 1: Build de la Imagen

```bash
docker build -t ai-recruiter-agent .
```

### Paso 2: Ejecutar Contenedor

```bash
docker run -p 8080:8080 \
  -e GOOGLE_API_KEY=tu_clave_aqui \
  -e ENVIRONMENT=development \
  ai-recruiter-agent
```

### Paso 3: Probar

```bash
curl http://localhost:8080/health
```

---

## Opción 3: Despliegue en Google Cloud Run

### Requisitos Previos

- Google Cloud SDK instalado (`gcloud`)
- Cuenta de GCP con billing habilitado
- Proyecto GCP creado

### Paso 1: Configurar GCP

```bash
# Autenticarse
gcloud auth login

# Configurar proyecto
gcloud config set project TU_PROJECT_ID
```

### Paso 2: Desplegar

```bash
# Opción A: Script automático
./deploy.sh tu-project-id us-central1

# Opción B: Manual
gcloud builds submit --tag gcr.io/tu-project-id/ai-recruiter-agent
gcloud run deploy ai-recruiter-agent \
  --image gcr.io/tu-project-id/ai-recruiter-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=tu_clave
```

### Paso 3: Obtener URL

```bash
gcloud run services describe ai-recruiter-agent \
  --region us-central1 \
  --format 'value(status.url)'
```

---

## Testing

### Ejecutar Tests Unitarios

```bash
# Todos los tests
pytest test_microservice.py -v

# Con coverage
pytest test_microservice.py -v --cov=. --cov-report=html

# Tests específicos
pytest test_microservice.py::TestAPIEndpoints -v

# Usando Makefile
make test
make test-cov
```

### Ver Reporte de Coverage

```bash
# El reporte HTML se genera en htmlcov/
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## Ejemplos de Uso

### Python Client

```python
import requests

# Iniciar conversación
response = requests.post(
    "http://localhost:8080/api/conversation/start",
    json={
        "candidate_id": "linkedin_12345",
        "platform": "linkedin",
        "job_id": "senior_python_dev"
    }
)
session_id = response.json()["session_id"]

# Enviar mensaje
response = requests.post(
    "http://localhost:8080/api/conversation/message",
    json={
        "session_id": session_id,
        "message": "Tengo 6 años de experiencia con Python y FastAPI"
    }
)
print(response.json()["agent_response"])
```

### cURL Examples

Ver archivo `README.md` sección "API Endpoints" para más ejemplos.

---

## Comandos Útiles (Makefile)

```bash
make help          # Ver todos los comandos disponibles
make install       # Instalar dependencias
make test          # Ejecutar tests
make run           # Ejecutar servidor
make example       # Ejecutar ejemplo
make lint          # Ejecutar linter
make format        # Formatear código
make clean         # Limpiar archivos generados
make docker-build  # Build Docker image
make docker-run    # Ejecutar Docker container
```

---

## Troubleshooting

### Error: "GOOGLE_API_KEY not set"

**Solución**: Asegúrate de configurar la variable de entorno:

```bash
export GOOGLE_API_KEY=tu_clave_aqui
# O añadirla al archivo .env
```

### Error: "Module not found"

**Solución**: Instala las dependencias:

```bash
pip install -r requirements.txt
```

### Error: "Port 8080 already in use"

**Solución**: Cambia el puerto:

```bash
PORT=8081 python main.py
# O en .env: PORT=8081
```

### Tests Failing

**Solución**: Verifica que todas las dependencias de desarrollo estén instaladas:

```bash
pip install pytest pytest-asyncio pytest-cov
```

---

## Próximos Pasos

1. **Explora el código**:
   - Lee `ARCHITECTURE.md` para entender la arquitectura
   - Revisa `data_model.py` para ver los modelos de datos
   - Explora `graph.py` para entender el flujo de LangGraph

2. **Personaliza**:
   - Modifica `services.py` para añadir tus propias ofertas de trabajo
   - Ajusta las "killer questions" para tu caso de uso
   - Personaliza los prompts en `llm_chain.py`

3. **Integra**:
   - Conecta con tu sistema de ATS (Applicant Tracking System)
   - Integra con bases de datos reales
   - Añade webhooks para LinkedIn/otras plataformas

4. **Despliega**:
   - Configura CI/CD (GitHub Actions, Cloud Build)
   - Añade monitoring y alertas
   - Implementa autenticación y autorización

---

## Recursos Adicionales

- **Documentación Completa**: `README.md`
- **Arquitectura Detallada**: `ARCHITECTURE.md`
- **Ejemplo Completo**: `example_usage.py`
- **Tests**: `test_microservice.py`

---

**¿Preguntas o problemas?** Revisa la documentación o los comentarios en el código. Todo está diseñado para ser auto-explicativo siguiendo estándares Senior A++.

**¡Feliz coding! 🚀**
