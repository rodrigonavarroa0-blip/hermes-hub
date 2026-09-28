Plaintext
~/.hermes-hub/
├── config/
│   ├── graph.json              # Matriz de adyacencia y sinapsis ponderadas
│   └── mcp_server.py           # Servidor MCP para consultar y propagar contexto
├── memory/
│   ├── USER.md                 # Preferencias de desarrollo y stack predilecto
│   └── MEMORY.md               # Reglas no negociables y convenciones globales
├── skills/                     # Habilidades validadas (formato agentskills.io)
│   ├── stripe-webhook-sync.md
│   └── supabase-rls-setup.md
├── patterns/                   # Arquitecturas y snippets reutilizables
│   └── nextjs-app-router-auth.md
├── antipatterns/               # Errores registrados para no repetir
│   └── edge-runtime-secrets.md
└── drafts/                     # Skills en cuarentena (esperando 2da validación)
    └── draft-drizzle-migration.md
1. Plantilla de Nodo / Skill (skills/stripe-webhook-sync.md)

Cada archivo utiliza Frontmatter estructurado para que el enrutador lea sus conexiones sin necesidad de parsear todo el texto:

Markdown
---
id: skill_stripe_webhooks
type: skill
tags: [stripe, backend, payments, webhooks]
synapses:
  - target: pattern_raw_body_parser
    weight: 0.95
    relation: requires
  - target: antipattern_edge_runtime_secrets
    weight: 0.85
    relation: prevents
  - target: skill_supabase_rls_setup
    weight: 0.40
    relation: pairs_with
---

# Stripe Webhook Handler Pattern

## Cuándo usar
Cuando se procesen eventos asíncronos de pago (`checkout.session.completed`, `invoice.payment_failed`).

## Procedimiento
1. Desactivar el parseo automático de JSON en el endpoint para preservar el `rawBody`.
2. Verificar la firma criptográfica usando `stripe.webhooks.constructEvent`.
3. Procesar de forma idempotente guardando el `event.id` en base de datos antes de mutar estado.
2. Matriz de Conexiones Neuronal (config/graph.json)

JSON
{
  "nodes": {
    "stripe": { "type": "tag", "layer": "input" },
    "skill_stripe_webhooks": { "type": "skill", "file": "skills/stripe-webhook-sync.md" },
    "pattern_raw_body_parser": { "type": "pattern", "file": "patterns/nextjs-app-router-auth.md" },
    "antipattern_edge_runtime_secrets": { "type": "antipattern", "file": "antipatterns/edge-runtime-secrets.md" }
  },
  "edges": [
    { "from": "stripe", "to": "skill_stripe_webhooks", "weight": 1.0 },
    { "from": "skill_stripe_webhooks", "to": "pattern_raw_body_parser", "weight": 0.95 },
    { "from": "skill_stripe_webhooks", "to": "antipattern_edge_runtime_secrets", "weight": 0.85 }
  ]
}
3. Archivo de Enlace por Proyecto (AGENTS.md o .cursorrules)

Coloca este archivo en la raíz de cada nuevo proyecto de vibecoding:

Markdown
# Directivas del Agente

- Conexión al Hub Central: `~/.hermes-hub/`
- Servidor MCP Activo: `hermes-context-engine`

## Reglas de Ejecución:
1. Al recibir una tarea, invoca la herramienta MCP `resolve_context(prompt)` para traer únicamente las skills y anti-patrones con activación > 0.6.
2. Sigue las convenciones definidas en `~/.hermes-hub/memory/MEMORY.md`.
3. Si resuelves un bug nuevo o creas un flujo no documentado, ejecuta la herramienta `propose_skill(title, content)` para guardarlo en `drafts/`.
4. Servidor MCP Mínimo de Enrutamiento (config/mcp_server.py)

Python
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hermes-context-engine")
HUB_DIR = Path(__file__).parent.parent

@mcp.tool()
def resolve_context(prompt: str, threshold: float = 0.6) -> str:
    """Busca nodos semilla en el grafo y propaga energía para extraer contexto relevante."""
    with open(HUB_DIR / "config/graph.json") as f:
        graph = json.load(f)
    
    prompt_lower = prompt.lower()
    activated_nodes = set()
    
    # 1. Detección de semillas
    for node_id, data in graph["nodes"].items():
        if node_id in prompt_lower:
            activated_nodes.add(node_id)
            
    # 2. Propagación sináptica (1 salto)
    context_files = []
    for edge in graph["edges"]:
        if edge["from"] in activated_nodes and edge["weight"] >= threshold:
            target = graph["nodes"].get(edge["to"])
            if target and "file" in target:
                context_files.append(target["file"])
                
    # 3. Compilación del subgrafo
    bundle = []
    for rel_path in set(context_files):
        content = (HUB_DIR / rel_path).read_text(encoding="utf-8")
        bundle.append(f"--- INICIO: {rel_path} ---\n{content}\n--- FIN ---")
        
    return "\n\n".join(bundle) if bundle else "No se requiere contexto adicional específico."

if __name__ == "__main__":
    mcp.run()