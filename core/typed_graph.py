"""
typed_graph.py — Motor de Grafo de Propiedades Tipado y Relaciones Causales de Hermes Hub.
Permite enriquecer las conexiones sinápticas con semántica relacional formal:
- 'mitigates_antipattern': El patrón resuelve o previene un error o vulnerabilidad conocida.
- 'replaces_obsolete': La técnica sustituye una API o biblioteca deprecada.
- 'depends_on': Requisito técnico o infraestructura necesaria para funcionar.
- 'implements_cluster': Pertenencia y cohesión dentro de una familia tecnológica.
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Any

HUB_PATH = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_PATH / "config"
GRAPH_FILE = CONFIG_DIR / "graph.json"


class TypedPropertyGraphEngine:
    """
    Extensión del motor sináptico que gestiona relaciones tipadas y consultas causales.
    """

    RELATION_TYPES = {
        "mitigates_antipattern",
        "replaces_obsolete",
        "depends_on",
        "implements_cluster",
        "semantic_affinity",
        "co_activated",
        "dream_cluster_attachment"
    }

    def __init__(self, graph_file: Optional[Path] = None):
        self.graph_file = graph_file or GRAPH_FILE
        self._load_graph()

    def _load_graph(self):
        if self.graph_file.exists():
            with open(self.graph_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.nodes = data.get("nodes", {})
                self.edges = data.get("edges", [])
        else:
            self.nodes = {}
            self.edges = []

    def add_typed_relation(
        self,
        source: str,
        target: str,
        relation_type: str,
        weight: float = 0.85,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Añade o actualiza una relación tipada entre dos nodos."""
        if source not in self.nodes or target not in self.nodes:
            return {"status": "error", "message": f"Uno de los nodos ({source} o {target}) no existe"}

        pair_key = (min(source, target), max(source, target))
        updated = False

        for edge in self.edges:
            s = edge.get("source")
            t = edge.get("target")
            if (min(s, t), max(s, t)) == pair_key:
                edge["relation"] = relation_type
                edge["weight"] = weight
                if metadata:
                    edge["metadata"] = metadata
                updated = True
                break

        if not updated:
            self.edges.append({
                "source": source,
                "target": target,
                "relation": relation_type,
                "weight": weight,
                "metadata": metadata or {}
            })

        self._save_graph()
        return {
            "status": "success",
            "action": "updated" if updated else "created",
            "source": source,
            "target": target,
            "relation": relation_type,
            "weight": weight
        }

    def query_causal_relations(self, node_id: str, relation_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Busca todas las conexiones causales y dependencias de un nodo."""
        results = []
        for edge in self.edges:
            s = edge.get("source")
            t = edge.get("target")
            rel = edge.get("relation", "semantic_affinity")

            if s == node_id or t == node_id:
                other_id = t if s == node_id else s
                if relation_type and rel != relation_type:
                    continue

                other_node = self.nodes.get(other_id, {})
                results.append({
                    "related_node_id": other_id,
                    "relation": rel,
                    "weight": edge.get("weight", 0.5),
                    "label": other_node.get("label", other_id),
                    "type": other_node.get("type", "unknown"),
                    "summary": other_node.get("summary", "")[:200]
                })

        return sorted(results, key=lambda x: x["weight"], reverse=True)

    def _save_graph(self):
        tmp_file = self.graph_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump({"nodes": self.nodes, "edges": self.edges}, f, indent=2, ensure_ascii=False)
        tmp_file.replace(self.graph_file)


# Singleton
_TYPED_ENGINE: Optional[TypedPropertyGraphEngine] = None


def get_typed_graph_engine() -> TypedPropertyGraphEngine:
    global _TYPED_ENGINE
    if _TYPED_ENGINE is None:
        _TYPED_ENGINE = TypedPropertyGraphEngine()
    return _TYPED_ENGINE


if __name__ == "__main__":
    engine = get_typed_graph_engine()
    print(f"Typed Property Graph: {len(engine.nodes)} nodos, {len(engine.edges)} aristas.")
