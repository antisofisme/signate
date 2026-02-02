#!/usr/bin/env python3
"""
MANTRA Fine-Grained Weight Grid Search

Fine-grained search for optimal vector/keyword weights:
- Vector weights: 0.0 to 0.3 (step 0.05) - exploring around 10/90
- Keyword weights: 0.7 to 1.0 (step 0.05)
- Includes combinations like 0.05/0.95, 0.15/0.85, etc.
- 3 iterations per config for statistical significance
- Reports top 10 configurations with relevance scores

Run: python tests/agent1_fine_weights.py
"""

import sys
import time
import random
import statistics
import hashlib
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from enum import Enum

# Set seed for reproducibility of test data generation
random.seed(42)


# ============================================================================
# TEST DATA GENERATOR (Same as stress test)
# ============================================================================

class DecisionDomain(str, Enum):
    INT = "INT"
    ARCH = "ARCH"
    CTL = "CTL"
    EVO = "EVO"


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
    """Generate test queries with expected terms."""
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
        {"query": "graphql api patterns", "expected": ["graphql", "api"]},
        {"query": "python fastapi backend", "expected": ["python", "fastapi"]},
        {"query": "typescript frontend components", "expected": ["typescript", "frontend"]},
        {"query": "redis caching performance", "expected": ["redis", "caching"]},
        {"query": "ci/cd deployment pipeline", "expected": ["ci/cd", "deployment"]},
    ]


# ============================================================================
# SEARCH SIMULATION WITH DETERMINISTIC NOISE
# ============================================================================

def get_deterministic_noise(doc_id: str, query: str, search_type: str, iteration: int) -> float:
    """
    Generate deterministic noise based on document, query, search type, and iteration.
    This ensures:
    - Same noise for same doc+query+search_type+iteration combination
    - Different noise for vector vs keyword search (different search_type)
    - Reproducible across runs
    """
    seed_str = f"{doc_id}:{query}:{search_type}:{iteration}"
    hash_val = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    # Map to [-0.1, 0.1] range
    return (hash_val % 2001 - 1000) / 10000.0


def simulate_vector_search(
    query: str,
    decisions: List[Dict],
    iteration: int = 0
) -> Dict[str, float]:
    """
    Simulate vector search using term overlap + deterministic noise.
    Vector search captures semantic similarity with embedding variance.
    """
    query_terms = set(query.lower().split())
    scores = {}

    for d in decisions:
        # Combine all searchable text
        doc_terms = set(
            d["statement"].lower().split() +
            d["rationale"].lower().split() +
            d.get("tags", [])
        )

        # Calculate Jaccard-like overlap
        overlap = len(query_terms & doc_terms)
        total = len(query_terms | doc_terms)
        base_score = overlap / total if total > 0 else 0

        # Add deterministic noise to simulate embedding variance
        noise = get_deterministic_noise(d["decision_id"], query, "vector", iteration)
        score = max(0, min(1, base_score + noise))

        if score > 0.05:
            scores[d["decision_id"]] = score

    return scores


def simulate_keyword_search(
    query: str,
    decisions: List[Dict],
    iteration: int = 0
) -> Dict[str, float]:
    """
    Simulate keyword search with exact match scoring and tag bonus.
    Keyword search rewards exact term matches with deterministic BM25-like variance.
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

        # Exact word match scoring
        for term in query_terms:
            if f" {term} " in f" {text} ":  # Word boundary match
                score += 0.4
            elif term in text:  # Partial match
                score += 0.2

        # Tag bonus - tags are high-signal for relevance
        for tag in d.get("tags", []):
            if tag.lower() in query_terms:
                score += 0.5

        # Normalize by query length
        score = min(1.0, score / len(query_terms)) if query_terms else 0

        # Add deterministic noise (different from vector search)
        noise = get_deterministic_noise(d["decision_id"], query, "keyword", iteration)
        score = max(0, min(1, score + noise * 0.5))  # Less noise for keyword search

        if score > 0.05:
            scores[d["decision_id"]] = score

    return scores


def calculate_relevance(
    results: List[Tuple[str, float]],
    decisions: List[Dict],
    expected: List[str]
) -> float:
    """
    Calculate relevance score using weighted position scoring.
    Higher positions get more weight (NDCG-like).
    """
    if not results:
        return 0.0

    decision_map = {d["decision_id"]: d for d in decisions}
    expected_lower = [t.lower() for t in expected]

    # Position weights (higher weight for top results)
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

            # Count how many expected terms appear
            matches = sum(1 for t in expected_lower if t in text)
            total += weight * (matches / len(expected_lower) if expected_lower else 0)

    max_possible = sum(weights[:min(len(results), 10)])
    return total / max_possible if max_possible > 0 else 0


# ============================================================================
# FUSION METHOD
# ============================================================================

def linear_fusion(
    vector_scores: Dict[str, float],
    keyword_scores: Dict[str, float],
    vector_weight: float,
    keyword_weight: float
) -> List[Tuple[str, float]]:
    """
    Combine vector and keyword scores using linear interpolation.
    """
    all_docs = set(vector_scores.keys()) | set(keyword_scores.keys())

    combined = {}
    for doc_id in all_docs:
        v_score = vector_scores.get(doc_id, 0.0)
        k_score = keyword_scores.get(doc_id, 0.0)
        combined[doc_id] = vector_weight * v_score + keyword_weight * k_score

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)


# ============================================================================
# GRID SEARCH CONFIG
# ============================================================================

@dataclass
class WeightConfig:
    """Configuration for a single weight combination."""
    vector_weight: float
    keyword_weight: float

    @property
    def name(self) -> str:
        return f"V{int(self.vector_weight*100):02d}/K{int(self.keyword_weight*100):02d}"


@dataclass
class Result:
    """Result for a single configuration."""
    config: WeightConfig
    avg_relevance: float
    std_relevance: float
    min_relevance: float
    max_relevance: float
    avg_latency_ms: float
    iterations: int


def run_configuration(
    config: WeightConfig,
    decisions: List[Dict],
    queries: List[Dict],
    iterations: int = 3
) -> Result:
    """Run a single configuration multiple times and return statistics."""
    relevances = []
    latencies = []

    for iteration in range(iterations):
        for q in queries:
            start = time.time()

            # Run searches with deterministic noise based on iteration
            vector_scores = simulate_vector_search(q["query"], decisions, iteration)
            keyword_scores = simulate_keyword_search(q["query"], decisions, iteration)

            # Fuse results
            fused = linear_fusion(
                vector_scores,
                keyword_scores,
                config.vector_weight,
                config.keyword_weight
            )

            # Calculate metrics
            latency_ms = (time.time() - start) * 1000
            relevance = calculate_relevance(fused, decisions, q["expected"])

            relevances.append(relevance)
            latencies.append(latency_ms)

    return Result(
        config=config,
        avg_relevance=statistics.mean(relevances),
        std_relevance=statistics.stdev(relevances) if len(relevances) > 1 else 0,
        min_relevance=min(relevances),
        max_relevance=max(relevances),
        avg_latency_ms=statistics.mean(latencies),
        iterations=iterations * len(queries),
    )


def generate_weight_configs() -> List[WeightConfig]:
    """
    Generate all weight configurations for fine-grained grid search.

    Vector weights: 0.0 to 0.3 with 0.05 step (7 values)
    Keyword weights: 0.7 to 1.0 with 0.05 step (7 values)

    Only valid combinations where vector + keyword = 1.0
    """
    configs = []

    # Vector from 0.0 to 0.30 in 0.05 steps
    vector_weights = [i * 0.05 for i in range(0, 7)]  # 0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30

    for vw in vector_weights:
        kw = 1.0 - vw
        # Round to avoid floating point issues
        kw = round(kw, 2)

        if 0.7 <= kw <= 1.0:
            configs.append(WeightConfig(
                vector_weight=round(vw, 2),
                keyword_weight=kw
            ))

    return configs


def generate_extended_weight_configs() -> List[WeightConfig]:
    """
    Generate extended weight configurations with finer granularity.

    Includes:
    - 0.00 to 0.30 with 0.01 step for high precision
    """
    configs = []

    # Fine-grained: 0.00 to 0.30 in 0.01 steps (31 values)
    for i in range(0, 31):
        vw = i * 0.01
        kw = round(1.0 - vw, 2)

        configs.append(WeightConfig(
            vector_weight=round(vw, 2),
            keyword_weight=kw
        ))

    return configs


def main():
    print("=" * 80)
    print("MANTRA Fine-Grained Weight Grid Search")
    print("=" * 80)
    print()
    print("Testing vector weights from 0.00 to 0.30 (step 0.01)")
    print("With corresponding keyword weights from 0.70 to 1.00")
    print("3 iterations per configuration for statistical significance")
    print()

    # Generate test data (with fixed seed for reproducibility)
    print("Generating test data...")
    random.seed(42)
    decisions = [generate_decision(i) for i in range(1000)]
    queries = generate_queries()
    print(f"  Decisions: {len(decisions)}")
    print(f"  Queries: {len(queries)}")

    # Generate configurations - use extended for finer granularity
    configs = generate_extended_weight_configs()
    print(f"  Configurations to test: {len(configs)}")
    print()

    # Run grid search with 5 iterations for better statistical significance
    ITERATIONS = 5
    print(f"Running grid search ({ITERATIONS} iterations per config)...")
    print("-" * 80)
    print(f"{'Config':<15} {'Relevance':>12} {'StdDev':>10} {'Min':>8} {'Max':>8} {'Latency':>10}")
    print("-" * 80)

    results: List[Result] = []

    for i, config in enumerate(configs):
        result = run_configuration(config, decisions, queries, iterations=ITERATIONS)
        results.append(result)

        print(
            f"{config.name:<15} "
            f"{result.avg_relevance:>12.6f} "
            f"{result.std_relevance:>10.6f} "
            f"{result.min_relevance:>8.4f} "
            f"{result.max_relevance:>8.4f} "
            f"{result.avg_latency_ms:>8.2f}ms"
        )

    # Sort by average relevance (descending)
    results_sorted = sorted(results, key=lambda r: r.avg_relevance, reverse=True)

    print()
    print("=" * 80)
    print("TOP 10 CONFIGURATIONS (by relevance)")
    print("=" * 80)
    print()
    print(f"{'Rank':<6} {'Config':<15} {'Vector':>8} {'Keyword':>8} {'Relevance':>12} {'StdDev':>10}")
    print("-" * 80)

    for i, result in enumerate(results_sorted[:10], 1):
        print(
            f"{i:<6} "
            f"{result.config.name:<15} "
            f"{result.config.vector_weight:>8.2f} "
            f"{result.config.keyword_weight:>8.2f} "
            f"{result.avg_relevance:>12.6f} "
            f"{result.std_relevance:>10.6f}"
        )

    # Best configuration
    best = results_sorted[0]

    print()
    print("=" * 80)
    print("BEST CONFIGURATION")
    print("=" * 80)
    print(f"""
Configuration:  {best.config.name}
Vector Weight:  {best.config.vector_weight:.2f}
Keyword Weight: {best.config.keyword_weight:.2f}

Performance:
  Average Relevance: {best.avg_relevance:.6f}
  Std Deviation:     {best.std_relevance:.6f}
  Min Relevance:     {best.min_relevance:.6f}
  Max Relevance:     {best.max_relevance:.6f}
  Avg Latency:       {best.avg_latency_ms:.2f}ms

Total iterations per config: {best.iterations}

Python Configuration:
```python
OPTIMAL_CONFIG = {{
    "vector_weight": {best.config.vector_weight},
    "keyword_weight": {best.config.keyword_weight},
}}
```
""")

    # Statistical comparison with baseline (0.10/0.90)
    baseline_result = next(
        (r for r in results if r.config.vector_weight == 0.10),
        None
    )

    if baseline_result:
        improvement = (best.avg_relevance - baseline_result.avg_relevance) / baseline_result.avg_relevance * 100
        print(f"Comparison with 10/90 baseline:")
        print(f"  Baseline (V10/K90) relevance: {baseline_result.avg_relevance:.6f}")
        print(f"  Best relevance:               {best.avg_relevance:.6f}")
        print(f"  Improvement:                  {improvement:+.2f}%")

    print()
    print("=" * 80)

    # Additional analysis: show the 0.05 step configs
    print()
    print("ANALYSIS: 0.05 STEP CONFIGURATIONS")
    print("-" * 80)
    step_05_weights = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
    print(f"{'Config':<15} {'Vector':>8} {'Keyword':>8} {'Relevance':>12} {'StdDev':>10} {'Rank':>6}")
    print("-" * 80)

    for vw in step_05_weights:
        r = next((r for r in results if abs(r.config.vector_weight - vw) < 0.001), None)
        if r:
            rank = results_sorted.index(r) + 1
            print(
                f"{r.config.name:<15} "
                f"{r.config.vector_weight:>8.2f} "
                f"{r.config.keyword_weight:>8.2f} "
                f"{r.avg_relevance:>12.6f} "
                f"{r.std_relevance:>10.6f} "
                f"#{rank:>4}"
            )

    print()
    print("=" * 80)

    return results_sorted


if __name__ == "__main__":
    main()
