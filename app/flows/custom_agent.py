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
    
    # ==========================================================
    # Construcción del agente personalizado
    # ----------------------------------------------------------
    # En esta sección implementarás la lógica de tu agente que
    # incorpora fuentes de datos externas y otras funcionalidades.
    # Aquí podrás combinar el modelo y las herramientas MCP 
    # para definir cómo el agente procesa las consultas.
    #
    # Ejemplo:
    #   from langgraph.graph import StateGraph, END
    #   graph = StateGraph()
    #   graph.add_node("model", model)
    #   graph.add_edge("model", END)
    #   flow = graph.compile()
    #   return flow
    # ==========================================================
    pass  # Reemplazar con la implementación