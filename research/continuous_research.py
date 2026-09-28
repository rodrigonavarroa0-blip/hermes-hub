#!/usr/bin/env python3
"""
continuous_research.py — Motor de Ingesta Masiva y Continua de Conocimiento para Hermes Hub.
Utiliza consultas de alta densidad (high-yield keywords), fallback automático de términos,
y análisis profundo de hasta n=6 repositorios líderes por tecnología.
"""
import os
import sys
import time
import random

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

# Ensure local imports work cleanly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loop import run_cycle

# Matriz de Alta Densidad: Categoría -> Lista de Keywords precisas que garantizan resultados
HIGH_YIELD_TOPICS = [
    # 🧠 IA Agéntica & Sistemas Multi-Agente
    ("model context protocol", "python"),
    ("agent memory", "python"),
    ("multi agent", "python"),
    ("agent orchestration", "python"),
    ("autonomous agent sandbox", "python"),
    ("langgraph agent", "python"),
    ("crewai tools", "python"),
    ("autogen multiagent", "python"),
    ("pydantic ai", "python"),
    ("agentic rag", "python"),

    # ⚡ Backend, Concurrencia & Bases de Datos
    ("fastapi background tasks", "python"),
    ("redis rate limiter", "python"),
    ("distributed lock redis", "python"),
    ("sqlite vector search", "python"),
    ("qdrant vector db", "python"),
    ("celery task queue", "python"),
    ("temporal workflow", "python"),
    ("websocket async server", "python"),
    ("duckdb local analytics", "python"),
    ("pgvector postgres", "python"),

    # 🌐 Frontend Moderno, Next.js & UI
    ("nextjs server actions", "typescript"),
    ("react server components", "typescript"),
    ("xstate state machine", "typescript"),
    ("trpc fullstack", "typescript"),
    ("drizzle orm", "typescript"),
    ("tailwind design system", "typescript"),
    ("shadcn ui components", "typescript"),
    ("tanstack query", "typescript"),
    ("zustand state management", "typescript"),
    ("vite plugin optimization", "typescript"),

    # 🔒 DevOps, Sandboxing & Herramientas de Código
    ("docker sandbox isolation", "python"),
    ("tree sitter code parser", "python"),
    ("ast linting security", "javascript"),
    ("caddy reverse proxy", "go"),
    ("github actions ci template", None),

    # 🤖 Optimización de Modelos & Token Budgeting
    ("prompt compression", "python"),
    ("structured output llm", "python"),
    ("semantic cache", "python"),
    ("knowledge graph rag", "python"),
    ("vllm serving", "python"),
    ("ollama local llm", "python"),
    ("instructor pydantic", "python"),
    ("outlines structured text", "python"),
    ("hebbian learning memory", "python"),
    ("llmlingua prompt compression", "python"),
]


def start_massive_research_loop(n_per_topic=5, sleep_between_repos=1.0, sleep_between_topics=5.0):
    print("=" * 70)
    print("🚀 INICIANDO MOTOR DE INGESTA MASIVA DE CONOCIMIENTO PARA HERMES")
    print(f"📚 Total de Temas de Alta Densidad: {len(HIGH_YIELD_TOPICS)}")
    print(f"🎯 Repositorios analizados por tema: hasta {n_per_topic}")
    print(f"📂 Destino: ~/.hermes-hub/patterns/ & memory/notes.jsonl")
    print("=" * 70)

    round_count = 0
    while True:
        round_count += 1
        print(f"\n🌟 ==================== RONDA GLOBAL #{round_count} ====================")
        
        # Barajar aleatoriamente en cada ronda para variar las áreas de investigación
        topics_shuffled = list(HIGH_YIELD_TOPICS)
        random.shuffle(topics_shuffled)

        for idx, (topic, lang) in enumerate(topics_shuffled, 1):
            print(f"\n🔍 [{idx}/{len(topics_shuffled)}] Investigando: '{topic}' (Lenguaje: {lang or 'Todos'})")
            try:
                run_cycle(topic=topic, language=lang, n=n_per_topic, sleep_between=sleep_between_repos)
            except Exception as e:
                print(f"⚠️ Error en ciclo '{topic}': {e}")

            time.sleep(sleep_between_topics)


if __name__ == "__main__":
    start_massive_research_loop(n_per_topic=5)
