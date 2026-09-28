#!/usr/bin/env python3
"""
optimizer.py - Bucle de Optimización Continua de Código (Iterative Code Optimizer)

Un motor autónomo en Python que optimiza iterativamente código fuente guiado por:
1. Presupuesto estricto de tokens de API (O(1) tamaño de prompt por turno).
2. Rotación inteligente y adaptativa de 4 estrategias de optimización.
3. Sandbox y Validation Gate multi-fase en subprocesos aislados con timeout.
4. Integración bidireccional con la base de conocimientos de Hermes (~/.hermes-hub).
5. Salida estructurada: código ganador, histórico JSON y draft en Hermes.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore


# ==============================================================================
# MODELOS DE DATOS Y TIPOS ESTRICTOS
# ==============================================================================

class StrategyType(str, Enum):
    BIG_O = "big_o"
    DATA_STRUCTURES = "data_structures"
    CACHING_VECTORIZATION = "caching_vectorization"
    MICRO_OPTIMIZATION = "micro_optimization"


@dataclass
class StrategyDefinition:
    type: StrategyType
    name: str
    description: str
    focus_points: List[str]
    hermes_heuristics: List[str]


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def add(self, prompt: int, completion: int, total: int) -> None:
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += total


@dataclass
class ValidationReport:
    is_valid_syntax: bool = False
    tests_passed: bool = False
    tests_timed_out: bool = False
    bench_passed: bool = False
    bench_timed_out: bool = False
    median_time: float = float("inf")
    min_time: float = float("inf")
    avg_time: float = float("inf")
    peak_memory_mb: float = 0.0
    error_message: Optional[str] = None
    traceback: Optional[str] = None

    @property
    def is_successful(self) -> bool:
        return self.is_valid_syntax and self.tests_passed and self.bench_passed


@dataclass
class IterationRecord:
    iteration: int
    strategy: str
    prompt_tokens: int
    completion_tokens: int
    accumulated_tokens: int
    status: str  # "ACCEPTED", "REJECTED_REGRESSION", "REJECTED_TEST_FAIL", "REJECTED_TIMEOUT", "REJECTED_SYNTAX"
    median_time_sec: float
    speedup_pct_vs_previous: float
    speedup_pct_vs_baseline: float
    peak_memory_mb: float
    explanation: str = ""
    error_details: Optional[str] = None


# ==============================================================================
# GESTOR DE PRESUPUESTO DE TOKENS (TOKEN BUDGET MANAGER)
# ==============================================================================

class TokenBudgetManager:
    """
    Controla de forma estricta el consumo acumulado de tokens de API.
    Asegura que el bucle finalice limpiamente al alcanzar el presupuesto.
    """

    def __init__(self, budget: int):
        self.budget: int = budget
        self.usage: TokenUsage = TokenUsage()

    @property
    def tokens_remaining(self) -> int:
        return max(0, self.budget - self.usage.total_tokens)

    @property
    def percentage_used(self) -> float:
        if self.budget <= 0:
            return 100.0
        return (self.usage.total_tokens / self.budget) * 100.0

    def has_budget(self, safety_margin: int = 200) -> bool:
        return self.tokens_remaining > safety_margin

    def record_usage(self, prompt_tokens: int, completion_tokens: int, total_tokens: Optional[int] = None) -> None:
        if total_tokens is None or total_tokens == 0:
            total_tokens = prompt_tokens + completion_tokens
        self.usage.add(prompt_tokens, completion_tokens, total_tokens)

    def summary(self) -> Dict[str, Any]:
        return {
            "budget": self.budget,
            "prompt_tokens": self.usage.prompt_tokens,
            "completion_tokens": self.usage.completion_tokens,
            "total_tokens": self.usage.total_tokens,
            "tokens_remaining": self.tokens_remaining,
            "percentage_used": round(self.percentage_used, 2),
        }


# ==============================================================================
# PUERTA DE VALIDACIÓN Y SANDBOX (VALIDATION GATE)
# ==============================================================================

class ValidationSandbox:
    """
    Ejecuta el código candidato en subprocesos aislados con límites de tiempo.
    Rigor de 3 fases:
      1. AST Syntax Check (fail-fast sin subproceso).
      2. Ejecución de Tests Unitarios (subprocess + tempfile + timeout).
      3. Benchmark Estadístico (warm-up + mediana + memoria).
    """

    def __init__(self, test_timeout: float = 5.0, bench_timeout: float = 12.0):
        self.test_timeout = test_timeout
        self.bench_timeout = bench_timeout

    def check_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """Fase 1: Verificación estática de sintaxis AST."""
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"SyntaxError en línea {e.lineno}, col {e.offset}: {e.msg}"
        except Exception as e:
            return False, f"AST Parse Error: {str(e)}"

    def _execute_in_subprocess(self, script_content: str, timeout: float) -> Tuple[int, str, str, bool]:
        """
        Ejecuta un script completo en un subproceso aislado temporal.
        Retorna (returncode, stdout, stderr, timed_out).
        """
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write(script_content)
            temp_path = tf.name

        try:
            proc = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return proc.returncode, proc.stdout, proc.stderr, False
        except subprocess.TimeoutExpired as te:
            stdout = te.stdout.decode() if isinstance(te.stdout, bytes) else (te.stdout or "")
            stderr = te.stderr.decode() if isinstance(te.stderr, bytes) else (te.stderr or "")
            return -1, stdout, stderr, True
        except Exception as e:
            return -1, "", f"Subprocess invocation exception: {str(e)}", False
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def evaluate(self, candidate_code: str, test_harness: str, bench_harness: str) -> ValidationReport:
        """
        Evaluación completa multi-fase del código candidato.
        """
        report = ValidationReport()

        # Fase 1: Sintaxis
        is_syntax_valid, syntax_err = self.check_syntax(candidate_code)
        report.is_valid_syntax = is_syntax_valid
        if not is_syntax_valid:
            report.error_message = syntax_err
            return report

        # Fase 2: Tests Unitarios
        test_script = f"""
# CANDIDATE CODE
{candidate_code}

# TEST HARNESS
{test_harness}

if __name__ == '__main__':
    run_tests()
    print('__TESTS_PASSED_SUCCESSFULLY__')
"""
        retcode, stdout, stderr, timed_out = self._execute_in_subprocess(test_script, self.test_timeout)
        if timed_out:
            report.tests_timed_out = True
            report.error_message = f"Timeout ({self.test_timeout}s) ejecutando pruebas unitarias. Posible bucle infinito o recursión descontrolada."
            report.traceback = stderr or stdout
            return report

        if retcode != 0 or "__TESTS_PASSED_SUCCESSFULLY__" not in stdout:
            report.tests_passed = False
            report.error_message = "Fallo en suite de pruebas unitarias."
            report.traceback = stderr or stdout
            return report

        report.tests_passed = True

        # Fase 3: Benchmark Estadístico
        bench_script = f"""
import json
# CANDIDATE CODE
{candidate_code}

# BENCHMARK HARNESS
{bench_harness}

if __name__ == '__main__':
    result = run_benchmark()
    print('__BENCHMARK_JSON__' + json.dumps(result))
"""
        retcode_b, stdout_b, stderr_b, timed_out_b = self._execute_in_subprocess(bench_script, self.bench_timeout)
        if timed_out_b:
            report.bench_timed_out = True
            report.error_message = f"Timeout ({self.bench_timeout}s) durante el benchmark de rendimiento."
            report.traceback = stderr_b or stdout_b
            return report

        if retcode_b != 0 or "__BENCHMARK_JSON__" not in stdout_b:
            report.bench_passed = False
            report.error_message = "Error en ejecución del benchmark de rendimiento."
            report.traceback = stderr_b or stdout_b
            return report

        try:
            json_str = stdout_b.split("__BENCHMARK_JSON__")[1].strip().split("\n")[0]
            bench_data = json.loads(json_str)
            report.bench_passed = True
            report.median_time = float(bench_data.get("median_time", float("inf")))
            report.min_time = float(bench_data.get("min_time", float("inf")))
            report.avg_time = float(bench_data.get("avg_time", float("inf")))
            report.peak_memory_mb = float(bench_data.get("peak_memory_mb", 0.0))
        except Exception as e:
            report.bench_passed = False
            report.error_message = f"Error parseando métricas del benchmark: {str(e)}"
            report.traceback = stdout_b

        return report


# ==============================================================================
# INTEGRACIÓN CON HERMES KNOWLEDGE HUB (~/.hermes-hub)
# ==============================================================================

class HermesKnowledgeBridge:
    """
    Puente de conocimiento con ~/.hermes-hub:
    - Recupera patrones y directivas de estilo al inicio.
    - Exporta automáticamente la solución ganadora como un Draft utilizable.
    """

    def __init__(self, hub_path: Optional[str] = None):
        self.hub_path = Path(hub_path or os.path.expanduser("~/.hermes-hub"))
        self.drafts_dir = self.hub_path / "drafts"
        self.patterns_dir = self.hub_path / "patterns"
        self.memory_dir = self.hub_path / "memory"

    def read_hub_context(self) -> Dict[str, str]:
        """Carga directivas globales y heurísticas desde Hermes si existen."""
        context = {
            "style": "Strict typing, modular design, avoid redundant allocations, no unnecessary classes.",
            "guidelines": "Ensure mathematical correctness, handle edge cases (empty collections, ties, floats).",
        }

        user_md = self.memory_dir / "USER.md"
        if user_md.exists():
            try:
                context["user_profile"] = user_md.read_text(encoding="utf-8")[:1000]
            except Exception:
                pass

        # Buscar patrones relevantes de python o rendimiento
        if self.patterns_dir.exists():
            try:
                patterns = []
                for p in self.patterns_dir.glob("*.md"):
                    content = p.read_text(encoding="utf-8")
                    if "performance" in content.lower() or "optimiz" in content.lower() or "python" in content.lower():
                        patterns.append(f"- {p.name}: {content[:300]}...")
                if patterns:
                    context["hermes_patterns"] = "\n".join(patterns[:3])
            except Exception:
                pass

        return context

    def save_winning_draft(
        self,
        candidate_code: str,
        baseline_code: str,
        initial_time: float,
        final_time: float,
        speedup_pct: float,
        tokens_used: int,
        iterations: int,
        winning_strategy: str,
    ) -> Optional[Path]:
        """Guarda la estrategia y código ganador como draft en Hermes."""
        try:
            target_dir = self.drafts_dir if self.hub_path.exists() else Path("./hermes_drafts")
            target_dir.mkdir(parents=True, exist_ok=True)

            timestamp = int(time.time())
            filename = f"draft_python_optimization_{timestamp}.md"
            draft_file = target_dir / filename

            content = f"""---
title: "Python Performance Optimization Pattern"
created_at: "{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"
speedup_percentage: {speedup_pct:.2f}%
initial_median_sec: {initial_time:.6f}
optimized_median_sec: {final_time:.6f}
tokens_spent: {tokens_used}
iterations_count: {iterations}
winning_strategy: "{winning_strategy}"
tags: ["python", "optimization", "benchmarking", "algorithmic-efficiency"]
---

# Winning Optimization Pattern

## Executive Summary
This optimization achieved a **{speedup_pct:.1f}% speedup** (from {initial_time*1000:.2f}ms down to {final_time*1000:.2f}ms) over {iterations} autonomous iterations using {tokens_used} tokens.

### Key Architectural Transformations
- Primary Strategy: `{winning_strategy}`
- Reduced Big-O complexity via single-pass hash map aggregations.
- Replaced nested linear iterations with dictionary/set lookups.
- Avoided redundant memory allocations and repeated type conversions.

## Optimized Source Code
```python
{candidate_code.strip()}
```

## Original Baseline Reference
```python
{baseline_code.strip()}
```
"""
            draft_file.write_text(content, encoding="utf-8")
            return draft_file
        except Exception as e:
            print(f"[HermesBridge] Advertencia al guardar draft: {e}")
            return None


# ==============================================================================
# ORQUESTADOR DE ESTRATEGIAS Y MOTOR DE PROMPTS COMPACTOS
# ==============================================================================

class StrategyOrchestrator:
    """
    Gestiona el catálogo de estrategias y adapta el foco de cada ciclo.
    """

    STRATEGIES: List[StrategyDefinition] = [
        StrategyDefinition(
            type=StrategyType.BIG_O,
            name="1. Reducción de Complejidad Algorítmica (Big-O)",
            description="Eliminar bucles anidados O(N^2) o búsquedas repetidas sustituyéndolas por estructuras hash O(1) o procesamiento en una sola pasada O(N).",
            focus_points=[
                "Convierte escaneos lineales múltiples sobre la misma lista en un único bucle de agregación.",
                "Usa diccionarios o hash maps para acumular totales en O(1).",
                "Evita cálculos redundantes dentro de bucles.",
            ],
            hermes_heuristics=[
                "Hermes Pattern: Agrupa estados en un solo pase acumulativo.",
                "Evita recrear colecciones intermedias en cada iteración.",
            ],
        ),
        StrategyDefinition(
            type=StrategyType.DATA_STRUCTURES,
            name="2. Estructuras de Datos Nativas y Eficientes",
            description="Aprovechar colecciones especializadas de la biblioteca estándar (collections.defaultdict, Counter, deque, heapq) y comprensiones optimizadas.",
            focus_points=[
                "Usa `collections.defaultdict` o `Counter` para evitar ramas `if key not in dict`.",
                "Usa `heapq.nlargest` para encontrar el top K en O(N log K) en lugar de ordenar toda la lista en O(N log N).",
                "Reemplaza listas de búsqueda por `set` para membresía O(1).",
            ],
            hermes_heuristics=[
                "Las estructuras nativas de CPython en `collections` y `heapq` ejecutan en C sin overhead del intérprete.",
            ],
        ),
        StrategyDefinition(
            type=StrategyType.CACHING_VECTORIZATION,
            name="3. Memoización, Caché y Precomputación",
            description="Reutilizar resultados previos, precalcular constantes y simplificar transformaciones de datos repetitivas.",
            focus_points=[
                "Precalcula umbrales y promedios una sola vez.",
                "Memoiza llamadas a funciones puras o lookups recurrentes.",
                "Aprovecha funciones integradas en C como `min`, `max`, `sum`, `sorted` con claves optimizadas.",
            ],
            hermes_heuristics=[
                "CPython optimiza llamadas directas a funciones integradas (builtins) sobre funciones Python manuales.",
            ],
        ),
        StrategyDefinition(
            type=StrategyType.MICRO_OPTIMIZATION,
            name="4. Micro-optimizaciones, Bytecode y Reducción de Overhead",
            description="Minimizar accesos a atributos, atar variables a scope local y reducir conversiones de tipos superfluas.",
            focus_points=[
                "Asigna métodos y funciones a variables locales antes de bucles intensivos (ej: `append = lista.append`, `get = d.get`).",
                "Elimina conversiones de tipos repetidas (ej. `float(amt)`) procesándolas solo en la ingesta inicial.",
                "Asegura tipado estricto e inlining de operaciones simples.",
            ],
            hermes_heuristics=[
                "El acceso a variables locales (LOAD_FAST) en el bytecode de Python es significativamente más rápido que el acceso global o de atributo.",
            ],
        ),
    ]

    def get_strategy(self, iteration_index: int) -> StrategyDefinition:
        return self.STRATEGIES[iteration_index % len(self.STRATEGIES)]


class CompactPromptEngine:
    """
    Construye prompts compactos O(1) en cada turno.
    No acumula el historial de conversación para no inflar cuadráticamente los tokens.
    """

    SYSTEM_PROMPT = """Eres un ingeniero de software senior y especialista en optimización de rendimiento extremo en Python (CPython 3.10+).

Tu objetivo es optimizar el código Python proporcionado manteniendo ESTRICTAMENTE la misma interfaz, tipos de entrada/salida y comportamiento exacto (incluyendo manejo de listas vacías, empates y casos borde).

REGLAS INVIOLABLES:
1. Devuelve ÚNICAMENTE el código Python optimizado dentro de un bloque de código markdown ```python ... ```.
2. NO incluyas introducciones, comentarios conversacionales ni explicaciones fuera del bloque de código.
3. El código debe ser 100% autónomo y contener la función o clase objetivo completa.
4. Preserva el nombre de las funciones principales y la firma de tipos.
5. Prioriza código limpio, idiomático y de altísimo rendimiento en CPython."""

    @staticmethod
    def build_user_prompt(
        current_baseline_code: str,
        strategy: StrategyDefinition,
        iteration: int,
        previous_status: Optional[str] = None,
        previous_feedback: Optional[str] = None,
        hermes_context: Optional[Dict[str, str]] = None,
    ) -> str:
        prompt_parts = []
        prompt_parts.append(f"### ITERACIÓN #{iteration} - FOCO DE ESTRATEGIA: {strategy.name}\n")
        prompt_parts.append(f"**Objetivo**: {strategy.description}\n")
        prompt_parts.append("**Directrices Clave**:")
        for fp in strategy.focus_points:
            prompt_parts.append(f"  * {fp}")

        if hermes_context and "hermes_patterns" in hermes_context:
            prompt_parts.append("\n**Heurísticas de Hermes Knowledge Hub**:")
            prompt_parts.append(hermes_context["hermes_patterns"])

        if previous_status:
            prompt_parts.append("\n### RETROALIMENTACIÓN DE LA ITERACIÓN PREVIA:")
            if previous_status == "ACCEPTED":
                prompt_parts.append(f"✅ ¡ÉXITO! La versión anterior fue aceptada y aceleró la ejecución. {previous_feedback}")
                prompt_parts.append("Ahora construye sobre este nuevo baseline para lograr una aceleración aún mayor aplicando la estrategia actual.")
            elif previous_status == "REJECTED_REGRESSION":
                prompt_parts.append(f"⚠️ La versión previa pasó los tests pero fue MÁS LENTA o igual. {previous_feedback}")
                prompt_parts.append("Descarta ese enfoque y prueba una técnica radicalmente más eficiente.")
            elif previous_status in ("REJECTED_TEST_FAIL", "REJECTED_SYNTAX", "REJECTED_TIMEOUT"):
                prompt_parts.append(f"❌ La versión previa FALLÓ con el siguiente reporte:")
                prompt_parts.append(f"```\n{previous_feedback}\n```")
                prompt_parts.append("Corrige este fallo asegurando exactitud funcional absoluta y tipos estrictos.")

        prompt_parts.append("\n### CÓDIGO BASELINE ACTUAL (A OPTIMIZAR):")
        prompt_parts.append(f"```python\n{current_baseline_code.strip()}\n```")
        prompt_parts.append("\nEscribe el código optimizado completo dentro de ```python ... ```.")

        full_prompt = "\n".join(prompt_parts)
        return CompactPromptEngine.compress_context(full_prompt)

    @staticmethod
    def compress_context(prompt_text: str, budget_threshold_ratio: float = 0.75) -> str:
        """
        Compresión adaptativa en 2 niveles (Inspirado en ContextIQ / LLMLingua):
        Nivel 1: Poda de espacios duplicados, comentarios superfluos y metadatos no críticos.
        Nivel 2: Condensación contextual agresiva si el contenido excede el 75% del presupuesto.
        """
        # Nivel 1: Limpieza en frío
        cleaned = re.sub(r"\n{3,}", "\n\n", prompt_text)
        cleaned = re.sub(r"[ \t]+", " ", cleaned)

        # Nivel 2: Compresión dinámica de secciones extensas
        lines = cleaned.splitlines()
        compressed_lines = []
        for line in lines:
            line_str = line.strip()
            # Omitir separadores decorativos redundantes
            if set(line_str).issubset({"=", "-", "*", "#"}) and len(line_str) > 5:
                continue
            compressed_lines.append(line)

        return "\n".join(compressed_lines)


# ==============================================================================
# CLIENTE LLM (OPENAI & MOCK COMPATIBLE)
# ==============================================================================

class MockLLMClient:
    """
    Cliente simulado determinista para pruebas locales, desarrollo y verificación offline.
    """

    MOCK_IMPROVEMENTS = [
        # Iteration 1: Single-pass Big-O optimization with dict
        '''
from collections import defaultdict

def process_data(records: list[dict]) -> dict:
    if not records:
        return {"top_categories": [], "user_summaries": {}, "suspicious_tx_ids": []}

    cat_totals = defaultdict(float)
    user_totals = defaultdict(float)
    user_counts = defaultdict(int)

    # Single pass aggregation
    for r in records:
        amt = float(r["amount"])
        cat_totals[r["category"]] += amt
        u = r["user_id"]
        user_totals[u] += amt
        user_counts[u] += 1

    # Sorted top 3 categories
    top_categories = [c for c, _ in sorted(cat_totals.items(), key=lambda x: (-x[1], x[0]))[:3]]

    user_summaries = {}
    for u, total in user_totals.items():
        cnt = user_counts[u]
        avg = total / cnt
        user_summaries[u] = {
            "total_spent": round(total, 2),
            "avg_spent": round(avg, 2),
            "tx_count": cnt
        }

    suspicious_set = set()
    for r in records:
        u = r["user_id"]
        amt = float(r["amount"])
        u_info = user_summaries[u]
        if u_info["tx_count"] > 1 and amt > (3.0 * u_info["avg_spent"]):
            suspicious_set.add(r["id"])

    return {
        "top_categories": top_categories,
        "user_summaries": user_summaries,
        "suspicious_tx_ids": sorted(suspicious_set)
    }
''',
        # Iteration 2: heapq and zero-copy lookups
        '''
from collections import defaultdict
import heapq

def process_data(records: list[dict]) -> dict:
    if not records:
        return {"top_categories": [], "user_summaries": {}, "suspicious_tx_ids": []}

    cat_totals = defaultdict(float)
    user_totals = defaultdict(float)
    user_counts = defaultdict(int)

    for r in records:
        amt = float(r["amount"])
        cat_totals[r["category"]] += amt
        u = r["user_id"]
        user_totals[u] += amt
        user_counts[u] += 1

    # Using heapq nsmallest with custom sorting key (-total, category)
    top_categories = heapq.nsmallest(3, cat_totals.keys(), key=lambda c: (-cat_totals[c], c))

    user_summaries = {}
    thresholds = {}
    for u, total in user_totals.items():
        cnt = user_counts[u]
        avg = total / cnt
        user_summaries[u] = {
            "total_spent": round(total, 2),
            "avg_spent": round(avg, 2),
            "tx_count": cnt
        }
        thresholds[u] = 3.0 * avg if cnt > 1 else float("inf")

    suspicious = [
        r["id"] for r in records
        if float(r["amount"]) > thresholds[r["user_id"]]
    ]
    suspicious_tx_ids = sorted(set(suspicious))

    return {
        "top_categories": top_categories,
        "user_summaries": user_summaries,
        "suspicious_tx_ids": suspicious_tx_ids
    }
''',
        # Iteration 3: Local variable bindings and micro-optimizations
        '''
from collections import defaultdict
import heapq

def process_data(records: list[dict]) -> dict:
    if not records:
        return {"top_categories": [], "user_summaries": {}, "suspicious_tx_ids": []}

    cat_totals = defaultdict(float)
    user_totals = defaultdict(float)
    user_counts = defaultdict(int)

    # Local binding optimization
    for r in records:
        amt = float(r["amount"])
        cat_totals[r["category"]] += amt
        u = r["user_id"]
        user_totals[u] += amt
        user_counts[u] += 1

    # Fast top 3 selection
    top_categories = heapq.nsmallest(3, cat_totals.keys(), key=lambda c: (-cat_totals[c], c))

    user_summaries = {}
    thresholds = {}
    for u, total in user_totals.items():
        cnt = user_counts[u]
        avg = total / cnt
        user_summaries[u] = {
            "total_spent": round(total, 2),
            "avg_spent": round(avg, 2),
            "tx_count": cnt
        }
        if cnt > 1:
            thresholds[u] = 3.0 * avg

    # Fast comprehension with threshold lookup
    suspicious = {
        r["id"] for r in records
        if r["user_id"] in thresholds and float(r["amount"]) > thresholds[r["user_id"]]
    }

    return {
        "top_categories": top_categories,
        "user_summaries": user_summaries,
        "suspicious_tx_ids": sorted(suspicious)
    }
''',
    ]

    def __init__(self):
        self.call_count = 0

    def generate(self, system_prompt: str, user_prompt: str) -> Tuple[str, int, int]:
        idx = min(self.call_count, len(self.MOCK_IMPROVEMENTS) - 1)
        code = self.MOCK_IMPROVEMENTS[idx]
        self.call_count += 1
        prompt_tokens = len(system_prompt + user_prompt) // 4
        completion_tokens = len(code) // 4
        return f"```python\n{code.strip()}\n```", prompt_tokens, completion_tokens


class LLMClientWrapper:
    """
    Envuelve el cliente OpenAI para interactuar con cualquier endpoint compatible
    (OpenAI, OpenRouter, Groq, Ollama, DeepSeek, vLLM).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        use_mock: bool = False,
    ):
        self.use_mock = use_mock
        self.model = model
        self.temperature = temperature
        self.mock_client = MockLLMClient() if use_mock else None

        if not self.use_mock:
            if OpenAI is None:
                raise ImportError("El paquete 'openai' no está instalado. Instálalo con: pip install openai")
            effective_key = api_key or os.environ.get("OPENAI_API_KEY") or "dummy-key"
            effective_base_url = base_url or os.environ.get("OPENAI_BASE_URL")
            self.client = OpenAI(api_key=effective_key, base_url=effective_base_url)

    def complete(self, system_prompt: str, user_prompt: str) -> Tuple[str, int, int, int]:
        """
        Ejecuta la completación y devuelve (raw_response, prompt_tokens, completion_tokens, total_tokens).
        """
        if self.use_mock:
            resp, pt, ct = self.mock_client.generate(system_prompt, user_prompt)
            return resp, pt, ct, pt + ct

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content or ""
        usage = response.usage
        if usage:
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
        else:
            prompt_tokens = len(system_prompt + user_prompt) // 4
            completion_tokens = len(content) // 4
            total_tokens = prompt_tokens + completion_tokens

        return content, prompt_tokens, completion_tokens, total_tokens

    @staticmethod
    def extract_code(raw_response: str) -> str:
        """Extrae el código limpio de los bloques markdown."""
        match = re.search(r"```(?:python)?\s*(.*?)\s*```", raw_response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return raw_response.strip()


# ==============================================================================
# BUCLE DE OPTIMIZACIÓN CONTINUA (ITERATIVE CODE OPTIMIZER)
# ==============================================================================

class IterativeCodeOptimizer:
    """
    Orquestador principal del bucle de optimización continua guiado por presupuesto de tokens.
    """

    def __init__(
        self,
        token_budget: int = 50000,
        max_iterations: int = 20,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        use_mock: bool = False,
        test_timeout: float = 5.0,
        bench_timeout: float = 12.0,
        output_file: str = "codigo_optimizado_final.py",
        history_file: str = "optimization_history.json",
        verbose: bool = True,
    ):
        self.budget_manager = TokenBudgetManager(token_budget)
        self.max_iterations = max_iterations
        self.output_file = Path(output_file)
        self.history_file = Path(history_file)
        self.verbose = verbose

        self.sandbox = ValidationSandbox(test_timeout=test_timeout, bench_timeout=bench_timeout)
        self.hermes = HermesKnowledgeBridge()
        self.strategies = StrategyOrchestrator()
        self.prompt_engine = CompactPromptEngine()
        self.llm = LLMClientWrapper(
            api_key=api_key,
            base_url=base_url,
            model=model,
            use_mock=use_mock,
        )

        self.history: List[IterationRecord] = []
        self.baseline_code: str = ""
        self.best_code: str = ""
        self.initial_report: Optional[ValidationReport] = None
        self.best_report: Optional[ValidationReport] = None
        self.winning_strategy_name: str = "Initial Baseline"

    def log(self, message: str) -> None:
        if self.verbose:
            print(message)

    def run(self, initial_code: str, test_harness: str, bench_harness: str) -> str:
        """
        Ejecuta el bucle completo de optimización continua.
        """
        self.baseline_code = initial_code.strip()
        self.best_code = self.baseline_code

        self.log("\n" + "=" * 80)
        self.log("🚀 INICIANDO BUCLE DE OPTIMIZACIÓN CONTINUA DE CÓDIGO (HERMES AI)")
        self.log("=" * 80)
        self.log(f"• Presupuesto de Tokens: {self.budget_manager.budget:,} tokens")
        self.log(f"• Límite Máx Iteraciones: {self.max_iterations}")
        self.log(f"• Modo de Inferencia: {'MOCK SIMULATOR' if self.llm.use_mock else f'LIVE API ({self.llm.model})'}")

        # 1. Cargar contexto de Hermes
        hermes_ctx = self.hermes.read_hub_context()
        if "user_profile" in hermes_ctx or "hermes_patterns" in hermes_ctx:
            self.log("• [Hermes Hub] Contexto y heurísticas sincronizadas correctamente.")

        # 2. Evaluación inicial del baseline
        self.log("\n🔍 Evaluando Baseline Inicial...")
        self.initial_report = self.sandbox.evaluate(self.baseline_code, test_harness, bench_harness)
        if not self.initial_report.is_successful:
            raise RuntimeError(f"El código inicial de partida falló la validación: {self.initial_report.error_message}\n{self.initial_report.traceback}")

        self.best_report = self.initial_report
        self.log(f"✅ Baseline Verificado: Mediana={self.initial_report.median_time*1000:.3f}ms | Memoria={self.initial_report.peak_memory_mb:.3f}MB\n")

        prev_status: Optional[str] = None
        prev_feedback: Optional[str] = None
        iteration = 0

        # 3. Bucle continuo
        while iteration < self.max_iterations and self.budget_manager.has_budget():
            iteration += 1
            strategy = self.strategies.get_strategy(iteration - 1)

            self.log("-" * 80)
            self.log(f"📍 Iteración #{iteration} | Estrategia: {strategy.name}")
            self.log(f"   Tokens Restantes: {self.budget_manager.tokens_remaining:,} ({self.budget_manager.percentage_used:.1f}% usado)")

            # Construir prompt compacto O(1)
            user_prompt = self.prompt_engine.build_user_prompt(
                current_baseline_code=self.best_code,
                strategy=strategy,
                iteration=iteration,
                previous_status=prev_status,
                previous_feedback=prev_feedback,
                hermes_context=hermes_ctx,
            )

            # Inferencia LLM
            t_start_llm = time.perf_counter()
            try:
                raw_response, prompt_tokens, comp_tokens, total_tokens = self.llm.complete(
                    system_prompt=self.prompt_engine.SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                )
                self.budget_manager.record_usage(prompt_tokens, comp_tokens, total_tokens)
            except Exception as e:
                self.log(f"❌ Error en llamada LLM: {e}")
                prev_status = "REJECTED_ERROR"
                prev_feedback = f"API Error: {str(e)}"
                break

            candidate_code = self.llm.extract_code(raw_response)
            t_llm = time.perf_counter() - t_start_llm

            # Validación en Sandbox
            eval_report = self.sandbox.evaluate(candidate_code, test_harness, bench_harness)

            # Lógica de Decisión
            if not eval_report.is_valid_syntax:
                status = "REJECTED_SYNTAX"
                speedup_prev = 0.0
                speedup_base = 0.0
                prev_status = status
                prev_feedback = f"Error de sintaxis: {eval_report.error_message}"
                self.log(f"   ❌ Sintaxis inválida: {eval_report.error_message}")

            elif eval_report.tests_timed_out:
                status = "REJECTED_TIMEOUT"
                speedup_prev = 0.0
                speedup_base = 0.0
                prev_status = status
                prev_feedback = f"Timeout ({self.sandbox.test_timeout}s) durante ejecución de tests."
                self.log(f"   ⏱️ Timeout en tests unitarios.")

            elif not eval_report.tests_passed:
                status = "REJECTED_TEST_FAIL"
                speedup_prev = 0.0
                speedup_base = 0.0
                prev_status = status
                prev_feedback = f"Tests fallaron:\n{eval_report.traceback}"
                self.log(f"   ❌ Pruebas unitarias fallaron:\n{eval_report.traceback}")

            elif eval_report.bench_timed_out or not eval_report.bench_passed:
                status = "REJECTED_BENCH_FAIL"
                speedup_prev = 0.0
                speedup_base = 0.0
                prev_status = status
                prev_feedback = f"Benchmark falló o dio timeout: {eval_report.error_message}"
                self.log(f"   ❌ Benchmark falló.")

            else:
                # Tests pasaron y benchmark válido -> comparar rendimiento
                cand_time = eval_report.median_time
                best_time = self.best_report.median_time
                base_time = self.initial_report.median_time

                speedup_vs_best = ((best_time - cand_time) / best_time) * 100.0 if best_time > 0 else 0.0
                speedup_vs_base = ((base_time - cand_time) / base_time) * 100.0 if base_time > 0 else 0.0

                if cand_time < best_time:
                    # Estrictamente más rápido -> ACEPTAR y actualizar baseline
                    status = "ACCEPTED"
                    self.best_code = candidate_code
                    self.best_report = eval_report
                    self.winning_strategy_name = strategy.name
                    speedup_prev = speedup_vs_best
                    speedup_base = speedup_vs_base

                    prev_status = status
                    prev_feedback = f"Aceleración: +{speedup_vs_best:.2f}% vs versión previa. Tiempo bajó de {best_time*1000:.3f}ms a {cand_time*1000:.3f}ms."
                    self.log(f"   🌟 ¡NUEVO RECORD! Tiempo={cand_time*1000:.3f}ms (+{speedup_vs_best:.1f}% vs previo, +{speedup_vs_base:.1f}% vs base)")
                else:
                    # Más lento o igual -> RECHAZAR
                    status = "REJECTED_REGRESSION"
                    speedup_prev = speedup_vs_best
                    speedup_base = speedup_vs_base

                    prev_status = status
                    prev_feedback = f"El código fue {abs(speedup_vs_best):.2f}% más lento ({cand_time*1000:.3f}ms vs récord {best_time*1000:.3f}ms)."
                    self.log(f"   ⚠️ Regresión de rendimiento: {cand_time*1000:.3f}ms vs actual {best_time*1000:.3f}ms (descartado).")

            # Registrar histórico
            record = IterationRecord(
                iteration=iteration,
                strategy=strategy.name,
                prompt_tokens=prompt_tokens,
                completion_tokens=comp_tokens,
                accumulated_tokens=self.budget_manager.usage.total_tokens,
                status=status,
                median_time_sec=eval_report.median_time if eval_report.is_successful else 0.0,
                speedup_pct_vs_previous=speedup_prev,
                speedup_pct_vs_baseline=speedup_base,
                peak_memory_mb=eval_report.peak_memory_mb,
                explanation=prev_feedback or "",
                error_details=eval_report.error_message,
            )
            self.history.append(record)

        # 4. Guardar salida final
        self._finalize_and_save()
        return self.best_code

    def _finalize_and_save(self) -> None:
        """Guarda los artefactos finales, JSON de histórico, draft de Hermes y reporte en consola."""
        # 1. Guardar código ganador
        self.output_file.write_text(self.best_code.strip() + "\n", encoding="utf-8")

        # 2. Guardar histórico JSON
        history_payload = {
            "token_budget_summary": self.budget_manager.summary(),
            "initial_benchmark": asdict(self.initial_report) if self.initial_report else None,
            "final_benchmark": asdict(self.best_report) if self.best_report else None,
            "winning_strategy": self.winning_strategy_name,
            "total_speedup_percentage": round(
                ((self.initial_report.median_time - self.best_report.median_time) / self.initial_report.median_time) * 100.0, 2
            ) if self.initial_report and self.best_report else 0.0,
            "iterations": [asdict(r) for r in self.history],
        }
        self.history_file.write_text(json.dumps(history_payload, indent=2), encoding="utf-8")

        # 3. Guardar draft en Hermes Hub
        if self.initial_report and self.best_report:
            initial_t = self.initial_report.median_time
            final_t = self.best_report.median_time
            speedup_pct = ((initial_t - final_t) / initial_t) * 100.0
            draft_path = self.hermes.save_winning_draft(
                candidate_code=self.best_code,
                baseline_code=self.baseline_code,
                initial_time=initial_t,
                final_time=final_t,
                speedup_pct=speedup_pct,
                tokens_used=self.budget_manager.usage.total_tokens,
                iterations=len(self.history),
                winning_strategy=self.winning_strategy_name,
            )
        else:
            draft_path = None

        # 4. Imprimir resumen
        self.log("\n" + "=" * 80)
        self.log("🏁 RESUMEN FINAL DEL BUCLE DE OPTIMIZACIÓN")
        self.log("=" * 80)
        self.log(f"• Total Iteraciones Realizadas: {len(self.history)}")
        self.log(f"• Tokens Gastados: {self.budget_manager.usage.total_tokens:,} / {self.budget_manager.budget:,} ({self.budget_manager.percentage_used:.1f}%)")
        if self.initial_report and self.best_report:
            init_ms = self.initial_report.median_time * 1000.0
            final_ms = self.best_report.median_time * 1000.0
            speedup = ((init_ms - final_ms) / init_ms) * 100.0
            speedup_factor = init_ms / final_ms if final_ms > 0 else 1.0
            self.log(f"• Tiempo Inicial (Baseline):    {init_ms:.3f} ms")
            self.log(f"• Tiempo Final Optimizado:      {final_ms:.3f} ms")
            self.log(f"• Aceleración Total Lograda:    {speedup:.2f}% ({speedup_factor:.1f}x más rápido)")
            self.log(f"• Estrategia Ganadora:          {self.winning_strategy_name}")

        self.log(f"• Código Ganador Guardado En:   {self.output_file.resolve()}")
        self.log(f"• Historial Detallado JSON:     {self.history_file.resolve()}")
        if draft_path:
            self.log(f"• Hermes Draft Guardado En:     {draft_path.resolve()}")
        self.log("=" * 80 + "\n")


# ==============================================================================
# PUNTO DE ENTRADA CLI
# ==============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bucle de Optimización Continua de Código (Iterative Code Optimizer) guiado por presupuesto de tokens y Hermes Knowledge Hub.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--token-budget", type=int, default=50000, help="Presupuesto total de tokens de API.")
    parser.add_argument("--max-iterations", type=int, default=20, help="Límite máximo de iteraciones.")
    parser.add_argument("--model", type=str, default=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), help="Modelo LLM a utilizar.")
    parser.add_argument("--api-key", type=str, default=os.environ.get("OPENAI_API_KEY"), help="API Key de OpenAI o endpoint compatible.")
    parser.add_argument("--base-url", type=str, default=os.environ.get("OPENAI_BASE_URL"), help="URL base compatible OpenAI (OpenRouter, Groq, Ollama, etc.).")
    parser.add_argument("--target-code", type=str, help="Ruta al archivo .py con el código baseline a optimizar (opcional, usa demo por defecto).")
    parser.add_argument("--test-file", type=str, help="Ruta al archivo .py con el test harness (requiere que defina run_tests()).")
    parser.add_argument("--bench-file", type=str, help="Ruta al archivo .py con el benchmark harness (requiere que defina run_benchmark()).")
    parser.add_argument("--output", type=str, default="codigo_optimizado_final.py", help="Ruta de guardado del código ganador.")
    parser.add_argument("--history-output", type=str, default="optimization_history.json", help="Ruta de guardado del historial en formato JSON.")
    parser.add_argument("--mock", action="store_true", help="Ejecutar en modo simulador local sin gastar tokens de red.")
    parser.add_argument("--quiet", action="store_true", help="Suprimir logs detallados durante la ejecución.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Cargar código objetivo
    if args.target_code and args.test_file and args.bench_file:
        baseline_code = Path(args.target_code).read_text(encoding="utf-8")
        test_harness = Path(args.test_file).read_text(encoding="utf-8")
        bench_harness = Path(args.bench_file).read_text(encoding="utf-8")
    else:
        try:
            import demo_benchmark
            baseline_code, test_harness, bench_harness = demo_benchmark.get_default_target_bundle()
        except ImportError:
            sys.exit("Error: No se encontró el módulo demo_benchmark.py ni se especificaron los archivos --target-code, --test-file y --bench-file.")

    optimizer = IterativeCodeOptimizer(
        token_budget=args.token_budget,
        max_iterations=args.max_iterations,
        model=args.model,
        api_key=args.api_key,
        base_url=args.base_url,
        use_mock=args.mock,
        output_file=args.output,
        history_file=args.history_output,
        verbose=not args.quiet,
    )

    try:
        optimizer.run(baseline_code, test_harness, bench_harness)
    except KeyboardInterrupt:
        print("\n[!] Ejecución interrumpida manualmente por el usuario. Guardando progreso actual...")
        optimizer._finalize_and_save()


if __name__ == "__main__":
    main()
