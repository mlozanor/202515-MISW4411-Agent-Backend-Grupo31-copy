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
import json
import random
from pathlib import Path
import sys
from typing import Optional

from langchain_core.messages import HumanMessage

CURRENT_DIR = Path(__file__).resolve().parent
PARENT_DIR = CURRENT_DIR.parent

if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))
if str(PARENT_DIR) not in sys.path:
    sys.path.append(str(PARENT_DIR))

try:
    from mcp_server.model import llm
except ModuleNotFoundError:
    from model import llm


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
PROMPTS_DIR = ROOT_DIR / "prompts"
METADATA_FILE = DOCS_DIR / "metadata.json"


def _load_metadata() -> dict:
    if not METADATA_FILE.exists():
        raise FileNotFoundError(
            f"metadata.json no encontrado en {METADATA_FILE}. "
            "Asegúrate de crear este archivo con los capítulos disponibles."
        )

    with METADATA_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("El formato de metadata.json debe ser un objeto JSON con capítulos como llaves.")

    return data


def _load_prompt(prompt_filename: str) -> str:
    prompt_path = PROMPTS_DIR / prompt_filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt requerido no encontrado: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def _get_chapter_entry(metadata: dict, chapter: str) -> dict:
    if chapter not in metadata:
        available = ", ".join(metadata.keys()) or "N/A"
        raise ValueError(f"El capítulo '{chapter}' no existe. Capítulos disponibles: {available}")
    entry = metadata[chapter]
    if "chapter_file_path" not in entry:
        raise ValueError(f"El capítulo '{chapter}' no tiene 'chapter_file_path' definido en metadata.json.")
    return entry


def _load_chapter_content(chapter_path: str) -> str:
    chapter_file = DOCS_DIR / chapter_path
    if not chapter_file.exists():
        raise FileNotFoundError(f"No se encontró el archivo del capítulo en {chapter_file}")
    return chapter_file.read_text(encoding="utf-8")


async def _run_llm(prompt_filename: str, chapter_name: str, chapter_content: str, topic: Optional[str] = None) -> str:
    system_prompt = _load_prompt(prompt_filename)
    instruction = system_prompt + "\n\n"
    instruction += f"Chapter: {chapter_name}\n"
    if topic:
        instruction += f"Topic: {topic}\n"
    instruction += "\nChapter Content:\n"
    instruction += chapter_content

    response = await llm.ainvoke([HumanMessage(content=instruction)])
    return response.content.strip()


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


# ===============================================================================
# STUDY AGENT TOOLS
# ===============================================================================


@mcp.tool()
async def list_chapters() -> str:
    """
    Lista todos los capítulos disponibles para estudiar Google Cloud.
    """
    try:
        metadata = _load_metadata()
    except Exception as e:
        logger.error("[STUDY MCP TOOL] Error listando capítulos: %s", e)
        return f"Error al listar capítulos: {e}"

    if not metadata:
        return "No hay capítulos registrados en metadata.json."

    response_lines = ["Capítulos disponibles:"]
    for idx, chapter in enumerate(metadata.keys(), start=1):
        response_lines.append(f"{idx}. {chapter}")

    return "\n".join(response_lines)


@mcp.tool()
async def chapter_topics(chapter: str) -> str:
    """
    Devuelve la lista de temas principales del capítulo especificado.
    """
    try:
        metadata = _load_metadata()
        entry = _get_chapter_entry(metadata, chapter)
    except Exception as e:
        logger.error("[STUDY MCP TOOL] Error obteniendo temas: %s", e)
        return str(e)

    topics = entry.get("topics") or []
    if not topics:
        return f"El capítulo '{chapter}' no tiene temas registrados en metadata.json."

    lines = [f"Temas principales del capítulo '{chapter}':"]
    for idx, topic in enumerate(topics, start=1):
        lines.append(f"{idx}. {topic}")
    return "\n".join(lines)


@mcp.tool()
async def chapter_summary(chapter: str) -> str:
    """
    Resume el capítulo seleccionado en un solo párrafo utilizando el LLM.
    """
    try:
        metadata = _load_metadata()
        entry = _get_chapter_entry(metadata, chapter)
        chapter_content = _load_chapter_content(entry["chapter_file_path"])
    except Exception as e:
        logger.error("[STUDY MCP TOOL] Error generando resumen: %s", e)
        return str(e)

    try:
        summary = await _run_llm("chapter_summary.txt", chapter, chapter_content)
        return summary
    except Exception as e:
        logger.error("[STUDY MCP TOOL] Error invocando LLM para resumen: %s", e)
        return f"Error generando el resumen: {e}"


@mcp.tool()
async def learn_something(chapter: str, topic: Optional[str] = None) -> str:
    """
    Explica uno de los temas principales del capítulo en un solo párrafo.
    """
    try:
        metadata = _load_metadata()
        entry = _get_chapter_entry(metadata, chapter)
        topics = entry.get("topics") or []
        chapter_content = _load_chapter_content(entry["chapter_file_path"])
    except Exception as e:
        logger.error("[STUDY MCP TOOL] Error preparando explicación: %s", e)
        return str(e)

    chosen_topic = topic
    if not chosen_topic:
        if not topics:
            return f"El capítulo '{chapter}' no tiene temas registrados para seleccionar."
        chosen_topic = random.choice(topics)
        logger.info(
            "[STUDY MCP TOOL] Seleccionando tema aleatorio '%s' para el capítulo '%s'",
            chosen_topic,
            chapter,
        )
    else:
        if chosen_topic not in topics:
            available = ", ".join(topics) or "N/A"
            return (
                f"El tema '{chosen_topic}' no está registrado para el capítulo '{chapter}'. "
                f"Temas disponibles: {available}"
            )

    try:
        explanation = await _run_llm("learn_topic.txt", chapter, chapter_content, chosen_topic)
        return explanation
    except Exception as e:
        logger.error("[STUDY MCP TOOL] Error invocando LLM para aprendizaje: %s", e)
        return f"Error generando la explicación: {e}"


# Ejecución del servidor MCP
if __name__ == "__main__":
    mcp.run(transport="stdio")