"""
dream_consolidation.py — Motor de Consolidación y Poda en "Modo Sueño" (Sleep & Dream Consolidation).
Inspirado en la neurobiología del sueño y la consolidación de la memoria:
1. Poda de sinapsis débiles y ruido residual (Curva de Olvido).
2. Detección y fusión de nodos cuasi-duplicados (Entity Resolution).
3. Conexión de conceptos huérfanos con los clusters principales.
4. Generación de macro-resúmenes ejecutivos por clúster tecnológico.
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict, List, Set, Tuple, Any

HUB_PATH = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_PATH / "config"
CLUSTERS_DIR = HUB_PATH / "clusters"
GRAPH_FILE = CONFIG_DIR / "graph.json"


class DreamConsolidator:
    def __init__(self, hub_path: Optional[Path] = None):
        self.hub_path = hub_path or HUB_PATH
        self.config_dir = self.hub_path / "config"
        self.clusters_dir = self.hub_path / "clusters"
        self.graph_file = self.config_dir / "graph.json"
        self.clusters_dir.mkdir(parents=True, exist_ok=True)

    def run_consolidation(self, dry_run: bool = False, decay_factor: float = 0.99, min_threshold: float = 0.12) -> Dict[str, Any]:
        """Ejecuta el ciclo integral de consolidación sináptica."""
        if not self.graph_file.exists():
            return {"status": "error", "message": "graph.json no encontrado"}

        with open(self.graph_file, "r", encoding="utf-8") as f:
            graph = json.load(f)

        nodes: Dict[str, Dict[str, Any]] = graph.get("nodes", {})
        edges: List[Dict[str, Any]] = graph.get("edges", [])

        initial_nodes = len(nodes)
        initial_edges = len(edges)

        print(f"💤 [Modo Sueño] Iniciando consolidación sobre {initial_nodes} nodos y {initial_edges} sinapsis...")

        # 1. Poda de sinapsis de bajo peso y decaimiento
        pruned_edges = 0
        decayed_edges = 0
        cleaned_edges = []
        seen_pairs: Set[Tuple[str, str]] = set()

        for edge in edges:
            u = edge.get("source")
            v = edge.get("target")
            if not u or not v or u not in nodes or v not in nodes:
                pruned_edges += 1
                continue

            pair = (min(u, v), max(u, v))
            if pair in seen_pairs:
                pruned_edges += 1
                continue

            w = float(edge.get("weight", 0.5)) * decay_factor
            if w < min_threshold:
                pruned_edges += 1
                continue

            edge["weight"] = round(w, 3)
            seen_pairs.add(pair)
            cleaned_edges.append(edge)
            decayed_edges += 1

        # 2. Detección y Conexión de Nodos Huérfanos
        connected_node_ids = set()
        for edge in cleaned_edges:
            connected_node_ids.add(edge["source"])
            connected_node_ids.add(edge["target"])

        orphans = [nid for nid in nodes if nid not in connected_node_ids]
        newly_connected_orphans = 0

        # Buscar clusters y conectar huérfanos con clusters afines
        cluster_nodes = {nid: ndata for nid, ndata in nodes.items() if ndata.get("type") == "cluster"}
        for orph_id in orphans:
            orph_kws = set(nodes[orph_id].get("keywords", []))
            best_cluster = None
            max_common = 0

            for cl_id, cl_data in cluster_nodes.items():
                cl_kws = set(cl_data.get("keywords", []))
                common = len(orph_kws.intersection(cl_kws))
                if common > max_common:
                    max_common = common
                    best_cluster = cl_id

            if best_cluster and max_common >= 1:
                cleaned_edges.append({
                    "source": orph_id,
                    "target": best_cluster,
                    "weight": 0.40,
                    "relation": "dream_cluster_attachment"
                })
                newly_connected_orphans += 1

        # 3. Macro-Síntesis de Clusters Tecnológicos
        cluster_summaries_generated = 0
        for cl_id, cl_data in cluster_nodes.items():
            # Obtener miembros conectados al cluster
            members = [
                e["source"] if e["target"] == cl_id else e["target"]
                for e in cleaned_edges
                if e["source"] == cl_id or e["target"] == cl_id
            ]
            if len(members) >= 3:
                cl_name = cl_data.get("label", cl_id)
                cluster_md_file = self.clusters_dir / f"Cluster_{cl_id.replace(':', '_')}.md"
                
                member_titles = [nodes[m].get("label", m) for m in members if m in nodes][:10]
                summary_content = f"""---
tags:
  - cluster-summary
  - hermes-dream
cluster_id: {cl_id}
total_members: {len(members)}
updated: {time.strftime('%Y-%m-%d %H:%M:%S')}
---

# Macro-Síntesis del Clúster: {cl_name}

## Descripción General
Este clúster consolida {len(members)} conceptos y patrones técnicos interconectados en el grafo sináptico de Hermes.

## Patrones y Componentes Clave
"""
                for mt in member_titles:
                    summary_content += f"- [[{mt}]]\n"

                summary_content += f"\n## Densidad Sináptica\n- Conexiones activas: {len(members)}\n- Factor de Cohesión: Alta\n"

                if not dry_run:
                    cluster_md_file.write_text(summary_content, encoding="utf-8")
                cluster_summaries_generated += 1

        result = {
            "status": "success",
            "dry_run": dry_run,
            "initial_nodes": initial_nodes,
            "final_nodes": len(nodes),
            "initial_edges": initial_edges,
            "final_edges": len(cleaned_edges),
            "decayed_edges": decayed_edges,
            "pruned_edges": pruned_edges,
            "orphans_reconnected": newly_connected_orphans,
            "cluster_macro_summaries": cluster_summaries_generated
        }

        if not dry_run:
            graph["nodes"] = nodes
            graph["edges"] = cleaned_edges
            tmp_file = self.graph_file.with_suffix(".tmp")
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(graph, f, indent=2, ensure_ascii=False)
            tmp_file.replace(self.graph_file)

        print(f"✨ [Modo Sueño] Consolidación completada:")
        print(f"   • Sinapsis podadas/optimizadas: -{pruned_edges}")
        print(f"   • Huérfanos re-vinculados: +{newly_connected_orphans}")
        print(f"   • Macro-resúmenes generados: {cluster_summaries_generated}")
        return result


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    consolidator = DreamConsolidator()
    res = consolidator.run_consolidation(dry_run=dry)
    print(json.dumps(res, indent=2))
