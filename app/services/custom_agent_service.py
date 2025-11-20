"""
Servicio del Agente Especializado
==================================

Este módulo gestiona el ciclo de vida del Agente Especializado (ReAct), incluyendo
la inicialización de la sesión MCP, carga de múltiples herramientas y ejecución
del agente para procesar tareas complejas de los usuarios.

IMPLEMENTACIÓN SEMANA 7:
- Completar el método ask_custom para invocar el agente ReAct
- Pasar la pregunta del usuario al agente compilado
- Extraer el último mensaje (respuesta final) del resultado
- Retornar el string de la respuesta final
"""

from langchain_core.messages import HumanMessage, AIMessage
from flows.custom_agent import build_custom_agent
from mcp.client.stdio import stdio_client
from mcp_server.tools import load_tools
from mcp_server.model import llm
from core.errors import (
    AgentError,
    ConfigurationError,
    ConversationStateError,
    ExternalServiceError,
    ToolExecutionError,
)
from mcp import ClientSession
import asyncio
import logging
from typing import Optional, Dict, Any


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CustomAgentService:


    def __init__(self):
        self.custom_server_parameters = None
        self.rag_server_parameters = None
        self._lock = asyncio.Lock()
        self._custom_stdio_ctx = None
        self._custom_session = None
        self._rag_stdio_ctx = None
        self._rag_session = None
        self.agent = None
        self._tools_by_name: Dict[str, Any] = {}
        self._conversation_state: Optional[dict] = None

    @staticmethod
    def _format_agent_error(error: AgentError) -> str:
        message = str(error)
        if getattr(error, "detail", None):
            message = f"{message} Detalle: {error.detail}"
        return message

    
    def set_server_parameters(self, server_parameters):
        """
        Configura los parámetros del servidor MCP personalizado.
        """
        self.custom_server_parameters = server_parameters
    

    def set_rag_server_parameters(self, server_parameters):
        """
        Configura los parámetros del servidor MCP del agente RAG.
        """
        self.rag_server_parameters = server_parameters
    

    async def initialize(self):
        """
        Inicializa la sesión MCP y construye el agente personalizado.
        """
        async with self._lock:
            if self.agent is not None:
                return

            if not self.custom_server_parameters:
                raise ConfigurationError(
                    "Custom MCP server parameters not set.",
                    detail="Call set_server_parameters() before initialize().",
                )

            if not self.rag_server_parameters:
                raise ConfigurationError(
                    "RAG MCP server parameters not set.",
                    detail="Call set_rag_server_parameters() before initialize().",
                )

            try:
                logger.info("[CUSTOM SERVICE] Starting custom stdio_client...")
                self._custom_stdio_ctx = stdio_client(self.custom_server_parameters)
                custom_read, custom_write = await self._custom_stdio_ctx.__aenter__()
                self._custom_session = await ClientSession(custom_read, custom_write).__aenter__()
                await self._custom_session.initialize()
                logger.info("[CUSTOM SERVICE] Custom MCP session initialized successfully")

                custom_tools, custom_tools_by_name = await load_tools(self._custom_session)
                logger.info("[CUSTOM SERVICE] Loaded %s custom tools", len(custom_tools))

                logger.info("[CUSTOM SERVICE] Starting RAG stdio_client for ask tool...")
                self._rag_stdio_ctx = stdio_client(self.rag_server_parameters)
                rag_read, rag_write = await self._rag_stdio_ctx.__aenter__()
                self._rag_session = await ClientSession(rag_read, rag_write).__aenter__()
                await self._rag_session.initialize()
                logger.info("[CUSTOM SERVICE] RAG MCP session initialized successfully")

                rag_tools, rag_tools_by_name = await load_tools(self._rag_session)
                logger.info("[CUSTOM SERVICE] Loaded %s RAG tools", len(rag_tools))
            except Exception as exc:
                raise ExternalServiceError(
                    "Failed to initialize MCP sessions.",
                    detail=str(exc),
                ) from exc

            if "ask" not in rag_tools_by_name:
                raise ConfigurationError(
                    "The RAG MCP server does not expose a tool named 'ask'.",
                    detail="Verify the MCP server configuration for RAG.",
                )

            combined_tools_by_name = {**custom_tools_by_name, **rag_tools_by_name}
            rag_only_tools = [
                tool for name, tool in rag_tools_by_name.items() if name not in custom_tools_by_name
            ]
            combined_tools = custom_tools + rag_only_tools

            self._tools_by_name = combined_tools_by_name
            try:
                self.agent = build_custom_agent(llm.bind_tools(combined_tools), combined_tools_by_name)
            except Exception as exc:
                raise AgentError(
                    "Failed to compile the custom study agent.",
                    detail=str(exc),
                ) from exc

            logger.info("[CUSTOM SERVICE] Custom Agent created successfully")
    

    # ===============================================================================
    # SEMANA 7: Implementar la ejecución del agente personalizado
    # ===============================================================================
    

    async def ask_custom(self, question):
        """
        Procesa una pregunta usando el agente personalizado ReAct.
        
        Args:
            question (str): La pregunta o tarea del usuario
        
        Returns:
            str: La respuesta generada por el agente
        """
        # Asegurarse de que el agente está inicializado
        if self.agent is None:
            await self.initialize()

        logger.info("[CUSTOM SERVICE] Processing question: %s", question)

        if self._conversation_state is None:
            self._conversation_state = {
                "messages": [],
                "selected_chapter": None,
                "intent": None,
                "stage": None,
                "pending_chapter": None,
                "requested_topic": None,
                "last_tool_result": None,
            }

        existing_messages = list(self._conversation_state.get("messages", []))
        existing_messages.append(HumanMessage(content=question))
        self._conversation_state["messages"] = existing_messages
        self._conversation_state["intent"] = None
        self._conversation_state["requested_topic"] = None

        try:
            final_state = await self.agent.ainvoke(self._conversation_state)
        except ToolExecutionError as exc:
            logger.error("[CUSTOM SERVICE] Study agent failed: %s", exc)
            error_message = self._format_agent_error(exc)
            self._conversation_state["messages"] = [
                *self._conversation_state.get("messages", []),
                AIMessage(content=error_message),
            ]
            return error_message
        except Exception as exc:
            logger.error("[CUSTOM SERVICE] Unexpected error executing agent: %s", exc)
            error = ToolExecutionError(
                "The study agent failed while processing the question.",
                detail=str(exc),
            )
            error_message = self._format_agent_error(error)
            self._conversation_state["messages"] = [
                *self._conversation_state.get("messages", []),
                AIMessage(content=error_message),
            ]
            return error_message

        self._conversation_state = final_state

        messages = final_state.get("messages")
        if not messages:
            raise ConversationStateError(
                "The final state does not contain messages.",
                detail="Verify that the LangGraph workflow appends assistant responses.",
            )

        for message in reversed(messages):
            if isinstance(message, AIMessage):
                return message.content

        raise ConversationStateError(
            "No assistant response was produced by the agent.",
            detail="The workflow ended without generating an AIMessage.",
        )
    

    async def shutdown(self):
        """
        Cierra la sesión MCP y limpia recursos.
        
        NOTA: Este método ya está implementado y NO necesita modificación.
        """
        async with self._lock:
            if self._custom_session:
                await self._custom_session.__aexit__(None, None, None)
                self._custom_session = None
            if self._custom_stdio_ctx:
                await self._custom_stdio_ctx.__aexit__(None, None, None)
                self._custom_stdio_ctx = None
            if self._rag_session:
                await self._rag_session.__aexit__(None, None, None)
                self._rag_session = None
            if self._rag_stdio_ctx:
                await self._rag_stdio_ctx.__aexit__(None, None, None)
                self._rag_stdio_ctx = None
            logger.debug("MCP sessions and stdio_clients shut down")


CUSTOM_AGENT_SERVICE = CustomAgentService()
