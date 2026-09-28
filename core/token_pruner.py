"""
token_pruner.py — Poda y Compresión Inteligente de Contexto (Contextual Token Pruning).
Permite ajustar respuestas y notas de conocimiento a un presupuesto estricto de tokens (Dynamic Budgeting),
preservando intactos bloques de código, tablas, decisiones de arquitectura y advertencias críticas.
"""
import re
from typing import List, Dict, Tuple, Optional, Any


class ContextualTokenPruner:
    """
    Compresor de contexto que maximiza la densidad de información por token:
    1. Protege bloques críticos (código, advertencias, tablas, trade-offs).
    2. Poda párrafos descriptivos repetitivos o de baja señal.
    3. Asegura cumplimiento estricto del presupuesto de tokens (Dynamic Budget).
    """

    def __init__(self, chars_per_token: float = 3.8):
        self.chars_per_token = chars_per_token

    def estimate_tokens(self, text: str) -> int:
        """Estima la cantidad de tokens de forma rápida y precisa para LLMs estándar."""
        if not text:
            return 0
        return int(len(text) / self.chars_per_token)

    def prune_markdown(
        self,
        markdown_text: str,
        token_budget: int = 1200,
        keep_code_intact: bool = True
    ) -> str:
        """
        Poda el texto Markdown respetando el token_budget especificado.
        Prioridad de preservación:
        1. Encabezados principales y metadatos.
        2. Alertas y Callouts (> [!WARNING], > [!IMPORTANT], etc.).
        3. Bloques de código (```).
        4. Tablas y viñetas de reglas/decisiones.
        5. Prosa explicativa (se poda o condensa si excede el presupuesto).
        """
        current_tokens = self.estimate_tokens(markdown_text)
        if current_tokens <= token_budget:
            return markdown_text

        # Separar en secciones lógicas
        sections = re.split(r'(?=\n#{1,4}\s)', markdown_text)
        if not sections or len(sections) == 1:
            # Separar por párrafos
            sections = markdown_text.split("\n\n")

        scored_sections: List[Tuple[float, str]] = []

        for sec in sections:
            if not sec.strip():
                continue

            score = 1.0

            # Priorizar código
            if "```" in sec:
                score += 3.0 if keep_code_intact else 1.0

            # Priorizar alertas y warnings
            if any(alert in sec for alert in ["> [!WARNING]", "> [!IMPORTANT]", "> [!CAUTION]", "⚠️", "🚨"]):
                score += 4.0

            # Priorizar listas de reglas, trade-offs o mitigaciones
            if any(kw in sec.lower() for kw in ["mitiga", "trade-off", "regla", "solución", "antipatrón", "requisito", "dependencia"]):
                score += 2.5

            # Priorizar tablas
            if "|" in sec and "-|-" in sec:
                score += 2.0

            # Párrafos meramente descriptivos o de relleno
            if score == 1.0 and len(sec) > 300:
                score = 0.5

            scored_sections.append((score, sec))

        # Ordenar preservando la estructura pero filtrando lo de menor relevancia si nos pasamos
        sorted_by_score = sorted(enumerate(scored_sections), key=lambda x: x[1][0], reverse=True)

        selected_indices = set()
        accumulated_tokens = 0

        for original_idx, (score, sec_content) in sorted_by_score:
            sec_tokens = self.estimate_tokens(sec_content)
            if accumulated_tokens + sec_tokens <= token_budget:
                selected_indices.add(original_idx)
                accumulated_tokens += sec_tokens
            elif score >= 3.0 and accumulated_tokens + int(sec_tokens * 0.5) <= token_budget:
                # Condensar sección crítica si es muy larga
                condensed = self._condense_section(sec_content)
                condensed_tokens = self.estimate_tokens(condensed)
                scored_sections[original_idx] = (score, condensed)
                selected_indices.add(original_idx)
                accumulated_tokens += condensed_tokens
                break

        # Reensamblar en el orden original
        result_sections = [scored_sections[i][1] for i in sorted(selected_indices)]
        pruned_output = "\n\n".join(result_sections).strip()

        # Si aún excede un poco por desajustes, cortar limpiamente
        if self.estimate_tokens(pruned_output) > token_budget:
            char_limit = int(token_budget * self.chars_per_token)
            pruned_output = pruned_output[:char_limit].rsplit("\n", 1)[0] + "\n\n*(...contexto podado para optimizar presupuesto)*"

        return pruned_output

    def _condense_section(self, section: str) -> str:
        """Condensa una sección larga extrayendo viñetas y código."""
        lines = section.splitlines()
        filtered = []
        in_code = False
        for line in lines:
            if line.strip().startswith("```"):
                in_code = not in_code
                filtered.append(line)
                continue
            if in_code:
                filtered.append(line)
                continue
            if line.strip().startswith(("#", "-", "*", ">", "|", "1.", "2.", "3.")):
                filtered.append(line)
            elif len(line.strip()) > 0 and len(filtered) < 8:
                filtered.append(line[:120] + "...")
        return "\n".join(filtered)

    def prune_pattern_list(self, patterns: List[Dict[str, Any]], total_budget: int = 2500) -> List[Dict[str, Any]]:
        """Ajusta una lista de patrones recuperados a un presupuesto global."""
        if not patterns:
            return []

        per_pattern_budget = max(400, total_budget // len(patterns))
        pruned_list = []

        for pat in patterns:
            pat_copy = dict(pat)
            if "content" in pat_copy and pat_copy["content"]:
                pat_copy["content"] = self.prune_markdown(pat_copy["content"], token_budget=per_pattern_budget)
            if "summary" in pat_copy and pat_copy["summary"]:
                pat_copy["summary"] = pat_copy["summary"][:350]
            pruned_list.append(pat_copy)

        return pruned_list


# Singleton
_TOKEN_PRUNER: Optional[ContextualTokenPruner] = None


def get_token_pruner() -> ContextualTokenPruner:
    global _TOKEN_PRUNER
    if _TOKEN_PRUNER is None:
        _TOKEN_PRUNER = ContextualTokenPruner()
    return _TOKEN_PRUNER


if __name__ == "__main__":
    pruner = get_token_pruner()
    sample_md = """# Arquitectura de Microservicios
Esta es una introducción muy larga que contiene explicaciones teóricas extensas sobre el diseño de software.
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

> [!WARNING]
> Nunca uses llamadas HTTP síncronas bloqueantes dentro de handlers asíncronos.

```python
async def handle_event(event):
    await redis_pool.publish("events", event.json())
```

- Regla 1: Usar colas distribuidas.
- Regla 2: Implementar circuit breakers.
"""
    pruned = pruner.prune_markdown(sample_md, token_budget=60)
    print(f"Original tokens: {pruner.estimate_tokens(sample_md)} -> Podado tokens: {pruner.estimate_tokens(pruned)}")
    print(pruned)
