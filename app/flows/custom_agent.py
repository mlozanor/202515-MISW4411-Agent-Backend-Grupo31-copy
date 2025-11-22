"""
Workflow del Agente de Estudio de Google Cloud
==============================================

Este módulo define el flujo de ejecución del agente personalizado encargado
de guiar el estudio para la certificación de Google Cloud. El flujo se basa
en LangGraph y coordina herramientas MCP especializadas que permiten:

- Presentar capítulos disponibles.
- Mostrar los temas principales de cada capítulo.
- Generar resúmenes y explicaciones usando el LLM.
- Responder preguntas ad-hoc mediante el backend RAG existente.
- Detectar solicitudes fuera de alcance y guiarlas apropiadamente.

El flujo mantiene estado conversacional, permite cambiar de capítulo en cualquier
momento y prioriza respuestas concisas (un párrafo) según los requerimientos.
"""

from __future__ import annotations

from typing import Annotated, Sequence, TypedDict, Optional, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from pathlib import Path
from functools import lru_cache
import json
import logging
import re
import os

from core.errors import AgentError, ToolExecutionError


# ===============================================================================
# CONFIGURACIÓN DE LANGSMITH TRACING
# ===============================================================================

# Verificar y configurar las variables de ambiente para LangSmith
if os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    temp_logger = logging.getLogger(__name__)
    temp_logger.info("🔍 LangSmith tracing HABILITADO para Custom Agent")
    temp_logger.info("📊 Proyecto: %s", os.getenv("LANGCHAIN_PROJECT", "default"))
else:
    temp_logger = logging.getLogger(__name__)
    temp_logger.info("⚠️  LangSmith tracing DESHABILITADO")


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT_DIR / "prompts"
METADATA_FILE = ROOT_DIR / "docs" / "metadata.json"


class StudyAgentState(TypedDict, total=False):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    selected_chapter: Optional[str]
    stage: Optional[str]
    intent: Optional[str]
    pending_chapter: Optional[str]
    requested_topic: Optional[str]
    last_tool_result: Optional[str]


@lru_cache(maxsize=1)
def _load_metadata() -> dict:
    if not METADATA_FILE.exists():
        logger.warning("[CUSTOM AGENT] metadata.json no encontrado en %s", METADATA_FILE)
        return {}
    with METADATA_FILE.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            logger.error("[CUSTOM AGENT] Error parseando metadata.json: %s", exc)
            return {}
    if not isinstance(data, dict):
        logger.error("[CUSTOM AGENT] metadata.json debe contener un objeto JSON")
        return {}
    return data


def _load_prompt(name: str) -> str:
    prompt_path = PROMPTS_DIR / name
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt no encontrado en {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def _format_conversation(messages: Sequence[BaseMessage], limit: int = 6) -> str:
    recent = messages[-limit:]
    formatted: List[str] = []
    for msg in recent:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        formatted.append(f"{role.upper()}: {msg.content}")
    return "\n".join(formatted)


def _get_last_human_message(state: StudyAgentState) -> Optional[HumanMessage]:
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage):
            return msg
    return None


def _match_chapter_name(user_text: str) -> Optional[str]:
    if not user_text:
        return None
    metadata = _load_metadata()
    if not metadata:
        return None

    chapters = list(metadata.keys())
    lowered = user_text.lower()

    number_match = re.search(r"\b(\d+)\b", lowered)
    if number_match:
        idx = int(number_match.group(1)) - 1
        if 0 <= idx < len(chapters):
            return chapters[idx]

    for chapter in chapters:
        if chapter.lower() in lowered:
            return chapter
    return None


def _extract_topic(chapter: Optional[str], user_text: str) -> Optional[str]:
    if not chapter or not user_text:
        return None
    metadata = _load_metadata()
    entry = metadata.get(chapter, {})
    topics = entry.get("topics") or []
    lowered = user_text.lower()
    for topic in topics:
        if topic.lower() in lowered:
            return topic
    return None


def _parse_intent(raw_response: str) -> str:
    try:
        start = raw_response.index("{")
        end = raw_response.rindex("}") + 1
        data = json.loads(raw_response[start:end])
        intent = data.get("intent")
        if isinstance(intent, str):
            return intent
    except Exception as exc:
        logger.warning("[CUSTOM AGENT] No se pudo parsear intent: %s", exc)
    return "out_of_scope"


def _format_agent_error(exc: AgentError) -> str:
    if exc.detail:
        return f"{exc} Detalle: {exc.detail}"
    return str(exc)


def build_custom_agent(model, tools_by_name):
    """Construye el grafo del agente de estudio de Google Cloud."""

    logger.info("[CUSTOM AGENT] Construyendo agente de estudio...")
    logger.info("[CUSTOM AGENT] 🔍 Tracing: %s", "HABILITADO" if os.getenv("LANGCHAIN_TRACING_V2") == "true" else "DESHABILITADO")

    async def intro_node(state: StudyAgentState) -> StudyAgentState:
        list_tool = tools_by_name.get("list_chapters")
        if list_tool:
            try:
                chapters_text = await list_tool.ainvoke({})
            except AgentError as exc:
                logger.error("[INTRO NODE] Error obteniendo capítulos: %s", exc)
                chapters_text = _format_agent_error(exc)
            except Exception as exc:
                logger.error("[INTRO NODE] Error obteniendo capítulos: %s", exc)
                chapters_text = "No pude obtener la lista de capítulos en este momento."
        else:
            chapters_text = "No pude encontrar la herramienta para listar capítulos."

        content = (
            "¡Hola! Soy tu agente de estudio para la certificación de Google Cloud.\n\n"
            "Estos son los capítulos disponibles:\n"
            f"{chapters_text}\n\n"
            "Por favor, dime qué capítulo te gustaría estudiar."
        )

        return {
            **state,
            "stage": "awaiting_chapter",
            "intent": None,
            "pending_chapter": None,
            "messages": [AIMessage(content=content)],
        }

    async def classify_intent_node(state: StudyAgentState) -> StudyAgentState:
        last_human = _get_last_human_message(state)
        if last_human is None:
            return state

        try:
            prompt = _load_prompt("intention_classifier.txt")
        except FileNotFoundError as exc:
            logger.error("[CLASSIFIER NODE] %s", exc)
            return {**state, "intent": "out_of_scope"}

        conversation_text = _format_conversation(state.get("messages", []))
        classifier_input = (
            f"{prompt}\n\n"
            f"Conversation:\n{conversation_text}\n\n"
            f"Latest user message:\n{last_human.content}"
        )

        try:
            response = await model.ainvoke([HumanMessage(content=classifier_input)])
            raw_content = response.content if isinstance(response, AIMessage) else str(response)
        except Exception as exc:
            logger.error("[CLASSIFIER NODE] Error invocando modelo: %s", exc)
            return {**state, "intent": "out_of_scope"}

        intent = _parse_intent(raw_content)
        pending_chapter = _match_chapter_name(last_human.content)
        requested_topic = _extract_topic(state.get("selected_chapter"), last_human.content)

        return {
            **state,
            "intent": intent,
            "pending_chapter": pending_chapter,
            "requested_topic": requested_topic,
        }

    async def handle_chapter_selection(state: StudyAgentState) -> StudyAgentState:
        pending = state.get("pending_chapter")
        if pending:
            topics_tool = tools_by_name.get("list_topics")
            if topics_tool:
                try:
                    topics_text = await topics_tool.ainvoke({"chapter": pending})
                except AgentError as exc:
                    logger.error("[CHAPTER SELECTION] Error obteniendo temas: %s", exc)
                    topics_text = _format_agent_error(exc)
                except Exception as exc:
                    logger.error("[CHAPTER SELECTION] Error obteniendo temas: %s", exc)
                    topics_text = "No pude obtener los temas del capítulo."
            else:
                topics_text = "No pude encontrar la herramienta para listar temas."

            message = (
                f"¡Perfecto! Has seleccionado '{pending}'.\n\n"
                f"Estos son los temas principales:\n{topics_text}\n\n"
                "¿Te gustaría un resumen del capítulo, profundizar en algún tema específico "
                "o realizar una pregunta de Google Cloud?"
            )

            return {
                **state,
                "selected_chapter": pending,
                "pending_chapter": None,
                "stage": "awaiting_decision",
                "intent": None,
                "messages": [AIMessage(content=message)],
            }

        list_tool = tools_by_name.get("list_chapters")
        if list_tool:
            try:
                chapters_text = await list_tool.ainvoke({})
            except AgentError as exc:
                logger.error("[CHAPTER SELECTION] Error listando capítulos: %s", exc)
                chapters_text = _format_agent_error(exc)
            except Exception as exc:
                logger.error("[CHAPTER SELECTION] Error listando capítulos: %s", exc)
                chapters_text = "No pude obtener la lista de capítulos."
        else:
            chapters_text = "No pude encontrar la herramienta para listar capítulos."

        message = (
            "Por favor, elige un capítulo para comenzar:\n"
            f"{chapters_text}\n\n"
            "¿Cuál te gustaría estudiar?"
        )

        return {**state, "intent": None, "messages": [AIMessage(content=message)]}

    async def handle_change_chapter(state: StudyAgentState) -> StudyAgentState:
        new_state = {**state, "selected_chapter": None, "stage": "awaiting_chapter"}
        pending = state.get("pending_chapter")

        if pending:
            return await handle_chapter_selection({**new_state, "pending_chapter": pending})

        list_tool = tools_by_name.get("list_chapters")
        if list_tool:
            try:
                chapters_text = await list_tool.ainvoke({})
            except AgentError as exc:
                logger.error("[CHANGE NODE] Error listando capítulos: %s", exc)
                chapters_text = _format_agent_error(exc)
            except Exception as exc:
                logger.error("[CHANGE NODE] Error listando capítulos: %s", exc)
                chapters_text = "No pude obtener la lista de capítulos."
        else:
            chapters_text = "No pude encontrar la herramienta para listar capítulos."

        message = (
            "Claro, cambiemos de capítulo. Estos son los capítulos disponibles:\n"
            f"{chapters_text}\n\n"
            "¿Cuál te gustaría estudiar ahora?"
        )

        return {**new_state, "intent": None, "messages": [AIMessage(content=message)]}

    async def chapter_summary_node(state: StudyAgentState) -> StudyAgentState:
        chapter = state.get("selected_chapter")
        if not chapter:
            message = (
                "Primero selecciona un capítulo para poder generar un resumen. "
                "¿Qué capítulo te interesa?"
            )
            return {
                **state,
                "stage": "awaiting_chapter",
                "intent": None,
                "messages": [AIMessage(content=message)],
            }

        summary_tool = tools_by_name.get("chapter_summary")
        if not summary_tool:
            message = "La herramienta de resumen no está disponible en este momento."
            return {**state, "intent": None, "messages": [AIMessage(content=message)]}

        try:
            summary = await summary_tool.ainvoke({"chapter": chapter})
        except AgentError as exc:
            logger.error("[SUMMARY NODE] Error generando resumen: %s", exc)
            summary = _format_agent_error(exc)
        except Exception as exc:
            logger.error("[SUMMARY NODE] Error generando resumen: %s", exc)
            summary = "No pude generar el resumen debido a un error."

        message = (
            f"Aquí tienes un resumen de '{chapter}':\n\n"
            f"{summary}\n\n"
            "¿Quieres profundizar en algún tema, solicitar otra explicación o cambiar de capítulo?"
        )

        return {
            **state,
            "intent": None,
            "stage": "awaiting_decision",
            "last_tool_result": summary,
            "messages": [AIMessage(content=message)],
        }

    async def learn_topic_node(state: StudyAgentState) -> StudyAgentState:
        chapter = state.get("selected_chapter")
        if not chapter:
            message = (
                "Necesito que primero elijas un capítulo antes de explorar sus temas. "
                "¿Cuál capítulo deseas estudiar?"
            )
            return {
                **state,
                "stage": "awaiting_chapter",
                "intent": None,
                "messages": [AIMessage(content=message)],
            }

        learn_tool = tools_by_name.get("learn_something")
        if not learn_tool:
            message = "La herramienta para profundizar en temas no está disponible ahora mismo."
            return {**state, "intent": None, "messages": [AIMessage(content=message)]}

        topic = state.get("requested_topic")
        payload = {"chapter": chapter, "topic": topic}

        try:
            explanation = await learn_tool.ainvoke(payload)
        except AgentError as exc:
            logger.error("[LEARN NODE] Error generando explicación: %s", exc)
            explanation = _format_agent_error(exc)
        except Exception as exc:
            logger.error("[LEARN NODE] Error generando explicación: %s", exc)
            explanation = "No pude generar la explicación debido a un error."

        topic_label = topic or "un tema clave del capítulo"
        message = (
            f"Repasemos {topic_label} en '{chapter}':\n\n"
            f"{explanation}\n\n"
            "¿Quieres profundizar en otro tema, pedir un resumen o cambiar de capítulo?"
        )

        return {
            **state,
            "intent": None,
            "stage": "awaiting_decision",
            "last_tool_result": explanation,
            "messages": [AIMessage(content=message)],
        }

    async def rag_question_node(state: StudyAgentState) -> StudyAgentState:
        last_human = _get_last_human_message(state)
        question = last_human.content if last_human else ""

        ask_tool = tools_by_name.get("ask")
        if not ask_tool:
            answer = "La herramienta externa para preguntas de Google Cloud no está disponible ahora mismo."
        else:
            try:
                answer = await ask_tool.ainvoke({"query": question})
            except AgentError as exc:
                logger.error("[RAG NODE] Error consultando RAG: %s", exc)
                answer = _format_agent_error(exc)
            except Exception as exc:
                logger.error("[RAG NODE] Error consultando RAG: %s", exc)
                answer = "No pude conectar con la base de conocimientos en este momento."

        message = (
            f"Esto es lo que encontré sobre tu pregunta de Google Cloud:\n\n"
            f"{answer}\n\n"
            "¿Deseas continuar con el capítulo actual, cambiar a otro o realizar otra pregunta?"
        )

        return {**state, "intent": None, "messages": [AIMessage(content=message)]}

    async def out_of_scope_node(state: StudyAgentState) -> StudyAgentState:
        message = (
            "Puedo ayudarte exclusivamente con temas de aprendizaje sobre Google Cloud Platform. "
            "¿Hay algún capítulo o concepto de Google Cloud que quieras estudiar?"
        )
        return {**state, "intent": None, "messages": [AIMessage(content=message)]}

    def router(state: StudyAgentState) -> str:
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None

        if state.get("stage") is None:
            return "intro"

        if isinstance(last_message, AIMessage):
            return "end"

        if state.get("intent") is None:
            return "classify"

        intent = state["intent"]
        mapping = {
            "choose_chapter": "select_chapter",
            "change_chapter": "change_chapter",
            "request_summary": "summary",
            "request_learning": "learn",
            "ask_gcp_question": "rag",
            "out_of_scope": "out_of_scope",
        }
        return mapping.get(intent, "end")

    def passthrough(state: StudyAgentState) -> StudyAgentState:
        return state

    workflow = StateGraph(StudyAgentState)
    workflow.add_node("decide", passthrough)
    workflow.add_node("intro", intro_node)
    workflow.add_node("classify", classify_intent_node)
    workflow.add_node("select_chapter", handle_chapter_selection)
    workflow.add_node("change_chapter", handle_change_chapter)
    workflow.add_node("summary", chapter_summary_node)
    workflow.add_node("learn", learn_topic_node)
    workflow.add_node("rag", rag_question_node)
    workflow.add_node("out_of_scope", out_of_scope_node)

    workflow.set_entry_point("decide")

    workflow.add_conditional_edges(
        "decide",
        router,
        {
            "intro": "intro",
            "classify": "classify",
            "select_chapter": "select_chapter",
            "change_chapter": "change_chapter",
            "summary": "summary",
            "learn": "learn",
            "rag": "rag",
            "out_of_scope": "out_of_scope",
            "end": END,
        },
    )

    for node in [
        "intro",
        "classify",
        "select_chapter",
        "change_chapter",
        "summary",
        "learn",
        "rag",
        "out_of_scope",
    ]:
        workflow.add_edge(node, "decide")

    compiled_graph = workflow.compile()
    logger.info("[CUSTOM AGENT] ✅ Grafo de estudio compilado exitosamente")
    logger.info("[CUSTOM AGENT] 📊 Todas las invocaciones serán trazadas en LangSmith")
    return compiled_graph