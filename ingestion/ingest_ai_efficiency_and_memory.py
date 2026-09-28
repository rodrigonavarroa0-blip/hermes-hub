#!/usr/bin/env python3
"""
ingest_ai_efficiency_and_memory.py
Investiga y genera la documentación técnica de vanguardia sobre:
1. Tecnologías de Ahorro de Tokens y Compresión de Prompts (LLMLingua-2, Semantic Caching, Prompt Caching).
2. Memoria Conversacional Ultrarrápida y Arquitecturas Jerárquicas (Mem0, HippoRAG, Zep, RRF Memory Streams).
3. Eficiencia de Inferencia y Aceleración de Hardware (PagedAttention, FlashAttention-3, Speculative Decoding, FP8/AWQ).
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any

HUB_ROOT = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_ROOT / "config"
GRAPH_FILE = CONFIG_DIR / "graph.json"

EFFICIENCY_ITEMS = [
    # =========================================================
    # A. TOKEN REDUCTION & CONTEXT COMPRESSION
    # =========================================================
    {
        "id": "skill_prompt_compression_llmlingua",
        "category": "skills/efficiency",
        "type": "skill",
        "cluster": "cluster_ai_efficiency",
        "title": "Prompt Compression with LLMLingua-2 & Token Budgeting",
        "keywords": ["prompt_compression", "llmlingua", "token_budget", "context_pruning", "cost_reduction", "token_economy"],
        "content": """---
id: skill_prompt_compression_llmlingua
title: Prompt Compression with LLMLingua-2 & Token Budgeting
type: skill
cluster: cluster_ai_efficiency
category: efficiency_optimization
keywords: [prompt_compression, llmlingua, token_budget, context_pruning, cost_reduction, token_economy]
---

# Prompt Compression with LLMLingua-2

## 📌 Visión General
**LLMLingua-2** es un algoritmo de compresión de prompts basado en un modelo pequeño de clasificación de tokens (*Token-Level Task-Agnostic Compression*). Permite comprimir prompts masivos (RAG, transcripciones, código, contexto histórico) entre un **2x y 5x (reducción del 50% al 80% de tokens)** preservando el 98%+ de la precisión del LLM downstream.

---

## ⚡ Cómo Funciona el Algoritmo
1. **Clasificación por Probabilidad de Información**: Un modelo ligero (ej. `xlm-roberta-large` afinado) asigna un score de relevancia a cada palabra/subtoken.
2. **Poda Adaptativa de Tokens**: Se eliminan conectores redundantes, palabras de relleno y repeticiones mientras se preservan entidades clave, números, funciones y argumentos.
3. **Alineación de Presupuesto**: Comprime dinámicamente hasta alcanzar el presupuesto exacto de tokens objetivo (*Target Budget*).

---

## 🐍 Implementación en Python
```python
from llmlingua import PromptCompressor

compressor = PromptCompressor(
    model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
    use_llmlingua2=True
)

def compress_context_for_agent(raw_context: str, target_token_budget: int = 800) -> str:
    \"\"\"Comprime el contexto crudo para no exceder el presupuesto de tokens.\"\"\"
    results = compressor.compress_prompt(
        context=[raw_context],
        rate=0.4, # 60% de reducción de tokens
        target_token=target_token_budget,
        use_sentence_level_filter=False,
        condition_compare=True
    )
    print(f"📉 Tokens originales: {results['origin_tokens']} -> Comprimidos: {results['compressed_tokens']}")
    print(f"💰 Tasa de Ahorro: {results['ratio']}")
    return results['compressed_prompt']
```
"""
    },
    {
        "id": "pattern_semantic_caching_gptcache",
        "category": "patterns/efficiency",
        "type": "pattern",
        "cluster": "cluster_ai_efficiency",
        "title": "Semantic Caching Architecture with In-Memory Embeddings (GPTCache / Redis)",
        "keywords": ["semantic_cache", "gptcache", "redis_embeddings", "cosine_similarity", "zero_token_cost", "sub_10ms"],
        "content": """---
id: pattern_semantic_caching_gptcache
title: Semantic Caching Architecture with Vector Similarity
type: pattern
cluster: cluster_ai_efficiency
category: efficiency_optimization
keywords: [semantic_cache, gptcache, redis_embeddings, cosine_similarity, zero_token_cost, sub_10ms]
---

# Semantic Caching Architecture

## 📌 Visión General
A diferencia de los cachés tradicionales clave-valor (que solo aciertan si la consulta es carácter por carácter idéntica), un **Caché Semántico** calcula el embedding de la pregunta del usuario y busca en memoria si existe una consulta previa con similitud de coseno $cos(\theta) \ge 0.92$.

### 🏆 Beneficios:
- **Coste de Tokens**: $0 en peticiones cacheadas (100% de ahorro).
- **Latencia de Respuesta**: Pasa de ~1,500ms (LLM API) a **< 5ms** (memoria local).

---

## ⚡ Implementación en Python con In-Memory Embedding Cache
```python
import numpy as np
from typing import Optional, Dict, Tuple

class FastSemanticCache:
    def __init__(self, similarity_threshold: float = 0.92):
        self.threshold = similarity_threshold
        self.cache: Dict[str, Tuple[np.ndarray, str]] = {}

    def get(self, query_embedding: np.ndarray) -> Optional[str]:
        if not self.cache:
            return None
        
        # Búsqueda vectorial vectorizada en memoria RAM
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        for key, (cached_emb, cached_response) in self.cache.items():
            cached_norm = cached_emb / np.linalg.norm(cached_emb)
            sim = float(np.dot(query_norm, cached_norm))
            if sim >= self.threshold:
                return cached_response
        return None

    def set(self, query: str, query_embedding: np.ndarray, response: str):
        self.cache[query] = (query_embedding, response)
```
"""
    },

    # =========================================================
    # B. RAPID CONVERSATIONAL MEMORY & RETRIEVAL
    # =========================================================
    {
        "id": "pattern_mem0_hierarchical_memory",
        "category": "patterns/memory",
        "type": "pattern",
        "cluster": "cluster_cognitive_memory",
        "title": "Mem0 & MemGPT Hierarchical Memory Architecture (Working, Episodic & Core)",
        "keywords": ["mem0", "memgpt", "hierarchical_memory", "episodic_memory", "semantic_memory", "fast_recall"],
        "content": """---
id: pattern_mem0_hierarchical_memory
title: Hierarchical Conversational Memory Architecture (Mem0 & MemGPT)
type: pattern
cluster: cluster_cognitive_memory
category: memory_systems
keywords: [mem0, memgpt, hierarchical_memory, episodic_memory, semantic_memory, fast_recall]
---

# Hierarchical Conversational Memory Architecture

## 📌 Visión General
Los sistemas de memoria jerárquica emulan la arquitectura cognitiva humana dividiendo el conocimiento en 3 niveles de velocidad y persistencia:

1. **Memoria de Trabajo (Working Memory / Scratchpad)**: Contexto activo inmediato (últimos 3-5 turnos + variables de ejecución).
2. **Memoria Episódica (Episodic Memory)**: Registro temporal de eventos pasados, conversaciones previas y resultados de herramientas.
3. **Memoria Semántica / Central (Core Long-Term Memory)**: Hechos inmutables, preferencias del usuario, reglas del sistema y grafo de conceptos consolidados.

---

## ⚡ Diagrama de Flujo
```text
[ Mensaje Usuario ] 
        │
        ▼
[ Memoria de Trabajo (Working) ] ── (¿Faltan datos?) ──▶ [ Graph Spreading Activation (Hermes) ]
        │                                                              │ (Sub-milisegundo)
        ▼                                                              ▼
[ LLM Generation ] ──▶ [ Actualizador Asíncrono de Memoria ] ──▶ [ Memoria Semántica Persistente ]
```
"""
    },
    {
        "id": "concept_hipporag_synaptic_memory",
        "category": "concepts/memory",
        "type": "concept",
        "cluster": "cluster_cognitive_memory",
        "title": "HippoRAG & Hippocampal Indexing (Personalized PageRank & Spreading Activation)",
        "keywords": ["hipporag", "hippocampus", "spreading_activation", "personalized_pagerank", "sub_millisecond_recall"],
        "content": """---
id: concept_hipporag_synaptic_memory
title: HippoRAG & Neuro-Inspired Synaptic Memory
type: concept
cluster: cluster_cognitive_memory
category: cognitive_ai
keywords: [hipporag, hippocampus, spreading_activation, personalized_pagerank, sub_millisecond_recall]
---

# HippoRAG: Neuro-Inspired Synaptic Memory

## 📌 Fundamento Biológico
HippoRAG modela el funcionamiento del **Hipocampo Humano** en la consolidación y recuperación de memoria a largo plazo. En lugar de hacer búsquedas vectoriales aisladas en un espacio euclídeo desarticulado, HippoRAG utiliza **Grafos de Conocimiento Sinápticos** donde los conceptos están conectados por relaciones asociativas.

### ⚡ Algoritmo de Recuperación:
1. Las entidades mencionadas en la consulta actúan como **nodos semilla (*Seed Nodes*)**.
2. Se inyecta energía a las semillas y se propaga a través de las aristas ponderadas usando **Spreading Activation / Personalized PageRank (PPR)**.
3. El grafo converge en **< 1ms**, recuperando asociaciones no explícitas (descubrimiento de patrones multi-hop sin alucinaciones).
"""
    },
    {
        "id": "skill_zep_temporal_fact_extraction",
        "category": "skills/memory",
        "type": "skill",
        "cluster": "cluster_cognitive_memory",
        "title": "Fast Conversational Fact Extraction & Temporal Memory Graph (Zep Style)",
        "keywords": ["zep", "fact_extraction", "temporal_graph", "entity_linking", "dialogue_compression"],
        "content": """---
id: skill_zep_temporal_fact_extraction
title: Automated Conversational Fact Extraction & Temporal Graphs
type: skill
cluster: cluster_cognitive_memory
category: memory_systems
keywords: [zep, fact_extraction, temporal_graph, entity_linking, dialogue_compression]
---

# Conversational Fact Extraction & Temporal Graphs

## 📌 Visión General
Para evitar reenviar historiales de conversación gigantescos, este patrón extrae **hechos atómicos triples (Sujeto, Predicado, Objeto)** en segundo plano tras cada turno conversacional.

### Ejemplo de Compresión de Memoria:
- **Diálogo (150 tokens)**: *"Hola, ayer estuve probando la integración con PostgreSQL usando Drizzle ORM y configuré el pool a 20 conexiones porque teníamos errores de timeout."*
- **Hechos Extraídos (25 tokens)**:
  - `(Usuario, utiliza, Drizzle ORM)`
  - `(BaseDeDatos, es, PostgreSQL)`
  - `(PostgreSQL_Pool, max_connections, 20)`
  - `(Problema_Previo, fue, Timeout)`

Al siguiente turno, el sistema solo inyecta los hechos relevantes, reduciendo el consumo de tokens en un **83%**.
"""
    },

    # =========================================================
    # C. HARDWARE & INFERENCE EFFICIENCY
    # =========================================================
    {
        "id": "concept_paged_attention_vllm",
        "category": "concepts/inference",
        "type": "concept",
        "cluster": "cluster_ai_efficiency",
        "title": "PagedAttention & vLLM Virtual Memory Management for KV Cache",
        "keywords": ["paged_attention", "vllm", "kv_cache", "virtual_memory", "high_throughput", "gpu_memory"],
        "content": """---
id: concept_paged_attention_vllm
title: PagedAttention & vLLM High-Throughput Memory Architecture
type: concept
cluster: cluster_ai_efficiency
category: inference_engineering
keywords: [paged_attention, vllm, kv_cache, virtual_memory, high_throughput, gpu_memory]
---

# PagedAttention & vLLM Architecture

## 📌 El Problema de la Memoria KV Cache
En la inferencia tradicional de LLMs, la memoria reservada para el Key-Value (KV) Cache debe ser contigua. Esto genera hasta un **60% - 80% de desperdicio de VRAM** debido a la fragmentación interna y externa (memoria reservada para la longitud máxima de respuesta que nunca se utiliza).

## ⚡ Solución PagedAttention
Inspirado en la paginación de memoria virtual de los Sistemas Operativos, **PagedAttention** divide el KV Cache en bloques discretos (*KV Pages*) no contiguos mapeados por una tabla de páginas física:
- **Throughput**: Multiplica por **2x - 4x** la cantidad de peticiones concurrentes en la misma GPU.
- **Memoria Compartida**: Permite que múltiples secuencias (ej. Speculative Decoding, Parallel Sampling) compartan los mismos bloques de prefijo en VRAM con coste cero (*Copy-on-Write*).
"""
    },
    {
        "id": "concept_flash_attention_3",
        "category": "concepts/inference",
        "type": "concept",
        "cluster": "cluster_ai_efficiency",
        "title": "FlashAttention-3 & Flash-Decoding (IO-Aware Exact Attention)",
        "keywords": ["flashattention_3", "flash_decoding", "io_aware", "sram_gpu", "hopper_blackwell", "speedup"],
        "content": """---
id: concept_flash_attention_3
title: FlashAttention-3 & Flash-Decoding IO-Aware Speedup
type: concept
cluster: cluster_ai_efficiency
category: inference_engineering
keywords: [flashattention_3, flash_decoding, io_aware, sram_gpu, hopper_blackwell, speedup]
---

# FlashAttention-3 & Flash-Decoding

## 📌 Visión General
**FlashAttention-3** explota la jerarquía de memoria física de las GPUs modernas (NVIDIA H100 / Blackwell B200), solapando la computación tensorial (Tensor Cores) con las transferencias asíncronas de memoria entre HBM y SRAM (WGMMA - Asynchronous Warp Group Matrix Multiplication).

- **Flash-Decoding**: Paraleliza la fase de autoregresión a lo largo de la dimensión de la longitud de contexto, logrando aceleraciones de **hasta 8x en contextos de 64k a 256k tokens**.
"""
    },
    {
        "id": "pattern_speculative_decoding",
        "category": "patterns/inference",
        "type": "pattern",
        "cluster": "cluster_ai_efficiency",
        "title": "Speculative Decoding & Multi-Head Draft Models (Medusa / EAGLE)",
        "keywords": ["speculative_decoding", "medusa", "eagle", "draft_model", "fast_token_generation", "latency"],
        "content": """---
id: pattern_speculative_decoding
title: Speculative Decoding & Multi-Head Speculation (Medusa & EAGLE)
type: pattern
cluster: cluster_ai_efficiency
category: inference_engineering
keywords: [speculative_decoding, medusa, eagle, draft_model, fast_token_generation, latency]
---

# Speculative Decoding & Draft Models

## 📌 Visión General
La inferencia de LLMs estándar es *Memory-Bandwidth Bound* (genera 1 token por cada paso forward completo).

**Speculative Decoding** utiliza un modelo borrador ultra rápido (ej. Llama-3-1B) o cabezales neuronales múltiples paralelos (Medusa / EAGLE) para proponer $K$ tokens candidatos en un solo ciclo. El modelo principal (ej. Llama-3-70B) valida todos los candidatos en un único pase de atención vectorial.
- **Resultado**: Aceleración de **2.2x a 3.5x en latencia** sin cambiar un solo bit en la distribución de salida.
"""
    }
]

CLUSTERS = {
    "cluster_ai_efficiency": {
        "type": "cluster",
        "label": "⚡ AI Efficiency & Token Reduction",
        "file": "",
        "keywords": ["llmlingua", "prompt_compression", "semantic_cache", "paged_attention", "flash_attention", "speculative_decoding", "efficiency"]
    },
    "cluster_cognitive_memory": {
        "type": "cluster",
        "label": "🧠 Cognitive & Fast Memory Systems",
        "file": "",
        "keywords": ["mem0", "memgpt", "hipporag", "zep", "episodic_memory", "semantic_memory", "spreading_activation", "facts"]
    }
}


def ingest_all():
    print("🚀 Ingeriendo Tecnologías de Eficiencia, Ahorro de Tokens y Memoria Ultrarrápida...")

    with open(GRAPH_FILE, "r", encoding="utf-8") as f:
        graph = json.load(f)

    nodes: Dict[str, Any] = graph.get("nodes", {})
    edges: List[Dict[str, Any]] = graph.get("edges", [])

    # Registrar clusters
    for cid, cdata in CLUSTERS.items():
        if cid not in nodes:
            nodes[cid] = cdata
            print(f"  📁 Cluster registrado: {cid}")

    # Escribir archivos e incorporar nodos
    for item in EFFICIENCY_ITEMS:
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

        # Conectar al cluster
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

    print(f"\n✅ Se registraron {len(EFFICIENCY_ITEMS)} tecnologías de eficiencia y memoria.")


if __name__ == "__main__":
    ingest_all()
