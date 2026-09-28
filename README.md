# Hermes Ecosystem: Unified Hub & Improvements

Repositorio centralizado que unifica todas las mejoras, herramientas de investigación, motores de ingesta, arquitecturas y ecosistemas de skills para **Hermes Knowledge Hub** (`~/.hermes-hub`).

---

## 🏛️ Estructura del Ecosistema

```
mejora hermes/
├── core/                  # Motores de optimización Hebbiana, MCP server y CLI de Hermes
│   ├── optimizer.py       # Optimizador de contexto y poda sináptica
│   ├── mcp_server.py      # Servidor FastMCP para Antigravity e IDEs
│   ├── hermes_cli.py      # Interfaz CLI central de Hermes
│   └── tests/             # Suites de pruebas de plasticidad y eficiencia
│
├── research/              # Hermes Repo Research Loop (Adquisición de conocimiento GitHub)
│   ├── loop.py            # Orquestador del ciclo de investigación y consulta
│   ├── distill.py         # Motor de síntesis cognitiva con Google Gemini (fallback Claude/OpenAI)
│   ├── github_source.py   # Wrapper con control de rate limits de GitHub API
│   └── memory_store.py    # Integración dual: JSONL + Notas Obsidian en ~/.hermes-hub/patterns/
│
├── ingestion/             # Pipelines de ingesta masiva y enriquecimiento del Grafo
│   ├── ingest_all_uploaded_sources.py
│   ├── ingest_claw_code_into_hermes.py
│   ├── ingest_top_skills_to_hermes.py
│   ├── expand_massive_api_encyclopedia.py
│   └── synthesize_and_enrich_hermes.py
│
├── knowledge/             # Especificaciones arquitectónicas, grafos y benchmarks
│   ├── hermes_architecture.md
│   ├── hermes_kb.json
│   ├── structure.md
│   ├── benchmark.py
│   └── agent_definitions/
│
├── skills/                # Ecosistema consolidado de Skills para agentes
│   ├── anthropic_cybersecurity/
│   ├── n8n_skills/
│   └── community_skills/
│
├── automations/           # Workflows, servicios Docker y automatizaciones
│   ├── docker/
│   ├── n8n/
│   ├── services/
│   └── skills_manifest.json
│
├── loop_engine/           # Especificación y estado del bucle autónomo (Ralph Loop / Antigravity)
│   ├── PRD.md
│   ├── progress.txt
│   └── loop_instructions.txt
│
└── archives/              # Backups y fuentes comprimidas (zips, dmgs)
```

---

## 🚀 Comandos Rápidos

### 1. Investigar Repositorios y Extraer Patrones al Vault
```bash
python3 research/loop.py "distributed caching redis" --language python --n 3
```

### 2. Consultar la Memoria Persistente de Hermes
```bash
python3 research/loop.py --query-memory "fastapi"
```

### 3. Ejecutar Servidor MCP de Hermes
```bash
~/.hermes-hub/.venv/bin/python core/mcp_server.py
```

### 4. Validar Suite de Pruebas del Núcleo
```bash
~/.hermes-hub/.venv/bin/pytest core/tests/
```
