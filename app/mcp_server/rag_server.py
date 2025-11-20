"""
Servidor MCP para el Agente RAG
================================

Este módulo implementa el servidor MCP que expone la herramienta para consultar
el sistema RAG externo. El agente RAG utilizará esta herramienta para recuperar
contexto relevante de la base de datos vectorial.

IMPLEMENTACIÓN SEMANA 6:
- Implementar la herramienta MCP "ask" que consulta el sistema RAG
- La herramienta debe conectarse a la API del RAG (desarrollado en semanas anteriores)
- Debe manejar errores de conexión y timeout
- Retornar el contexto recuperado como string
"""

from mcp.server.fastmcp import FastMCP
import logging
import httpx
import os
import sys


# Configurar logging con UTF-8
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
# Asegurar que el handler use UTF-8
for handler in logging.root.handlers:
    if hasattr(handler, 'stream') and hasattr(handler.stream, 'reconfigure'):
        try:
            handler.stream.reconfigure(encoding='utf-8')
        except:
            pass

logger = logging.getLogger(__name__)

mcp = FastMCP("rag-server")


# ===============================================================================
# SEMANA 6: Implementación del servidor MCP para RAG
# ===============================================================================

# Configuración del RAG externo
# Estos valores se pueden modificar según las necesidades del proyecto
RAG_BASE_URL = os.getenv("RAG_BASE_URL", "http://136.119.169.213:8000")
RAG_COLLECTION = "chapter2_google_cloud"  # Mantener sincronizado con el backend RAG
RAG_TOP_K = 5
RAG_FORCE_REBUILD = False
RAG_USE_RERANKING = False
RAG_USE_QUERY_REWRITING = False


@mcp.tool()
async def ask(query: str) -> str:
    """
    Consulta el sistema RAG externo para recuperar contexto relevante.
    
    Esta herramienta se conecta al backend RAG desarrollado en semanas anteriores
    y recupera documentos relevantes de la base de datos vectorial basándose en
    la pregunta del usuario.
    
    Args:
        query (str): La pregunta o consulta del usuario que se usará para 
                     buscar documentos relevantes en la base vectorial.
    
    Returns:
        str: El contexto recuperado del RAG formateado como texto. Incluye
             los fragmentos de documentos más relevantes encontrados en la
             base de datos vectorial.
    
    Raises:
        Exception: Si hay problemas de conexión con el RAG o el servicio no responde.
    """
    logger.info("[MCP RAG TOOL] Consultando RAG con query: %s", query)
    
    try:
        # Preparar el payload para la solicitud al RAG
        payload = {
            "question": query,
            "collection": RAG_COLLECTION,
            "top_k": RAG_TOP_K,
            "force_rebuild": RAG_FORCE_REBUILD,
            "use_reranking": RAG_USE_RERANKING,
            "use_query_rewriting": RAG_USE_QUERY_REWRITING
        }
        
        # Crear cliente HTTP asíncrono con timeout
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info("[MCP RAG TOOL] Conectando a %s/api/v1/ask", RAG_BASE_URL)
            
            # Realizar la solicitud POST al endpoint del RAG
            response = await client.post(
                f"{RAG_BASE_URL}/api/v1/ask",
                json=payload
            )
            
            # Verificar que la respuesta sea exitosa
            response.raise_for_status()
            
            # Parsear la respuesta JSON
            result = response.json()
            
            logger.info("[MCP RAG TOOL] RAG respondió exitosamente")
            
            # Extraer y formatear el contexto de los documentos recuperados
            if "results" in result and result["results"]:
                # Construir el contexto concatenando los documentos recuperados
                context_parts = []
                
                for i, doc in enumerate(result["results"], 1):
                    # Extraer el contenido del documento
                    content = doc.get("content", "")
                    
                    # Extraer metadatos si están disponibles
                    metadata = doc.get("metadata", {})
                    source = metadata.get("source", "unknown")
                    
                    # Formatear cada documento
                    context_parts.append(
                        f"[Documento {i} - Fuente: {source}]\n{content}"
                    )
                
                # Unir todos los documentos en un solo string
                full_context = "\n\n---\n\n".join(context_parts)
                
                logger.info("[MCP RAG TOOL] Contexto recuperado: %s caracteres", len(full_context))
                return full_context
            
            elif "answer" in result:
                # Si el RAG devuelve directamente una respuesta
                logger.info("[MCP RAG TOOL] RAG devolvió respuesta directa")
                return result["answer"]
            
            else:
                # Si no hay resultados
                logger.warning("[MCP RAG TOOL] No se encontraron resultados")
                return "No se encontró información relevante en la base de conocimientos."
                
    except httpx.TimeoutException:
        error_msg = f"Timeout al conectar con el RAG en {RAG_BASE_URL}"
        logger.error("[MCP RAG TOOL] %s", error_msg)
        raise Exception(error_msg)
    
    except httpx.HTTPStatusError as e:
        error_msg = f"Error HTTP {e.response.status_code} al consultar RAG: {e.response.text}"
        logger.error("[MCP RAG TOOL] %s", error_msg)
        raise Exception(error_msg)
    
    except Exception as e:
        error_msg = f"Error inesperado al consultar RAG: {str(e)}"
        logger.error("[MCP RAG TOOL] %s", error_msg)
        raise Exception(error_msg)


if __name__ == "__main__":
    mcp.run(transport="stdio")