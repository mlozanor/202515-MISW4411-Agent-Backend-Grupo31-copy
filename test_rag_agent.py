"""
Script de Pruebas - Agente RAG Semana 6
========================================

Este script permite probar el agente RAG de forma rápida y verificar
que todos los componentes están funcionando correctamente.

Uso:
    python test_rag_agent.py
"""

import asyncio
import httpx
import json
from datetime import datetime


# ============================================
# Configuración
# ============================================

BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/v1/ask"


# ============================================
# Preguntas de Prueba
# ============================================

TEST_QUESTIONS = [
    "¿Qué información tienes en tu base de conocimientos?",
    "¿Qué son las APIs REST?",
    "Explícame los métodos HTTP",
    "¿Qué es autenticación?",
    "¿Cómo funciona CORS?"
]


# ============================================
# Colores para terminal
# ============================================

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


# ============================================
# Funciones de Prueba
# ============================================

async def test_health():
    """Verificar que el servidor está corriendo"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}1. Verificando que el servidor está corriendo...{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/docs")
            
            if response.status_code == 200:
                print(f"{Colors.GREEN}✅ Servidor FastAPI está corriendo{Colors.RESET}")
                return True
            else:
                print(f"{Colors.RED}❌ Servidor respondió con código: {response.status_code}{Colors.RESET}")
                return False
                
    except Exception as e:
        print(f"{Colors.RED}❌ No se puede conectar al servidor: {str(e)}{Colors.RESET}")
        print(f"{Colors.YELLOW}💡 Asegúrate de ejecutar: docker-compose up{Colors.RESET}")
        return False


async def test_single_question(question: str, question_num: int):
    """Probar una pregunta individual"""
    print(f"\n{Colors.MAGENTA}{'─'*60}{Colors.RESET}")
    print(f"{Colors.BOLD}Pregunta {question_num}:{Colors.RESET} {question}")
    print(f"{Colors.MAGENTA}{'─'*60}{Colors.RESET}")
    
    try:
        payload = {"question": question}
        
        print(f"{Colors.CYAN}⏳ Enviando solicitud...{Colors.RESET}")
        start_time = datetime.now()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BASE_URL}{ENDPOINT}",
                json=payload
            )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "Sin respuesta")
            
            print(f"\n{Colors.GREEN}✅ Respuesta recibida ({duration:.2f}s):{Colors.RESET}")
            print(f"{Colors.BLUE}{'─'*60}{Colors.RESET}")
            print(f"{answer}")
            print(f"{Colors.BLUE}{'─'*60}{Colors.RESET}")
            
            # Mostrar metadata si está disponible
            if "metadata" in result:
                print(f"\n{Colors.YELLOW}📊 Metadata:{Colors.RESET}")
                print(json.dumps(result["metadata"], indent=2))
            
            return True
            
        else:
            print(f"{Colors.RED}❌ Error {response.status_code}: {response.text}{Colors.RESET}")
            return False
            
    except httpx.TimeoutException:
        print(f"{Colors.RED}❌ Timeout: La solicitud tardó más de 60 segundos{Colors.RESET}")
        print(f"{Colors.YELLOW}💡 Verifica que el RAG Backend esté respondiendo{Colors.RESET}")
        return False
        
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {str(e)}{Colors.RESET}")
        return False


async def test_all_questions():
    """Probar todas las preguntas de prueba"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}2. Probando agente con múltiples preguntas...{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    
    results = []
    
    for i, question in enumerate(TEST_QUESTIONS, 1):
        success = await test_single_question(question, i)
        results.append(success)
        
        # Pequeña pausa entre preguntas
        if i < len(TEST_QUESTIONS):
            await asyncio.sleep(1)
    
    # Resumen
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}Resumen de Pruebas{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    
    successful = sum(results)
    total = len(results)
    
    print(f"\n{Colors.BOLD}Total:{Colors.RESET} {total} preguntas")
    print(f"{Colors.GREEN}Exitosas:{Colors.RESET} {successful}")
    print(f"{Colors.RED}Fallidas:{Colors.RESET} {total - successful}")
    
    if successful == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ¡Todas las pruebas pasaron!{Colors.RESET}")
    else:
        print(f"\n{Colors.YELLOW}⚠️  Algunas pruebas fallaron. Revisa los logs.{Colors.RESET}")


async def test_custom_question():
    """Permitir al usuario hacer una pregunta personalizada"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}3. Prueba personalizada{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    
    print(f"\n{Colors.YELLOW}Escribe tu pregunta (o presiona Enter para saltar):{Colors.RESET}")
    question = input(f"{Colors.BLUE}> {Colors.RESET}")
    
    if question.strip():
        await test_single_question(question, "Custom")
    else:
        print(f"{Colors.YELLOW}Saltando prueba personalizada...{Colors.RESET}")


# ============================================
# Función Principal
# ============================================

async def main():
    """Ejecutar todas las pruebas"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     SCRIPT DE PRUEBAS - AGENTE RAG SEMANA 6             ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")
    
    # Test 1: Verificar servidor
    server_ok = await test_health()
    
    if not server_ok:
        print(f"\n{Colors.RED}❌ No se puede continuar sin el servidor corriendo{Colors.RESET}")
        return
    
    # Test 2: Preguntas automáticas
    await test_all_questions()
    
    # Test 3: Pregunta personalizada
    await test_custom_question()
    
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}Pruebas completadas{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Pruebas interrumpidas por el usuario{Colors.RESET}\n")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error fatal: {str(e)}{Colors.RESET}\n")