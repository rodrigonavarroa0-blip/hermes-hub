"""
ast_graph_parser.py — Parser de Código Estructural AST Multi-Lenguaje de Hermes Hub.
Extrae símbolos de código (clases, funciones, interfaces, imports, decorators) en:
- Python (.py)
- TypeScript / JavaScript (.ts, .tsx, .js, .jsx)
- Rust (.rs)
- Go (.go)
Y vincula automáticamente el código del proyecto con los 429+ patrones arquitectónicos de Hermes.
"""
import os
import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any

HUB_PATH = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_PATH / "config"
GRAPH_FILE = CONFIG_DIR / "graph.json"


class ASTCodeGraphParser:
    """
    Parser estructural multi-lenguaje de código que construye un subgrafo de símbolos
    y los mapea semánticamente a los patrones y reglas de Hermes.
    """

    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = Path(workspace_path or Path.cwd()).resolve()
        self._load_hermes_patterns()

    def _load_hermes_patterns(self):
        """Carga los patrones y palabras clave del grafo de Hermes para vincular símbolos."""
        self.pattern_index: Dict[str, Dict[str, Any]] = {}
        if GRAPH_FILE.exists():
            try:
                with open(GRAPH_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                nodes = data.get("nodes", {})
                for nid, ndata in nodes.items():
                    self.pattern_index[nid] = {
                        "label": ndata.get("label", nid),
                        "keywords": set([k.lower() for k in ndata.get("keywords", [])]),
                        "type": ndata.get("type", "pattern")
                    }
            except Exception:
                pass

    def parse_python_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extrae símbolos de un archivo Python usando el módulo nativo ast."""
        symbols = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(file_path))
        except Exception:
            return symbols

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                is_async = isinstance(node, ast.AsyncFunctionDef)
                docstring = ast.get_docstring(node) or ""
                decorators = [ast.unparse(d) if hasattr(ast, "unparse") else str(d) for d in node.decorator_list]
                symbols.append({
                    "name": node.name,
                    "kind": "function" if not hasattr(node, "parent_class") else "method",
                    "language": "python",
                    "file": str(file_path.relative_to(self.workspace_path) if self.workspace_path in file_path.parents else file_path),
                    "line": node.lineno,
                    "is_async": is_async,
                    "docstring": docstring[:150],
                    "decorators": decorators
                })
            elif isinstance(node, ast.ClassDef):
                bases = [ast.unparse(b) if hasattr(ast, "unparse") else str(b) for b in node.bases]
                docstring = ast.get_docstring(node) or ""
                symbols.append({
                    "name": node.name,
                    "kind": "class",
                    "language": "python",
                    "file": str(file_path.relative_to(self.workspace_path) if self.workspace_path in file_path.parents else file_path),
                    "line": node.lineno,
                    "bases": bases,
                    "docstring": docstring[:150]
                })

        return symbols

    def parse_typescript_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extrae símbolos de TypeScript/JavaScript mediante análisis sintáctico de firmas."""
        symbols = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return symbols

        lines = content.splitlines()
        rel_path = str(file_path.relative_to(self.workspace_path) if self.workspace_path in file_path.parents else file_path)

        # 1. Clases e Interfaces
        class_regex = re.compile(r'^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?(class|interface)\s+([A-Za-z0-9_]+)(?:\s+extends\s+([A-Za-z0-9_]+))?')
        # 2. Funciones estándar y arrow functions exportadas
        func_regex = re.compile(r'^\s*(?:export\s+)?(?:default\s+)?(async\s+)?function\s+([A-Za-z0-9_]+)\s*\(')
        arrow_func_regex = re.compile(r'^\s*(?:export\s+)?const\s+([A-Za-z0-9_]+)\s*=\s*(async\s*)?\([^)]*\)\s*(?::\s*[^=]+)?\s*=>')

        for idx, line in enumerate(lines, 1):
            c_match = class_regex.match(line)
            if c_match:
                kind, name, extends_cls = c_match.groups()
                symbols.append({
                    "name": name,
                    "kind": kind.lower(),
                    "language": "typescript",
                    "file": rel_path,
                    "line": idx,
                    "extends": extends_cls
                })
                continue

            f_match = func_regex.match(line)
            if f_match:
                is_async, name = f_match.groups()
                symbols.append({
                    "name": name,
                    "kind": "function",
                    "language": "typescript",
                    "file": rel_path,
                    "line": idx,
                    "is_async": bool(is_async)
                })
                continue

            af_match = arrow_func_regex.match(line)
            if af_match:
                name, is_async = af_match.groups()
                symbols.append({
                    "name": name,
                    "kind": "arrow_function",
                    "language": "typescript",
                    "file": rel_path,
                    "line": idx,
                    "is_async": bool(is_async)
                })

        return symbols

    def parse_rust_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extrae structs, traits, enums y funciones en Rust."""
        symbols = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return symbols

        lines = content.splitlines()
        rel_path = str(file_path.relative_to(self.workspace_path) if self.workspace_path in file_path.parents else file_path)

        struct_regex = re.compile(r'^\s*(?:pub\s+)?(struct|trait|enum)\s+([A-Za-z0-9_]+)')
        fn_regex = re.compile(r'^\s*(?:pub\s+)?(async\s+)?fn\s+([A-Za-z0-9_]+)')

        for idx, line in enumerate(lines, 1):
            s_match = struct_regex.match(line)
            if s_match:
                kind, name = s_match.groups()
                symbols.append({
                    "name": name,
                    "kind": kind.lower(),
                    "language": "rust",
                    "file": rel_path,
                    "line": idx
                })
                continue

            f_match = fn_regex.match(line)
            if f_match:
                is_async, name = f_match.groups()
                symbols.append({
                    "name": name,
                    "kind": "function",
                    "language": "rust",
                    "file": rel_path,
                    "line": idx,
                    "is_async": bool(is_async)
                })

        return symbols

    def parse_go_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extrae funciones, structs e interfaces en Go."""
        symbols = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return symbols

        lines = content.splitlines()
        rel_path = str(file_path.relative_to(self.workspace_path) if self.workspace_path in file_path.parents else file_path)

        type_regex = re.compile(r'^\s*type\s+([A-Za-z0-9_]+)\s+(struct|interface)')
        func_regex = re.compile(r'^\s*func\s+(?:\([^)]+\)\s+)?([A-Za-z0-9_]+)\s*\(')

        for idx, line in enumerate(lines, 1):
            t_match = type_regex.match(line)
            if t_match:
                name, kind = t_match.groups()
                symbols.append({
                    "name": name,
                    "kind": kind.lower(),
                    "language": "go",
                    "file": rel_path,
                    "line": idx
                })
                continue

            f_match = func_regex.match(line)
            if f_match:
                name = f_match.group(1)
                symbols.append({
                    "name": name,
                    "kind": "function",
                    "language": "go",
                    "file": rel_path,
                    "line": idx
                })

        return symbols

    def scan_workspace_symbols(self, max_files: int = 150) -> Dict[str, Any]:
        """Escanea todos los archivos del workspace y extrae el árbol de símbolos."""
        all_symbols = []
        scanned_files = 0

        ignore_dirs = {".git", "node_modules", "target", "dist", "build", ".venv", "__pycache__", ".hermes-hub", ".obsidian"}

        for root, dirs, files in os.walk(self.workspace_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
            for file in files:
                fpath = Path(root) / file
                ext = fpath.suffix.lower()

                if ext == ".py":
                    all_symbols.extend(self.parse_python_file(fpath))
                    scanned_files += 1
                elif ext in (".ts", ".tsx", ".js", ".jsx"):
                    all_symbols.extend(self.parse_typescript_file(fpath))
                    scanned_files += 1
                elif ext == ".rs":
                    all_symbols.extend(self.parse_rust_file(fpath))
                    scanned_files += 1
                elif ext == ".go":
                    all_symbols.extend(self.parse_go_file(fpath))
                    scanned_files += 1

                if scanned_files >= max_files:
                    break
            if scanned_files >= max_files:
                break

        # Vincular símbolos con patrones de Hermes
        symbol_links = self._link_symbols_to_patterns(all_symbols)

        return {
            "workspace": str(self.workspace_path),
            "files_scanned": scanned_files,
            "total_symbols_extracted": len(all_symbols),
            "symbols": all_symbols,
            "pattern_bindings": symbol_links
        }

    def _link_symbols_to_patterns(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Mapea los nombres y docstrings de los símbolos a los patrones del grafo."""
        bindings = []
        for sym in symbols:
            name_tokens = set(re.findall(r'[a-zA-Z0-9]+', sym["name"].lower()))
            matched_patterns = []

            for pid, pdata in self.pattern_index.items():
                kws = pdata["keywords"]
                # Coincidencia con nombre de símbolo
                if name_tokens.intersection(kws) or any(t in pid.lower() for t in name_tokens if len(t) > 3):
                    matched_patterns.append({
                        "pattern_id": pid,
                        "label": pdata["label"],
                        "type": pdata["type"]
                    })

            if matched_patterns:
                bindings.append({
                    "symbol_name": sym["name"],
                    "file": sym["file"],
                    "line": sym["line"],
                    "kind": sym["kind"],
                    "associated_patterns": matched_patterns[:3]
                })

        return bindings


# Singleton
_AST_PARSER: Optional[ASTCodeGraphParser] = None


def get_ast_parser(workspace_path: Optional[Path] = None) -> ASTCodeGraphParser:
    global _AST_PARSER
    if _AST_PARSER is None or (workspace_path and _AST_PARSER.workspace_path != Path(workspace_path).resolve()):
        _AST_PARSER = ASTCodeGraphParser(workspace_path)
    return _AST_PARSER


if __name__ == "__main__":
    parser = get_ast_parser()
    report = parser.scan_workspace_symbols()
    print(f"Escaneo AST completado:")
    print(f"- Archivos analizados: {report['files_scanned']}")
    print(f"- Símbolos extraídos: {report['total_symbols_extracted']}")
    print(f"- Vínculos con patrones: {len(report['pattern_bindings'])}")
