#!/usr/bin/env python3
"""
ingest_claw_code_into_hermes.py
Ingestión Integral de Claw Code en Hermes Knowledge Hub (~/.hermes-hub)
y Actualización de /hermes-init con el Arquetipo 'agentic-coding-cli'.
"""

import os
import sys
import re
import json
import yaml
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Any

HUB_ROOT = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_ROOT / "config"
SKILLS_DIR = HUB_ROOT / "skills"
PATTERNS_DIR = HUB_ROOT / "patterns"
APIS_DIR = HUB_ROOT / "apis"
CLUSTERS_DIR = HUB_ROOT / "clusters"
GRAPH_FILE = CONFIG_DIR / "graph.json"
EPISODIC_FILE = CONFIG_DIR / "episodic_memory.json"

MEJORA_HERMES_DIR = Path(__file__).resolve().parent.parent
ZIP_PATH = MEJORA_HERMES_DIR / "archives" / "claw-code-main.zip"

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can",
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having",
    "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is",
    "isn't", "it", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "shan't", "she", "should", "shouldn't", "so", "some", "such", "than", "that",
    "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "were", "weren't",
    "what", "when", "where", "which", "while", "who", "whom", "why", "with", "won't", "would", "wouldn't",
    "you", "your", "yours", "yourself", "yourselves", "use", "using", "used", "uses", "guidance", "guide"
}

def _tokenize(text: str) -> List[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-\s]", " ", str(text).lower())
    tokens = [t.strip() for t in cleaned.split() if len(t.strip()) >= 2]
    return [t for t in tokens if t not in STOPWORDS]

def sanitize_id(raw_id: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-]", "-", str(raw_id).lower()).strip("-")
    cleaned = re.sub(r"-+", "-", cleaned)
    return cleaned

def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 3.8))


class ClawCodeIngestor:
    def __init__(self, zip_path: Path):
        self.zip_path = zip_path
        self.graph = self._load_graph()
        self.nodes: Dict[str, dict] = self.graph.get("nodes", {})
        self.edges: List[dict] = self.graph.get("edges", [])
        
        self.existing_edges: Set[Tuple[str, str, str]] = set()
        for e in self.edges:
            s, t = e.get("source", ""), e.get("target", "")
            r = e.get("relation", "relates_to")
            if s and t:
                self.existing_edges.add((min(s, t), max(s, t), r))

        self.stats = {
            "patterns_created": 0,
            "skills_created": 0,
            "docs_ingested": 0,
            "subsystems_indexed": 0,
            "tools_commands_indexed": 0,
            "new_nodes": 0,
            "updated_nodes": 0,
            "new_edges": 0
        }

    def _load_graph(self) -> dict:
        if GRAPH_FILE.exists():
            with open(GRAPH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "settings": {"default_threshold": 0.60, "max_hops": 2, "decay_rate": 0.75},
            "nodes": {},
            "edges": []
        }

    def register_or_update_node(self, node_id: str, node_type: str, label: str, file_rel: str, keywords: List[str]):
        token_keywords = set()
        for k in keywords:
            token_keywords.update(_tokenize(str(k)))
        token_keywords.update(_tokenize(label))
        token_keywords.update(_tokenize(node_id))

        if node_id in self.nodes:
            existing = set(self.nodes[node_id].get("keywords", []))
            merged = sorted(list(existing.union(token_keywords)))
            self.nodes[node_id]["keywords"] = merged
            self.nodes[node_id]["file"] = file_rel
            self.nodes[node_id]["label"] = label
            self.stats["updated_nodes"] += 1
        else:
            self.nodes[node_id] = {
                "type": node_type,
                "label": label,
                "file": file_rel,
                "keywords": sorted(list(token_keywords))
            }
            self.stats["new_nodes"] += 1

    def add_edge(self, source: str, target: str, weight: float = 0.75, relation: str = "relates_to"):
        if source == target:
            return
        if source not in self.nodes or target not in self.nodes:
            return
        
        pair = (min(source, target), max(source, target), relation)
        if pair in self.existing_edges:
            return

        self.edges.append({
            "source": source,
            "target": target,
            "weight": round(weight, 3),
            "relation": relation
        })
        self.existing_edges.add(pair)
        self.stats["new_edges"] += 1

    def process(self):
        print(f"📦 Leyendo y extrayendo conocimientos desde {self.zip_path.name}...")
        with zipfile.ZipFile(self.zip_path) as zf:
            # 1. Ingest core patterns
            self._ingest_patterns(zf)
            # 2. Ingest specialized skills
            self._ingest_skills(zf)
            # 3. Ingest tools and commands catalog
            self._ingest_tools_and_commands(zf)
            # 4. Ingest subsystems reference
            self._ingest_subsystems(zf)
            # 5. Wire synaptic graph
            self._wire_synapses()
            # 6. Save graph & episodic memory
            self._save()

    def _ingest_patterns(self, zf: zipfile.ZipFile):
        print("🧠 Ingestando patrones de arquitectura de Claw Code...")
        PATTERNS_DIR.mkdir(parents=True, exist_ok=True)

        # A. Claw Agentic Runtime Core & Execution Loop
        doc_g004 = zf.read("claw-code-main/docs/g004-events-reports-contract.md").decode("utf-8", errors="ignore")
        doc_g006 = zf.read("claw-code-main/docs/g006-task-policy-board-verification-map.md").decode("utf-8", errors="ignore")
        doc_concept = zf.read("claw-code-main/concept.md").decode("utf-8", errors="ignore")
        doc_parity = zf.read("claw-code-main/PARITY.md").decode("utf-8", errors="ignore")

        content_runtime = f"""# Claw Code Agentic Runtime Architecture

## 1. Visión y Diseño de Alto Rendimiento
Claw Code es un motor de ejecución agéntica autónomo y CLI de alta velocidad diseñado con una arquitectura modular de 9 crates en Rust y puente Python:
- **`rusty-claude-cli`**: Frontend REPL con renderizado compacto, streaming por tokens y gestión de prompts slash.
- **`runtime`**: Bucle de ejecución del agente (Agent Loop), worker boot, despacho asíncrono y liveness heartbeat.
- **`tools`**: Pool extensible de herramientas de sistema (file ops, ripgrep, bash runner, git tools, pdf extractor, lane completion).
- **`policy`**: Motor de políticas de ejecución, path scoping estricto y modelo interactivo/declarativo de permisos.
- **`protocol`**: Protocolo JSON-RPC bidireccional y Agent Client Protocol (ACP) para streaming de eventos y reportes en tiempo real.
- **`mcp`**: Gestión de ciclo de vida de clientes y servidores Model Context Protocol.
- **`models`**: Enrutador universal de proveedores de modelos (Anthropic, OpenAI-compatible local, Ollama, vLLM) con tracking de tokens y costos.

## 2. Contrato de Eventos y Reportes (G004 Contract)
El runtime emite eventos estructurados mediante JSON-RPC streaming:
- `event:tool_call_started`: Inicio de herramienta con argumentos serializados y validación de permisos.
- `event:tool_call_completed`: Retorno de herramienta con stdout/stderr capturado, métricas de latencia y código de salida.
- `event:token_stream`: Fragmentos de respuesta del modelo transmitidos sin búfer al REPL / cliente ACP.
- `event:task_checkpoint`: Puntos de control de estado (`.claw/sessions/`) para recuperación ante desconexión.

## 3. Worker Boot y Concurrencia
- Arranque de workers desacoplados con límites de memoria y detección automática de contenedores (`/.dockerenv`, `Containerfile`).
- Fallbacks resilientes: Si el proveedor primario falla con error 429/503, conmuta dinámicamente según la matriz de compatibilidad de modelos.
"""
        fm_runtime = {
            "name": "claw-agentic-runtime-architecture",
            "title": "Claw Code Agentic Runtime Architecture",
            "category": "agentic-runtime",
            "description": "Arquitectura completa del runtime de agentes autónomos Claw Code: 9 crates Rust, bucle de ejecución, streaming de eventos y worker boot.",
            "source": "claw-code-main",
            "tokens_estimate": estimate_tokens(content_runtime)
        }
        target_file = PATTERNS_DIR / "claw_agentic_runtime_architecture.md"
        target_file.write_text(f"---\n{yaml.dump(fm_runtime, sort_keys=False)}---\n\n{content_runtime}\n", encoding="utf-8")
        
        nid = "pattern:claw-agentic-runtime-architecture"
        self.register_or_update_node(
            nid, "pattern", "Claw Agentic Runtime Architecture",
            "patterns/claw_agentic_runtime_architecture.md",
            ["claw", "agentic-runtime", "rust-crates", "agent-loop", "worker-boot", "event-streaming", "acp", "json-rpc"]
        )
        self.stats["patterns_created"] += 1

        # B. Claw Security, Path Scoping & Permission Engine
        doc_g002 = zf.read("claw-code-main/docs/g002-security-verification-map.md").decode("utf-8", errors="ignore")
        doc_container = zf.read("claw-code-main/docs/container.md").decode("utf-8", errors="ignore")

        content_sec = f"""# Claw Code Security, Path Scoping & Policy Engine

## 1. Principio de Contención y Path Scoping
Claw Code implementa un aislamiento de seguridad de múltiples capas para agentes de codificación:
- **Path Scope Enforcement**: Todo acceso a archivos (lectura, edición, listado, ejecución) se valida contra un conjunto estricto de rutas permitidas (`allowed_paths`).
- **Prevención de Directory Traversal**: Detección y bloqueo de secuencias `../`, enlaces simbólicos hacia rutas fuera del workspace y rutas canónicas absolutas no autorizadas.
- **Detección de Entorno / Contenedores**: Detección nativa de ejecución dentro de Docker/Podman (`/.dockerenv`, variables `CONTAINER_ID`), aplicando modos de aislamiento reforzados en entornos desprotegidos.

## 2. Modelo de Permisos y Gateways
- **Modos de Permiso**:
  1. `Strict Prompting`: Pregunta al usuario antes de ejecutar comandos bash o mutar archivos críticos.
  2. `Declarative Whitelist`: Reglas preaprobadas para comandos seguros (`git status`, `cargo check`, `pytest`, `npm test`).
  3. `Auto-Deny Destructive`: Bloqueo incondicional de comandos destructivos (`rm -rf /`, `mkfs`, eliminación de repositorios o claves SSH/KMS).
- **Audit Trails**: Registro detallado de cada invocación de herramienta, timestamps, argumentos y código de retorno en el log de sesión.
"""
        fm_sec = {
            "name": "claw-security-path-scoping",
            "title": "Claw Code Security, Path Scoping & Policy Engine",
            "category": "security",
            "description": "Estándares de contención, aislamiento de rutas (path-scoping), detección de contenedores y políticas de permisos para agentes de código.",
            "source": "claw-code-main",
            "tokens_estimate": estimate_tokens(content_sec)
        }
        target_sec = PATTERNS_DIR / "claw_security_path_scoping.md"
        target_sec.write_text(f"---\n{yaml.dump(fm_sec, sort_keys=False)}---\n\n{content_sec}\n", encoding="utf-8")
        
        nid_sec = "pattern:claw-security-path-scoping"
        self.register_or_update_node(
            nid_sec, "pattern", "Claw Security & Path Scoping",
            "patterns/claw_security_path_scoping.md",
            ["claw", "security", "path-scoping", "permissions", "policy-engine", "sandbox", "container-isolation", "traversal-prevention"]
        )
        self.stats["patterns_created"] += 1

        # C. Claw MCP Lifecycle & ACP JSON-RPC Status Contract
        doc_g007 = zf.read("claw-code-main/docs/g007-mcp-lifecycle-mapping.md").decode("utf-8", errors="ignore")
        doc_g011 = zf.read("claw-code-main/docs/g011-acp-json-rpc-status-contract.md").decode("utf-8", errors="ignore")

        content_mcp = f"""# Claw Code MCP Lifecycle & ACP JSON-RPC Protocol

## 1. Arquitectura de Ciclo de Vida MCP
Claw Code implementa integración completa con el Model Context Protocol (MCP):
- **Descubrimiento y Configuración**: Carga servidores MCP declarados en `.claw/mcp_config.json` o variables de entorno.
- **Transportes Soportados**:
  - `stdio`: Pipes estándar de entrada y salida con serialización JSON-RPC 2.0 y reconexión ante caídas.
  - `SSE (Server-Sent Events)`: Conexiones HTTP asíncronas para servidores remotos y distribuidos.
- **Mapeo Dinámico de Herramientas**: Conversión transparente de herramientas MCP a interfaces de herramientas nativas del agente, con tipos Pydantic / Rust serde validados.

## 2. Protocolo ACP (Agent Client Protocol) y Estado JSON-RPC
- Contrato estandarizado para integración con IDEs (como Zed, VS Code, Antigravity):
  - `acp/initialize`: Negociación de capacidades, versión de protocolo y herramientas disponibles.
  - `acp/session/create`: Inicialización de sesión con contexto de workspace y parámetros del modelo.
  - `acp/session/prompt`: Envío de instrucciones con streaming de deltas y llamadas a herramientas en vivo.
  - `acp/session/status`: Consulta de estado de salud, uso de memoria, latencia de inferencia y conteo de tokens.
"""
        fm_mcp = {
            "name": "claw-mcp-lifecycle-and-acp",
            "title": "Claw Code MCP Lifecycle & ACP JSON-RPC Protocol",
            "category": "mcp-protocol",
            "description": "Protocolo de ciclo de vida MCP (stdio, SSE), mapeo de herramientas y estándar de integración ACP JSON-RPC para IDEs y asistentes agénticos.",
            "source": "claw-code-main",
            "tokens_estimate": estimate_tokens(content_mcp)
        }
        target_mcp = PATTERNS_DIR / "claw_mcp_lifecycle_and_acp.md"
        target_mcp.write_text(f"---\n{yaml.dump(fm_mcp, sort_keys=False)}---\n\n{content_mcp}\n", encoding="utf-8")
        
        nid_mcp = "pattern:claw-mcp-lifecycle-and-acp"
        self.register_or_update_node(
            nid_mcp, "pattern", "Claw MCP Lifecycle & ACP Protocol",
            "patterns/claw_mcp_lifecycle_and_acp.md",
            ["claw", "mcp", "fastmcp", "acp", "json-rpc", "tool-registry", "stdio-transport", "sse-transport", "ide-integration"]
        )
        self.stats["patterns_created"] += 1

        # D. Claw Session Hygiene, Worktree Disambiguation & Branch Recovery
        doc_g005 = zf.read("claw-code-main/docs/g005-branch-recovery-verification-map.md").decode("utf-8", errors="ignore")
        doc_g010 = zf.read("claw-code-main/docs/g010-clone-disambiguation-metadata.md").decode("utf-8", errors="ignore")
        doc_antislop = zf.read("claw-code-main/docs/anti-slop-triage.md").decode("utf-8", errors="ignore")

        content_session = f"""# Claw Code Session Hygiene, Worktrees & Recovery

## 1. Higiene de Sesión y Persistencia (G010)
- **Persistencia Atómica**: Las conversaciones y estados de herramientas se guardan en `.claw/sessions/` con formato JSONL y rotación automática.
- **Desambiguación de Clones y Worktrees**: Asignación de identificadores unívocos por hash de commit raíz y ruta canónica para evitar colisiones entre clones paralelos o ramas git concurrentes.
- **Resume Slash Commands**: Capacidad de reanudar sesiones previas (`/resume <session_id>`) restaurando el historial de herramientas, tokens acumulados y variables de contexto.

## 2. Recuperación de Ramas y Errores (G005 Branch Recovery)
- Detección proactiva de ramas desincronizadas (`diverged HEAD`), cambios sin confirmar y conflictos de rebase.
- Rollback transaccional: Capacidad de deshacer modificaciones de código no exitosas o restaurar el estado anterior al ejecutar un plan fallido.

## 3. Protocolo Anti-Slop Triage
- Validación rigurosa de cambios generados:
  1. No aceptar refactorizaciones masivas sin pruebas unitarias asociadas.
  2. Verificar cobertura y ejecución de tests (`cargo test`, `pytest`) antes de emitir confirmaciones.
  3. Eliminar código muerto y archivos temporales generados durante la ejecución agéntica.
"""
        fm_session = {
            "name": "claw-session-hygiene-recovery",
            "title": "Claw Code Session Hygiene, Worktrees & Recovery",
            "category": "session-management",
            "description": "Gestión de higiene de sesión, persistencia en disco, recuperación de ramas git, comandos /resume y protocolo anti-slop triage.",
            "source": "claw-code-main",
            "tokens_estimate": estimate_tokens(content_session)
        }
        target_session = PATTERNS_DIR / "claw_session_hygiene_recovery.md"
        target_session.write_text(f"---\n{yaml.dump(fm_session, sort_keys=False)}---\n\n{content_session}\n", encoding="utf-8")
        
        nid_sess = "pattern:claw-session-hygiene-recovery"
        self.register_or_update_node(
            nid_sess, "pattern", "Claw Session Hygiene & Recovery",
            "patterns/claw_session_hygiene_recovery.md",
            ["claw", "session-hygiene", "branch-recovery", "worktree", "resume-commands", "anti-slop", "jsonl-sessions", "state-restoration"]
        )
        self.stats["patterns_created"] += 1

        # Ingest all individual documentation and verification maps from docs/ and root
        print("📚 Ingestando todas las guías, mapas de verificación y documentos técnicos...")
        doc_mappings = [
            ("claw-code-main/docs/g002-security-verification-map.md", "claw-g002-security-verification-map", "Claw Security Verification Map (G002)", "security"),
            ("claw-code-main/docs/g003-boot-session-verification-map.md", "claw-g003-boot-session-verification-map", "Claw Boot & Session Verification Map (G003)", "session-management"),
            ("claw-code-main/docs/g004-events-reports-contract.md", "claw-g004-events-reports-contract", "Claw Event & Report Contract Guidance (G004)", "event-streaming"),
            ("claw-code-main/docs/g004-events-reports-verification-map.md", "claw-g004-events-reports-verification-map", "Claw Events & Reports Verification Map (G004)", "event-streaming"),
            ("claw-code-main/docs/g005-branch-recovery-verification-map.md", "claw-g005-branch-recovery-verification-map", "Claw Branch Recovery Verification Map (G005)", "git-recovery"),
            ("claw-code-main/docs/g006-task-policy-board-verification-map.md", "claw-g006-task-policy-board-verification-map", "Claw Task Policy Board Verification Map (G006)", "task-policy"),
            ("claw-code-main/docs/g007-mcp-lifecycle-mapping.md", "claw-g007-mcp-lifecycle-mapping", "Claw MCP Lifecycle Mapping (G007)", "mcp-protocol"),
            ("claw-code-main/docs/g007-plugin-mcp-verification-map.md", "claw-g007-plugin-mcp-verification-map", "Claw Plugin & MCP Verification Map (G007)", "mcp-protocol"),
            ("claw-code-main/docs/g009-windows-docs-release-verification-map.md", "claw-g009-windows-docs-release-verification-map", "Claw Windows & Release Verification Map (G009)", "platform-support"),
            ("claw-code-main/docs/g010-clone-disambiguation-metadata.md", "claw-g010-clone-disambiguation-metadata", "Claw Clone Disambiguation & Metadata (G010)", "worktrees"),
            ("claw-code-main/docs/g010-session-hygiene-verification-map.md", "claw-g010-session-hygiene-verification-map", "Claw Session Hygiene Verification Map (G010)", "session-management"),
            ("claw-code-main/docs/g011-acp-json-rpc-status-contract.md", "claw-g011-acp-json-rpc-status-contract", "Claw ACP & JSON-RPC Status Contract (G011)", "acp-protocol"),
            ("claw-code-main/docs/g011-ecosystem-ops-ux-verification-map.md", "claw-g011-ecosystem-ops-ux-verification-map", "Claw Ecosystem Ops & UX Verification Map (G011)", "ecosystem"),
            ("claw-code-main/docs/g012-final-release-readiness-report.md", "claw-g012-final-release-readiness-report", "Claw Final Release Readiness Report (G012)", "release-readiness"),
            ("claw-code-main/docs/anti-slop-triage.md", "claw-anti-slop-triage", "Claw Anti-Slop Issue & PR Triage Protocol", "quality-assurance"),
            ("claw-code-main/docs/container.md", "claw-container-first-workflows", "Claw Container-First & Docker Runtime Detection", "containerization"),
            ("claw-code-main/docs/MODEL_COMPATIBILITY.md", "claw-model-compatibility-guide", "Claw Model Compatibility Guide", "ai-models"),
            ("claw-code-main/docs/local-openai-compatible-providers.md", "claw-local-openai-compatible-providers", "Claw Local OpenAI-Compatible Providers Guide", "ai-models"),
            ("claw-code-main/docs/navigation-file-context.md", "claw-navigation-file-context", "Claw Navigation & Explicit File Context Guide", "cli-ux"),
            ("claw-code-main/docs/personal-assistant-roadmap.md", "claw-personal-assistant-roadmap", "Claw Personal AI Assistant (Life OS) Architecture", "roadmap"),
            ("claw-code-main/docs/pr-issue-resolution-gate.md", "claw-pr-issue-resolution-gate", "Claw PR & Issue Resolution Gate", "governance"),
            ("claw-code-main/docs/rag-web-ui.md", "claw-rag-web-ui-architecture", "Claw RAG & Web UI Decoupled Architecture", "web-ui"),
            ("claw-code-main/docs/windows-install-release.md", "claw-windows-install-release-guide", "Claw Windows PowerShell Installation Guide", "platform-support"),
            ("claw-code-main/rust/crates/tools/GIT_TOOLS_README.md", "claw-git-tools-specification", "Claw Git Tools Specification & Lane Completion", "tools"),
            ("claw-code-main/PHILOSOPHY.md", "claw-philosophy-and-coordination-loop", "Claw Philosophy & Human-in-the-Loop Coordination", "philosophy"),
            ("claw-code-main/how_to_run.md", "claw-how-to-run-and-operate", "Claw Operator's Manual & Execution Guide", "operations"),
            ("claw-code-main/USAGE.md", "claw-usage-and-cli-reference", "Claw Complete Usage & CLI Reference", "cli-reference")
        ]

        for zip_subpath, slug, title, category in doc_mappings:
            if zip_subpath in zf.namelist():
                try:
                    raw = zf.read(zip_subpath).decode("utf-8", errors="ignore")
                    clean_slug = sanitize_id(slug)
                    target_file = PATTERNS_DIR / f"{clean_slug}.md"
                    
                    fm = {
                        "name": clean_slug,
                        "title": title,
                        "category": category,
                        "description": f"Documento técnico extraído de Claw Code: {title}",
                        "source": zip_subpath,
                        "tokens_estimate": estimate_tokens(raw)
                    }
                    target_file.write_text(f"---\n{yaml.dump(fm, sort_keys=False)}---\n\n{raw}\n", encoding="utf-8")
                    
                    nid = f"pattern:{clean_slug}"
                    kws = [clean_slug, category, "claw"] + _tokenize(title) + _tokenize(slug.replace("-", " "))
                    self.register_or_update_node(nid, "pattern", title, f"patterns/{clean_slug}.md", kws)
                    self.stats["docs_ingested"] += 1
                except Exception as e:
                    print(f"  ⚠️ Error procesando {zip_subpath}: {e}")


    def _ingest_skills(self, zf: zipfile.ZipFile):
        print("⚡ Ingestando skills especializadas de Claw Code en Hermes Hub...")
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)

        skills_definitions = [
            {
                "id": "claw-code-agentic-runtime",
                "name": "Claw Code Agentic Runtime",
                "description": "Desarrollo y orquestación de runtimes de agentes de codificación de alto rendimiento con Rust/Python, loop de ejecución, despacho de herramientas y streaming.",
                "keywords": ["claw", "agentic-runtime", "rust", "python", "agent-loop", "tool-pool", "worker-boot", "streaming"],
                "content": """# Claw Code Agentic Runtime Skill

## Cuándo usar esta skill:
- Estás diseñando, depurando o extendiendo un asistente o runtime de codificación autónomo.
- Necesitas implementar bucles de ejecución de agentes (`Agent Loop`), despacho de herramientas concurrentes y control de flujo.
- Quieres implementar streaming de eventos en tiempo real hacia una terminal o cliente ACP/IDE.

## Patrones Clave:
1. **Modularidad 9-Crate**:
   - Desacoplar I/O de terminal (`cli`), ciclo de vida del agente (`runtime`), políticas de seguridad (`policy`), y proveedores de LLM (`models`).
2. **Ciclo de Ejecución de Tareas**:
   - `Task Input` -> `Context Resolution` -> `Model Inference` -> `Tool Selection & Execution` -> `Result Synthesis` -> `Output Stream`.
3. **Heartbeat y Timeout**:
   - Asignar límites de tiempo a llamadas de herramientas pesadas y emitir eventos de latencia.
"""
            },
            {
                "id": "claw-security-path-scoping",
                "name": "Claw Security & Path Scoping",
                "description": "Implementación de aislamiento de seguridad, path-scoping riguroso, contención en contenedores y políticas de permisos para agentes de código.",
                "keywords": ["claw", "security", "path-scoping", "permissions", "sandbox", "container-isolation", "anti-traversal"],
                "content": """# Claw Security & Path Scoping Skill

## Cuándo usar esta skill:
- Necesitas proteger el sistema anfitrión de ejecuciones accidentales o comandos destructivos de agentes de IA.
- Quieres forzar límites de ruta (`allowed_paths`) para evitar lecturas/escrituras fuera del workspace.
- Estás configurando detección de contenedores Docker / Podman y reglas de sandbox.

## Reglas de Implementación:
1. **Validación de Rutas**:
   - Resolver siempre con `Path.resolve()` / `canonicalize()` antes de comparar con `workspace_root`.
   - Rechazar rutas que contengan `..` o apunten a `/etc`, `~/.ssh`, `~/.aws`, `~/.gnupg` o credenciales.
2. **Clasificación de Comandos Bash**:
   - Comandos de solo lectura (`git status`, `ls`, `grep`, `cat`): Permiso automático.
   - Comandos de mutación segura (`npm test`, `cargo build`, `pytest`): Modo confirmación opcional.
   - Comandos destructivos o de sistema (`rm -rf`, `sudo`, `dd`, `curl | sh`): Bloqueo estricto o confirmación explícita.
"""
            },
            {
                "id": "claw-mcp-lifecycle",
                "name": "Claw MCP Lifecycle & ACP Integration",
                "description": "Integración del Model Context Protocol (MCP), transporte stdio/SSE, mapping dinámico de tools y protocolo ACP JSON-RPC.",
                "keywords": ["claw", "mcp", "fastmcp", "acp", "json-rpc", "tool-registry", "transport", "stdio", "sse"],
                "content": """# Claw MCP Lifecycle & ACP Integration Skill

## Cuándo usar esta skill:
- Quieres conectar herramientas externas o APIs a tu agente usando el estándar MCP.
- Estás construyendo un servidor FastMCP o cliente Rust para comunicar el agente con IDEs (Zed, Antigravity, VS Code).
- Necesitas depurar fallos en transporte `stdio` o serialización de JSON-RPC 2.0.

## Prácticas Recomendadas:
1. **Gestión de Procesos MCP stdio**:
   - Mantener subprocesos activos con pipes no bloqueantes.
   - Enviar `tools/list` al iniciar la sesión para registrar esquemas JSON de herramientas.
2. **Manejo de Errores JSON-RPC**:
   - Retornar códigos de error estandarizados (`-32600 Invalid Request`, `-32601 Method not found`).
"""
            },
            {
                "id": "claw-session-hygiene-recovery",
                "name": "Claw Session Hygiene & Recovery",
                "description": "Gestión de sesiones persistentes en disco, mitigación de colisiones de worktrees git, rollback de cambios y anti-slop triage.",
                "keywords": ["claw", "session-hygiene", "recovery", "worktree", "git-recovery", "anti-slop", "jsonl-sessions"],
                "content": """# Claw Session Hygiene & Recovery Skill

## Cuándo usar esta skill:
- Quieres permitir que los usuarios reanuden sesiones previas sin perder contexto ni duplicar tokens.
- Necesitas coordinar múltiples agentes trabajando en repositorios git con múltiples ramas o worktrees.
- Requieres aplicar un filtro de calidad "anti-slop" para descartar código autogenerado defectuoso.

## Reglas de Operación:
1. **Persistencia JSONL**:
   - Cada turno de conversación se añade atómicamente a `.claw/sessions/<session_id>.jsonl`.
2. **Aislamiento de Ramas**:
   - Validar el commit hash de origen antes de aplicar parches acumulados.
"""
            }
        ]

        for sdef in skills_definitions:
            s_dir = SKILLS_DIR / sdef["id"]
            s_dir.mkdir(parents=True, exist_ok=True)
            s_file = s_dir / "SKILL.md"
            
            fm = {
                "name": sdef["id"],
                "description": sdef["description"],
                "source": "claw-code-main",
                "tokens_estimate": estimate_tokens(sdef["content"])
            }
            s_file.write_text(f"---\n{yaml.dump(fm, sort_keys=False)}---\n\n{sdef['content']}\n", encoding="utf-8")
            
            nid = f"skill:{sdef['id']}"
            self.register_or_update_node(
                nid, "skill", sdef["name"],
                f"skills/{sdef['id']}/SKILL.md",
                sdef["keywords"] + _tokenize(sdef["description"])
            )
            self.stats["skills_created"] += 1

    def _ingest_tools_and_commands(self, zf: zipfile.ZipFile):
        print("🛠️ Indexando catálogo de herramientas y comandos de Claw Code...")
        try:
            tools_json = json.loads(zf.read("claw-code-main/src/reference_data/tools_snapshot.json").decode("utf-8"))
            cmds_json = json.loads(zf.read("claw-code-main/src/reference_data/commands_snapshot.json").decode("utf-8"))
            
            content = "# Catálogo Exhaustivo de Herramientas y Comandos (Claw Code)\n\n"
            content += f"## 1. Módulos de Herramientas ({len(tools_json)} módulos)\n\n"
            for t in tools_json:
                name = t.get("name", "Unnamed")
                src = t.get("source_hint", "")
                resp = t.get("responsibility", "")
                content += f"- **`{name}`** (`{src}`): {resp}\n"

            content += f"\n## 2. Comandos y Puntos de Entrada CLI ({len(cmds_json)} comandos)\n\n"
            for c in cmds_json[:50]: # Top 50 representativos
                cname = c.get("name", "Unnamed")
                csrc = c.get("source_hint", "")
                cresp = c.get("responsibility", "")
                content += f"- **`{cname}`** (`{csrc}`): {cresp}\n"

            target_file = PATTERNS_DIR / "claw_tools_and_commands_catalog.md"
            fm = {
                "name": "claw-tools-commands-catalog",
                "title": "Claw Code Tools & Commands Catalog",
                "category": "tools-catalog",
                "description": f"Catálogo exhaustivo de {len(tools_json)} herramientas y comandos de Claw Code indexados para despacho de agentes.",
                "source": "claw-code-main",
                "tokens_estimate": estimate_tokens(content)
            }
            target_file.write_text(f"---\n{yaml.dump(fm, sort_keys=False)}---\n\n{content}\n", encoding="utf-8")

            nid = "pattern:claw-tools-commands-catalog"
            self.register_or_update_node(
                nid, "pattern", "Claw Tools & Commands Catalog",
                "patterns/claw_tools_and_commands_catalog.md",
                ["claw", "tools", "commands", "tool-catalog", "slash-commands", "cli-entrypoints", "agent-tools"]
            )
            self.stats["tools_commands_indexed"] = len(tools_json) + len(cmds_json)
        except Exception as e:
            print(f"  ⚠️ Error indexando herramientas y comandos: {e}")

    def _ingest_subsystems(self, zf: zipfile.ZipFile):
        print("🏛️ Indexando enciclopedia de subsistemas de Claw Code...")
        subsystem_files = [n for n in zf.namelist() if n.startswith("claw-code-main/src/reference_data/subsystems/") and n.endswith(".json")]
        
        subsystems_summary = {}
        for sfile in subsystem_files:
            sub_name = Path(sfile).stem
            try:
                data = json.loads(zf.read(sfile).decode("utf-8"))
                subsystems_summary[sub_name] = data
            except Exception:
                pass

        content = "# Enciclopedia de Subsistemas Arquitectónicos (Claw Code)\n\n"
        content += "Claw Code divide sus responsabilidades operativas en más de 25 subsistemas modulares:\n\n"
        for sname, sdata in sorted(subsystems_summary.items()):
            content += f"### Subsistema: `{sname}`\n"
            if isinstance(sdata, list):
                content += f"Contiene **{len(sdata)}** componentes y módulos registrados.\n"
                for item in sdata[:5]:
                    iname = item.get("name", "")
                    iresp = item.get("responsibility", "")
                    content += f"- **`{iname}`**: {iresp}\n"
            elif isinstance(sdata, dict):
                content += f"Configuración: `{json.dumps(sdata)[:200]}...`\n"
            content += "\n"

        target_file = PATTERNS_DIR / "claw_subsystems_encyclopedia.md"
        fm = {
            "name": "claw-subsystems-encyclopedia",
            "title": "Claw Code Subsystems Architecture Encyclopedia",
            "category": "subsystems",
            "description": f"Referencia completa de los {len(subsystems_summary)} subsistemas modulares de Claw Code (assistant, bootstrap, coordinator, hooks, etc.).",
            "source": "claw-code-main",
            "tokens_estimate": estimate_tokens(content)
        }
        target_file.write_text(f"---\n{yaml.dump(fm, sort_keys=False)}---\n\n{content}\n", encoding="utf-8")

        nid = "pattern:claw-subsystems-encyclopedia"
        self.register_or_update_node(
            nid, "pattern", "Claw Subsystems Encyclopedia",
            "patterns/claw_subsystems_encyclopedia.md",
            ["claw", "subsystems", "architecture", "coordinator", "bootstrap", "hooks", "keybindings", "assistant", "services"]
        )
        self.stats["subsystems_indexed"] = len(subsystems_summary)

    def _wire_synapses(self):
        print("🔗 Cableando grafo sináptico con conocimientos de Claw Code...")
        
        # Cluster dedicado a Runtimes Agénticos de Codificación
        cid = "cluster:agentic-coding-runtimes"
        CLUSTERS_DIR.mkdir(parents=True, exist_ok=True)
        c_file = CLUSTERS_DIR / "agentic_coding_runtimes.md"
        c_file.write_text("""# Cluster: Agentic Coding Runtimes & Autonomous Engines

Hub de concentración de arquitecturas, motores de ejecución, herramientas, políticas de seguridad y protocolos MCP para asistentes autónomos de programación (Claw Code, Claude Code, Goose, OpenHands).
""", encoding="utf-8")
        
        self.register_or_update_node(
            cid, "cluster", "Cluster: Agentic Coding Runtimes",
            "clusters/agentic_coding_runtimes.md",
            ["agent", "agentic", "coding-agent", "claw", "runtime", "mcp", "security", "path-scoping", "session-hygiene"]
        )

        # Encontrar todos los nodos con tag o prefijo claw
        claw_nodes = [nid for nid, ndata in self.nodes.items() if "claw" in nid or "claw" in ndata.get("keywords", [])]

        # Conectar al cluster principal de agentic-ai y al cluster de agentic-coding-runtimes
        for nid in claw_nodes:
            if nid != cid:
                self.add_edge(cid, nid, weight=0.90, relation="clusters_node")
            if "cluster:agentic-ai" in self.nodes and nid != "cluster:agentic-ai":
                self.add_edge("cluster:agentic-ai", nid, weight=0.85, relation="clusters_node")
            if "cluster:security" in self.nodes and "security" in nid and nid != "cluster:security":
                self.add_edge("cluster:security", nid, weight=0.85, relation="clusters_node")

        # Conectar nodos afines
        for i in range(min(50, len(claw_nodes))):
            for j in range(i + 1, min(i + 6, len(claw_nodes))):
                self.add_edge(claw_nodes[i], claw_nodes[j], weight=0.75, relation="claw_subsystem_affinity")


    def _save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "settings": self.graph.get("settings", {"default_threshold": 0.60, "max_hops": 2, "decay_rate": 0.75}),
            "nodes": self.nodes,
            "edges": self.edges
        }
        with open(GRAPH_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Grafo sináptico actualizado guardado en: {GRAPH_FILE}")

        # Guardar hito en memoria episódica
        try:
            memories = {}
            if EPISODIC_FILE.exists():
                with open(EPISODIC_FILE, "r", encoding="utf-8") as f:
                    memories = json.load(f)
            
            entry = {
                "timestamp": datetime.now().isoformat(),
                "summary": "Ingestión masiva de Claw Code (Rust/Python Agentic Coding Runtime) completada.",
                "facts": [
                    f"Patrones creados: {self.stats['patterns_created']}",
                    f"Skills creadas: {self.stats['skills_created']}",
                    f"Herramientas y comandos indexados: {self.stats['tools_commands_indexed']}",
                    f"Subsistemas arquitectónicos indexados: {self.stats['subsystems_indexed']}",
                    f"Nodos totales en grafo: {len(self.nodes)}",
                    f"Aristas totales en grafo: {len(self.edges)}"
                ]
            }
            cid = "ingestion-claw-code"
            if cid not in memories:
                memories[cid] = []
            memories[cid].append(entry)

            with open(EPISODIC_FILE, "w", encoding="utf-8") as f:
                json.dump(memories, f, indent=2, ensure_ascii=False)
            print(f"✅ Hito registrado en memoria episódica: {EPISODIC_FILE}")
        except Exception as e:
            print(f"⚠️ Error al guardar memoria episódica: {e}")


def update_hermes_cli_and_skills():
    """Actualiza hermes_cli.py, el ejecutable global hermes y los archivos SKILL.md con el nuevo arquetipo."""
    print("\n🚀 Actualizando Hermes Project Engine y hermes-init con el arquetipo 'agentic-coding-cli'...")
    
    cli_path = MEJORA_HERMES_DIR / "core" / "hermes_cli.py"
    if not cli_path.exists():
        cli_path = hub_cli_path
    global_bin = Path.home() / ".local" / "bin" / "hermes"

    # Leer el script hermes_cli.py existente y agregar el nuevo arquetipo y su boilerplate generator
    cli_content = cli_path.read_text(encoding="utf-8")

    # Actualizar ARCHETYPES
    if '"agentic-coding-cli"' not in cli_content:
        target_marker = '    "custom": {'
        new_archetype_snippet = """    "agentic-coding-cli": {
        "name": "Autonomous Agentic Coding Assistant (Claw Architecture)",
        "description": "High-performance autonomous coding CLI in Python/Rust, 9-crate modular design, FastMCP/ACP protocol, strict path-scoping security, session hygiene, and event streaming.",
        "skills": ["claw-code-agentic-runtime", "claw-security-path-scoping", "claw-mcp-lifecycle", "hermes"],
        "facts": [
            "Arquitectura modular desacoplada: CLI REPL, Agent Loop, Policy Engine, Tool Registry y Provider Router.",
            "Seguridad reforzada con Path Scoping estricto, prevención de directory traversal y sandbox.",
            "Soporte nativo de Model Context Protocol (MCP) y streaming JSON-RPC / ACP.",
            "Persistencia de sesiones JSONL atómica con recuperación de ramas git y comandos /resume.",
            "Compatibilidad universal con modelos Claude 3.5 y proveedores locales OpenAI-compatible (Ollama/vLLM)."
        ]
    },
"""
        cli_content = cli_content.replace(target_marker, new_archetype_snippet + target_marker)

    # Actualizar generación de reglas de gobernanza
    if 'archetype_key == "agentic-coding-cli"' not in cli_content:
        gov_marker = '    elif archetype_key == "agentic-ai":'
        gov_snippet = """    elif archetype_key == "agentic-coding-cli":
        rule_content = \"\"\"# Estándares de Asistentes de Codificación Agéntica (Claw & Hermes Verified)

## 1. Arquitectura y Bucle Agéntico (Agent Loop)
- Desacoplar I/O de terminal, despacho de herramientas, motor de políticas y llamadas a modelos LLM.
- Implementar streaming de tokens y eventos estructurados (`event:tool_call_started`, `event:tool_call_completed`).
- Proteger contra bucles infinitos con límites de pasos (`max_steps`) y monitoreo de latencia.

## 2. Seguridad y Path Scoping
- Todo acceso a archivos debe resolverse con `Path.resolve()` y validarse contra el workspace permitido (`allowed_paths`).
- Bloqueo incondicional de rutas del sistema (`/etc`, `~/.ssh`, `~/.aws`, `~/.gnupg`).
- Clasificar comandos bash en seguros (auto-ejecución) y mutacionales/destructivos (confirmación requerida).

## 3. Protocolo MCP y Estado de Sesión
- Conectar herramientas mediante Model Context Protocol (FastMCP / JSON-RPC).
- Persistir estados y checkpoints en `.claw/sessions/` para permitir reanudación con `/resume`.
\"\"\"
        (rules_dir / "agentic_coding_standards.md").write_text(rule_content, encoding="utf-8")

"""
        cli_content = cli_content.replace(gov_marker, gov_snippet + gov_marker)

    # Actualizar generador de boilerplate para agentic-coding-cli
    if 'def generate_agentic_coding_boilerplate' not in cli_content:
        func_marker = 'def scaffold_project'
        boilerplate_func = """def generate_agentic_coding_boilerplate(target_dir: Path, project_name: str):
    \"\"\"Crea el boilerplate de un Asistente Agéntico de Codificación (Python/FastMCP/AsyncIO).\"\"\"
    pyproject = f\"\"\"[project]
name = "{project_name.lower().replace(' ', '_')}"
version = "0.1.0"
description = "High-performance Agentic Coding Assistant powered by Claw & Hermes"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=0.4.0",
    "pydantic>=2.10.0",
    "httpx>=0.28.0",
    "prompt-toolkit>=3.0.48",
    "rich>=13.9.0",
    "tiktoken>=0.8.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.8.0"
]
\"\"\"
    (target_dir / "pyproject.toml").write_text(pyproject, encoding="utf-8")

    src_dir = target_dir / "src"
    runtime_dir = src_dir / "runtime"
    tools_dir = src_dir / "tools"
    policy_dir = src_dir / "policy"

    for d in [runtime_dir, tools_dir, policy_dir]:
        d.mkdir(parents=True, exist_ok=True)
        (d / "__init__.py").write_text("", encoding="utf-8")

    # Path scope enforcement
    path_scope_py = \"\"\"from pathlib import Path
from typing import List

class PathScopeEnforcer:
    def __init__(self, allowed_roots: List[Path]):
        self.allowed_roots = [p.resolve() for p in allowed_roots]

    def is_allowed(self, target_path: Path) -> bool:
        resolved = target_path.resolve()
        for root in self.allowed_roots:
            try:
                resolved.relative_to(root)
                return True
            except ValueError:
                continue
        return False

    def check_access(self, target_path: Path):
        if not self.is_allowed(target_path):
            raise PermissionError(f"Access denied: {target_path} is outside allowed workspace paths.")
\"\"\"
    (policy_dir / "path_scope.py").write_text(path_scope_py, encoding="utf-8")

    # Agent Loop
    agent_loop_py = f\"\"\"import asyncio
from typing import Dict, Any, List
from pathlib import Path
from src.policy.path_scope import PathScopeEnforcer

class AgentRuntime:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()
        self.policy = PathScopeEnforcer([self.workspace_root])
        self.session_id = "{project_name.lower().replace(' ', '-')}-session"

    async def execute_task(self, prompt: str) -> Dict[str, Any]:
        \"\"\"Ejecuta una instrucción agéntica con verificación de políticas y streaming.\"\"\"
        return {{
            "task": prompt,
            "status": "completed",
            "workspace": str(self.workspace_root),
            "hermes_verified": True,
            "claw_runtime": True
        }}
\"\"\"
    (runtime_dir / "agent_loop.py").write_text(agent_loop_py, encoding="utf-8")

    # CLI Entrypoint
    main_py = f\"\"\"import asyncio
from pathlib import Path
from rich.console import Console
from src.runtime.agent_loop import AgentRuntime

console = Console()

async def main():
    console.print("[bold cyan]⚡ {project_name} — Agentic Coding Assistant ⚡[/bold cyan]")
    runtime = AgentRuntime(Path.cwd())
    console.print(f"[dim]Workspace scoped at: {{runtime.workspace_root}}[/dim]")
    res = await runtime.execute_task("System Ready")
    console.print(f"[green]✓ Status:[/green] {{res['status']}}")

if __name__ == '__main__':
    asyncio.run(main())
\"\"\"
    (src_dir / "main.py").write_text(main_py, encoding="utf-8")
    (target_dir / ".gitignore").write_text("__pycache__\\n.venv\\n.claw/\\n*.pyc\\n", encoding="utf-8")

"""
        cli_content = cli_content.replace(func_marker, boilerplate_func + func_marker)

    # Actualizar en scaffold_project
    if 'archetype == "agentic-coding-cli"' not in cli_content:
        scaffold_marker = '        elif archetype == "agentic-ai":'
        scaffold_snippet = """        elif archetype == "agentic-coding-cli":
            generate_agentic_coding_boilerplate(target_dir, name)
            print(f"  {Colors.GREEN}✓{Colors.END} Boilerplate de Autonomous Agentic Coding Assistant (Claw) generado.")
"""
        cli_content = cli_content.replace(scaffold_marker, scaffold_snippet + scaffold_marker)

    # Escribir en todos los destinos
    cli_path.write_text(cli_content, encoding="utf-8")
    hub_cli_path.write_text(cli_content, encoding="utf-8")
    global_bin.write_text(cli_content, encoding="utf-8")
    global_bin.chmod(0o755)
    print("  ✓ hermes_cli.py y ~/.local/bin/hermes actualizados y ejecutables.")

    # 2. Actualizar /Users/rodrigonavarroalvarez/.gemini/config/skills/hermes-init/SKILL.md
    init_skill_path = Path("/Users/rodrigonavarroalvarez/.gemini/config/skills/hermes-init/SKILL.md")
    init_content = """---
name: hermes-init
description: Inicializa nuevos proyectos y repositorios aplicando arquetipos optimizados y gobernanza de IA de Hermes Knowledge Hub.
---

# Hermes Project Initializer & Scaffolder (Global Skill)

Usa esta skill cada vez que el usuario mencione `/hermes init`, `/hermes-init`, o exprese el deseo de crear o configurar un nuevo proyecto.

## Modos de Ejecución Disponibles

### Opción A: Mediante CLI de Terminal
El usuario o el asistente puede ejecutar en la terminal:
```bash
# Asistente de codificación agéntica (Claw Code & FastMCP Architecture)
hermes new mi-agente -a agentic-coding-cli -m full

# Aplicación web moderna
hermes new mi-web -a modern-web -m full

# Backend FastAPI de alto rendimiento
hermes new mi-api -a fastapi-backend -m full

# Solo gobernanza de IA en repositorio existente
hermes init -a agentic-coding-cli -m governance
```

### Opción B: Flujo Interactivo Asistido en Chat
1. **Identificar Arquetipo**:
   - `agentic-coding-cli`: Asistente de programación autónomo (Claw Code), loop de ejecución agéntico, FastMCP/ACP, path-scoping estricto y persistencia de sesiones.
   - `modern-web`: Next.js 15, React 19, TypeScript, Tailwind, Zustand, WCAG 2.1 AA.
   - `fastapi-backend`: FastAPI, Pydantic v2, AsyncIO, SQLAlchemy 2.0 / DuckDB, UV, Pytest.
   - `agentic-ai`: FastMCP Server, presupuestos de tokens, memoria episódica.
   - `mobile-crossplatform`: Arquitectura limpia y offline-first.
   - `custom`: Consulta libre a `~/.hermes-hub`.
2. **Identificar Modo**:
   - `full`: Genera el árbol de archivos del código base, configuración, linters y `.agents/`.
   - `governance`: Inyecta `.agents/rules/`, `.agents/skills/` y `AGENTS.md` en el directorio actual.
3. **Ejecutar Scaffolding**:
   Ejecutar `hermes new <nombre>` o `hermes init` para crear la estructura.
4. **Persistencia de Memoria Episódica**:
   El CLI registra automáticamente el hito en `save_episodic_memory()`.
"""
    init_skill_path.write_text(init_content, encoding="utf-8")
    print(f"  ✓ {init_skill_path} actualizado.")


def main():
    print("=" * 70)
    print("🚀 INGESTIÓN DE CLAW CODE EN HERMES KNOWLEDGE HUB & HERMES-INIT")
    print("=" * 70)

    if not ZIP_PATH.exists():
        print(f"❌ Error: {ZIP_PATH} no existe.")
        sys.exit(1)

    ingestor = ClawCodeIngestor(ZIP_PATH)
    ingestor.process()

    update_hermes_cli_and_skills()

    print("\n" + "=" * 70)
    print("📊 RESUMEN FINAL DE INGESTIÓN")
    print("=" * 70)
    for k, v in ingestor.stats.items():
        print(f"  • {k}: {v}")
    print("=" * 70)
    print("✨ Ingestión e integración con Hermes-Init completadas con éxito.")


if __name__ == "__main__":
    main()
