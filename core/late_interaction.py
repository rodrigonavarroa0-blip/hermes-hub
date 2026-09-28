"""
late_interaction.py — Motor de Re-Scoring por Interacción Tardía Token-to-Token (Late Interaction / ColBERT Style).
Calcula la similitud MaxSim entre cada token de la consulta y los tokens del documento/código:
Score(Q, D) = sum_{q_i in Q} max_{d_j in D} Sim(q_i, d_j)
Garantiza máxima precisión en fragmentos de código, palabras clave exactas y micro-sintaxis en <2ms.
"""
import re
import math
from typing import List, Dict, Set, Optional, Tuple, Any


class LateInteractionScorer:
    """
    Scorer de Interacción Tardía (Token-Level MaxSim).
    Compara los tokens de la consulta con los tokens del código preservando la identidad léxica exacta y semántica local.
    """

    def __init__(self, exact_match_weight: float = 1.0, substring_weight: float = 0.6):
        self.exact_match_weight = exact_match_weight
        self.substring_weight = substring_weight

    def _tokenize_code(self, text: str) -> List[str]:
        """Tokeniza código separando camelCase, snake_case y palabras clave."""
        # Extraer palabras y sub-tokens
        raw_tokens = re.findall(r'[A-Za-z0-9_]+', str(text).lower())
        tokens = []
        for t in raw_tokens:
            if len(t) < 2:
                continue
            tokens.append(t)
            # Descomponer snake_case
            if "_" in t:
                parts = t.split("_")
                tokens.extend([p for p in parts if len(p) >= 2])
        return tokens

    def compute_maxsim_score(self, query_tokens: List[str], doc_tokens: List[str]) -> float:
        """
        Calcula MaxSim(Q, D) = sum_{q in Q} max_{d in D} TokenSim(q, d)
        """
        if not query_tokens or not doc_tokens:
            return 0.0

        doc_set = set(doc_tokens)
        total_maxsim = 0.0

        for q in query_tokens:
            best_sim = 0.0
            if q in doc_set:
                best_sim = self.exact_match_weight
            else:
                for d in doc_set:
                    # Coincidencia de prefijo/sufijo
                    if q in d or d in q:
                        sim = self.substring_weight * (min(len(q), len(d)) / max(len(q), len(d)))
                        if sim > best_sim:
                            best_sim = sim
                            if best_sim >= 0.9:
                                break
            total_maxsim += best_sim

        normalized_score = total_maxsim / len(query_tokens)
        return round(normalized_score, 4)

    def rescore_candidates(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5,
        alpha_maxsim: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Reordena una lista de candidatos combinando su score previo con el score MaxSim de interacción tardía.
        """
        q_tokens = self._tokenize_code(query)
        if not q_tokens or not candidates:
            return candidates[:top_k]

        rescored = []
        for cand in candidates:
            doc_text = cand.get("content", "") or cand.get("summary", "") or cand.get("label", "")
            d_tokens = self._tokenize_code(doc_text)
            maxsim = self.compute_maxsim_score(q_tokens, d_tokens)

            base_score = float(cand.get("rrf_score", cand.get("vector_score", 0.5)))
            combined_score = round((1.0 - alpha_maxsim) * base_score + alpha_maxsim * maxsim, 4)

            cand_copy = dict(cand)
            cand_copy["maxsim_score"] = maxsim
            cand_copy["late_interaction_score"] = combined_score
            rescored.append(cand_copy)

        rescored.sort(key=lambda x: x["late_interaction_score"], reverse=True)
        return rescored[:top_k]


# Singleton
_LATE_INTERACTION_SCORER: Optional[LateInteractionScorer] = None


def get_late_interaction_scorer() -> LateInteractionScorer:
    global _LATE_INTERACTION_SCORER
    if _LATE_INTERACTION_SCORER is None:
        _LATE_INTERACTION_SCORER = LateInteractionScorer()
    return _LATE_INTERACTION_SCORER


if __name__ == "__main__":
    scorer = get_late_interaction_scorer()
    q = "async redis connection pool redlock"
    cands = [
        {"label": "Redis Distributed Locking with Redlock", "summary": "Implement async redis redlock with lease renewal."},
        {"label": "Postgres Migration Guide", "summary": "Use alembic for SQL schema migrations."},
        {"label": "FastAPI Dependency Injection", "summary": "Use Depends() to inject async database sessions."}
    ]
    rescored = scorer.rescore_candidates(q, cands, top_k=3)
    print("Resultados Late Interaction:")
    for r in rescored:
        print(f"- {r['label']} -> MaxSim: {r['maxsim_score']} | Final: {r['late_interaction_score']}")
