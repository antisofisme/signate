"""
MANTRA Optimal Retrieval Configuration v2.0

Based on MULTI-AGENT optimization (Jan 2025):
- 6 parallel agents explored 100+ configurations
- 1000 decisions, 15 query types, 5 iterations each
- Multiple fusion algorithms, reranking, thresholds tested

KEY FINDINGS (Multi-Agent Search):
1. Threshold tuning (min_score=0.37) provides +5% improvement
2. CombSUM-Normalized beats Linear and RRF fusion
3. Pure keyword (0/100) dominates for most query types
4. Fine-grained weights: 3%/97% optimal (not 10/90)
5. Reranking adds only +0.3% in optimized configs

MULTI-AGENT TOP 5:
| Rank | Agent | Config                          | Relevance |
|------|-------|--------------------------------|-----------|
| 1    | Ag5   | Boost/Threshold Tuned          | 0.8720    |
| 2    | Ag2   | CombSUM-Normalized             | 0.8544    |
| 3    | Ag6   | SquaredK-0/100                 | 0.8418    |
| 4    | Ag6   | MaxFusion                      | 0.8401    |
| 5    | -     | Linear-10/90+CrossEncoder@30   | 0.8301    |

RECOMMENDED CONFIGS:
| Use Case        | Config                    | Latency | Relevance |
|-----------------|---------------------------|---------|-----------|
| Max Accuracy    | ThresholdTuned+CombSUM    | ~6ms    | 0.87      |
| High Accuracy   | CombSUM-Normalized        | ~6ms    | 0.85      |
| Balanced        | Linear-3/97+threshold     | ~6ms    | 0.82      |
| Low Latency     | Linear-0/100              | ~5ms    | 0.82      |
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RetrievalProfile(str, Enum):
    """Predefined retrieval profiles."""
    MAX_ACCURACY = "max_accuracy"       # Best relevance (Agent 5 optimized)
    HIGH_ACCURACY = "high_accuracy"     # CombSUM-Normalized (Agent 2)
    BALANCED = "balanced"               # Good trade-off
    LOW_LATENCY = "low_latency"         # Fastest, still good
    PURE_KEYWORD = "pure_keyword"       # 0/100 keyword-only (Agent 4)
    RRF_STANDARD = "rrf_standard"       # Classic RRF (industry standard)


@dataclass
class OptimalConfig:
    """Optimal retrieval configuration."""
    # Fusion
    fusion_method: str = "linear"  # "linear", "rrf", "combsum", "combsum_normalized"
    vector_weight: float = 0.03    # Agent 1: 3% optimal (not 10%!)
    keyword_weight: float = 0.97   # Agent 1: 97% optimal
    rrf_k: int = 60                # RRF constant

    # Reranking
    rerank_enabled: bool = False   # Agent 3: marginal improvement only
    rerank_method: str = "none"    # "crossencoder", "tfidf", "none"
    rerank_top_n: int = 75         # Agent 3: 75 better than 30

    # Search - Agent 5 optimized thresholds
    min_score: float = 0.37        # Agent 5: KEY finding (+5% improvement)
    max_results: int = 10
    boost_multi_source: float = 1.05   # Agent 5: minimal boost
    boost_exact_match: float = 1.0     # Agent 5: no boost needed

    # Additional bonuses - Agent 5
    tag_match_bonus: float = 0.45      # Agent 5 optimal
    phrase_match_bonus: float = 0.17   # Agent 5 optimal

    # Profile name
    profile: str = "custom"


# Predefined optimal configurations (based on multi-agent search)
OPTIMAL_CONFIGS = {
    # Agent 5 Winner: Best overall (0.8720 relevance)
    RetrievalProfile.MAX_ACCURACY: OptimalConfig(
        fusion_method="combsum_normalized",  # Agent 2 fusion
        vector_weight=0.03,        # Agent 1 optimal
        keyword_weight=0.97,
        rerank_enabled=False,      # Agent 3: marginal improvement
        rerank_method="none",
        min_score=0.37,            # Agent 5 KEY finding
        boost_multi_source=1.05,   # Agent 5
        boost_exact_match=1.0,     # Agent 5
        tag_match_bonus=0.45,      # Agent 5
        phrase_match_bonus=0.17,   # Agent 5
        max_results=10,
        profile="max_accuracy",
    ),
    # Agent 2: CombSUM-Normalized (0.8544 relevance)
    RetrievalProfile.HIGH_ACCURACY: OptimalConfig(
        fusion_method="combsum_normalized",
        vector_weight=0.03,
        keyword_weight=0.97,
        rerank_enabled=False,
        rerank_method="none",
        min_score=0.3,
        max_results=10,
        profile="high_accuracy",
    ),
    # Balanced: Linear with optimized thresholds
    RetrievalProfile.BALANCED: OptimalConfig(
        fusion_method="linear",
        vector_weight=0.03,        # Agent 1 optimal
        keyword_weight=0.97,
        rerank_enabled=False,
        rerank_method="none",
        min_score=0.37,            # Agent 5 threshold
        boost_multi_source=1.05,
        max_results=10,
        profile="balanced",
    ),
    # Agent 4: Pure keyword (fastest, still 0.82+)
    RetrievalProfile.LOW_LATENCY: OptimalConfig(
        fusion_method="linear",
        vector_weight=0.0,         # Pure keyword
        keyword_weight=1.0,
        rerank_enabled=False,
        rerank_method="none",
        min_score=0.3,
        max_results=10,
        profile="low_latency",
    ),
    # Pure keyword profile (Agent 4)
    RetrievalProfile.PURE_KEYWORD: OptimalConfig(
        fusion_method="linear",
        vector_weight=0.0,
        keyword_weight=1.0,
        rerank_enabled=False,
        rerank_method="none",
        min_score=0.35,
        max_results=10,
        profile="pure_keyword",
    ),
    # RRF for compatibility
    RetrievalProfile.RRF_STANDARD: OptimalConfig(
        fusion_method="rrf",
        rrf_k=60,
        rerank_enabled=False,
        rerank_method="none",
        rerank_top_n=75,           # Agent 3 optimal
        max_results=10,
        profile="rrf_standard",
    ),
}


# Query-type specific adjustments (based on Agent 4 multi-agent search)
# Key finding: Pure keyword (0/100) wins for most query types!
QUERY_TYPE_ADJUSTMENTS = {
    "short": {
        # Short queries (1-2 words): pure keyword (0.9713 relevance)
        "vector_weight": 0.0,
        "keyword_weight": 1.0,
        "rerank_enabled": False,
    },
    "long": {
        # Long queries (5+ words): still keyword-heavy
        "vector_weight": 0.0,
        "keyword_weight": 1.0,
        "rerank_enabled": False,
    },
    "technical": {
        # Technical queries: pure keyword (0.6123 relevance)
        "vector_weight": 0.0,
        "keyword_weight": 1.0,
        "rerank_enabled": False,
    },
    "conceptual": {
        # Conceptual queries: keyword + TF-IDF rerank (0.6496 relevance)
        "vector_weight": 0.0,
        "keyword_weight": 1.0,
        "rerank_enabled": True,
        "rerank_method": "tfidf",
    },
    "domain": {
        # Domain-specific (ARCH, CTL, etc): pure keyword (1.0 relevance!)
        "vector_weight": 0.0,
        "keyword_weight": 1.0,
        "rerank_enabled": False,
    },
    "exact": {
        # Exact match queries: pure keyword
        "vector_weight": 0.0,
        "keyword_weight": 1.0,
        "rerank_enabled": False,
        "boost_exact_match": 1.5,
    },
    "fuzzy": {
        # Fuzzy/typo queries: ONLY case where vector helps (0.5971)
        "vector_weight": 0.2,
        "keyword_weight": 0.8,
        "rerank_enabled": True,
        "rerank_method": "tfidf",
    },
}


# Dataset size adjustments
DATASET_SIZE_ADJUSTMENTS = {
    "small": {  # < 200 decisions
        "rerank_top_n": 20,
        "max_results": 10,
    },
    "medium": {  # 200-1000 decisions
        "rerank_top_n": 30,
        "max_results": 15,
    },
    "large": {  # > 1000 decisions
        "rerank_top_n": 50,
        "max_results": 20,
    },
}


def get_optimal_config(
    profile: RetrievalProfile = RetrievalProfile.BALANCED,
    query_type: Optional[str] = None,
    dataset_size: Optional[int] = None,
) -> OptimalConfig:
    """
    Get optimal configuration based on profile and context.

    Args:
        profile: Retrieval profile (max_accuracy, high_accuracy, balanced, low_latency)
        query_type: Query type (short, long, technical, conceptual, domain, exact, fuzzy)
        dataset_size: Number of decisions in index

    Returns:
        OptimalConfig with adjusted settings
    """
    # Start with profile defaults
    config = OPTIMAL_CONFIGS.get(profile, OPTIMAL_CONFIGS[RetrievalProfile.BALANCED])

    # Create a copy to modify
    config = OptimalConfig(
        fusion_method=config.fusion_method,
        vector_weight=config.vector_weight,
        keyword_weight=config.keyword_weight,
        rrf_k=config.rrf_k,
        rerank_enabled=config.rerank_enabled,
        rerank_method=config.rerank_method,
        rerank_top_n=config.rerank_top_n,
        min_score=config.min_score,
        max_results=config.max_results,
        boost_multi_source=config.boost_multi_source,
        boost_exact_match=config.boost_exact_match,
        tag_match_bonus=config.tag_match_bonus,
        phrase_match_bonus=config.phrase_match_bonus,
        profile=config.profile,
    )

    # Apply query type adjustments
    if query_type and query_type in QUERY_TYPE_ADJUSTMENTS:
        adjustments = QUERY_TYPE_ADJUSTMENTS[query_type]
        for key, value in adjustments.items():
            if hasattr(config, key):
                setattr(config, key, value)

    # Apply dataset size adjustments
    if dataset_size:
        if dataset_size < 200:
            size_key = "small"
        elif dataset_size < 1000:
            size_key = "medium"
        else:
            size_key = "large"

        adjustments = DATASET_SIZE_ADJUSTMENTS[size_key]
        for key, value in adjustments.items():
            if hasattr(config, key):
                setattr(config, key, value)

    return config


def get_config_summary() -> str:
    """Get summary of all optimal configurations."""
    lines = [
        "MANTRA Optimal Retrieval Configurations",
        "=" * 50,
        "",
    ]

    for profile, config in OPTIMAL_CONFIGS.items():
        lines.append(f"{profile.value.upper()}:")
        lines.append(f"  Fusion: {config.fusion_method} ({config.vector_weight}/{config.keyword_weight})")
        lines.append(f"  Rerank: {config.rerank_method if config.rerank_enabled else 'disabled'}")
        lines.append(f"  RRF k: {config.rrf_k}")
        lines.append("")

    return "\n".join(lines)


# Default configuration for MANTRA (using best multi-agent result)
DEFAULT_CONFIG = OPTIMAL_CONFIGS[RetrievalProfile.MAX_ACCURACY]


__all__ = [
    "RetrievalProfile",
    "OptimalConfig",
    "OPTIMAL_CONFIGS",
    "QUERY_TYPE_ADJUSTMENTS",
    "DATASET_SIZE_ADJUSTMENTS",
    "get_optimal_config",
    "get_config_summary",
    "DEFAULT_CONFIG",
]
