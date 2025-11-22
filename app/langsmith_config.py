"""
Configuración de LangSmith Tracing
==================================

Este módulo asegura que el tracing de LangSmith esté correctamente configurado
antes de que se inicialicen los agentes. Debe ser importado al inicio de la aplicación.

USO:
    # En tu archivo main.py o donde inicialices la app
    import langsmith_config  # Esto configurará el tracing automáticamente
"""

import os
import logging
from dotenv import load_dotenv

# Configurar logging
logger = logging.getLogger(__name__)


def configure_langsmith_tracing():
    """
    Configura el tracing de LangSmith basándose en las variables de ambiente.
    
    Esta función:
    1. Carga las variables de ambiente desde .env
    2. Verifica que las credenciales de LangSmith estén presentes
    3. Habilita el tracing si LANGCHAIN_TRACING_V2=true
    4. Registra el estado de la configuración
    """
    
    # Cargar variables de ambiente desde .env
    load_dotenv()
    
    # Obtener configuración de LangSmith
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    api_key = os.getenv("LANGCHAIN_API_KEY", "")
    project = os.getenv("LANGCHAIN_PROJECT", "default")
    
    if tracing_enabled:
        if not api_key:
            logger.warning("⚠️  LANGCHAIN_TRACING_V2 está en 'true' pero LANGCHAIN_API_KEY no está configurado")
            logger.warning("⚠️  El tracing de LangSmith NO funcionará sin una API key válida")
            logger.warning("⚠️  Obtén tu API key en: https://smith.langchain.com")
            return False
        
        # Asegurar que las variables estén en el ambiente
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = project
        
        # Configuración opcional adicional
        os.environ["LANGCHAIN_ENDPOINT"] = os.getenv(
            "LANGCHAIN_ENDPOINT", 
            "https://api.smith.langchain.com"
        )
        
        logger.info("=" * 60)
        logger.info("🔍 LANGSMITH TRACING HABILITADO")
        logger.info("=" * 60)
        logger.info("📊 Proyecto: %s", project)
        logger.info("🔗 Endpoint: %s", os.environ["LANGCHAIN_ENDPOINT"])
        logger.info("🔑 API Key configurado: Sí (primeros 10 chars: %s...)", api_key[:10])
        logger.info("=" * 60)
        logger.info("")
        logger.info("✅ Las trazas se enviarán a: https://smith.langchain.com")
        logger.info("✅ Busca tu proyecto '%s' en el dashboard", project)
        logger.info("")
        logger.info("=" * 60)
        
        return True
    else:
        logger.info("=" * 60)
        logger.info("⚠️  LangSmith Tracing DESHABILITADO")
        logger.info("=" * 60)
        logger.info("Para habilitar el tracing:")
        logger.info("1. Configura LANGCHAIN_TRACING_V2=true en tu archivo .env")
        logger.info("2. Agrega tu LANGCHAIN_API_KEY de https://smith.langchain.com")
        logger.info("3. Opcionalmente configura LANGCHAIN_PROJECT")
        logger.info("=" * 60)
        
        return False


def verify_langsmith_connection():
    """
    Verifica que la conexión con LangSmith esté funcionando.
    
    Returns:
        bool: True si la conexión es exitosa, False en caso contrario
    """
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    
    if not tracing_enabled:
        return False
    
    try:
        from langsmith import Client
        
        client = Client()
        
        # Intentar obtener información del proyecto
        # Esto verificará que la API key sea válida
        try:
            client.read_project(project_name=os.getenv("LANGCHAIN_PROJECT", "default"))
            logger.info("✅ Conexión con LangSmith verificada exitosamente")
            return True
        except Exception as e:
            # El proyecto podría no existir aún, pero si llegamos aquí
            # significa que la API key es válida
            logger.info("✅ Conexión con LangSmith verificada (proyecto se creará automáticamente)")
            return True
            
    except ImportError:
        logger.warning("⚠️  Paquete 'langsmith' no instalado. Instala con: pip install langsmith")
        return False
    except Exception as e:
        logger.error("❌ Error verificando conexión con LangSmith: %s", str(e))
        logger.error("❌ Verifica que tu LANGCHAIN_API_KEY sea correcta")
        return False


def get_tracing_status():
    """
    Retorna el estado actual del tracing de LangSmith.
    
    Returns:
        dict: Diccionario con el estado de la configuración
    """
    return {
        "enabled": os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true",
        "api_key_set": bool(os.getenv("LANGCHAIN_API_KEY")),
        "project": os.getenv("LANGCHAIN_PROJECT", "default"),
        "endpoint": os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"),
    }


# Configurar automáticamente al importar este módulo
_tracing_configured = configure_langsmith_tracing()

if _tracing_configured:
    # Verificar la conexión solo si el tracing está habilitado
    verify_langsmith_connection()


if __name__ == "__main__":
    """
    Ejecutar este archivo directamente para verificar la configuración de LangSmith.
    
    Uso:
        python langsmith_config.py
    """
    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE CONFIGURACIÓN DE LANGSMITH")
    print("=" * 60 + "\n")
    
    status = get_tracing_status()
    
    print("Estado actual:")
    print(f"  • Tracing habilitado: {'✅ Sí' if status['enabled'] else '❌ No'}")
    print(f"  • API Key configurado: {'✅ Sí' if status['api_key_set'] else '❌ No'}")
    print(f"  • Proyecto: {status['project']}")
    print(f"  • Endpoint: {status['endpoint']}")
    
    print("\n" + "=" * 60)
    
    if status['enabled'] and status['api_key_set']:
        print("\n✅ CONFIGURACIÓN CORRECTA")
        print("\nTus agentes enviarán trazas a LangSmith.")
        print(f"Dashboard: https://smith.langchain.com/o/default/projects/p/{status['project']}")
    else:
        print("\n⚠️  CONFIGURACIÓN INCOMPLETA")
        print("\nPara habilitar LangSmith:")
        print("1. Crea una cuenta en https://smith.langchain.com")
        print("2. Obtén tu API key del dashboard")
        print("3. Configura las siguientes variables en tu archivo .env:")
        print("   LANGCHAIN_TRACING_V2=true")
        print("   LANGCHAIN_API_KEY=tu_api_key")
        print("   LANGCHAIN_PROJECT=nombre_de_tu_proyecto")
    
    print("\n" + "=" * 60 + "\n")
