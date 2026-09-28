# Perfil del Desarrollador

- **Enfoque Principal:** Desarrollo Full-Stack moderno, Serverless, Edge Computing.
- **Stack Preferido:** Next.js (App Router), TypeScript, Tailwind CSS, Supabase / PostgreSQL, Drizzle ORM, tRPC.
- **Estilo de Código:** Funcional, fuertemente tipado, modular, componentes limpios y sin sobre-abstracciones.
- **Formato de Respuesta Preferido:** Código conciso, explicaciones directas al grano, sin explicaciones redundantes de sintaxis básica.

# Convenciones y Reglas No Negociables

1. **Seguridad:**
   - Jamás exponer variables de entorno que no inicien con `NEXT_PUBLIC_` en el cliente.
   - Toda tabla de PostgreSQL debe tener Row Level Security (RLS) habilitado por defecto.
2. **Arquitectura:**
   - Usar Server Actions exclusivamente para mutaciones, no para queries de lectura.
   - Centralizar validación de esquemas con Zod en capas de entrada/salida.
3. **Manejo de Errores:**
   - Usar tipos `Result<T, E>` o bloques de captura tipados en endpoints críticos.


   Use this as a guide: {"""
Hermes Context Engine - Servidor FastMCP
Gestiona la lectura asociativa por grafos y el registro de auto-perfeccionamiento.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Any
import yaml
from mcp.server.fastmcp import FastMCP

# Inicialización del servidor
mcp = FastMCP(
    "hermes-context-engine",
    instructions="Servidor MCP central para enrutamiento por grafos asociativos y auto-aprendizaje de skills."
)

HUB_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = HUB_DIR / "config"
GRAPH_FILE = CONFIG_DIR / "graph.json"
MEMORY_DIR = HUB_DIR / "memory"
SKILLS_DIR = HUB_DIR / "skills"
PATTERNS_DIR = HUB_DIR / "patterns"
ANTIPATTERNS_DIR = HUB_DIR / "antipatterns"
DRAFTS_DIR = HUB_DIR / "drafts"

# Asegurar directorios
for directory in [CONFIG_DIR, MEMORY_DIR, SKILLS_DIR, PATTERNS_DIR, ANTIPATTERNS_DIR, DRAFTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def load_graph() -> Dict[str, Any]:
    if not GRAPH_FILE.exists():
        default_graph = {
            "version": "1.0.0",
            "settings": {"default_threshold": 0.60, "max_hops": 2, "decay_rate": 0.75},
            "nodes": {},
            "edges": []
        }
        with open(GRAPH_FILE, "w", encoding="utf-8") as f:
            json.dump(default_graph, f, indent=2)
        return default_graph
    with open(GRAPH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_graph(graph_data: Dict[str, Any]) -> None:
    with open(GRAPH_FILE, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2)


def extract_frontmatter(file_path: Path) -> tuple[Dict[str, Any], str]:
    if not file_path.exists():
        return {}, ""
    raw_text = file_path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw_text, re.DOTALL)
    if match:
        meta = yaml.safe_load(match.group(1)) or {}
        body = match.group(2)
        return meta, body
    return {}, raw_text


@mcp.tool()
def get_global_memory() -> str:
    """Obtiene las directivas globales del desarrollador (USER.md) y reglas no negociables (MEMORY.md)."""
    user_file = MEMORY_DIR / "USER.md"
    memory_file = MEMORY_DIR / "MEMORY.md"
    
    parts = []
    if user_file.exists():
        parts.append(f"# DIRECTIVAS DEL USUARIO\n{user_file.read_text(encoding='utf-8')}")
    if memory_file.exists():
        parts.append(f"# REGLAS GLOBALES Y CONVENCIONES\n{memory_file.read_text(encoding='utf-8')}")
        
    return "\n\n---\n\n".join(parts) if parts else "No hay archivos de memoria global configurados."


@mcp.tool()
def resolve_context(prompt: str, threshold: float = 0.60, max_hops: int = 2) -> str:
    """
    Ejecuta el algoritmo de propagación sináptica sobre el grafo para retornar
    únicamente las skills, patterns y antipatterns relevantes al prompt.
    """
    graph = load_graph()
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])
    decay = graph.get("settings", {}).get("decay_rate", 0.75)
    
    prompt_tokens = set(re.findall(r"\w+", prompt.lower()))
    activation: Dict[str, float] = {}

    # 1. Identificar semillas
    for node_id, data in nodes.items():
        node_label = data.get("label", node_id).lower()
        node_tokens = set(re.findall(r"\w+", node_label + " " + node_id))
        
        # Coincidencia con tokens del prompt
        if node_tokens & prompt_tokens:
            activation[node_id] = 1.0

    if not activation:
        return "No se encontraron nodos específicos para el prompt. Aplica memoria global estándar."

    # 2. Spreading Activation por saltos
    for _ in range(max_hops):
        current_active = list(activation.items())
        for u, energy in current_active:
            for edge in edges:
                if edge["from"] == u:
                    v = edge["to"]
                    transmitted = energy * edge.get("weight", 0.5) * decay
                    if transmitted > activation.get(v, 0.0):
                        activation[v] = transmitted

    # 3. Filtrado por umbral y carga de documentos
    compiled_bundle = []
    loaded_files: Set[str] = set()

    for node_id, energy in sorted(activation.items(), key=lambda x: x[1], reverse=True):
        if energy >= threshold:
            node_data = nodes.get(node_id, {})
            rel_file = node_data.get("file")
            if rel_file and rel_file not in loaded_files:
                target_path = HUB_DIR / rel_file
                if target_path.exists():
                    meta, body = extract_frontmatter(target_path)
                    title = meta.get("title", node_id)
                    node_type = meta.get("type", "conocimiento").upper()
                    
                    compiled_bundle.append(
                        f"### [{node_type}] {title} (Activación: {energy:.2f})\n"
                        f"**Archivo:** `{rel_file}`\n\n"
                        f"{body.strip()}"
                    )
                    loaded_files.add(rel_file)

    if not compiled_bundle:
        return "La energía de propagación no superó el umbral configurado. Usa directivas base."

    return "\n\n========================================\n\n".join(compiled_bundle)


@mcp.tool()
def propose_skill(id: str, title: str, type: str, tags: List[str], procedure_markdown: str) -> str:
    """
    Registra una nueva habilidad o patrón en la carpeta de cuarentena (drafts/)
    para iniciar el loop de auto-perfeccionamiento.
    """
    clean_id = re.sub(r"[^a-zA-Z0-9_-]", "_", id.lower())
    draft_path = DRAFTS_DIR / f"draft-{clean_id}.md"
    
    frontmatter = {
        "id": clean_id,
        "title": title,
        "type": type,
        "tags": tags,
        "usage_count": 1,
        "status": "quarantined",
        "synapses": []
    }
    
    full_content = (
        "---\n"
        + yaml.dump(frontmatter, sort_keys=False, allow_unicode=True)
        + "---\n\n"
        + procedure_markdown.strip()
        + "\n"
    )
    
    draft_path.write_text(full_content, encoding="utf-8")
    return f"Habilidad propuesta con éxito guardada en cuarentena: `drafts/draft-{clean_id}.md` (Uso: 1/2)."


@mcp.tool()
def validate_and_promote_skill(draft_id: str, related_nodes: List[Dict[str, Any]] = None) -> str:
    """
    Incrementa el contador de validación de un borrador. Si alcanza 2 validaciones,
    lo promueve automáticamente a skills/ y actualiza graph.json.
    """
    clean_id = re.sub(r"[^a-zA-Z0-9_-]", "_", draft_id.lower())
    draft_file = DRAFTS_DIR / f"draft-{clean_id}.md"
    
    if not draft_file.exists():
        return f"Error: No se encontró el borrador `draft-{clean_id}.md` en drafts/."
    
    meta, body = extract_frontmatter(draft_file)
    usage = meta.get("usage_count", 1) + 1
    meta["usage_count"] = usage

    if usage >= 2:
        # Promoción
        meta["status"] = "validated"
        meta.pop("usage_count", None)
        
        target_dir = SKILLS_DIR if meta.get("type") == "skill" else PATTERNS_DIR
        final_file = target_dir / f"{clean_id}.md"
        rel_path = str(final_file.relative_to(HUB_DIR))
        
        # Escribir archivo validado
        new_content = (
            "---\n"
            + yaml.dump(meta, sort_keys=False, allow_unicode=True)
            + "---\n\n"
            + body.strip()
            + "\n"
        )
        final_file.write_text(new_content, encoding="utf-8")
        draft_file.unlink()  # Eliminar borrador
        
        # Actualizar grafo
        graph = load_graph()
        graph["nodes"][clean_id] = {
            "type": meta.get("type", "skill"),
            "file": rel_path,
            "label": meta.get("title", clean_id)
        }
        
        # Enlazar tags
        for tag in meta.get("tags", []):
            tag_id = tag.lower()
            if tag_id not in graph["nodes"]:
                graph["nodes"][tag_id] = {"type": "tag", "layer": "input", "label": tag}
            graph["edges"].append({"from": tag_id, "to": clean_id, "weight": 0.90, "relation": "triggers"})
            
        # Enlazar nodos relacionados adicionales
        if related_nodes:
            for rel in related_nodes:
                graph["edges"].append({
                    "from": clean_id,
                    "to": rel["target"],
                    "weight": rel.get("weight", 0.75),
                    "relation": rel.get("relation", "pairs_with")
                })
                
        save_graph(graph)
        return f"¡Éxito! Habilidad `{clean_id}` validada 2 veces y promovida a `{rel_path}` con sinapsis integradas al grafo."
    
    else:
        # Actualizar contador en borrador
        new_content = (
            "---\n"
            + yaml.dump(meta, sort_keys=False, allow_unicode=True)
            + "---\n\n"
            + body.strip()
            + "\n"
        )
        draft_file.write_text(new_content, encoding="utf-8")
        return f"Borrador `{clean_id}` validado. Uso actual: {usage}/2. Requiere una validación más para promoción."


if __name__ == "__main__":
    mcp.run() }


    # Directivas de Contexto de IA y Vibecoding

Este proyecto está conectado a la base de conocimiento centralizada de Hermes.

## Reglas de Ejecución:
1. **Inicio de Tarea:**
   - Antes de implementar cualquier funcionalidad compleja o resolver bugs, invoca la herramienta MCP `resolve_context(prompt=...)` pasando un resumen de la tarea.
   - Aplica estrictamente las skills, patrones y evita los antipatrones devueltos.
2. **Convenciones Globales:**
   - Consulta `get_global_memory()` cuando inicies un proyecto desde cero para heredar estilo, stack preferido y convenciones no negociables.
3. **Loop de Auto-Perfeccionamiento:**
   - Si creas una solución nueva, patrón de diseño reutilizable o resuelves un bug no documentado, invoca `propose_skill(...)`.
   - Si reutilizas con éxito una skill que estaba en `drafts/`, invoca `validate_and_promote_skill(...)`.

   ──────────────┐       1er Uso Exitoso        ┌──────────────┐
│  Resolución  │ ───────────────────────────▶ │   drafts/    │ (usage = 1, quarantined)
│  Novedosa    │                              └──────┬───────┘
└──────────────┘                                     │
                                                     │ 2do Uso Validado
                                                     ▼
┌──────────────┐      Actualización Sináptica ┌──────────────┐
│  graph.json  │ ◀─────────────────────────── │   skills/    │ (status = validated)
└──────────────┘                              └──────────────┘


