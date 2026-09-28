"""
feedback_engine.py — Motor de Aprendizaje por Refuerzo y Bucle de Feedback de Ejecución (Execution RL Loop).
Permite que Hermes aprenda y re-calibre el peso de las sinapsis basándose en el éxito o fallo real
de pruebas unitarias, builds o ejecuciones de código de agentes.
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from core.typed_graph import TypedPropertyGraphEngine, get_typed_graph_engine
except ImportError:
    from typed_graph import TypedPropertyGraphEngine, get_typed_graph_engine

HUB_PATH = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_PATH / "config"
FEEDBACK_LOG_FILE = CONFIG_DIR / "execution_feedback_history.jsonl"
FEEDBACK_STATS_FILE = CONFIG_DIR / "execution_feedback_stats.json"


class ExecutionFeedbackEngine:
    """
    Gestiona el aprendizaje por refuerzo:
    1. Éxito de test/build -> Refuerzo positivo Hebbiano (+delta de peso) y aumento de confianza.
    2. Fallo de test/build -> Penalización (-delta) y creación de enlace causal 'execution_risk'.
    """

    def __init__(self, typed_engine: Optional[TypedPropertyGraphEngine] = None):
        self.engine = typed_engine or get_typed_graph_engine()
        self.log_file = FEEDBACK_LOG_FILE
        self.stats_file = FEEDBACK_STATS_FILE
        self._load_stats()

    def _load_stats(self):
        if self.stats_file.exists():
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    self.stats = json.load(f)
            except Exception:
                self.stats = {}
        else:
            self.stats = {}

    def _save_stats(self):
        tmp = self.stats_file.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2)
        tmp.replace(self.stats_file)

    def record_execution_result(
        self,
        pattern_ids: List[str],
        success: bool,
        task_type: str = "unit_test",
        execution_time_ms: float = 0.0,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registra el resultado de una ejecución y actualiza las sinapsis y estadísticas.
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        delta = 0.05 if success else -0.08

        # 1. Registrar en log JSONL
        log_entry = {
            "timestamp": timestamp,
            "pattern_ids": pattern_ids,
            "success": success,
            "task_type": task_type,
            "execution_time_ms": execution_time_ms,
            "error_message": error_message
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        # 2. Actualizar estadísticas acumuladas
        for pid in pattern_ids:
            if pid not in self.stats:
                self.stats[pid] = {
                    "total_runs": 0,
                    "success_runs": 0,
                    "failure_runs": 0,
                    "success_rate": 1.0,
                    "last_error": None
                }
            st = self.stats[pid]
            st["total_runs"] += 1
            if success:
                st["success_runs"] += 1
            else:
                st["failure_runs"] += 1
                st["last_error"] = str(error_message)[:200]
            st["success_rate"] = round(st["success_runs"] / st["total_runs"], 3)

        self._save_stats()

        # 3. Aplicar Refuerzo Hebbiano sobre las sinapsis entre patrones
        synapses_updated = []
        if len(pattern_ids) >= 2:
            for i in range(len(pattern_ids)):
                for j in range(i + 1, len(pattern_ids)):
                    p1, p2 = pattern_ids[i], pattern_ids[j]
                    if p1 in self.engine.nodes and p2 in self.engine.nodes:
                        rel_type = "co_activated" if success else "execution_risk"
                        current_weight = 0.5
                        # Buscar arista existente
                        for edge in self.engine.edges:
                            s, t = edge.get("source"), edge.get("target")
                            if (s == p1 and t == p2) or (s == p2 and t == p1):
                                current_weight = float(edge.get("weight", 0.5))
                                break

                        new_weight = max(0.05, min(0.99, current_weight + delta))
                        res = self.engine.add_typed_relation(
                            source=p1,
                            target=p2,
                            relation_type=rel_type,
                            weight=round(new_weight, 3),
                            metadata={"last_task": task_type, "last_result": "success" if success else "failure"}
                        )
                        synapses_updated.append(res)

        return {
            "status": "success",
            "recorded_patterns": pattern_ids,
            "execution_success": success,
            "delta_applied": delta,
            "synapses_updated_count": len(synapses_updated),
            "stats_summary": {pid: self.stats.get(pid, {}) for pid in pattern_ids}
        }

    def get_pattern_reliability(self, pattern_id: str) -> Dict[str, Any]:
        """Obtiene la fiabilidad empírica de un patrón."""
        return self.stats.get(pattern_id, {
            "total_runs": 0,
            "success_runs": 0,
            "failure_runs": 0,
            "success_rate": 1.0,
            "status": "untested"
        })


# Singleton
_FEEDBACK_ENGINE: Optional[ExecutionFeedbackEngine] = None


def get_feedback_engine() -> ExecutionFeedbackEngine:
    global _FEEDBACK_ENGINE
    if _FEEDBACK_ENGINE is None:
        _FEEDBACK_ENGINE = ExecutionFeedbackEngine()
    return _FEEDBACK_ENGINE


if __name__ == "__main__":
    fb = get_feedback_engine()
    res = fb.record_execution_result(["fastapi_async", "redis_pubsub"], success=True, task_type="pytest")
    print(f"Feedback registrado: {res}")
