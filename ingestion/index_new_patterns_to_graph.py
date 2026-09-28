#!/usr/bin/env python3
"""
index_new_patterns_to_graph.py — Ingesta e Indexación Incremental de Patrones al Grafo Sináptico de Hermes.
Lee todas las notas en ~/.hermes-hub/patterns/, crea los nodos correspondientes en graph.json,
calcula sinapsis automáticas con los clusters y skills existentes, y actualiza hermes_dataset.jsonl.
"""
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Any

HUB_DIR = Path(os.path.expanduser("~/.hermes-hub"))
CONFIG_DIR = HUB_DIR / "config"
PATTERNS_DIR = HUB_DIR / "patterns"
GRAPH_FILE = CONFIG_DIR / "graph.json"
DATASET_FILE = HUB_DIR / "hermes_dataset.jsonl"

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "me", "more",
    "most", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so", "some",
    "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these",
    "they", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "we",
    "were", "what", "when", "where", "which", "while", "who", "whom", "why", "with", "would", "you",
    "your", "yours", "yourself", "yourselves", "patron", "pattern", "relevante", "para"
}


def _tokenize(text: str) -> List[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-\s]", " ", str(text).lower())
    tokens = [t.strip() for t in cleaned.split() if len(t.strip()) >= 3 and t.strip() not in STOPWORDS]
    return list(set(tokens))


def parse_frontmatter_and_content(file_path: Path) -> Dict[str, Any]:
    content = file_path.read_text(encoding="utf-8", errors="replace")
    frontmatter = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2]
            for line in fm_text.splitlines():
                if ":" in line and not line.startswith(" "):
                    k, v = line.split(":", 1)
                    frontmatter[k.strip()] = v.strip()

    title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else file_path.stem.replace("_", " ")

    return {
        "title": title,
        "frontmatter": frontmatter,
        "body": body.strip(),
        "keywords": _tokenize(body[:1500] + " " + title),
    }


def sync_patterns_to_synaptic_graph():
    print("=" * 65)
    print("🕸️ Sincronizando Patrones al Grafo Sináptico de Hermes Hub...")
    print("=" * 65)

    if not GRAPH_FILE.exists():
        graph = {"nodes": {}, "edges": []}
    else:
        with open(GRAPH_FILE, "r", encoding="utf-8") as f:
            graph = json.load(f)

    nodes = graph.setdefault("nodes", {})
    edges = graph.setdefault("edges", [])

    existing_pairs: Set[tuple] = set()
    for e in edges:
        u = e.get("source")
        v = e.get("target")
        if u and v:
            existing_pairs.add((min(u, v), max(u, v)))

    new_nodes_count = 0
    new_synapses_count = 0

    pattern_files = list(PATTERNS_DIR.glob("*.md"))
    print(f"📁 Total de notas de patrones encontradas en Vault: {len(pattern_files)}")

    for pfile in pattern_files:
        parsed = parse_frontmatter_and_content(pfile)
        node_id = f"pattern_{pfile.stem.lower().replace(' ', '_').replace('-', '_')}"

        if node_id not in nodes:
            nodes[node_id] = {
                "label": parsed["title"],
                "type": "pattern",
                "keywords": parsed["keywords"][:15],
                "path": str(pfile.relative_to(HUB_DIR)) if str(pfile).startswith(str(HUB_DIR)) else str(pfile),
                "summary": parsed["body"][:250],
                "created_at": parsed["frontmatter"].get("created", "2026-08-23"),
            }
            new_nodes_count += 1

        pattern_kws = set(parsed["keywords"])

        # Conectar sinápticamente con nodos afines existentes
        for other_id, other_data in nodes.items():
            if other_id == node_id:
                continue

            other_kws = set(other_data.get("keywords", []))
            common = pattern_kws.intersection(other_kws)

            if len(common) >= 2:
                pair = (min(node_id, other_id), max(node_id, other_id))
                if pair not in existing_pairs:
                    # Peso proporcional a afinidad semántica
                    weight = round(min(0.95, 0.45 + (len(common) * 0.10)), 2)
                    edges.append({
                        "source": pair[0],
                        "target": pair[1],
                        "weight": weight,
                        "relation": "semantic_affinity"
                    })
                    existing_pairs.add(pair)
                    new_synapses_count += 1

    # Guardar graph.json
    tmp_graph = GRAPH_FILE.with_suffix(".tmp")
    with open(tmp_graph, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)
    tmp_graph.replace(GRAPH_FILE)

    print(f"✅ Grafo actualizado exitosamente:")
    print(f"   • Nodos totales: {len(nodes)} (+{new_nodes_count} nuevos)")
    print(f"   • Sinapsis totales: {len(edges)} (+{new_synapses_count} nuevas)")

    # Actualizar dataset de entrenamiento hermes_dataset.jsonl
    if DATASET_FILE.exists():
        with open(DATASET_FILE, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()
    else:
        existing_lines = []

    dataset_keys = {json.loads(l).get("instruction") for l in existing_lines if l.strip()}
    new_dataset_entries = 0

    with open(DATASET_FILE, "a", encoding="utf-8") as f:
        for pfile in pattern_files:
            parsed = parse_frontmatter_and_content(pfile)
            instr = f"Explica el patrón de diseño y arquitectura de Hermes: {parsed['title']}"
            if instr not in dataset_keys:
                entry = {
                    "instruction": instr,
                    "input": "",
                    "output": parsed["body"][:1200]
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                dataset_keys.add(instr)
                new_dataset_entries += 1

    print(f"   • Ejemplos añadidos al dataset de Hermes: +{new_dataset_entries}")
    print("=" * 65)


if __name__ == "__main__":
    sync_patterns_to_synaptic_graph()
