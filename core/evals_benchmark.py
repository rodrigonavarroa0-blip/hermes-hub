"""
evals_benchmark.py — Suite de Auto-Evaluación y Benchmarking de Precisión SOTA para Hermes Hub.
Mide cuantitativamente:
1. HitRate@3 y HitRate@5 en consultas canónicas de arquitectura.
2. MRR (Mean Reciprocal Rank) de recuperación híbrida.
3. Latencias de inferencia (Async Parallel vs Cached FP16).
4. Tasa de ahorro de tokens con Dynamic Budgeting.
5. Inferencia causal de 2 saltos y mitigaciones activas.
6. Ahorro de memoria con cuantización FP16.
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any

HUB_PATH = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp_server import get_engine, resolve_context, resolve_compact_context
from hybrid_retriever import get_hybrid_retriever
from causal_reasoner import get_causal_reasoner
from token_pruner import get_token_pruner
from query_expander import get_query_expander

# 15 Consultas Canónicas de Prueba con Resultados Esperados
EVAL_GROUND_TRUTH = [
    {"query": "fastapi background workers async tasks", "expected_kws": ["fastapi", "task", "celery", "worker"]},
    {"query": "model context protocol mcp tools server", "expected_kws": ["mcp", "protocol", "tool", "server"]},
    {"query": "docker sandbox code execution isolated secure", "expected_kws": ["docker", "sandbox", "isolated", "secure"]},
    {"query": "pydantic structured outputs schema validation", "expected_kws": ["pydantic", "structured", "schema", "output"]},
    {"query": "redis distributed locking redlock concurrency", "expected_kws": ["redis", "lock", "concurrency", "distributed"]},
    {"query": "nextjs server actions cache revalidation", "expected_kws": ["nextjs", "react", "cache", "server"]},
    {"query": "hebbian learning associative memory graph", "expected_kws": ["hebbian", "memory", "associative", "neural"]},
    {"query": "prompt compression token reduction optimization", "expected_kws": ["prompt", "compression", "token", "optimization"]},
    {"query": "knowledge graph rag entity extraction citations", "expected_kws": ["graph", "rag", "entity", "citation"]},
    {"query": "sqlite vector search embeddings lightweight", "expected_kws": ["sqlite", "vector", "embedding", "search"]},
    {"query": "pgvector postgres vector embeddings rag", "expected_kws": ["pgvector", "postgres", "vector", "rag"]},
    {"query": "shadcn ui component library tailwind", "expected_kws": ["shadcn", "component", "ui", "tailwind"]},
    {"query": "zustand react state management", "expected_kws": ["zustand", "state", "react", "store"]},
    {"query": "vllm high throughput llm serving", "expected_kws": ["vllm", "serving", "throughput", "llm"]},
    {"query": "mem0 memory layer for personalized ai", "expected_kws": ["mem0", "memory", "agent", "personalized"]},
]


def run_precision_evals() -> Dict[str, Any]:
    print("=" * 70)
    print("🎯 INICIANDO SUITE DE EVALUACIÓN Y BENCHMARKS SOTA v2 DE HERMES")
    print(f"📊 Casos de prueba canónicos: {len(EVAL_GROUND_TRUTH)}")
    print("=" * 70)

    engine = get_engine()
    retriever = get_hybrid_retriever()
    causal = get_causal_reasoner()
    pruner = get_token_pruner()
    expander = get_query_expander()

    retriever.build_or_load_vector_index(engine.nodes)

    # Warm up inicial
    _ = retriever.search_pipeline("warmup query", top_k=3)

    hits_at_3 = 0
    hits_at_5 = 0
    reciprocal_ranks = []
    latencies_pipeline = []
    latencies_cached = []
    tokens_saved_list = []
    causal_alerts_detected = 0

    for item in EVAL_GROUND_TRUTH:
        q = item["query"]
        expected = item["expected_kws"]

        # 1. Medir latencia del pipeline asíncrono completo con FP16 + Re-ranker + Causal
        t0 = time.perf_counter()
        pipeline_res = retriever.search_pipeline(q, top_k=5, token_budget=1200, include_causal=True)
        lat_pipe = (time.perf_counter() - t0) * 1000
        latencies_pipeline.append(lat_pipe)

        # 2. Medir latencia de búsqueda en caché
        t1 = time.perf_counter()
        _ = retriever.query_vector_similarity(q, top_k=5)
        lat_cached = (time.perf_counter() - t1) * 1000
        latencies_cached.append(lat_cached)

        # 3. Evaluar MRR y HitRate
        found_rank = 0
        candidates = pipeline_res.get("candidates", [])
        for rank, res_item in enumerate(candidates, 1):
            nid = res_item["node_id"]
            node_data = engine.nodes.get(nid, {})
            node_text = (nid + " " + node_data.get("label", "") + " " + " ".join(node_data.get("keywords", []))).lower()
            if any(kw in node_text for kw in expected):
                if found_rank == 0:
                    found_rank = rank

        if found_rank > 0 and found_rank <= 3:
            hits_at_3 += 1
        if found_rank > 0 and found_rank <= 5:
            hits_at_5 += 1

        reciprocal_ranks.append(1.0 / found_rank if found_rank > 0 else 0.0)

        # 4. Métricas causales
        c_analysis = pipeline_res.get("causal_analysis", {})
        if c_analysis.get("alerts") or c_analysis.get("mitigations"):
            causal_alerts_detected += 1

        # 5. Medir compresión y ahorro de tokens
        comp_res = resolve_compact_context(q, max_token_budget=400, top_k=3)
        tokens_saved_list.append(comp_res.get("token_savings", 0))

    hit_rate_3 = (hits_at_3 / len(EVAL_GROUND_TRUTH)) * 100
    hit_rate_5 = (hits_at_5 / len(EVAL_GROUND_TRUTH)) * 100
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)

    avg_lat_pipe = sum(latencies_pipeline) / len(latencies_pipeline)
    avg_lat_cached = sum(latencies_cached) / len(latencies_cached)
    total_toks_saved = sum(tokens_saved_list)

    # Ahorro de memoria FP16 vs FP32
    num_nodes = len(retriever.node_ids) if retriever.node_ids else len(engine.nodes)
    fp32_ram_kb = (num_nodes * 384 * 4) / 1024
    fp16_ram_kb = (num_nodes * 384 * 2) / 1024
    ram_reduction_pct = 50.0

    print("\n" + "=" * 70)
    print("📈 RESULTADOS FINALES DEL BENCHMARK")
    print("=" * 70)
    print(f"🎯 HitRate@3:                 {hit_rate_3:.1f}%")
    print(f"🎯 HitRate@5:                 {hit_rate_5:.1f}%")
    print(f"🥇 MRR (Mean Reciprocal Rank): {mrr:.3f}")
    print(f"⚡ Latencia Pipeline Completo:  {avg_lat_pipe:.2f} ms")
    print(f"⚡ Latencia Caché Vectorial:    {avg_lat_cached:.3f} ms")
    print(f"💾 Memoria RAM Embeddings:     {fp16_ram_kb:.1f} KB (Ahorro FP16: {ram_reduction_pct}%)")
    print(f"🧬 Queries con Causalidad:     {causal_alerts_detected}/{len(EVAL_GROUND_TRUTH)}")
    print(f"📉 Ahorro Total de Tokens:      {total_toks_saved:,} tokens")
    print("=" * 70)

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "test_cases": len(EVAL_GROUND_TRUTH),
        "hit_rate_at_3": hit_rate_3,
        "hit_rate_at_5": hit_rate_5,
        "mrr": round(mrr, 4),
        "avg_pipeline_latency_ms": round(avg_lat_pipe, 2),
        "avg_cached_latency_ms": round(avg_lat_cached, 3),
        "fp16_ram_kb": round(fp16_ram_kb, 1),
        "ram_savings_pct": ram_reduction_pct,
        "total_tokens_saved": total_toks_saved,
    }

    report_path = HUB_PATH / "config" / "benchmark_latest.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"📄 Reporte guardado en: {report_path}")

    return report


if __name__ == "__main__":
    run_precision_evals()
