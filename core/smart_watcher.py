"""
smart_watcher.py — Daemon de Vigilancia y Scanner de Antipatrones en Código de Hermes.
Inspecciona repositorios locales en tiempo real o bajo demanda para detectar violaciones
de las reglas de oro de Hermes y sugerir el refactor óptimo.
"""
import os
import sys
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

HUB_PATH = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
ALERTS_DIR = HUB_PATH / "alerts"
ALERTS_DIR.mkdir(parents=True, exist_ok=True)

# Catálogo de Heurísticas y Reglas de Detección de Antipatrones
ANTIPATTERN_RULES = [
    {
        "id": "HERMES_ASYNC_BLOCKING_SLEEP",
        "severity": "CRITICAL",
        "category": "Concurrency",
        "regex": r"async\s+def\s+.*:\s*(?:.*\n)*?.*time\.sleep\(",
        "extensions": [".py"],
        "message": "Uso bloqueante de 'time.sleep()' dentro de una función 'async def'. Esto congela todo el Event Loop de Python/FastAPI.",
        "fix_suggestion": "Reemplazar por 'await asyncio.sleep(...)'.",
        "hermes_pattern": "[[FastAPI Non-Blocking Async Tasks]]"
    },
    {
        "id": "HERMES_DOCKER_ROOT_USER",
        "severity": "HIGH",
        "category": "Security",
        "regex": r"FROM\s+[^\n]+\n(?![\s\S]*USER\s+(?!root))",
        "extensions": ["dockerfile", ".dockerfile"],
        "message": "El contenedor Docker se ejecuta como 'root' sin cambiar a un usuario no privilegiado ('USER appuser').",
        "fix_suggestion": "Agregar 'RUN adduser --disabled-password appuser && USER appuser' antes de CMD/ENTRYPOINT.",
        "hermes_pattern": "[[Docker Non-Root Sandbox Security]]"
    },
    {
        "id": "HERMES_REDIS_BLOCKING_KEYS",
        "severity": "CRITICAL",
        "category": "Database",
        "regex": r"\.keys\(\s*[\'\"]\*",
        "extensions": [".py", ".ts", ".js"],
        "message": "Uso del comando bloqueante 'KEYS *' en Redis. En producción puede congelar el hilo único de Redis.",
        "fix_suggestion": "Usar iteración no bloqueante con 'SCAN' / 'scan_iter()'.",
        "hermes_pattern": "[[Redis Distributed Lock & Safe Iteration]]"
    },
    {
        "id": "HERMES_PYDANTIC_V1_METHODS",
        "severity": "MEDIUM",
        "category": "Deprecation",
        "regex": r"\.(?:dict|parse_obj)\(",
        "extensions": [".py"],
        "message": "Uso de métodos obsoletos de Pydantic V1 (.dict(), .parse_obj()) que degradan el rendimiento de V2.",
        "fix_suggestion": "Migrar a .model_dump() y .model_validate().",
        "hermes_pattern": "[[Pydantic V2 Rust Core Validation]]"
    },
    {
        "id": "HERMES_EVAL_EXECUTION",
        "severity": "CRITICAL",
        "category": "Security",
        "regex": r"\beval\s*\(",
        "extensions": [".py", ".ts", ".js"],
        "message": "Invocación insegura de 'eval()'. Permite inyección de código arbitrario.",
        "fix_suggestion": "Usar 'ast.literal_eval()' o parsers declarativos seguros (Pydantic / Zod).",
        "hermes_pattern": "[[Secure Code Execution Sandbox]]"
    }
]


class SmartWorkspaceWatcher:
    """
    Escanea y vigila el espacio de trabajo en busca de antipatrones técnicos.
    """

    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path.cwd()

    def scan_file(self, file_path: Path) -> List[Dict[str, Any]]:
        findings = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        fname = file_path.name.lower()
        for rule in ANTIPATTERN_RULES:
            ext_match = any(fname.endswith(ext) or ext in fname for ext in rule["extensions"])
            if not ext_match:
                continue

            if re.search(rule["regex"], content, re.MULTILINE):
                findings.append({
                    "rule_id": rule["id"],
                    "severity": rule["severity"],
                    "category": rule["category"],
                    "file": str(file_path.relative_to(self.workspace_path) if file_path.is_relative_to(self.workspace_path) else file_path),
                    "message": rule["message"],
                    "fix_suggestion": rule["fix_suggestion"],
                    "hermes_pattern": rule["hermes_pattern"]
                })

        return findings

    def scan_workspace(self, root_dir: Optional[Path] = None) -> Dict[str, Any]:
        target = root_dir or self.workspace_path
        all_findings = []
        files_scanned = 0

        ignore_dirs = {".git", "node_modules", ".venv", "__pycache__", "dist", "build", ".hermes-hub"}

        for path in target.rglob("*"):
            if path.is_file() and not any(part in ignore_dirs for part in path.parts):
                findings = self.scan_file(path)
                if findings:
                    all_findings.extend(findings)
                files_scanned += 1

        alert_file = ALERTS_DIR / f"scan_report_{int(time.time())}.json"
        report_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "workspace": str(target),
            "files_scanned": files_scanned,
            "total_findings": len(all_findings),
            "findings": all_findings
        }

        try:
            with open(alert_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        return report_data

    def watch_daemon(self, interval_sec: float = 3.0):
        print(f"👀 [Smart Watcher] Vigilando espacio de trabajo: {self.workspace_path} (Ctrl+C para salir)...")
        last_mtimes: Dict[str, float] = {}

        try:
            while True:
                for path in self.workspace_path.rglob("*"):
                    if path.is_file() and not any(part in {".git", ".venv", "node_modules"} for part in path.parts):
                        mtime = path.stat().st_mtime
                        p_str = str(path)
                        if p_str in last_mtimes and mtime > last_mtimes[p_str]:
                            # Archivo modificado
                            findings = self.scan_file(path)
                            if findings:
                                print(f"\n⚠️ [ALERTA HERMES] Antipatrón detectado en {path.name}:")
                                for f in findings:
                                    print(f"   • [{f['severity']}] {f['message']}")
                                    print(f"   💡 Sugerencia: {f['fix_suggestion']}")
                        last_mtimes[p_str] = mtime
                time.sleep(interval_sec)
        except KeyboardInterrupt:
            print("\n👋 Smart Watcher detenido.")


if __name__ == "__main__":
    watcher = SmartWorkspaceWatcher()
    if "--watch" in sys.argv:
        watcher.watch_daemon()
    else:
        res = watcher.scan_workspace()
        print(f"Archivos escaneados: {res['files_scanned']} | Antipatrones detectados: {res['total_findings']}")
        if res["findings"]:
            for item in res["findings"]:
                print(f"  • [{item['severity']}] {item['file']}: {item['message']}")
