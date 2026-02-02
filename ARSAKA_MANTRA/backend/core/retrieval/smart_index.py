"""
MANTRA Smart Indexing

Hybrid search combining keyword matching and vector embeddings
for semantic similarity search.

SEARCH MODES:
1. KEYWORD - Traditional keyword/TF-IDF matching
2. SEMANTIC - Vector embedding similarity
3. HYBRID - Combined keyword + semantic (weighted)

EMBEDDING PROVIDERS:
- Local: sentence-transformers (offline, fast)
- Remote: OpenAI, Cohere, etc. (API-based)
- Meilisearch: Built-in hybrid search

ARCHITECTURE:
- DecisionIndex: Main index holding all indexed decisions
- SearchResult: Unified result format with scores
- EmbeddingProvider: Interface for embedding generation
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
import math


# ============================================================================
# ENUMS
# ============================================================================

class SearchMode(str, Enum):
    """Search mode for retrieval."""
    KEYWORD = "KEYWORD"     # Traditional keyword search
    SEMANTIC = "SEMANTIC"   # Vector similarity search
    HYBRID = "HYBRID"       # Combined (default)


class EmbeddingModel(str, Enum):
    """Supported embedding models."""
    LOCAL_MINILM = "all-MiniLM-L6-v2"           # 384 dims, fast
    LOCAL_MPNET = "all-mpnet-base-v2"           # 768 dims, better quality
    OPENAI_ADA = "text-embedding-ada-002"       # 1536 dims, API
    OPENAI_3_SMALL = "text-embedding-3-small"   # 1536 dims, API
    MEILISEARCH = "meilisearch"                 # Built-in


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class IndexedDecision:
    """A decision prepared for indexing."""
    decision_id: str
    code: str
    text: str  # Combined searchable text
    embedding: Optional[List[float]] = None
    keywords: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Pre-computed for keyword search
    term_frequencies: Optional[Dict[str, float]] = None


@dataclass
class SearchResult:
    """A single search result with scores."""
    decision_id: str
    code: str

    # Scores (0-1, higher = more relevant)
    keyword_score: float = 0.0
    semantic_score: float = 0.0
    combined_score: float = 0.0

    # What matched
    matched_keywords: List[str] = field(default_factory=list)
    snippet: Optional[str] = None

    # Original data
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchQuery:
    """A search query with options."""
    query: str
    mode: SearchMode = SearchMode.HYBRID
    limit: int = 10
    min_score: float = 0.0

    # Weights for hybrid search
    keyword_weight: float = 0.4
    semantic_weight: float = 0.6

    # Filters
    scope_path: Optional[str] = None
    tags: Optional[List[str]] = None
    domain_id: Optional[str] = None


# ============================================================================
# EMBEDDING PROVIDER INTERFACE
# ============================================================================

class EmbeddingProvider(ABC):
    """Interface for embedding generation."""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding dimension."""
        pass


class DummyEmbeddingProvider(EmbeddingProvider):
    """
    Dummy provider for testing without real embeddings.

    Uses hash-based pseudo-embeddings that are deterministic
    but not semantically meaningful.
    """

    def __init__(self, dimension: int = 384):
        self._dimension = dimension

    def embed(self, text: str) -> List[float]:
        """Generate pseudo-embedding from text hash."""
        import hashlib
        # Create deterministic pseudo-random embedding
        hash_bytes = hashlib.sha256(text.encode()).digest()
        embedding = []
        for i in range(self._dimension):
            # Use hash bytes to generate float values
            byte_idx = i % len(hash_bytes)
            val = (hash_bytes[byte_idx] / 255.0) * 2 - 1  # -1 to 1
            embedding.append(val)
        # Normalize
        norm = math.sqrt(sum(v*v for v in embedding))
        return [v / norm for v in embedding] if norm > 0 else embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]

    @property
    def dimension(self) -> int:
        return self._dimension


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Local embedding using sentence-transformers.

    Requires: pip install sentence-transformers
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._dimension = None

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                # Get dimension from model
                test_emb = self._model.encode(["test"])
                self._dimension = len(test_emb[0])
            except ImportError:
                raise ImportError(
                    "sentence-transformers required. Install with: "
                    "pip install sentence-transformers"
                )

    def embed(self, text: str) -> List[float]:
        self._load_model()
        embedding = self._model.encode([text])[0]
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        self._load_model()
        embeddings = self._model.encode(texts)
        return [e.tolist() for e in embeddings]

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            self._load_model()
        return self._dimension


# ============================================================================
# KEYWORD SEARCH ENGINE
# ============================================================================

class KeywordSearchEngine:
    """
    TF-IDF based keyword search.

    Simple but effective for exact matches.

    OPTIMIZATION: IDF recalculation is now lazy/batched:
    - Single document: Mark IDF as stale, recalc on next search
    - Batch indexing: Recalc once after all documents
    """

    # Stop words to ignore
    STOP_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "must", "shall",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after",
        "and", "but", "or", "nor", "so", "yet", "if", "then",
        "use", "using", "used", "uses", "all", "each", "every"
    }

    def __init__(self):
        self.documents: Dict[str, IndexedDecision] = {}
        self.idf: Dict[str, float] = {}  # Inverse document frequency
        self.doc_count = 0
        self._idf_stale = False  # Track if IDF needs recalculation
        self._pending_terms: set = set()  # Terms added since last IDF update

    def index(self, decision: IndexedDecision) -> None:
        """Index a decision for keyword search."""
        # Extract and normalize terms
        terms = self._tokenize(decision.text)
        term_freq = {}
        for term in terms:
            term_freq[term] = term_freq.get(term, 0) + 1

        # Normalize term frequencies
        max_freq = max(term_freq.values()) if term_freq else 1
        decision.term_frequencies = {
            term: freq / max_freq for term, freq in term_freq.items()
        }
        decision.keywords = list(term_freq.keys())

        self.documents[decision.decision_id] = decision
        self.doc_count = len(self.documents)

        # Mark IDF as stale instead of recalculating immediately
        # This makes indexing O(1) instead of O(n)
        self._idf_stale = True
        self._pending_terms.update(term_freq.keys())

    def index_batch(self, decisions: List[IndexedDecision]) -> None:
        """
        Batch index multiple decisions efficiently.

        IDF is recalculated only once at the end.
        """
        for decision in decisions:
            # Index without IDF update
            terms = self._tokenize(decision.text)
            term_freq = {}
            for term in terms:
                term_freq[term] = term_freq.get(term, 0) + 1

            max_freq = max(term_freq.values()) if term_freq else 1
            decision.term_frequencies = {
                term: freq / max_freq for term, freq in term_freq.items()
            }
            decision.keywords = list(term_freq.keys())
            self.documents[decision.decision_id] = decision

        self.doc_count = len(self.documents)

        # Recalculate IDF once for entire batch
        self._update_idf()
        self._idf_stale = False
        self._pending_terms.clear()

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into terms."""
        text = text.lower()
        # Remove special chars, keep alphanumeric
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        terms = text.split()
        # Filter stop words and short terms
        return [t for t in terms if len(t) > 2 and t not in self.STOP_WORDS]

    def _update_idf(self) -> None:
        """Update IDF values for all terms."""
        term_doc_count: Dict[str, int] = {}

        for doc in self.documents.values():
            for term in (doc.keywords or []):
                term_doc_count[term] = term_doc_count.get(term, 0) + 1

        # Calculate IDF: log(N / df)
        for term, df in term_doc_count.items():
            self.idf[term] = math.log(self.doc_count / df) if df > 0 else 0

    def search(self, query: str, limit: int = 10) -> List[Tuple[str, float, List[str]]]:
        """
        Search using TF-IDF.

        Returns:
            List of (decision_id, score, matched_keywords)
        """
        # Lazy IDF update - only recalculate when actually searching
        if self._idf_stale:
            self._update_idf()
            self._idf_stale = False
            self._pending_terms.clear()

        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        results = []
        for doc_id, doc in self.documents.items():
            if not doc.term_frequencies:
                continue

            score = 0.0
            matched = []

            for term in query_terms:
                if term in doc.term_frequencies:
                    tf = doc.term_frequencies[term]
                    idf = self.idf.get(term, 0)
                    score += tf * idf
                    matched.append(term)

            if score > 0:
                results.append((doc_id, score, matched))

        # Normalize scores to 0-1
        if results:
            max_score = max(r[1] for r in results)
            if max_score > 0:
                results = [(r[0], r[1] / max_score, r[2]) for r in results]

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]


# ============================================================================
# SEMANTIC SEARCH ENGINE
# ============================================================================

class SemanticSearchEngine:
    """
    Vector similarity search using embeddings.
    """

    def __init__(self, embedding_provider: EmbeddingProvider):
        self.provider = embedding_provider
        self.documents: Dict[str, IndexedDecision] = {}

    def index(self, decision: IndexedDecision) -> None:
        """Index a decision with embedding."""
        if decision.embedding is None:
            decision.embedding = self.provider.embed(decision.text)
        self.documents[decision.decision_id] = decision

    def index_batch(self, decisions: List[IndexedDecision]) -> None:
        """Batch index multiple decisions."""
        texts_to_embed = []
        indices_to_embed = []

        for i, dec in enumerate(decisions):
            if dec.embedding is None:
                texts_to_embed.append(dec.text)
                indices_to_embed.append(i)

        if texts_to_embed:
            embeddings = self.provider.embed_batch(texts_to_embed)
            for idx, emb in zip(indices_to_embed, embeddings):
                decisions[idx].embedding = emb

        for dec in decisions:
            self.documents[dec.decision_id] = dec

    def search(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Search using cosine similarity.

        Returns:
            List of (decision_id, similarity_score)
        """
        query_embedding = self.provider.embed(query)
        results = []

        for doc_id, doc in self.documents.items():
            if doc.embedding is None:
                continue

            similarity = self._cosine_similarity(query_embedding, doc.embedding)
            results.append((doc_id, similarity))

        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)


# ============================================================================
# HYBRID SEARCH INDEX
# ============================================================================

class DecisionIndex:
    """
    Main index combining keyword and semantic search.

    This is the primary interface for smart retrieval.
    """

    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
        use_semantic: bool = True
    ):
        """
        Initialize the index.

        Args:
            embedding_provider: Provider for embeddings (uses dummy if None)
            use_semantic: Whether to enable semantic search
        """
        self.use_semantic = use_semantic

        if embedding_provider is None:
            embedding_provider = DummyEmbeddingProvider()

        self.keyword_engine = KeywordSearchEngine()
        self.semantic_engine = SemanticSearchEngine(embedding_provider) if use_semantic else None

        self.documents: Dict[str, IndexedDecision] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def index_decision(
        self,
        decision_id: str,
        code: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> None:
        """
        Index a single decision.

        Args:
            decision_id: Unique identifier
            code: Decision code for display
            text: Searchable text (statement + rationale + constraints, etc.)
            metadata: Additional metadata (scope_path, tags, domain_id, etc.)
            embedding: Pre-computed embedding (optional)
        """
        doc = IndexedDecision(
            decision_id=decision_id,
            code=code,
            text=text,
            embedding=embedding,
            metadata=metadata or {}
        )

        self.documents[decision_id] = doc
        self._metadata[decision_id] = metadata or {}

        # Index in both engines
        self.keyword_engine.index(doc)
        if self.semantic_engine:
            self.semantic_engine.index(doc)

    def index_batch(
        self,
        decisions: List[Dict[str, Any]],
        text_builder: Optional[Callable[[Dict], str]] = None
    ) -> int:
        """
        Batch index multiple decisions.

        Args:
            decisions: List of decision dicts
            text_builder: Function to build searchable text from decision

        Returns:
            Number of decisions indexed
        """
        if text_builder is None:
            text_builder = self._default_text_builder

        docs = []
        for dec in decisions:
            doc = IndexedDecision(
                decision_id=dec.get("decision_id", ""),
                code=dec.get("code", dec.get("decision_code", "")),
                text=text_builder(dec),
                metadata={
                    "scope_path": dec.get("scope_path", "*"),
                    "tags": dec.get("tags", []),
                    "domain_id": dec.get("domain_id", ""),
                    "impact": dec.get("impact", "IMPORTANT"),
                }
            )
            docs.append(doc)
            self.documents[doc.decision_id] = doc
            self._metadata[doc.decision_id] = doc.metadata

        # Batch index
        for doc in docs:
            self.keyword_engine.index(doc)

        if self.semantic_engine:
            self.semantic_engine.index_batch(docs)

        return len(docs)

    def _default_text_builder(self, decision: Dict[str, Any]) -> str:
        """Build searchable text from decision dict."""
        parts = [
            decision.get("statement", ""),
            decision.get("rationale", ""),
            decision.get("summary", ""),
        ]

        # Add constraints
        for c in decision.get("constraints", []):
            if isinstance(c, dict):
                parts.append(c.get("rule", ""))
            else:
                parts.append(str(c))

        # Add tags
        parts.extend(decision.get("tags", []))

        return " ".join(filter(None, parts))

    def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Execute a search query.

        Returns:
            List of SearchResult objects sorted by relevance
        """
        results: Dict[str, SearchResult] = {}

        # Keyword search
        if query.mode in (SearchMode.KEYWORD, SearchMode.HYBRID):
            kw_results = self.keyword_engine.search(query.query, limit=query.limit * 2)
            for doc_id, score, matched in kw_results:
                if doc_id not in results:
                    doc = self.documents.get(doc_id)
                    results[doc_id] = SearchResult(
                        decision_id=doc_id,
                        code=doc.code if doc else "",
                        metadata=self._metadata.get(doc_id, {})
                    )
                results[doc_id].keyword_score = score
                results[doc_id].matched_keywords = matched

        # Semantic search
        if self.semantic_engine and query.mode in (SearchMode.SEMANTIC, SearchMode.HYBRID):
            sem_results = self.semantic_engine.search(query.query, limit=query.limit * 2)
            for doc_id, score in sem_results:
                if doc_id not in results:
                    doc = self.documents.get(doc_id)
                    results[doc_id] = SearchResult(
                        decision_id=doc_id,
                        code=doc.code if doc else "",
                        metadata=self._metadata.get(doc_id, {})
                    )
                results[doc_id].semantic_score = score

        # Calculate combined scores
        for result in results.values():
            if query.mode == SearchMode.KEYWORD:
                result.combined_score = result.keyword_score
            elif query.mode == SearchMode.SEMANTIC:
                result.combined_score = result.semantic_score
            else:  # HYBRID
                result.combined_score = (
                    query.keyword_weight * result.keyword_score +
                    query.semantic_weight * result.semantic_score
                )

        # Apply filters
        filtered_results = list(results.values())

        if query.scope_path:
            filtered_results = [
                r for r in filtered_results
                if self._scope_matches(r.metadata.get("scope_path", "*"), query.scope_path)
            ]

        if query.tags:
            query_tags = set(t.lower() for t in query.tags)
            filtered_results = [
                r for r in filtered_results
                if query_tags & set(t.lower() for t in r.metadata.get("tags", []))
            ]

        if query.domain_id:
            filtered_results = [
                r for r in filtered_results
                if r.metadata.get("domain_id") == query.domain_id
            ]

        # Filter by min_score and sort
        filtered_results = [
            r for r in filtered_results
            if r.combined_score >= query.min_score
        ]
        filtered_results.sort(key=lambda r: r.combined_score, reverse=True)

        return filtered_results[:query.limit]

    def _scope_matches(self, doc_scope: str, query_scope: str) -> bool:
        """Check if document scope matches query scope."""
        if doc_scope == "*" or query_scope == "*":
            return True
        return (
            doc_scope == query_scope or
            doc_scope.startswith(query_scope + ".") or
            query_scope.startswith(doc_scope + ".")
        )

    def simple_search(
        self,
        query: str,
        limit: int = 10,
        mode: SearchMode = SearchMode.HYBRID
    ) -> List[SearchResult]:
        """Simplified search interface."""
        return self.search(SearchQuery(
            query=query,
            mode=mode,
            limit=limit
        ))

    def get_similar(self, decision_id: str, limit: int = 5) -> List[SearchResult]:
        """Find decisions similar to a given decision."""
        doc = self.documents.get(decision_id)
        if not doc:
            return []

        return self.simple_search(doc.text, limit=limit + 1)[1:]  # Exclude self


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_index_from_decisions(
    decisions: List[Dict[str, Any]],
    use_semantic: bool = True,
    embedding_provider: Optional[EmbeddingProvider] = None
) -> DecisionIndex:
    """
    Create and populate an index from decisions.

    Args:
        decisions: List of decision dictionaries
        use_semantic: Enable semantic search
        embedding_provider: Custom embedding provider (optional)

    Returns:
        Populated DecisionIndex
    """
    index = DecisionIndex(
        embedding_provider=embedding_provider,
        use_semantic=use_semantic
    )
    index.index_batch(decisions)
    return index


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "SearchMode",
    "EmbeddingModel",
    # Data structures
    "IndexedDecision",
    "SearchResult",
    "SearchQuery",
    # Embedding providers
    "EmbeddingProvider",
    "DummyEmbeddingProvider",
    "LocalEmbeddingProvider",
    # Search engines
    "KeywordSearchEngine",
    "SemanticSearchEngine",
    # Main index
    "DecisionIndex",
    # Convenience
    "create_index_from_decisions",
]
