"""
Ejemplo de uso del microservicio AIR mediante llamadas HTTP.

Este script demuestra cómo interactuar con el API del agente recruiter
usando requests HTTP.
"""

import requests
import json
import time

# URL base del servicio (ajustar según despliegue)
BASE_URL = "http://localhost:8080"


def test_health_check():
    """Prueba el endpoint de health check."""
    print("🔍 Verificando salud del servicio...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_conversation_flow():
    """Simula un flujo completo de conversación."""
    print("💬 Iniciando flujo de conversación...\n")
    
    mensajes = [
        {
            "mensaje": "Hola, estoy interesado en conocer más sobre las oportunidades",
            "plataforma": "linkedin",
            "candidato_id": "candidate_test_001"
        },
        {
            "mensaje": "Me interesa la posición de Senior Software Engineer",
            "plataforma": "linkedin",
            "candidato_id": "candidate_test_001"
        },
        {
            "mensaje": "Sí, tengo 7 años de experiencia con microservicios",
            "plataforma": "linkedin",
            "candidato_id": "candidate_test_001"
        }
    ]
    
    for i, msg in enumerate(mensajes, 1):
        print(f"--- Mensaje {i} ---")
        print(f"Candidato: {msg['mensaje']}\n")
        
        try:
            response = requests.post(
                f"{BASE_URL}/webhook/message",
                json=msg,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"Agente: {data.get('respuesta', 'Sin respuesta')}")
                print(f"Estado: {data.get('estado', 'N/A')}")
                print(f"Finalizado: {data.get('finalizado', False)}")
                
                if data.get('puntuacion_idoneidad'):
                    print(f"Puntuación: {data.get('puntuacion_idoneidad')}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
            
            print("\n" + "-"*60 + "\n")
            time.sleep(1)  # Pequeña pausa entre mensajes
            
        except requests.exceptions.ConnectionError:
            print("❌ Error: No se pudo conectar al servicio.")
            print("Asegúrate de que el servidor esté ejecutándose con: python main.py")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            break


if __name__ == "__main__":
    print("="*60)
    print("EJEMPLO DE USO - AIR Agente Recruiter")
    print("="*60)
    print()
    
    # Verificar salud del servicio
    try:
        test_health_check()
    except requests.exceptions.ConnectionError:
        print("⚠️  El servicio no está disponible.")
        print("Inicia el servidor con: python main.py")
        exit(1)
    
    # Ejecutar flujo de conversación
    test_conversation_flow()
    
    print("✅ Ejemplo completado")
