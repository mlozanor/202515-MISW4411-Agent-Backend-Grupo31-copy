"""
Servicio del Agente RAG
========================

Este módulo gestiona el ciclo de vida del Agente RAG, incluyendo la inicialización
de la sesión MCP, carga de herramientas y ejecución del agente para procesar
consultas de los usuarios.

IMPLEMENTACIÓN SEMANA 6:
- Completar el método ask_rag para invocar el agente
- Pasar la pregunta del usuario al agente compilado
- Extraer la respuesta del resultado
- Retornar el string de la respuesta final
"""

from langchain_core.messages import HumanMessage
from flows.rag_agent import build_rag_agent
from mcp.client.stdio import stdio_client
from mcp_server.tools import load_tools
from mcp_server.model import llm
from core.errors import (
    ConfigurationError,
    ExternalServiceError,
    ToolExecutionError,
    ConversationStateError,
    AgentError,
)
from mcp import ClientSession
import asyncio
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class RagAgentService:

    def __init__(self):
        self.server_parameters = None
        self._lock = asyncio.Lock()
        self._stdio_ctx = None
        self._session = None
        self.agent = None

    
    def set_server_parameters(self, server_parameters):
        self.server_parameters = server_parameters

    @staticmethod
    def _format_error(error: AgentError) -> str:
        message = str(error)
        if getattr(error, "detail", None):
            message = f"{message} Detalle: {error.detail}"
        return message
    

    async def initialize(self):
        """
        Inicializa la sesión MCP y construye el agente RAG.
        
        NOTA: Este método ya está implementado y NO necesita modificación.
        """
        async with self._lock:
            if self._session is not None and self.agent is not None:
                return

            if not self.server_parameters:
                raise ConfigurationError(
                    "MCP server parameters not set.",
                    detail="Call set_server_parameters() before initialize().",
                )

            try:
                logger.info("Starting stdio_client...")
                self._stdio_ctx = stdio_client(self.server_parameters)
                read, write = await self._stdio_ctx.__aenter__()
                self._session = await ClientSession(read, write).__aenter__()
                await self._session.initialize()
                logger.info("MCP session initialized successfully")

                tools, tools_by_name = await load_tools(self._session)
            except Exception as exc:
                raise ExternalServiceError(
                    "Failed to initialize RAG MCP session.",
                    detail=str(exc),
                ) from exc

            if "ask" not in tools_by_name:
                raise ConfigurationError(
                    "The MCP server does not have a tool called 'ask'.",
                    detail="Ensure the RAG MCP server exposes the ask tool.",
                )

            ask_tool = tools_by_name["ask"]

            try:
                self.agent = build_rag_agent(llm, ask_tool)
            except Exception as exc:
                raise ToolExecutionError(
                    "Failed to build the RAG agent.",
                    detail=str(exc),
                ) from exc

            logger.info("RAG Agent created successfully")
    

    # ===============================================================================
    # SEMANA 6: Implementación de la ejecución del agente RAG
    # ===============================================================================
    
    async def ask_rag(self, question: str) -> str:
        """
        Procesa una pregunta usando el agente RAG.
        
        Basado en los tutoriales de LangGraph, este método:
        1. Verifica que el agente esté inicializado
        2. Crea el estado inicial con la pregunta del usuario
        3. Invoca el agente compilado
        4. Extrae y retorna la respuesta generada
        
        Args:
            question (str): La pregunta del usuario
        
        Returns:
            str: La respuesta generada por el agente
        """
        # Asegurarse de que el agente está inicializado
        if self._session is None or self.agent is None:
            await self.initialize()
        
        logger.info("[RAG SERVICE] Processing question: %s", question)
        
        # ===============================================================================
        # Ejecución del agente RAG con LangGraph
        # -------------------------------------------------------------------------------
        # Basado en el tutorial, creamos el estado inicial y invocamos el agente
        # ===============================================================================
        
        try:
            initial_state = {
                "input": question,
                "messages": [HumanMessage(content=question)],
                "context": "",
            }

            logger.info("[RAG SERVICE] Estado inicial creado, invocando agente...")
            final_state = await self.agent.ainvoke(initial_state)
            logger.info("[RAG SERVICE] Agente ejecutado exitosamente")
        except ToolExecutionError as exc:
            logger.error("[RAG SERVICE] Tool execution error: %s", exc)
            return self._format_error(exc)
        except Exception as exc:
            logger.error("[RAG SERVICE] Unexpected error executing agent: %s", exc)
            error = ToolExecutionError(
                "The RAG agent failed while processing the question.",
                detail=str(exc),
            )
            return self._format_error(error)

        messages = final_state.get("messages")
        if messages:
            last_message = messages[-1]
            answer = last_message.content
            logger.info("[RAG SERVICE] Respuesta extraída: %s caracteres", len(answer))
            return answer

        raise ConversationStateError(
            "No response was produced by the RAG agent.",
            detail="The final LangGraph state does not contain assistant messages.",
        )
    

    async def shutdown(self):
        """
        Cierra la sesión MCP y limpia recursos.
        
        NOTA: Este método ya está implementado y NO necesita modificación.
        """
        async with self._lock:
            if self._session:
                await self._session.__aexit__(None, None, None)
                self._session = None
            if self._stdio_ctx:
                await self._stdio_ctx.__aexit__(None, None, None)
                self._stdio_ctx = None
            logger.debug("MCP session and stdio_client shut down")


RAG_AGENT_SERVICE = RagAgentService()