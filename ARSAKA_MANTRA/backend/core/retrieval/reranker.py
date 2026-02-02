"""
MANTRA Reranker - Cross-Encoder & Late Interaction Reranking

Implements state-of-the-art reranking for improved retrieval accuracy:

1. CROSS-ENCODER RERANKING:
   - Two-stage retrieval: bi-encoder (fast) → cross-encoder (accurate)
   - Processes query-document pairs for semantic similarity
   - +20-35% accuracy improvement over bi-encoder alone

2. LATE INTERACTION (ColBERT-style):
   - Token-level matching between query and document
   - MaxSim operation for fine-grained relevance
   - 100x faster than cross-encoder with similar accuracy

3. COHERE RERANK:
   - Cloud API for production-grade reranking
   - No GPU required, easy integration

USAGE:
    from core.retrieval.reranker import Reranker, RerankerConfig

    reranker = Reranker(config=RerankerConfig(
        method="cross_encoder",
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_k=10,
    ))

    reranked = reranker.rerank(query, candidates)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple, Protocol, Callable
from enum import Enum
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & CONFIG
# ============================================================================

class RerankerMethod(str, Enum):
    """Reranking method selection."""
    NONE = "none"                    # No reranking (passthrough)
    CROSS_ENCODER = "cross_encoder"  # Full cross-encoder (most accurate)
    LATE_INTERACTION = "late_interaction"  # ColBERT-style (fast + accurate)
    COHERE = "cohere"                # Cohere Rerank API
    CUSTOM = "custom"                # Custom scoring function


@dataclass
class RerankerConfig:
    """Reranker configuration."""
    method: RerankerMethod = RerankerMethod.CROSS_ENCODER
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    top_k: int = 10                  # Return top K after reranking
    batch_size: int = 32             # Batch size for inference
    max_length: int = 512            # Max tokens for cross-encoder
    normalize_scores: bool = True    # Normalize scores to 0-1

    # Cohere-specific
    cohere_api_key: Optional[str] = None
    cohere_model: str = "rerank-english-v3.0"

    # Late interaction specific
    token_dim: int = 128             # Token embedding dimension

    # Fallback
    fallback_to_original: bool = True  # If reranker fails, return original


@dataclass
class RerankerCandidate:
    """Candidate document for reranking."""
    doc_id: str
    text: str
    original_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RerankerResult:
    """Reranking result for a single document."""
    doc_id: str
    text: str
    original_score: float
    rerank_score: float
    final_score: float
    rank: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Debug info
    score_breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass
class RerankerResponse:
    """Complete reranking response."""
    results: List[RerankerResult]
    method_used: RerankerMethod
    candidates_received: int
    candidates_returned: int
    rerank_time_ms: float
    model_name: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# ABSTRACT BASE
# ============================================================================

class RerankerBackend(ABC):
    """Abstract base for reranker implementations."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: List[RerankerCandidate],
        top_k: int = 10,
    ) -> List[Tuple[str, float]]:
        """
        Rerank candidates for a query.

        Args:
            query: Search query
            candidates: List of candidate documents
            top_k: Number of results to return

        Returns:
            List of (doc_id, score) tuples, sorted by score descending
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available."""
        pass


# ============================================================================
# CROSS-ENCODER BACKEND
# ============================================================================

class CrossEncoderBackend(RerankerBackend):
    """
    Cross-encoder reranking using sentence-transformers.

    Processes query-document pairs through a transformer model
    for accurate semantic similarity scoring.

    Requires: sentence-transformers
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        max_length: int = 512,
        batch_size: int = 32,
        device: Optional[str] = None,
    ):
        self.model_name = model_name
        self.max_length = max_length
        self.batch_size = batch_size
        self.device = device
        self._model = None
        self._available = None

    def is_available(self) -> bool:
        """Check if sentence-transformers is available."""
        if self._available is not None:
            return self._available

        try:
            from sentence_transformers import CrossEncoder
            self._available = True
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
            self._available = False

        return self._available

    def _load_model(self):
        """Lazy load the cross-encoder model."""
        if self._model is None and self.is_available():
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading cross-encoder model: {self.model_name}")
            self._model = CrossEncoder(
                self.model_name,
                max_length=self.max_length,
                device=self.device,
            )

    def rerank(
        self,
        query: str,
        candidates: List[RerankerCandidate],
        top_k: int = 10,
    ) -> List[Tuple[str, float]]:
        """Rerank using cross-encoder."""
        if not self.is_available():
            return [(c.doc_id, c.original_score) for c in candidates[:top_k]]

        self._load_model()

        # Prepare query-document pairs
        pairs = [(query, c.text) for c in candidates]

        # Score in batches
        scores = self._model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )

        # Combine with doc_ids
        scored = list(zip([c.doc_id for c in candidates], scores))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[:top_k]


# ============================================================================
# LATE INTERACTION (ColBERT-style) BACKEND
# ============================================================================

class LateInteractionBackend(RerankerBackend):
    """
    ColBERT-style late interaction reranking.

    Uses token-level embeddings with MaxSim operation:
    - Embed query and document tokens separately
    - Compute max similarity for each query token to any doc token
    - Sum the max similarities

    Much faster than cross-encoder while maintaining accuracy.

    Requires: sentence-transformers (for token embeddings)
    """

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        token_dim: int = 128,
        device: Optional[str] = None,
    ):
        self.model_name = model_name
        self.token_dim = token_dim
        self.device = device
        self._model = None
        self._tokenizer = None
        self._available = None

    def is_available(self) -> bool:
        """Check if required libraries are available."""
        if self._available is not None:
            return self._available

        try:
            from transformers import AutoModel, AutoTokenizer
            import torch
            self._available = True
        except ImportError:
            logger.warning(
                "transformers/torch not installed for late interaction. "
                "Install with: pip install transformers torch"
            )
            self._available = False

        return self._available

    def _load_model(self):
        """Lazy load the model."""
        if self._model is None and self.is_available():
            from transformers import AutoModel, AutoTokenizer
            logger.info(f"Loading late interaction model: {self.model_name}")
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModel.from_pretrained(self.model_name)
            if self.device:
                self._model = self._model.to(self.device)
            self._model.eval()

    def _get_token_embeddings(self, text: str) -> "torch.Tensor":
        """Get token-level embeddings for text."""
        import torch

        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )

        if self.device:
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model(**inputs)
            # Use last hidden state as token embeddings
            token_embs = outputs.last_hidden_state  # [1, seq_len, hidden_dim]

        return token_embs.squeeze(0)  # [seq_len, hidden_dim]

    def _maxsim_score(
        self,
        query_embs: "torch.Tensor",
        doc_embs: "torch.Tensor",
    ) -> float:
        """
        Compute MaxSim score between query and document.

        For each query token, find max similarity to any doc token.
        Sum all max similarities.
        """
        import torch
        import torch.nn.functional as F

        # Normalize embeddings
        query_embs = F.normalize(query_embs, p=2, dim=-1)
        doc_embs = F.normalize(doc_embs, p=2, dim=-1)

        # Compute similarity matrix [query_len, doc_len]
        sim_matrix = torch.mm(query_embs, doc_embs.T)

        # MaxSim: max over document tokens for each query token
        max_sims = sim_matrix.max(dim=1).values  # [query_len]

        # Sum and normalize
        score = max_sims.sum().item() / len(max_sims)

        return score

    def rerank(
        self,
        query: str,
        candidates: List[RerankerCandidate],
        top_k: int = 10,
    ) -> List[Tuple[str, float]]:
        """Rerank using late interaction."""
        if not self.is_available():
            return [(c.doc_id, c.original_score) for c in candidates[:top_k]]

        self._load_model()

        # Get query token embeddings (compute once)
        query_embs = self._get_token_embeddings(query)

        # Score each candidate
        scores = []
        for candidate in candidates:
            doc_embs = self._get_token_embeddings(candidate.text)
            score = self._maxsim_score(query_embs, doc_embs)
            scores.append((candidate.doc_id, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_k]


# ============================================================================
# COHERE RERANK BACKEND
# ============================================================================

class CohereRerankerBackend(RerankerBackend):
    """
    Cohere Rerank API backend.

    Cloud-based reranking with high accuracy and no GPU required.
    Cost: ~$1 per 1000 queries.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "rerank-english-v3.0",
    ):
        self.api_key = api_key
        self.model = model
        self._client = None
        self._available = None

    def is_available(self) -> bool:
        """Check if Cohere is available."""
        if self._available is not None:
            return self._available

        if not self.api_key:
            import os
            self.api_key = os.environ.get("COHERE_API_KEY")

        if not self.api_key:
            logger.warning("Cohere API key not set")
            self._available = False
            return False

        try:
            import cohere
            self._available = True
        except ImportError:
            logger.warning("cohere not installed. Install with: pip install cohere")
            self._available = False

        return self._available

    def _get_client(self):
        """Lazy load the Cohere client."""
        if self._client is None and self.is_available():
            import cohere
            self._client = cohere.Client(self.api_key)
        return self._client

    def rerank(
        self,
        query: str,
        candidates: List[RerankerCandidate],
        top_k: int = 10,
    ) -> List[Tuple[str, float]]:
        """Rerank using Cohere API."""
        if not self.is_available():
            return [(c.doc_id, c.original_score) for c in candidates[:top_k]]

        client = self._get_client()

        # Prepare documents
        documents = [c.text for c in candidates]

        try:
            response = client.rerank(
                query=query,
                documents=documents,
                model=self.model,
                top_n=top_k,
            )

            # Map back to doc_ids
            results = []
            for result in response.results:
                doc_id = candidates[result.index].doc_id
                score = result.relevance_score
                results.append((doc_id, score))

            return results

        except Exception as e:
            logger.error(f"Cohere rerank failed: {e}")
            return [(c.doc_id, c.original_score) for c in candidates[:top_k]]


# ============================================================================
# TF-IDF FALLBACK BACKEND
# ============================================================================

class TFIDFFallbackBackend(RerankerBackend):
    """
    TF-IDF based fallback reranker.

    Used when ML models are not available.
    Simple but effective for keyword-heavy queries.
    """

    def __init__(self):
        self._vectorizer = None
        self._available = None

    def is_available(self) -> bool:
        """Always available (uses sklearn or pure Python)."""
        if self._available is not None:
            return self._available

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            self._available = True
        except ImportError:
            # Pure Python fallback
            self._available = True

        return True

    def rerank(
        self,
        query: str,
        candidates: List[RerankerCandidate],
        top_k: int = 10,
    ) -> List[Tuple[str, float]]:
        """Rerank using TF-IDF similarity."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            # Combine query with all documents
            all_texts = [query] + [c.text for c in candidates]

            vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=5000,
                ngram_range=(1, 2),
            )

            tfidf_matrix = vectorizer.fit_transform(all_texts)

            # Query is first row, documents are rest
            query_vec = tfidf_matrix[0:1]
            doc_vecs = tfidf_matrix[1:]

            # Compute cosine similarity
            similarities = cosine_similarity(query_vec, doc_vecs).flatten()

            # Combine with doc_ids
            scored = list(zip([c.doc_id for c in candidates], similarities))
            scored.sort(key=lambda x: x[1], reverse=True)

            return scored[:top_k]

        except ImportError:
            # Pure Python fallback: simple word overlap
            return self._simple_overlap_rerank(query, candidates, top_k)

    def _simple_overlap_rerank(
        self,
        query: str,
        candidates: List[RerankerCandidate],
        top_k: int,
    ) -> List[Tuple[str, float]]:
        """Simple word overlap scoring."""
        query_words = set(query.lower().split())

        scores = []
        for candidate in candidates:
            doc_words = set(candidate.text.lower().split())
            overlap = len(query_words & doc_words)
            union = len(query_words | doc_words)
            score = overlap / union if union > 0 else 0.0
            scores.append((candidate.doc_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ============================================================================
# MAIN RERANKER CLASS
# ============================================================================

class Reranker:
    """
    Main reranker class with multiple backend support.

    Supports:
    - Cross-encoder (most accurate)
    - Late interaction / ColBERT (fast + accurate)
    - Cohere API (cloud, no GPU)
    - TF-IDF fallback (always available)

    Example:
        reranker = Reranker(config=RerankerConfig(
            method=RerankerMethod.CROSS_ENCODER,
            top_k=10,
        ))

        response = reranker.rerank(
            query="database design patterns",
            candidates=[
                RerankerCandidate(doc_id="1", text="SQL schema design...", original_score=0.8),
                RerankerCandidate(doc_id="2", text="NoSQL databases...", original_score=0.7),
            ],
        )
    """

    def __init__(self, config: Optional[RerankerConfig] = None):
        self.config = config or RerankerConfig()

        # Initialize backends
        self._backends: Dict[RerankerMethod, RerankerBackend] = {
            RerankerMethod.CROSS_ENCODER: CrossEncoderBackend(
                model_name=self.config.model_name,
                max_length=self.config.max_length,
                batch_size=self.config.batch_size,
            ),
            RerankerMethod.LATE_INTERACTION: LateInteractionBackend(
                token_dim=self.config.token_dim,
            ),
            RerankerMethod.COHERE: CohereRerankerBackend(
                api_key=self.config.cohere_api_key,
                model=self.config.cohere_model,
            ),
        }

        # Fallback backend (always available)
        self._fallback = TFIDFFallbackBackend()

        # Custom scoring function
        self._custom_scorer: Optional[Callable] = None

    def set_custom_scorer(
        self,
        scorer: Callable[[str, List[RerankerCandidate]], List[Tuple[str, float]]],
    ):
        """Set a custom scoring function."""
        self._custom_scorer = scorer

    def rerank(
        self,
        query: str,
        candidates: List[RerankerCandidate],
        method: Optional[RerankerMethod] = None,
        top_k: Optional[int] = None,
    ) -> RerankerResponse:
        """
        Rerank candidates for a query.

        Args:
            query: Search query
            candidates: List of candidate documents
            method: Override default method
            top_k: Override default top_k

        Returns:
            RerankerResponse with reranked results
        """
        import time
        start_time = time.time()

        method = method or self.config.method
        top_k = top_k or self.config.top_k

        # Handle empty or small candidate lists
        if not candidates:
            return RerankerResponse(
                results=[],
                method_used=method,
                candidates_received=0,
                candidates_returned=0,
                rerank_time_ms=0,
            )

        if len(candidates) <= top_k and method == RerankerMethod.NONE:
            # No reranking needed
            results = [
                RerankerResult(
                    doc_id=c.doc_id,
                    text=c.text,
                    original_score=c.original_score,
                    rerank_score=c.original_score,
                    final_score=c.original_score,
                    rank=i + 1,
                    metadata=c.metadata,
                )
                for i, c in enumerate(candidates)
            ]
            return RerankerResponse(
                results=results,
                method_used=RerankerMethod.NONE,
                candidates_received=len(candidates),
                candidates_returned=len(results),
                rerank_time_ms=(time.time() - start_time) * 1000,
            )

        # Try primary method
        scored: Optional[List[Tuple[str, float]]] = None
        error: Optional[str] = None
        model_name: Optional[str] = None

        if method == RerankerMethod.NONE:
            # Passthrough
            scored = [(c.doc_id, c.original_score) for c in candidates]
            scored.sort(key=lambda x: x[1], reverse=True)
            scored = scored[:top_k]

        elif method == RerankerMethod.CUSTOM and self._custom_scorer:
            try:
                scored = self._custom_scorer(query, candidates)[:top_k]
            except Exception as e:
                error = f"Custom scorer failed: {e}"

        elif method in self._backends:
            backend = self._backends[method]
            if backend.is_available():
                try:
                    scored = backend.rerank(query, candidates, top_k)
                    model_name = getattr(backend, "model_name", None)
                except Exception as e:
                    error = f"{method.value} reranking failed: {e}"
            else:
                error = f"{method.value} backend not available"

        # Fallback if needed
        if scored is None and self.config.fallback_to_original:
            logger.warning(f"Using TF-IDF fallback due to: {error}")
            scored = self._fallback.rerank(query, candidates, top_k)
            method = RerankerMethod.NONE  # Mark as fallback

        # Build results
        if scored is None:
            scored = []

        # Create doc_id -> candidate mapping
        candidate_map = {c.doc_id: c for c in candidates}

        # Normalize scores if configured
        if self.config.normalize_scores and scored:
            max_score = max(s[1] for s in scored) if scored else 1.0
            min_score = min(s[1] for s in scored) if scored else 0.0
            score_range = max_score - min_score
            if score_range > 0:
                scored = [
                    (doc_id, (score - min_score) / score_range)
                    for doc_id, score in scored
                ]

        results = []
        for rank, (doc_id, rerank_score) in enumerate(scored, 1):
            candidate = candidate_map.get(doc_id)
            if candidate:
                # Combine original and rerank scores
                # Weight: 70% rerank, 30% original
                final_score = 0.7 * rerank_score + 0.3 * candidate.original_score

                results.append(RerankerResult(
                    doc_id=doc_id,
                    text=candidate.text,
                    original_score=candidate.original_score,
                    rerank_score=rerank_score,
                    final_score=final_score,
                    rank=rank,
                    metadata=candidate.metadata,
                    score_breakdown={
                        "original": candidate.original_score,
                        "rerank": rerank_score,
                        "final": final_score,
                    },
                ))

        elapsed_ms = (time.time() - start_time) * 1000

        return RerankerResponse(
            results=results,
            method_used=method,
            candidates_received=len(candidates),
            candidates_returned=len(results),
            rerank_time_ms=elapsed_ms,
            model_name=model_name,
            error=error,
        )

    def get_available_methods(self) -> List[RerankerMethod]:
        """Get list of available reranking methods."""
        available = [RerankerMethod.NONE]

        for method, backend in self._backends.items():
            if backend.is_available():
                available.append(method)

        if self._custom_scorer:
            available.append(RerankerMethod.CUSTOM)

        return available

    def get_stats(self) -> Dict[str, Any]:
        """Get reranker statistics."""
        return {
            "default_method": self.config.method.value,
            "top_k": self.config.top_k,
            "available_methods": [m.value for m in self.get_available_methods()],
            "model_name": self.config.model_name,
            "has_custom_scorer": self._custom_scorer is not None,
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_reranker(
    method: str = "cross_encoder",
    top_k: int = 10,
    model_name: Optional[str] = None,
    cohere_api_key: Optional[str] = None,
) -> Reranker:
    """
    Create a reranker with specified configuration.

    Args:
        method: Reranking method ("cross_encoder", "late_interaction", "cohere", "none")
        top_k: Number of results to return
        model_name: Model name for cross-encoder/late interaction
        cohere_api_key: API key for Cohere

    Returns:
        Configured Reranker instance
    """
    config = RerankerConfig(
        method=RerankerMethod(method),
        top_k=top_k,
        cohere_api_key=cohere_api_key,
    )

    if model_name:
        config.model_name = model_name

    return Reranker(config)


def create_fast_reranker(top_k: int = 10) -> Reranker:
    """Create a fast reranker using TF-IDF (no ML models)."""
    config = RerankerConfig(
        method=RerankerMethod.NONE,
        top_k=top_k,
        fallback_to_original=True,
    )
    return Reranker(config)


def create_accurate_reranker(top_k: int = 10) -> Reranker:
    """Create an accurate reranker using cross-encoder."""
    config = RerankerConfig(
        method=RerankerMethod.CROSS_ENCODER,
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_k=top_k,
    )
    return Reranker(config)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "RerankerMethod",
    # Config
    "RerankerConfig",
    # Data classes
    "RerankerCandidate",
    "RerankerResult",
    "RerankerResponse",
    # Backends
    "RerankerBackend",
    "CrossEncoderBackend",
    "LateInteractionBackend",
    "CohereRerankerBackend",
    "TFIDFFallbackBackend",
    # Main class
    "Reranker",
    # Factory functions
    "create_reranker",
    "create_fast_reranker",
    "create_accurate_reranker",
]
