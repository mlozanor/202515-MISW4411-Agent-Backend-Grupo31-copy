"""
Script de Prueba de LangSmith Tracing - Conversación Completa
==============================================================

Este script genera trazas en LangSmith simulando la conversación completa
del asistente de Google Cloud con respuestas específicas.

REQUISITOS:
- Archivo .env con LANGCHAIN_TRACING_V2=true
- API Key válida de LangSmith configurada
- Dependencias instaladas (langchain, langsmith)

USO:
    python test_langsmith_tracing_conversacion.py
"""

import os
import sys
from datetime import datetime
import time

# Importar configuración de LangSmith
try:
    import langsmith_config
except ImportError:
    print("❌ Error: No se pudo importar langsmith_config.py")
    print("   Asegúrate de que el archivo exista en el directorio actual")
    sys.exit(1)


def verify_setup():
    """Verifica que la configuración esté lista."""
    print("\n" + "=" * 80)
    print("  VERIFICACIÓN DE CONFIGURACIÓN")
    print("=" * 80 + "\n")
    
    if os.getenv("LANGCHAIN_TRACING_V2", "").lower() != "true":
        print("❌ LANGCHAIN_TRACING_V2 no está habilitado")
        return False
    
    if not os.getenv("LANGCHAIN_API_KEY"):
        print("❌ LANGCHAIN_API_KEY no está configurada")
        return False
    
    print(f"✅ Tracing habilitado")
    print(f"✅ Proyecto: {os.getenv('LANGCHAIN_PROJECT', 'default')}")
    print()
    return True


def generate_conversation_traces():
    """Genera trazas simulando la conversación completa con el asistente."""
    
    try:
        from langchain_core.runnables import RunnableLambda, RunnableSequence
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        from langchain_core.prompts import ChatPromptTemplate
        
        print("=" * 80)
        print("  GENERANDO TRAZAS DE CONVERSACIÓN")
        print("=" * 80 + "\n")
        
        # Definir las conversaciones con sus respuestas específicas
        conversations = [
            {
                "question": "Quiero el capítulo 3.",
                "classification": "content_selection",
                "response": """Excelente, trabajaremos con el capítulo 'Capítulo 3: Comprensión de los Diferentes Modelos de Cloud Computing'.

Temas principales del capítulo 'Capítulo 3: Comprensión de los Diferentes Modelos de Cloud Computing':
Modelo de Responsabilidad Compartida
Infraestructura como Servicio (IaaS)
Plataforma como Servicio (PaaS)
Software como Servicio (SaaS)
Modelos Avanzados (CaaS y FaaS)

¿Prefieres un resumen del capítulo o aprender alguno de los temas listados?""",
                "metadata": {
                    "chapter": "3",
                    "action": "chapter_selection",
                    "requires_rag": True,
                    "topics_listed": 5
                }
            },
            {
                "question": "Hazme un summary del capítulo 3.",
                "classification": "content_summary",
                "response": """Aquí tienes un resumen de 'Capítulo 3: Comprensión de los Diferentes Modelos de Cloud Computing':

¡Excelente trabajo en este capítulo! Has explorado los modelos fundamentales de cloud computing y el crucial Modelo de Responsabilidad Compartida (SRM).

Este capítulo es esencial para tu preparación, ya que detalla los modelos de alojamiento en la nube: Software como Servicio (SaaS), Plataforma como Servicio (PaaS) e Infraestructura como Servicio (IaaS). Comprenderás cómo estos difieren en términos de Costo Total de Propiedad (TCO), flexibilidad, nivel de gestión y responsabilidades compartidas entre el proveedor de la nube (como Google Cloud) y el cliente. Por ejemplo, en SaaS (ej. Google Compute Engine), el cliente gestiona PaaS (ej. App Engine) y SaaS (ej. Gmail), el proveedor asume progresivamente más gestión de la infraestructura subyacente. Además, se introducen CaaS (Contenedores como Servicio) y FaaS (Funciones como Servicio) como evoluciones que ofrecen niveles de abstracción aún mayores, destacando la importancia de elegir el modelo adecuado para cada escenario y caso de uso para optimizar recursos y asegurar el cumplimiento.

¿Quieres profundizar en algún tema, solicitar otra explicación o cambiar de capítulo?""",
                "metadata": {
                    "chapter": "3",
                    "action": "summary",
                    "requires_rag": True,
                    "documents_retrieved": 5
                }
            },
            {
                "question": "Quiero aprender sobre PaaS.",
                "classification": "concept_explanation",
                "response": """Repasemos un tema clave del capítulo en 'Capítulo 3: Comprensión de los Diferentes Modelos de Cloud Computing':

Infraestructura como Servicio (IaaS) es un modelo de cloud computing que proporciona recursos de infraestructura virtualizados bajo demanda, como máquinas virtuales (VMs), almacenamiento, redes y virtualización. Los clientes obtienen la mayor flexibilidad y control, siendo responsables del sistema operativo, el entorno de ejecución, las aplicaciones, los datos y la configuración de red, mientras que el proveedor de la nube gestiona el hardware y la capa de virtualización. En Google Cloud, el servicio IaaS principal es Compute Engine, que permite a los clientes lanzar y gestionar VMs, configurar tamaños personalizados y aprovechar características como Managed Instance Groups (MIGs) para autoescalado y autorreparación. Este modelo implica el Costo Total de Propiedad (TCO) más alto y requiere el mayor nivel de gestión y experiencia técnica por parte del cliente, siendo ideal para organizaciones que necesitan un control granular sobre su infraestructura, como aquellas en industrias reguladas.

¿Quieres profundizar en otro tema, pedir un resumen o cambiar de capítulo?""",
                "metadata": {
                    "chapter": "3",
                    "concept": "IaaS",
                    "action": "concept_explanation",
                    "requires_rag": True,
                    "documents_retrieved": 3
                }
            },
            {
                "question": "¿Cómo es Infraestructura como Servicio (IaaS)?",
                "classification": "technical_question",
                "response": """Repasemos Infraestructura como Servicio (IaaS) en 'Capítulo 3: Comprensión de los Diferentes Modelos de Cloud Computing':

La Infraestructura como Servicio (IaaS) es un modelo de cloud computing que proporciona recursos de infraestructura esenciales bajo demanda, como cómputo, almacenamiento, redes y virtualización, a través de Internet. En este modelo, el proveedor de la nube (como Google Cloud) es responsable únicamente del hardware físico y la capa de virtualización subyacente, mientras que el cliente mantiene el control total y la responsabilidad de los sistemas operativos, entornos de ejecución, aplicaciones, datos y su configuración. IaaS ofrece la mayor flexibilidad y control sobre la infraestructura, lo que permite a las organizaciones migrar cargas de trabajo on-premises con poca modificación, pero también implica el Costo Total de Propiedad (TCO) más alto de los modelos de nube principales debido a la gestión de personal y licencias necesarias para gestionar la pila superior. En Google Cloud, el servicio IaaS por excelencia es Compute Engine, que permite a los clientes lanzar y gestionar Máquinas Virtuales (VMs) personalizables, incluyendo características como los Managed Instance Groups (MIGs) para autoescalado y autocuración. Es ideal para escenarios donde se requiere un control profundo sobre el entorno de ejecución y el sistema operativo.

¿Quieres profundizar en otro tema, pedir un resumen o cambiar de capítulo?""",
                "metadata": {
                    "chapter": "3",
                    "concept": "IaaS",
                    "action": "concept_explanation",
                    "requires_rag": True,
                    "documents_retrieved": 3
                }
            },
            {
                "question": "¿Y qué opinas del horóscopo de hoy?",
                "classification": "out_of_scope",
                "response": """Puedo ayudarte exclusivamente con temas de aprendizaje sobre Google Cloud Platform. ¿Hay algún capítulo o concepto de Google Cloud que quieras estudiar?""",
                "metadata": {
                    "action": "out_of_scope_rejection",
                    "requires_rag": False
                }
            }
        ]
        
        # Sistema de mensajes inicial
        system_message = """Eres un Asistente Inteligente especializado en Google Cloud Platform. 
Tu función es ayudar a los usuarios a estudiar para su certificación de Google Cloud y 
responder preguntas sobre la plataforma."""
        
        # Crear funciones para simular el pipeline RAG
        def classify_input(data):
            """Clasifica la entrada del usuario."""
            question = data["question"]
            classification = data["classification"]
            print(f"   🔍 Clasificación: {classification}")
            return {**data, "classified": True}
        
        def retrieve_documents(data):
            """Simula la recuperación de documentos."""
            if data["metadata"].get("requires_rag"):
                num_docs = data["metadata"].get("documents_retrieved", 0)
                if num_docs > 0:
                    print(f"   📚 Documentos recuperados: {num_docs}")
                    docs = [f"Documento {i+1} sobre {data['metadata'].get('concept', 'el tema')}" 
                            for i in range(num_docs)]
                    return {**data, "documents": docs}
            return {**data, "documents": []}
        
        def generate_response(data):
            """Genera la respuesta final."""
            response = data["response"]
            print(f"   ✅ Respuesta generada ({len(response)} caracteres)")
            return {**data, "final_response": response}
        
        # Crear el pipeline como secuencia de Runnables
        classify_chain = RunnableLambda(classify_input)
        retrieve_chain = RunnableLambda(retrieve_documents)
        generate_chain = RunnableLambda(generate_response)
        
        # Pipeline completo
        pipeline = classify_chain | retrieve_chain | generate_chain
        
        print(f"💬 Generando {len(conversations)} conversaciones...\n")
        
        successful_traces = 0
        
        # Procesar cada conversación
        for i, conv in enumerate(conversations, 1):
            try:
                print(f"{'─' * 80}")
                print(f"Conversación {i}/{len(conversations)}")
                print(f"{'─' * 80}")
                print(f"👤 Usuario: {conv['question']}")
                
                # Ejecutar el pipeline (esto genera la traza en LangSmith)
                result = pipeline.invoke(conv)
                
                print(f"🤖 Asistente: {result['final_response'][:100]}...")
                print(f"   ⏱️  Timestamp: {datetime.now().isoformat()}")
                
                successful_traces += 1
                
                # Pausa entre conversaciones para que sean más fáciles de distinguir
                time.sleep(1)
                print()
                
            except Exception as e:
                print(f"   ❌ Error en conversación {i}: {e}")
                import traceback
                traceback.print_exc()
                print()
        
        # Resumen final
        print("=" * 80)
        print("  RESUMEN")
        print("=" * 80)
        print(f"✅ Trazas generadas: {successful_traces}/{len(conversations)}")
        print(f"📊 Proyecto: {os.getenv('LANGCHAIN_PROJECT', 'default')}")
        print(f"⏰ Completado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("🔗 Ve tus trazas en LangSmith:")
        print(f"   https://smith.langchain.com")
        print()
        print("💡 Deberías ver 5 trazas representando:")
        print("   1. Selección de capítulo (sin RAG)")
        print("   2. Resumen de capítulo (con RAG, 3 docs)")
        print("   3. Explicación de PaaS (con RAG, 2 docs)")
        print("   4. Pregunta sobre IaaS (falló la generación)")
        print("   5. Consulta fuera de alcance (rechazada)")
        print("=" * 80)
        
        return successful_traces > 0
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal."""
    print("\n" + "█" * 80)
    print("  TEST DE LANGSMITH - CONVERSACIÓN COMPLETA DEL ASISTENTE")
    print("█" * 80)
    
    # Verificar configuración
    if not verify_setup():
        print("\n❌ Configuración incompleta. Revisa tu archivo .env")
        return 1
    
    # Generar trazas
    success = generate_conversation_traces()
    
    if success:
        print("\n🎉 ¡Trazas generadas exitosamente!")
        return 0
    else:
        print("\n⚠️  Hubo problemas generando las trazas")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
    