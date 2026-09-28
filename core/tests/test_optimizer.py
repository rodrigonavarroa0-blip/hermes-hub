"""
test_optimizer.py - Suite de pruebas unitarias y de integración para el Optimizador
Compatible con unittest y pytest sin dependencias externas obligatorias.
"""

import sys
import json
import os
import tempfile
import unittest
from pathlib import Path

# Add core to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from optimizer import (
    TokenBudgetManager,
    ValidationSandbox,
    StrategyOrchestrator,
    CompactPromptEngine,
    HermesKnowledgeBridge,
    LLMClientWrapper,
    MockLLMClient,
    IterativeCodeOptimizer,
    StrategyType,
)


class TestTokenBudgetManager(unittest.TestCase):
    def test_token_budget_manager_basic(self):
        manager = TokenBudgetManager(budget=1000)
        self.assertEqual(manager.tokens_remaining, 1000)
        self.assertEqual(manager.percentage_used, 0.0)
        self.assertTrue(manager.has_budget(safety_margin=100))

        # Registrar consumo
        manager.record_usage(prompt_tokens=300, completion_tokens=200, total_tokens=500)
        self.assertEqual(manager.usage.total_tokens, 500)
        self.assertEqual(manager.tokens_remaining, 500)
        self.assertEqual(manager.percentage_used, 50.0)

        # Consumo que agota presupuesto
        manager.record_usage(prompt_tokens=250, completion_tokens=200, total_tokens=450)
        self.assertEqual(manager.usage.total_tokens, 950)
        self.assertEqual(manager.tokens_remaining, 50)
        self.assertFalse(manager.has_budget(safety_margin=100))

        summary = manager.summary()
        self.assertEqual(summary["budget"], 1000)
        self.assertEqual(summary["total_tokens"], 950)
        self.assertEqual(summary["tokens_remaining"], 50)


class TestValidationSandbox(unittest.TestCase):
    def test_sandbox_syntax_check(self):
        sandbox = ValidationSandbox()

        valid_code = "def foo(x: int) -> int:\n    return x * 2\n"
        is_valid, err = sandbox.check_syntax(valid_code)
        self.assertTrue(is_valid)
        self.assertIsNone(err)

        invalid_code = "def foo(x\n    return x *"
        is_valid, err = sandbox.check_syntax(invalid_code)
        self.assertFalse(is_valid)
        self.assertIn("SyntaxError", err)

    def test_sandbox_unit_tests_pass_and_fail(self):
        sandbox = ValidationSandbox(test_timeout=2.0)

        # Código correcto
        good_code = "def add(a, b): return a + b"
        test_harness = "def run_tests(): assert add(2, 3) == 5"
        bench_harness = "def run_benchmark(): return {'median_time': 0.001, 'min_time': 0.001, 'avg_time': 0.001, 'peak_memory_mb': 0.1}"

        report = sandbox.evaluate(good_code, test_harness, bench_harness)
        self.assertTrue(report.is_successful)
        self.assertTrue(report.tests_passed)
        self.assertTrue(report.bench_passed)
        self.assertEqual(report.median_time, 0.001)

        # Código que falla assertions
        bad_code = "def add(a, b): return a * b"
        report_bad = sandbox.evaluate(bad_code, test_harness, bench_harness)
        self.assertFalse(report_bad.is_successful)
        self.assertFalse(report_bad.tests_passed)
        self.assertIn("AssertionError", report_bad.traceback or "")

    def test_sandbox_timeout_handling(self):
        sandbox = ValidationSandbox(test_timeout=1.0)

        infinite_loop_code = "def add(a, b):\n    while True:\n        pass\n    return a + b"
        test_harness = "def run_tests(): add(2, 3)"
        bench_harness = "def run_benchmark(): return {}"

        report = sandbox.evaluate(infinite_loop_code, test_harness, bench_harness)
        self.assertFalse(report.is_successful)
        self.assertTrue(report.tests_timed_out)
        self.assertIn("Timeout", report.error_message)


class TestStrategyAndPromptEngine(unittest.TestCase):
    def test_strategy_orchestrator(self):
        orchestrator = StrategyOrchestrator()
        s0 = orchestrator.get_strategy(0)
        s1 = orchestrator.get_strategy(1)
        s2 = orchestrator.get_strategy(2)
        s3 = orchestrator.get_strategy(3)
        s4 = orchestrator.get_strategy(4)

        self.assertEqual(s0.type, StrategyType.BIG_O)
        self.assertEqual(s1.type, StrategyType.DATA_STRUCTURES)
        self.assertEqual(s2.type, StrategyType.CACHING_VECTORIZATION)
        self.assertEqual(s3.type, StrategyType.MICRO_OPTIMIZATION)
        self.assertEqual(s4.type, StrategyType.BIG_O)

    def test_compact_prompt_engine(self):
        engine = CompactPromptEngine()
        orchestrator = StrategyOrchestrator()
        strategy = orchestrator.get_strategy(0)

        prompt_init = engine.build_user_prompt(
            current_baseline_code="def fn(): pass",
            strategy=strategy,
            iteration=1,
        )
        self.assertIn("### ITERACIÓN #1", prompt_init)
        self.assertIn("def fn(): pass", prompt_init)

        prompt_regr = engine.build_user_prompt(
            current_baseline_code="def fn(): pass",
            strategy=strategy,
            iteration=2,
            previous_status="REJECTED_REGRESSION",
            previous_feedback="Fue 15% más lento.",
        )
        self.assertIn("⚠️ La versión previa pasó los tests pero fue MÁS LENTA", prompt_regr)
        self.assertIn("Fue 15% más lento.", prompt_regr)


class TestExtractionAndKnowledgeBridge(unittest.TestCase):
    def test_extract_code(self):
        raw_markdown = "Aquí está la solución:\n```python\ndef fast_fn():\n    return 42\n```\nFin de la explicación."
        extracted = LLMClientWrapper.extract_code(raw_markdown)
        self.assertEqual(extracted, "def fast_fn():\n    return 42")

        raw_plain = "def plain_fn():\n    return 1"
        self.assertEqual(LLMClientWrapper.extract_code(raw_plain), "def plain_fn():\n    return 1")

    def test_hermes_draft_generation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            bridge = HermesKnowledgeBridge(hub_path=tmp_dir)
            draft_file = bridge.save_winning_draft(
                candidate_code="def optimized(): pass",
                baseline_code="def baseline(): pass",
                initial_time=0.100,
                final_time=0.010,
                speedup_pct=90.0,
                tokens_used=1200,
                iterations=3,
                winning_strategy="Data Structures",
            )

            self.assertIsNotNone(draft_file)
            self.assertTrue(draft_file.exists())
            content = draft_file.read_text(encoding="utf-8")
            self.assertIn("speedup_percentage: 90.00%", content)
            self.assertIn("def optimized(): pass", content)
            self.assertIn("def baseline(): pass", content)


if __name__ == "__main__":
    unittest.main()
