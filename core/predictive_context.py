"""
predictive_context.py — Inyección Predictiva de Contexto y Reglas de Oro para IDEs.
Inspecciona rutas de archivos, extensiones, dependencias y fragmentos de código para
predecir la tecnología en uso y precargar las directivas críticas de Hermes antes de codificar.
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

HUB_PATH = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_PATH / "config"
PATTERNS_DIR = HUB_PATH / "patterns"

TECH_SIGNATURES = {
    "nextjs": {
        "extensions": [".tsx", ".jsx", ".ts", ".js"],
        "keywords": ["app/", "page.", "layout.", "route.", "use client", "server actions", "next/"],
        "heuristics": [
            "Next.js 15: Los componentes en `app/` son Server Components por defecto. Usa 'use client' solo para hooks interactivos.",
            "Evita recrear Server Actions dentro de ciclos; colócalas en archivos separados con 'use server'.",
            "Usa caching granular con `fetch(url, { next: { tags: [...] } })` y `revalidateTag` en vez de revalidación global."
        ],
        "antipatterns": [
            "Importar librerías pesadas de Node en Client Components.",
            "Olvidar separar la metadata del viewport conforme al estándar Next.js 15."
        ]
    },
    "fastapi": {
        "extensions": [".py"],
        "keywords": ["fastapi", "apirouter", "depends", "backgroundtasks", "pydantic"],
        "heuristics": [
            "FastAPI: Desacopla la inyección de dependencias con `Depends()` para reutilizarla en workers y CLI.",
            "Para tareas pesadas en background, usa `BackgroundTasks` para tareas cortas o Celery/ARQ para trabajos distribuidos.",
            "Asegura que los endpoints async no bloqueen el event loop con operaciones I/O síncronas."
        ],
        "antipatterns": [
            "Llamar a `time.sleep()` o librerías síncronas bloqueantes dentro de rutas `async def`."
        ]
    },
    "pydantic": {
        "extensions": [".py"],
        "keywords": ["basemodel", "field(", "validator", "field_validator"],
        "heuristics": [
            "Pydantic V2: Usa `field_validator` y `model_validator(mode='after')` para validaciones declarativas.",
            "Prefiere `model_dump()` y `model_validate()` sobre los métodos obsoletos v1 (`dict()`, `parse_obj()`)."
        ],
        "antipatterns": [
            "Mutar campos de instancias de modelos congelados sin `model_copy(update=...)`."
        ]
    },
    "docker": {
        "extensions": ["dockerfile", ".dockerfile", ".yml", ".yaml"],
        "keywords": ["from ", "run ", "docker", "compose", "services:"],
        "heuristics": [
            "Docker Sandbox: Usa imágenes mínimas (`python:3.10-slim` o `alpine`), ejecuta como usuario no-root y monta volúmenes de solo lectura.",
            "Aprovecha el caché de capas ordenando primero `COPY requirements.txt` antes del resto del código fuente."
        ],
        "antipatterns": [
            "Ejecutar contenedores en modo privilegiado `--privileged` en producción o sandboxes de ejecución."
        ]
    },
    "redis": {
        "extensions": [".py", ".ts", ".js", ".go"],
        "keywords": ["redis", "redlock", "pubsub", "redis.createclient"],
        "heuristics": [
            "Redis: Para bloqueos distribuidos, implementa el algoritmo Redlock con TTL explícito y auto-renovación.",
            "Usa pipelines (`pipe = redis.pipeline()`) para agrupar múltiples comandos y minimizar latencias de red."
        ],
        "antipatterns": [
            "Usar el comando `KEYS *` en producción; reemplázalo por `SCAN` para evitar congelar el hilo de Redis."
        ]
    },
    "mcp": {
        "extensions": [".py", ".ts", ".json"],
        "keywords": ["mcp", "fastmcp", "modelcontextprotocol", "tools/list", "call_tool"],
        "heuristics": [
            "Model Context Protocol: Declara herramientas de forma atómica con docstrings claros que el LLM entienda sin ambigüedades.",
            "Maneja timeouts y errores controlados devolviendo estructuras JSON enriquecidas con `status: 'error'`."
        ],
        "antipatterns": [
            "Registrar herramientas gigantes con decenas de parámetros opcionales que confunden el razonamiento del LLM."
        ]
    }
}


def detect_tech_stack(file_path: Optional[str] = None, code_snippet: Optional[str] = None) -> List[str]:
    """Detecta tecnologías activas según el archivo o snippet."""
    detected = []
    fpath_str = (file_path or "").lower()
    snippet_str = (code_snippet or "").lower()

    for tech, data in TECH_SIGNATURES.items():
        # Coincidencia por extensión
        ext_match = any(fpath_str.endswith(ext) for ext in data["extensions"])
        # Coincidencia por palabra clave en ruta o snippet
        kw_match = any(kw in fpath_str or kw in snippet_str for kw in data["keywords"])

        if ext_match and kw_match:
            detected.append(tech)
        elif kw_match:
            detected.append(tech)

    return list(set(detected))


def resolve_predictive_context(
    file_path: Optional[str] = None,
    code_snippet: Optional[str] = None,
    tech_stack: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Genera el paquete predictivo de contexto con reglas y antipatrones para el IDE.
    """
    detected_techs = tech_stack or []
    if not detected_techs:
        detected_techs = detect_tech_stack(file_path, code_snippet)

    rules = []
    antipatterns = []

    for tech in detected_techs:
        if tech in TECH_SIGNATURES:
            rules.extend(TECH_SIGNATURES[tech]["heuristics"])
            antipatterns.extend(TECH_SIGNATURES[tech]["antipatterns"])

    return {
        "status": "success",
        "file_analyzed": file_path,
        "detected_technologies": detected_techs or ["general_software_engineering"],
        "predictive_rules": rules[:5] if rules else [
            "Garantizar tipado estricto, modularidad y manejo exhaustivo de excepciones.",
            "Desacoplar la lógica de dominio de las capas de transporte y persistencia."
        ],
        "critical_antipatterns": antipatterns[:3] if antipatterns else [
            "Evitar efectos secundarios ocultos en funciones puras."
        ]
    }


if __name__ == "__main__":
    test_path = sys.argv[1] if len(sys.argv) > 1 else "app/api/auth/route.ts"
    result = resolve_predictive_context(file_path=test_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
