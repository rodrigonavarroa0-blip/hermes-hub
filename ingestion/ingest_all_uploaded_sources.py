#!/usr/bin/env python3
"""
ingest_all_uploaded_sources.py
Ingestión Masiva de Conocimiento en Hermes Hub (~/.hermes-hub) a partir de:
1. ECC-main (1).zip (897 skills de ingeniería, agentes y arquitectura)
2. superpowers-main.zip (14 skills especializadas de Claude/Agent workflows)
3. mindrally_skills (240 skills de desarrollo web, cloud, backend, mobile y testing)
4. awesome-llm-apps-main.zip (213 apps completas, MCP agents, RAG y multi-agent architectures)
5. public-apis-master.zip (catálogo de APIs públicas y patrones de integración)
"""

import os
import sys
import re
import json
import yaml
import zipfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Set, Tuple, Any

HUB_ROOT = Path(os.environ.get("HERMES_HUB_PATH", Path.home() / ".hermes-hub")).resolve()
CONFIG_DIR = HUB_ROOT / "config"
SKILLS_DIR = HUB_ROOT / "skills"
PATTERNS_DIR = HUB_ROOT / "patterns"
APIS_DIR = HUB_ROOT / "apis"
CLUSTERS_DIR = HUB_ROOT / "clusters"
MEJORA_HERMES_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = MEJORA_HERMES_DIR / "archives"

# Stopwords y tokenizer
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can",
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having",
    "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is",
    "isn't", "it", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "shan't", "she", "should", "shouldn't", "so", "some", "such", "than", "that",
    "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "were", "weren't",
    "what", "when", "where", "which", "while", "who", "whom", "why", "with", "won't", "would", "wouldn't",
    "you", "your", "yours", "yourself", "yourselves", "use", "using", "used", "uses", "guidance", "guide"
}

def _tokenize(text: str) -> List[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-\s]", " ", str(text).lower())
    tokens = [t.strip() for t in cleaned.split() if len(t.strip()) >= 2]
    return [t for t in tokens if t not in STOPWORDS]

def sanitize_id(raw_id: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-]", "-", str(raw_id).lower()).strip("-")
    cleaned = re.sub(r"-+", "-", cleaned)
    return cleaned

def parse_frontmatter(content: str) -> Tuple[dict, str]:
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
                return fm, body
            except Exception:
                pass
    return {}, content.strip()

def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 3.8))


class MasterKnowledgeIngestor:
    def __init__(self):
        self.graph = self._load_graph()
        self.nodes: Dict[str, dict] = self.graph.get("nodes", {})
        self.edges: List[dict] = self.graph.get("edges", [])
        
        # Edge lookup set: (min_id, max_id, relation)
        self.existing_edges: Set[Tuple[str, str, str]] = set()
        for e in self.edges:
            s, t = e.get("source", ""), e.get("target", "")
            r = e.get("relation", "relates_to")
            if s and t:
                pair = (min(s, t), max(s, t), r)
                self.existing_edges.add(pair)

        self.stats = {
            "ecc_skills": 0,
            "superpowers_skills": 0,
            "mindrally_skills": 0,
            "awesome_llm_apps": 0,
            "public_apis": 0,
            "new_nodes": 0,
            "updated_nodes": 0,
            "new_edges": 0
        }

    def _load_graph(self) -> dict:
        if GRAPH_FILE.exists():
            with open(GRAPH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "settings": {"default_threshold": 0.60, "max_hops": 2, "decay_rate": 0.75},
            "nodes": {},
            "edges": []
        }

    def register_or_update_node(self, node_id: str, node_type: str, label: str, file_rel: str, keywords: List[str]):
        token_keywords = set()
        for k in keywords:
            token_keywords.update(_tokenize(str(k)))
        token_keywords.update(_tokenize(label))
        token_keywords.update(_tokenize(node_id))

        if node_id in self.nodes:
            # Merge keywords
            existing = set(self.nodes[node_id].get("keywords", []))
            merged = sorted(list(existing.union(token_keywords)))
            self.nodes[node_id]["keywords"] = merged
            self.nodes[node_id]["file"] = file_rel
            self.stats["updated_nodes"] += 1
        else:
            self.nodes[node_id] = {
                "type": node_type,
                "label": label,
                "file": file_rel,
                "keywords": sorted(list(token_keywords))
            }
            self.stats["new_nodes"] += 1

    def add_edge(self, source: str, target: str, weight: float = 0.75, relation: str = "relates_to"):
        if source == target:
            return
        if source not in self.nodes or target not in self.nodes:
            return
        
        pair = (min(source, target), max(source, target), relation)
        if pair in self.existing_edges:
            return

        self.edges.append({
            "source": source,
            "target": target,
            "weight": round(weight, 3),
            "relation": relation
        })
        self.existing_edges.add(pair)
        self.stats["new_edges"] += 1

    # --------------------------------------------------------------------------
    # 1. Ingest ECC-main (897 skills)
    # --------------------------------------------------------------------------
    def ingest_ecc(self, zip_path: Path):
        print(f"📦 Procesando ECC-main.zip ({zip_path.name})...")
        with zipfile.ZipFile(zip_path) as zf:
            skill_files = [n for n in zf.namelist() if n.endswith("SKILL.md") and not n.startswith("__MACOSX")]
            print(f"  Encontrados {len(skill_files)} SKILL.md en ECC...")
            
            for file_path in skill_files:
                try:
                    # Extraer nombre del skill
                    # Formato típico: ECC-main/.agents/skills/<skill_name>/SKILL.md
                    parts = file_path.split("/")
                    skill_folder = parts[-2]
                    raw_content = zf.read(file_path).decode("utf-8", errors="ignore")
                    
                    fm, body = parse_frontmatter(raw_content)
                    skill_name = fm.get("name", skill_folder)
                    skill_desc = fm.get("description", "")
                    
                    if not skill_desc and body:
                        # Extraer primera oración
                        first_lines = [l.strip() for l in body.split("\n") if l.strip() and not l.startswith("#")]
                        if first_lines:
                            skill_desc = first_lines[0][:200]

                    clean_name = sanitize_id(skill_name)
                    node_id = f"skill:{clean_name}"
                    target_dir = SKILLS_DIR / clean_name
                    target_file = target_dir / "SKILL.md"
                    target_dir.mkdir(parents=True, exist_ok=True)

                    # Escribir archivo en hub
                    fm_out = {
                        "name": clean_name,
                        "description": skill_desc or f"Skill especializada en {clean_name}",
                        "source": "ECC-main",
                        "tokens_estimate": estimate_tokens(raw_content)
                    }
                    yaml_hdr = yaml.dump(fm_out, sort_keys=False, default_flow_style=False)
                    target_file.write_text(f"---\n{yaml_hdr}---\n\n{body}\n", encoding="utf-8")

                    # Registrar nodo
                    rel_path = f"skills/{clean_name}/SKILL.md"
                    kws = [clean_name, skill_desc] + _tokenize(clean_name.replace("-", " ")) + _tokenize(skill_desc)
                    self.register_or_update_node(node_id, "skill", skill_name.replace("-", " ").title(), rel_path, kws)
                    self.stats["ecc_skills"] += 1

                except Exception as e:
                    print(f"  ⚠️ Error en {file_path}: {e}")

    # --------------------------------------------------------------------------
    # 2. Ingest Superpowers (14 skills + scripts)
    # --------------------------------------------------------------------------
    def ingest_superpowers(self, zip_path: Path):
        print(f"⚡ Procesando superpowers-main.zip ({zip_path.name})...")
        with zipfile.ZipFile(zip_path) as zf:
            skill_files = [n for n in zf.namelist() if n.endswith("SKILL.md") and not n.startswith("__MACOSX")]
            print(f"  Encontrados {len(skill_files)} SKILL.md en Superpowers...")
            
            for file_path in skill_files:
                try:
                    parts = file_path.split("/")
                    skill_folder = parts[-2]
                    raw_content = zf.read(file_path).decode("utf-8", errors="ignore")
                    
                    fm, body = parse_frontmatter(raw_content)
                    skill_name = fm.get("name", skill_folder)
                    skill_desc = fm.get("description", "")
                    
                    clean_name = sanitize_id(skill_name)
                    node_id = f"skill:{clean_name}"
                    target_dir = SKILLS_DIR / clean_name
                    target_file = target_dir / "SKILL.md"
                    target_dir.mkdir(parents=True, exist_ok=True)

                    # Extraer posibles scripts de soporte de este skill
                    skill_prefix = "/".join(parts[:-1]) + "/"
                    for member in zf.namelist():
                        if member.startswith(skill_prefix) and not member.endswith("/"):
                            rel_in_skill = member[len(skill_prefix):]
                            dest_member = target_dir / rel_in_skill
                            dest_member.parent.mkdir(parents=True, exist_ok=True)
                            dest_member.write_bytes(zf.read(member))

                    fm_out = {
                        "name": clean_name,
                        "description": skill_desc or f"Superpower workflow skill: {clean_name}",
                        "source": "superpowers-main",
                        "tokens_estimate": estimate_tokens(raw_content)
                    }
                    yaml_hdr = yaml.dump(fm_out, sort_keys=False, default_flow_style=False)
                    target_file.write_text(f"---\n{yaml_hdr}---\n\n{body}\n", encoding="utf-8")

                    rel_path = f"skills/{clean_name}/SKILL.md"
                    kws = [clean_name, skill_desc, "superpowers", "agent-workflow"] + _tokenize(clean_name.replace("-", " "))
                    self.register_or_update_node(node_id, "skill", f"Superpower: {skill_name.replace('-', ' ').title()}", rel_path, kws)
                    self.stats["superpowers_skills"] += 1

                except Exception as e:
                    print(f"  ⚠️ Error en {file_path}: {e}")

    # --------------------------------------------------------------------------
    # 3. Ingest Mindrally Skills (240 skills)
    # --------------------------------------------------------------------------
    def ingest_mindrally(self, source_dir: Path):
        print(f"🧠 Procesando mindrally_skills ({source_dir.name})...")
        skill_dirs = [d for d in source_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        print(f"  Encontrados {len(skill_dirs)} directorios de skills en Mindrally...")
        
        for d in skill_dirs:
            skill_md = d / "SKILL.md"
            if not skill_md.exists():
                continue
            try:
                raw_content = skill_md.read_text(encoding="utf-8", errors="ignore")
                fm, body = parse_frontmatter(raw_content)
                
                skill_name = fm.get("name", d.name)
                skill_desc = fm.get("description", "")
                
                clean_name = sanitize_id(skill_name)
                node_id = f"skill:{clean_name}"
                target_dir = SKILLS_DIR / clean_name
                target_file = target_dir / "SKILL.md"
                target_dir.mkdir(parents=True, exist_ok=True)

                # Copiar todo el directorio de skill si tiene scripts o subdirectorios
                for item in d.rglob("*"):
                    if item.is_file():
                        rel = item.relative_to(d)
                        dest = target_dir / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(item.read_bytes())

                fm_out = {
                    "name": clean_name,
                    "description": skill_desc or f"Mindrally verified skill: {clean_name}",
                    "source": "mindrally_skills",
                    "tokens_estimate": estimate_tokens(raw_content)
                }
                yaml_hdr = yaml.dump(fm_out, sort_keys=False, default_flow_style=False)
                target_file.write_text(f"---\n{yaml_hdr}---\n\n{body}\n", encoding="utf-8")

                rel_path = f"skills/{clean_name}/SKILL.md"
                kws = [clean_name, skill_desc, "mindrally"] + _tokenize(clean_name.replace("-", " ")) + _tokenize(skill_desc)
                self.register_or_update_node(node_id, "skill", skill_name.replace("-", " ").title(), rel_path, kws)
                self.stats["mindrally_skills"] += 1

            except Exception as e:
                print(f"  ⚠️ Error en {d.name}: {e}")

    # --------------------------------------------------------------------------
    # 4. Ingest Awesome LLM Apps (213 apps & patterns)
    # --------------------------------------------------------------------------
    def ingest_awesome_llm_apps(self, zip_path: Path):
        print(f"🤖 Procesando awesome-llm-apps-main.zip ({zip_path.name})...")
        with zipfile.ZipFile(zip_path) as zf:
            readmes = [n for n in zf.namelist() if n.endswith("README.md") and not n.startswith("awesome-llm-apps-main/.github") and not n.startswith("__MACOSX")]
            print(f"  Encontrados {len(readmes)} READMEs de apps LLM...")
            
            for file_path in readmes:
                parts = file_path.split("/")
                if len(parts) < 3:
                    continue
                try:
                    category = parts[1] # e.g. mcp_ai_agents, advanced_ai_agents, rag_tutorials
                    app_name = parts[-2]
                    raw_content = zf.read(file_path).decode("utf-8", errors="ignore")
                    
                    if len(raw_content.strip()) < 50:
                        continue

                    clean_app = sanitize_id(app_name)
                    node_id = f"pattern:llm-app-{clean_app}"
                    target_file = PATTERNS_DIR / f"llm_app_{clean_app}.md"
                    target_file.parent.mkdir(parents=True, exist_ok=True)

                    # Resumen y descripción
                    first_lines = [l.strip() for l in raw_content.split("\n") if l.strip() and not l.startswith("#")]
                    summary = first_lines[0][:250] if first_lines else f"Patrón de aplicación LLM: {app_name}"

                    fm_out = {
                        "name": f"llm-app-{clean_app}",
                        "title": app_name.replace("_", " ").title(),
                        "category": category,
                        "description": summary,
                        "source": "awesome-llm-apps",
                        "tokens_estimate": estimate_tokens(raw_content)
                    }
                    yaml_hdr = yaml.dump(fm_out, sort_keys=False, default_flow_style=False)
                    target_file.write_text(f"---\n{yaml_hdr}---\n\n# {app_name.replace('_', ' ').title()}\n\n{raw_content}\n", encoding="utf-8")

                    rel_path = f"patterns/llm_app_{clean_app}.md"
                    kws = [clean_app, category, "llm-app", "rag", "agent", "ai-pattern"] + _tokenize(app_name.replace("_", " ")) + _tokenize(category) + _tokenize(summary)
                    self.register_or_update_node(node_id, "pattern", f"LLM App: {app_name.replace('_', ' ').title()}", rel_path, kws)
                    self.stats["awesome_llm_apps"] += 1

                except Exception as e:
                    print(f"  ⚠️ Error en {file_path}: {e}")

    # --------------------------------------------------------------------------
    # 5. Ingest Public APIs & API Catalog
    # --------------------------------------------------------------------------
    def ingest_public_apis(self, zip_path: Path):
        print(f"🌐 Procesando public-apis-master.zip ({zip_path.name})...")
        APIS_DIR.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            # Extraer especificaciones y validaciones
            target_spec = APIS_DIR / "public_apis_catalog_standards.md"
            content = """# Catálogo y Estándares de Integración de APIs Públicas

## 1. Directrices de Autenticación
- **apiKey**: Parámetros pasados en headers (`X-API-Key`, `Authorization: Bearer <key>`) o query params.
- **OAuth 2.0**: Flujos de autorización PKCE para SPAs / mobile, client_credentials para servidores.
- **No Auth**: Endpoints abiertos con rate limiting basado en IP.

## 2. Política de CORS y HTTPS
- Toda API integrada en producción debe operar sobre **HTTPS** (TLS 1.3).
- Validar soporte de **CORS** (`Access-Control-Allow-Origin`) para llamadas de clientes web.
- En caso de CORS restrictivo, implementar API Route Proxy (Next.js `/api/proxy` o FastAPI proxy).

## 3. Manejo de Errores y Circuit Breakers
- Implementar reintentos exponenciales con jitter para respuestas `429 Too Many Requests` y `503 Service Unavailable`.
- Fallback con caché local para datos semánticos no críticos.
"""
            fm_out = {
                "name": "public-apis-catalog-standards",
                "category": "api-standards",
                "description": "Estándares y protocolos para la integración segura de APIs públicas y servicios externos.",
                "tokens_estimate": estimate_tokens(content)
            }
            yaml_hdr = yaml.dump(fm_out, sort_keys=False, default_flow_style=False)
            target_spec.write_text(f"---\n{yaml_hdr}---\n\n{content}\n", encoding="utf-8")

            node_id = "api:public-apis-integration-standards"
            self.register_or_update_node(
                node_id,
                "api",
                "Public APIs Integration Standards",
                "apis/public_apis_catalog_standards.md",
                ["api", "public-api", "oauth", "cors", "https", "rest", "rate-limiting", "circuit-breaker"]
            )
            self.stats["public_apis"] += 1

    # --------------------------------------------------------------------------
    # 6. Auto Synaptic Wiring (Hebbian & Clusters)
    # --------------------------------------------------------------------------
    def wire_synaptic_graph(self):
        print("\n🧠 Generando Conexiones Sinápticas (Spreading Activation Graph)...")

        # Inverted index de tokens
        token_to_nodes: Dict[str, Set[str]] = {}
        for nid, ndata in self.nodes.items():
            for kw in ndata.get("keywords", []):
                if kw not in token_to_nodes:
                    token_to_nodes[kw] = set()
                token_to_nodes[kw].add(nid)

        # 1. Conectar a Clusters Principales
        cluster_keywords = {
            "cluster:frontend": ["frontend", "react", "nextjs", "vue", "angular", "tailwind", "css", "html", "svelte", "astro", "alpine", "ui", "dom", "web"],
            "cluster:backend": ["backend", "fastapi", "django", "flask", "node", "express", "nest", "spring", "aspnet", "api", "rest", "graphql", "grpc", "server"],
            "cluster:agentic-ai": ["agent", "agentic", "mcp", "fastmcp", "llm", "rag", "langchain", "llamaindex", "crewai", "autogen", "prompt", "token", "multimodal"],
            "cluster:databases": ["database", "sql", "postgres", "mysql", "sqlite", "duckdb", "mongodb", "redis", "prisma", "sqlalchemy", "drizzle", "vector", "qdrant", "pinecone", "chroma"],
            "cluster:devops-cloud": ["docker", "kubernetes", "aws", "gcp", "azure", "ci-cd", "github-actions", "terraform", "ansible", "nginx", "linux", "devops"],
            "cluster:security": ["security", "auth", "oauth", "jwt", "pentesting", "vulnerability", "encryption", "cors", "owasp", "sanitization"],
            "cluster:testing-qa": ["testing", "test", "pytest", "jest", "vitest", "playwright", "cypress", "mock", "tdd", "e2e"],
            "cluster:mobile": ["mobile", "android", "ios", "flutter", "react-native", "swift", "kotlin", "capacitor"]
        }

        # Asegurar nodos de cluster
        CLUSTERS_DIR.mkdir(parents=True, exist_ok=True)
        for cid, kws in cluster_keywords.items():
            c_name = cid.split(":")[-1].replace("-", " ").title()
            if cid not in self.nodes:
                c_file = CLUSTERS_DIR / f"{cid.split(':')[-1]}.md"
                c_file.write_text(f"# Cluster: {c_name}\n\nHub de concentración para {c_name}.\n", encoding="utf-8")
                self.register_or_update_node(cid, "cluster", f"Cluster: {c_name}", f"clusters/{cid.split(':')[-1]}.md", kws)

            # Conectar nodos que coincidan con los keywords del cluster
            for kw in kws:
                if kw in token_to_nodes:
                    for target_nid in token_to_nodes[kw]:
                        if target_nid != cid:
                            self.add_edge(cid, target_nid, weight=0.80, relation="clusters_node")

        # 2. Conectar Nodos Hermanos por Co-ocurrencia de Tokens Significativos
        print("  Cableando sinapsis inter-nodos...")
        # Iterar sobre pares que comparten tokens clave fuertes
        for kw, matching_nodes in token_to_nodes.items():
            if len(matching_nodes) > 1 and len(matching_nodes) <= 15: # Evitar tokens hiper genéricos
                nodes_list = list(matching_nodes)
                for i in range(len(nodes_list)):
                    for j in range(i + 1, min(i + 5, len(nodes_list))): # Limitar conexiones por token
                        u, v = nodes_list[i], nodes_list[j]
                        if u != v:
                            self.add_edge(u, v, weight=0.65, relation="semantic_co_occurrence")

        # 3. Limpiar aristas dangling (hacia nodos inexistentes)
        valid_nodes = set(self.nodes.keys())
        clean_edges = []
        for e in self.edges:
            if e.get("source") in valid_nodes and e.get("target") in valid_nodes:
                clean_edges.append(e)
        self.edges = clean_edges

        print(f"  Total Nodos Finales: {len(self.nodes)}")
        print(f"  Total Aristas Finales: {len(self.edges)}")

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        temp_file = GRAPH_FILE.with_suffix(".tmp")
        data = {
            "settings": self.graph.get("settings", {"default_threshold": 0.60, "max_hops": 2, "decay_rate": 0.75}),
            "nodes": self.nodes,
            "edges": self.edges
        }
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_file.replace(GRAPH_FILE)
        print(f"\n✅ Grafo guardado exitosamente en: {GRAPH_FILE}")


def main():
    print("=" * 70)
    print("🚀 INICIANDO INGESTIÓN MASIVA MULTI-FUENTE EN HERMES KNOWLEDGE HUB")
    print("=" * 70)

    ingestor = MasterKnowledgeIngestor()

    # 1. ECC-main (1).zip
    ecc_zip = BASE_DIR / "ECC-main (1).zip"
    if ecc_zip.exists():
        ingestor.ingest_ecc(ecc_zip)

    # 2. superpowers-main.zip
    sp_zip = BASE_DIR / "superpowers-main.zip"
    if sp_zip.exists():
        ingestor.ingest_superpowers(sp_zip)

    # 3. mindrally_skills
    mr_dir = BASE_DIR / "external_skills" / "mindrally_skills"
    if mr_dir.exists():
        ingestor.ingest_mindrally(mr_dir)

    # 4. awesome-llm-apps-main.zip
    llm_zip = BASE_DIR / "awesome-llm-apps-main.zip"
    if llm_zip.exists():
        ingestor.ingest_awesome_llm_apps(llm_zip)

    # 5. public-apis-master.zip
    api_zip = BASE_DIR / "public-apis-master.zip"
    if api_zip.exists():
        ingestor.ingest_public_apis(api_zip)

    # Cablear el grafo
    ingestor.wire_synaptic_graph()

    # Guardar
    ingestor.save()

    print("\n" + "=" * 70)
    print("📊 REPORTE DE INGESTIÓN FINAL")
    print("=" * 70)
    for k, v in ingestor.stats.items():
        print(f"  • {k}: {v}")
    print("=" * 70)


if __name__ == "__main__":
    main()
