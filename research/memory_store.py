"""
memory_store.py
Hermes Knowledge Hub & Local Dual Memory Store for distilled research insights.
Supports Hermes Pro Obsidian template with Pydantic structured schemas.
"""
import os
import re
import json
import hashlib
import datetime
from typing import Optional, Union, Dict, Any, List

# Local directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_DIR = os.path.join(BASE_DIR, "memory")
NOTES_JSONL = os.path.join(MEMORY_DIR, "notes.jsonl")
NOTES_MD = os.path.join(MEMORY_DIR, "NOTES.md")

# Hermes Hub paths
HERMES_HUB_DIR = os.path.expanduser("~/.hermes-hub")
HERMES_PATTERNS_DIR = os.path.join(HERMES_HUB_DIR, "patterns")
HERMES_CONCEPTS_DIR = os.path.join(HERMES_HUB_DIR, "concepts")

os.makedirs(MEMORY_DIR, exist_ok=True)
if os.path.exists(HERMES_HUB_DIR):
    os.makedirs(HERMES_PATTERNS_DIR, exist_ok=True)
    os.makedirs(HERMES_CONCEPTS_DIR, exist_ok=True)


def _note_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _clean_filename(text: str) -> str:
    clean = re.sub(r'[\\/*?:"<>|]', "", text)
    clean = clean.replace(" ", "_").strip()
    return clean[:60]


def load_notes() -> List[Dict[str, Any]]:
    if not os.path.exists(NOTES_JSONL):
        return []
    notes = []
    with open(NOTES_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    notes.append(json.loads(line))
                except Exception:
                    continue
    return notes


def save_note(
    summary: Union[str, Any],
    source_repo: str,
    source_url: str,
    tags: Optional[List[str]] = None,
    license: Optional[str] = None,
    confidence: str = "high",
    title: Optional[str] = None,
    key_rules: Optional[List[str]] = None,
    antipatterns: Optional[List[str]] = None,
    code_example: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Appends a distilled note to the local store and generates an Obsidian note in Hermes Hub
    conforme al estándar Hermes Pro.
    """
    # Extract fields if summary is a Pydantic schema
    if hasattr(summary, "summary"):
        schema_obj = summary
        summary_text = schema_obj.summary
        title = schema_obj.title or title
        key_rules = schema_obj.key_rules or key_rules
        antipatterns = schema_obj.antipatterns or antipatterns
        code_example = schema_obj.code_example or code_example
        if schema_obj.tags:
            tags = list(set((tags or []) + schema_obj.tags))
    elif isinstance(summary, dict):
        summary_text = summary.get("summary", "")
        title = summary.get("title", title)
        key_rules = summary.get("key_rules", key_rules)
        antipatterns = summary.get("antipatterns", antipatterns)
        code_example = summary.get("code_example", code_example)
    else:
        summary_text = str(summary)

    notes = load_notes()
    nid = _note_id(summary_text)
    if any(n.get("id") == nid for n in notes):
        return None  # already exists

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    now_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    tags_list = tags or []
    repo_title = source_repo.replace("/", " - ")
    resolved_title = title or f"Pattern {repo_title}"

    note = {
        "id": nid,
        "title": resolved_title,
        "summary": summary_text,
        "key_rules": key_rules or ["Aplicar arquitectura modular desacoplada.", "Garantizar tipado estricto y manejo de errores.", "Optimizar asignaciones de memoria y ciclos."],
        "antipatterns": antipatterns or ["Evitar acoplamiento directo sin interfaces intermedias."],
        "code_example": code_example,
        "source_repo": source_repo,
        "source_url": source_url,
        "tags": tags_list,
        "license": license or "unknown",
        "confidence": confidence,
        "created": now_iso,
        "times_used": 0,
    }

    with open(NOTES_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(note, ensure_ascii=False) + "\n")

    _regenerate_markdown()
    _save_to_hermes_vault(note, now_date)
    return note


def _save_to_hermes_vault(note: Dict[str, Any], now_date: str):
    """Generates an Obsidian note inside ~/.hermes-hub/patterns/ with Hermes Pro template."""
    if not os.path.exists(HERMES_HUB_DIR):
        return

    title = note.get("title") or f"Pattern {note['source_repo'].replace('/', ' - ')}"
    filename = f"{_clean_filename(title)}.md"
    filepath = os.path.join(HERMES_PATTERNS_DIR, filename)

    tags_yaml = "\n".join([f"  - {t.lower().replace(' ', '-')}" for t in (["pattern", "github-research"] + note.get("tags", []))])
    wikilinks = "\n".join([f"- [[{t}]]" for t in note.get("tags", [])])

    rules_md = "\n".join([f"{i+1}. {r}" for i, r in enumerate(note.get("key_rules", []))])
    antipatterns_md = "\n".join([f"- {a}" for a in note.get("antipatterns", [])])
    
    code_block = ""
    if note.get("code_example"):
        code_block = f"""
## Ejemplo de Código Mínimo
```python
{note['code_example']}
```
"""

    content = f"""---
tags:
{tags_yaml}
created: {now_date}
id: {note['id']}
source_repo: {note['source_repo']}
source_url: {note['source_url']}
license: {note['license']}
confidence: {note['confidence']}
aliases:
  - {note['source_repo']}
  - {title}
---

# {title}

## Descripción del Patrón
{note['summary']}

## Reglas de Implementación
{rules_md}

## Antipatrones a Evitar
{antipatterns_md}
{code_block}
## Origen y Metadatos
- **Repositorio:** [{note['source_repo']}]({note['source_url']})
- **Licencia:** `{note['license']}`
- **Confianza:** `{note['confidence']}`
- **ID:** `{note['id']}`

## Enlaces Relacionados en Hermes
{wikilinks or "- [[Architecture]]"}
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def query_notes(keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    keyword = keyword.lower()
    notes = load_notes()
    scored = []
    for n in notes:
        haystack = (n.get("summary", "") + " " + n.get("title", "") + " " + " ".join(n.get("tags", [])) + " " + n.get("source_repo", "")).lower()
        if keyword in haystack:
            scored.append(n)
    return scored[:limit]


def mark_used(note_id: str):
    notes = load_notes()
    changed = False
    for n in notes:
        if n["id"] == note_id:
            n["times_used"] = n.get("times_used", 0) + 1
            changed = True
    if changed:
        with open(NOTES_JSONL, "w", encoding="utf-8") as f:
            for n in notes:
                f.write(json.dumps(n, ensure_ascii=False) + "\n")


def _regenerate_markdown():
    notes = load_notes()
    lines = [
        "# Hermes Research Memory",
        "",
        f"_{len(notes)} distilled engineering pattern(s)_",
        "",
    ]
    for n in sorted(notes, key=lambda x: x.get("created", ""), reverse=True):
        tags_str = ", ".join(n.get("tags", [])) or "general"
        title_str = n.get("title", n.get("id"))
        lines.append(f"## {title_str} ({n.get('id')}) — {tags_str}")
        lines.append(f"- **Source:** [{n['source_repo']}]({n['source_url']}) (license: `{n.get('license', 'unknown')}`)")
        lines.append(f"- **Confidence:** {n.get('confidence', 'high')} | **Used:** {n.get('times_used', 0)}x | **Added:** {n.get('created', '')}")
        lines.append(f"- **Descripción:** {n['summary']}")
        if n.get("key_rules"):
            lines.append("- **Reglas:** " + " | ".join(n["key_rules"][:2]))
        lines.append("")
    with open(NOTES_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
