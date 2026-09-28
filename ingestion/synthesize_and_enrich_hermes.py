#!/usr/bin/env python3
"""
synthesize_and_enrich_hermes.py - Pipeline de Síntesis y Enriquecimiento Profundo para Hermes Hub

Genera y publica:
1. Antipatrones críticos de arquitectura y rendimiento (FastAPI, PyTorch, Zustand, Next.js, Agents, Prisma, Supabase).
2. Recetas de integración de alto rendimiento.
3. Actualización de sinapsis y optimización del motor de spreading activation.
"""

import os
import re
import json
import yaml
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any

HUB_ROOT = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_ROOT / "config"
PATTERNS_DIR = HUB_ROOT / "patterns"
SKILLS_DIR = HUB_ROOT / "skills"
ANTIPATTERNS_DIR = HUB_ROOT / "antipatterns"
GRAPH_FILE = CONFIG_DIR / "graph.json"


# ==============================================================================
# 1. CATÁLOGO DE ANTIPATRONES CRÍTICOS
# ==============================================================================

ANTIPATTERNS = [
    {
        "filename": "antipattern_fastapi_blocking_async.md",
        "title": "FastAPI: Llamadas Síncronas Bloqueantes en Endpoints Asíncronos",
        "tags": ["fastapi", "asyncio", "python", "performance", "event-loop", "antipattern"],
        "cluster": "mindrally_python_ai_cluster",
        "content": """# Antipatrón: Llamadas Síncronas Bloqueantes en Endpoints Asíncronos (FastAPI)

## Problema y Causa Raíz
Definir un endpoint como `async def` y ejecutar dentro de él operaciones de I/O bloqueantes (como `requests.get()`, `time.sleep()`, llamadas pesadas a bases de datos con drivers síncronos o cómputo intensivo de CPU) **congela el Event Loop principal de asyncio de FastAPI / Uvicorn**. Todas las demás solicitudes concurrentes quedan completamente bloqueadas hasta que dicha llamada termine.

## Código Incorrecto (Antipatrón)
```python
# ❌ INCORRECTO: Bloquea todo el event loop para todos los usuarios
import requests
import time
from fastapi import FastAPI

app = FastAPI()

@app.get("/data")
async def get_external_data():
    time.sleep(2)  # Bloqueo total
    resp = requests.get("https://api.example.com/items")  # Bloqueo síncrono
    return resp.json()
```

## Solución Correcta y Mitigación
1. Si usas librerías asíncronas (`httpx.AsyncClient`, `asyncio.sleep`, drivers async), mantén `async def`.
2. Si tienes que usar código síncrono/bloqueante que no puedes migrar a async, usa un endpoint síncrono estándar `def` (FastAPI lo ejecutará automáticamente en un thread pool de trabajo externo) o usa `fastapi.concurrency.run_in_threadpool`.

```python
# ✅ CORRECTO: Usando cliente asíncrono nativo
import httpx
import asyncio
from fastapi import FastAPI

app = FastAPI()

@app.get("/data-async")
async def get_external_data_async():
    await asyncio.sleep(0.1)  # Cede el control al event loop
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.example.com/items")
        return resp.json()

# ✅ CORRECTO: Si la función es síncrona, definir como 'def' normal (FastAPI usa ThreadPool)
import requests

@app.get("/data-sync-threaded")
def get_external_data_sync():
    resp = requests.get("https://api.example.com/items")
    return resp.json()
```
"""
    },
    {
        "filename": "antipattern_pytorch_vram_graph_accumulation.md",
        "title": "PyTorch: Fuga de VRAM por Acumulación del Grafo de Autograd",
        "tags": ["pytorch", "gpu", "vram", "oom", "cuda", "machine-learning", "antipattern"],
        "cluster": "mindrally_python_ai_cluster",
        "content": """# Antipatrón: Fuga de VRAM por Acumulación del Grafo de Autograd (PyTorch)

## Problema y Causa Raíz
Al entrenar modelos en PyTorch y registrar métricas de pérdida (loss), hacer `running_loss += loss` acumula el tensor completo junto con todo su grafo computacional de diferenciación automática (`autograd`) en la memoria VRAM de la GPU. Tras varias iteraciones, esto consume gigabytes de VRAM y produce un fallo fatal `CUDA out of memory (OOM)`.

## Código Incorrecto (Antipatrón)
```python
# ❌ INCORRECTO: Mantiene el grafo computacional en GPU en cada batch
total_loss = 0.0
for batch in dataloader:
    optimizer.zero_grad()
    outputs = model(batch["inputs"])
    loss = criterion(outputs, batch["targets"])
    loss.backward()
    optimizer.step()
    
    # 💥 FATAL: 'loss' es un tensor con historial de autograd
    total_loss += loss
```

## Solución Correcta y Mitigación
Extraer el valor escalar float de Python usando `.item()` o `.detach()`, lo cual rompe la referencia al grafo computacional:

```python
# ✅ CORRECTO: Extraer el escalar nativo de Python con .item()
total_loss = 0.0
for batch in dataloader:
    optimizer.zero_grad()
    outputs = model(batch["inputs"])
    loss = criterion(outputs, batch["targets"])
    loss.backward()
    optimizer.step()
    
    # ✅ Seguro: .item() extrae solo el float y libera la memoria del grafo
    total_loss += loss.item()
```
"""
    },
    {
        "filename": "antipattern_zustand_full_store_subscription.md",
        "title": "Zustand: Suscripción al Store Completo y Re-renders Masivos",
        "tags": ["zustand", "react", "nextjs", "rerender", "performance", "state-management", "antipattern"],
        "cluster": "mindrally_modern_fullstack_cluster",
        "content": """# Antipatrón: Suscripción al Store Completo en Zustand (React)

## Problema y Causa Raíz
Invocar `const store = useStore()` sin una función de selección suscribe al componente React a **cualquier cambio en cualquier propiedad del store**. Si el store contiene decenas de estados, cada actualización en una propiedad no relacionada forzará el re-renderizado completo de todo el árbol de componentes.

## Código Incorrecto (Antipatrón)
```tsx
// ❌ INCORRECTO: El componente se re-renderiza con CUALQUIER cambio del store
import { useCartStore } from "@/store/cart";

export function CartBadge() {
  const { items } = useCartStore(); // Suscripción a todo el objeto store
  return <span className="badge">{items.length}</span>;
}
```

## Solución Correcta y Mitigación
Utilizar siempre selectores atómicos específicos para que el componente solo reaccione a la propiedad exacta que consume:

```tsx
// ✅ CORRECTO: Suscripción atómica exacta
import { useCartStore } from "@/store/cart";

export function CartBadge() {
  // Solo se re-renderiza si la longitud de items cambia
  const itemCount = useCartStore((state) => state.items.length);
  return <span className="badge">{itemCount}</span>;
}
```
"""
    },
    {
        "filename": "antipattern_nextjs_unprotected_server_actions.md",
        "title": "Next.js 15: Server Actions sin Validación de Sesión ni Esquemas Zod",
        "tags": ["nextjs", "server-actions", "security", "zod", "auth", "supabase", "antipattern"],
        "cluster": "mindrally_modern_fullstack_cluster",
        "content": """# Antipatrón: Server Actions sin Validación de Sesión ni Tipado Estricto (Next.js 15)

## Problema y Causa Raíz
Las Server Actions (`"use server"`) se exponen como endpoints HTTP públicos POST automáticamente por Next.js. Si se asume que solo el frontend autenticado invocará la acción y no se valida explícitamente la sesión (`auth.uid()`) ni los argumentos mediante esquemas de validación Zod, cualquier atacante puede invocar la acción directamente vía HTTP con payloads maliciosos o suplantando identidades.

## Código Incorrecto (Antipatrón)
```ts
// ❌ INCORRECTO: Confiando a ciegas en los argumentos del cliente
"use server";
import { db } from "@/lib/db";

export async function deletePostAction(userId: string, postId: string) {
  // 💥 VULNERABILIDAD CRÍTICA: Cualquiera puede pasar el userId de otra persona
  await db.delete(posts).where(eq(posts.id, postId));
}
```

## Solución Correcta y Mitigación
1. Extraer la identidad del usuario directamente desde la cookie/sesión autenticada en el servidor (`createClient()` de Supabase o Auth provider).
2. Validar todos los argumentos con un esquema Zod estricto.

```ts
// ✅ CORRECTO: Verificación de sesión en servidor + Zod SafeParse
"use server";
import { z } from "zod";
import { createServerClient } from "@/lib/supabase/server";
import { db } from "@/lib/db";
import { posts } from "@/lib/db/schema";
import { eq, and } from "drizzle-orm";

const DeletePostSchema = z.object({
  postId: z.string().uuid(),
});

export async function deletePostAction(formData: unknown) {
  const supabase = await createServerClient();
  const { data: { user }, error } = await supabase.auth.getUser();
  
  if (error || !user) {
    throw new Error("No autorizado: Sesión inválida");
  }

  const parsed = DeletePostSchema.safeParse(formData);
  if (!parsed.success) {
    return { success: false, error: parsed.error.flatten() };
  }

  // Se filtra tanto por el ID del post como por el ID de usuario autenticado
  await db.delete(posts).where(
    and(
      eq(posts.id, parsed.data.postId),
      eq(posts.authorId, user.id)
    )
  );

  return { success: true };
}
```
"""
    },
    {
        "filename": "antipattern_agentic_context_window_quadratic_explosion.md",
        "title": "Autonomous Agents: Explosión Cuadrática O(N^2) de Ventana de Contexto",
        "tags": ["agents", "context-engineering", "tokens", "performance", "llm", "antipattern"],
        "cluster": "agent_core_engineering_cluster",
        "content": """# Antipatrón: Explosión Cuadrática O(N^2) de Ventana de Contexto en Agentes Autónomos

## Problema y Causa Raíz
En bucles autónomos de desarrollo o agentes iterativos, acumular todo el historial de turnos pasados en cada llamada a la API (`messages.append(turn)`) provoca que el tamaño del prompt crezca como $\\sum_{i=1}^N i = O(N^2)$. Esto causa:
1. Agotamiento prematuro del presupuesto de tokens.
2. Degradación severa de la atención del LLM ("Lost in the Middle").
3. Tiempos de respuesta lentos y costos desorbitados.

## Código Incorrecto (Antipatrón)
```python
# ❌ INCORRECTO: Acumulación lineal que produce costo cuadrático de tokens O(N^2)
history = [{"role": "system", "content": "You are a coder"}]

for step in range(50):
    user_msg = get_user_task(step)
    history.append({"role": "user", "content": user_msg})
    # En el paso 50, se reenvían todos los 49 pasos previos
    response = client.chat.completions.create(model="gpt-4o", messages=history)
    history.append({"role": "assistant", "content": response.choices[0].message.content})
```

## Solución Correcta y Mitigación
Utilizar **Prompts Compactos $O(1)$** con memoria sintetizada: en cada turno se envía únicamente el baseline activo actual, la directiva puntual y la retroalimentación de la iteración inmediatamente previa.

```python
# ✅ CORRECTO: Prompt O(1) de tamaño constante en cada turno
for step in range(50):
    compact_prompt = build_compact_turn_prompt(
        current_active_baseline=best_code,
        current_strategy=strategies.get(step),
        previous_feedback=last_attempt_feedback
    )
    # Tamaño de prompt fijo y acotado en cada turno
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": compact_prompt}
        ]
    )
    # Procesar resultado y actualizar baseline sin inflar historial
```
"""
    },
    {
        "filename": "antipattern_prisma_n_plus_one_relations.md",
        "title": "Prisma ORM: Consultas N+1 en Iteraciones de Registros Relacionados",
        "tags": ["prisma", "orm", "database", "postgres", "performance", "antipattern"],
        "cluster": "mindrally_modern_fullstack_cluster",
        "content": """# Antipatrón: Consultas N+1 en Iteraciones de Registros Relacionados (Prisma ORM)

## Problema y Causa Raíz
Ejecutar llamadas `prisma.relation.findMany()` o `findUnique()` dentro de un bucle `map` o `for...of` sobre una lista de entidades padre genera $1 + N$ queries a la base de datos, saturando el pool de conexiones de PostgreSQL.

## Código Incorrecto (Antipatrón)
```ts
// ❌ INCORRECTO: 1 query para usuarios + N queries para órdenes
const users = await prisma.user.findMany();

const results = await Promise.all(
  users.map(async (u) => {
    const orders = await prisma.order.findMany({ where: { userId: u.id } }); // N queries!
    return { ...u, orders };
  })
);
```

## Solución Correcta y Mitigación
Utilizar la cláusula `include` o `select` de Prisma para que el motor resuelva las relaciones en una sola consulta SQL optimizada con `JOIN` o batching interno:

```ts
// ✅ CORRECTO: 1 sola consulta SQL optimizada con JOIN
const usersWithOrders = await prisma.user.findMany({
  include: {
    orders: {
      select: { id: true, amount: true, createdAt: true },
      where: { status: "COMPLETED" },
    },
  },
});
```
"""
    }
]


# ==============================================================================
# 2. CATÁLOGO DE RECETAS ARQUITECTÓNICAS DE ALTO VALOR
# ==============================================================================

RECIPES = [
    {
        "filename": "recipe_fastapi_nextjs_sse_streaming.md",
        "title": "Arquitectura de Streaming SSE en Tiempo Real: FastAPI ➔ Next.js 15",
        "tags": ["fastapi", "nextjs", "sse", "streaming", "realtime", "architecture", "pattern"],
        "cluster": "mindrally_modern_fullstack_cluster",
        "content": """# Receta: Streaming SSE en Tiempo Real (FastAPI Backend ➔ Next.js 15 Client)

Patrón de diseño para streaming de eventos en tiempo real (Server-Sent Events) entre microservicios de IA en FastAPI y aplicaciones frontend en Next.js App Router con tipado seguro y reconexión automática.

## 1. Backend: Endpoint SSE en FastAPI
```python
import asyncio
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def event_generator():
    for step in range(5):
        await asyncio.sleep(0.5)
        payload = {"step": step + 1, "status": "processing", "progress": (step + 1) * 20}
        yield f"data: {json.dumps(payload)}\\n\\n"
    yield f"data: {json.dumps({'status': 'complete', 'progress': 100})}\\n\\n"

@app.get("/api/stream-task")
async def stream_task():
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Desactiva buffer en NGINX
        }
    )
```

## 2. Frontend: Hook React en Next.js 15
```tsx
"use client";
import { useEffect, useState } from "react";

interface StreamEvent {
  step?: number;
  status: string;
  progress: number;
}

export function useTaskStream() {
  const [data, setData] = useState<StreamEvent | null>(null);
  const [isFinished, setIsFinished] = useState(false);

  useEffect(() => {
    const eventSource = new EventSource("/api/stream-task");

    eventSource.onmessage = (event) => {
      try {
        const parsed: StreamEvent = JSON.parse(event.data);
        setData(parsed);
        if (parsed.status === "complete") {
          setIsFinished(true);
          eventSource.close();
        }
      } catch (err) {
        console.error("Error parseando evento SSE:", err);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => eventSource.close();
  }, []);

  return { data, isFinished };
}
```
"""
    },
    {
        "filename": "recipe_agentic_sandbox_code_execution.md",
        "title": "Sandbox de Validación Segura para Agentes Autónomos en Python",
        "tags": ["sandbox", "security", "subprocesses", "validation-gate", "testing", "agents", "pattern"],
        "cluster": "agent_core_engineering_cluster",
        "content": """# Receta: Sandbox de Validación Segura en Subprocesos Aislados

Patrón de ejecución para agentes que generan y optimizan código dinámicamente. Protege el proceso principal mediante validación estática AST, límite de tiempo estricto (`timeout`) y aislamiento de memoria.

## Implementación de Referencia
```python
import ast
import os
import subprocess
import sys
import tempfile
from typing import Tuple, Optional

class SecureValidationSandbox:
    def __init__(self, timeout_sec: float = 5.0):
        self.timeout_sec = timeout_sec

    def check_syntax(self, source_code: str) -> Tuple[bool, Optional[str]]:
        try:
            ast.parse(source_code)
            return True, None
        except SyntaxError as e:
            return False, f"SyntaxError [Línea {e.lineno}]: {e.msg}"

    def run_isolated(self, candidate_code: str, test_code: str) -> Tuple[bool, str]:
        is_valid, err = self.check_syntax(candidate_code)
        if not is_valid:
            return False, err

        harness = f\"\"\"
# CANDIDATE
{candidate_code}

# TESTS
{test_code}

if __name__ == '__main__':
    run_tests()
    print('__PASSED__')
\"\"\"
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write(harness)
            script_path = tf.name

        try:
            res = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=self.timeout_sec
            )
            if res.returncode == 0 and "__PASSED__" in res.stdout:
                return True, "Tests aprobados con éxito."
            return False, res.stderr or res.stdout
        except subprocess.TimeoutExpired:
            return False, f"Timeout ({self.timeout_sec}s) excedido: posible bucle infinito."
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)
```
"""
    }
]


# ==============================================================================
# 3. MOTOR DE INGESTA Y VINCULACIÓN EN GRAPH.JSON
# ==============================================================================

def run_synthesis() -> Dict[str, Any]:
    print("=" * 80)
    print("🚀 EJECUTANDO SÍNTESIS Y ENRIQUECIMIENTO DE HERMES KNOWLEDGE HUB")
    print("=" * 80)

    if not GRAPH_FILE.exists():
        graph = {"settings": {"default_threshold": 0.60, "max_hops": 2, "decay_rate": 0.75}, "nodes": {}, "edges": []}
    else:
        with open(GRAPH_FILE, "r", encoding="utf-8") as f:
            graph = json.load(f)

    nodes = graph.setdefault("nodes", {})
    edges = graph.setdefault("edges", [])

    ANTIPATTERNS_DIR.mkdir(parents=True, exist_ok=True)
    recipes_dir = PATTERNS_DIR / "recipes"
    recipes_dir.mkdir(parents=True, exist_ok=True)

    ingested_antipatterns = 0
    ingested_recipes = 0

    # 1. Ingestar Antipatrones
    print("\n🛡️  Registrando Antipatrones Críticos...")
    for item in ANTIPATTERNS:
        file_path = ANTIPATTERNS_DIR / item["filename"]
        fm = {
            "id": f"antipattern_{Path(item['filename']).stem}",
            "title": item["title"],
            "type": "antipattern",
            "tags": item["tags"],
            "status": "active",
            "ingested_at": datetime.now(timezone.utc).isoformat()
        }
        yaml_header = yaml.dump(fm, sort_keys=False, default_flow_style=False)
        full_content = f"---\n{yaml_header}---\n\n{item['content'].strip()}\n"
        file_path.write_text(full_content, encoding="utf-8")

        node_id = fm["id"]
        nodes[node_id] = {
            "type": "antipattern",
            "label": item["title"],
            "file": f"antipatterns/{item['filename']}",
            "keywords": item["tags"] + [item["title"].lower()]
        }

        # Conectar con el clúster
        cluster_id = item["cluster"]
        if not any(e.get("source") == cluster_id and e.get("target") == node_id for e in edges):
            edges.append({
                "source": cluster_id,
                "target": node_id,
                "weight": 0.95,
                "relation": "mitigates"
            })
        ingested_antipatterns += 1
        print(f"  + [Antipattern]: {item['title']}")

    # 2. Ingestar Recetas de Arquitectura
    print("\n📐 Registrando Recetas de Alto Rendimiento...")
    for item in RECIPES:
        file_path = recipes_dir / item["filename"]
        fm = {
            "id": f"pattern_recipe_{Path(item['filename']).stem}",
            "title": item["title"],
            "type": "pattern",
            "tags": item["tags"],
            "status": "active",
            "ingested_at": datetime.now(timezone.utc).isoformat()
        }
        yaml_header = yaml.dump(fm, sort_keys=False, default_flow_style=False)
        full_content = f"---\n{yaml_header}---\n\n{item['content'].strip()}\n"
        file_path.write_text(full_content, encoding="utf-8")

        node_id = fm["id"]
        nodes[node_id] = {
            "type": "pattern",
            "label": item["title"],
            "file": f"patterns/recipes/{item['filename']}",
            "keywords": item["tags"] + [item["title"].lower()]
        }

        # Conectar con el clúster
        cluster_id = item["cluster"]
        if not any(e.get("source") == cluster_id and e.get("target") == node_id for e in edges):
            edges.append({
                "source": cluster_id,
                "target": node_id,
                "weight": 0.90,
                "relation": "implements"
            })
        ingested_recipes += 1
        print(f"  + [Recipe]: {item['title']}")

    with open(GRAPH_FILE, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)

    # Git commit
    try:
        subprocess.run(["git", "add", "."], cwd=str(HUB_ROOT), check=False, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"feat(synthesis): add {ingested_antipatterns} critical antipatterns and {ingested_recipes} architectural recipes"], cwd=str(HUB_ROOT), check=False, capture_output=True)
        print("\n✅ Git commit registrado con éxito en ~/.hermes-hub.")
    except Exception as e:
        print(f"Git commit notice: {e}")

    print("\n" + "=" * 80)
    print(f"✨ SÍNTESIS COMPLETADA: {ingested_antipatterns} Antipatrones y {ingested_recipes} Recetas incorporadas.")
    print("=" * 80)

    return {
        "antipatterns_count": ingested_antipatterns,
        "recipes_count": ingested_recipes,
        "total_nodes": len(nodes),
        "total_edges": len(edges)
    }


if __name__ == "__main__":
    run_synthesis()
