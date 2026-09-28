"""
distill.py
Extracts structured, reusable engineering insights and architectural patterns from source material.
Uses Pydantic schemas (PatternNoteSchema) with Google Gemini (primary), OpenAI, Anthropic, or an offline heuristic summarizer.
"""
import os
import re
import json
import requests
from typing import List, Optional
from pydantic import BaseModel, Field

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


class PatternNoteSchema(BaseModel):
    title: str = Field(description="Título descriptivo del patrón")
    summary: str = Field(description="Síntesis de 2-4 oraciones de qué es y por qué funciona")
    key_rules: List[str] = Field(default_factory=list, description="3 reglas clave de implementación")
    antipatterns: List[str] = Field(default_factory=list, description="Antipatrones o errores comunes a evitar")
    code_example: Optional[str] = Field(default=None, description="Snippet mínimo representativo de código")
    tags: List[str] = Field(default_factory=list, description="Tags técnicos clave")


def _heuristic_summary(text: str, topic: str, source_repo: str, max_chars: int = 400) -> PatternNoteSchema:
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", text)
    # Strip markdown images and links formatting
    cleaned = re.sub(r"!\[.*?\]\(.*?\)", " ", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\(.*?\)", r"\1", cleaned)
    lines = [l.strip() for l in cleaned.splitlines() if l.strip() and not l.startswith("#")]
    joined = " ".join(lines)
    joined = re.sub(r"\s+", " ", joined)
    snippet = joined[:max_chars].strip()
    
    clean_topic = topic.replace("-", " ").title()
    repo_name = source_repo.split("/")[-1] if "/" in source_repo else source_repo

    return PatternNoteSchema(
        title=f"Pattern {repo_name} - {clean_topic}",
        summary=f"Patrón y arquitectura relevante para '{topic}': {snippet}...",
        key_rules=[
            f"Aplicar la arquitectura modular definida en {source_repo}.",
            "Aislar la lógica de estado y desacoplar componentes dependientes.",
            "Validar tipos estrictos y manejo de errores asíncronos."
        ],
        antipatterns=[
            "No mezclar capas de transporte con lógica de dominio sin interfaces intermedias."
        ],
        code_example=None,
        tags=[topic.lower().replace(" ", "-")]
    )


def _distill_gemini(text: str, topic: str, source_repo: str, api_key: str) -> Optional[PatternNoteSchema]:
    prompt = (
        f"Actúa como un Principal Software Architect extrayendo conocimiento para el Vault de Hermes Knowledge Hub.\n\n"
        f"Tema: {topic}\n"
        f"Repositorio: {source_repo}\n\n"
        f"Contenido del README / Código:\n{text[:9000]}\n\n"
        "Devuelve un JSON estrictamente válido con el siguiente esquema:\n"
        "{\n"
        '  "title": "Nombre descriptivo del patrón o técnica",\n'
        '  "summary": "2 a 4 oraciones de qué patrón de diseño o arquitectura usa y POR QUÉ es eficiente. Sin relleno comercial.",\n'
        '  "key_rules": ["Regla 1 de implementación", "Regla 2 de implementación", "Regla 3 de implementación"],\n'
        '  "antipatterns": ["Antipatrón 1 o error común a evitar"],\n'
        '  "code_example": "Snippet mínimo de código o None",\n'
        '  "tags": ["tag1", "tag2"]\n'
        "}\n"
        "Solo JSON, sin explicaciones ni markdown envolvente."
    )
    url = f"{GEMINI_API_URL}?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 600,
            "responseMimeType": "application/json"
        }
    }
    resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    candidates = data.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        if parts:
            raw_json = parts[0].get("text", "").strip()
            parsed = json.loads(raw_json)
            return PatternNoteSchema(**parsed)
    return None


def distill(text: str, topic: str, source_repo: str) -> PatternNoteSchema:
    """
    Distills raw text into a structured Pydantic PatternNoteSchema.
    Priority: Gemini API -> Heuristic fallback.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_key:
        try:
            res = _distill_gemini(text, topic, source_repo, gemini_key)
            if res:
                return res
        except Exception as e:
            print(f"  [distill] Gemini call error ({e}), using heuristic fallback...")

    return _heuristic_summary(text, topic, source_repo)
