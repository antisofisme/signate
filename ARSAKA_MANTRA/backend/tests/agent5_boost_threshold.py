#!/usr/bin/env python3
"""
MANTRA Agent 5 - Boost & Threshold Parameter Tuning

Based on Linear-10/90 as optimal base, tunes:
1. boost_multi_source: 1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.4, 1.5, 2.0
2. boost_exact_match: 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0
3. min_score_threshold: 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4
4. tag_match_bonus: 0.3, 0.4, 0.5, 0.6, 0.7
5. phrase_match_bonus: 0.1, 0.15, 0.2, 0.25, 0.3

Test: 1000 decisions, 10 queries, 3 iterations each

Output: Best boost/threshold configuration
"""

import sys
import time
import random
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
from enum import Enum
import json
from itertools import product

# Set seed for reproducibility
random.seed(42)

# ============================================================================
# CONSTANTS & PARAMETERS TO TUNE
# ============================================================================

BOOST_MULTI_SOURCE_VALUES = [1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.4, 1.5, 2.0]
BOOST_EXACT_MATCH_VALUES = [1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0]
MIN_SCORE_THRESHOLD_VALUES = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]
TAG_MATCH_BONUS_VALUES = [0.3, 0.4, 0.5, 0.6, 0.7]
PHRASE_MATCH_BONUS_VALUES = [0.1, 0.15, 0.2, 0.25, 0.3]

# Base config (Linear 10/90 from grid search optimization)
BASE_VECTOR_WEIGHT = 0.1
BASE_KEYWORD_WEIGHT = 0.9

# Test parameters
NUM_DECISIONS = 1000
NUM_QUERIES = 10
ITERATIONS_PER_QUERY = 3

# ============================================================================
# TEST DATA GENERATION
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
    "The {tech1} architecture MUST enforce {purpose} standards",
    "Security {purpose} SHALL be handled by {tech1} with {tech2}",
]

PURPOSES = [
    "data fetching", "state management", "error handling",
    "form validation", "routing", "authorization",
    "caching", "logging", "monitoring", "testing",
    "performance", "security", "scalability",
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
    rationale = f"This decision ensures consistency in {purpose}. Using {tech1} with {tech2} provides better maintainability and follows industry best practices."

    # Generate tags
    tags = list(set([tech1, tech2, purpose.split()[0]]))
    if random.random() > 0.5:
        tags.append(domain.value.lower())

    return {
        "decision_id": f"decision-{idx:05d}",
        "code": f"{domain.value}-F{(idx % 16) + 1:02d}",
        "domain_id": domain.value,
        "statement": statement,
        "rationale": rationale,
        "tags": tags,
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
        {"query": "microservices architecture patterns", "expected": ["microservices"]},
        {"query": "event-driven design cqrs", "expected": ["event-driven", "cqrs"]},
        {"query": "security authorization rbac", "expected": ["security", "authorization", "rbac"]},
    ]

# ============================================================================
# SEARCH SIMULATION
# ============================================================================

def simulate_vector_search(query: str, decisions: List[Dict]) -> Dict[str, float]:
    """Simulate vector similarity search."""
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
        noise = random.uniform(-0.1, 0.1)
        score = max(0, min(1, score + noise))
        if score > 0.05:
            scores[d["decision_id"]] = score
    return scores

def simulate_keyword_search(
    query: str,
    decisions: List[Dict],
    boost_exact_match: float,
    tag_match_bonus: float,
    phrase_match_bonus: float
) -> Dict[str, float]:
    """
    Simulate keyword search with configurable bonuses.

    Args:
        boost_exact_match: Multiplier for exact word boundary matches
        tag_match_bonus: Bonus for tag matches
        phrase_match_bonus: Bonus for consecutive phrase matches
    """
    query_terms = query.lower().split()
    query_terms_set = set(query_terms)
    scores = {}

    for d in decisions:
        score = 0.0
        text = d["statement"].lower() + " " + d["rationale"].lower() + " " + " ".join(d.get("tags", []))

        # Term matching with exact match boost
        for term in query_terms_set:
            if f" {term} " in f" {text} ":
                # Exact word boundary match
                score += 0.3 * boost_exact_match
            elif term in text:
                # Partial match
                score += 0.15

        # Tag matching with configurable bonus
        for tag in d.get("tags", []):
            if tag.lower() in query_terms_set:
                score += tag_match_bonus

        # Phrase matching - consecutive terms bonus
        for i in range(len(query_terms) - 1):
            phrase = " ".join(query_terms[i:i+2])
            if phrase in text:
                score += phrase_match_bonus

        # 3-word phrase bonus (stronger signal)
        for i in range(len(query_terms) - 2):
            phrase = " ".join(query_terms[i:i+3])
            if phrase in text:
                score += phrase_match_bonus * 1.5

        # Normalize by query length
        score = min(1.0, score / max(len(query_terms_set), 1))

        if score > 0.05:
            scores[d["decision_id"]] = score

    return scores

def linear_fusion(
    vector_scores: Dict[str, float],
    keyword_scores: Dict[str, float],
    vector_weight: float = 0.1,
    keyword_weight: float = 0.9
) -> List[Tuple[str, float]]:
    """Linear fusion of scores."""
    all_docs = set(vector_scores.keys()) | set(keyword_scores.keys())

    combined = {}
    for doc_id in all_docs:
        v_score = vector_scores.get(doc_id, 0.0)
        k_score = keyword_scores.get(doc_id, 0.0)
        combined[doc_id] = vector_weight * v_score + keyword_weight * k_score

    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

def apply_boosts_and_threshold(
    fused_results: List[Tuple[str, float]],
    vector_scores: Dict[str, float],
    keyword_scores: Dict[str, float],
    boost_multi_source: float,
    min_score_threshold: float
) -> List[Tuple[str, float]]:
    """Apply multi-source boost and score threshold filtering."""
    vector_ids = set(vector_scores.keys())
    keyword_ids = set(keyword_scores.keys())

    boosted = []
    for doc_id, score in fused_results:
        # Skip if below threshold
        if score < min_score_threshold:
            continue

        # Boost if found in both sources
        if doc_id in vector_ids and doc_id in keyword_ids:
            score *= boost_multi_source

        boosted.append((doc_id, score))

    # Re-sort after boosting
    boosted.sort(key=lambda x: x[1], reverse=True)
    return boosted

def calculate_relevance(
    results: List[Tuple[str, float]],
    decisions: List[Dict],
    expected: List[str]
) -> float:
    """Calculate weighted relevance score based on expected terms."""
    if not results:
        return 0.0

    decision_map = {d["decision_id"]: d for d in decisions}
    expected_lower = [t.lower() for t in expected]

    # DCG-style weights for top positions
    weights = [1.0, 0.8, 0.6, 0.4, 0.3, 0.2, 0.15, 0.1, 0.08, 0.05]

    total = 0.0
    for i, (doc_id, _) in enumerate(results[:10]):
        weight = weights[i] if i < len(weights) else 0.05
        if doc_id in decision_map:
            d = decision_map[doc_id]
            text = d["statement"].lower() + " " + d["rationale"].lower() + " " + " ".join(d.get("tags", []))
            matches = sum(1 for t in expected_lower if t in text)
            total += weight * (matches / len(expected_lower) if expected_lower else 0)

    max_possible = sum(weights[:min(len(results), 10)])
    return total / max_possible if max_possible > 0 else 0

# ============================================================================
# CONFIG DATA STRUCTURE
# ============================================================================

@dataclass
class TuningConfig:
    """Configuration for boost/threshold tuning."""
    name: str
    boost_multi_source: float = 1.2
    boost_exact_match: float = 1.5
    min_score_threshold: float = 0.3
    tag_match_bonus: float = 0.5
    phrase_match_bonus: float = 0.15

    def to_dict(self) -> Dict[str, Any]:
        return {
            "boost_multi_source": self.boost_multi_source,
            "boost_exact_match": self.boost_exact_match,
            "min_score_threshold": self.min_score_threshold,
            "tag_match_bonus": self.tag_match_bonus,
            "phrase_match_bonus": self.phrase_match_bonus,
        }

def run_config(
    config: TuningConfig,
    decisions: List[Dict],
    queries: List[Dict]
) -> Tuple[float, float, float]:
    """
    Run configuration and return (avg_relevance, std_dev, avg_latency).

    Uses Linear-10/90 as base and applies boost/threshold parameters.
    """
    relevances = []
    latencies = []

    for q in queries:
        for _ in range(ITERATIONS_PER_QUERY):
            start = time.time()

            # Vector search
            vector_scores = simulate_vector_search(q["query"], decisions)

            # Keyword search with configurable bonuses
            keyword_scores = simulate_keyword_search(
                q["query"],
                decisions,
                boost_exact_match=config.boost_exact_match,
                tag_match_bonus=config.tag_match_bonus,
                phrase_match_bonus=config.phrase_match_bonus,
            )

            # Linear fusion (10/90 base)
            fused = linear_fusion(
                vector_scores,
                keyword_scores,
                vector_weight=BASE_VECTOR_WEIGHT,
                keyword_weight=BASE_KEYWORD_WEIGHT,
            )

            # Apply boosts and threshold
            results = apply_boosts_and_threshold(
                fused,
                vector_scores,
                keyword_scores,
                boost_multi_source=config.boost_multi_source,
                min_score_threshold=config.min_score_threshold,
            )

            latency = (time.time() - start) * 1000
            relevance = calculate_relevance(results, decisions, q["expected"])

            relevances.append(relevance)
            latencies.append(latency)

    avg_rel = statistics.mean(relevances)
    std_rel = statistics.stdev(relevances) if len(relevances) > 1 else 0
    avg_lat = statistics.mean(latencies)

    return avg_rel, std_rel, avg_lat

# ============================================================================
# GRID SEARCH PHASES
# ============================================================================

def phase1_multi_source_boost(decisions: List[Dict], queries: List[Dict]) -> Tuple[float, List]:
    """Phase 1: Tune boost_multi_source parameter."""
    print("\nPHASE 1: Tuning boost_multi_source")
    print("-" * 60)

    results = []
    for boost in BOOST_MULTI_SOURCE_VALUES:
        config = TuningConfig(
            name=f"boost_multi={boost}",
            boost_multi_source=boost,
        )
        rel, std, lat = run_config(config, decisions, queries)
        results.append((boost, rel, std, lat))
        print(f"  boost_multi_source={boost:<5} | Relevance: {rel:.4f} +/- {std:.4f} | Latency: {lat:.2f}ms")

    best = max(results, key=lambda x: x[1])
    print(f"\n  BEST boost_multi_source: {best[0]} (Relevance: {best[1]:.4f})")
    return best[0], results

def phase2_exact_match_boost(
    decisions: List[Dict],
    queries: List[Dict],
    best_multi: float
) -> Tuple[float, List]:
    """Phase 2: Tune boost_exact_match parameter."""
    print("\nPHASE 2: Tuning boost_exact_match")
    print("-" * 60)

    results = []
    for boost in BOOST_EXACT_MATCH_VALUES:
        config = TuningConfig(
            name=f"boost_exact={boost}",
            boost_multi_source=best_multi,
            boost_exact_match=boost,
        )
        rel, std, lat = run_config(config, decisions, queries)
        results.append((boost, rel, std, lat))
        print(f"  boost_exact_match={boost:<5} | Relevance: {rel:.4f} +/- {std:.4f} | Latency: {lat:.2f}ms")

    best = max(results, key=lambda x: x[1])
    print(f"\n  BEST boost_exact_match: {best[0]} (Relevance: {best[1]:.4f})")
    return best[0], results

def phase3_min_threshold(
    decisions: List[Dict],
    queries: List[Dict],
    best_multi: float,
    best_exact: float
) -> Tuple[float, List]:
    """Phase 3: Tune min_score_threshold parameter."""
    print("\nPHASE 3: Tuning min_score_threshold")
    print("-" * 60)

    results = []
    for threshold in MIN_SCORE_THRESHOLD_VALUES:
        config = TuningConfig(
            name=f"min_score={threshold}",
            boost_multi_source=best_multi,
            boost_exact_match=best_exact,
            min_score_threshold=threshold,
        )
        rel, std, lat = run_config(config, decisions, queries)
        results.append((threshold, rel, std, lat))
        print(f"  min_score_threshold={threshold:<5} | Relevance: {rel:.4f} +/- {std:.4f} | Latency: {lat:.2f}ms")

    best = max(results, key=lambda x: x[1])
    print(f"\n  BEST min_score_threshold: {best[0]} (Relevance: {best[1]:.4f})")
    return best[0], results

def phase4_tag_bonus(
    decisions: List[Dict],
    queries: List[Dict],
    best_multi: float,
    best_exact: float,
    best_threshold: float
) -> Tuple[float, List]:
    """Phase 4: Tune tag_match_bonus parameter."""
    print("\nPHASE 4: Tuning tag_match_bonus")
    print("-" * 60)

    results = []
    for bonus in TAG_MATCH_BONUS_VALUES:
        config = TuningConfig(
            name=f"tag_bonus={bonus}",
            boost_multi_source=best_multi,
            boost_exact_match=best_exact,
            min_score_threshold=best_threshold,
            tag_match_bonus=bonus,
        )
        rel, std, lat = run_config(config, decisions, queries)
        results.append((bonus, rel, std, lat))
        print(f"  tag_match_bonus={bonus:<5} | Relevance: {rel:.4f} +/- {std:.4f} | Latency: {lat:.2f}ms")

    best = max(results, key=lambda x: x[1])
    print(f"\n  BEST tag_match_bonus: {best[0]} (Relevance: {best[1]:.4f})")
    return best[0], results

def phase5_phrase_bonus(
    decisions: List[Dict],
    queries: List[Dict],
    best_multi: float,
    best_exact: float,
    best_threshold: float,
    best_tag: float
) -> Tuple[float, List]:
    """Phase 5: Tune phrase_match_bonus parameter."""
    print("\nPHASE 5: Tuning phrase_match_bonus")
    print("-" * 60)

    results = []
    for bonus in PHRASE_MATCH_BONUS_VALUES:
        config = TuningConfig(
            name=f"phrase_bonus={bonus}",
            boost_multi_source=best_multi,
            boost_exact_match=best_exact,
            min_score_threshold=best_threshold,
            tag_match_bonus=best_tag,
            phrase_match_bonus=bonus,
        )
        rel, std, lat = run_config(config, decisions, queries)
        results.append((bonus, rel, std, lat))
        print(f"  phrase_match_bonus={bonus:<5} | Relevance: {rel:.4f} +/- {std:.4f} | Latency: {lat:.2f}ms")

    best = max(results, key=lambda x: x[1])
    print(f"\n  BEST phrase_match_bonus: {best[0]} (Relevance: {best[1]:.4f})")
    return best[0], results

def phase6_fine_tune(
    decisions: List[Dict],
    queries: List[Dict],
    best_multi: float,
    best_exact: float,
    best_threshold: float,
    best_tag: float,
    best_phrase: float
) -> Tuple[TuningConfig, List]:
    """Phase 6: Fine-tune around best values with smaller steps."""
    print("\nPHASE 6: Fine-tuning around optimal values")
    print("-" * 60)

    # Generate fine-tune variations
    def nearby(value: float, step: float = 0.05, count: int = 3) -> List[float]:
        return [
            round(value + (i - count//2) * step, 3)
            for i in range(count)
        ]

    fine_multi = nearby(best_multi, 0.05)
    fine_exact = nearby(best_exact, 0.1)
    fine_threshold = nearby(best_threshold, 0.02)
    fine_tag = nearby(best_tag, 0.05)
    fine_phrase = nearby(best_phrase, 0.02)

    # Test all combinations (limited grid)
    results = []
    total_combos = len(fine_multi) * len(fine_exact) * len(fine_threshold) * len(fine_tag) * len(fine_phrase)
    print(f"  Testing {total_combos} fine-tune combinations...")

    combo_count = 0
    for multi, exact, thresh, tag, phrase in product(
        fine_multi, fine_exact, fine_threshold, fine_tag, fine_phrase
    ):
        # Skip invalid values
        if multi < 1.0 or exact < 1.0 or thresh < 0.05 or tag < 0.1 or phrase < 0.05:
            continue

        config = TuningConfig(
            name=f"fine_{combo_count}",
            boost_multi_source=multi,
            boost_exact_match=exact,
            min_score_threshold=thresh,
            tag_match_bonus=tag,
            phrase_match_bonus=phrase,
        )
        rel, std, lat = run_config(config, decisions, queries)
        results.append((config, rel, std, lat))
        combo_count += 1

        if combo_count % 50 == 0:
            print(f"    Progress: {combo_count}/{total_combos} combinations tested...")

    best = max(results, key=lambda x: x[1])
    return best[0], results

def compare_with_baseline(
    decisions: List[Dict],
    queries: List[Dict],
    best_config: TuningConfig
) -> Dict[str, Any]:
    """Compare best config with baseline (default values)."""
    print("\n" + "=" * 60)
    print("COMPARISON: Best Config vs Baseline")
    print("=" * 60)

    # Baseline config (default values from searcher.py)
    baseline = TuningConfig(
        name="baseline",
        boost_multi_source=1.2,
        boost_exact_match=1.5,
        min_score_threshold=0.3,
        tag_match_bonus=0.5,
        phrase_match_bonus=0.15,
    )

    baseline_rel, baseline_std, baseline_lat = run_config(baseline, decisions, queries)
    best_rel, best_std, best_lat = run_config(best_config, decisions, queries)

    improvement = ((best_rel - baseline_rel) / baseline_rel) * 100 if baseline_rel > 0 else 0

    print(f"\n  Baseline:     Relevance: {baseline_rel:.4f} +/- {baseline_std:.4f}")
    print(f"  Best Config:  Relevance: {best_rel:.4f} +/- {best_std:.4f}")
    print(f"  Improvement:  {improvement:+.2f}%")

    return {
        "baseline_relevance": baseline_rel,
        "best_relevance": best_rel,
        "improvement_pct": improvement,
    }

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("MANTRA Agent 5 - Boost & Threshold Parameter Tuning")
    print("=" * 80)
    print(f"\nBase Configuration: Linear-{int(BASE_VECTOR_WEIGHT*100)}/{int(BASE_KEYWORD_WEIGHT*100)}")
    print(f"Test Size: {NUM_DECISIONS} decisions, {NUM_QUERIES} queries, {ITERATIONS_PER_QUERY} iterations each")
    print()

    # Generate test data
    print("Generating test data...")
    decisions = [generate_decision(i) for i in range(NUM_DECISIONS)]
    queries = generate_queries()
    print(f"  Decisions: {len(decisions)}")
    print(f"  Queries: {len(queries)}")

    start_time = time.time()

    # Phase 1: Multi-source boost
    best_multi, multi_results = phase1_multi_source_boost(decisions, queries)

    # Phase 2: Exact match boost
    best_exact, exact_results = phase2_exact_match_boost(decisions, queries, best_multi)

    # Phase 3: Min score threshold
    best_threshold, threshold_results = phase3_min_threshold(
        decisions, queries, best_multi, best_exact
    )

    # Phase 4: Tag match bonus
    best_tag, tag_results = phase4_tag_bonus(
        decisions, queries, best_multi, best_exact, best_threshold
    )

    # Phase 5: Phrase match bonus
    best_phrase, phrase_results = phase5_phrase_bonus(
        decisions, queries, best_multi, best_exact, best_threshold, best_tag
    )

    # Phase 6: Fine-tuning
    best_config, fine_results = phase6_fine_tune(
        decisions, queries, best_multi, best_exact, best_threshold, best_tag, best_phrase
    )

    # Compare with baseline
    comparison = compare_with_baseline(decisions, queries, best_config)

    # Final validation run (more iterations for confidence)
    print("\n" + "=" * 60)
    print("FINAL VALIDATION (5 iterations per query)")
    print("=" * 60)

    # Override iterations for final validation
    old_iterations = ITERATIONS_PER_QUERY
    final_relevances = []
    for q in queries:
        for _ in range(5):
            vector_scores = simulate_vector_search(q["query"], decisions)
            keyword_scores = simulate_keyword_search(
                q["query"], decisions,
                boost_exact_match=best_config.boost_exact_match,
                tag_match_bonus=best_config.tag_match_bonus,
                phrase_match_bonus=best_config.phrase_match_bonus,
            )
            fused = linear_fusion(vector_scores, keyword_scores)
            results = apply_boosts_and_threshold(
                fused, vector_scores, keyword_scores,
                boost_multi_source=best_config.boost_multi_source,
                min_score_threshold=best_config.min_score_threshold,
            )
            rel = calculate_relevance(results, decisions, q["expected"])
            final_relevances.append(rel)

    final_avg = statistics.mean(final_relevances)
    final_std = statistics.stdev(final_relevances)

    # Calculate total time
    total_time = time.time() - start_time

    # =========================================================================
    # FINAL OUTPUT
    # =========================================================================
    print("\n" + "=" * 80)
    print("OPTIMAL BOOST/THRESHOLD CONFIGURATION")
    print("=" * 80)
    print(f"""
Base Retrieval: Linear Fusion {int(BASE_VECTOR_WEIGHT*100)}/{int(BASE_KEYWORD_WEIGHT*100)} (Vector/Keyword)

BEST PARAMETERS:
  boost_multi_source:  {best_config.boost_multi_source}
  boost_exact_match:   {best_config.boost_exact_match}
  min_score_threshold: {best_config.min_score_threshold}
  tag_match_bonus:     {best_config.tag_match_bonus}
  phrase_match_bonus:  {best_config.phrase_match_bonus}

PERFORMANCE:
  Final Relevance:     {final_avg:.4f} +/- {final_std:.4f}
  Improvement vs Base: {comparison['improvement_pct']:+.2f}%

CONFIGURATION (Python):
```python
SearchConfig(
    mode = SearchMode.HYBRID,
    fusion_mode = FusionMode.LINEAR,
    vector_weight = {BASE_VECTOR_WEIGHT},
    keyword_weight = {BASE_KEYWORD_WEIGHT},
    min_score = {best_config.min_score_threshold},
    boost_exact_match = {best_config.boost_exact_match},
    boost_multi_source = {best_config.boost_multi_source},
)

# Additional bonuses (in keyword search):
TAG_MATCH_BONUS = {best_config.tag_match_bonus}
PHRASE_MATCH_BONUS = {best_config.phrase_match_bonus}
```

Total Tuning Time: {total_time:.1f}s
""")

    # Save results
    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "base_config": {
            "fusion_mode": "LINEAR",
            "vector_weight": BASE_VECTOR_WEIGHT,
            "keyword_weight": BASE_KEYWORD_WEIGHT,
        },
        "optimal_parameters": best_config.to_dict(),
        "performance": {
            "final_relevance": final_avg,
            "final_std": final_std,
            "improvement_vs_baseline_pct": comparison["improvement_pct"],
        },
        "test_config": {
            "num_decisions": NUM_DECISIONS,
            "num_queries": NUM_QUERIES,
            "iterations_per_query": ITERATIONS_PER_QUERY,
        },
        "phase_results": {
            "boost_multi_source": [(v, r, s, l) for v, r, s, l in multi_results],
            "boost_exact_match": [(v, r, s, l) for v, r, s, l in exact_results],
            "min_score_threshold": [(v, r, s, l) for v, r, s, l in threshold_results],
            "tag_match_bonus": [(v, r, s, l) for v, r, s, l in tag_results],
            "phrase_match_bonus": [(v, r, s, l) for v, r, s, l in phrase_results],
        },
    }

    output_file = "/mnt/f/WINDSURF/neliti_code/signate/ARSAKA_MANTRA/backend/tests/agent5_boost_threshold_results.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Results saved to: {output_file}")
    print("=" * 80)

if __name__ == "__main__":
    main()
