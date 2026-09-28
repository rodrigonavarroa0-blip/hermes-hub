"""
query_expander.py — Expansor Adaptativo de Consultas y Generador HyDE Ligero de Hermes Hub.
Detecta consultas cortas o abstractas y las expande con terminología técnica canónica y patrones hipotéticos
sin sobrecoste de latencia en consultas que ya son específicas.
"""
import re
from typing import List, Dict, Set, Optional, Tuple

# Base de conocimiento de afinidades técnicas y expansiones canónicas de alta precisión
TECHNICAL_EXPANSIONS: Dict[str, List[str]] = {
    "auth": ["oauth2", "jwt", "pkce", "session", "rbac", "token refresh", "stateless auth"],
    "autenticacion": ["oauth2", "jwt", "pkce", "session", "rbac", "token refresh", "stateless auth"],
    "seguridad": ["cors", "csrf", "rate limit", "sanitization", "xss", "security headers", "least privilege"],
    "cache": ["redis", "lru", "ttl", "stale-while-revalidate", "cache invalidation", "distributed cache"],
    "cola": ["rabbitmq", "celery", "kafka", "event loop", "pubsub", "dlq", "dead letter queue"],
    "eventos": ["event-driven", "kafka", "redis pubsub", "outbox pattern", "cqrs", "event sourcing"],
    "concurrencia": ["race condition", "mutex", "distributed lock", "redlock", "asyncio", "optimistic locking"],
    "db": ["connection pool", "indexes", "migrations", "alembic", "prisma", "acid", "query optimization"],
    "base de datos": ["connection pool", "indexes", "migrations", "alembic", "prisma", "acid", "query optimization"],
    "api": ["rest", "graphql", "grpc", "fastapi", "openapi", "versioning", "pagination", "rate limiting"],
    "antipatron": ["anti-pattern", "code smell", "blocking io", "n+1 query", "memory leak", "tight coupling"],
    "arquitectura": ["clean architecture", "hexagonal", "domain driven design", "solid", "modular monolith"],
    "frontend": ["react", "next.js", "state management", "server components", "hydration", "bundle size"],
    "despliegue": ["docker", "kubernetes", "ci/cd", "health check", "graceful shutdown", "multi-stage build"]
}


class AdaptiveQueryExpander:
    """
    Expansor de consultas inteligente que opera en modo dual:
    1. Direct Pass-Through: Si la consulta es específica (>= 6 palabras técnicas), costo 0.05ms.
    2. Adaptive Expansion / HyDE: Si la consulta es corta o ambigua, expande con sinónimos y conceptos canónicos.
    """

    def __init__(self, min_words_threshold: int = 5):
        self.min_words_threshold = min_words_threshold

    def is_abstract_query(self, query: str) -> bool:
        """Determina si una consulta se beneficiaría de expansión adaptativa."""
        words = re.findall(r'\w+', query.lower())
        if len(words) <= self.min_words_threshold:
            return True
        # Si contiene términos abstractos como 'como mejorar', 'buenas practicas', etc.
        abstract_markers = ["mejorar", "buenas practicas", "arquitectura", "problema", "optimo", "seguro", "rapido"]
        return any(m in query.lower() for m in abstract_markers)

    def expand_query(self, query: str) -> Tuple[str, List[str]]:
        """
        Retorna la consulta enriquecida y la lista de términos técnicos añadidos.
        """
        words = set(re.findall(r'\w+', query.lower()))
        added_terms: Set[str] = set()

        for key, expansions in TECHNICAL_EXPANSIONS.items():
            if key in words or any(key in w for w in words):
                # Añadir hasta 4 términos más relevantes
                for exp in expansions[:4]:
                    if exp not in query.lower():
                        added_terms.add(exp)

        if not added_terms:
            return query, []

        expansion_str = " ".join(list(added_terms)[:6])
        enriched_query = f"{query} ({expansion_str})"
        return enriched_query, list(added_terms)

    def generate_hypothetical_snippet(self, query: str) -> str:
        """
        Genera un documento sintético hipotético (HyDE Ligero) para guiar la búsqueda vectorial.
        """
        enriched, terms = self.expand_query(query)
        return f"Patrón de arquitectura y mejores prácticas para {query}. Implementa {', '.join(terms)}. Previene antipatrones y optimiza rendimiento."


# Singleton
_QUERY_EXPANDER: Optional[AdaptiveQueryExpander] = None


def get_query_expander() -> AdaptiveQueryExpander:
    global _QUERY_EXPANDER
    if _QUERY_EXPANDER is None:
        _QUERY_EXPANDER = AdaptiveQueryExpander()
    return _QUERY_EXPANDER


if __name__ == "__main__":
    expander = get_query_expander()
    q1 = "auth seguro en api"
    enriched, terms = expander.expand_query(q1)
    print(f"Query original: '{q1}'")
    print(f"Enriquecida: '{enriched}'")
    print(f"HyDE snippet: {expander.generate_hypothetical_snippet(q1)}")
