"""
MANTRA Score Fusion - RRF & Hybrid Fusion Methods

Implements state-of-the-art score fusion algorithms:

1. RRF (Reciprocal Rank Fusion):
   - Standard in industry (Elasticsearch, Vespa, Pinecone)
   - Robust to score scale differences
   - Formula: RRF(d) = Σ 1 / (k + rank(d)) where k=60 typical

2. WEIGHTED LINEAR:
   - Simple weighted combination
   - Score = w1*s1 + w2*s2
   - Sensitive to score distributions

3. COMBMNZ (CombMNZ):
   - Multiply by number of sources that retrieved the doc
   - Good for high-recall scenarios

4. COMBSUM:
   - Simple sum of scores
   - Baseline approach

5. COMBSUM_NORMALIZED (NEW - Multi-Agent Winner):
   - Normalize each source to [0,1] before summing
   - 0.8544 relevance (Agent 2 finding)
   - Best for keyword-heavy content like MANTRA decisions

6. BORDA COUNT:
   - Voting-based fusion
   - Each ranker "votes" for documents

USAGE:
    from core.retrieval.fusion import RRFusion, FusionConfig

    fuser = RRFusion(k=60)
    results = fuser.fuse([
        {"doc1": 0.9, "doc2": 0.7},  # Vector scores
        {"doc2": 0.8, "doc1": 0.5},  # Keyword scores
    ])
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
from abc import ABC, abstractmethod
import math


# ============================================================================
# ENUMS & CONFIG
# ============================================================================

class FusionMethod(str, Enum):
    """Score fusion method."""
    RRF = "rrf"                    # Reciprocal Rank Fusion (recommended)
    WEIGHTED_LINEAR = "weighted"   # Weighted linear combination
    COMBMNZ = "combmnz"           # Multiply by retrieval count
    COMBSUM = "combsum"           # Simple sum
    COMBSUM_NORMALIZED = "combsum_normalized"  # Normalized sum (Agent 2 winner)
    COMBMAX = "combmax"           # Take max score
    COMBMIN = "combmin"           # Take min score (conservative)
    BORDA = "borda"               # Borda count voting


@dataclass
class FusionConfig:
    """Fusion configuration."""
    method: FusionMethod = FusionMethod.RRF
    rrf_k: int = 60               # RRF constant (typical: 60)
    weights: Optional[List[float]] = None  # Weights for linear fusion
    normalize_output: bool = True  # Normalize final scores to 0-1
    min_sources: int = 1          # Min sources required to include doc


@dataclass
class FusedResult:
    """Result of score fusion."""
    doc_id: str
    final_score: float
    source_scores: Dict[str, float]  # source_name -> score
    source_ranks: Dict[str, int]     # source_name -> rank
    num_sources: int                 # How many sources retrieved this doc
    fusion_breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass
class FusionResponse:
    """Complete fusion response."""
    results: List[FusedResult]
    method_used: FusionMethod
    num_sources: int
    total_unique_docs: int
    fusion_time_ms: float


# ============================================================================
# FUSION ALGORITHMS
# ============================================================================

class ScoreFuser(ABC):
    """Abstract base for score fusion algorithms."""

    @abstractmethod
    def fuse(
        self,
        score_lists: List[Dict[str, float]],
        source_names: Optional[List[str]] = None,
    ) -> List[FusedResult]:
        """
        Fuse scores from multiple sources.

        Args:
            score_lists: List of {doc_id: score} dicts from each source
            source_names: Optional names for each source

        Returns:
            List of FusedResult sorted by final_score descending
        """
        pass


class RRFusion(ScoreFuser):
    """
    Reciprocal Rank Fusion (RRF).

    The de-facto standard for combining ranked lists.
    Robust to:
    - Different score scales across sources
    - Outliers
    - Missing documents in some sources

    Formula:
        RRF(d) = Σ 1 / (k + rank_i(d))

    Where:
    - k is a constant (default 60)
    - rank_i(d) is the rank of document d in source i
    - Documents not in a source get rank = infinity (0 contribution)

    Properties:
    - Top-ranked docs get ~1/k contribution
    - Lower-ranked docs get diminishing contribution
    - k=60 is empirically good for most cases
    """

    def __init__(self, k: int = 60):
        """
        Initialize RRF.

        Args:
            k: RRF constant. Higher = more emphasis on top ranks.
               Default 60 is standard.
        """
        self.k = k

    def fuse(
        self,
        score_lists: List[Dict[str, float]],
        source_names: Optional[List[str]] = None,
    ) -> List[FusedResult]:
        """Fuse using RRF."""
        if not score_lists:
            return []

        num_sources = len(score_lists)
        source_names = source_names or [f"source_{i}" for i in range(num_sources)]

        # Convert scores to ranks for each source
        rank_lists: List[Dict[str, int]] = []
        for scores in score_lists:
            # Sort by score descending
            sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(sorted_docs)}
            rank_lists.append(ranks)

        # Collect all unique documents
        all_docs: Set[str] = set()
        for scores in score_lists:
            all_docs.update(scores.keys())

        # Calculate RRF score for each document
        results = []
        for doc_id in all_docs:
            rrf_score = 0.0
            source_scores = {}
            source_ranks = {}
            num_sources_hit = 0

            for i, (scores, ranks) in enumerate(zip(score_lists, rank_lists)):
                source_name = source_names[i]

                if doc_id in scores:
                    rank = ranks[doc_id]
                    contribution = 1.0 / (self.k + rank)
                    rrf_score += contribution

                    source_scores[source_name] = scores[doc_id]
                    source_ranks[source_name] = rank
                    num_sources_hit += 1

            results.append(FusedResult(
                doc_id=doc_id,
                final_score=rrf_score,
                source_scores=source_scores,
                source_ranks=source_ranks,
                num_sources=num_sources_hit,
                fusion_breakdown={"rrf_k": self.k, "rrf_score": rrf_score},
            ))

        # Sort by RRF score descending
        results.sort(key=lambda r: r.final_score, reverse=True)

        return results


class WeightedLinearFusion(ScoreFuser):
    """
    Weighted Linear Score Fusion.

    Simple weighted combination:
        final_score = Σ w_i * score_i

    Pros:
    - Simple and interpretable
    - Direct control via weights

    Cons:
    - Sensitive to score scales
    - Requires normalized scores
    """

    def __init__(self, weights: Optional[List[float]] = None):
        """
        Initialize weighted fusion.

        Args:
            weights: Weights for each source. If None, equal weights.
        """
        self.weights = weights

    def fuse(
        self,
        score_lists: List[Dict[str, float]],
        source_names: Optional[List[str]] = None,
    ) -> List[FusedResult]:
        """Fuse using weighted linear combination."""
        if not score_lists:
            return []

        num_sources = len(score_lists)
        source_names = source_names or [f"source_{i}" for i in range(num_sources)]

        # Default to equal weights
        weights = self.weights or [1.0 / num_sources] * num_sources

        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        # Collect all unique documents
        all_docs: Set[str] = set()
        for scores in score_lists:
            all_docs.update(scores.keys())

        # Calculate weighted score for each document
        results = []
        for doc_id in all_docs:
            weighted_score = 0.0
            source_scores = {}
            source_ranks = {}
            num_sources_hit = 0
            breakdown = {}

            for i, (scores, name) in enumerate(zip(score_lists, source_names)):
                weight = weights[i]

                if doc_id in scores:
                    score = scores[doc_id]
                    contribution = weight * score
                    weighted_score += contribution

                    source_scores[name] = score
                    num_sources_hit += 1
                    breakdown[f"{name}_contribution"] = contribution

            results.append(FusedResult(
                doc_id=doc_id,
                final_score=weighted_score,
                source_scores=source_scores,
                source_ranks=source_ranks,
                num_sources=num_sources_hit,
                fusion_breakdown=breakdown,
            ))

        results.sort(key=lambda r: r.final_score, reverse=True)

        # Add ranks
        for i, result in enumerate(results):
            for name in source_names:
                if name in result.source_scores:
                    # Calculate rank for this source
                    sorted_by_source = sorted(
                        [r for r in results if name in r.source_scores],
                        key=lambda r: r.source_scores[name],
                        reverse=True,
                    )
                    for rank, r in enumerate(sorted_by_source, 1):
                        if r.doc_id == result.doc_id:
                            result.source_ranks[name] = rank
                            break

        return results


class CombMNZFusion(ScoreFuser):
    """
    CombMNZ (Combination of Multiple Evidence with MNZ).

    Formula:
        CombMNZ(d) = count(d) * Σ score_i(d)

    Where count(d) is the number of sources that retrieved document d.

    Intuition: Documents retrieved by more sources are more likely relevant.

    Pros:
    - Rewards documents found by multiple sources
    - Good for high-recall scenarios

    Cons:
    - May over-reward popular documents
    """

    def fuse(
        self,
        score_lists: List[Dict[str, float]],
        source_names: Optional[List[str]] = None,
    ) -> List[FusedResult]:
        """Fuse using CombMNZ."""
        if not score_lists:
            return []

        num_sources = len(score_lists)
        source_names = source_names or [f"source_{i}" for i in range(num_sources)]

        # Collect all unique documents
        all_docs: Set[str] = set()
        for scores in score_lists:
            all_docs.update(scores.keys())

        # Calculate CombMNZ for each document
        results = []
        for doc_id in all_docs:
            sum_score = 0.0
            source_scores = {}
            num_sources_hit = 0

            for i, (scores, name) in enumerate(zip(score_lists, source_names)):
                if doc_id in scores:
                    score = scores[doc_id]
                    sum_score += score
                    source_scores[name] = score
                    num_sources_hit += 1

            # CombMNZ: multiply sum by count
            combmnz_score = num_sources_hit * sum_score

            results.append(FusedResult(
                doc_id=doc_id,
                final_score=combmnz_score,
                source_scores=source_scores,
                source_ranks={},
                num_sources=num_sources_hit,
                fusion_breakdown={
                    "sum_score": sum_score,
                    "num_sources": num_sources_hit,
                    "combmnz": combmnz_score,
                },
            ))

        results.sort(key=lambda r: r.final_score, reverse=True)
        return results


class CombSUMNormalizedFusion(ScoreFuser):
    """
    CombSUM with Min-Max Normalization (Multi-Agent Winner - Agent 2).

    Normalizes each source's scores to [0,1] before summing.
    This handles score scale differences between vector and keyword scores.

    Formula:
        score_norm(d) = (score(d) - min) / (max - min)
        CombSUM_norm(d) = Σ score_norm_i(d)

    Multi-Agent Results:
        - Relevance: 0.8544 (vs baseline 0.8227)
        - +3.9% improvement over unnormalized
        - Beats RRF for keyword-heavy content

    Pros:
    - Handles different score scales automatically
    - Simple and interpretable
    - No hyperparameters needed

    Cons:
    - Sensitive to outliers in each source
    """

    def __init__(self, weighted: bool = False, weights: Optional[List[float]] = None):
        """
        Initialize CombSUM-Normalized fusion.

        Args:
            weighted: If True, apply weights after normalization
            weights: Optional weights for each source (only if weighted=True)
        """
        self.weighted = weighted
        self.weights = weights

    def _normalize_minmax(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Normalize scores to [0,1] using min-max scaling."""
        if not scores:
            return {}

        values = list(scores.values())
        min_val = min(values)
        max_val = max(values)

        # Avoid division by zero
        if max_val == min_val:
            return {doc_id: 1.0 for doc_id in scores}

        return {
            doc_id: (score - min_val) / (max_val - min_val)
            for doc_id, score in scores.items()
        }

    def fuse(
        self,
        score_lists: List[Dict[str, float]],
        source_names: Optional[List[str]] = None,
    ) -> List[FusedResult]:
        """Fuse using CombSUM with normalization."""
        if not score_lists:
            return []

        num_sources = len(score_lists)
        source_names = source_names or [f"source_{i}" for i in range(num_sources)]

        # Normalize each source
        normalized_lists = [self._normalize_minmax(scores) for scores in score_lists]

        # Set up weights
        if self.weighted and self.weights:
            weights = self.weights
            # Normalize weights to sum to 1
            total = sum(weights)
            weights = [w / total for w in weights]
        else:
            weights = [1.0] * num_sources

        # Collect all unique documents
        all_docs: Set[str] = set()
        for scores in score_lists:
            all_docs.update(scores.keys())

        # Calculate normalized sum for each document
        results = []
        for doc_id in all_docs:
            sum_score = 0.0
            source_scores = {}
            source_normalized = {}
            num_sources_hit = 0

            for i, (orig_scores, norm_scores, name) in enumerate(
                zip(score_lists, normalized_lists, source_names)
            ):
                if doc_id in orig_scores:
                    orig_score = orig_scores[doc_id]
                    norm_score = norm_scores[doc_id]
                    weighted_norm = norm_score * weights[i]
                    sum_score += weighted_norm

                    source_scores[name] = orig_score
                    source_normalized[f"{name}_normalized"] = norm_score
                    num_sources_hit += 1

            results.append(FusedResult(
                doc_id=doc_id,
                final_score=sum_score,
                source_scores=source_scores,
                source_ranks={},
                num_sources=num_sources_hit,
                fusion_breakdown={
                    **source_normalized,
                    "combsum_normalized": sum_score,
                },
            ))

        results.sort(key=lambda r: r.final_score, reverse=True)
        return results


class BordaCountFusion(ScoreFuser):
    """
    Borda Count Fusion.

    Each source "votes" for documents based on rank:
        vote(d) = N - rank(d) + 1

    Where N is the number of candidates in that source.

    Pros:
    - Pure rank-based, ignores score magnitudes
    - Robust to score calibration issues

    Cons:
    - Loses score magnitude information
    """

    def fuse(
        self,
        score_lists: List[Dict[str, float]],
        source_names: Optional[List[str]] = None,
    ) -> List[FusedResult]:
        """Fuse using Borda count."""
        if not score_lists:
            return []

        num_sources = len(score_lists)
        source_names = source_names or [f"source_{i}" for i in range(num_sources)]

        # Collect all unique documents
        all_docs: Set[str] = set()
        for scores in score_lists:
            all_docs.update(scores.keys())

        # Calculate Borda score for each document
        results = []
        for doc_id in all_docs:
            borda_score = 0.0
            source_scores = {}
            source_ranks = {}
            num_sources_hit = 0

            for i, (scores, name) in enumerate(zip(score_lists, source_names)):
                if doc_id in scores:
                    # Convert to rank
                    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                    n = len(sorted_docs)

                    for rank, (d, s) in enumerate(sorted_docs, 1):
                        if d == doc_id:
                            # Borda vote: N - rank + 1
                            vote = n - rank + 1
                            borda_score += vote
                            source_scores[name] = scores[doc_id]
                            source_ranks[name] = rank
                            num_sources_hit += 1
                            break

            results.append(FusedResult(
                doc_id=doc_id,
                final_score=borda_score,
                source_scores=source_scores,
                source_ranks=source_ranks,
                num_sources=num_sources_hit,
                fusion_breakdown={"borda_score": borda_score},
            ))

        results.sort(key=lambda r: r.final_score, reverse=True)
        return results


# ============================================================================
# MAIN FUSION CLASS
# ============================================================================

class ScoreFusion:
    """
    Main score fusion class with multiple method support.

    Example:
        fusion = ScoreFusion(config=FusionConfig(
            method=FusionMethod.RRF,
            rrf_k=60,
        ))

        response = fusion.fuse(
            score_lists=[
                {"doc1": 0.9, "doc2": 0.7},  # Vector scores
                {"doc2": 0.8, "doc1": 0.5},  # Keyword scores
            ],
            source_names=["vector", "keyword"],
        )
    """

    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()

        # Initialize fusers
        self._fusers: Dict[FusionMethod, ScoreFuser] = {
            FusionMethod.RRF: RRFusion(k=self.config.rrf_k),
            FusionMethod.WEIGHTED_LINEAR: WeightedLinearFusion(
                weights=self.config.weights
            ),
            FusionMethod.COMBMNZ: CombMNZFusion(),
            FusionMethod.COMBSUM: WeightedLinearFusion(weights=None),  # Equal weights
            FusionMethod.COMBSUM_NORMALIZED: CombSUMNormalizedFusion(
                weighted=self.config.weights is not None,
                weights=self.config.weights,
            ),
            FusionMethod.BORDA: BordaCountFusion(),
        }

    def fuse(
        self,
        score_lists: List[Dict[str, float]],
        source_names: Optional[List[str]] = None,
        method: Optional[FusionMethod] = None,
        top_k: Optional[int] = None,
    ) -> FusionResponse:
        """
        Fuse scores from multiple sources.

        Args:
            score_lists: List of {doc_id: score} dicts
            source_names: Optional names for sources
            method: Override default fusion method
            top_k: Limit results to top K

        Returns:
            FusionResponse with fused results
        """
        import time
        start_time = time.time()

        method = method or self.config.method

        if not score_lists:
            return FusionResponse(
                results=[],
                method_used=method,
                num_sources=0,
                total_unique_docs=0,
                fusion_time_ms=0,
            )

        # Get the appropriate fuser
        fuser = self._fusers.get(method, self._fusers[FusionMethod.RRF])

        # Perform fusion
        results = fuser.fuse(score_lists, source_names)

        # Filter by min_sources
        if self.config.min_sources > 1:
            results = [r for r in results if r.num_sources >= self.config.min_sources]

        # Normalize if configured
        if self.config.normalize_output and results:
            max_score = max(r.final_score for r in results)
            if max_score > 0:
                for r in results:
                    r.final_score = r.final_score / max_score

        # Limit to top_k
        if top_k:
            results = results[:top_k]

        elapsed_ms = (time.time() - start_time) * 1000

        # Count unique docs across all sources
        all_docs = set()
        for scores in score_lists:
            all_docs.update(scores.keys())

        return FusionResponse(
            results=results,
            method_used=method,
            num_sources=len(score_lists),
            total_unique_docs=len(all_docs),
            fusion_time_ms=elapsed_ms,
        )

    def fuse_simple(
        self,
        vector_scores: Dict[str, float],
        keyword_scores: Dict[str, float],
        method: Optional[FusionMethod] = None,
        top_k: int = 10,
    ) -> List[Tuple[str, float]]:
        """
        Simplified fusion for two sources (vector + keyword).

        Returns list of (doc_id, score) tuples.
        """
        response = self.fuse(
            score_lists=[vector_scores, keyword_scores],
            source_names=["vector", "keyword"],
            method=method,
            top_k=top_k,
        )

        return [(r.doc_id, r.final_score) for r in response.results]


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_rrf_fusion(k: int = 60) -> ScoreFusion:
    """Create RRF fusion (recommended)."""
    return ScoreFusion(FusionConfig(
        method=FusionMethod.RRF,
        rrf_k=k,
    ))


def create_weighted_fusion(
    weights: List[float],
    normalize: bool = True,
) -> ScoreFusion:
    """Create weighted linear fusion."""
    return ScoreFusion(FusionConfig(
        method=FusionMethod.WEIGHTED_LINEAR,
        weights=weights,
        normalize_output=normalize,
    ))


def fuse_rrf(
    score_lists: List[Dict[str, float]],
    k: int = 60,
    top_k: int = 10,
) -> List[Tuple[str, float]]:
    """
    Quick RRF fusion.

    Args:
        score_lists: List of {doc_id: score} dicts
        k: RRF constant
        top_k: Number of results

    Returns:
        List of (doc_id, score) tuples
    """
    fusion = create_rrf_fusion(k)
    response = fusion.fuse(score_lists, top_k=top_k)
    return [(r.doc_id, r.final_score) for r in response.results]


def fuse_hybrid(
    vector_scores: Dict[str, float],
    keyword_scores: Dict[str, float],
    method: str = "rrf",
    top_k: int = 10,
) -> List[Tuple[str, float]]:
    """
    Quick hybrid fusion for vector + keyword scores.

    Args:
        vector_scores: {doc_id: vector_score}
        keyword_scores: {doc_id: keyword_score}
        method: "rrf" or "weighted"
        top_k: Number of results

    Returns:
        List of (doc_id, score) tuples
    """
    fusion_method = FusionMethod.RRF if method == "rrf" else FusionMethod.WEIGHTED_LINEAR
    fusion = ScoreFusion(FusionConfig(method=fusion_method))
    return fusion.fuse_simple(vector_scores, keyword_scores, top_k=top_k)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "FusionMethod",
    # Config
    "FusionConfig",
    # Data classes
    "FusedResult",
    "FusionResponse",
    # Fusers
    "ScoreFuser",
    "RRFusion",
    "WeightedLinearFusion",
    "CombMNZFusion",
    "CombSUMNormalizedFusion",
    "BordaCountFusion",
    # Main class
    "ScoreFusion",
    # Factory functions
    "create_rrf_fusion",
    "create_weighted_fusion",
    # Quick functions
    "fuse_rrf",
    "fuse_hybrid",
]
