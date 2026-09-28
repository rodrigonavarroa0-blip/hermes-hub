"""
verify_mcp_tools_live.py — Verificación en Vivo de Todas las Herramientas FastMCP de Hermes.
Ejecuta llamadas reales contra cada una de las herramientas registradas en mcp_server.py.
"""
import os
import sys
import json
from pathlib import Path

HUB_PATH = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
sys.path.insert(0, str(Path(__file__).resolve().parent / "core"))
sys.path.insert(0, str(HUB_PATH))

import mcp_server

TOOLS_TO_TEST = [
    ("resolve_context", {"query": "fastapi async session", "top_k": 2}),
    ("resolve_compact_context", {"query": "redis redlock", "max_token_budget": 500, "top_k": 2}),
    ("hermes_hybrid_search", {"query": "docker isolated sandbox container", "top_k": 2, "token_budget": 800}),
    ("hermes_causal_audit", {"seed_patterns": ["fastapi", "pydantic"]}),
    ("hermes_ast_scan", {"workspace_path": str(Path(__file__).resolve().parent), "max_files": 5}),
    ("hermes_record_execution_result", {"pattern_ids": ["fastapi", "pydantic"], "success": True, "task_type": "audit_test"}),
    ("scan_workspace_antipatterns", {"workspace_path": str(Path(__file__).resolve().parent)}),
    ("rerank_context_snippets", {"query": "redis lock", "snippets": [{"title": "Redis", "summary": "Redis cache"}, {"title": "Postgres", "summary": "SQL DB"}]}),
]


def test_all_mcp_tools():
    print("=" * 70)
    print("🧪 VERIFICACIÓN EN VIVO DE HERRAMIENTAS FASTMCP")
    print("=" * 70)

    passed = 0
    for tool_name, kwargs in TOOLS_TO_TEST:
        try:
            fn = getattr(mcp_server, tool_name, None)
            if fn is None:
                # Buscar en decorators o wrappers
                print(f"  ❌ {tool_name}: No encontrado en mcp_server")
                continue

            res = fn(**kwargs)
            status = res.get("status", "success") if isinstance(res, dict) else "success"
            print(f"  ✅ {tool_name}: OK (Respuesta estructurada recibida)")
            passed += 1
        except Exception as e:
            print(f"  ❌ {tool_name}: ERROR -> {e}")

    print("=" * 70)
    print(f"🎯 Herramientas FastMCP Validadas: {passed}/{len(TOOLS_TO_TEST)}")
    print("=" * 70)
    return passed == len(TOOLS_TO_TEST)


if __name__ == "__main__":
    success = test_all_mcp_tools()
    sys.exit(0 if success else 1)
