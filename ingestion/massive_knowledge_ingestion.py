#!/usr/bin/env python3
"""
massive_knowledge_ingestion.py - Ingestión Masiva de Conocimiento en Hermes Hub
Extrae skills y patrones de:
1. n8n-skills-main (15 skills de automatización y orquestación)
2. Anthropic Cybersecurity Skills (skills de seguridad, pentesting, mitigación)
3. Proyectos locales (Zorba Sports Next.js 15, RL_web, loop_investigation)
4. Patrones de élite de GitHub (LangGraph, Drizzle/Postgres, FastAPI, DevOps)
Y cablea el grafo sináptico en ~/.hermes-hub/config/graph.json.
"""

import os
import sys
import re
import json
import yaml
import zipfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Set, Tuple

HUB_ROOT = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_ROOT / "config"
SKILLS_DIR = HUB_ROOT / "skills"
PATTERNS_DIR = HUB_ROOT / "patterns"
ANTIPATTERNS_DIR = HUB_ROOT / "antipatterns"
GRAPH_FILE = CONFIG_DIR / "graph.json"

PROJECTS_DIR = Path("/Users/rodrigonavarroalvarez/Desktop/projects")


def _tokenize(text: str) -> List[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-\s]", " ", str(text).lower())
    return [t.strip() for t in cleaned.split() if len(t.strip()) >= 2]


def _parse_frontmatter(content: str) -> Tuple[dict, str]:
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
                return fm, body
            except Exception:
                pass
    return {}, content.strip()


def sanitize_id(raw_id: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-]", "-", raw_id.lower()).strip("-")
    cleaned = re.sub(r"-+", "-", cleaned)
    return cleaned


def save_markdown_file(target_path: Path, frontmatter: dict, body: str):
    target_path.parent.mkdir(parents=True, exist_ok=True)
    yaml_header = yaml.dump(frontmatter, sort_keys=False, default_flow_style=False)
    content = f"---\n{yaml_header}---\n\n{body}\n"
    target_path.write_text(content, encoding="utf-8")


class MassiveIngestor:
    def __init__(self):
        self.graph = self._load_current_graph()
        self.nodes: Dict[str, dict] = self.graph.get("nodes", {})
        self.edges: List[dict] = self.graph.get("edges", [])
        self.ingested_count = 0

    def _load_current_graph(self) -> dict:
        if GRAPH_FILE.exists():
            with open(GRAPH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "settings": {"default_threshold": 0.60, "max_hops": 2, "decay_rate": 0.75},
            "nodes": {},
            "edges": []
        }

    def register_node(self, node_id: str, node_type: str, label: str, file_rel: str, keywords: List[str]):
        token_keywords = set()
        for k in keywords:
            token_keywords.update(_tokenize(str(k)))
        token_keywords.update(_tokenize(label))
        token_keywords.update(_tokenize(node_id))

        self.nodes[node_id] = {
            "type": node_type,
            "label": label,
            "file": file_rel,
            "keywords": sorted(list(token_keywords))
        }
        self.ingested_count += 1

    def add_edge(self, source: str, target: str, weight: float = 0.85, relation: str = "relates_to"):
        # Check if edge already exists
        for e in self.edges:
            if e.get("source") == source and e.get("target") == target and e.get("relation") == relation:
                return
        self.edges.append({
            "source": source,
            "target": target,
            "weight": weight,
            "relation": relation
        })

    # =========================================================================
    # 1. INGESTIÓN DE N8N SKILLS
    # =========================================================================
    def ingest_n8n_skills(self):
        print("📦 Ingestando n8n Workflow Skills...")
        n8n_dir = PROJECTS_DIR / "n8n-skills-main" / "skills"
        if not n8n_dir.exists():
            print("⚠️ n8n skills dir not found")
            return

        for skill_dir in n8n_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            raw_content = skill_file.read_text(encoding="utf-8", errors="ignore")
            fm, body = _parse_frontmatter(raw_content)

            folder_name = skill_dir.name
            clean_id = sanitize_id(fm.get("id", folder_name))
            title = fm.get("title", fm.get("name", folder_name.replace("-", " ").title()))
            tags = fm.get("tags", ["n8n", "automation", "workflow", "integration"])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]

            rel_file = f"skills/n8n/{folder_name}.md"
            target_path = HUB_ROOT / rel_file

            frontmatter = {
                "id": clean_id,
                "title": title,
                "type": "skill",
                "category": "n8n_automation",
                "tags": tags,
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            save_markdown_file(target_path, frontmatter, body)

            node_key = f"skill_n8n_{clean_id.replace('-', '_')}"
            self.register_node(
                node_id=node_key,
                node_type="skill",
                label=f"n8n: {title}",
                file_rel=rel_file,
                keywords=tags + [clean_id, "n8n", "webhook", "automation", "workflow"]
            )
            # Connect to n8n cluster
            self.add_edge("cluster_n8n_automation", node_key, weight=0.90, relation="contains")

    # =========================================================================
    # 2. INGESTIÓN DE ANTHROPIC CYBERSECURITY SKILLS
    # =========================================================================
    def ingest_cybersecurity_skills(self):
        print("🛡️ Ingestando Cybersecurity & Security Architecture Skills...")
        zip_path = PROJECTS_DIR / "RL_web" / "Anthropic-Cybersecurity-Skills-main.zip"
        if not zip_path.exists():
            print("⚠️ Cybersecurity zip not found")
            return

        with zipfile.ZipFile(zip_path, 'r') as z:
            for item in z.infolist():
                if item.filename.endswith("SKILL.md"):
                    content = z.read(item.filename).decode('utf-8', errors='ignore')
                    fm, body = _parse_frontmatter(content)

                    # Extract folder name from path
                    parts = item.filename.split("/")
                    skill_folder = parts[-2] if len(parts) >= 2 else "sec_skill"

                    clean_id = sanitize_id(fm.get("id", skill_folder))
                    title = fm.get("title", fm.get("name", skill_folder.replace("-", " ").title()))
                    tags = fm.get("tags", ["cybersecurity", "security", "threat-modeling", "mitre"])
                    if isinstance(tags, str):
                        tags = [t.strip() for t in tags.split(",")]

                    rel_file = f"skills/cybersecurity/{skill_folder}.md"
                    target_path = HUB_ROOT / rel_file

                    frontmatter = {
                        "id": clean_id,
                        "title": title,
                        "type": "skill",
                        "category": "cybersecurity",
                        "tags": tags,
                        "status": "active",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    save_markdown_file(target_path, frontmatter, body)

                    node_key = f"skill_sec_{clean_id.replace('-', '_')}"
                    self.register_node(
                        node_id=node_key,
                        node_type="skill",
                        label=f"SecOps: {title}",
                        file_rel=rel_file,
                        keywords=tags + [clean_id, "cybersecurity", "security", "defense", "auth", "vulnerability"]
                    )
                    self.add_edge("cluster_cybersecurity", node_key, weight=0.90, relation="contains")

    # =========================================================================
    # 3. SÍNTESIS DE PATRONES FULLSTACK, AGENTES, DEVOPS Y BACKEND
    # =========================================================================
    def ingest_synthesized_architectures(self):
        print("🧠 Sintetizando Patrones y Recetas Avanzadas...")

        recipes = [
            # NEXT.JS 15 E-COMMERCE & STATE MANAGEMENT
            {
                "id": "nextjs-15-zustand-cart-hydration",
                "title": "Next.js 15: Carrito E-commerce con Zustand y Persist Sin Errores de Hidratación",
                "type": "pattern",
                "category": "web",
                "tags": ["nextjs15", "zustand", "react", "hydration", "ecommerce", "cart"],
                "file": "patterns/web/nextjs-15-zustand-cart-hydration.md",
                "related": ["cluster_web_ecosystem", "antipattern_react_zustand_full_store_subscription"],
                "body": """# Next.js 15: Carrito E-commerce con Zustand y Persist Seguro

## Problema
Al usar Zustand con `persist` (localStorage) en Next.js App Router (SSR), el HTML renderizado en servidor no coincide con el estado local del cliente, generando el clásico warning `Hydration failed because the initial UI does not match`.

## Solución Arquitectónica
Implementar un hook selector o un flag `useHydrated()` para asegurar que la lectura del localStorage solo ocurra tras el montaje del cliente.

```tsx
// store/useCartStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
  size?: string;
}

interface CartState {
  items: CartItem[];
  addItem: (item: CartItem) => void;
  removeItem: (id: string) => void;
  clearCart: () => void;
  totalPrice: () => number;
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],
      addItem: (newItem) =>
        set((state) => {
          const existing = state.items.find((i) => i.id === newItem.id && i.size === newItem.size);
          if (existing) {
            return {
              items: state.items.map((i) =>
                i === existing ? { ...i, quantity: i.quantity + newItem.quantity } : i
              ),
            };
          }
          return { items: [...state.items, newItem] };
        }),
      removeItem: (id) =>
        set((state) => ({ items: state.items.filter((i) => i.id !== id) })),
      clearCart: () => set({ items: [] }),
      totalPrice: () => get().items.reduce((acc, item) => acc + item.price * item.quantity, 0),
    }),
    {
      name: 'zorba-cart-storage',
      storage: createJSONStorage(() => localStorage),
      skipHydration: true, // Crucial para Next.js 15 SSR
    }
  )
);
```

### Componente React Seguro contra Deshidratación
```tsx
// components/CartDrawer.tsx
'use client';
import { useEffect, useState } from 'react';
import { useCartStore } from '@/store/useCartStore';

export function CartDrawer() {
  const [hydrated, setHydrated] = useState(false);
  const items = useCartStore((s) => s.items);
  const totalPrice = useCartStore((s) => s.totalPrice);

  useEffect(() => {
    useCartStore.persist.rehydrate();
    setHydrated(true);
  }, []);

  if (!hydrated) {
    return <div className="animate-pulse p-4">Cargando bolsa...</div>;
  }

  return (
    <div className="cart-container">
      <h3>Bolsa ({items.length})</h3>
      {items.map((item) => (
        <div key={`${item.id}-${item.size}`}>{item.name} x {item.quantity} - ${item.price}</div>
      ))}
      <div>Total: ${totalPrice()}</div>
    </div>
  );
}
```
"""
            },
            # LANGGRAPH MULTI-AGENT STATE GRAPH
            {
                "id": "langgraph-multi-agent-stategraph-supervisor",
                "title": "LangGraph: Arquitectura Multi-Agente con Supervisor Central y StateGraph",
                "type": "pattern",
                "category": "agents",
                "tags": ["langgraph", "agents", "multi-agent", "stategraph", "supervisor", "python"],
                "file": "patterns/agents/langgraph-multi-agent-supervisor.md",
                "related": ["cluster_agentic_ai", "pattern_agentic_subprocess_validation_sandbox"],
                "body": """# LangGraph: Arquitectura Multi-Agente con Supervisor Central

## Descripción
Patrón de orquestación donde un nodo supervisor toma decisiones de enrutamiento basadas en el estado del grafo, delegando tareas especializadas a agentes trabajadores (ej. Investigador, Coder, Validador) hasta que la tarea es completada (`FINISH`).

## Arquitectura de Estado
```python
from typing import Annotated, Sequence, TypedDict, Literal
from langchain_core.messages import BaseMessage
import operator
from langgraph.graph import StateGraph, END

# 1. Definición del Estado Compartido
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_worker: str
    code_artifact: str
    validation_status: bool
    iteration_count: int

# 2. Supervisor Node
def supervisor_node(state: AgentState):
    messages = state["messages"]
    last_msg = messages[-1].content if messages else ""
    
    if state["validation_status"]:
        return {"next_worker": "FINISH"}
    if state["iteration_count"] >= 5:
        return {"next_worker": "FINISH"}
    
    if "def " in state.get("code_artifact", "") and not state["validation_status"]:
        return {"next_worker": "validator"}
    
    return {"next_worker": "coder"}

# 3. Coder Node
def coder_node(state: AgentState):
    # Genera código optimizado
    return {
        "code_artifact": "def process_data(x): return [i*2 for i in x]",
        "iteration_count": state["iteration_count"] + 1
    }

# 4. Validator Node
def validator_node(state: AgentState):
    # Corre tests en sandbox
    is_valid = len(state.get("code_artifact", "")) > 0
    return {"validation_status": is_valid}

# 5. Construcción del Grafo
workflow = StateGraph(AgentState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("coder", coder_node)
workflow.add_node("validator", validator_node)

workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    lambda state: state["next_worker"],
    {
        "coder": "coder",
        "validator": "validator",
        "FINISH": END
    }
)
workflow.add_edge("coder", "supervisor")
workflow.add_edge("validator", "supervisor")

app = workflow.compile()
```
"""
            },
            # DRIZZLE ORM POSTGRESQL CONNECTION POOLING & TRANSACTIONS
            {
                "id": "drizzle-orm-postgres-pooling-transactions",
                "title": "Drizzle ORM: Connection Pooling con Neon/Supabase y Transacciones Seguras",
                "type": "pattern",
                "category": "database",
                "tags": ["drizzle", "postgresql", "supabase", "neon", "typescript", "orm", "database"],
                "file": "patterns/database/drizzle-orm-postgres-transactions.md",
                "related": ["cluster_web_ecosystem", "antipattern_prisma_n_plus_one_relations"],
                "body": """# Drizzle ORM: Connection Pooling & Transacciones Seguras

## Descripción
Configuración de alto rendimiento para TypeScript con Drizzle ORM sobre PostgreSQL Serverless (Neon/Supabase), asegurando pooling de conexiones HTTP/WebSockets y transacciones ACID sin fugas de cliente.

```typescript
// db/index.ts
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './schema';

const connectionString = process.env.DATABASE_URL!;

// Configuración para Serverless / Edge (Next.js 15)
const client = postgres(connectionString, {
  max: 10, // Pool size controlado
  idle_timeout: 20,
  connect_timeout: 10,
});

export const db = drizzle(client, { schema });

// Transacción ACID segura con Rollback Automático
export async function transferCredits(senderId: string, receiverId: string, amount: number) {
  return await db.transaction(async (tx) => {
    const [sender] = await tx
      .select()
      .from(schema.users)
      .where(schema.eq(schema.users.id, senderId))
      .for('update'); // Row-level lock

    if (!sender || sender.balance < amount) {
      tx.rollback();
      throw new Error('Fondos insuficientes');
    }

    await tx
      .update(schema.users)
      .set({ balance: sender.balance - amount })
      .where(schema.eq(schema.users.id, senderId));

    await tx
      .update(schema.users)
      .set({ balance: schema.sql`${schema.users.balance} + ${amount}` })
      .where(schema.eq(schema.users.id, receiverId));

    return { success: true };
  });
}
```
"""
            },
            # DOCKER MULTI-STAGE PYTHON FASTAPI
            {
                "id": "docker-multistage-production-fastapi",
                "title": "Docker: Multi-Stage Build Optimizado para Python FastAPI (< 120MB)",
                "type": "pattern",
                "category": "devops",
                "tags": ["docker", "fastapi", "devops", "containers", "security", "python"],
                "file": "patterns/devops/docker-multistage-fastapi.md",
                "related": ["cluster_devops_cloud", "antipattern_fastapi_blocking_async_event_loop"],
                "body": """# Docker: Multi-Stage Build para FastAPI

## Descripción
Dockerfile de 2 etapas que compila ruedas de dependencias con compilador C y transfiere solo el virtualenv a una imagen final `python:3.11-slim`, reduciendo el tamaño de la imagen de 1.2GB a menos de 120MB y eliminando herramientas de compilación que representan riesgos de seguridad.

```dockerfile
# -------------------------------------------------------------
# Stage 1: Build & Dependencies
# -------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------------------
# Stage 2: Final Production Runner
# -------------------------------------------------------------
FROM python:3.11-slim AS runner

WORKDIR /app

# Crear usuario no root por seguridad
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 appuser

COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appgroup . /app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8000

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```
"""
            },
            # GITHUB ACTIONS CI/CD PYTEST & LINT PIPELINE
            {
                "id": "github-actions-ci-cd-python-matrix",
                "title": "GitHub Actions: Pipeline CI/CD con Matriz de Pruebas, Cache uv y Linting Estricto",
                "type": "pattern",
                "category": "devops",
                "tags": ["github-actions", "cicd", "pytest", "ruff", "devops", "automation"],
                "file": "patterns/devops/github-actions-ci-matrix.md",
                "related": ["cluster_devops_cloud"],
                "body": """# GitHub Actions: CI/CD Pipeline para Python con uv Cache

```yaml
name: CI Suite

on:
  push:
    branches: [ main, master, dev ]
  pull_request:
    branches: [ main, master ]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true

      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          uv sync --all-extras --dev

      - name: Static Analysis with Ruff
        run: |
          uv run ruff check .
          uv run ruff format --check .

      - name: Type Checking with MyPy
        run: |
          uv run mypy .

      - name: Run Test Suite with Pytest & Coverage
        run: |
          uv run pytest --cov=. --cov-report=xml --timeout=10

      - name: Upload Coverage Artifacts
        uses: actions/upload-artifact@v4
        if: matrix.python-version == '3.11'
        with:
          name: coverage-report
          path: coverage.xml
```
"""
            }
        ]

        for r in recipes:
            clean_id = sanitize_id(r["id"])
            rel_path = r["file"]
            target_path = HUB_ROOT / rel_path

            fm = {
                "id": clean_id,
                "title": r["title"],
                "type": r["type"],
                "category": r["category"],
                "tags": r["tags"],
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            save_markdown_file(target_path, fm, r["body"])

            node_key = f"{r['type']}_{clean_id.replace('-', '_')}"
            rel_file = rel_path
            self.register_node(
                node_id=node_key,
                node_type=r["type"],
                label=r["title"],
                file_rel=rel_file,
                keywords=r["tags"] + [clean_id, r["category"]]
            )

            for rel_node in r.get("related", []):
                self.add_edge(rel_node, node_key, weight=0.85, relation="pairs_with")

    # =========================================================================
    # 4. CABLEADO DE CLUSTERS Y ARISTAS CRUZADAS
    # =========================================================================
    def wire_semantic_clusters(self):
        print("🔗 Cableando Clusters Semánticos y Sinapsis Cruzadas...")

        clusters = [
            ("cluster_n8n_automation", "n8n Workflow Automation Hub", ["n8n", "automation", "webhook", "integration", "workflow", "trigger"]),
            ("cluster_cybersecurity", "Cybersecurity & Threat Defense Hub", ["security", "cybersecurity", "defense", "mitre", "auth", "vulnerability", "privesc"]),
            ("cluster_web_ecosystem", "Modern Web & Next.js 15 Ecosystem", ["nextjs", "react", "tailwind", "zustand", "frontend", "ecommerce", "ui", "drizzle"]),
            ("cluster_agentic_ai", "Autonomous Agents & Memory Systems", ["agent", "agents", "langgraph", "sandbox", "token", "prompt", "memory", "optimizer"]),
            ("cluster_devops_cloud", "DevOps, Containers & CI/CD Hub", ["docker", "devops", "github-actions", "cicd", "container", "deployment", "kubernetes"]),
            ("cluster_backend_fastapi", "High-Performance Backend & APIs", ["fastapi", "asyncio", "python", "sse", "streaming", "rest", "api"]),
        ]

        for cid, clabel, ckeywords in clusters:
            if cid not in self.nodes:
                self.nodes[cid] = {
                    "type": "cluster",
                    "label": clabel,
                    "file": "",
                    "keywords": sorted(list(set(_tokenize(clabel) + ckeywords)))
                }

        # Aristas cruzadas estratégicas
        cross_edges = [
            ("cluster_backend_fastapi", "cluster_web_ecosystem", 0.90, "pairs_with"),
            ("cluster_agentic_ai", "cluster_backend_fastapi", 0.85, "pairs_with"),
            ("cluster_n8n_automation", "cluster_backend_fastapi", 0.88, "triggers"),
            ("cluster_cybersecurity", "cluster_web_ecosystem", 0.85, "protects"),
            ("cluster_devops_cloud", "cluster_backend_fastapi", 0.90, "deploys"),
            ("cluster_devops_cloud", "cluster_web_ecosystem", 0.90, "deploys"),
            ("cluster_agentic_ai", "cluster_cybersecurity", 0.80, "audits"),
        ]

        for src, tgt, w, rel in cross_edges:
            self.add_edge(src, tgt, weight=w, relation=rel)

    def save_and_commit(self):
        print("💾 Guardando nuevo grafo sináptico...")
        self.graph["nodes"] = self.nodes
        self.graph["edges"] = self.edges
        self.graph["settings"] = self.graph.get("settings", {
            "default_threshold": 0.60,
            "max_hops": 2,
            "decay_rate": 0.75
        })

        with open(GRAPH_FILE, "w", encoding="utf-8") as f:
            json.dump(self.graph, f, indent=2, ensure_ascii=False)

        print(f"✅ Ingesta finalizada exitosamente.")
        print(f"📊 Nodos Totales: {len(self.nodes)}")
        print(f"🔗 Aristas Totales: {len(self.edges)}")


if __name__ == "__main__":
    ingestor = MassiveIngestor()
    ingestor.wire_semantic_clusters()
    ingestor.ingest_n8n_skills()
    ingestor.ingest_cybersecurity_skills()
    ingestor.ingest_synthesized_architectures()
    ingestor.save_and_commit()
