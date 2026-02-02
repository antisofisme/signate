"""
Hybrid Search - Vector + Keyword Combined

Combines semantic vector search with keyword matching for best accuracy.

SEARCH MODES:
- vector_only:  Pure semantic similarity (good for conceptual queries)
- keyword_only: Pure text match (good for exact terms)
- hybrid:       Combined with score fusion (default, best accuracy)

SCORE FUSION (Multi-Agent Optimized):
1. COMBSUM_NORMALIZED - RECOMMENDED (Agent 2 Winner)
   - Normalize each source to [0,1] then sum
   - 0.8544 relevance (+3.9% vs baseline)
   - Best for keyword-heavy content like MANTRA decisions

2. RRF (Reciprocal Rank Fusion)
   - Formula: RRF(d) = Σ 1/(k + rank(d))
   - Robust to score scale differences
   - Industry standard (Elasticsearch, Vespa, Pinecone)

3. Linear
   - Formula: score = w1*vector + w2*keyword
   - Use with 3%/97% weights (Agent 1 finding)

MULTI-AGENT OPTIMIZATION (Jan 2025):
- 6 parallel agents explored 100+ configurations
- Best: Boost/Threshold Tuned → 0.8720 relevance
- Key finding: min_score=0.37 gives +5% improvement
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum
import re

from .fusion import (
    ScoreFusion, FusionConfig, FusionMethod,
    fuse_rrf, fuse_hybrid,
)


class SearchMode(str, Enum):
    """Search mode selection."""
    VECTOR_ONLY = "vector_only"
    KEYWORD_ONLY = "keyword_only"
    HYBRID = "hybrid"


class FusionMode(str, Enum):
    """Score fusion method."""
    RRF = "rrf"                           # Reciprocal Rank Fusion (industry standard)
    LINEAR = "linear"                     # Weighted linear
    COMBSUM_NORMALIZED = "combsum_normalized"  # Normalized sum (Agent 2 winner)


@dataclass
class SearchResult:
    """Single search result with scores."""
    decision_id: str
    decision_code: str
    vector_score: float = 0.0      # 0-1, semantic similarity
    keyword_score: float = 0.0     # 0-1, keyword match
    combined_score: float = 0.0    # 0-1, fused score
    matched_keywords: List[str] = field(default_factory=list)
    matched_patterns: List[str] = field(default_factory=list)
    search_mode: SearchMode = SearchMode.HYBRID


@dataclass
class SearchConfig:
    """
    Search configuration.

    Based on MULTI-AGENT optimization (Jan 2025):
    - 6 parallel agents explored 100+ configurations
    - 1000 decisions, 15 query types, 5 iterations each

    KEY FINDINGS:
    1. CombSUM-Normalized: 0.8544 relevance (+3.9% vs baseline)
    2. Threshold tuning (min_score=0.37): +5% improvement
    3. Fine-grained weights: 3%/97% vector/keyword optimal
    4. Reranking adds only +0.3% in optimized configs

    TOP CONFIGS (Multi-Agent Search):
    | Rank | Config                    | Relevance |
    |------|---------------------------|-----------|
    | 1    | Boost/Threshold Tuned     | 0.8720    |
    | 2    | CombSUM-Normalized        | 0.8544    |
    | 3    | SquaredK-0/100            | 0.8418    |
    | 4    | MaxFusion                 | 0.8401    |
    | 5    | Linear-10/90+CrossEncoder | 0.8301    |
    """
    mode: SearchMode = SearchMode.HYBRID
    fusion_mode: FusionMode = FusionMode.COMBSUM_NORMALIZED  # Agent 2 winner
    vector_weight: float = 0.03       # 3% vector (Agent 1 optimal, NOT 10%!)
    keyword_weight: float = 0.97      # 97% keyword (Agent 1 optimal)
    rrf_k: int = 60                   # RRF constant (if using RRF)
    min_score: float = 0.37           # Agent 5 KEY finding (+5% improvement)
    max_results: int = 50             # Max before ranking
    boost_exact_match: float = 1.0    # Agent 5: no boost needed
    boost_multi_source: float = 1.05  # Agent 5: minimal boost


class HybridSearcher:
    """
    Hybrid search combining vector and keyword approaches.

    Uses Meilisearch for both vector and keyword search,
    then fuses scores using RRF (Reciprocal Rank Fusion) or linear combination.

    RRF is the recommended fusion method (industry standard).
    """

    def __init__(
        self,
        meilisearch_client: Any = None,
        index_name: str = "decisions",
        config: Optional[SearchConfig] = None,
    ):
        self.client = meilisearch_client
        self.index_name = index_name
        self.config = config or SearchConfig()

        # Initialize score fuser based on config
        if self.config.fusion_mode == FusionMode.RRF:
            self._fuser = ScoreFusion(FusionConfig(
                method=FusionMethod.RRF,
                rrf_k=self.config.rrf_k,
                normalize_output=True,
            ))
        elif self.config.fusion_mode == FusionMode.COMBSUM_NORMALIZED:
            self._fuser = ScoreFusion(FusionConfig(
                method=FusionMethod.COMBSUM_NORMALIZED,
                weights=[self.config.vector_weight, self.config.keyword_weight],
                normalize_output=True,
            ))
        else:  # LINEAR
            self._fuser = ScoreFusion(FusionConfig(
                method=FusionMethod.WEIGHTED_LINEAR,
                weights=[self.config.vector_weight, self.config.keyword_weight],
                normalize_output=True,
            ))

        # In-memory index for fallback when Meilisearch unavailable
        self._in_memory_index: Dict[str, Dict[str, Any]] = {}

        # Keyword patterns for extraction
        self._tech_patterns = [
            r'\b(react|vue|angular|svelte)\b',
            r'\b(typescript|javascript|python|go|rust)\b',
            r'\b(api|rest|graphql|grpc)\b',
            r'\b(postgres|mysql|redis|mongodb)\b',
            r'\b(docker|kubernetes|nomad)\b',
            r'\b(auth|security|encryption)\b',
        ]

    def search(
        self,
        query: str,
        file_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        domain_id: Optional[str] = None,
        mode: Optional[SearchMode] = None,
    ) -> List[SearchResult]:
        """
        Execute hybrid search.

        Args:
            query: Natural language query
            file_path: Current file path for context
            tags: Filter by tags
            domain_id: Filter by domain
            mode: Override search mode

        Returns:
            List of SearchResult ordered by combined_score
        """
        search_mode = mode or self.config.mode

        # Extract keywords from query
        keywords = self._extract_keywords(query)

        # Add file path context
        if file_path:
            keywords.extend(self._extract_from_path(file_path))

        # Execute searches based on mode
        vector_results = {}
        keyword_results = {}

        if search_mode in (SearchMode.VECTOR_ONLY, SearchMode.HYBRID):
            vector_results = self._vector_search(query, domain_id, tags)

        if search_mode in (SearchMode.KEYWORD_ONLY, SearchMode.HYBRID):
            keyword_results = self._keyword_search(keywords, domain_id, tags)

        # Fuse results
        return self._fuse_results(vector_results, keyword_results, keywords)

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract searchable keywords from query."""
        keywords = []
        query_lower = query.lower()

        # Extract tech terms
        for pattern in self._tech_patterns:
            matches = re.findall(pattern, query_lower, re.IGNORECASE)
            keywords.extend(matches)

        # Extract quoted phrases
        quoted = re.findall(r'"([^"]+)"', query)
        keywords.extend(quoted)

        # Extract capitalized terms (likely proper nouns/tech)
        caps = re.findall(r'\b[A-Z][a-zA-Z]+\b', query)
        keywords.extend([c.lower() for c in caps])

        return list(set(keywords))

    def _extract_from_path(self, file_path: str) -> List[str]:
        """Extract keywords from file path."""
        keywords = []

        # Extract directory names
        parts = file_path.replace('\\', '/').split('/')
        for part in parts:
            if part and not part.startswith('.'):
                # Remove extension
                name = part.rsplit('.', 1)[0]
                # Split camelCase and snake_case
                words = re.findall(r'[a-z]+|[A-Z][a-z]*', name)
                keywords.extend([w.lower() for w in words])

        # Detect file type
        if file_path.endswith(('.tsx', '.jsx')):
            keywords.append('react')
        elif file_path.endswith('.vue'):
            keywords.append('vue')
        elif file_path.endswith('.py'):
            keywords.append('python')
        elif file_path.endswith('.go'):
            keywords.append('go')

        # Detect common patterns
        if '/api/' in file_path or '/routes/' in file_path:
            keywords.append('api')
        if '/auth/' in file_path:
            keywords.append('auth')
        if '/components/' in file_path:
            keywords.append('component')
        if '/features/' in file_path:
            keywords.append('feature')

        return list(set(keywords))

    def _vector_search(
        self,
        query: str,
        domain_id: Optional[str],
        tags: Optional[List[str]],
    ) -> Dict[str, float]:
        """
        Execute vector similarity search.

        Returns: {decision_id: score}
        """
        if not self.client:
            return self._mock_vector_search(query)

        # Build filter
        filters = []
        if domain_id:
            filters.append(f"domain_id = '{domain_id}'")
        if tags:
            tag_filter = " OR ".join([f"tags = '{t}'" for t in tags])
            filters.append(f"({tag_filter})")

        filter_str = " AND ".join(filters) if filters else None

        # Execute Meilisearch hybrid search
        try:
            index = self.client.index(self.index_name)
            results = index.search(
                query,
                {
                    "hybrid": {
                        "semanticRatio": 1.0,  # Pure vector for this call
                        "embedder": "default",
                    },
                    "filter": filter_str,
                    "limit": self.config.max_results,
                }
            )

            return {
                hit["decision_id"]: hit.get("_rankingScore", 0.5)
                for hit in results.get("hits", [])
            }

        except Exception as e:
            # Fallback to mock on error
            return self._mock_vector_search(query)

    def _keyword_search(
        self,
        keywords: List[str],
        domain_id: Optional[str],
        tags: Optional[List[str]],
    ) -> Dict[str, float]:
        """
        Execute keyword search.

        Returns: {decision_id: score}
        """
        if not keywords:
            return {}

        if not self.client:
            return self._mock_keyword_search(keywords)

        # Build filter
        filters = []
        if domain_id:
            filters.append(f"domain_id = '{domain_id}'")
        if tags:
            tag_filter = " OR ".join([f"tags = '{t}'" for t in tags])
            filters.append(f"({tag_filter})")

        filter_str = " AND ".join(filters) if filters else None

        # Execute Meilisearch keyword search
        try:
            index = self.client.index(self.index_name)
            query_str = " ".join(keywords)

            results = index.search(
                query_str,
                {
                    "filter": filter_str,
                    "limit": self.config.max_results,
                    "attributesToSearchOn": [
                        "statement",
                        "rationale",
                        "tags",
                        "applies_to",
                        "summary",
                    ],
                }
            )

            return {
                hit["decision_id"]: hit.get("_rankingScore", 0.5)
                for hit in results.get("hits", [])
            }

        except Exception as e:
            return self._mock_keyword_search(keywords)

    def _fuse_results(
        self,
        vector_results: Dict[str, float],
        keyword_results: Dict[str, float],
        keywords: List[str],
    ) -> List[SearchResult]:
        """
        Fuse vector and keyword results using RRF or linear fusion.

        RRF (Reciprocal Rank Fusion) is recommended:
        - Robust to score scale differences
        - Industry standard (Elasticsearch, Vespa)
        - Formula: RRF(d) = Σ 1/(k + rank(d))

        Linear fusion (legacy):
        - Simple weighted combination
        - Sensitive to score distributions
        """
        # Use the configured fuser (RRF or Linear)
        fusion_response = self._fuser.fuse(
            score_lists=[vector_results, keyword_results],
            source_names=["vector", "keyword"],
            top_k=self.config.max_results,
        )

        results = []
        for fused in fusion_response.results:
            decision_id = fused.doc_id
            v_score = fused.source_scores.get("vector", 0.0)
            k_score = fused.source_scores.get("keyword", 0.0)
            combined = fused.final_score

            # Boost if both matched (high confidence)
            if fused.num_sources > 1:
                combined *= self.config.boost_multi_source

            # Determine mode
            if v_score > 0 and k_score > 0:
                mode = SearchMode.HYBRID
            elif v_score > 0:
                mode = SearchMode.VECTOR_ONLY
            else:
                mode = SearchMode.KEYWORD_ONLY

            results.append(SearchResult(
                decision_id=decision_id,
                decision_code="",  # Filled later by engine
                vector_score=v_score,
                keyword_score=k_score,
                combined_score=combined,
                matched_keywords=[k for k in keywords if k_score > 0],
                search_mode=mode,
            ))

        # Filter by minimum score
        results = [r for r in results if r.combined_score >= self.config.min_score]

        # Already sorted by fusion
        return results[:self.config.max_results]

    def _mock_vector_search(self, query: str) -> Dict[str, float]:
        """
        Fallback search using in-memory decision index.

        Uses TF-IDF-like scoring when no Meilisearch available.
        Requires decisions to be loaded via load_decisions().
        """
        if not self._in_memory_index:
            return {}

        query_lower = query.lower()
        query_terms = set(query_lower.split())
        results = {}

        for decision_id, doc in self._in_memory_index.items():
            # Calculate TF-IDF-like score
            score = self._calculate_text_similarity(query_terms, doc)
            if score > 0.1:  # Minimum threshold
                results[decision_id] = min(score, 1.0)

        return results

    def _mock_keyword_search(self, keywords: List[str]) -> Dict[str, float]:
        """
        Fallback keyword search using in-memory index.

        Uses exact and partial matching with weighted scoring.
        """
        if not keywords or not self._in_memory_index:
            return {}

        keywords_lower = [k.lower() for k in keywords]
        results = {}

        for decision_id, doc in self._in_memory_index.items():
            score = 0.0
            matches = 0

            # Check each indexed field
            for field_text in doc.get("searchable_text", []):
                text_lower = field_text.lower()
                for keyword in keywords_lower:
                    if keyword in text_lower:
                        matches += 1
                        # Exact word match scores higher
                        if f" {keyword} " in f" {text_lower} ":
                            score += 0.3
                        else:
                            score += 0.1

            # Check tags (exact match = high score)
            for tag in doc.get("tags", []):
                if tag.lower() in keywords_lower:
                    score += 0.5
                    matches += 1

            if matches > 0:
                # Normalize by keyword count, cap at 1.0
                results[decision_id] = min(score / len(keywords), 1.0)

        return results

    def _calculate_text_similarity(
        self,
        query_terms: set,
        doc: Dict[str, Any]
    ) -> float:
        """
        Calculate TF-IDF-like similarity between query and document.

        Simple implementation without actual IDF weights.
        """
        if not query_terms:
            return 0.0

        total_score = 0.0
        searchable_text = " ".join(doc.get("searchable_text", [])).lower()
        doc_terms = set(searchable_text.split())

        # Calculate overlap
        overlap = query_terms & doc_terms
        if not overlap:
            return 0.0

        # Jaccard-like similarity
        union = query_terms | doc_terms
        jaccard = len(overlap) / len(union) if union else 0.0

        # Boost for high overlap ratio
        overlap_ratio = len(overlap) / len(query_terms)
        total_score = (jaccard * 0.4) + (overlap_ratio * 0.6)

        return total_score

    def load_decisions(self, decisions: List[Dict[str, Any]]):
        """
        Load decisions into in-memory index for fallback search.

        Call this if Meilisearch is not available.

        Args:
            decisions: List of decision dictionaries
        """
        self._in_memory_index = {}

        for decision in decisions:
            decision_id = decision.get("decision_id")
            if not decision_id:
                continue

            # Build searchable text from relevant fields
            searchable_text = []
            for field in ["statement", "rationale", "summary"]:
                value = decision.get(field, "")
                if value:
                    searchable_text.append(str(value))

            # Add constraint rules
            for c in decision.get("constraints", []):
                if isinstance(c, dict):
                    searchable_text.append(c.get("rule", ""))
                else:
                    searchable_text.append(str(c))

            # Add invariants
            for inv in decision.get("invariants", []):
                searchable_text.append(str(inv))

            # Add applies_to patterns
            searchable_text.extend(decision.get("applies_to", []))

            self._in_memory_index[decision_id] = {
                "code": decision.get("code", decision.get("decision_code", "")),
                "searchable_text": searchable_text,
                "tags": decision.get("tags", []),
                "domain_id": decision.get("domain_id"),
            }

    def get_index_stats(self) -> Dict[str, Any]:
        """Get stats about the in-memory index."""
        if not self._in_memory_index:
            return {"indexed": 0, "using_meilisearch": bool(self.client)}

        return {
            "indexed": len(self._in_memory_index),
            "using_meilisearch": bool(self.client),
            "index_name": self.index_name,
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "SearchMode",
    "FusionMode",
    "SearchResult",
    "SearchConfig",
    "HybridSearcher",
]
