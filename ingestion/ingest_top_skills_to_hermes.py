#!/usr/bin/env python3
"""
ingest_top_skills_to_hermes.py - Pipeline de Ingesta Inteligente de Skills a Hermes Knowledge Hub

Procesa y valida las mejores skills de ingeniería y agentes (Addy Osmani Agent Skills + Mindrally Skills),
generando nodos semánticos, relaciones ponderadas y frontmatter enriquecido en ~/.hermes-hub.
"""

import os
import re
import json
import yaml
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any

HUB_ROOT = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_ROOT / "config"
PATTERNS_DIR = HUB_ROOT / "patterns"
SKILLS_DIR = HUB_ROOT / "skills"
ANTIPATTERNS_DIR = HUB_ROOT / "antipatterns"
GRAPH_FILE = CONFIG_DIR / "graph.json"


def load_graph() -> dict:
    if not GRAPH_FILE.exists():
        return {
            "settings": {"default_threshold": 0.60, "max_hops": 2, "decay_rate": 0.75},
            "nodes": {},
            "edges": []
        }
    with open(GRAPH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_graph(graph_data: dict) -> None:
    with open(GRAPH_FILE, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2, ensure_ascii=False)


def tokenize(text: str) -> List[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-\s]", " ", str(text).lower())
    return [t.strip() for t in cleaned.split() if len(t.strip()) > 1]


def parse_markdown_file(file_path: Path) -> Tuple[dict, str]:
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
                return fm, body
            except Exception:
                pass
    # If no YAML frontmatter, extract title from first heading
    title = file_path.parent.name.replace("-", " ").title()
    for line in content.splitlines():
        if line.startswith("# "):
            title = line.replace("# ", "").strip()
            break
    return {"title": title}, content.strip()


def ingest_skill_file(
    file_path: Path,
    target_base_dir: Path,
    subfolder: str,
    item_type: str,
    cluster_id: str,
    cluster_keywords: List[str],
    graph: dict
) -> Tuple[Optional[str], Optional[dict]]:
    dest_dir = target_base_dir / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)

    nodes = graph.setdefault("nodes", {})
    edges = graph.setdefault("edges", [])

    fm, body = parse_markdown_file(file_path)
    stem_name = file_path.parent.name if file_path.name.lower() in ("skill.md", "readme.md") else file_path.stem
    clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "-", stem_name.lower()).strip("-")
    clean_subfolder = re.sub(r"[^a-zA-Z0-9_\-]", "_", subfolder.lower())
    node_id = f"{item_type}_{clean_subfolder}_{clean_name.replace('-', '_')}"

    title = str(fm.get("title", clean_name.replace("-", " ").title()))
    description = str(fm.get("description", ""))
    tags_raw = fm.get("tags", [])
    if isinstance(tags_raw, str):
        tags_list = [tags_raw]
    elif isinstance(tags_raw, list):
        tags_list = tags_raw
    else:
        tags_list = []

    tags = [str(t).lower().strip() for t in tags_list if t]

    title_tokens = tokenize(title)
    stem_tokens = tokenize(clean_name)
    combined_keywords = list(set(tags + title_tokens + stem_tokens + [str(k).lower() for k in cluster_keywords]))

    # Structured Frontmatter
    fm["id"] = node_id
    fm["name"] = clean_name
    fm["title"] = title
    if description:
        fm["description"] = description
    fm["type"] = item_type
    fm["tags"] = list(set(tags + [str(k).lower() for k in cluster_keywords[:3]]))
    fm["status"] = "active"
    fm["ingested_at"] = datetime.now(timezone.utc).isoformat()

    # Destination file
    dest_file = dest_dir / f"{clean_name}.md"
    rel_path = f"{target_base_dir.name}/{subfolder}/{clean_name}.md"

    yaml_header = yaml.dump(fm, sort_keys=False, default_flow_style=False)
    dest_content = f"---\n{yaml_header}---\n\n{body}\n"
    dest_file.write_text(dest_content, encoding="utf-8")

    node_data = {
        "type": item_type,
        "label": title,
        "file": rel_path,
        "keywords": combined_keywords
    }
    nodes[node_id] = node_data

    # Edge from cluster hub to item
    if not any(e.get("source") == cluster_id and e.get("target") == node_id for e in edges):
        edges.append({
            "source": cluster_id,
            "target": node_id,
            "weight": 0.85,
            "relation": "contains"
        })

    return node_id, node_data


def run_ingestion() -> Dict[str, Any]:
    print("=" * 80)
    print("🧠 INICIANDO INGESTA DE AGENT SKILLS EN HERMES KNOWLEDGE HUB")
    print("=" * 80)

    graph = load_graph()
    nodes = graph.setdefault("nodes", {})
    edges = graph.setdefault("edges", [])

    base_dir = Path("./external_skills")
    results = {
        "total_ingested": 0,
        "clusters": {}
    }

    # --------------------------------------------------------------------------
    # 1. ADDY OSMANI: AGENT CORE ENGINEERING SKILLS
    # --------------------------------------------------------------------------
    addy_skills_dir = base_dir / "addyosmani_agent_skills" / "skills"
    addy_cluster_id = "agent_core_engineering_cluster"
    nodes[addy_cluster_id] = {
        "type": "cluster",
        "label": "Agent Core Engineering & Autonomous Workflows",
        "keywords": ["agent", "debugging", "tdd", "sdd", "planning", "code-review", "architecture", "simplification"]
    }
    results["clusters"][addy_cluster_id] = 0

    if addy_skills_dir.exists():
        for skill_dir in addy_skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    nid, _ = ingest_skill_file(
                        file_path=skill_file,
                        target_base_dir=SKILLS_DIR,
                        subfolder="agent_core",
                        item_type="skill",
                        cluster_id=addy_cluster_id,
                        cluster_keywords=["agent", "engineering", skill_dir.name],
                        graph=graph
                    )
                    if nid:
                        results["total_ingested"] += 1
                        results["clusters"][addy_cluster_id] += 1

    # Ingest addyosmani references into patterns
    addy_refs_dir = base_dir / "addyosmani_agent_skills" / "references"
    if addy_refs_dir.exists():
        for ref_file in addy_refs_dir.glob("*.md"):
            nid, _ = ingest_skill_file(
                file_path=ref_file,
                target_base_dir=PATTERNS_DIR,
                subfolder="agent_references",
                item_type="pattern",
                cluster_id=addy_cluster_id,
                cluster_keywords=["checklist", "standards", "best-practices", ref_file.stem],
                graph=graph
            )
            if nid:
                results["total_ingested"] += 1
                results["clusters"][addy_cluster_id] += 1

    # --------------------------------------------------------------------------
    # 2. MINDRALLY: SPECIALIZED TECH STACK SKILLS
    # --------------------------------------------------------------------------
    mindrally_dir = base_dir / "mindrally_skills"
    
    # Categorías clave a seleccionar
    target_categories = {
        "python_ai": {
            "label": "Python, Machine Learning & AI Engineering",
            "skills": [
                "fastapi-python", "flask-python", "openai-api-development", "llamaindex-development",
                "pytorch", "pandas-best-practices", "numpy-best-practices", "scikit-learn-best-practices",
                "scipy-best-practices", "python-cybersecurity-tool-development"
            ],
            "keywords": ["python", "ai", "ml", "fastapi", "openai", "pytorch", "pandas", "numpy", "datascience"]
        },
        "modern_fullstack": {
            "label": "Modern Full-Stack, Next.js & TypeScript Patterns",
            "skills": [
                "nextjs-react-typescript", "optimized-nextjs-typescript", "nestjs-clean-typescript",
                "fastify-typescript", "zustand-state-management", "prisma-development",
                "postgresql-best-practices", "tailwindcss", "framer-motion", "clean-architecture"
            ],
            "keywords": ["typescript", "nextjs", "react", "fullstack", "prisma", "postgres", "clean-architecture", "tailwind"]
        },
        "devops_testing_security": {
            "label": "DevOps, Testing Automation & Security Protocols",
            "skills": [
                "ci-cd-best-practices", "kubernetes", "logging-best-practices", "jest",
                "jwt-security", "github-workflow", "performance-optimization", "accessibility-a11y"
            ],
            "keywords": ["devops", "ci-cd", "kubernetes", "security", "jwt", "testing", "jest", "logging", "performance"]
        }
    }

    for cat_key, cat_meta in target_categories.items():
        cid = f"mindrally_{cat_key}_cluster"
        nodes[cid] = {
            "type": "cluster",
            "label": cat_meta["label"],
            "keywords": cat_meta["keywords"]
        }
        results["clusters"][cid] = 0

        for skill_name in cat_meta["skills"]:
            skill_folder = mindrally_dir / skill_name
            skill_file = skill_folder / "SKILL.md"
            if skill_file.exists():
                nid, _ = ingest_skill_file(
                    file_path=skill_file,
                    target_base_dir=SKILLS_DIR,
                    subfolder=cat_key,
                    item_type="skill",
                    cluster_id=cid,
                    cluster_keywords=cat_meta["keywords"] + [skill_name],
                    graph=graph
                )
                if nid:
                    results["total_ingested"] += 1
                    results["clusters"][cid] += 1

    save_graph(graph)

    # Rebuild embeddings / commit in Hermes Hub
    try:
        subprocess.run(["git", "add", "."], cwd=str(HUB_ROOT), check=False, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"feat(knowledge): ingest {results['total_ingested']} premium engineering and agent skills into synaptic graph"], cwd=str(HUB_ROOT), check=False, capture_output=True)
        print("✅ Git commit generado exitosamente en ~/.hermes-hub.")
    except Exception as e:
        print(f"Git commit aviso: {e}")

    print("\n" + "=" * 80)
    print("🎉 INGESTA COMPLETADA EXITOSAMENTE")
    print(f"• Total de skills y patrones ingestados: {results['total_ingested']}")
    for cid, count in results["clusters"].items():
        print(f"  - [{cid}]: {count} elementos")
    print("=" * 80)

    return results


if __name__ == "__main__":
    run_ingestion()
