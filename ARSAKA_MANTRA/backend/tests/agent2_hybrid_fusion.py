#!/usr/bin/env python3
"""
MANTRA Hybrid Fusion Exploration - Agent 2

Explores advanced HYBRID fusion approaches:
1. RRF + Linear in sequence (RRF first, then linear blend)
2. Weighted RRF (different weights for each source's RRF contribution)
3. Adaptive fusion (switch method based on query length)
4. CombSUM with normalization
5. Geometric mean fusion
6. Harmonic mean fusion

For each approach:
- 1000 test decisions
- 10 diverse queries
- 3 iterations per query
- Calculate relevance score
"""

import sys
import time
import random
import statistics
import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Callable
from enum import Enum
import json

# Set seed for reproducibility
random.seed(42)

# ============================================================================
# TEST DATA GENERATION
# ============================================================================

class DecisionDomain(str, Enum):
    INT = "INT"    # Integration
    ARCH = "ARCH"  # Architecture
    CTL = "CTL"    # Control
    EVO = "EVO"    # Evolution

TECH_TERMS = [
    "react", "vue", "angular", "typescript", "javascript", "python",
    "fastapi", "django", "flask", "postgresql", "mongodb", "redis",
    "docker", "kubernetes", "nomad", "graphql", "rest", "api",
    "authentication", "authorization", "jwt", "oauth", "rbac",
    "caching", "indexing", "optimization", "performance", "scaling",
    "testing", "ci/cd", "deployment", "monitoring", "logging",
    "microservices", "monolith", "event-driven", "cqrs", "ddd",
]

STATEMENT_TEMPLATES = [
    "All {tech1} components MUST use {tech2} for {purpose}",
    "When implementing {purpose}, developers SHALL use {tech1}",
    "{tech1} services MUST implement {tech2} patterns",
    "Database operations MUST use {tech1} with {tech2} caching",
    "Frontend {purpose} SHALL follow {tech1} conventions",
    "API endpoints MUST implement {tech2} for {purpose}",
]

PURPOSES = [
    "data fetching", "state management", "error handling",
    "form validation", "routing", "authorization",
    "caching", "logging", "monitoring", "testing",
]

def generate_decision(idx: int) -> Dict[str, Any]:
    """Generate a single test decision."""
    domain = random.choice(list(DecisionDomain))
    tech1 = random.choice(TECH_TERMS)
    tech2 = random.choice(TECH_TERMS)
    purpose = random.choice(PURPOSES)

    statement = random.choice(STATEMENT_TEMPLATES).format(
        tech1=tech1, tech2=tech2, purpose=purpose
    )
    rationale = f"This decision ensures consistency in {purpose}. Using {tech1} with {tech2} provides better maintainability."

    return {
        "decision_id": f"decision-{idx:05d}",
        "code": f"{domain.value}-F{(idx % 16) + 1:02d}",
        "domain_id": domain.value,
        "statement": statement,
        "rationale": rationale,
        "tags": list(set([tech1, tech2, purpose.split()[0]])),
    }

def generate_queries() -> List[Dict]:
    """Generate 10 diverse test queries."""
    return [
        {"query": "react components", "expected": ["react"]},
        {"query": "database caching", "expected": ["database", "caching"]},
        {"query": "api authentication", "expected": ["api", "authentication"]},
        {"query": "react state management redux", "expected": ["react", "state"]},
        {"query": "jwt authentication fastapi", "expected": ["jwt", "authentication"]},
        {"query": "postgresql indexing optimization", "expected": ["postgresql", "indexing"]},
        {"query": "kubernetes docker deployment", "expected": ["kubernetes", "docker"]},
        {"query": "microservices architecture", "expected": ["microservices"]},
        {"query": "event-driven design", "expected": ["event-driven"]},
        {"query": "security authorization rbac", "expected": ["authorization", "rbac"]},
    ]

# ============================================================================
# SEARCH SIMULATION (Term overlap for vector, exact match + tag bonus for keyword)
# ============================================================================

def simulate_vector_search(query: str, decisions: List[Dict]) -> Dict[str, float]:
    """
    Simulate vector search using term overlap.
    Vector similarity is approximated by Jaccard-like overlap.
    """
    query_terms = set(query.lower().split())
    scores = {}
    for d in decisions:
        doc_terms = set(
            d["statement"].lower().split() +
            d["rationale"].lower().split() +
            d.get("tags", [])
        )
        overlap = len(query_terms & doc_terms)
        total = len(query_terms | doc_terms)
        score = overlap / total if total > 0 else 0
        # Add small noise for realism
        noise = random.uniform(-0.1, 0.1)
        score = max(0, min(1, score + noise))
        if score > 0.05:
            scores[d["decision_id"]] = score
    return scores

def simulate_keyword_search(query: str, decisions: List[Dict]) -> Dict[str, float]:
    """
    Simulate keyword search with exact match + tag bonus.
    """
    query_terms = set(query.lower().split())
    scores = {}
    for d in decisions:
        score = 0.0
        text = (
            d["statement"].lower() + " " +
            d["rationale"].lower() + " " +
            " ".join(d.get("tags", []))
        )

        # Exact match scoring
        for term in query_terms:
            if f" {term} " in f" {text} ":
                score += 0.4  # Exact word match
            elif term in text:
                score += 0.2  # Partial match

        # Tag bonus
        for tag in d.get("tags", []):
            if tag.lower() in query_terms:
                score += 0.5

        score = min(1.0, score / len(query_terms)) if query_terms else 0
        if score > 0.05:
            scores[d["decision_id"]] = score
    return scores

def calculate_relevance(
    results: List[Tuple[str, float]],
    decisions: List[Dict],
    expected: List[str]
) -> float:
    """
    Calculate relevance score with weighted position scoring.
    Higher weight for top positions, diminishing for lower positions.
    """
    if not results:
        return 0.0

    decision_map = {d["decision_id"]: d for d in decisions}
    expected_lower = [t.lower() for t in expected]

    # Weighted position scoring (DCG-like)
    weights = [1.0, 0.8, 0.6, 0.4, 0.3, 0.2, 0.15, 0.1, 0.08, 0.05]

    total = 0.0
    for i, (doc_id, _) in enumerate(results[:10]):
        weight = weights[i] if i < len(weights) else 0.05
        if doc_id in decision_map:
            d = decision_map[doc_id]
            text = (
                d["statement"].lower() + " " +
                d["rationale"].lower() + " " +
                " ".join(d.get("tags", []))
            )
            matches = sum(1 for t in expected_lower if t in text)
            total += weight * (matches / len(expected_lower) if expected_lower else 0)

    max_possible = sum(weights[:len(results)])
    return total / max_possible if max_possible > 0 else 0

# ============================================================================
# BASIC FUSION METHODS (Building blocks)
# ============================================================================

def rrf_fusion(
    scores_list: List[Dict[str, float]],
    k: int = 60
) -> List[Tuple[str, float]]:
    """Standard RRF fusion."""
    rank_lists = []
    for scores in scores_list:
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(sorted_docs)}
        rank_lists.append(ranks)

    all_docs = set()
    for scores in scores_list:
        all_docs.update(scores.keys())

    rrf_scores = {}
    for doc_id in all_docs:
        score = 0.0
        for ranks in rank_lists:
            if doc_id in ranks:
                score += 1.0 / (k + ranks[doc_id])
        rrf_scores[doc_id] = score

    return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

def linear_fusion(
    scores_list: List[Dict[str, float]],
    weights: List[float]
) -> List[Tuple[str, float]]:
    """Standard linear weighted fusion."""
    all_docs = set()
    for scores in scores_list:
        all_docs.update(scores.keys())

    combined = {}
    for doc_id in all_docs:
        score = 0.0
        for i, scores in enumerate(scores_list):
            if doc_id in scores:
                score += weights[i] * scores[doc_id]
        combined[doc_id] = score

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

# ============================================================================
# HYBRID FUSION APPROACHES
# ============================================================================

def hybrid_rrf_then_linear(
    vector_scores: Dict[str, float],
    keyword_scores: Dict[str, float],
    rrf_k: int = 60,
    linear_weights: Tuple[float, float] = (0.6, 0.4)
) -> List[Tuple[str, float]]:
    """
    Approach 1: RRF first, then linear blend.
    RRF normalizes ranks, then linear combines with original scores.
    """
    # Step 1: RRF to get rank-normalized scores
    rrf_results = rrf_fusion([vector_scores, keyword_scores], k=rrf_k)
    rrf_dict = dict(rrf_results)

    # Normalize RRF scores to 0-1
    if rrf_dict:
        max_rrf = max(rrf_dict.values())
        min_rrf = min(rrf_dict.values())
        rrf_range = max_rrf - min_rrf if max_rrf != min_rrf else 1.0
        rrf_normalized = {k: (v - min_rrf) / rrf_range for k, v in rrf_dict.items()}
    else:
        rrf_normalized = {}

    # Step 2: Linear blend of RRF with original scores
    all_docs = set(rrf_normalized.keys())
    combined = {}
    for doc_id in all_docs:
        rrf_score = rrf_normalized.get(doc_id, 0)
        vec_score = vector_scores.get(doc_id, 0)
        kw_score = keyword_scores.get(doc_id, 0)

        # Blend: RRF provides structure, linear provides magnitude
        combined[doc_id] = (
            0.5 * rrf_score +
            linear_weights[0] * vec_score * 0.25 +
            linear_weights[1] * kw_score * 0.25
        )

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

def weighted_rrf(
    vector_scores: Dict[str, float],
    keyword_scores: Dict[str, float],
    k: int = 60,
    source_weights: Tuple[float, float] = (0.6, 0.4)
) -> List[Tuple[str, float]]:
    """
    Approach 2: Weighted RRF - different weights for each source's RRF contribution.
    """
    # Build rank lists
    vec_sorted = sorted(vector_scores.items(), key=lambda x: x[1], reverse=True)
    vec_ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(vec_sorted)}

    kw_sorted = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
    kw_ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(kw_sorted)}

    all_docs = set(vector_scores.keys()) | set(keyword_scores.keys())

    combined = {}
    for doc_id in all_docs:
        score = 0.0
        if doc_id in vec_ranks:
            score += source_weights[0] * (1.0 / (k + vec_ranks[doc_id]))
        if doc_id in kw_ranks:
            score += source_weights[1] * (1.0 / (k + kw_ranks[doc_id]))
        combined[doc_id] = score

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

def adaptive_fusion(
    query: str,
    vector_scores: Dict[str, float],
    keyword_scores: Dict[str, float],
    short_threshold: int = 2,
    long_threshold: int = 4,
    rrf_k: int = 60
) -> List[Tuple[str, float]]:
    """
    Approach 3: Adaptive fusion - switch method based on query length.
    - Short queries (<=2 words): Favor keyword (precise)
    - Medium queries (3-4 words): Balanced RRF
    - Long queries (>4 words): Favor vector (semantic)
    """
    query_length = len(query.split())

    if query_length <= short_threshold:
        # Short query: keyword-heavy linear
        return linear_fusion(
            [vector_scores, keyword_scores],
            weights=[0.3, 0.7]
        )
    elif query_length <= long_threshold:
        # Medium query: balanced RRF
        return rrf_fusion([vector_scores, keyword_scores], k=rrf_k)
    else:
        # Long query: vector-heavy linear
        return linear_fusion(
            [vector_scores, keyword_scores],
            weights=[0.7, 0.3]
        )

def combsum_normalized(
    vector_scores: Dict[str, float],
    keyword_scores: Dict[str, float]
) -> List[Tuple[str, float]]:
    """
    Approach 4: CombSUM with min-max normalization.
    Normalize each source to 0-1, then sum.
    """
    def normalize(scores: Dict[str, float]) -> Dict[str, float]:
        if not scores:
            return {}
        max_s = max(scores.values())
        min_s = min(scores.values())
        range_s = max_s - min_s if max_s != min_s else 1.0
        return {k: (v - min_s) / range_s for k, v in scores.items()}

    vec_norm = normalize(vector_scores)
    kw_norm = normalize(keyword_scores)

    all_docs = set(vec_norm.keys()) | set(kw_norm.keys())

    combined = {}
    for doc_id in all_docs:
        combined[doc_id] = vec_norm.get(doc_id, 0) + kw_norm.get(doc_id, 0)

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

def geometric_mean_fusion(
    vector_scores: Dict[str, float],
    keyword_scores: Dict[str, float],
    epsilon: float = 0.01
) -> List[Tuple[str, float]]:
    """
    Approach 5: Geometric mean fusion.
    sqrt(vec_score * kw_score) - emphasizes docs that score well in BOTH.
    """
    # Normalize first
    def normalize(scores: Dict[str, float]) -> Dict[str, float]:
        if not scores:
            return {}
        max_s = max(scores.values())
        min_s = min(scores.values())
        range_s = max_s - min_s if max_s != min_s else 1.0
        return {k: (v - min_s) / range_s + epsilon for k, v in scores.items()}

    vec_norm = normalize(vector_scores)
    kw_norm = normalize(keyword_scores)

    all_docs = set(vec_norm.keys()) | set(kw_norm.keys())

    combined = {}
    for doc_id in all_docs:
        v = vec_norm.get(doc_id, epsilon)
        k = kw_norm.get(doc_id, epsilon)
        combined[doc_id] = math.sqrt(v * k)

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

def harmonic_mean_fusion(
    vector_scores: Dict[str, float],
    keyword_scores: Dict[str, float],
    epsilon: float = 0.01
) -> List[Tuple[str, float]]:
    """
    Approach 6: Harmonic mean fusion.
    2 * vec * kw / (vec + kw) - penalizes if either source scores poorly.
    """
    def normalize(scores: Dict[str, float]) -> Dict[str, float]:
        if not scores:
            return {}
        max_s = max(scores.values())
        min_s = min(scores.values())
        range_s = max_s - min_s if max_s != min_s else 1.0
        return {k: (v - min_s) / range_s + epsilon for k, v in scores.items()}

    vec_norm = normalize(vector_scores)
    kw_norm = normalize(keyword_scores)

    all_docs = set(vec_norm.keys()) | set(kw_norm.keys())

    combined = {}
    for doc_id in all_docs:
        v = vec_norm.get(doc_id, epsilon)
        k = kw_norm.get(doc_id, epsilon)
        combined[doc_id] = 2 * v * k / (v + k) if (v + k) > 0 else 0

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

# ============================================================================
# HYBRID CONFIGURATION DATACLASS
# ============================================================================

@dataclass
class HybridConfig:
    """Configuration for a hybrid fusion approach."""
    name: str
    approach: str
    params: Dict[str, Any] = field(default_factory=dict)

    def describe(self) -> str:
        """Return human-readable description."""
        param_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.name} ({param_str})"

# ============================================================================
# EVALUATION ENGINE
# ============================================================================

def run_fusion_config(
    config: HybridConfig,
    decisions: List[Dict],
    queries: List[Dict],
    iterations: int = 3
) -> Tuple[float, float, float]:
    """
    Run a fusion configuration and return (avg_relevance, std_dev, avg_latency).
    """
    relevances = []
    latencies = []

    for q in queries:
        for _ in range(iterations):
            start = time.time()

            # Generate search results
            vector_scores = simulate_vector_search(q["query"], decisions)
            keyword_scores = simulate_keyword_search(q["query"], decisions)

            # Apply fusion based on approach
            if config.approach == "rrf_then_linear":
                results = hybrid_rrf_then_linear(
                    vector_scores, keyword_scores,
                    rrf_k=config.params.get("rrf_k", 60),
                    linear_weights=config.params.get("linear_weights", (0.6, 0.4))
                )
            elif config.approach == "weighted_rrf":
                results = weighted_rrf(
                    vector_scores, keyword_scores,
                    k=config.params.get("k", 60),
                    source_weights=config.params.get("source_weights", (0.5, 0.5))
                )
            elif config.approach == "adaptive":
                results = adaptive_fusion(
                    q["query"], vector_scores, keyword_scores,
                    short_threshold=config.params.get("short_threshold", 2),
                    long_threshold=config.params.get("long_threshold", 4),
                    rrf_k=config.params.get("rrf_k", 60)
                )
            elif config.approach == "combsum":
                results = combsum_normalized(vector_scores, keyword_scores)
            elif config.approach == "geometric":
                results = geometric_mean_fusion(
                    vector_scores, keyword_scores,
                    epsilon=config.params.get("epsilon", 0.01)
                )
            elif config.approach == "harmonic":
                results = harmonic_mean_fusion(
                    vector_scores, keyword_scores,
                    epsilon=config.params.get("epsilon", 0.01)
                )
            else:
                raise ValueError(f"Unknown approach: {config.approach}")

            latency = (time.time() - start) * 1000
            relevance = calculate_relevance(results, decisions, q["expected"])

            relevances.append(relevance)
            latencies.append(latency)

    avg_rel = statistics.mean(relevances)
    std_rel = statistics.stdev(relevances) if len(relevances) > 1 else 0
    avg_lat = statistics.mean(latencies)

    return avg_rel, std_rel, avg_lat

# ============================================================================
# MAIN EXPERIMENT
# ============================================================================

def main():
    print("=" * 80)
    print("MANTRA Hybrid Fusion Exploration - Agent 2")
    print("=" * 80)
    print()

    # Generate test data
    print("Generating test data...")
    decisions = [generate_decision(i) for i in range(1000)]
    queries = generate_queries()
    print(f"  Decisions: {len(decisions)}")
    print(f"  Queries: {len(queries)}")
    print(f"  Iterations per query: 3")
    print()

    all_results = []

    # =========================================================================
    # APPROACH 1: RRF + Linear in sequence
    # =========================================================================
    print("=" * 60)
    print("APPROACH 1: RRF + Linear in Sequence")
    print("-" * 60)

    rrf_k_values = [30, 60, 100]
    linear_weight_combos = [
        (0.5, 0.5), (0.6, 0.4), (0.7, 0.3), (0.4, 0.6)
    ]

    for rrf_k in rrf_k_values:
        for lw in linear_weight_combos:
            config = HybridConfig(
                name=f"RRF-k{rrf_k}+Linear({lw[0]:.1f},{lw[1]:.1f})",
                approach="rrf_then_linear",
                params={"rrf_k": rrf_k, "linear_weights": lw}
            )
            rel, std, lat = run_fusion_config(config, decisions, queries)
            all_results.append((config, rel, std, lat))
            print(f"  {config.name:40} | Rel: {rel:.4f} +/- {std:.4f} | Lat: {lat:.2f}ms")

    # =========================================================================
    # APPROACH 2: Weighted RRF
    # =========================================================================
    print("\n" + "=" * 60)
    print("APPROACH 2: Weighted RRF")
    print("-" * 60)

    k_values = [30, 60, 100]
    weight_combos = [
        (0.5, 0.5), (0.6, 0.4), (0.7, 0.3), (0.4, 0.6), (0.8, 0.2)
    ]

    for k in k_values:
        for sw in weight_combos:
            config = HybridConfig(
                name=f"WeightedRRF-k{k}({sw[0]:.1f},{sw[1]:.1f})",
                approach="weighted_rrf",
                params={"k": k, "source_weights": sw}
            )
            rel, std, lat = run_fusion_config(config, decisions, queries)
            all_results.append((config, rel, std, lat))
            print(f"  {config.name:40} | Rel: {rel:.4f} +/- {std:.4f} | Lat: {lat:.2f}ms")

    # =========================================================================
    # APPROACH 3: Adaptive Fusion
    # =========================================================================
    print("\n" + "=" * 60)
    print("APPROACH 3: Adaptive Fusion (query-length based)")
    print("-" * 60)

    threshold_combos = [
        (2, 4), (2, 3), (1, 3), (3, 5)
    ]
    adaptive_rrf_k = [30, 60, 100]

    for st, lt in threshold_combos:
        for k in adaptive_rrf_k:
            config = HybridConfig(
                name=f"Adaptive(short<={st},long>{lt})-k{k}",
                approach="adaptive",
                params={"short_threshold": st, "long_threshold": lt, "rrf_k": k}
            )
            rel, std, lat = run_fusion_config(config, decisions, queries)
            all_results.append((config, rel, std, lat))
            print(f"  {config.name:40} | Rel: {rel:.4f} +/- {std:.4f} | Lat: {lat:.2f}ms")

    # =========================================================================
    # APPROACH 4: CombSUM with normalization
    # =========================================================================
    print("\n" + "=" * 60)
    print("APPROACH 4: CombSUM with Normalization")
    print("-" * 60)

    config = HybridConfig(
        name="CombSUM-Normalized",
        approach="combsum",
        params={}
    )
    rel, std, lat = run_fusion_config(config, decisions, queries)
    all_results.append((config, rel, std, lat))
    print(f"  {config.name:40} | Rel: {rel:.4f} +/- {std:.4f} | Lat: {lat:.2f}ms")

    # =========================================================================
    # APPROACH 5: Geometric Mean Fusion
    # =========================================================================
    print("\n" + "=" * 60)
    print("APPROACH 5: Geometric Mean Fusion")
    print("-" * 60)

    epsilon_values = [0.001, 0.01, 0.05, 0.1]
    for eps in epsilon_values:
        config = HybridConfig(
            name=f"GeometricMean-eps{eps}",
            approach="geometric",
            params={"epsilon": eps}
        )
        rel, std, lat = run_fusion_config(config, decisions, queries)
        all_results.append((config, rel, std, lat))
        print(f"  {config.name:40} | Rel: {rel:.4f} +/- {std:.4f} | Lat: {lat:.2f}ms")

    # =========================================================================
    # APPROACH 6: Harmonic Mean Fusion
    # =========================================================================
    print("\n" + "=" * 60)
    print("APPROACH 6: Harmonic Mean Fusion")
    print("-" * 60)

    for eps in epsilon_values:
        config = HybridConfig(
            name=f"HarmonicMean-eps{eps}",
            approach="harmonic",
            params={"epsilon": eps}
        )
        rel, std, lat = run_fusion_config(config, decisions, queries)
        all_results.append((config, rel, std, lat))
        print(f"  {config.name:40} | Rel: {rel:.4f} +/- {std:.4f} | Lat: {lat:.2f}ms")

    # =========================================================================
    # FINAL RESULTS
    # =========================================================================
    print("\n" + "=" * 80)
    print("FINAL RESULTS: TOP 15 HYBRID CONFIGURATIONS")
    print("=" * 80)

    # Sort by relevance
    all_sorted = sorted(all_results, key=lambda x: x[1], reverse=True)

    print(f"\n{'Rank':<5} {'Configuration':<50} {'Relevance':>10} {'StdDev':>10} {'Latency':>10}")
    print("-" * 90)

    for i, (config, rel, std, lat) in enumerate(all_sorted[:15], 1):
        print(f"{i:<5} {config.name:<50} {rel:>10.4f} {std:>10.4f} {lat:>8.2f}ms")

    # Group by approach for analysis
    print("\n" + "=" * 80)
    print("BEST BY APPROACH TYPE")
    print("=" * 80)

    approach_groups = {}
    for config, rel, std, lat in all_results:
        if config.approach not in approach_groups:
            approach_groups[config.approach] = []
        approach_groups[config.approach].append((config, rel, std, lat))

    best_by_approach = {}
    for approach, results in approach_groups.items():
        best = max(results, key=lambda x: x[1])
        best_by_approach[approach] = best
        config, rel, std, lat = best
        print(f"\n{approach.upper():20} | Best: {config.name}")
        print(f"{'':20} | Relevance: {rel:.4f} +/- {std:.4f} | Latency: {lat:.2f}ms")
        print(f"{'':20} | Params: {config.params}")

    # =========================================================================
    # OPTIMAL CONFIGURATION
    # =========================================================================
    best_overall = all_sorted[0]
    best_config, best_rel, best_std, best_lat = best_overall

    print("\n" + "=" * 80)
    print("OPTIMAL HYBRID CONFIGURATION FOUND")
    print("=" * 80)

    print(f"""
Configuration: {best_config.name}
Approach:      {best_config.approach}
Relevance:     {best_rel:.4f} (+/- {best_std:.4f})
Latency:       {best_lat:.2f}ms

Parameters:
{json.dumps(best_config.params, indent=2)}

Python Implementation:
```python
def optimal_hybrid_fusion(vector_scores, keyword_scores):
""")

    # Generate code based on best approach
    if best_config.approach == "rrf_then_linear":
        print(f'''    """RRF + Linear Sequence Fusion (OPTIMAL)"""
    rrf_k = {best_config.params.get("rrf_k", 60)}
    linear_weights = {best_config.params.get("linear_weights", (0.6, 0.4))}

    # Step 1: RRF for rank normalization
    rrf_results = rrf_fusion([vector_scores, keyword_scores], k=rrf_k)
    rrf_dict = dict(rrf_results)

    # Normalize RRF scores
    max_rrf = max(rrf_dict.values())
    min_rrf = min(rrf_dict.values())
    rrf_range = max_rrf - min_rrf if max_rrf != min_rrf else 1.0
    rrf_normalized = {{k: (v - min_rrf) / rrf_range for k, v in rrf_dict.items()}}

    # Step 2: Blend RRF with original scores
    combined = {{}}
    for doc_id in rrf_normalized.keys():
        combined[doc_id] = (
            0.5 * rrf_normalized.get(doc_id, 0) +
            linear_weights[0] * vector_scores.get(doc_id, 0) * 0.25 +
            linear_weights[1] * keyword_scores.get(doc_id, 0) * 0.25
        )

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)
```''')
    elif best_config.approach == "weighted_rrf":
        print(f'''    """Weighted RRF Fusion (OPTIMAL)"""
    k = {best_config.params.get("k", 60)}
    source_weights = {best_config.params.get("source_weights", (0.5, 0.5))}

    # Build rank lists
    vec_ranks = {{doc: i+1 for i, (doc, _) in enumerate(
        sorted(vector_scores.items(), key=lambda x: x[1], reverse=True)
    )}}
    kw_ranks = {{doc: i+1 for i, (doc, _) in enumerate(
        sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
    )}}

    # Weighted RRF
    combined = {{}}
    for doc_id in set(vector_scores.keys()) | set(keyword_scores.keys()):
        score = 0.0
        if doc_id in vec_ranks:
            score += source_weights[0] * (1.0 / (k + vec_ranks[doc_id]))
        if doc_id in kw_ranks:
            score += source_weights[1] * (1.0 / (k + kw_ranks[doc_id]))
        combined[doc_id] = score

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)
```''')
    elif best_config.approach == "adaptive":
        print(f'''    """Adaptive Fusion (OPTIMAL)"""
    short_threshold = {best_config.params.get("short_threshold", 2)}
    long_threshold = {best_config.params.get("long_threshold", 4)}
    rrf_k = {best_config.params.get("rrf_k", 60)}

    query_length = len(query.split())

    if query_length <= short_threshold:
        # Short query: keyword-heavy
        return linear_fusion([vector_scores, keyword_scores], [0.3, 0.7])
    elif query_length <= long_threshold:
        # Medium: balanced RRF
        return rrf_fusion([vector_scores, keyword_scores], k=rrf_k)
    else:
        # Long: vector-heavy
        return linear_fusion([vector_scores, keyword_scores], [0.7, 0.3])
```''')
    elif best_config.approach == "combsum":
        print('''    """CombSUM Normalized Fusion (OPTIMAL)"""
    def normalize(scores):
        if not scores: return {}
        max_s, min_s = max(scores.values()), min(scores.values())
        range_s = max_s - min_s if max_s != min_s else 1.0
        return {k: (v - min_s) / range_s for k, v in scores.items()}

    vec_norm = normalize(vector_scores)
    kw_norm = normalize(keyword_scores)

    combined = {}
    for doc_id in set(vec_norm.keys()) | set(kw_norm.keys()):
        combined[doc_id] = vec_norm.get(doc_id, 0) + kw_norm.get(doc_id, 0)

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)
```''')
    elif best_config.approach == "geometric":
        eps = best_config.params.get("epsilon", 0.01)
        print(f'''    """Geometric Mean Fusion (OPTIMAL)"""
    epsilon = {eps}

    def normalize(scores):
        if not scores: return {{}}
        max_s, min_s = max(scores.values()), min(scores.values())
        range_s = max_s - min_s if max_s != min_s else 1.0
        return {{k: (v - min_s) / range_s + epsilon for k, v in scores.items()}}

    vec_norm = normalize(vector_scores)
    kw_norm = normalize(keyword_scores)

    combined = {{}}
    for doc_id in set(vec_norm.keys()) | set(kw_norm.keys()):
        v = vec_norm.get(doc_id, epsilon)
        k = kw_norm.get(doc_id, epsilon)
        combined[doc_id] = math.sqrt(v * k)

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)
```''')
    elif best_config.approach == "harmonic":
        eps = best_config.params.get("epsilon", 0.01)
        print(f'''    """Harmonic Mean Fusion (OPTIMAL)"""
    epsilon = {eps}

    def normalize(scores):
        if not scores: return {{}}
        max_s, min_s = max(scores.values()), min(scores.values())
        range_s = max_s - min_s if max_s != min_s else 1.0
        return {{k: (v - min_s) / range_s + epsilon for k, v in scores.items()}}

    vec_norm = normalize(vector_scores)
    kw_norm = normalize(keyword_scores)

    combined = {{}}
    for doc_id in set(vec_norm.keys()) | set(kw_norm.keys()):
        v = vec_norm.get(doc_id, epsilon)
        k = kw_norm.get(doc_id, epsilon)
        combined[doc_id] = 2 * v * k / (v + k) if (v + k) > 0 else 0

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)
```''')

    # Save results to JSON
    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_config": {
            "decisions": 1000,
            "queries": len(queries),
            "iterations_per_query": 3,
        },
        "best_config": {
            "name": best_config.name,
            "approach": best_config.approach,
            "params": best_config.params,
            "relevance": best_rel,
            "std_dev": best_std,
            "latency_ms": best_lat,
        },
        "best_by_approach": {
            approach: {
                "name": cfg.name,
                "params": cfg.params,
                "relevance": rel,
                "std_dev": std,
                "latency_ms": lat,
            }
            for approach, (cfg, rel, std, lat) in best_by_approach.items()
        },
        "all_results": [
            {
                "name": cfg.name,
                "approach": cfg.approach,
                "params": cfg.params,
                "relevance": rel,
                "std_dev": std,
                "latency_ms": lat,
            }
            for cfg, rel, std, lat in all_sorted
        ]
    }

    output_path = "/mnt/f/WINDSURF/neliti_code/signate/ARSAKA_MANTRA/backend/tests/hybrid_fusion_results.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n\nResults saved to: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
