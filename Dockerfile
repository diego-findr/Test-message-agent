# Dockerfile para Microservicio AIR - Agente Recruiter de IA
# Optimizado para Google Cloud Run

FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY main.py .

# Exponer puerto (Cloud Run usa PORT env var)
EXPOSE 8080

# Variable de entorno para el puerto (Cloud Run la sobrescribe)
ENV PORT=8080

# Comando para ejecutar la aplicación
CMD ["python", "main.py"]
