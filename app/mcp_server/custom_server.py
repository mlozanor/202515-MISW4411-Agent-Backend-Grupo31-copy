"""
Servidor MCP para el Agente Especializado
==========================================

Este módulo implementa el servidor MCP que expone múltiples herramientas
personalizadas para el Agente Especializado. Las herramientas permiten al agente
acceder a fuentes de datos externas y realizar tareas específicas del dominio.

IMPLEMENTACIÓN SEMANA 7:
- Implementar al menos 2-3 herramientas MCP personalizadas
- Cada herramienta debe tener un propósito claro y documentado
- Las herramientas deben ser relevantes para el caso de negocio
- Conectar con APIs externas, bases de datos o servicios externos

IMPORTANTE:
- Todas las funciones deben ser async
- Docstrings claros (el LLM los lee para decidir qué herramienta usar)
- Retornar siempre strings
- Manejar errores apropiadamente
"""

from mcp.server.fastmcp import FastMCP
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


mcp = FastMCP("custom-server")


# ===============================================================================
# SEMANA 7: Implementar el servidor MCP personalizado
# ===============================================================================
# Implementación de herramientas personalizadas
# ----------------------------------------------------------
# Agrega aquí las funciones que tu servidor expondrá como herramientas.
# Cada función decorada con @mcp.tool() se registrará automáticamente.
# EJEMPLOS DE HERRAMIENTAS:
#
# a) Búsqueda en Wikipedia:
#    - get_summary(term: str) -> str: Obtiene resumen de un artículo
#    - get_page_sections(term: str) -> str: Lista secciones de un artículo
#    - get_section_content(term: str, section: str) -> str: Obtiene contenido de sección
#
# b) APIs Externas:
#    - get_weather(city: str) -> str: Consulta clima en una ciudad
#    - get_news(topic: str) -> str: Busca noticias sobre un tema
#    - get_stock_price(symbol: str) -> str: Obtiene precio de acciones
#
# c) Cálculos/Utilidades:
#    - calculate(expression: str) -> str: Evalúa expresiones matemáticas
#    - convert_units(value: float, from_unit: str, to_unit: str) -> str
#    - translate_text(text: str, target_lang: str) -> str
#
# d) Bases de datos:
#    - search_database(query: str) -> str: Busca en base de datos
#    - get_user_info(user_id: str) -> str: Obtiene info de usuario
#
# LAS HERRAMIENTAS QUE VAN A IMPLEMENTAR DEBEN ESTAR RELACIONADOS CON EL CASO DE SU NEGOCIO.
#
# Ejemplo:
#
# @mcp.tool()
# async def greet(name: str) -> str:
#     '''
#     Devuelve un saludo personalizado.
#
#     Args:
#         name (str): Nombre de la persona a saludar.
#
#     Returns:
#         str: Mensaje de saludo.
#     '''
#     return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run(transport="stdio")
