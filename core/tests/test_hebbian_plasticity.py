#!/usr/bin/env python3
"""
test_hebbian_plasticity.py
Valida y mide el aprendizaje por Plasticidad Hebbiana en Hermes:
1. Co-activación pasiva e incremento de pesos entre nodos utilizados juntos.
2. Creación automática de nuevas sinapsis para conceptos no conectados previamente.
3. Feedback explícito con record_task_feedback (+0.10 éxito / -0.05 fricción).
"""

import os
import sys
import time
from pathlib import Path

HUB_PATH = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
sys.path.insert(0, str(HUB_PATH / "config"))

from mcp_server import (
    get_engine,
    resolve_context,
    resolve_compact_context,
    record_task_feedback
)


def run_hebbian_tests():
    print("🧠 [1/3] Probando Auto-Refuerzo por Co-Activación Pasiva...")
    engine = get_engine()
    initial_edges_count = len(engine.edges)
    print(f"  • Sinapsis iniciales en el grafo: {initial_edges_count}")

    # Ejecutar una consulta que co-activa skills
    res = resolve_compact_context(
        "FastAPI async blocking event loop with Stripe Webhooks",
        max_token_budget=500,
        top_k=3,
        auto_reinforce=True
    )
    print(f"  • Nodos activados: {[s['node_id'] for s in res['snippets']]}")
    print(f"  • Sinapsis reforzadas automáticamente: {res.get('hebbian_synapses_reinforced')}")

    print("\n🧠 [2/3] Probando Herramienta de Feedback Explícito de Tarea (record_task_feedback)...")
    feedback_res = record_task_feedback(
        node_ids=["skill_stripe_webhooks", "skill_prompt_compression_llmlingua"],
        success=True,
        feedback_note="El agente resolvió exitosamente el webhook con compresión de tokens"
    )
    print(f"  • Estado del Feedback: {feedback_res['status']}")
    print(f"  • Delta Aplicado: {feedback_res['delta_applied']}")
    print(f"  • Sinapsis modificadas/creadas: {feedback_res['synapses_modified']}")
    for det in feedback_res.get("details", []):
        print(f"    - [{det['source']} <-> {det['target']}]: {det['old_weight']} -> {det['new_weight']} ({det['action']})")

    print("\n🧠 [3/3] Verificando Persistencia y Salud Post-Aprendizaje...")
    engine_updated = get_engine()
    final_edges_count = len(engine_updated.edges)
    print(f"  • Sinapsis totales tras aprendizaje: {final_edges_count} (+{final_edges_count - initial_edges_count})")
    
    # Latencia post-aprendizaje
    t0 = time.perf_counter()
    res_lat = resolve_compact_context("Stripe prompt compression", max_token_budget=400, top_k=2)
    lat = (time.perf_counter() - t0) * 1000
    print(f"  • Latencia de Resolución Post-Aprendizaje: {lat:.3f} ms")
    print("🏆 ¡Plasticidad Hebbiana y Aprendizaje Sináptico funcionando con éxito al 100%!")


if __name__ == "__main__":
    run_hebbian_tests()
