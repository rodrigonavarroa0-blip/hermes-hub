#!/usr/bin/env python3
"""
loop.py — Hermes Repo Research & Pattern Ingestion Loop

Ciclo de investigación autónomo:
    1. Query    -> Tema o problema de arquitectura a investigar
    2. Retrieve -> Verifica memoria local y Vault de Hermes para evitar duplicados
    3. Search   -> Búsqueda de repositorios de calidad en GitHub
    4. Fetch    -> Descarga READMEs y código clave
    5. Distill  -> Síntesis con Gemini / LLM a patrones accionables
    6. Store    -> Almacenamiento dual (JSONL + Notas Obsidian en ~/.hermes-hub/patterns)
    7. Report   -> Resumen de patrones incorporados

Uso:
    python loop.py "fastapi background workers" --language python --n 3
    python loop.py --query-memory "rate limiting"
"""
import os
import sys
import time
import argparse

# Ensure local imports work regardless of execution location
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from github_source import search_repos, list_repo_readme
from memory_store import save_note, query_notes, load_notes
from distill import distill


def already_have_source(source_url):
    return any(n.get("source_url") == source_url for n in load_notes())


def run_cycle(topic, language=None, n=5, sleep_between=1.0):
    print(f"\n==================================================")
    print(f"🔬 Hermes Research Loop: '{topic}' (Lenguaje: {language or 'Cualquiera'})")
    print(f"==================================================")

    existing = query_notes(topic)
    if existing:
        print(f"\n[Hermes Memory] Se encontraron {len(existing)} patrón(es) previo(s) en memoria:")
        for note in existing[:3]:
            print(f"  📌 [{note['id']}] ({note['source_repo']}): {note['summary'][:110]}...")

    print(f"\n[GitHub Search] Consultando repositorios relevantes sobre '{topic}'...")
    try:
        repos = search_repos(topic, language=language, max_results=n)
    except Exception as e:
        print(f"[GitHub Search] Error al consultar API: {e}", file=sys.stderr)
        return []

    if not repos:
        print("[GitHub Search] No se encontraron repositorios.")
        return []

    learned = []
    for repo in repos:
        full_name = repo["full_name"]
        url = repo["html_url"]
        stars = repo.get("stargazers_count", 0)
        license_info = (repo.get("license") or {}).get("spdx_id", "unknown")

        if already_have_source(url):
            print(f"\n⏩ [Saltar] {full_name} — ya se encuentra en el Vault")
            continue

        print(f"\n📦 [Descargar] {full_name} (⭐ {stars} | Licencia: {license_info})")
        try:
            owner, name = full_name.split("/")
            readme = list_repo_readme(owner, name)
        except Exception as e:
            print(f"  ❌ Error al obtener README: {e}")
            continue

        print("  🧠 [Destilar] Extrayendo patrones y decisiones de diseño...")
        try:
            summary = distill(readme, topic=topic, source_repo=full_name)
        except Exception as e:
            print(f"  ❌ Error en destilación: {e}")
            continue

        tags = [topic]
        if language:
            tags.append(language)

        note = save_note(
            summary=summary,
            source_repo=full_name,
            source_url=url,
            tags=tags,
            license=license_info,
        )
        if note:
            print(f"  💾 [Guardado] Nota generada en ~/.hermes-hub/patterns/ -> ID: {note['id']}")
            learned.append(note)
        else:
            print("  ⚠️ [Duplicado] Patrón idéntico omitido.")

        time.sleep(sleep_between)

    print(f"\n==================================================")
    print(f"✨ Ciclo completado: {len(learned)} nuevo(s) patrón(es) integrado(s) a Hermes Hub")
    print(f"==================================================")
    for note in learned:
        print(f"\n• [{note['source_repo']}] ({note['id']})\n  {note['summary']}")
    return learned


def main():
    parser = argparse.ArgumentParser(description="Hermes Repo Research & Knowledge Ingestion Loop")
    parser.add_argument("topic", nargs="?", help="Tema o arquitectura a investigar (ej. 'rate limiting patterns')")
    parser.add_argument("--language", default=None, help="Filtrar por lenguaje (ej. python, typescript, rust)")
    parser.add_argument("--n", type=int, default=3, help="Cantidad máxima de repositorios a analizar por ciclo")
    parser.add_argument("--query-memory", metavar="KEYWORD", help="Consultar memoria existente sin realizar nuevas llamadas")
    args = parser.parse_args()

    if args.query_memory:
        results = query_notes(args.query_memory)
        print(f"\n🔍 Resultados en Memoria Hermes para '{args.query_memory}' ({len(results)} encontrado(s)):\n")
        for n in results:
            print(f"[{n['id']}] {n['source_repo']} (Licencia: {n.get('license', 'unknown')})")
            print(f"Tags: {', '.join(n.get('tags', []))}")
            print(f"{n['summary']}\n")
        return

    if not args.topic:
        parser.error("Se requiere especificar el tema o usar --query-memory <palabra_clave>")

    run_cycle(args.topic, language=args.language, n=args.n)


if __name__ == "__main__":
    main()
