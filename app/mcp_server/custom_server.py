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
import wikipediaapi
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


mcp = FastMCP("custom-server")


# ===============================================================================
# SEMANA 7: Implementación del servidor MCP personalizado con Wikipedia
# ===============================================================================
# 
# Se implementan 3 herramientas basadas en Wikipedia que permiten al agente
# consultar información enciclopédica de forma estructurada.
#
# Estas herramientas son relevantes para casos de uso donde se necesita
# información general, histórica, técnica o biográfica.
# ===============================================================================

# Inicializar cliente de Wikipedia
# Usar idioma español y definir un user agent según políticas de Wikipedia
wiki = wikipediaapi.Wikipedia(
    language='es',
    user_agent='misw4411-custom-agent/1.0'
)


@mcp.tool()
async def get_summary(term: str) -> str:
    """
    Obtiene el resumen introductorio de un artículo de Wikipedia.
    
    Esta herramienta es útil para obtener una visión general rápida de un tema,
    persona, lugar o concepto. Devuelve los primeros párrafos del artículo.
    
    Úsala cuando necesites:
    - Información general sobre un tema
    - Contexto básico sobre una persona o lugar
    - Una introducción a un concepto
    
    Args:
        term (str): Término o título del artículo a buscar en Wikipedia.
                    Ejemplo: "Python", "Gabriel García Márquez", "Bogotá"
    
    Returns:
        str: Resumen del artículo de Wikipedia.
             Si el artículo no existe, devuelve un mensaje indicándolo.
    
    Ejemplos de uso:
        - Para obtener info sobre un lenguaje: "Python (programming language)"
        - Para obtener info sobre una persona: "Gabriel García Márquez"
        - Para obtener info sobre un lugar: "Bogotá"
    """
    logger.info(f"[CUSTOM MCP TOOL] get_summary llamada con term: {term}")
    
    try:
        page = wiki.page(term)
        
        if not page.exists():
            logger.warning(f"[CUSTOM MCP TOOL] No se encontró página para: {term}")
            return f"No se encontró ninguna página de Wikipedia para el término '{term}'. Verifica la ortografía o intenta con un término más específico."
        
        summary = page.summary
        
        if not summary:
            logger.warning(f"[CUSTOM MCP TOOL] Página existe pero sin resumen: {term}")
            return f"Se encontró la página '{term}' pero no tiene resumen disponible."
        
        # Limitar el resumen a los primeros 1000 caracteres para no saturar el contexto
        if len(summary) > 1000:
            summary = summary[:1000] + "..."
        
        logger.info(f"[CUSTOM MCP TOOL] Resumen obtenido: {len(summary)} caracteres")
        return f"Resumen de '{term}':\n\n{summary}"
        
    except Exception as e:
        logger.error(f"[CUSTOM MCP TOOL] Error en get_summary: {str(e)}")
        return f"Error al obtener el resumen: {str(e)}"


@mcp.tool()
async def get_page_sections(term: str) -> str:
    """
    Lista las secciones principales de un artículo de Wikipedia.
    
    Esta herramienta permite explorar la estructura de un artículo de Wikipedia,
    mostrando todas las secciones y subsecciones disponibles. Es útil para
    saber qué aspectos específicos cubre el artículo.
    
    Úsala cuando necesites:
    - Ver qué temas específicos cubre un artículo
    - Explorar la estructura de información disponible
    - Decidir qué sección consultar después con get_section_content
    
    Args:
        term (str): Término o título del artículo a consultar en Wikipedia.
    
    Returns:
        str: Lista de títulos de las secciones del artículo.
             Si el artículo no existe o no tiene secciones, lo indica.
    
    Ejemplos de uso:
        - Para ver qué secciones tiene un artículo sobre una persona
        - Para explorar los temas cubiertos en un artículo técnico
        - Para decidir qué sección específica consultar después
    """
    logger.info(f"[CUSTOM MCP TOOL] get_page_sections llamada con term: {term}")
    
    try:
        page = wiki.page(term)
        
        if not page.exists():
            logger.warning(f"[CUSTOM MCP TOOL] No se encontró página para: {term}")
            return f"No se encontró ningún artículo de Wikipedia para '{term}'."
        
        sections = [s.title for s in page.sections]
        
        if not sections:
            logger.info(f"[CUSTOM MCP TOOL] Artículo sin secciones: {term}")
            return f"El artículo '{term}' no tiene secciones identificables o es muy corto."
        
        # Formatear las secciones de forma legible
        sections_text = f"Secciones del artículo '{term}':\n"
        for i, section in enumerate(sections, 1):
            sections_text += f"{i}. {section}\n"
        
        logger.info(f"[CUSTOM MCP TOOL] {len(sections)} secciones encontradas")
        return sections_text
        
    except Exception as e:
        logger.error(f"[CUSTOM MCP TOOL] Error en get_page_sections: {str(e)}")
        return f"Error al obtener las secciones: {str(e)}"


@mcp.tool()
async def get_section_content(term: str, section_title: str) -> str:
    """
    Extrae el contenido completo de una sección específica de un artículo de Wikipedia.
    
    Esta herramienta permite obtener información detallada sobre un aspecto particular
    de un tema. Primero usa get_page_sections() para ver qué secciones están disponibles,
    luego usa esta herramienta para obtener el contenido de la sección que te interesa.
    
    Úsala cuando necesites:
    - Información detallada sobre un aspecto específico
    - Profundizar en un tema después de leer el resumen
    - Obtener datos precisos de una sección particular
    
    Args:
        term (str): Título del artículo de Wikipedia.
        section_title (str): Título exacto de la sección cuyo contenido se desea extraer.
                             Debe coincidir con uno de los títulos listados por get_page_sections().
    
    Returns:
        str: Texto completo del contenido de la sección solicitada.
             Si el artículo o la sección no existen, lo indica.
    
    Ejemplos de uso:
        - Para obtener info sobre la biografía: term="Persona", section_title="Biografía"
        - Para obtener info técnica específica: term="Python", section_title="Características"
        - Para obtener contexto histórico: term="Ciudad", section_title="Historia"
    
    Nota: La búsqueda de la sección es case-insensitive y busca recursivamente
          en secciones anidadas.
    """
    logger.info(f"[CUSTOM MCP TOOL] get_section_content llamada con term: {term}, section: {section_title}")
    
    try:
        page = wiki.page(term)
        
        if not page.exists():
            logger.warning(f"[CUSTOM MCP TOOL] No se encontró página para: {term}")
            return f"No se encontró ningún artículo de Wikipedia para '{term}'."
        
        # Función recursiva para buscar la sección en la jerarquía
        def find_section(sections):
            for s in sections:
                if s.title.lower() == section_title.lower():
                    return s.text
                # Buscar recursivamente en subsecciones
                result = find_section(s.sections)
                if result:
                    return result
            return None
        
        content = find_section(page.sections)
        
        if not content:
            # Listar secciones disponibles para ayudar al usuario
            available_sections = [s.title for s in page.sections]
            logger.warning(f"[CUSTOM MCP TOOL] Sección no encontrada: {section_title}")
            return f"No se encontró la sección '{section_title}' en el artículo '{term}'.\n\nSecciones disponibles: {', '.join(available_sections)}"
        
        # Limitar el contenido si es muy largo
        if len(content) > 2000:
            content = content[:2000] + "..."
        
        logger.info(f"[CUSTOM MCP TOOL] Contenido de sección obtenido: {len(content)} caracteres")
        return f"Contenido de la sección '{section_title}' en '{term}':\n\n{content}"
        
    except Exception as e:
        logger.error(f"[CUSTOM MCP TOOL] Error en get_section_content: {str(e)}")
        return f"Error al obtener el contenido de la sección: {str(e)}"


# Ejecución del servidor MCP
if __name__ == "__main__":
    mcp.run(transport="stdio")