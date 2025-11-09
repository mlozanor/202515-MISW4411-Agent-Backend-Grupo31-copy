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
        logging.StreamHandler(sys.stdout)
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
# SEMANA 6: Implementar el servidor MCP para RAG
# ===============================================================================

# ===============================================================================

# TODO: Implementar la herramienta "ask" aquí
#
# @mcp.tool()
# async def ask(query: str) -> str:
#     """
#     COMPLETAR: Agregar docstring describiendo la herramienta
#     
#     Args:
#         query (str): La pregunta del usuario
#     
#     Returns:
#         str: El contexto recuperado del RAG
#     """

#     
#     pass


if __name__ == "__main__":
    mcp.run(transport="stdio")