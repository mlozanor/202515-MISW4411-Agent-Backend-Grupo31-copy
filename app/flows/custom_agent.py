"""
Workflow del Agente Especializado
==========================================

Este módulo define el flujo de ejecución del Agente Especializado utilizando
LangGraph. El agente implementa el patrón ReAct (Reasoning + Acting) que permite
tomar decisiones dinámicas sobre qué herramientas usar.

IMPLEMENTACIÓN SEMANA 7:
- Construir el workflow ReAct del agente especilizado
- Definir el estado del agente (solo necesita "messages")
- Crear nodo "llm" que razona y decide qué hacer
- Crear nodo "tools" que ejecuta herramientas solicitadas
- Crear función should_continue que decide si usar más herramientas
- Construir grafo con ciclo: llm ↔ tools

CARACTERÍSTICAS:
- Patrón ReAct: Reasoning (razonamiento) + Acting (acción)
- Decisiones dinámicas sobre qué herramientas usar
- Puede ejecutar múltiples herramientas en secuencia
- El LLM analiza resultados y decide siguientes pasos
"""

from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
import logging


logging.basicConfig(level = logging.INFO, format = "%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ===============================================================================
# SEMANA 7: Construir el agente ReAct con herramientas
# ===============================================================================
#
# DIFERENCIAS CON EL RAG AGENT:
# - RAG Agent: Flujo LINEAL (siempre ejecuta "ask")
# - Custom Agent: Flujo CÍCLICO (decide dinámicamente qué hacer)

def build_custom_agent(model, tools_by_name):
    """
    Construye un agente ReAct que puede usar múltiples herramientas.
    
    Args:
        model: El modelo LLM con herramientas ya vinculadas (bind_tools)
        tools_by_name: Diccionario mapeando nombres a herramientas MCP
    
    Returns:
        CompiledGraph: El grafo compilado listo para ejecutar
    """
    
    logger.info("[CUSTOM AGENT] Construyendo agente ReAct...")
    
    # ==========================================================
    # Construcción del agente personalizado con patrón ReAct
    # ----------------------------------------------------------
    # Este agente implementa el patrón ReAct (Reasoning + Acting)
    # que permite al modelo decidir dinámicamente qué herramientas
    # usar y cuándo terminar.
    # ==========================================================
    
    # Definición del estado del agente
    class CustomAgentState(TypedDict):
        """
        Estado del agente personalizado.
        Solo necesita mantener el historial de mensajes que incluye:
        - Mensajes del usuario (HumanMessage)
        - Respuestas del modelo (AIMessage)
        - Resultados de herramientas (ToolMessage)
        """
        messages: Annotated[Sequence[BaseMessage], add_messages]
    
    
    # NODO 1: LLM (Razonamiento)
    def call_model(state: CustomAgentState, config: RunnableConfig):
        """
        Nodo que invoca el modelo de lenguaje para razonar sobre qué hacer.
        
        El modelo puede:
        1. Responder directamente al usuario (si ya tiene la info)
        2. Solicitar usar una o más herramientas (si necesita info externa)
        """
        logger.info(f"[LLM NODE] Invocando modelo con {len(state['messages'])} mensajes en el historial")
        
        try:
            # Invocar el modelo con todo el historial
            response = model.invoke(state["messages"], config)
            
            # Log para debugging
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_names = [tc['name'] for tc in response.tool_calls]
                logger.info(f"[LLM NODE] Modelo solicitó herramientas: {tool_names}")
            else:
                content_preview = str(response.content)[:60].replace("\n", " ")
                logger.info(f"[LLM NODE] Modelo respondió directamente: {content_preview}...")
            
            return {"messages": [response]}
            
        except Exception as e:
            logger.error(f"[LLM NODE] Error al invocar el modelo: {str(e)}")
            raise
    
    
    # NODO 2: TOOLS (Ejecución de Herramientas)
    async def call_tools(state: CustomAgentState):
        """
        Nodo que ejecuta las herramientas solicitadas por el modelo.
        
        Por cada tool_call:
        - Busca la herramienta correspondiente por nombre
        - La invoca con los argumentos proporcionados por el modelo
        - Empaqueta el resultado en un ToolMessage
        """
        last_message = state["messages"][-1]
        tool_calls = last_message.tool_calls
        
        logger.info(f"[TOOLS NODE] Ejecutando {len(tool_calls)} herramienta(s)")
        
        tool_messages = []
        
        try:
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_call_id = tool_call["id"]
                
                logger.info(f"[TOOLS NODE] Invocando '{tool_name}' con args: {tool_args}")
                
                # Buscar y ejecutar la herramienta
                tool = tools_by_name[tool_name]
                result = await tool.ainvoke(tool_args)
                
                # Log del resultado (limitado para no saturar los logs)
                result_preview = str(result)[:100].replace("\n", " ")
                logger.info(f"[TOOLS NODE] Resultado de '{tool_name}': {result_preview}...")
                
                # Crear mensaje con el resultado
                tool_message = ToolMessage(
                    content=result,
                    name=tool_name,
                    tool_call_id=tool_call_id
                )
                
                tool_messages.append(tool_message)
            
            return {"messages": tool_messages}
            
        except KeyError as e:
            logger.error(f"[TOOLS NODE] Herramienta no encontrada: {str(e)}")
            error_message = ToolMessage(
                content=f"Error: La herramienta '{tool_name}' no está disponible",
                name=tool_name,
                tool_call_id=tool_call_id
            )
            return {"messages": [error_message]}
            
        except Exception as e:
            logger.error(f"[TOOLS NODE] Error ejecutando herramienta '{tool_name}': {str(e)}")
            error_message = ToolMessage(
                content=f"Error ejecutando herramienta: {str(e)}",
                name=tool_name,
                tool_call_id=tool_call_id
            )
            return {"messages": [error_message]}
    
    
    # FUNCIÓN DE DECISIÓN CONDICIONAL
    def should_continue(state: CustomAgentState) -> str:
        """
        Decide si el flujo debe continuar hacia herramientas o terminar.
        
        - Si tiene tool_calls → "continue" (ir al nodo de tools)
        - Si no tiene tool_calls → "end" (terminar, el modelo ya respondió)
        """
        last_message = state["messages"][-1]
        
        # Verificar si el modelo solicitó herramientas
        has_tool_calls = hasattr(last_message, 'tool_calls') and last_message.tool_calls
        
        decision = "continue" if has_tool_calls else "end"
        
        logger.info(f"[DECISION] Flujo: {decision} (tool_calls: {has_tool_calls})")
        
        return decision
    
    
    # CONSTRUCCIÓN DEL GRAFO
    logger.info("[CUSTOM AGENT] Construyendo grafo de estado...")
    
    # Crear el grafo con el estado definido
    workflow = StateGraph(CustomAgentState)
    
    # Agregar nodos
    workflow.add_node("llm", call_model)
    workflow.add_node("tools", call_tools)
    
    # Definir el punto de entrada
    workflow.set_entry_point("llm")
    
    # Agregar aristas condicionales desde el LLM
    workflow.add_conditional_edges(
        "llm",
        should_continue,
        {
            "continue": "tools",
            "end": END
        }
    )
    
    # Después de ejecutar herramientas, volver al LLM
    workflow.add_edge("tools", "llm")
    
    # Compilar el grafo
    compiled_graph = workflow.compile()
    
    logger.info("[CUSTOM AGENT] ✅ Agente ReAct compilado exitosamente")
    logger.info("[CUSTOM AGENT] Flujo: START → llm → [tools → llm]* → END")
    
    return compiled_graph