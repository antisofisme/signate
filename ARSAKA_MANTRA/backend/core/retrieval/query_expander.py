"""
Query Expansion - Improve Recall Without Losing Precision

Expands user queries to include:
1. Domain-specific synonyms (INT, ARCH, CTL, EVO)
2. Technical term expansions (database → schema, ERD, PostgreSQL)
3. Taxonomy references (aspect codes)
4. Related concept detection
5. Multilingual support (15 languages)

USAGE:
    expander = QueryExpander()

    # Basic expansion
    expanded = expander.expand("database design")
    # Returns: ["database design", "data model", "schema", "ERD", "PostgreSQL"]

    # With context hints
    expanded = expander.expand(
        "API security",
        context={"domain_id": "CTL", "file_path": "src/api/auth.py"}
    )

    # Multilingual expansion
    expanded = expander.expand("desain basis data")  # Indonesian
    # Returns Indonesian + English terms
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Set
from enum import Enum
import re

# Import multilingual support
try:
    from .multilingual import (
        MultilingualSupport, STOPWORDS, TECH_SYNONYMS as ML_TECH_SYNONYMS,
        CROSS_LANGUAGE_TERMS
    )
    HAS_MULTILINGUAL = True
except ImportError:
    HAS_MULTILINGUAL = False


@dataclass
class ExpansionResult:
    """Result of query expansion."""
    original_query: str
    expanded_terms: List[str]
    domain_hints: List[str]
    technical_expansions: List[str]
    taxonomy_hints: List[str]

    @property
    def all_terms(self) -> List[str]:
        """Get all unique expanded terms including original."""
        terms = [self.original_query]
        terms.extend(self.expanded_terms)
        return list(dict.fromkeys(terms))  # Preserve order, remove duplicates

    def to_search_query(self, boost_original: bool = True) -> str:
        """Convert to search query string."""
        if boost_original:
            # Original query gets higher weight
            parts = [f'"{self.original_query}"^2']
            parts.extend(self.expanded_terms)
            return " ".join(parts)
        return " ".join(self.all_terms)


class QueryExpander:
    """
    Expands queries to improve recall without losing precision.

    Uses domain knowledge and technical synonyms to find related terms
    that should be included in search.
    """

    # MANTRA Domain-specific expansions (4 groups)
    DOMAIN_EXPANSIONS: Dict[str, List[str]] = {
        # Intent group (A01-A04)
        "INT": [
            "intent", "vision", "goals", "objectives", "strategy",
            "purpose", "mission", "north star", "direction", "outcome",
        ],
        # Architecture group (A05-A08)
        "ARCH": [
            "architecture", "structure", "design", "boundaries", "layers",
            "system", "component", "module", "interface", "pattern",
            "separation", "coupling", "cohesion",
        ],
        # Control group (A09-A12)
        "CTL": [
            "control", "policy", "risk", "governance", "compliance",
            "security", "authorization", "audit", "constraint", "rule",
            "permission", "access", "validation",
        ],
        # Evolution group (A13-A16)
        "EVO": [
            "execution", "evolution", "implementation", "deployment",
            "migration", "versioning", "release", "rollout", "change",
            "iteration", "phase", "roadmap",
        ],
    }

    # Aspect code to keywords mapping
    ASPECT_EXPANSIONS: Dict[str, List[str]] = {
        # Intent aspects
        "A01": ["purpose", "vision", "north star", "why"],
        "A02": ["objective", "goal", "outcome", "metric", "KPI"],
        "A03": ["scope", "boundary", "inclusion", "exclusion"],
        "A04": ["stakeholder", "user", "persona", "audience"],
        # Architecture aspects
        "A05": ["layer", "tier", "separation", "abstraction"],
        "A06": ["component", "module", "service", "microservice"],
        "A07": ["interface", "contract", "API", "protocol"],
        "A08": ["pattern", "idiom", "convention", "standard"],
        # Control aspects
        "A09": ["policy", "rule", "constraint", "invariant"],
        "A10": ["security", "auth", "permission", "RBAC", "access"],
        "A11": ["compliance", "audit", "governance", "regulation"],
        "A12": ["risk", "mitigation", "contingency", "fallback"],
        # Evolution aspects
        "A13": ["implementation", "coding", "development", "engineering"],
        "A14": ["deployment", "release", "rollout", "CI/CD"],
        "A15": ["migration", "upgrade", "transition", "backward"],
        "A16": ["maintenance", "support", "monitoring", "observability"],
    }

    # Technical term synonyms
    TECH_SYNONYMS: Dict[str, List[str]] = {
        # Database
        "database": ["db", "data store", "persistence", "PostgreSQL", "schema", "table"],
        "schema": ["data model", "ERD", "table structure", "database design"],
        "migration": ["schema change", "database migration", "alembic", "flyway"],

        # API
        "api": ["endpoint", "REST", "interface", "route", "HTTP", "GraphQL"],
        "endpoint": ["route", "API path", "controller", "handler"],
        "rest": ["RESTful", "HTTP API", "resource", "CRUD"],

        # Auth
        "auth": ["authentication", "authorization", "login", "security", "RBAC"],
        "authentication": ["login", "auth", "identity", "credential", "JWT", "session"],
        "authorization": ["permission", "access control", "RBAC", "ACL", "policy"],
        "rbac": ["role-based", "permission", "access control", "role"],

        # Frontend
        "component": ["UI element", "widget", "React component", "view"],
        "react": ["React.js", "JSX", "TSX", "component", "hook"],
        "hook": ["React hook", "use", "useState", "useEffect", "custom hook"],
        "state": ["state management", "Zustand", "Redux", "context", "store"],
        "form": ["input", "validation", "react-hook-form", "Zod", "schema"],

        # Backend
        "service": ["business logic", "use case", "domain service", "application service"],
        "repository": ["data access", "DAO", "persistence", "query"],
        "controller": ["handler", "endpoint", "route", "API"],
        "middleware": ["interceptor", "filter", "pipe", "guard"],

        # Architecture
        "clean architecture": ["hexagonal", "ports adapters", "onion", "DDD"],
        "microservice": ["micro service", "service", "distributed", "SOA"],
        "monolith": ["monolithic", "single deployment", "modular monolith"],

        # Testing
        "test": ["testing", "unit test", "integration test", "e2e", "spec"],
        "mock": ["stub", "fake", "spy", "test double"],
        "coverage": ["test coverage", "code coverage", "branch coverage"],

        # DevOps
        "deployment": ["deploy", "release", "rollout", "ship"],
        "docker": ["container", "containerization", "image", "Dockerfile"],
        "ci/cd": ["pipeline", "continuous integration", "continuous deployment", "GitHub Actions"],

        # Error handling
        "error": ["exception", "failure", "fault", "error handling"],
        "validation": ["input validation", "schema validation", "constraint", "Zod", "Pydantic"],
        "logging": ["log", "trace", "debug", "monitoring", "observability"],
    }

    # Query pattern to domain hints
    PATTERN_TO_DOMAIN: Dict[str, str] = {
        r"\b(vision|mission|goal|objective|purpose|why)\b": "INT",
        r"\b(architecture|design|structure|layer|component|module)\b": "ARCH",
        r"\b(security|auth|permission|policy|rule|compliance|audit)\b": "CTL",
        r"\b(deploy|implement|migrate|release|version|phase)\b": "EVO",
    }

    # File path patterns to domain hints
    PATH_TO_DOMAIN: Dict[str, str] = {
        r"(docs?|spec|requirements)": "INT",
        r"(src|lib|core|domain)": "ARCH",
        r"(auth|security|policy|rbac)": "CTL",
        r"(deploy|migration|scripts|infra)": "EVO",
    }

    def __init__(
        self,
        max_expansions: int = 10,
        include_synonyms: bool = True,
        include_domain_terms: bool = True,
        include_aspect_terms: bool = True,
        enable_multilingual: bool = True,
    ):
        """
        Initialize QueryExpander.

        Args:
            max_expansions: Maximum number of expanded terms
            include_synonyms: Include technical synonyms
            include_domain_terms: Include domain-specific terms
            include_aspect_terms: Include aspect-based terms
            enable_multilingual: Enable multilingual query expansion
        """
        self.max_expansions = max_expansions
        self.include_synonyms = include_synonyms
        self.include_domain_terms = include_domain_terms
        self.include_aspect_terms = include_aspect_terms
        self.enable_multilingual = enable_multilingual and HAS_MULTILINGUAL

        # Initialize multilingual support if available
        if self.enable_multilingual:
            self._multilingual = MultilingualSupport()
        else:
            self._multilingual = None

    def expand(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExpansionResult:
        """
        Expand query with related terms.

        Args:
            query: Original user query
            context: Optional context with domain_id, file_path, etc.

        Returns:
            ExpansionResult with expanded terms
        """
        context = context or {}
        query_lower = query.lower()

        expanded_terms: Set[str] = set()
        domain_hints: List[str] = []
        technical_expansions: List[str] = []
        taxonomy_hints: List[str] = []

        # Step 0: Detect language and get cross-language terms
        detected_lang = "en"
        if self._multilingual:
            detected_lang = self._multilingual.detect_language(query)
            # Add cross-language expansions for technical terms
            cross_lang_terms = self._expand_cross_language(query_lower, detected_lang)
            expanded_terms.update(cross_lang_terms)

        # Step 1: Detect domain hints from query and context
        domain_hints = self._detect_domain_hints(query_lower, context)

        # Step 2: Add domain-specific terms
        if self.include_domain_terms:
            for domain in domain_hints:
                terms = self.DOMAIN_EXPANSIONS.get(domain, [])
                for term in terms[:3]:  # Top 3 from each domain
                    if term.lower() not in query_lower:
                        expanded_terms.add(term)

        # Step 3: Add technical synonyms (language-aware)
        if self.include_synonyms:
            technical_expansions = self._expand_technical_terms(query_lower, detected_lang)
            expanded_terms.update(technical_expansions)

        # Step 4: Add aspect-based terms
        if self.include_aspect_terms:
            taxonomy_hints = self._detect_aspect_hints(query_lower, context)
            for aspect in taxonomy_hints:
                terms = self.ASPECT_EXPANSIONS.get(aspect, [])
                for term in terms[:2]:  # Top 2 from each aspect
                    if term.lower() not in query_lower:
                        expanded_terms.add(term)

        # Step 5: Extract important keywords (language-aware)
        query_keywords = self._extract_keywords(query_lower, detected_lang)

        # Limit to max expansions
        final_terms = list(expanded_terms)[:self.max_expansions]

        return ExpansionResult(
            original_query=query,
            expanded_terms=final_terms,
            domain_hints=domain_hints,
            technical_expansions=technical_expansions,
            taxonomy_hints=taxonomy_hints,
        )

    def expand_to_queries(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        max_queries: int = 3,
    ) -> List[str]:
        """
        Generate multiple search queries from expansion.

        Useful for parallel search with different query variants.

        Args:
            query: Original query
            context: Optional context
            max_queries: Maximum queries to generate

        Returns:
            List of search query strings
        """
        result = self.expand(query, context)
        queries = [query]  # Original always first

        # Add domain-focused query if domain hints found
        if result.domain_hints:
            domain_terms = []
            for domain in result.domain_hints[:1]:
                domain_terms.extend(self.DOMAIN_EXPANSIONS.get(domain, [])[:2])
            if domain_terms:
                queries.append(f"{query} {' '.join(domain_terms[:3])}")

        # Add technical expansion query
        if result.technical_expansions:
            queries.append(f"{query} {' '.join(result.technical_expansions[:3])}")

        return queries[:max_queries]

    def _detect_domain_hints(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> List[str]:
        """Detect relevant MANTRA domains from query and context."""
        domains: Set[str] = set()

        # Check explicit domain_id in context
        if context.get("domain_id"):
            domains.add(context["domain_id"])

        # Check query patterns
        for pattern, domain in self.PATTERN_TO_DOMAIN.items():
            if re.search(pattern, query, re.IGNORECASE):
                domains.add(domain)

        # Check file path
        file_path = context.get("file_path", "")
        if file_path:
            for pattern, domain in self.PATH_TO_DOMAIN.items():
                if re.search(pattern, file_path, re.IGNORECASE):
                    domains.add(domain)

        return list(domains)

    def _expand_technical_terms(self, query: str, lang: str = "en") -> List[str]:
        """Expand technical terms in query (language-aware)."""
        expansions: Set[str] = set()

        # Use English synonyms as base
        for term, synonyms in self.TECH_SYNONYMS.items():
            if term in query:
                # Add top synonyms
                for syn in synonyms[:3]:
                    if syn.lower() not in query:
                        expansions.add(syn)

        # Add multilingual synonyms if available
        if self._multilingual and lang != "en":
            ml_synonyms = ML_TECH_SYNONYMS.get(lang, {})
            for term, synonyms in ml_synonyms.items():
                if term.lower() in query:
                    for syn in synonyms[:2]:
                        if syn.lower() not in query:
                            expansions.add(syn)
                    # Also add English equivalents
                    eng_term = self._get_english_equivalent(term, lang)
                    if eng_term and eng_term.lower() not in query:
                        expansions.add(eng_term)

        return list(expansions)

    def _expand_cross_language(self, query: str, source_lang: str) -> Set[str]:
        """Expand query terms across languages for better retrieval."""
        expansions: Set[str] = set()

        if not self._multilingual:
            return expansions

        # Find known terms in query and get cross-language equivalents
        for concept, translations in CROSS_LANGUAGE_TERMS.items():
            source_term = translations.get(source_lang, "")
            if source_term and source_term.lower() in query:
                # Add English equivalent if not already English
                if source_lang != "en":
                    eng_term = translations.get("en", "")
                    if eng_term and eng_term.lower() not in query:
                        expansions.add(eng_term)
                # Add common variations
                for lang in ["en", "id"]:  # Common languages in codebase
                    term = translations.get(lang, "")
                    if term and term.lower() not in query:
                        expansions.add(term)

        return expansions

    def _get_english_equivalent(self, term: str, source_lang: str) -> Optional[str]:
        """Get English equivalent of a term."""
        if not self._multilingual:
            return None

        for concept, translations in CROSS_LANGUAGE_TERMS.items():
            source_term = translations.get(source_lang, "")
            if source_term and source_term.lower() == term.lower():
                return translations.get("en")

    def _detect_aspect_hints(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> List[str]:
        """Detect relevant aspect codes."""
        aspects: Set[str] = set()

        # Check explicit aspect_id in context
        if context.get("aspect_id"):
            aspects.add(context["aspect_id"])

        # Check for aspect keywords in query
        for aspect, keywords in self.ASPECT_EXPANSIONS.items():
            for keyword in keywords:
                if keyword.lower() in query:
                    aspects.add(aspect)
                    break

        return list(aspects)

    def _extract_keywords(self, query: str, lang: str = "en") -> List[str]:
        """Extract important keywords from query (language-aware)."""
        # Get language-specific stopwords
        if self._multilingual:
            stop_words = STOPWORDS.get(lang, STOPWORDS.get("en", set()))
        else:
            stop_words = {
                "the", "a", "an", "is", "are", "was", "were", "be", "been",
                "being", "have", "has", "had", "do", "does", "did", "will",
                "would", "could", "should", "may", "might", "must", "shall",
                "can", "need", "dare", "ought", "used", "to", "of", "in",
                "for", "on", "with", "at", "by", "from", "as", "into",
                "through", "during", "before", "after", "above", "below",
                "between", "under", "again", "further", "then", "once",
                "here", "there", "when", "where", "why", "how", "all",
                "each", "few", "more", "most", "other", "some", "such",
                "no", "nor", "not", "only", "own", "same", "so", "than",
                "too", "very", "just", "also", "now", "and", "or", "but",
                "if", "what", "which", "who", "whom", "this", "that",
                "these", "those", "i", "me", "my", "we", "our", "you",
                "your", "he", "him", "his", "she", "her", "it", "its",
                "they", "them", "their", "saya", "aku", "kamu", "dia",
                "kami", "kita", "mereka", "ini", "itu", "yang", "dan",
                "atau", "untuk", "dengan", "dari", "ke", "di", "pada",
            }

        # Tokenize (handle unicode for non-Latin scripts)
        words = re.findall(r'\b\w+\b', query.lower())

        # Filter
        keywords = [w for w in words if w not in stop_words and len(w) > 1]

        return keywords


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "QueryExpander",
    "ExpansionResult",
]
