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
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

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
# DEFINICIÓN DEL ESTADO DEL AGENTE
# ===============================================================================

class AgentState(TypedDict):
    """
    Estado del agente RAG que se propaga entre nodos.
    
    Basado en los tutoriales de LangGraph, el estado mantiene:
    - messages: Historial de mensajes de la conversación
    - context: Contexto recuperado del RAG
    - input: Pregunta original del usuario
    """
    
    # Historial de mensajes con anotación para agregar mensajes automáticamente
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Contexto recuperado del RAG
    context: str
    
    # Pregunta original del usuario
    input: str


# ===============================================================================
# PROMPT TEMPLATE PARA EL AGENTE
# ===============================================================================

# Basado en el tutorial, definimos un prompt que integra el contexto del RAG
RAG_PROMPT = ChatPromptTemplate.from_template("""
Eres un asistente especializado en responder preguntas basándote en el contexto proporcionado.

CONTEXTO RECUPERADO:
{context}

INSTRUCCIONES:
- Responde ÚNICAMENTE basándote en el contexto proporcionado
- Si la información no está en el contexto, indícalo claramente
- Mantén las respuestas concisas y precisas
- Cita las fuentes cuando sea posible

PREGUNTA DEL USUARIO:
{question}

RESPUESTA:
""")


# ===============================================================================
# SEMANA 6: Construir el flujo del agente RAG
# ===============================================================================

def build_rag_agent(model, ask_tool):
    """
    Construye un agente RAG con flujo lineal basado en LangGraph.
    
    ARQUITECTURA DEL FLUJO:
    
    START → ask_node → llm_node → END
    
    - ask_node: Invoca la herramienta MCP del RAG para recuperar contexto
    - llm_node: Genera la respuesta usando el modelo LLM y el contexto
    
    Args:
        model: El modelo LLM (Gemini) configurado
        ask_tool: Herramienta MCP para consultar el RAG
    
    Returns:
        CompiledGraph: El grafo compilado listo para ejecutar
    """
    
    logger.info("[RAG AGENT] Construyendo agente RAG con LangGraph...")
    
    # ===============================================================================
    # NODO 1: Recuperación de contexto desde el RAG
    # ===============================================================================
    
    async def ask_node(state: AgentState) -> AgentState:
        """
        Nodo que invoca la herramienta del RAG para recuperar contexto.
        
        Similar al nodo retrieve_documents del tutorial, pero usando la herramienta MCP.
        """
        logger.info("[ASK NODE] Iniciando recuperación de contexto...")
        
        # Obtener la pregunta del usuario del estado
        question = state["input"]
        logger.info(f"[ASK NODE] Pregunta: {question}")
        
        # Invocar la herramienta del RAG de forma síncrona
        # La herramienta MCP ya está configurada como herramienta de LangChain
        context = await ask_tool.ainvoke({"query": question})
        
        logger.info(f"[ASK NODE] Contexto recuperado: {len(context)} caracteres")
        
        # Actualizar el estado con el contexto recuperado
        return {
            **state,
            "context": context
        }
    
    
    # ===============================================================================
    # NODO 2: Generación de respuesta con el LLM
    # ===============================================================================
    
    def llm_node(state: AgentState) -> AgentState:
        """
        Nodo que genera la respuesta usando el modelo LLM y el contexto.
        
        Similar al nodo generate_response del tutorial, formatea el prompt
        con el contexto recuperado y genera la respuesta.
        """
        logger.info("[LLM NODE] Generando respuesta...")
        
        # Obtener datos del estado
        question = state["input"]
        context = state.get("context", "No se pudo recuperar contexto del RAG.")
        
        # Formatear el prompt con el contexto y la pregunta
        formatted_prompt = RAG_PROMPT.invoke({
            "context": context,
            "question": question
        })
        
        logger.info(f"[LLM NODE] Invocando modelo LLM...")
        
        # Generar respuesta con el modelo
        response = model.invoke(formatted_prompt)
        
        logger.info(f"[LLM NODE] Respuesta generada: {len(response.content)} caracteres")
        
        # Crear mensaje de respuesta del asistente
        assistant_message = AIMessage(content=response.content)
        
        # Actualizar el estado con la respuesta
        return {
            **state,
            "messages": [assistant_message]
        }
    
    
    # ===============================================================================
    # CONSTRUCCIÓN DEL GRAFO
    # ===============================================================================
    
    logger.info("[RAG AGENT] Construyendo grafo de estado...")
    
    # Crear el grafo con el estado definido
    workflow = StateGraph(AgentState)
    
    # Agregar nodos al grafo
    workflow.add_node("ask", ask_node)
    workflow.add_node("llm", llm_node)
    
    # Definir el flujo LINEAL: START → ask → llm → END
    workflow.add_edge(START, "ask")
    workflow.add_edge("ask", "llm")
    workflow.add_edge("llm", END)
    
    # Compilar el grafo
    compiled_graph = workflow.compile()
    
    logger.info("[RAG AGENT] ✅ Agente RAG compilado exitosamente")
    
    return compiled_graph