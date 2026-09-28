#!/usr/bin/env python3
"""
ingest_agentic_ecosystem_and_frameworks.py
Ingesta la suite de vanguardia de Frameworks de Agentes, RAG de Grafos,
Optimización Algorítmica de Prompts (DSPy), Salidas Estructuradas (Instructor),
Seguridad (NeMo-Guardrails) y Observabilidad (Langfuse, DeepEval) en Hermes Hub.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any

HUB_ROOT = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_ROOT / "config"
GRAPH_FILE = CONFIG_DIR / "graph.json"

FRAMEWORK_ITEMS = [
    # 1. ORQUESTACIÓN Y AGENTES AUTÓNOMOS
    {
        "id": "skill_langgraph_cyclic_agents",
        "category": "skills/agents",
        "type": "skill",
        "cluster": "cluster_agent_orchestration",
        "title": "LangGraph: Cyclic State Graphs, Checkpointers & Multi-Agent Supervisors",
        "keywords": ["langgraph", "stategraph", "checkpointer", "multi_agent_supervisor", "human_in_the_loop", "time_travel", "cycles"],
        "content": """# LangGraph: StateGraph Cíclico y Orquestación Multi-Agente

## 📌 Visión General
LangGraph extiende LangChain permitiendo flujos de agentes modelados como **Grafos de Estado Cíclicos** con soporte nativo para persistencia (Checkpointers), puntos de control interactivos (Human-in-the-Loop) y retroceso temporal (Time-Travel Debugging).

---

## ⚡ Implementación de un Grafo de Estado con Supervisor
```python
from typing import Annotated, TypedDict, List, Literal
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    next_step: str
    code_solution: str

def research_node(state: AgentState) -> dict:
    return {"messages": [HumanMessage(content="Investigación completada: usar FastAPI y Pydantic-AI.")]}

def coding_node(state: AgentState) -> dict:
    return {"code_solution": "def app(): return 'FastAPI ready'", "next_step": "review"}

def reviewer_node(state: AgentState) -> dict:
    is_valid = len(state.get("code_solution", "")) > 10
    return {"next_step": "approved" if is_valid else "retry"}

def router(state: AgentState) -> Literal["coding", END]:
    if state["next_step"] == "retry":
        return "coding"
    return END

builder = StateGraph(AgentState)
builder.add_node("research", research_node)
builder.add_node("coding", coding_node)
builder.add_node("reviewer", reviewer_node)

builder.add_edge(START, "research")
builder.add_edge("research", "coding")
builder.add_edge("coding", "reviewer")
builder.add_conditional_edges("reviewer", router, {"coding": "coding", END: END})

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
```
"""
    },
    {
        "id": "skill_pydantic_ai_type_safe_agents",
        "category": "skills/agents",
        "type": "skill",
        "cluster": "cluster_agent_orchestration",
        "title": "Pydantic-AI: Type-Safe Agent Framework with Runtime Data Validation",
        "keywords": ["pydantic_ai", "type_safe_agents", "dependency_injection", "runtime_validation", "structured_tools", "clean_architecture"],
        "content": """# Pydantic-AI: Agentes Type-Safe con Inyección de Dependencias

## 📌 Visión General
Pydantic-AI es un framework ligero y agnóstico de modelos construido por el equipo de Pydantic. Ofrece **seguridad de tipos en tiempo de compilación y ejecución**, validación estricta de esquemas en inputs y outputs de agentes, e inyección de dependencias de producción.

---

## ⚡ Implementación en Python
```python
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

class DatabaseConn:
    def execute_query(self, sql: str) -> dict:
        return {"rows_affected": 1, "status": "success"}

@dataclass
class AgentDependencies:
    db: DatabaseConn
    user_tier: str

class MigrationPlan(BaseModel):
    database_type: str = Field(description="Tipo de motor de base de datos")
    steps: list[str] = Field(description="Lista ordenada de sentencias SQL a ejecutar")
    estimated_downtime_sec: int

agent = Agent(
    'openai:gpt-4o',
    deps_type=AgentDependencies,
    result_type=MigrationPlan,
    system_prompt="Eres un DBA senior especializado en migraciones de esquema seguras."
)

@agent.tool
def validate_sql(ctx: RunContext[AgentDependencies], sql_statement: str) -> str:
    res = ctx.deps.db.execute_query(sql_statement)
    return f"Validación exitosa: {res}"
```
"""
    },
    {
        "id": "skill_crewai_role_playing_teams",
        "category": "skills/agents",
        "type": "skill",
        "cluster": "cluster_agent_orchestration",
        "title": "CrewAI: Role-Playing Multi-Agent Orchestration & Hierarchical Delegation",
        "keywords": ["crewai", "role_playing_agents", "hierarchical_process", "task_delegation", "agent_collaboration", "specialized_personas"],
        "content": """# CrewAI: Equipos Multi-Agente Basados en Roles

## 📌 Visión General
CrewAI modela flujos de trabajo colaborativos asignando **roles humanos estructurados** (Role, Goal, Backstory) a agentes que delegan tareas entre sí mediante procesos secuenciales o jerárquicos.

---

## ⚡ Implementación de un Equipo de Auditoría
```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(
    role="Analista de Ciberseguridad",
    goal="Descubrir vulnerabilidades y vectores de ataque en APIs REST",
    backstory="Especialista en OWASP Top 10.",
    verbose=True
)

writer = Agent(
    role="Ingeniero de Documentación Técnica",
    goal="Sintetizar hallazgos técnicos en guías de remediación",
    backstory="Redactor técnico senior con foco en claridad.",
    verbose=True
)

audit_task = Task(
    description="Analiza los riesgos de autenticación JWT sin rotación de claves.",
    expected_output="Informe con 3 vulnerabilidades críticas y su impacto.",
    agent=researcher
)

remediation_task = Task(
    description="Genera el código de remediación en Python/FastAPI para las vulnerabilidades halladas.",
    expected_output="Snippet de código completo con middleware de rotación de claves JWKS.",
    agent=writer
)

security_crew = Crew(
    agents=[researcher, writer],
    tasks=[audit_task, remediation_task],
    process=Process.sequential,
    verbose=True
)
```
"""
    },
    {
        "id": "skill_autogen_conversational_agents",
        "category": "skills/agents",
        "type": "skill",
        "cluster": "cluster_agent_orchestration",
        "title": "Microsoft AutoGen: Conversational Multi-Agent & Sandboxed Code Execution",
        "keywords": ["autogen", "assistant_agent", "user_proxy_agent", "docker_code_execution", "group_chat", "cooperative_problem_solving"],
        "content": """# Microsoft AutoGen: Agentes Conversacionales y Sandbox de Código

## 📌 Visión General
AutoGen de Microsoft estructura la interacción entre agentes como un diálogo continuo. Su componente `UserProxyAgent` es capaz de ejecutar código generado por los agentes en un entorno aislado (local o contenedor Docker) y retroalimentar stdout/stderr al LLM en bucle cerrado.
"""
    },
    {
        "id": "pattern_metagpt_sop_software_company",
        "category": "patterns/agents",
        "type": "pattern",
        "cluster": "cluster_agent_orchestration",
        "title": "MetaGPT Architecture: Standard Operating Procedures (SOPs) for Software Companies",
        "keywords": ["metagpt", "sop", "software_company", "prd", "architecture_design", "role_specialization", "multi_agent_pipeline"],
        "content": """# MetaGPT: Arquitectura Basada en SOPs (Standard Operating Procedures)

## 📌 Concepto Clave
MetaGPT reduce el caos y la deriva conversacional en sistemas multi-agente forzando Procedimientos Operativos Estándar (SOPs). Cada agente representa un rol empresarial con artefactos estructurados:
1. Product Manager (PRD).
2. Architect (Diseño y diagramas).
3. Project Manager (Tareas).
4. Engineer (Código fuente).
5. QA Engineer (Pruebas unitarias).
"""
    },

    # 2. INGENIERÍA DE CONTEXTO, MEMORIA Y RAG
    {
        "id": "skill_llama_index_advanced_rag",
        "category": "skills/rag",
        "type": "skill",
        "cluster": "cluster_context_rag",
        "title": "LlamaIndex: Advanced RAG, Semantic Chunking & Property Graph Indexes",
        "keywords": ["llamaindex", "semantic_chunking", "hybrid_search", "sub_question_query_engine", "property_graph_index", "rerankers"],
        "content": """# LlamaIndex: Pipelines de RAG Avanzado y Chunking Semántico

## 📌 Visión General
LlamaIndex es el framework estándar para ingestión, indexación y recuperación en sistemas RAG complejos. Incluye transformadores de datos, índices de grafos de propiedades (`PropertyGraphIndex`), y motores de consulta con sub-preguntas.

---

## ⚡ Implementación de RAG Híbrido con Reranker Cohere
```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.postprocessor.cohere_rerank import CohereRerank

embed_model = OpenAIEmbedding(model="text-embedding-3-small")
splitter = SemanticSplitterNodeParser(
    buffer_size=1, 
    breakpoint_percentile_threshold=95, 
    embed_model=embed_model
)

documents = SimpleDirectoryReader("./data").load_data()
nodes = splitter.get_nodes_from_documents(documents)
index = VectorStoreIndex(nodes, embed_model=embed_model)

reranker = CohereRerank(top_n=3)
query_engine = index.as_query_engine(
    similarity_top_k=10,
    node_postprocessors=[reranker]
)
```
"""
    },
    {
        "id": "skill_ragflow_deep_document_understanding",
        "category": "skills/rag",
        "type": "skill",
        "cluster": "cluster_context_rag",
        "title": "RAGFlow: Deep Document Understanding (DDU) for Complex Layouts & Tables",
        "keywords": ["ragflow", "deep_document_understanding", "pdf_parsing", "ocr_tables", "layout_analysis", "complex_docs"],
        "content": """# RAGFlow: Comprensión Profunda de Documentos Complejos (DDU)

## 📌 Solución DDU de RAGFlow:
1. Detección de Layout Basada en Visión (reconoce encabezados, párrafos, tablas).
2. Reconstrucción Estructural de Tablas (convierte celdas en Markdown enriquecido).
3. Extracción Multimodal conectando texto con figuras.
"""
    },
    {
        "id": "skill_lightrag_dual_level_graphs",
        "category": "skills/rag",
        "type": "skill",
        "cluster": "cluster_context_rag",
        "title": "LightRAG: Dual-Level Knowledge Graph RAG (Low-Level Entities & High-Level Themes)",
        "keywords": ["lightrag", "dual_level_graph", "knowledge_graph_rag", "multi_hop_reasoning", "global_themes", "entity_resolution"],
        "content": """# LightRAG: RAG Dual Basado en Grafos de Conocimiento

## 📌 Arquitectura Dual
LightRAG indexa la información en dos niveles jerárquicos complementarios:
1. **Nivel Bajo (Low-Level Entity Retrieval)**: Indexa entidades discretas para responder preguntas de hechos puntuales.
2. **Nivel Alto (High-Level Theme Retrieval)**: Agrupa clusters y relaciones abstractas para responder preguntas globales de síntesis.
"""
    },
    {
        "id": "skill_mem0_persistent_memory_layer",
        "category": "skills/rag",
        "type": "skill",
        "cluster": "cluster_context_rag",
        "title": "Mem0: Personalized Persistent Memory Layer for AI Agents",
        "keywords": ["mem0", "personalized_memory", "multi_session_memory", "user_preferences", "long_term_memory"],
        "content": """# Mem0: Capa de Memoria Personalizada y Persistente

## 📌 Visión General
Mem0 proporciona una capa de memoria adaptativa a largo plazo para agentes y asistentes conversacionales, extrayendo hechos relevantes de cada sesión y comprimiendo el contexto histórico.
"""
    },
    {
        "id": "skill_mcp_servers_anthropic_protocol",
        "category": "skills/rag",
        "type": "skill",
        "cluster": "cluster_context_rag",
        "title": "Model Context Protocol (MCP) Standard Servers & Architecture",
        "keywords": ["mcp", "model_context_protocol", "fastmcp", "mcp_servers", "standard_tools", "agent_interoperability"],
        "content": """# Model Context Protocol (MCP) Standard

## 📌 Visión General
El protocolo abierto estándar de Anthropic para conectar modelos de lenguaje con herramientas locales, bases de datos y sistemas de archivos con interoperabilidad universal.
"""
    },

    # 3. OPTIMIZACIÓN DE PARÁMETROS Y PROMPT ENGINEERING
    {
        "id": "skill_dspy_declarative_prompt_programming",
        "category": "skills/prompting",
        "type": "skill",
        "cluster": "cluster_prompt_optimization",
        "title": "DSPy: Declarative Programming & Algorithmic Prompt Compilers (MIPROv2 & Teleprompters)",
        "keywords": ["dspy", "declarative_prompts", "miprov2", "teleprompter", "prompt_compiler", "metric_driven_optimization", "signatures"],
        "content": """# DSPy: Programación Declarativa y Compiladores de Prompts

## 📌 Paradigma: De Prompt Hacking a Prompt Compiling
DSPy define Firmas Declarativas (`Signatures`) y Módulos (`ChainOfThought`, `ReAct`). Un optimizador algorítmico (como **MIPROv2**) compila y encuentra automáticamente el mejor prompt basándose en una métrica objetiva.

---

## ⚡ Implementación en Python con DSPy
```python
import dspy

lm = dspy.LM('openai/gpt-4o-mini')
dspy.configure(lm=lm)

class GenerateUnitTests(dspy.Signature):
    \"\"\"Genera pruebas unitarias exhaustivas con pytest.\"\"\"
    source_code: str = dspy.InputField(desc="Código fuente Python a evaluar")
    test_suite: str = dspy.OutputField(desc="Suite completa de pruebas en pytest")

class TestGeneratorPipeline(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(GenerateUnitTests)

    def forward(self, source_code: str):
        return self.generate(source_code=source_code)
```
"""
    },
    {
        "id": "skill_prompt_engineering_reasoning_patterns",
        "category": "skills/prompting",
        "type": "skill",
        "cluster": "cluster_prompt_optimization",
        "title": "Prompt Engineering Guide: Advanced Reasoning Patterns (CoT, ReAct, ToT, Self-Consistency)",
        "keywords": ["prompt_engineering", "chain_of_thought", "react_pattern", "tree_of_thoughts", "self_consistency", "skeleton_of_thought"],
        "content": """# Patrones Avanzados de Razonamiento en Prompt Engineering

## 📌 1. ReAct (Reasoning + Acting)
Entrelaza el razonamiento verbal (Thought) con llamadas a herramientas (Action) y lectura de resultados (Observation).

## 📌 2. Tree of Thoughts (ToT)
Explora múltiples ramas de pensamiento con evaluación heurística y poda (Backtracking).

## 📌 3. Self-Consistency Sampling
Muestrea múltiples caminos de razonamiento estocásticos y selecciona la respuesta final mediante votación mayoritaria.
"""
    },
    {
        "id": "skill_openai_cookbook_recipes",
        "category": "skills/prompting",
        "type": "skill",
        "cluster": "cluster_prompt_optimization",
        "title": "OpenAI Cookbook: Production Recipes for Function Calling & Structured Outputs",
        "keywords": ["openai_cookbook", "structured_outputs", "json_schema", "function_calling", "batch_api", "embeddings_clustering"],
        "content": """# OpenAI Cookbook: Patrones de Producción

## 📌 Patrones Principales
- **Structured Outputs (`response_format: json_schema`)**: Garantiza 100% de conformidad al esquema JSON sin alucinaciones de formato.
- **Function Calling Paralelo**: Invocación simultánea de múltiples herramientas en un único ciclo.
- **Batch API**: Reducción del 50% de costos en cargas de trabajo no bloqueantes de procesamiento masivo.
"""
    },
    {
        "id": "skill_anthropic_cookbook_patterns",
        "category": "skills/prompting",
        "type": "skill",
        "cluster": "cluster_prompt_optimization",
        "title": "Anthropic Cookbook: Prompt Caching, Extended Thinking & Context Management",
        "keywords": ["anthropic_cookbook", "prompt_caching", "extended_thinking", "context_window_200k", "citation_extraction"],
        "content": """# Anthropic Cookbook: Patrones Avanzados para Modelos Claude

## 📌 Patrones Principales
- **Prompt Caching (`type: ephemeral`)**: Hasta 90% de reducción de costos y 80% de reducción de latencia en prefijos de contexto repetidos.
- **Extended Thinking Budget**: Control milimétrico de tokens de razonamiento (`budget_tokens: 2048`).
- **Extracción de Citas**: Verificación de fuentes mediante citations nativas en respuestas de documentos largos.
"""
    },

    # 4. HERRAMIENTAS, SALIDAS ESTRUCTURADAS Y SEGURIDAD
    {
        "id": "skill_instructor_structured_outputs",
        "category": "skills/guardrails",
        "type": "skill",
        "cluster": "cluster_tools_safety",
        "title": "Instructor: Structured Outputs, Dynamic Validation & Automatic Retries with Pydantic",
        "keywords": ["instructor", "pydantic_validation", "structured_outputs", "automatic_retries", "partial_json_streaming", "json_schema"],
        "content": """# Instructor: Salidas Estructuradas con Validación y Reintentos Automáticos

## 📌 Visión General
Instructor envuelve los clientes oficiales de OpenAI, Anthropic, Gemini y Ollama para forzar respuestas estrictamente conformes a modelos Pydantic con reintentos automáticos ante errores de validación.

---

## ⚡ Implementación en Python
```python
import instructor
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator

client = instructor.from_openai(OpenAI())

class SecurityPatch(BaseModel):
    cve_id: str = Field(description="Identificador CVE estándar")
    severity: str = Field(description="Nivel de severidad")
    remediation_code: str

    @field_validator('cve_id')
    @classmethod
    def validate_cve(cls, v: str) -> str:
        if not v.startswith("CVE-"):
            raise ValueError("El CVE debe comenzar con 'CVE-'.")
        return v

patch = client.chat.completions.create(
    model="gpt-4o-mini",
    response_model=SecurityPatch,
    max_retries=3,
    messages=[{"role": "user", "content": "Genera el parche para CVE-2024-0001"}]
)
```
"""
    },
    {
        "id": "skill_composio_agent_integrations",
        "category": "skills/guardrails",
        "type": "skill",
        "cluster": "cluster_tools_safety",
        "title": "Composio: 100+ Production Tool Integrations & Managed Auth for Agents",
        "keywords": ["composio", "agent_tools", "managed_oauth", "github_tool", "notion_tool", "slack_integration", "action_execution"],
        "content": """# Composio: Integración de Herramientas de Producción para Agentes

## 📌 Visión General
Composio conecta agentes con más de 100 herramientas (GitHub, Linear, Slack, Gmail, Notion, Terminal) manejando autenticación OAuth, renovación de tokens y tipado seguro.
"""
    },
    {
        "id": "skill_nemo_guardrails_safety",
        "category": "skills/guardrails",
        "type": "skill",
        "cluster": "cluster_tools_safety",
        "title": "NVIDIA NeMo-Guardrails: Programmable Rails & Jailbreak Prevention with Colang",
        "keywords": ["nemo_guardrails", "colang", "jailbreak_prevention", "topical_rails", "input_moderation", "output_safety", "llm_security"],
        "content": """# NVIDIA NeMo-Guardrails: Seguridad Programable con Colang

## 📌 Tipos de Guardrails:
1. **Topical Rails**: Evita que el agente se desvíe del tema técnico establecido.
2. **Execution Rails**: Intercepta inyecciones de prompts y jailbreaks antes de llegar al LLM.
3. **Output Rails**: Valida que la respuesta generada no contenga datos confidenciales (PII).
"""
    },

    # 5. OBSERVABILIDAD, EVALUACIÓN Y ARQUITECTURA
    {
        "id": "skill_langfuse_observability_tracing",
        "category": "skills/observability",
        "type": "skill",
        "cluster": "cluster_observability_evals",
        "title": "Langfuse: Open-Source LLM Observability, Distributed Tracing & Token Cost Tracking",
        "keywords": ["langfuse", "distributed_tracing", "prompt_versioning", "token_cost_tracking", "llm_observability", "latency_monitoring"],
        "content": """# Langfuse: Observabilidad y Trazabilidad Distribuida para LLMs

## 📌 Visión General
Langfuse proporciona observabilidad integral para aplicaciones de IA:
- Trazas Distribuidas paso a paso en grafos y agentes.
- Auditoría financiera y tracking de costos de tokens en tiempo real.
- Gestión y versionado de prompts en producción.
"""
    },
    {
        "id": "skill_deepeval_ci_cd_unit_testing",
        "category": "skills/observability",
        "type": "skill",
        "cluster": "cluster_observability_evals",
        "title": "DeepEval: Unit Testing & Continuous Evaluation (CI/CD) for RAG & Agents",
        "keywords": ["deepeval", "rag_evaluation", "faithfulness_metric", "hallucination_metric", "answer_relevancy", "g_eval", "pytest_ci_cd"],
        "content": """# DeepEval: Pruebas Unitarias Automatizadas para RAG y Agentes

## 📌 Métricas Clave de Evaluación
1. **Faithfulness Metric**: Evalúa si la respuesta se basa estrictamente en el contexto recuperado (anti-alucinación).
2. **Answer Relevancy Metric**: Mide si la respuesta atiende la intención de la pregunta.
3. **Contextual Precision & Recall**: Mide la calidad del ranking de recuperación RAG.
4. **G-Eval**: Evaluación LLM-as-a-Judge con rúbricas personalizadas.
"""
    }
]

CLUSTERS = {
    "cluster_agent_orchestration": {
        "type": "cluster",
        "label": "🤖 Agent Orchestration & State Control",
        "file": "",
        "keywords": ["langgraph", "pydantic_ai", "crewai", "autogen", "metagpt", "stategraph", "multi_agent"]
    },
    "cluster_context_rag": {
        "type": "cluster",
        "label": "📚 Context Engineering & Knowledge Graphs (RAG)",
        "file": "",
        "keywords": ["llamaindex", "ragflow", "lightrag", "mem0", "mcp_servers", "semantic_chunking"]
    },
    "cluster_prompt_optimization": {
        "type": "cluster",
        "label": "🎯 Parameter Optimization & Prompt Compilers",
        "file": "",
        "keywords": ["dspy", "prompt_engineering", "miprov2", "chain_of_thought", "react_pattern", "tree_of_thoughts"]
    },
    "cluster_tools_safety": {
        "type": "cluster",
        "label": "🛡️ Tools, Structured Outputs & Safety Rails",
        "file": "",
        "keywords": ["instructor", "composio", "nemo_guardrails", "structured_outputs", "pydantic_validation"]
    },
    "cluster_observability_evals": {
        "type": "cluster",
        "label": "📊 Observability, Tracing & CI/CD Evaluations",
        "file": "",
        "keywords": ["langfuse", "deepeval", "observability", "distributed_tracing", "faithfulness", "ci_cd_tests"]
    }
}


def ingest_agentic_ecosystem():
    print("🚀 Ingeriendo Ecosistema de Agentes, RAG de Grafos, DSPy, Instructor, NeMo y Langfuse...")

    with open(GRAPH_FILE, "r", encoding="utf-8") as f:
        graph = json.load(f)

    nodes: Dict[str, Any] = graph.get("nodes", {})
    edges: List[Dict[str, Any]] = graph.get("edges", [])

    # Registrar nuevos clusters
    for cid, cdata in CLUSTERS.items():
        if cid not in nodes:
            nodes[cid] = cdata
            print(f"  📁 Cluster registrado: {cid}")

    # Escribir archivos de frameworks y conectar
    for item in FRAMEWORK_ITEMS:
        nid = item["id"]
        cat = item["category"]
        file_name = f"{nid.replace('skill_', '').replace('pattern_', '').replace('concept_', '')}.md"
        rel_file = f"{cat}/{file_name}"
        full_path = HUB_ROOT / rel_file
        full_path.parent.mkdir(parents=True, exist_ok=True)

        full_path.write_text(item["content"].strip(), encoding="utf-8")

        nodes[nid] = {
            "type": item["type"],
            "label": item["title"],
            "file": rel_file,
            "keywords": item["keywords"]
        }

        # Conectar al cluster correspondiente
        edges.append({
            "source": item["cluster"],
            "target": nid,
            "weight": 0.95,
            "relation": "contains"
        })
        print(f"  📄 Documento OK: [{item['type'].upper()}] {nid} -> {rel_file}")

    graph["nodes"] = nodes
    graph["edges"] = edges

    with open(GRAPH_FILE, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Se registraron {len(FRAMEWORK_ITEMS)} especificaciones avanzadas del Ecosistema de IA.")


if __name__ == "__main__":
    ingest_agentic_ecosystem()
