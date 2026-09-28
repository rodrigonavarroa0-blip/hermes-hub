#!/usr/bin/env python3
"""
audit_clean_and_connect_skills.py
1. Audita y elimina skills duplicadas, vacías o inútiles en ~/.hermes-hub.
2. Conecta densamente todas las skills entre sí generando una red sináptica rica y coherente.
"""

import os
import sys
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple

HUB_ROOT = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_ROOT / "config"
GRAPH_FILE = CONFIG_DIR / "graph.json"


def _tokenize(text: str) -> List[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-\s]", " ", str(text).lower())
    return [t.strip() for t in cleaned.split() if len(t.strip()) >= 2]


def hash_content(content: str) -> str:
    cleaned = re.sub(r"\s+", " ", content.strip().lower())
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()


class KnowledgeAuditorAndConnector:
    def __init__(self):
        with open(GRAPH_FILE, "r", encoding="utf-8") as f:
            self.graph = json.load(f)

        self.nodes: Dict[str, dict] = self.graph.get("nodes", {})
        self.edges: List[dict] = self.graph.get("edges", [])
        self.removed_nodes = []
        self.removed_files = []

    def audit_and_clean(self):
        print("🔍 [1/3] Auditando skills duplicadas, vacías o de baja calidad...")
        
        seen_hashes: Dict[str, str] = {}
        seen_titles: Dict[str, str] = {}
        nodes_to_delete = set()

        for nid, ndata in list(self.nodes.items()):
            ntype = ndata.get("type", "skill")
            file_rel = ndata.get("file")
            label = ndata.get("label", nid).strip().lower()

            if ntype in ["cluster", "concept"] and not file_rel:
                continue

            if not file_rel:
                # Nodo sin archivo y no es cluster/concept
                nodes_to_delete.add(nid)
                self.removed_nodes.append((nid, "Sin archivo asociado"))
                continue

            full_path = HUB_ROOT / file_rel
            if not full_path.exists():
                nodes_to_delete.add(nid)
                self.removed_nodes.append((nid, "Archivo no existe en disco"))
                continue

            content = full_path.read_text(encoding="utf-8", errors="ignore").strip()

            # 1. Chequeo de contenido vacío o trivial (< 80 caracteres)
            if len(content) < 80:
                nodes_to_delete.add(nid)
                self.removed_nodes.append((nid, f"Contenido vacío o trivial ({len(content)} chars)"))
                if full_path.exists():
                    full_path.unlink()
                    self.removed_files.append(str(file_rel))
                continue

            # 2. Chequeo de duplicados por Hash de Contenido
            chash = hash_content(content)
            if chash in seen_hashes:
                existing_nid = seen_hashes[chash]
                nodes_to_delete.add(nid)
                self.removed_nodes.append((nid, f"Duplicado exacto de nodo {existing_nid}"))
                if full_path.exists() and full_path != (HUB_ROOT / self.nodes[existing_nid].get("file", "")):
                    full_path.unlink()
                    self.removed_files.append(str(file_rel))
                continue
            else:
                seen_hashes[chash] = nid

            # 3. Chequeo de títulos exactamente repetidos en la misma categoría
            title_key = f"{ntype}:{label}"
            if title_key in seen_titles:
                existing_nid = seen_titles[title_key]
                # Si el contenido actual es menor o igual, descartar
                existing_file = HUB_ROOT / self.nodes[existing_nid].get("file", "")
                existing_len = len(existing_file.read_text(encoding="utf-8", errors="ignore")) if existing_file.exists() else 0
                if len(content) <= existing_len:
                    nodes_to_delete.add(nid)
                    self.removed_nodes.append((nid, f"Título duplicado de {existing_nid}"))
                    if full_path.exists() and full_path != existing_file:
                        full_path.unlink()
                        self.removed_files.append(str(file_rel))
                    continue
                else:
                    nodes_to_delete.add(existing_nid)
                    self.removed_nodes.append((existing_nid, f"Reemplazado por versión más completa {nid}"))
                    seen_titles[title_key] = nid
            else:
                seen_titles[title_key] = nid

        # Aplicar borrado de nodos
        for nid in nodes_to_delete:
            if nid in self.nodes:
                del self.nodes[nid]

        print(f"🧹 Nodos eliminados por baja calidad/duplicación: {len(nodes_to_delete)}")
        print(f"📄 Archivos eliminados del disco: {len(self.removed_files)}")

    def clean_existing_edges(self):
        print("🧹 [2/3] Limpiando aristas huérfanas...")
        valid_edges = []
        for e in self.edges:
            src = e.get("source")
            tgt = e.get("target")
            if src in self.nodes and tgt in self.nodes and src != tgt:
                valid_edges.append(e)
        self.edges = valid_edges
        print(f"🔗 Aristas válidas preservadas: {len(self.edges)}")

    def densely_connect_skills(self):
        print("⚡ [3/3] Generando conexiones sinápticas densas entre skills...")
        
        # Inverted keyword mapping: keyword -> set of node_ids
        kw_map: Dict[str, Set[str]] = {}
        stopwords = {
            "and", "the", "for", "with", "using", "from", "into", "skill", "pattern",
            "antipattern", "code", "file", "overview", "guidelines", "best", "practices",
            "development", "expert", "sec", "n8n", "performing", "testing", "analyzing"
        }

        for nid, ndata in self.nodes.items():
            kws = ndata.get("keywords", [])
            label_tokens = _tokenize(ndata.get("label", ""))
            all_tokens = set(kws + label_tokens)
            
            for t in all_tokens:
                t_clean = t.lower().strip()
                if len(t_clean) >= 3 and t_clean not in stopwords:
                    kw_map.setdefault(t_clean, set()).add(nid)

        # Matriz de afinidad
        pair_scores: Dict[Tuple[str, str], int] = {}
        for kw, node_set in kw_map.items():
            if len(node_set) < 2 or len(node_set) > 80:  # Ignorar palabras demasiado ubicuas o únicas
                continue
            nodes_list = list(node_set)
            for i in range(len(nodes_list)):
                for j in range(i + 1, len(nodes_list)):
                    u, v = nodes_list[i], nodes_list[j]
                    pair = (min(u, v), max(u, v))
                    pair_scores[pair] = pair_scores.get(pair, 0) + 1

        existing_pairs = set((min(e["source"], e["target"]), max(e["source"], e["target"])) for e in self.edges)
        new_synapses = 0

        # Conectar nodos afines
        for (u, v), shared_count in pair_scores.items():
            if (u, v) in existing_pairs:
                continue

            type_u = self.nodes[u].get("type", "skill")
            type_v = self.nodes[v].get("type", "skill")

            # Definir peso y tipo de relación semántica
            if shared_count >= 5:
                weight = 0.90
            elif shared_count >= 3:
                weight = 0.80
            elif shared_count >= 2:
                weight = 0.70
            else:
                continue

            if type_u == "antipattern" or type_v == "antipattern":
                relation = "prevents"
            elif type_u == "cluster" or type_v == "cluster":
                relation = "contains"
            elif "n8n" in u and "n8n" in v:
                relation = "triggers"
            elif "sec" in u and "sec" in v:
                relation = "correlates_with"
            else:
                relation = "pairs_with"

            self.edges.append({
                "source": u,
                "target": v,
                "weight": weight,
                "relation": relation
            })
            existing_pairs.add((u, v))
            new_synapses += 1

        print(f"✨ Nuevas sinapsis semánticas generadas: {new_synapses}")
        print(f"🔗 Total final de Aristas Sinápticas: {len(self.edges)}")

    def save(self):
        self.graph["nodes"] = self.nodes
        self.graph["edges"] = self.edges
        with open(GRAPH_FILE, "w", encoding="utf-8") as f:
            json.dump(self.graph, f, indent=2, ensure_ascii=False)
        print(f"💾 Grafo guardado con éxito en {GRAPH_FILE}")


if __name__ == "__main__":
    runner = KnowledgeAuditorAndConnector()
    runner.audit_and_clean()
    runner.clean_existing_edges()
    runner.densely_connect_skills()
    runner.save()
