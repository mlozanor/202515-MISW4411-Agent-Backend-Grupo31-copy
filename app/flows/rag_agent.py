"""
Workflow del Agente RAG
========================

Este módulo define el flujo de ejecución del Agente RAG utilizando LangGraph.
El agente implementa un flujo LINEAL que consulta el sistema RAG y genera una
respuesta basada en el contexto recuperado.

IMPLEMENTACIÓN SEMANA 6:
- Construir el workflow del agente RAG con LangGraph
- Definir el estado del agente (AgentState)
- Crear nodo "ask" que invoca la herramienta MCP del RAG
- Crear nodo "llm" que genera respuesta con el contexto
- Conectar los nodos en flujo lineal: ask → llm

CARACTERÍSTICAS:
- Flujo determinístico (sin ramificaciones)
- No usa bind_tools (herramienta específica recibida como parámetro)
- Siempre ejecuta la misma secuencia de pasos
"""

from typing import Annotated, Sequence, TypedDict

import logging
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

# ===============================================================================
# SEMANA 6: Construir el flujo del agente RAG
# ===============================================================================
def build_rag_agent(model, ask_tool):

    """
    Construye un agente RAG con flujo lineal.
    Recuerden usar la herrmaienta del MCP definida para consultar el RAG.
    
    Args:
        model: El modelo LLM (Gemini) configurado
        ask_tool: Herramienta MCP para consultar el RAG
    
    Returns:
        CompiledGraph: El grafo compilado listo para ejecutar
    """
    
    # Ejemplo:
    #   from langgraph.graph import StateGraph, END
    #   graph = StateGraph()
    #   graph.add_node("model", model)
    #   graph.add_edge("model", END)
    #   flow = graph.compile()
    #   return flow
    
    pass  # Reemplazar con la implementación
