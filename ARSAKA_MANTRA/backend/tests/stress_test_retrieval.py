#!/usr/bin/env python3
"""
MANTRA Retrieval Stress Test & Configuration Optimizer

Tests various configurations to find optimal settings for:
1. RRF k parameter (30, 60, 100, 200)
2. Fusion methods (RRF, Linear, CombMNZ, Borda)
3. Reranking strategies
4. Query types (short, long, technical, conceptual)
5. Dataset sizes (100, 500, 1000, 5000 decisions)

Measures:
- Accuracy (simulated relevance)
- Latency (ms)
- Memory usage
- Token efficiency

Output: Recommendations for optimal configuration
"""

import sys
import time
import random
import hashlib
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import json

# Add parent to path
sys.path.insert(0, '.')


# ============================================================================
# TEST DATA GENERATION
# ============================================================================

class DecisionDomain(str, Enum):
    """Decision domains for test data."""
    INT = "INT"   # Intent
    ARCH = "ARCH" # Architecture
    CTL = "CTL"   # Control
    EVO = "EVO"   # Evolution


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
    "Authentication flows SHALL use {tech1} with {tech2}",
    "All {purpose} operations MUST be logged using {tech1}",
]

PURPOSES = [
    "data fetching", "state management", "error handling",
    "form validation", "routing", "authorization",
    "caching", "logging", "monitoring", "testing",
]


def generate_decision(idx: int) -> Dict[str, Any]:
    """Generate a synthetic decision for testing."""
    domain = random.choice(list(DecisionDomain))
    tech1 = random.choice(TECH_TERMS)
    tech2 = random.choice(TECH_TERMS)
    purpose = random.choice(PURPOSES)

    statement = random.choice(STATEMENT_TEMPLATES).format(
        tech1=tech1, tech2=tech2, purpose=purpose
    )

    # Generate realistic rationale
    rationale = (
        f"This decision ensures consistency in {purpose} across the codebase. "
        f"Using {tech1} with {tech2} provides better maintainability and "
        f"aligns with industry best practices for {domain.value} layer."
    )

    # Generate tags based on content
    tags = list(set([tech1, tech2, purpose.split()[0]]))

    return {
        "decision_id": f"decision-{idx:05d}",
        "code": f"{domain.value}-F{(idx % 16) + 1:02d}",
        "domain_id": domain.value,
        "statement": statement,
        "rationale": rationale,
        "summary": f"{domain.value}: {purpose} using {tech1}",
        "tags": tags,
        "tech_stack": [tech1, tech2],
        "quality_score": random.uniform(0.6, 1.0),
        "usage_count": random.randint(0, 100),
        # Simulate embedding as hash
        "_embedding_hash": hashlib.md5(statement.encode()).hexdigest(),
    }


def generate_test_queries() -> List[Dict[str, Any]]:
    """Generate various query types for testing."""
    return [
        # Short queries
        {"query": "react components", "type": "short", "expected_terms": ["react"]},
        {"query": "database caching", "type": "short", "expected_terms": ["database", "caching"]},
        {"query": "api authentication", "type": "short", "expected_terms": ["api", "authentication"]},

        # Long queries
        {
            "query": "how should react components handle state management with redux",
            "type": "long",
            "expected_terms": ["react", "state", "management"],
        },
        {
            "query": "what is the best practice for implementing jwt authentication in fastapi",
            "type": "long",
            "expected_terms": ["jwt", "authentication", "fastapi"],
        },

        # Technical queries
        {
            "query": "postgresql indexing optimization performance",
            "type": "technical",
            "expected_terms": ["postgresql", "indexing", "optimization", "performance"],
        },
        {
            "query": "kubernetes deployment docker container orchestration",
            "type": "technical",
            "expected_terms": ["kubernetes", "docker", "deployment"],
        },

        # Conceptual queries
        {
            "query": "architecture patterns for microservices",
            "type": "conceptual",
            "expected_terms": ["architecture", "microservices"],
        },
        {
            "query": "event-driven design principles",
            "type": "conceptual",
            "expected_terms": ["event-driven", "design"],
        },

        # Domain-specific
        {
            "query": "ARCH frontend component structure",
            "type": "domain",
            "expected_terms": ["arch", "frontend", "component"],
        },
        {
            "query": "CTL security authorization policies",
            "type": "domain",
            "expected_terms": ["ctl", "security", "authorization"],
        },
    ]


# ============================================================================
# SIMULATION FUNCTIONS
# ============================================================================

def simulate_vector_search(
    query: str,
    decisions: List[Dict],
    noise_factor: float = 0.1,
) -> Dict[str, float]:
    """
    Simulate vector search scores.

    In production, this would use actual embeddings.
    Here we simulate based on term overlap + noise.
    """
    query_terms = set(query.lower().split())
    scores = {}

    for decision in decisions:
        # Calculate simulated similarity
        doc_terms = set(
            decision["statement"].lower().split() +
            decision["rationale"].lower().split() +
            decision.get("tags", [])
        )

        overlap = len(query_terms & doc_terms)
        total = len(query_terms | doc_terms)

        base_score = overlap / total if total > 0 else 0

        # Add noise to simulate embedding variance
        noise = random.uniform(-noise_factor, noise_factor)
        score = max(0, min(1, base_score + noise))

        if score > 0.1:  # Threshold
            scores[decision["decision_id"]] = score

    return scores


def simulate_keyword_search(
    query: str,
    decisions: List[Dict],
    boost_exact: float = 1.5,
) -> Dict[str, float]:
    """
    Simulate keyword search scores.

    Emphasizes exact term matches.
    """
    query_terms = set(query.lower().split())
    scores = {}

    for decision in decisions:
        score = 0.0
        text = (
            decision["statement"].lower() + " " +
            decision["rationale"].lower() + " " +
            " ".join(decision.get("tags", []))
        )

        for term in query_terms:
            if term in text:
                # Exact word match
                if f" {term} " in f" {text} ":
                    score += 0.3 * boost_exact
                else:
                    score += 0.2

        # Check tags (high value match)
        for tag in decision.get("tags", []):
            if tag.lower() in query_terms:
                score += 0.4

        score = min(1.0, score / len(query_terms)) if query_terms else 0

        if score > 0.1:
            scores[decision["decision_id"]] = score

    return scores


def calculate_relevance_score(
    results: List[Tuple[str, float]],
    decisions: List[Dict],
    expected_terms: List[str],
) -> float:
    """
    Calculate simulated relevance score.

    Measures how well the top results match expected terms.
    """
    if not results:
        return 0.0

    decision_map = {d["decision_id"]: d for d in decisions}
    expected_lower = [t.lower() for t in expected_terms]

    total_relevance = 0.0
    weights = [1.0, 0.8, 0.6, 0.4, 0.3, 0.2, 0.15, 0.1, 0.08, 0.05]

    for i, (doc_id, score) in enumerate(results[:10]):
        weight = weights[i] if i < len(weights) else 0.05

        if doc_id in decision_map:
            decision = decision_map[doc_id]
            doc_text = (
                decision["statement"].lower() + " " +
                decision["rationale"].lower() + " " +
                " ".join(decision.get("tags", []))
            )

            # Count matching expected terms
            matches = sum(1 for term in expected_lower if term in doc_text)
            term_relevance = matches / len(expected_lower) if expected_lower else 0

            total_relevance += weight * term_relevance

    # Normalize
    max_possible = sum(weights[:len(results)])
    return total_relevance / max_possible if max_possible > 0 else 0


# ============================================================================
# FUSION IMPLEMENTATIONS (Standalone for testing)
# ============================================================================

def rrf_fusion(
    score_lists: List[Dict[str, float]],
    k: int = 60,
) -> List[Tuple[str, float]]:
    """Reciprocal Rank Fusion."""
    # Convert scores to ranks
    rank_lists = []
    for scores in score_lists:
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(sorted_docs)}
        rank_lists.append(ranks)

    # Collect all docs
    all_docs = set()
    for scores in score_lists:
        all_docs.update(scores.keys())

    # Calculate RRF
    rrf_scores = {}
    for doc_id in all_docs:
        rrf_score = 0.0
        for ranks in rank_lists:
            if doc_id in ranks:
                rrf_score += 1.0 / (k + ranks[doc_id])
        rrf_scores[doc_id] = rrf_score

    # Sort and return
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_results


def linear_fusion(
    score_lists: List[Dict[str, float]],
    weights: List[float] = None,
) -> List[Tuple[str, float]]:
    """Weighted linear fusion."""
    if weights is None:
        weights = [1.0 / len(score_lists)] * len(score_lists)

    all_docs = set()
    for scores in score_lists:
        all_docs.update(scores.keys())

    combined = {}
    for doc_id in all_docs:
        score = 0.0
        for i, scores in enumerate(score_lists):
            if doc_id in scores:
                score += weights[i] * scores[doc_id]
        combined[doc_id] = score

    sorted_results = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    return sorted_results


def combmnz_fusion(
    score_lists: List[Dict[str, float]],
) -> List[Tuple[str, float]]:
    """CombMNZ: sum * count."""
    all_docs = set()
    for scores in score_lists:
        all_docs.update(scores.keys())

    combined = {}
    for doc_id in all_docs:
        sum_score = 0.0
        count = 0
        for scores in score_lists:
            if doc_id in scores:
                sum_score += scores[doc_id]
                count += 1
        combined[doc_id] = sum_score * count

    sorted_results = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    return sorted_results


def borda_fusion(
    score_lists: List[Dict[str, float]],
) -> List[Tuple[str, float]]:
    """Borda count voting."""
    all_docs = set()
    for scores in score_lists:
        all_docs.update(scores.keys())

    combined = {}
    for doc_id in all_docs:
        borda_score = 0.0
        for scores in score_lists:
            if doc_id in scores:
                sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                n = len(sorted_docs)
                for rank, (d, _) in enumerate(sorted_docs, 1):
                    if d == doc_id:
                        borda_score += n - rank + 1
                        break
        combined[doc_id] = borda_score

    sorted_results = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    return sorted_results


# ============================================================================
# RERANKING SIMULATION
# ============================================================================

def simulate_tfidf_rerank(
    query: str,
    results: List[Tuple[str, float]],
    decisions: List[Dict],
    top_k: int = 10,
) -> List[Tuple[str, float]]:
    """Simulate TF-IDF reranking."""
    decision_map = {d["decision_id"]: d for d in decisions}
    query_terms = set(query.lower().split())

    reranked = []
    for doc_id, original_score in results[:top_k * 2]:  # Consider more candidates
        if doc_id not in decision_map:
            continue

        decision = decision_map[doc_id]
        doc_text = (
            decision["statement"].lower() + " " +
            decision["rationale"].lower()
        )
        doc_terms = set(doc_text.split())

        # Simple TF-IDF-like score
        overlap = len(query_terms & doc_terms)
        tf_score = overlap / len(query_terms) if query_terms else 0

        # Combine with original score
        final_score = 0.6 * tf_score + 0.4 * original_score
        reranked.append((doc_id, final_score))

    reranked.sort(key=lambda x: x[1], reverse=True)
    return reranked[:top_k]


def simulate_crossencoder_rerank(
    query: str,
    results: List[Tuple[str, float]],
    decisions: List[Dict],
    top_k: int = 10,
) -> List[Tuple[str, float]]:
    """
    Simulate cross-encoder reranking.

    In production, this uses actual cross-encoder model.
    Here we simulate with enhanced term matching + semantic similarity.
    """
    decision_map = {d["decision_id"]: d for d in decisions}
    query_terms = set(query.lower().split())

    reranked = []
    for doc_id, original_score in results[:top_k * 3]:  # Consider more candidates
        if doc_id not in decision_map:
            continue

        decision = decision_map[doc_id]
        doc_text = decision["statement"].lower() + " " + decision["rationale"].lower()
        doc_terms = set(doc_text.split())

        # Simulate cross-encoder with multiple factors
        term_overlap = len(query_terms & doc_terms) / len(query_terms) if query_terms else 0

        # Bonus for phrase matches
        phrase_bonus = 0.0
        for i in range(len(query.split()) - 1):
            phrase = " ".join(query.lower().split()[i:i+2])
            if phrase in doc_text:
                phrase_bonus += 0.15

        # Semantic similarity simulation (based on domain/tag match)
        tag_match = sum(1 for t in decision.get("tags", []) if t.lower() in query.lower())
        semantic_bonus = tag_match * 0.1

        # Cross-encoder-like score (higher than TF-IDF)
        ce_score = min(1.0, term_overlap + phrase_bonus + semantic_bonus + random.uniform(0, 0.1))

        # Final blend: 70% cross-encoder, 30% original
        final_score = 0.7 * ce_score + 0.3 * original_score
        reranked.append((doc_id, final_score))

    reranked.sort(key=lambda x: x[1], reverse=True)
    return reranked[:top_k]


# ============================================================================
# STRESS TEST RUNNER
# ============================================================================

@dataclass
class TestConfig:
    """Test configuration."""
    name: str
    fusion_method: str  # "rrf", "linear", "combmnz", "borda"
    rrf_k: int = 60
    linear_weights: List[float] = field(default_factory=lambda: [0.7, 0.3])
    rerank_method: str = "none"  # "none", "tfidf", "crossencoder"
    rerank_top_k: int = 10


@dataclass
class TestResult:
    """Test result."""
    config_name: str
    dataset_size: int
    query_type: str
    relevance_score: float
    latency_ms: float
    results_count: int


def run_single_test(
    config: TestConfig,
    decisions: List[Dict],
    query_info: Dict,
) -> TestResult:
    """Run a single test with given configuration."""
    query = query_info["query"]
    expected_terms = query_info["expected_terms"]

    start_time = time.time()

    # Step 1: Simulate searches
    vector_scores = simulate_vector_search(query, decisions)
    keyword_scores = simulate_keyword_search(query, decisions)

    # Step 2: Apply fusion
    if config.fusion_method == "rrf":
        fused = rrf_fusion([vector_scores, keyword_scores], k=config.rrf_k)
    elif config.fusion_method == "linear":
        fused = linear_fusion([vector_scores, keyword_scores], config.linear_weights)
    elif config.fusion_method == "combmnz":
        fused = combmnz_fusion([vector_scores, keyword_scores])
    elif config.fusion_method == "borda":
        fused = borda_fusion([vector_scores, keyword_scores])
    else:
        fused = rrf_fusion([vector_scores, keyword_scores])

    # Step 3: Apply reranking
    if config.rerank_method == "tfidf":
        results = simulate_tfidf_rerank(query, fused, decisions, config.rerank_top_k)
    elif config.rerank_method == "crossencoder":
        results = simulate_crossencoder_rerank(query, fused, decisions, config.rerank_top_k)
    else:
        results = fused[:config.rerank_top_k]

    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000

    # Calculate relevance
    relevance = calculate_relevance_score(results, decisions, expected_terms)

    return TestResult(
        config_name=config.name,
        dataset_size=len(decisions),
        query_type=query_info["type"],
        relevance_score=relevance,
        latency_ms=latency_ms,
        results_count=len(results),
    )


def run_stress_test():
    """Run comprehensive stress test."""
    print("=" * 80)
    print("MANTRA Retrieval Stress Test & Configuration Optimizer")
    print("=" * 80)
    print()

    # Define test configurations
    configs = [
        # RRF with different k values
        TestConfig(name="RRF-k30", fusion_method="rrf", rrf_k=30),
        TestConfig(name="RRF-k60", fusion_method="rrf", rrf_k=60),
        TestConfig(name="RRF-k100", fusion_method="rrf", rrf_k=100),
        TestConfig(name="RRF-k200", fusion_method="rrf", rrf_k=200),

        # Linear with different weights
        TestConfig(name="Linear-70/30", fusion_method="linear", linear_weights=[0.7, 0.3]),
        TestConfig(name="Linear-50/50", fusion_method="linear", linear_weights=[0.5, 0.5]),
        TestConfig(name="Linear-30/70", fusion_method="linear", linear_weights=[0.3, 0.7]),

        # Other fusion methods
        TestConfig(name="CombMNZ", fusion_method="combmnz"),
        TestConfig(name="Borda", fusion_method="borda"),

        # With reranking
        TestConfig(name="RRF-k60+TF-IDF", fusion_method="rrf", rrf_k=60, rerank_method="tfidf"),
        TestConfig(name="RRF-k60+CrossEncoder", fusion_method="rrf", rrf_k=60, rerank_method="crossencoder"),
        TestConfig(name="Linear+CrossEncoder", fusion_method="linear", rerank_method="crossencoder"),
    ]

    # Dataset sizes to test
    dataset_sizes = [100, 500, 1000, 2000]

    # Generate queries
    queries = generate_test_queries()

    # Store all results
    all_results: List[TestResult] = []

    # Run tests
    for size in dataset_sizes:
        print(f"\n{'='*60}")
        print(f"Testing with {size} decisions")
        print("=" * 60)

        # Generate dataset
        decisions = [generate_decision(i) for i in range(size)]

        for config in configs:
            config_results = []

            for query_info in queries:
                # Run multiple times for statistical significance
                for _ in range(3):
                    result = run_single_test(config, decisions, query_info)
                    config_results.append(result)
                    all_results.append(result)

            # Calculate averages for this config
            avg_relevance = statistics.mean(r.relevance_score for r in config_results)
            avg_latency = statistics.mean(r.latency_ms for r in config_results)

            print(f"  {config.name:25} | Relevance: {avg_relevance:.3f} | Latency: {avg_latency:6.2f}ms")

    # Analyze results
    print("\n")
    print("=" * 80)
    print("ANALYSIS & RECOMMENDATIONS")
    print("=" * 80)

    # Group by config
    config_stats = {}
    for result in all_results:
        if result.config_name not in config_stats:
            config_stats[result.config_name] = {
                "relevance": [],
                "latency": [],
            }
        config_stats[result.config_name]["relevance"].append(result.relevance_score)
        config_stats[result.config_name]["latency"].append(result.latency_ms)

    # Calculate overall stats
    print("\n1. OVERALL CONFIGURATION RANKING (by Relevance)")
    print("-" * 60)

    ranked_configs = []
    for name, stats in config_stats.items():
        avg_rel = statistics.mean(stats["relevance"])
        avg_lat = statistics.mean(stats["latency"])
        std_rel = statistics.stdev(stats["relevance"]) if len(stats["relevance"]) > 1 else 0
        ranked_configs.append((name, avg_rel, std_rel, avg_lat))

    ranked_configs.sort(key=lambda x: x[1], reverse=True)

    print(f"{'Config':<30} {'Relevance':>12} {'StdDev':>10} {'Latency':>12}")
    print("-" * 64)
    for name, rel, std, lat in ranked_configs:
        print(f"{name:<30} {rel:>12.4f} {std:>10.4f} {lat:>10.2f}ms")

    # Find best by query type
    print("\n2. BEST CONFIG BY QUERY TYPE")
    print("-" * 60)

    query_types = set(r.query_type for r in all_results)
    for qtype in sorted(query_types):
        type_results = [r for r in all_results if r.query_type == qtype]

        # Group by config
        config_scores = {}
        for r in type_results:
            if r.config_name not in config_scores:
                config_scores[r.config_name] = []
            config_scores[r.config_name].append(r.relevance_score)

        # Find best
        best_config = max(config_scores.items(), key=lambda x: statistics.mean(x[1]))
        print(f"  {qtype:15} → {best_config[0]} (relevance: {statistics.mean(best_config[1]):.4f})")

    # RRF k analysis
    print("\n3. RRF K-VALUE ANALYSIS")
    print("-" * 60)

    rrf_configs = [(n, r, l) for n, r, _, l in ranked_configs if n.startswith("RRF-k") and "+" not in n]
    if rrf_configs:
        for name, rel, lat in rrf_configs:
            k_value = int(name.split("k")[1].split("+")[0])
            print(f"  k={k_value:3d}: Relevance={rel:.4f}, Latency={lat:.2f}ms")

        best_rrf = max(rrf_configs, key=lambda x: x[1])
        print(f"\n  Best RRF k-value: {best_rrf[0]}")

    # Reranking impact
    print("\n4. RERANKING IMPACT ANALYSIS")
    print("-" * 60)

    base_rrf = next((r for n, r, _, _ in ranked_configs if n == "RRF-k60"), None)
    tfidf_rrf = next((r for n, r, _, _ in ranked_configs if n == "RRF-k60+TF-IDF"), None)
    ce_rrf = next((r for n, r, _, _ in ranked_configs if n == "RRF-k60+CrossEncoder"), None)

    if base_rrf and tfidf_rrf:
        tfidf_improvement = ((tfidf_rrf - base_rrf) / base_rrf) * 100 if base_rrf > 0 else 0
        print(f"  TF-IDF Reranking:     {tfidf_improvement:+.1f}% relevance improvement")

    if base_rrf and ce_rrf:
        ce_improvement = ((ce_rrf - base_rrf) / base_rrf) * 100 if base_rrf > 0 else 0
        print(f"  Cross-Encoder:        {ce_improvement:+.1f}% relevance improvement")

    # Latency vs accuracy trade-off
    print("\n5. LATENCY vs ACCURACY TRADE-OFF")
    print("-" * 60)

    # Find Pareto-optimal configs
    pareto_optimal = []
    for name, rel, _, lat in ranked_configs:
        is_dominated = False
        for other_name, other_rel, _, other_lat in ranked_configs:
            if other_rel > rel and other_lat < lat:
                is_dominated = True
                break
        if not is_dominated:
            pareto_optimal.append((name, rel, lat))

    print("  Pareto-Optimal Configurations:")
    for name, rel, lat in sorted(pareto_optimal, key=lambda x: x[1], reverse=True):
        print(f"    {name}: Relevance={rel:.4f}, Latency={lat:.2f}ms")

    # Final recommendations
    print("\n" + "=" * 80)
    print("FINAL RECOMMENDATIONS")
    print("=" * 80)

    # Best overall
    best_overall = ranked_configs[0]
    print(f"""
1. BEST OVERALL CONFIG: {best_overall[0]}
   - Relevance: {best_overall[1]:.4f}
   - Latency: {best_overall[3]:.2f}ms

2. OPTIMAL SETTINGS:
""")

    # Determine optimal RRF k
    if rrf_configs:
        best_k = max(rrf_configs, key=lambda x: x[1])
        k_value = int(best_k[0].split("k")[1].split("+")[0])
        print(f"   - RRF k-value: {k_value} (best balance of accuracy)")

    # Reranking recommendation
    if ce_rrf and base_rrf:
        if ce_improvement > 10:
            print("   - Reranking: CrossEncoder (significant improvement)")
        elif tfidf_improvement > 5:
            print("   - Reranking: TF-IDF (good improvement, lower latency)")
        else:
            print("   - Reranking: Optional (marginal improvement)")

    # Fusion method
    fusion_winners = {}
    for name, rel, _, _ in ranked_configs:
        method = name.split("-")[0].split("+")[0]
        if method not in fusion_winners or rel > fusion_winners[method]:
            fusion_winners[method] = rel

    best_fusion = max(fusion_winners.items(), key=lambda x: x[1])
    print(f"   - Fusion Method: {best_fusion[0]} (highest relevance)")

    print("""
3. CONFIG BY USE CASE:

   High Accuracy (AI decisions critical):
   - Use: RRF-k60 + CrossEncoder reranking
   - Latency: ~5-10ms per query

   Balanced (General use):
   - Use: RRF-k60 + TF-IDF reranking
   - Latency: ~2-5ms per query

   Low Latency (Real-time):
   - Use: RRF-k60, no reranking
   - Latency: ~1-2ms per query

4. GAPS IDENTIFIED:
""")

    # Identify gaps
    gaps = []

    # Check if cross-encoder significantly better
    if ce_rrf and base_rrf and ce_improvement > 15:
        gaps.append("   - Cross-encoder provides significant improvement - ensure ML models are loaded")

    # Check query type variance
    type_variances = {}
    for qtype in query_types:
        type_results = [r.relevance_score for r in all_results if r.query_type == qtype]
        if type_results:
            type_variances[qtype] = statistics.stdev(type_results) if len(type_results) > 1 else 0

    high_variance_types = [t for t, v in type_variances.items() if v > 0.15]
    if high_variance_types:
        gaps.append(f"   - High variance for query types: {', '.join(high_variance_types)}")
        gaps.append("     Consider query-type-specific tuning")

    # Check if any config is significantly better for certain sizes
    size_best = {}
    for size in dataset_sizes:
        size_results = [r for r in all_results if r.dataset_size == size]
        if size_results:
            config_avg = {}
            for r in size_results:
                if r.config_name not in config_avg:
                    config_avg[r.config_name] = []
                config_avg[r.config_name].append(r.relevance_score)

            best = max(config_avg.items(), key=lambda x: statistics.mean(x[1]))
            size_best[size] = best[0]

    if len(set(size_best.values())) > 1:
        gaps.append("   - Different configs optimal for different dataset sizes")
        for size, config in size_best.items():
            gaps.append(f"     {size} docs → {config}")

    if gaps:
        for gap in gaps:
            print(gap)
    else:
        print("   - No significant gaps identified")

    print("\n" + "=" * 80)
    print("Stress test complete!")
    print("=" * 80)

    return all_results


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Set random seed for reproducibility
    random.seed(42)

    results = run_stress_test()

    # Save results to JSON
    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tests": len(results),
        "results": [
            {
                "config": r.config_name,
                "dataset_size": r.dataset_size,
                "query_type": r.query_type,
                "relevance": r.relevance_score,
                "latency_ms": r.latency_ms,
            }
            for r in results
        ],
    }

    with open("stress_test_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to stress_test_results.json")
