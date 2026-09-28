"""
test_sota_engine.py — Suite de Pruebas Automatizadas para el Motor de Inteligencia y Velocidad SOTA de Hermes.
Valida:
1. Razonamiento Causal Multi-Salto (2-Hop).
2. Poda Contextual Dinámica (Dynamic Token Budgeting).
3. Expansión Adaptativa de Consultas (HyDE).
4. Motor Híbrido Asíncrono con Embeddings FP16.
"""
import unittest
import asyncio
import numpy as np
from pathlib import Path

import sys
core_dir = Path(__file__).resolve().parent.parent
if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))

from causal_reasoner import CausalMultiHopReasoner, get_causal_reasoner
from token_pruner import ContextualTokenPruner, get_token_pruner
from query_expander import AdaptiveQueryExpander, get_query_expander
from hybrid_retriever import HybridGraphRetriever, get_hybrid_retriever


class TestSOTAEngine(unittest.TestCase):

    def setUp(self):
        self.reasoner = get_causal_reasoner()
        self.pruner = get_token_pruner()
        self.expander = get_query_expander()
        self.retriever = get_hybrid_retriever()

    def test_causal_multi_hop_reasoning(self):
        """Valida que el razonador causal extraiga relaciones de 1 y 2 saltos y genere alertas."""
        nodes = list(self.reasoner.engine.nodes.keys())
        self.assertTrue(len(nodes) > 0, "El grafo no tiene nodos cargados.")
        
        sample_seeds = nodes[:5]
        analysis = self.reasoner.analyze_2hop_causality(sample_seeds)
        
        self.assertIn("seed_nodes", analysis)
        self.assertIn("hop1_connections", analysis)
        self.assertIn("hop2_consequences", analysis)
        self.assertIn("alerts", analysis)
        self.assertIn("mitigations", analysis)
        
        md_report = self.reasoner.format_causal_report_markdown(analysis)
        self.assertIsInstance(md_report, str)
        print(f"\n[Test] Causal Reasoning: {len(analysis['alerts'])} alertas, {len(analysis['mitigations'])} mitigaciones detectadas.")

    def test_token_pruner_budgeting(self):
        """Valida que el token pruner respete el presupuesto sin romper código crítico."""
        sample_doc = """# Patrón de Inyección de Dependencias en FastAPI
Esta es una introducción redundante con texto largo. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam.

> [!WARNING]
> Nunca uses dependencias bloqueantes sin run_in_threadpool.

```python
from fastapi import Depends, FastAPI

app = FastAPI()

async def get_db_session():
    async with SessionLocal() as session:
        yield session
```

| Componente | Rol |
|---|---|
| FastAPI | Router |
| SQLAlchemy | ORM |

- Regla 1: Usar context managers asíncronos.
- Regla 2: Cerrar conexiones en finally.
"""
        budget = 75
        pruned = self.pruner.prune_markdown(sample_doc, token_budget=budget)
        pruned_tokens = self.pruner.estimate_tokens(pruned)
        
        # Debe preservar el código y la alerta
        self.assertIn("```python", pruned)
        self.assertIn("FastAPI", pruned)
        self.assertLessEqual(pruned_tokens, budget + 15, "Excedió significativamente el presupuesto de tokens.")
        print(f"\n[Test] Token Pruner: Original ~{self.pruner.estimate_tokens(sample_doc)} toks -> Podado ~{pruned_tokens} toks (Límite: {budget}).")

    def test_adaptive_query_expander(self):
        """Valida la detección y expansión adaptativa para queries abstractas vs específicas."""
        abstract_q = "auth seguro"
        enriched, terms = self.expander.expand_query(abstract_q)
        self.assertTrue(len(terms) > 0, "No generó expansiones para query abstracta.")
        self.assertIn("oauth2", terms)
        
        snippet = self.expander.generate_hypothetical_snippet(abstract_q)
        self.assertIn("auth seguro", snippet)
        print(f"\n[Test] Query Expander: '{abstract_q}' expandido a '{enriched}' (Términos: {terms})")

    def test_hybrid_search_fp16_pipeline(self):
        """Valida la ejecución del pipeline de búsqueda asíncrono con FP16 y re-ranking."""
        # 1. Warm-up / Primera consulta (carga modelos ONNX si no estaban en RAM)
        cold_res = self.retriever.search_pipeline("FastAPI async redis concurrency", top_k=3, token_budget=1000)
        
        # 2. Warm query (en caliente en memoria)
        warm_res = self.retriever.search_pipeline("FastAPI async redis concurrency", top_k=3, token_budget=1000)
        
        self.assertIn("latency_ms", warm_res)
        self.assertIn("candidates", warm_res)
        self.assertIn("causal_analysis", warm_res)
        self.assertLess(warm_res["latency_ms"], 40.0, f"La latencia en caliente ({warm_res['latency_ms']}ms) superó los 40ms.")
        
        # Validar precisión FP16 en los embeddings cargados
        if self.retriever.embeddings is not None:
            self.assertEqual(self.retriever.embeddings.dtype, np.float16)
        
        print(f"\n[Test] Hybrid Search Pipeline: Cold = {cold_res['latency_ms']:.2f}ms | Warm = {warm_res['latency_ms']:.2f}ms | Candidatos = {len(warm_res['candidates'])}")



if __name__ == "__main__":
    unittest.main()
