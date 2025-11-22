"""
Script de Prueba de LangSmith Tracing
======================================

Este script permite verificar que el tracing de LangSmith esté funcionando
correctamente antes de ejecutar tus agentes principales.

REQUISITOS:
- Archivo .env con LANGCHAIN_TRACING_V2=true
- API Key válida de LangSmith configurada
- Dependencias instaladas (langchain, langsmith)

USO:
    python test_langsmith_tracing.py
"""

import os
import sys
from datetime import datetime

# Importar configuración de LangSmith
try:
    import langsmith_config
except ImportError:
    print("❌ Error: No se pudo importar langsmith_config.py")
    print("   Asegúrate de que el archivo exista en el directorio actual")
    sys.exit(1)


def print_separator(char="=", length=70):
    """Imprime una línea separadora."""
    print(char * length)


def print_section(title):
    """Imprime un título de sección."""
    print("\n")
    print_separator()
    print(f"  {title}")
    print_separator()
    print()


def test_environment_variables():
    """Prueba 1: Verificar variables de ambiente."""
    print_section("PRUEBA 1: Variables de Ambiente")
    
    required_vars = {
        "LANGCHAIN_TRACING_V2": "Habilitar tracing",
        "LANGCHAIN_API_KEY": "API Key de LangSmith",
        "LANGCHAIN_PROJECT": "Nombre del proyecto"
    }
    
    all_ok = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Ocultar API key por seguridad
            if "KEY" in var and len(value) > 10:
                display_value = f"{value[:10]}...{value[-4:]}"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NO CONFIGURADO")
            print(f"   → {description}")
            all_ok = False
    
    if all_ok:
        print("\n✅ Todas las variables están configuradas correctamente")
    else:
        print("\n❌ Faltan variables de ambiente")
        print("   Configúralas en tu archivo .env")
    
    return all_ok


def test_langsmith_import():
    """Prueba 2: Verificar importación de langsmith."""
    print_section("PRUEBA 2: Dependencias de LangSmith")
    
    try:
        from langsmith import Client
        print("✅ Módulo 'langsmith' importado correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error importando 'langsmith': {e}")
        print("   Instala con: pip install langsmith")
        return False


def test_langchain_imports():
    """Prueba 3: Verificar importaciones de LangChain."""
    print_section("PRUEBA 3: Dependencias de LangChain")
    
    imports = [
        ("langchain_core.messages", "Mensajes"),
        ("langchain_core.prompts", "Prompts"),
        ("langgraph.graph", "LangGraph"),
    ]
    
    all_ok = True
    
    for module, description in imports:
        try:
            __import__(module)
            print(f"✅ {description} ({module})")
        except ImportError as e:
            print(f"❌ {description} ({module}): {e}")
            all_ok = False
    
    return all_ok


def test_langsmith_connection():
    """Prueba 4: Verificar conexión con LangSmith."""
    print_section("PRUEBA 4: Conexión con LangSmith")
    
    if os.getenv("LANGCHAIN_TRACING_V2", "").lower() != "true":
        print("⚠️  LANGCHAIN_TRACING_V2 no está en 'true'")
        print("   El tracing está deshabilitado")
        return False
    
    try:
        from langsmith import Client
        
        client = Client()
        project_name = os.getenv("LANGCHAIN_PROJECT", "default")
        
        print(f"🔍 Intentando conectar con proyecto: {project_name}")
        
        try:
            # Intentar obtener el proyecto
            project = client.read_project(project_name=project_name)
            print(f"✅ Proyecto encontrado: {project.name}")
            print(f"   ID: {project.id}")
            return True
        except Exception as e:
            # El proyecto podría no existir aún, pero si llegamos aquí
            # la API key es válida
            error_msg = str(e).lower()
            if "not found" in error_msg or "404" in error_msg:
                print(f"⚠️  Proyecto '{project_name}' no existe aún")
                print("   Se creará automáticamente en la primera ejecución")
                print("✅ Conexión con LangSmith verificada (API Key válida)")
                return True
            else:
                print(f"❌ Error conectando con LangSmith: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("\nPosibles causas:")
        print("  - API Key incorrecta")
        print("  - Problemas de red")
        print("  - Servicio de LangSmith no disponible")
        return False


def test_simple_trace():
    """Prueba 5: Enviar una traza de prueba simple."""
    print_section("PRUEBA 5: Traza de Prueba")
    
    if os.getenv("LANGCHAIN_TRACING_V2", "").lower() != "true":
        print("⚠️  Tracing deshabilitado, saltando prueba")
        return False
    
    try:
        from langchain_core.messages import HumanMessage
        from langchain_core.prompts import ChatPromptTemplate
        
        print("🔍 Creando traza de prueba...")
        
        # Crear un prompt simple
        prompt = ChatPromptTemplate.from_template("Di 'Hola' si me recibes: {input}")
        
        # Formatear el prompt (esto genera una traza)
        result = prompt.invoke({"input": "test"})
        
        print("✅ Traza de prueba generada exitosamente")
        print(f"   Timestamp: {datetime.now().isoformat()}")
        print(f"   Proyecto: {os.getenv('LANGCHAIN_PROJECT', 'default')}")
        print("\n📊 Verifica tu dashboard de LangSmith:")
        print(f"   https://smith.langchain.com/o/default/projects/p/{os.getenv('LANGCHAIN_PROJECT', 'default')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generando traza: {e}")
        return False


def run_all_tests():
    """Ejecuta todas las pruebas."""
    print("\n")
    print("=" * 70)
    print("  VERIFICACIÓN DE CONFIGURACIÓN DE LANGSMITH")
    print("=" * 70)
    print(f"\n📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Ejecutar todas las pruebas
    results.append(("Variables de Ambiente", test_environment_variables()))
    results.append(("Importación de LangSmith", test_langsmith_import()))
    results.append(("Importaciones de LangChain", test_langchain_imports()))
    results.append(("Conexión con LangSmith", test_langsmith_connection()))
    results.append(("Traza de Prueba", test_simple_trace()))
    
    # Resumen
    print_section("RESUMEN DE PRUEBAS")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status:12} - {test_name}")
    
    print()
    print_separator()
    print(f"  RESULTADO: {passed}/{total} pruebas pasaron")
    print_separator()
    
    if passed == total:
        print("\n🎉 ¡PERFECTO! Tu configuración de LangSmith está lista")
        print("\nPróximos pasos:")
        print("  1. Ejecuta tus agentes (RAG o Custom)")
        print("  2. Ve al dashboard de LangSmith para ver las trazas")
        print(f"  3. URL: https://smith.langchain.com")
        return 0
    else:
        print("\n⚠️  Hay problemas con tu configuración")
        print("\nRevisión recomendada:")
        print("  1. Verifica tu archivo .env")
        print("  2. Asegúrate de que la API Key sea correcta")
        print("  3. Instala dependencias faltantes")
        print("  4. Consulta LANGSMITH_SETUP.md para más ayuda")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
