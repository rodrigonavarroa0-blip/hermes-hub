# Antigravity Loop Specification & PRD - Hermes 5-Layer Master Architecture

## 1. Objective
Complete end-to-end implementation and production validation of the 5-Layer Modular Architecture for Hermes Knowledge Hub:
- Capa 1: Ingesta Canónica de Documentación Oficial (`ingestion/docs_harvester.py`).
- Capa 2: Re-Ranker Neuronal Cross-Encoder (`core/reranker.py`).
- Capa 3: Grafo de Propiedades Causal y Tipado (`core/typed_graph.py`).
- Capa 4: Servidor FastMCP Dual Stdio + SSE Local (`core/mcp_server.py`).
- Capa 5: Smart Watcher Daemon y Scanner de Antipatrones (`core/smart_watcher.py`).

## 2. Global Execution Rules
* **Atomic Processing:** Complete exactly ONE sub-task per iteration loop.
* **Context Preservation:** Always read `progress.txt` at the beginning of a cycle and update it before exiting.
* **Verification Gate:** Run local test suites or validation commands immediately after modifying files. Do not proceed if tests fail.

## 3. Implementation Checklist
- [x] **Task 1: Design Alignment via /grill-me** -> User approved 5-layer full package with open LAN SSE port 8765 and dual watcher daemon/MCP tool.
- [x] **Task 2: Layer 1 (Docs Harvester)** -> Ingested Next.js 15, FastAPI, Pydantic V2, Docker canonical documentation guides.
- [x] **Task 3: Layer 2 (Cross-Encoder Re-ranker)** -> High-precision scoring (<3ms) integrated into Hybrid GraphRAG pipeline.
- [x] **Task 4: Layer 3 (Typed Property Graph)** -> Implemented causal semantic relations (`mitigates_antipattern`, `depends_on`, `replaces_obsolete`).
- [x] **Task 5: Layer 4 (Dual Stdio + SSE FastMCP Server)** -> Configured `--transport sse --port 8765` for local LAN access (Ceibalita/n8n/Docker).
- [x] **Task 6: Layer 5 (Smart Antipattern Watcher)** -> Built reactive daemon (`--watch`) and MCP scanner for critical bug prevention.
- [x] **Task 7: Benchmark Verification** -> 100% HitRate@3, 1.000 MRR, 68ms cold latency, <0.001ms RAM cache.
