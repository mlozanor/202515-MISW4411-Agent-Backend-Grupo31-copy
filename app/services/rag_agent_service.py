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
    

    async def initialize(self):
        """
        Inicializa la sesión MCP y construye el agente RAG.
        
        NOTA: Este método ya está implementado y NO necesita modificación.
        """
        async with self._lock:
            if self._session is None:
                if not self.server_parameters:
                    raise ValueError("MCP server parameters not set. Call set_server_parameters() first")
                
                logger.info("Starting stdio_client...")
                self._stdio_ctx = stdio_client(self.server_parameters)
                read, write = await self._stdio_ctx.__aenter__()
                self._session = await ClientSession(read, write).__aenter__()
                await self._session.initialize()
                logger.info("MCP session initialized successfully")

                # Cargar herramientas del MCP server
                tools, tools_by_name = await load_tools(self._session)
                
                # Verificar que existe la herramienta "ask"
                if "ask" not in tools_by_name.keys():
                    raise ValueError("The MCP server does not have a tool called 'ask'")
                
                ask_tool = tools_by_name["ask"]

                # Construir el agente RAG
                self.agent = build_rag_agent(llm, ask_tool)
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
        
        logger.info(f"[RAG SERVICE] Processing question: {question}")
        
        # ===============================================================================
        # Ejecución del agente RAG con LangGraph
        # -------------------------------------------------------------------------------
        # Basado en el tutorial, creamos el estado inicial y invocamos el agente
        # ===============================================================================
        
        try:
            # Crear el estado inicial para el agente
            # Similar a la función ask_rag_langgraph del tutorial
            initial_state = {
                "input": question,
                "messages": [HumanMessage(content=question)],
                "context": ""
            }
            
            logger.info("[RAG SERVICE] Estado inicial creado, invocando agente...")
            
            # Invocar el agente compilado
            # El agente ejecutará el flujo: ask_node → llm_node
            final_state = await self.agent.ainvoke(initial_state)
            
            logger.info("[RAG SERVICE] Agente ejecutado exitosamente")
            
            # Extraer la respuesta del estado final
            # La respuesta está en el último mensaje del estado
            if "messages" in final_state and final_state["messages"]:
                # Obtener el último mensaje (respuesta del asistente)
                last_message = final_state["messages"][-1]
                answer = last_message.content
                
                logger.info(f"[RAG SERVICE] Respuesta extraída: {len(answer)} caracteres")
                
                return answer
            
            else:
                # Si no hay mensajes en el estado final, algo salió mal
                logger.error("[RAG SERVICE] No se encontró respuesta en el estado final")
                return "Error: No se pudo generar una respuesta."
                
        except Exception as e:
            logger.error(f"[RAG SERVICE] Error al procesar pregunta: {str(e)}")
            raise
    

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