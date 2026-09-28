import os
import sys
import re
import json
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from datetime import datetime
from itertools import combinations

# FastMCP
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    try:
        from fastmcp import FastMCP
    except ImportError:
        class FastMCP:
            def __init__(self, name: str, **kwargs):
                self.name = name
            def tool(self, **kwargs):
                def decorator(fn):
                    return fn
                return decorator
            def resource(self, *args, **kwargs):
                def decorator(fn):
                    return fn
                return decorator
            def prompt(self, *args, **kwargs):
                def decorator(fn):
                    return fn
                return decorator
            def run(self, *args, **kwargs):
                print(f"FastMCP server '{self.name}' (fallback mode - install 'mcp' for live stdio/sse server)")

HUB_PATH = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_PATH / "config"
GRAPH_FILE = CONFIG_DIR / "graph.json"
EPISODIC_MEMORY_FILE = HUB_PATH / "config" / "episodic_memory.json"

mcp = FastMCP("HermesKnowledgeHub")


def _tokenize(text: str) -> List[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-\s]", " ", str(text).lower())
    return [t.strip() for t in cleaned.split() if len(t.strip()) >= 2]


def estimate_tokens(text: str) -> int:
    """Estimación precisa de tokens (aprox 1 token = 3.8 caracteres en código/markdown)."""
    return max(1, int(len(text) / 3.8))


class FastQueryCache:
    """Caché ultrarrápido en memoria para respuestas precalculadas (< 0.05ms)."""
    def __init__(self, max_size: int = 500, ttl_seconds: float = 300.0):
        self.cache: Dict[str, Tuple[float, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            ts, val = self.cache[key]
            if time.time() - ts < self.ttl:
                return val
            else:
                del self.cache[key]
        return None

    def set(self, key: str, val: Any):
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][0])
            del self.cache[oldest_key]
        self.cache[key] = (time.time(), val)

    def clear(self):
        self.cache.clear()


class HermesGraphEngine:
    """
    Motor de Activación Propagada y Plasticidad Hebbiana (Living Synaptic Graph).
    Aprende, refuerza y crea conexiones automáticamente con cada resolución.
    """
    def __init__(self, graph_data: dict):
        self.nodes: Dict[str, Any] = graph_data.get("nodes", {})
        self.edges: List[Dict[str, Any]] = graph_data.get("edges", [])
        
        # 1. Mapa de Aristas O(1) para búsqueda rápida
        self.edge_map: Dict[Tuple[str, str], int] = {}
        # 2. Lista de Adyacencia O(1)
        self.adj: Dict[str, List[Tuple[str, float]]] = {nid: [] for nid in self.nodes}

        for idx, edge in enumerate(self.edges):
            src = edge.get("source")
            tgt = edge.get("target")
            w = float(edge.get("weight", 0.5))
            if src in self.nodes and tgt in self.nodes:
                pair_key = (min(src, tgt), max(src, tgt))
                self.edge_map[pair_key] = idx
                self.adj[src].append((tgt, w))
                self.adj[tgt].append((src, w))
                
        # 3. Índice Invertido de Tokens O(1)
        self.token_index: Dict[str, Set[str]] = {}
        for nid, ndata in self.nodes.items():
            kws = ndata.get("keywords", [])
            label_tokens = _tokenize(ndata.get("label", ""))
            nid_tokens = _tokenize(nid)
            all_tokens = set([k.lower() for k in kws] + label_tokens + nid_tokens)
            for token in all_tokens:
                if token not in self.token_index:
                    self.token_index[token] = set()
                self.token_index[token].add(nid)

        self._dirty = False

    def activate(self, query: str, top_k: int = 5, decay: float = 0.65, max_hops: int = 2) -> List[Tuple[str, float]]:
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []

        node_scores: Dict[str, float] = {}
        for token in q_tokens:
            matching_nodes = self.token_index.get(token, set())
            for nid in matching_nodes:
                node_scores[nid] = node_scores.get(nid, 0.0) + 1.0

        if not node_scores:
            return []

        max_init = max(node_scores.values())
        active_frontier: Dict[str, float] = {
            nid: score / max_init 
            for nid, score in node_scores.items() 
            if (score / max_init) >= 0.2
        }

        final_energy: Dict[str, float] = dict(active_frontier)
        for _ in range(max_hops):
            next_frontier: Dict[str, float] = {}
            for u, energy in active_frontier.items():
                if energy < 0.05:
                    continue
                for v, weight in self.adj.get(u, []):
                    propagated = energy * weight * decay
                    if propagated > next_frontier.get(v, 0.0):
                        next_frontier[v] = propagated
                        final_energy[v] = max(final_energy.get(v, 0.0), propagated)
            active_frontier = next_frontier

        sorted_nodes = sorted(final_energy.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_k]

    def reinforce_hebbian(self, node_ids: List[str], delta: float = 0.02, relation: str = "co_activated") -> List[dict]:
        """
        Aplica la Regla de Hebb ('Neurons that fire together, wire together').
        Refuerza o crea sinapsis entre todos los pares de nodos co-activados.
        """
        valid_nodes = [nid for nid in node_ids if nid in self.nodes]
        if len(valid_nodes) < 2:
            return []

        updated_synapses = []
        for u, v in combinations(valid_nodes, 2):
            pair_key = (min(u, v), max(u, v))
            if pair_key in self.edge_map:
                # Arista existente: ajustar peso
                idx = self.edge_map[pair_key]
                old_w = float(self.edges[idx].get("weight", 0.5))
                new_w = round(max(0.1, min(1.0, old_w + delta)), 3)
                self.edges[idx]["weight"] = new_w
                if relation and relation != "co_activated":
                    self.edges[idx]["relation"] = relation
                
                # Actualizar listas de adyacencia
                self._update_adj_weight(u, v, new_w)
                self._update_adj_weight(v, u, new_w)
                
                updated_synapses.append({
                    "source": u,
                    "target": v,
                    "old_weight": old_w,
                    "new_weight": new_w,
                    "action": "reinforced" if delta > 0 else "attenuated"
                })
            elif delta > 0:
                # Nueva conexión sináptica aprendida
                init_w = round(min(1.0, 0.35 + delta), 3)
                new_edge = {
                    "source": u,
                    "target": v,
                    "weight": init_w,
                    "relation": relation
                }
                new_idx = len(self.edges)
                self.edges.append(new_edge)
                self.edge_map[pair_key] = new_idx
                self.adj[u].append((v, init_w))
                self.adj[v].append((u, init_w))
                
                updated_synapses.append({
                    "source": u,
                    "target": v,
                    "old_weight": 0.0,
                    "new_weight": init_w,
                    "action": "new_synapse_created"
                })

        if updated_synapses:
            self._dirty = True
            self.save_graph_safely()

        return updated_synapses

    def _update_adj_weight(self, u: str, v: str, new_w: float):
        if u in self.adj:
            for i, (target, _) in enumerate(self.adj[u]):
                if target == v:
                    self.adj[u][i] = (target, new_w)
                    break

    def decay_synapses(self, decay_factor: float = 0.99, min_threshold: float = 0.10) -> Dict[str, Any]:
        """
        Aplica la Curva de Olvido de Ebbinghaus (Decaimiento Hebbiano gradual) a las sinapsis.
        Atenúa suavemente los pesos y poda conexiones muertas que caen por debajo del umbral mínimo.
        """
        decayed_count = 0
        pruned_count = 0
        new_edges = []
        new_edge_map = {}
        self.adj = {nid: [] for nid in self.nodes}

        for edge in self.edges:
            src = edge.get("source")
            tgt = edge.get("target")
            w = float(edge.get("weight", 0.5))
            new_w = round(w * decay_factor, 3)

            if new_w < min_threshold:
                pruned_count += 1
                continue

            edge["weight"] = new_w
            pair_key = (min(src, tgt), max(src, tgt))
            new_edge_map[pair_key] = len(new_edges)
            new_edges.append(edge)
            self.adj[src].append((tgt, new_w))
            self.adj[tgt].append((src, new_w))
            decayed_count += 1

        self.edges = new_edges
        self.edge_map = new_edge_map
        self._dirty = True
        self.save_graph_safely()
        _QUERY_CACHE.clear()

        return {
            "decayed_synapses": decayed_count,
            "pruned_synapses": pruned_count,
            "active_synapses": len(self.edges),
            "decay_factor": decay_factor,
            "min_threshold": min_threshold
        }

    def save_graph_safely(self):
        """Guarda el grafo de forma atómica en disco."""
        if not self._dirty:
            return
        try:
            temp_file = GRAPH_FILE.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump({"nodes": self.nodes, "edges": self.edges}, f, indent=2, ensure_ascii=False)
            temp_file.replace(GRAPH_FILE)
            self._dirty = False
        except Exception as e:
            print(f"⚠️ Error guardando graph.json: {e}", file=sys.stderr)


# Singletons & Cache
_ENGINE: Optional[HermesGraphEngine] = None
_LAST_GRAPH_MTIME: float = 0.0
_QUERY_CACHE = FastQueryCache(max_size=1000, ttl_seconds=600.0)


def get_engine() -> HermesGraphEngine:
    global _ENGINE, _LAST_GRAPH_MTIME
    if not GRAPH_FILE.exists():
        return HermesGraphEngine({"nodes": {}, "edges": []})

    mtime = GRAPH_FILE.stat().st_mtime
    if _ENGINE is None or mtime > _LAST_GRAPH_MTIME:
        with open(GRAPH_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        _ENGINE = HermesGraphEngine(data)
        _LAST_GRAPH_MTIME = mtime
        _QUERY_CACHE.clear()
    return _ENGINE


def compress_markdown_content(raw_text: str) -> str:
    """Comprime texto markdown eliminando comentarios HTML y exceso de líneas en blanco."""
    text = re.sub(r"<!--.*?-->", "", raw_text, flags=re.DOTALL)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


@mcp.tool()
def resolve_context(query: str, top_k: int = 4, auto_reinforce: bool = True) -> dict:
    """
    Resuelve contexto sináptico instantáneo (<1ms) utilizando Spreading Activation y Caché Semántico.
    Aplica Plasticidad Hebbiana reforzando las sinapsis entre conceptos co-activados.
    """
    cache_key = f"resolve:{top_k}:{query.strip().lower()}"
    cached = _QUERY_CACHE.get(cache_key)
    if cached:
        cached["from_cache"] = True
        return cached

    t0 = time.perf_counter()
    engine = get_engine()
    activations = engine.activate(query, top_k=top_k)

    results = []
    total_tokens = 0
    activated_nids = [nid for nid, _ in activations]

    for nid, score in activations:
        ndata = engine.nodes.get(nid, {})
        rel_file = ndata.get("file")
        content = ""
        if rel_file:
            fpath = HUB_PATH / rel_file
            if fpath.exists():
                content = fpath.read_text(encoding="utf-8", errors="ignore")

        toks = estimate_tokens(content)
        total_tokens += toks

        results.append({
            "node_id": nid,
            "label": ndata.get("label", nid),
            "type": ndata.get("type", "skill"),
            "energy_score": round(score, 4),
            "file": rel_file,
            "content": content,
            "estimated_tokens": toks
        })

    # Auto-refuerzo Hebbiano pasivo
    synapses_updated = []
    if auto_reinforce and len(activated_nids) >= 2:
        synapses_updated = engine.reinforce_hebbian(activated_nids[:3], delta=0.02, relation="co_activated")

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
    response = {
        "query": query,
        "elapsed_ms": elapsed_ms,
        "from_cache": False,
        "total_estimated_tokens": total_tokens,
        "nodes_found": len(results),
        "hebbian_synapses_reinforced": len(synapses_updated),
        "results": results
    }
    _QUERY_CACHE.set(cache_key, response)
    return response


@mcp.tool()
def resolve_compact_context(query: str, max_token_budget: int = 800, top_k: int = 5, auto_reinforce: bool = True) -> dict:
    """
    Resuelve contexto con Límite Estricto de Tokens (Token Budget Pruning).
    Aplica compresión de contenido, poda de contexto y plasticidad sináptica automática.
    """
    cache_key = f"compact:{max_token_budget}:{top_k}:{query.strip().lower()}"
    cached = _QUERY_CACHE.get(cache_key)
    if cached:
        cached["from_cache"] = True
        return cached

    t0 = time.perf_counter()
    engine = get_engine()
    activations = engine.activate(query, top_k=top_k)

    compact_snippets = []
    consumed_tokens = 0
    original_tokens = 0
    activated_nids = []

    for nid, score in activations:
        ndata = engine.nodes.get(nid, {})
        rel_file = ndata.get("file")
        if not rel_file:
            continue
        
        fpath = HUB_PATH / rel_file
        if not fpath.exists():
            continue

        raw_content = fpath.read_text(encoding="utf-8", errors="ignore")
        orig_toks = estimate_tokens(raw_content)
        original_tokens += orig_toks

        compressed = compress_markdown_content(raw_content)
        comp_toks = estimate_tokens(compressed)

        remaining_budget = max_token_budget - consumed_tokens
        if remaining_budget <= 50:
            break

        if comp_toks > remaining_budget:
            char_limit = int(remaining_budget * 3.8)
            compressed = compressed[:char_limit] + "\n... [Contexto truncado por límite de tokens]"
            comp_toks = estimate_tokens(compressed)

        consumed_tokens += comp_toks
        activated_nids.append(nid)
        compact_snippets.append({
            "node_id": nid,
            "title": ndata.get("label", nid),
            "energy": round(score, 3),
            "compressed_content": compressed,
            "tokens": comp_toks
        })

    # Auto-refuerzo Hebbiano pasivo
    synapses_updated = []
    if auto_reinforce and len(activated_nids) >= 2:
        synapses_updated = engine.reinforce_hebbian(activated_nids, delta=0.02, relation="co_activated")

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
    tokens_saved = max(0, original_tokens - consumed_tokens)
    ratio = round((tokens_saved / original_tokens * 100), 1) if original_tokens > 0 else 0.0

    response = {
        "query": query,
        "elapsed_ms": elapsed_ms,
        "from_cache": False,
        "token_budget_requested": max_token_budget,
        "tokens_consumed": consumed_tokens,
        "tokens_saved": tokens_saved,
        "token_savings_percent": f"{ratio}%",
        "hebbian_synapses_reinforced": len(synapses_updated),
        "snippets": compact_snippets
    }
    _QUERY_CACHE.set(cache_key, response)
    return response


@mcp.tool()
def record_task_feedback(node_ids: List[str], success: bool, feedback_note: Optional[str] = None) -> dict:
    """
    Herramienta de Plasticidad Hebbiana Explícita.
    Permite al agente o usuario reforzar (+0.10) o atenuar (-0.05) las sinapsis utilizadas tras completar una tarea.
    """
    engine = get_engine()
    delta = 0.10 if success else -0.05
    relation = "task_success_reinforced" if success else "task_friction_attenuated"
    
    updated = engine.reinforce_hebbian(node_ids, delta=delta, relation=relation)
    
    # Invalidar caché de queries para reflejar los nuevos pesos
    _QUERY_CACHE.clear()

    return {
        "status": "success",
        "task_success": success,
        "delta_applied": delta,
        "synapses_modified": len(updated),
        "details": updated,
        "feedback_note": feedback_note
    }


@mcp.tool()
def save_episodic_memory(conversation_id: str, summary: str, extracted_facts: List[str]) -> dict:
    """
    Guarda memoria episódica estructurada (estilo Mem0/Zep) para recordar conversaciones pasadas en <1ms.
    """
    EPISODIC_MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    memories = {}
    if EPISODIC_MEMORY_FILE.exists():
        try:
            with open(EPISODIC_MEMORY_FILE, "r", encoding="utf-8") as f:
                memories = json.load(f)
        except Exception:
            memories = {}

    entry = {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "facts": extracted_facts
    }

    if conversation_id not in memories:
        memories[conversation_id] = []
    memories[conversation_id].append(entry)

    with open(EPISODIC_MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memories, f, indent=2, ensure_ascii=False)

    return {
        "status": "success",
        "conversation_id": conversation_id,
        "total_episodes": len(memories[conversation_id]),
        "facts_stored": len(extracted_facts)
    }


@mcp.tool()
def get_episodic_memory(conversation_id: Optional[str] = None, keyword_filter: Optional[str] = None) -> dict:
    """
    Recupera memoria conversacional y hechos extraídos al instante.
    """
    if not EPISODIC_MEMORY_FILE.exists():
        return {"episodes": [], "total_facts": 0}

    with open(EPISODIC_MEMORY_FILE, "r", encoding="utf-8") as f:
        memories = json.load(f)

    if conversation_id and conversation_id in memories:
        target_episodes = memories[conversation_id]
    else:
        target_episodes = [ep for eps in memories.values() for ep in eps]

    if keyword_filter:
        kw = keyword_filter.lower()
        target_episodes = [
            ep for ep in target_episodes 
            if kw in ep.get("summary", "").lower() or any(kw in f.lower() for f in ep.get("facts", []))
        ]

    return {
        "retrieved_episodes": len(target_episodes),
        "episodes": target_episodes
    }


@mcp.tool()
def get_global_memory() -> dict:
    """Devuelve las estadísticas y salud global del grafo sináptico de Hermes."""
    engine = get_engine()
    return {
        "hub_root": str(HUB_PATH),
        "total_nodes": len(engine.nodes),
        "total_edges": len(engine.edges),
        "node_types": {
            t: sum(1 for n in engine.nodes.values() if n.get("type") == t)
            for t in set(n.get("type", "skill") for n in engine.nodes.values())
        }
    }


@mcp.tool()
def research_github_patterns(topic: str, language: Optional[str] = None, max_results: int = 3) -> dict:
    """
    Investiga repositorios en GitHub en tiempo real, destila patrones de diseño con Google Gemini y guarda notas automáticas en el Vault de Hermes (~/.hermes-hub/patterns).
    """
    research_dir = Path(__file__).resolve().parent.parent / "research"
    if str(research_dir) not in sys.path:
        sys.path.insert(0, str(research_dir))
    try:
        from loop import run_cycle
        notes = run_cycle(topic=topic, language=language, n=max_results, sleep_between=0.5)
        return {
            "status": "success",
            "topic": topic,
            "language": language,
            "patterns_extracted": len(notes),
            "notes": notes
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


@mcp.tool()
def query_research_memory(keyword: str, limit: int = 5) -> dict:
    """
    Consulta patrones técnicos y lecciones aprendidas previamente destiladas en la memoria de Hermes sin llamadas externas.
    """
    research_dir = Path(__file__).resolve().parent.parent / "research"
    if str(research_dir) not in sys.path:
        sys.path.insert(0, str(research_dir))
    try:
        from memory_store import query_notes
        results = query_notes(keyword=keyword, limit=limit)
        return {
            "status": "success",
            "keyword": keyword,
            "found_count": len(results),
            "results": results
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


@mcp.tool()
def apply_synaptic_decay(decay_factor: float = 0.99, min_threshold: float = 0.10) -> dict:
    """
    Aplica la curva de olvido Hebbiana gradual a las sinapsis de Hermes Hub, podando conexiones obsoletas.
    """
    engine = get_engine()
    result = engine.decay_synapses(decay_factor=decay_factor, min_threshold=min_threshold)
    return {
        "status": "success",
        **result
    }


@mcp.tool()
def resolve_hybrid_context(
    query: str,
    max_token_budget: int = 500,
    top_k: int = 3,
    alpha: float = 0.5,
    auto_reinforce: bool = True
) -> dict:
    """
    Recuperación híbrida SOTA: Fusiona embeddings vectoriales densos (FastEmbed ONNX)
    con propagación de energía sináptica Hebbiana y comprime el contexto para el agente.
    """
    engine = get_engine()
    core_dir = Path(__file__).resolve().parent
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))

    try:
        from hybrid_retriever import get_hybrid_retriever
        retriever = get_hybrid_retriever()
        synaptic_results = engine.activate(query, top_k=top_k * 2)
        vector_results = retriever.query_vector_similarity(query, top_k=top_k * 2)
        fused = retriever.hybrid_fuse_ranks(synaptic_results, vector_results, top_k=top_k, alpha=alpha)

        active_nids = [item["node_id"] for item in fused]
        reinforced = 0
        if auto_reinforce and len(active_nids) >= 2:
            updated = engine.reinforce_hebbian(active_nids, delta=0.02, relation="hybrid_co_activated")
            reinforced = len(updated)

        snippets = []
        current_tokens = 0
        for item in fused:
            nid = item["node_id"]
            ndata = engine.nodes.get(nid, {})
            snippet_text = f"[{ndata.get('type', 'pattern')}] {ndata.get('label', nid)}:\n{ndata.get('summary', '')}"
            t_est = estimate_tokens(snippet_text)
            if current_tokens + t_est <= max_token_budget or not snippets:
                snippets.append({
                    "node_id": nid,
                    "type": ndata.get("type"),
                    "title": ndata.get("label"),
                    "rrf_score": item.get("rrf_score"),
                    "snippet": snippet_text,
                    "estimated_tokens": t_est
                })
                current_tokens += t_est

        return {
            "status": "success",
            "query": query,
            "hybrid_fused_nodes": len(fused),
            "token_budget_used": current_tokens,
            "max_token_budget": max_token_budget,
            "hebbian_synapses_reinforced": reinforced,
            "snippets": snippets
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


@mcp.tool()
def run_sleep_consolidation(dry_run: bool = False, decay_factor: float = 0.99) -> dict:
    """
    Ejecuta el ciclo de consolidación en modo sueño: poda de ruido, re-conexión de huérfanos y macro-síntesis de clusters.
    """
    core_dir = Path(__file__).resolve().parent
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    try:
        from dream_consolidation import DreamConsolidator
        consolidator = DreamConsolidator()
        return consolidator.run_consolidation(dry_run=dry_run, decay_factor=decay_factor)
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


@mcp.tool()
def resolve_predictive_context(file_path: Optional[str] = None, tech_stack: Optional[List[str]] = None) -> dict:
    """
    Inyección predictiva de contexto para IDEs: Detecta el stack en uso y precarga las 3 reglas de oro y antipatrones de Hermes.
    """
    core_dir = Path(__file__).resolve().parent
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    try:
        from predictive_context import resolve_predictive_context as rpc
        return rpc(file_path=file_path, tech_stack=tech_stack)
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


@mcp.tool()
def query_causal_relations(node_id: str, relation_type: Optional[str] = None) -> dict:
    """
    Consulta relaciones semánticas causales (mitigates_antipattern, depends_on, replaces_obsolete) en el grafo de Hermes.
    """
    core_dir = Path(__file__).resolve().parent
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    try:
        from typed_graph import get_typed_graph_engine
        engine = get_typed_graph_engine()
        relations = engine.query_causal_relations(node_id=node_id, relation_type=relation_type)
        return {
            "status": "success",
            "node_id": node_id,
            "relation_filter": relation_type,
            "total_relations": len(relations),
            "relations": relations
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


@mcp.tool()
def scan_workspace_antipatterns(workspace_path: Optional[str] = None) -> dict:
    """
    Escanea el espacio de trabajo en busca de violaciones a las reglas de oro de Hermes y antipatrones de arquitectura.
    """
    core_dir = Path(__file__).resolve().parent
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    try:
        from smart_watcher import SmartWorkspaceWatcher
        watcher = SmartWorkspaceWatcher(workspace_path=Path(workspace_path) if workspace_path else None)
        report = watcher.scan_workspace()
        return {
            "status": "success",
            **report
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


@mcp.tool()
def rerank_context_snippets(query: str, snippets: List[dict], top_k: int = 3) -> dict:
    """
    Reordena fragmentos de contexto usando el Re-ranker Cross-Encoder de alta precisión de Hermes.
    """
    core_dir = Path(__file__).resolve().parent
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    try:
        from reranker import get_reranker
        reranker = get_reranker()
        reranked = reranker.rerank(query=query, candidates=snippets, top_k=top_k)
        return {
            "status": "success",
            "query": query,
            "top_k": top_k,
            "reranked_snippets": reranked
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


@mcp.tool()
def hermes_hybrid_search(
    query: str,
    top_k: int = 5,
    token_budget: int = 1500,
    include_causal: bool = True
) -> dict:
    """
    Búsqueda híbrida SOTA de 5ta Generación en Hermes Hub:
    - Embeddings densos cuantizados FP16 en memoria + BM25 léxico.
    - Expansión adaptativa de consulta (HyDE ligero).
    - Re-ranker Neuronal Cross-Encoder.
    - Razonamiento causal multi-salto (2-Hop) y advertencias preventivas.
    - Poda contextual de tokens con Dynamic Budgeting.
    """
    core_dir = Path(__file__).resolve().parent
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    try:
        from hybrid_retriever import get_hybrid_retriever
        retriever = get_hybrid_retriever()
        result = retriever.search_pipeline(
            query=query,
            top_k=top_k,
            token_budget=token_budget,
            include_causal=include_causal
        )
        return {
            "status": "success",
            **result
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


@mcp.tool()
def hermes_causal_audit(seed_patterns: List[str]) -> dict:
    """
    Audita y evalúa el impacto causal de arquitectura de 2 saltos (2-Hop Causal Reasoning)
    para un conjunto de patrones o tecnologías, detectando dependencias transitivas y riesgos de antipatrones.
    """
    core_dir = Path(__file__).resolve().parent
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    try:
        from causal_reasoner import get_causal_reasoner
        reasoner = get_causal_reasoner()
        analysis = reasoner.analyze_2hop_causality(seed_patterns)
        report_md = reasoner.format_causal_report_markdown(analysis)
        return {
            "status": "success",
            "analysis": analysis,
            "markdown_report": report_md
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


@mcp.tool()
def hermes_ast_scan(workspace_path: Optional[str] = None, max_files: int = 150) -> dict:
    """
    Escaneo estructural de código con AST multi-lenguaje (Python, TypeScript, Rust, Go).
    Extrae funciones, clases, decorators e imports, y los vincula automáticamente con los patrones de Hermes.
    """
    core_dir = Path(__file__).resolve().parent
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    try:
        from ast_graph_parser import get_ast_parser
        parser = get_ast_parser(Path(workspace_path) if workspace_path else None)
        scan_result = parser.scan_workspace_symbols(max_files=max_files)
        return {
            "status": "success",
            **scan_result
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


@mcp.tool()
def hermes_record_execution_result(
    pattern_ids: List[str],
    success: bool,
    task_type: str = "unit_test",
    execution_time_ms: float = 0.0,
    error_message: Optional[str] = None
) -> dict:
    """
    Bucle de Aprendizaje por Refuerzo (Execution RL Loop):
    Registra el éxito (+recompensa) o fallo (-alerta de riesgo) de compilación y tests para calibrar sinapsis Hebbianas.
    """
    core_dir = Path(__file__).resolve().parent
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    try:
        from feedback_engine import get_feedback_engine
        engine = get_feedback_engine()
        result = engine.record_execution_result(
            pattern_ids=pattern_ids,
            success=success,
            task_type=task_type,
            execution_time_ms=execution_time_ms,
            error_message=error_message
        )
        return result
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


@mcp.tool()
def hermes_trigger_dream_cycle(decay_factor: float = 0.995, min_threshold: float = 0.10) -> dict:
    """
    Dispara un ciclo de consolidación 'Modo Sueño' (Sleep & Dream Consolidation):
    Poda sinapsis muertas, fusiona duplicados y descubre nuevos clusters de manera autónoma.
    """
    core_dir = Path(__file__).resolve().parent
    if str(core_dir) not in sys.path:
        sys.path.insert(0, str(core_dir))
    try:
        from dream_daemon import DreamConsolidationDaemon
        daemon = DreamConsolidationDaemon(decay_factor=decay_factor)
        result = daemon.run_single_cycle()
        return {
            "status": "success",
            "consolidation_result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }




if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hermes FastMCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio", help="Transporte de comunicación")
    parser.add_argument("--host", default="0.0.0.0", help="Host para el servidor SSE")
    parser.add_argument("--port", type=int, default=8765, help="Puerto para el servidor SSE")
    args, unknown = parser.parse_known_args()

    if args.transport == "sse":
        print(f"🚀 Iniciando Hermes FastMCP Server sobre SSE en http://{args.host}:{args.port}")
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
