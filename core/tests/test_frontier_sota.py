"""
test_frontier_sota.py — Suite de Pruebas Automatizadas para las Capacidades de Frontera SOTA v3 de Hermes.
Valida:
1. AST Code-Graph Parser (Multi-lenguaje: Python, TypeScript, Rust, Go).
2. Execution Feedback Engine (Refuerzo Hebbiano y alertas de riesgo).
3. Late Interaction Token-to-Token MaxSim Scorer.
4. Dream Consolidation Daemon (Modo Sueño y poda de memoria).
"""
import unittest
import tempfile
from pathlib import Path

import sys
core_dir = Path(__file__).resolve().parent.parent
if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))

from ast_graph_parser import ASTCodeGraphParser, get_ast_parser
from feedback_engine import ExecutionFeedbackEngine, get_feedback_engine
from late_interaction import LateInteractionScorer, get_late_interaction_scorer
from dream_daemon import DreamConsolidationDaemon


class TestFrontierSOTA(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp_dir.name)
        self.ast_parser = ASTCodeGraphParser(self.workspace)
        self.feedback_engine = get_feedback_engine()
        self.late_scorer = get_late_interaction_scorer()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_ast_multi_language_parsing(self):
        """Valida que el parser AST procese Python, TypeScript, Rust y Go."""
        # 1. Archivo Python
        py_file = self.workspace / "service.py"
        py_file.write_text("""
from fastapi import FastAPI, Depends

class DatabaseManager:
    def __init__(self):
        pass

async def get_db_session():
    yield None
""", encoding="utf-8")

        # 2. Archivo TypeScript
        ts_file = self.workspace / "auth.ts"
        ts_file.write_text("""
export interface UserSession {
    id: string;
    token: string;
}

export const authenticateUser = async (token: string): Promise<UserSession> => {
    return { id: "1", token };
};
""", encoding="utf-8")

        # 3. Archivo Rust
        rs_file = self.workspace / "engine.rs"
        rs_file.write_text("""
pub struct RedlockClient {
    pub quorum: usize,
}

pub async fn acquire_distributed_lock(resource: &str) -> bool {
    true
}
""", encoding="utf-8")

        # 4. Archivo Go
        go_file = self.workspace / "worker.go"
        go_file.write_text("""
package main

type TaskWorker struct {
    Queue string
}

func ProcessJob(jobID string) error {
    return nil
}
""", encoding="utf-8")

        report = self.ast_parser.scan_workspace_symbols()
        self.assertGreaterEqual(report["files_scanned"], 4)
        self.assertGreaterEqual(report["total_symbols_extracted"], 6)

        extracted_names = [s["name"] for s in report["symbols"]]
        self.assertIn("DatabaseManager", extracted_names)
        self.assertIn("get_db_session", extracted_names)
        self.assertIn("authenticateUser", extracted_names)
        self.assertIn("RedlockClient", extracted_names)
        self.assertIn("ProcessJob", extracted_names)

        print(f"\n[Test] AST Multi-Language Parser: {report['total_symbols_extracted']} símbolos extraídos de 4 lenguajes.")

    def test_execution_feedback_reinforcement(self):
        """Valida que el feedback de ejecución actualice estadísticas y pesos sinápticos."""
        p_success = ["fastapi_async_pattern", "redis_cache_pattern"]
        res_ok = self.feedback_engine.record_execution_result(
            pattern_ids=p_success,
            success=True,
            task_type="pytest",
            execution_time_ms=45.2
        )
        self.assertEqual(res_ok["status"], "success")
        self.assertTrue(res_ok["execution_success"])
        self.assertEqual(res_ok["delta_applied"], 0.05)

        stats = self.feedback_engine.get_pattern_reliability("fastapi_async_pattern")
        self.assertGreaterEqual(stats["total_runs"], 1)
        self.assertGreaterEqual(stats["success_rate"], 0.5)

        print(f"\n[Test] Feedback Engine: Recompensa aplicada con éxito (+0.05). Reliability: {stats['success_rate']*100}%")

    def test_late_interaction_maxsim(self):
        """Valida que Late Interaction calcule el score MaxSim token-to-token con alta fidelidad."""
        query = "async redis redlock distributed locking"
        candidates = [
            {"label": "Redis Distributed Lock with Redlock", "summary": "Implements async redis redlock lease mutex."},
            {"label": "PostgreSQL Migration", "summary": "Database table schema migration with alembic."},
            {"label": "React Redux State", "summary": "Frontend client-side state store."}
        ]
        rescored = self.late_scorer.rescore_candidates(query, candidates, top_k=3)
        self.assertEqual(len(rescored), 3)
        # El primer candidato debe ser el de Redis
        self.assertEqual(rescored[0]["label"], "Redis Distributed Lock with Redlock")
        self.assertGreater(rescored[0]["maxsim_score"], rescored[1]["maxsim_score"])
        print(f"\n[Test] Late Interaction MaxSim: Top match '{rescored[0]['label']}' (MaxSim: {rescored[0]['maxsim_score']})")

    def test_dream_consolidation_cycle(self):
        """Valida la ejecución de un ciclo de consolidación 'Modo Sueño'."""
        daemon = DreamConsolidationDaemon(decay_factor=0.999)
        cycle_res = daemon.run_single_cycle()
        self.assertIn("status", cycle_res)
        self.assertIn("pruned_edges", cycle_res)
        print(f"\n[Test] Dream Consolidation Daemon: Ciclo ejecutado exitosamente.")



if __name__ == "__main__":
    unittest.main()
