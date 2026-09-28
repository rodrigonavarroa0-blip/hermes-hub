"""
causal_reasoner.py — Motor de Razonamiento Causal Multi-Salto (2-Hop) de Hermes Hub.
Permite evaluar dependencias de segundo orden, conflictos de arquitectura y mitigaciones preventivas
a partir del grafo de propiedades tipado de Hermes.
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from collections import defaultdict

try:
    from core.typed_graph import TypedPropertyGraphEngine, get_typed_graph_engine
except ImportError:
    from typed_graph import TypedPropertyGraphEngine, get_typed_graph_engine

HUB_PATH = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()


class CausalMultiHopReasoner:
    """
    Motor de inferencia causal que realiza recorridos de 2 saltos en el grafo
    para detectar riesgos arquitectónicos, pre-requisitos y mitigaciones automáticas.
    """

    def __init__(self, typed_engine: Optional[TypedPropertyGraphEngine] = None):
        self.engine = typed_engine or get_typed_graph_engine()
        self._build_fast_adjacency()

    def _build_fast_adjacency(self):
        """Construye un índice de adyacencia ordenado por peso y tipo de relación."""
        self.adj = defaultdict(list)
        for edge in self.engine.edges:
            s = edge.get("source")
            t = edge.get("target")
            rel = edge.get("relation", "semantic_affinity")
            w = edge.get("weight", 0.5)
            meta = edge.get("metadata", {})

            # Dar mayor prioridad de orden a relaciones causales explícitas
            priority = 2.0 if rel in ("mitigates_antipattern", "depends_on", "replaces_obsolete") else 1.0

            self.adj[s].append({"neighbor": t, "relation": rel, "weight": w, "priority_weight": w * priority, "direction": "outgoing", "meta": meta})
            self.adj[t].append({"neighbor": s, "relation": rel, "weight": w, "priority_weight": w * priority, "direction": "incoming", "meta": meta})

        # Ordenar adyacencias por peso efectivo descendente
        for node in self.adj:
            self.adj[node].sort(key=lambda x: x["priority_weight"], reverse=True)

    def reload(self):
        """Recarga el grafo y reconstruye la adyacencia."""
        self.engine._load_graph()
        self._build_fast_adjacency()

    def analyze_2hop_causality(self, seed_node_ids: List[str], max_hop1: int = 15, max_hop2: int = 10) -> Dict[str, Any]:
        """
        Ejecuta un análisis causal de 2 saltos de alto rendimiento (<1ms) partiendo de nodos semilla.
        """
        seed_set = set(seed_node_ids[:5])
        hop1_results = {}
        hop2_results = {}
        alerts: List[Dict[str, str]] = []
        mitigations: List[Dict[str, str]] = []
        dependencies: List[Dict[str, str]] = []

        visited = set(seed_set)

        # 1er Salto
        for seed in seed_set:
            if seed not in self.engine.nodes:
                continue
            seed_label = self.engine.nodes[seed].get("label", seed)
            hop1_edges = self.adj.get(seed, [])[:max_hop1]

            hop1_results[seed] = []
            for edge in hop1_edges:
                nbr = edge["neighbor"]
                rel = edge["relation"]
                w = edge["weight"]
                nbr_node = self.engine.nodes.get(nbr, {})
                nbr_label = nbr_node.get("label", nbr)
                nbr_type = nbr_node.get("type", "unknown")

                hop1_results[seed].append({
                    "from_node": seed,
                    "to_node": nbr,
                    "label": nbr_label,
                    "relation": rel,
                    "weight": w,
                    "type": nbr_type
                })

                # Clasificar semántica causal directa
                if rel == "mitigates_antipattern":
                    mitigations.append({
                        "pattern": seed_label,
                        "mitigates": nbr_label,
                        "details": f"El patrón '{seed_label}' mitiga activamente el riesgo/antipatrón '{nbr_label}'."
                    })
                elif rel == "depends_on":
                    dependencies.append({
                        "source": seed_label,
                        "requires": nbr_label,
                        "details": f"'{seed_label}' depende directamente de '{nbr_label}'."
                    })
                elif rel == "replaces_obsolete":
                    alerts.append({
                        "type": "deprecation",
                        "title": f"Tecnología obsoleta reemplazada por {seed_label}",
                        "message": f"'{seed_label}' sustituye a '{nbr_label}', la cual está deprecada."
                    })

                # 2do Salto
                if nbr not in visited:
                    visited.add(nbr)
                    hop2_edges = self.adj.get(nbr, [])[:max_hop2]
                    hop2_results[nbr] = []

                    for edge2 in hop2_edges:
                        nbr2 = edge2["neighbor"]
                        if nbr2 in visited:
                            continue
                        rel2 = edge2["relation"]
                        w2 = edge2["weight"]
                        nbr2_node = self.engine.nodes.get(nbr2, {})
                        nbr2_label = nbr2_node.get("label", nbr2)
                        nbr2_type = nbr2_node.get("type", "unknown")

                        hop2_entry = {
                            "origin_seed": seed,
                            "via_hop1": nbr,
                            "to_node": nbr2,
                            "label": nbr2_label,
                            "relation": rel2,
                            "combined_weight": round(w * w2, 3),
                            "type": nbr2_type
                        }
                        hop2_results[nbr].append(hop2_entry)

                        # Inferencia de segundo orden
                        if rel == "depends_on" and rel2 == "mitigates_antipattern":
                            mitigations.append({
                                "pattern": seed_label,
                                "indirect_mitigation": nbr2_label,
                                "via": nbr_label,
                                "details": f"A través de su dependencia '{nbr_label}', '{seed_label}' ayuda a prevenir '{nbr2_label}'."
                            })
                        elif rel == "depends_on" and rel2 == "depends_on":
                            dependencies.append({
                                "source": seed_label,
                                "transitive_requirement": nbr2_label,
                                "via": nbr_label,
                                "details": f"Dependencia transitiva: '{seed_label}' requiere '{nbr_label}', que a su vez requiere '{nbr2_label}'."
                            })
                        elif nbr2_type == "antipattern" or "antipattern" in nbr2.lower():
                            alerts.append({
                                "type": "antipattern_risk",
                                "title": f"Riesgo de Antipatrón de 2º Orden ({nbr2_label})",
                                "message": f"Atención: '{seed_label}' se conecta vía '{nbr_label}' con el riesgo conocido '{nbr2_label}'."
                            })

        return {
            "seed_nodes": seed_node_ids,
            "hop1_connections": hop1_results,
            "hop2_consequences": hop2_results,
            "alerts": alerts,
            "mitigations": mitigations,
            "dependencies": dependencies
        }

    def format_causal_report_markdown(self, analysis: Dict[str, Any]) -> str:
        """Formatea el análisis causal en un bloque Markdown estructurado y de alta señal."""
        lines = []
        alerts = analysis.get("alerts", [])
        mitigations = analysis.get("mitigations", [])
        deps = analysis.get("dependencies", [])

        if not alerts and not mitigations and not deps:
            return ""

        lines.append("\n### 🧬 Razonamiento Causal & Dependencias Multi-Salto")

        if alerts:
            lines.append("#### ⚠️ Alertas Preventivas de Arquitectura")
            for a in alerts[:5]:
                lines.append(f"- **{a.get('title', 'Alerta')}**: {a.get('message', '')}")

        if mitigations:
            lines.append("#### 🛡️ Mitigaciones Activas Detectadas")
            for m in mitigations[:5]:
                lines.append(f"- {m.get('details', '')}")

        if deps:
            lines.append("#### 🔗 Cadena de Dependencias y Requisitos")
            for d in deps[:5]:
                lines.append(f"- {d.get('details', '')}")

        return "\n".join(lines)


# Singleton
_CAUSAL_REASONER: Optional[CausalMultiHopReasoner] = None


def get_causal_reasoner() -> CausalMultiHopReasoner:
    global _CAUSAL_REASONER
    if _CAUSAL_REASONER is None:
        _CAUSAL_REASONER = CausalMultiHopReasoner()
    return _CAUSAL_REASONER


if __name__ == "__main__":
    reasoner = get_causal_reasoner()
    # Test con algunos nodos semilla de ejemplo
    sample_nodes = list(reasoner.engine.nodes.keys())[:3]
    print(f"Probando análisis causal para nodos: {sample_nodes}")
    res = reasoner.analyze_2hop_causality(sample_nodes)
    print(reasoner.format_causal_report_markdown(res))
