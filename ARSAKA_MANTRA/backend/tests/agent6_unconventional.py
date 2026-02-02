#!/usr/bin/env python3
"""
MANTRA Agent 6 - Unconventional Retrieval Approaches

Explores non-standard fusion and scoring methods:
1. Negative vector weight: keyword - 0.1*vector
2. Squared keyword scoring: keyword_score^2
3. Log-scaled fusion: log(1 + keyword) + log(1 + vector)
4. Max fusion: max(vector, keyword) instead of weighted sum
5. Multiplicative fusion: vector * keyword (rewards both matching)
6. Rank-based only (ignore scores): pure position-based fusion
7. Top-k filtering before fusion: only fuse if in top-k of either source
8. Exponential decay scoring based on rank
9. Domain-weighted scoring (boost decisions from same domain)

Test: 1000 decisions, 10 queries, 3 iterations
Baseline to beat: Linear-10/90 = 0.8227 relevance
"""

import sys
import time
import random
import math
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional, Callable
from enum import Enum
import json

# Set seed for reproducibility
random.seed(42)

# ============================================================================
# TEST DATA GENERATION
# ============================================================================

class DecisionDomain(str, Enum):
    INT = "INT"      # Integration
    ARCH = "ARCH"    # Architecture
    CTL = "CTL"      # Control
    EVO = "EVO"      # Evolution

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
        {"query": "react components", "expected": ["react"], "domain": "INT"},
        {"query": "database caching", "expected": ["database", "caching"], "domain": "ARCH"},
        {"query": "api authentication", "expected": ["api", "authentication"], "domain": "CTL"},
        {"query": "react state management redux", "expected": ["react", "state"], "domain": "INT"},
        {"query": "jwt authentication fastapi", "expected": ["jwt", "authentication"], "domain": "CTL"},
        {"query": "postgresql indexing optimization", "expected": ["postgresql", "indexing"], "domain": "ARCH"},
        {"query": "kubernetes docker deployment", "expected": ["kubernetes", "docker"], "domain": "EVO"},
        {"query": "microservices architecture", "expected": ["microservices"], "domain": "ARCH"},
        {"query": "event-driven design", "expected": ["event-driven"], "domain": "ARCH"},
        {"query": "security authorization", "expected": ["security", "authorization"], "domain": "CTL"},
    ]

# ============================================================================
# SEARCH SIMULATION (Same as baseline)
# ============================================================================

def simulate_vector_search(query: str, decisions: List[Dict]) -> Dict[str, float]:
    """Simulate vector (semantic) search."""
    query_terms = set(query.lower().split())
    scores = {}
    for d in decisions:
        doc_terms = set(d["statement"].lower().split() +
                       d["rationale"].lower().split() +
                       d.get("tags", []))
        overlap = len(query_terms & doc_terms)
        total = len(query_terms | doc_terms)
        score = overlap / total if total > 0 else 0
        # Add semantic noise (embeddings aren't perfect)
        noise = random.uniform(-0.1, 0.1)
        score = max(0, min(1, score + noise))
        if score > 0.05:
            scores[d["decision_id"]] = score
    return scores

def simulate_keyword_search(query: str, decisions: List[Dict]) -> Dict[str, float]:
    """Simulate keyword (BM25-style) search."""
    query_terms = set(query.lower().split())
    scores = {}
    for d in decisions:
        score = 0.0
        text = d["statement"].lower() + " " + d["rationale"].lower() + " " + " ".join(d.get("tags", []))
        for term in query_terms:
            if f" {term} " in f" {text} ":
                score += 0.4
            elif term in text:
                score += 0.2
        for tag in d.get("tags", []):
            if tag.lower() in query_terms:
                score += 0.5
        score = min(1.0, score / len(query_terms)) if query_terms else 0
        if score > 0.05:
            scores[d["decision_id"]] = score
    return scores

def calculate_relevance(results: List[Tuple[str, float]], decisions: List[Dict], expected: List[str]) -> float:
    """Calculate relevance score (NDCG-like)."""
    if not results:
        return 0.0
    decision_map = {d["decision_id"]: d for d in decisions}
    expected_lower = [t.lower() for t in expected]
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
# UNCONVENTIONAL FUSION METHODS
# ============================================================================

@dataclass
class UnconventionalConfig:
    """Configuration for unconventional approaches."""
    name: str
    description: str
    fusion_fn: Callable

# 1. Negative Vector Weight: keyword - 0.1*vector
def negative_vector_fusion(vector: Dict[str, float], keyword: Dict[str, float],
                           neg_weight: float = 0.1) -> List[Tuple[str, float]]:
    """Subtract vector score from keyword to prioritize pure keyword matches."""
    all_docs = set(vector.keys()) | set(keyword.keys())
    combined = {}
    for doc_id in all_docs:
        v_score = vector.get(doc_id, 0)
        k_score = keyword.get(doc_id, 0)
        # keyword - negative_weight * vector
        combined[doc_id] = k_score - neg_weight * v_score
    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

# 2. Squared Keyword Scoring: keyword_score^2
def squared_keyword_fusion(vector: Dict[str, float], keyword: Dict[str, float],
                           vw: float = 0.1, kw: float = 0.9) -> List[Tuple[str, float]]:
    """Square keyword scores to amplify differences."""
    all_docs = set(vector.keys()) | set(keyword.keys())
    combined = {}
    for doc_id in all_docs:
        v_score = vector.get(doc_id, 0)
        k_score = keyword.get(doc_id, 0)
        # Use squared keyword score
        combined[doc_id] = vw * v_score + kw * (k_score ** 2)
    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

# 3. Log-Scaled Fusion: log(1 + keyword) + log(1 + vector)
def log_scaled_fusion(vector: Dict[str, float], keyword: Dict[str, float]) -> List[Tuple[str, float]]:
    """Use logarithmic scaling to reduce impact of outlier scores."""
    all_docs = set(vector.keys()) | set(keyword.keys())
    combined = {}
    for doc_id in all_docs:
        v_score = vector.get(doc_id, 0)
        k_score = keyword.get(doc_id, 0)
        # Log-scaled combination
        combined[doc_id] = math.log(1 + k_score) + math.log(1 + v_score)
    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

# 4. Max Fusion: max(vector, keyword)
def max_fusion(vector: Dict[str, float], keyword: Dict[str, float]) -> List[Tuple[str, float]]:
    """Take maximum score from either source."""
    all_docs = set(vector.keys()) | set(keyword.keys())
    combined = {}
    for doc_id in all_docs:
        v_score = vector.get(doc_id, 0)
        k_score = keyword.get(doc_id, 0)
        combined[doc_id] = max(v_score, k_score)
    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

# 5. Multiplicative Fusion: vector * keyword
def multiplicative_fusion(vector: Dict[str, float], keyword: Dict[str, float],
                          bonus: float = 0.0) -> List[Tuple[str, float]]:
    """Multiply scores - rewards documents that appear in both sources."""
    all_docs = set(vector.keys()) | set(keyword.keys())
    combined = {}
    for doc_id in all_docs:
        v_score = vector.get(doc_id, 0)
        k_score = keyword.get(doc_id, 0)
        if v_score > 0 and k_score > 0:
            # Both match - use product + bonus
            combined[doc_id] = v_score * k_score + bonus
        else:
            # Only one matches - use the non-zero score with penalty
            combined[doc_id] = max(v_score, k_score) * 0.5
    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

# 6. Rank-Based Only (Borda Count)
def rank_only_fusion(vector: Dict[str, float], keyword: Dict[str, float]) -> List[Tuple[str, float]]:
    """Pure rank-based fusion ignoring actual scores (Borda count)."""
    # Get ranks
    v_sorted = sorted(vector.items(), key=lambda x: x[1], reverse=True)
    k_sorted = sorted(keyword.items(), key=lambda x: x[1], reverse=True)

    n_v = len(v_sorted)
    n_k = len(k_sorted)

    v_ranks = {doc_id: n_v - i for i, (doc_id, _) in enumerate(v_sorted)}
    k_ranks = {doc_id: n_k - i for i, (doc_id, _) in enumerate(k_sorted)}

    all_docs = set(vector.keys()) | set(keyword.keys())
    combined = {}
    for doc_id in all_docs:
        combined[doc_id] = v_ranks.get(doc_id, 0) + k_ranks.get(doc_id, 0)
    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

# 7. Top-K Filtering Before Fusion
def topk_filtered_fusion(vector: Dict[str, float], keyword: Dict[str, float],
                         k: int = 50, vw: float = 0.1, kw: float = 0.9) -> List[Tuple[str, float]]:
    """Only fuse documents that appear in top-k of at least one source."""
    v_sorted = sorted(vector.items(), key=lambda x: x[1], reverse=True)[:k]
    k_sorted = sorted(keyword.items(), key=lambda x: x[1], reverse=True)[:k]

    v_topk = set(doc_id for doc_id, _ in v_sorted)
    k_topk = set(doc_id for doc_id, _ in k_sorted)

    eligible_docs = v_topk | k_topk

    combined = {}
    for doc_id in eligible_docs:
        v_score = vector.get(doc_id, 0)
        k_score = keyword.get(doc_id, 0)
        combined[doc_id] = vw * v_score + kw * k_score
    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

# 8. Exponential Decay Scoring
def exponential_decay_fusion(vector: Dict[str, float], keyword: Dict[str, float],
                             decay: float = 0.1) -> List[Tuple[str, float]]:
    """Score based on exponential decay of rank position."""
    v_sorted = sorted(vector.items(), key=lambda x: x[1], reverse=True)
    k_sorted = sorted(keyword.items(), key=lambda x: x[1], reverse=True)

    v_decay = {doc_id: math.exp(-decay * i) for i, (doc_id, _) in enumerate(v_sorted)}
    k_decay = {doc_id: math.exp(-decay * i) for i, (doc_id, _) in enumerate(k_sorted)}

    all_docs = set(vector.keys()) | set(keyword.keys())
    combined = {}
    for doc_id in all_docs:
        combined[doc_id] = v_decay.get(doc_id, 0) + k_decay.get(doc_id, 0)
    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

# 9. Domain-Weighted Scoring
def domain_weighted_fusion(vector: Dict[str, float], keyword: Dict[str, float],
                           decisions: List[Dict], query_domain: str,
                           domain_boost: float = 1.5, vw: float = 0.1, kw: float = 0.9) -> List[Tuple[str, float]]:
    """Boost scores for decisions from the same domain as query."""
    decision_map = {d["decision_id"]: d for d in decisions}
    all_docs = set(vector.keys()) | set(keyword.keys())

    combined = {}
    for doc_id in all_docs:
        v_score = vector.get(doc_id, 0)
        k_score = keyword.get(doc_id, 0)
        base_score = vw * v_score + kw * k_score

        # Apply domain boost
        if doc_id in decision_map:
            doc_domain = decision_map[doc_id].get("domain_id", "")
            if doc_domain == query_domain:
                base_score *= domain_boost

        combined[doc_id] = base_score
    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

# ============================================================================
# BASELINE: Linear 10/90
# ============================================================================

def linear_fusion(vector: Dict[str, float], keyword: Dict[str, float],
                  vw: float = 0.1, kw: float = 0.9) -> List[Tuple[str, float]]:
    """Standard linear fusion baseline."""
    all_docs = set(vector.keys()) | set(keyword.keys())
    combined = {}
    for doc_id in all_docs:
        v_score = vector.get(doc_id, 0)
        k_score = keyword.get(doc_id, 0)
        combined[doc_id] = vw * v_score + kw * k_score
    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

# ============================================================================
# TEST RUNNER
# ============================================================================

def run_approach(name: str, fusion_fn: Callable, decisions: List[Dict],
                 queries: List[Dict], iterations: int = 3) -> Tuple[float, float, float]:
    """Run an approach and return (avg_relevance, std_dev, avg_latency)."""
    relevances = []
    latencies = []

    for q in queries:
        for _ in range(iterations):
            start = time.time()

            # Perform searches
            vector = simulate_vector_search(q["query"], decisions)
            keyword = simulate_keyword_search(q["query"], decisions)

            # Apply fusion
            if "domain_weighted" in name:
                results = fusion_fn(vector, keyword, decisions, q.get("domain", "INT"))
            else:
                results = fusion_fn(vector, keyword)

            latency = (time.time() - start) * 1000
            relevance = calculate_relevance(results, decisions, q["expected"])

            relevances.append(relevance)
            latencies.append(latency)

    avg_rel = statistics.mean(relevances)
    std_rel = statistics.stdev(relevances) if len(relevances) > 1 else 0
    avg_lat = statistics.mean(latencies)

    return avg_rel, std_rel, avg_lat

def main():
    print("=" * 80)
    print("MANTRA Agent 6 - Unconventional Retrieval Approaches")
    print("=" * 80)
    print()

    # Configuration
    num_decisions = 1000
    num_iterations = 3
    baseline_relevance = 0.8227

    # Generate test data
    print(f"Generating {num_decisions} decisions...")
    decisions = [generate_decision(i) for i in range(num_decisions)]
    queries = generate_queries()
    print(f"Loaded {len(queries)} test queries")
    print()

    # =========================================================================
    # RUN BASELINE
    # =========================================================================
    print("=" * 60)
    print("BASELINE: Linear-10/90")
    print("-" * 60)

    baseline_fn = lambda v, k: linear_fusion(v, k, 0.1, 0.9)
    b_rel, b_std, b_lat = run_approach("Linear-10/90", baseline_fn, decisions, queries, num_iterations)
    print(f"  Relevance: {b_rel:.4f} +/- {b_std:.4f}")
    print(f"  Latency:   {b_lat:.2f}ms")
    print(f"  Target:    {baseline_relevance:.4f}")
    print()

    # =========================================================================
    # RUN UNCONVENTIONAL APPROACHES
    # =========================================================================

    results = []

    # 1. Negative Vector Weight
    print("=" * 60)
    print("1. Negative Vector Weight (keyword - 0.1*vector)")
    print("-" * 60)

    for neg_w in [0.05, 0.1, 0.2, 0.3]:
        fn = lambda v, k, nw=neg_w: negative_vector_fusion(v, k, nw)
        rel, std, lat = run_approach(f"NegVec-{neg_w}", fn, decisions, queries, num_iterations)
        results.append((f"NegVec-{neg_w}", rel, std, lat))
        print(f"  neg_weight={neg_w}: {rel:.4f} +/- {std:.4f}")

    # 2. Squared Keyword Scoring
    print()
    print("=" * 60)
    print("2. Squared Keyword Scoring (k^2)")
    print("-" * 60)

    for vw in [0.0, 0.1, 0.2, 0.3]:
        kw = 1.0 - vw
        fn = lambda v, k, vweight=vw, kweight=kw: squared_keyword_fusion(v, k, vweight, kweight)
        rel, std, lat = run_approach(f"SquaredK-{int(vw*100)}/{int(kw*100)}", fn, decisions, queries, num_iterations)
        results.append((f"SquaredK-{int(vw*100)}/{int(kw*100)}", rel, std, lat))
        print(f"  v={vw:.1f}/k^2={kw:.1f}: {rel:.4f} +/- {std:.4f}")

    # 3. Log-Scaled Fusion
    print()
    print("=" * 60)
    print("3. Log-Scaled Fusion (log(1+k) + log(1+v))")
    print("-" * 60)

    fn = lambda v, k: log_scaled_fusion(v, k)
    rel, std, lat = run_approach("LogScaled", fn, decisions, queries, num_iterations)
    results.append(("LogScaled", rel, std, lat))
    print(f"  LogScaled: {rel:.4f} +/- {std:.4f}")

    # 4. Max Fusion
    print()
    print("=" * 60)
    print("4. Max Fusion (max(v, k))")
    print("-" * 60)

    fn = lambda v, k: max_fusion(v, k)
    rel, std, lat = run_approach("MaxFusion", fn, decisions, queries, num_iterations)
    results.append(("MaxFusion", rel, std, lat))
    print(f"  MaxFusion: {rel:.4f} +/- {std:.4f}")

    # 5. Multiplicative Fusion
    print()
    print("=" * 60)
    print("5. Multiplicative Fusion (v * k)")
    print("-" * 60)

    for bonus in [0.0, 0.1, 0.2, 0.3]:
        fn = lambda v, k, b=bonus: multiplicative_fusion(v, k, b)
        rel, std, lat = run_approach(f"Multiply-bonus{bonus}", fn, decisions, queries, num_iterations)
        results.append((f"Multiply-bonus{bonus}", rel, std, lat))
        print(f"  bonus={bonus}: {rel:.4f} +/- {std:.4f}")

    # 6. Rank-Based Only (Borda Count)
    print()
    print("=" * 60)
    print("6. Rank-Based Only (Borda Count)")
    print("-" * 60)

    fn = lambda v, k: rank_only_fusion(v, k)
    rel, std, lat = run_approach("BordaCount", fn, decisions, queries, num_iterations)
    results.append(("BordaCount", rel, std, lat))
    print(f"  BordaCount: {rel:.4f} +/- {std:.4f}")

    # 7. Top-K Filtering Before Fusion
    print()
    print("=" * 60)
    print("7. Top-K Filtering Before Fusion")
    print("-" * 60)

    for k in [20, 50, 100, 200]:
        fn = lambda v, kw, topk=k: topk_filtered_fusion(v, kw, topk, 0.1, 0.9)
        rel, std, lat = run_approach(f"TopK-{k}", fn, decisions, queries, num_iterations)
        results.append((f"TopK-{k}", rel, std, lat))
        print(f"  k={k}: {rel:.4f} +/- {std:.4f}")

    # 8. Exponential Decay Scoring
    print()
    print("=" * 60)
    print("8. Exponential Decay Scoring")
    print("-" * 60)

    for decay in [0.05, 0.1, 0.2, 0.3]:
        fn = lambda v, k, d=decay: exponential_decay_fusion(v, k, d)
        rel, std, lat = run_approach(f"ExpDecay-{decay}", fn, decisions, queries, num_iterations)
        results.append((f"ExpDecay-{decay}", rel, std, lat))
        print(f"  decay={decay}: {rel:.4f} +/- {std:.4f}")

    # 9. Domain-Weighted Scoring
    print()
    print("=" * 60)
    print("9. Domain-Weighted Scoring")
    print("-" * 60)

    for boost in [1.2, 1.5, 2.0, 3.0]:
        fn = lambda v, k, d, q_domain, b=boost: domain_weighted_fusion(v, k, d, q_domain, b, 0.1, 0.9)

        # Special handling for domain-weighted
        rels = []
        lats = []
        for q in queries:
            for _ in range(num_iterations):
                start = time.time()
                vector = simulate_vector_search(q["query"], decisions)
                keyword = simulate_keyword_search(q["query"], decisions)
                res = domain_weighted_fusion(vector, keyword, decisions, q.get("domain", "INT"), boost, 0.1, 0.9)
                lat = (time.time() - start) * 1000
                rel = calculate_relevance(res, decisions, q["expected"])
                rels.append(rel)
                lats.append(lat)

        avg_rel = statistics.mean(rels)
        std_rel = statistics.stdev(rels)
        avg_lat = statistics.mean(lats)
        results.append((f"DomainBoost-{boost}", avg_rel, std_rel, avg_lat))
        print(f"  boost={boost}: {avg_rel:.4f} +/- {std_rel:.4f}")

    # =========================================================================
    # HYBRID COMBINATIONS
    # =========================================================================
    print()
    print("=" * 60)
    print("BONUS: Hybrid Combinations")
    print("-" * 60)

    # Squared + TopK
    for k in [50, 100]:
        def hybrid_squared_topk(v, k_scores, topk=k):
            # First apply TopK filter
            v_sorted = sorted(v.items(), key=lambda x: x[1], reverse=True)[:topk]
            k_sorted = sorted(k_scores.items(), key=lambda x: x[1], reverse=True)[:topk]
            v_topk = set(doc_id for doc_id, _ in v_sorted)
            k_topk = set(doc_id for doc_id, _ in k_sorted)
            eligible = v_topk | k_topk

            combined = {}
            for doc_id in eligible:
                v_score = v.get(doc_id, 0)
                k_score = k_scores.get(doc_id, 0)
                # Squared keyword
                combined[doc_id] = 0.1 * v_score + 0.9 * (k_score ** 2)
            return sorted(combined.items(), key=lambda x: x[1], reverse=True)

        rel, std, lat = run_approach(f"Squared+TopK{k}", hybrid_squared_topk, decisions, queries, num_iterations)
        results.append((f"Squared+TopK{k}", rel, std, lat))
        print(f"  Squared+TopK{k}: {rel:.4f} +/- {std:.4f}")

    # Multiply + Exponential Decay
    def hybrid_mult_decay(v, k):
        # First get multiplicative scores
        mult_results = multiplicative_fusion(v, k, 0.1)
        # Convert to dict
        mult_dict = dict(mult_results)
        # Apply exponential decay on ranks
        sorted_mult = sorted(mult_dict.items(), key=lambda x: x[1], reverse=True)
        decay_scores = {doc_id: score * math.exp(-0.05 * i)
                       for i, (doc_id, score) in enumerate(sorted_mult)}
        return sorted(decay_scores.items(), key=lambda x: x[1], reverse=True)

    rel, std, lat = run_approach("Multiply+ExpDecay", hybrid_mult_decay, decisions, queries, num_iterations)
    results.append(("Multiply+ExpDecay", rel, std, lat))
    print(f"  Multiply+ExpDecay: {rel:.4f} +/- {std:.4f}")

    # =========================================================================
    # FINAL RESULTS
    # =========================================================================
    print()
    print("=" * 80)
    print("FINAL RESULTS: Approaches vs Baseline")
    print("=" * 80)

    # Sort by relevance
    results_sorted = sorted(results, key=lambda x: x[1], reverse=True)

    print(f"\nBaseline (Linear-10/90): {b_rel:.4f} (Target: {baseline_relevance:.4f})")
    print()

    # Find winners
    winners = [r for r in results_sorted if r[1] > baseline_relevance]

    print(f"{'Rank':<5} {'Approach':<30} {'Relevance':>10} {'vs Baseline':>12} {'Latency':>10}")
    print("-" * 75)

    for i, (name, rel, std, lat) in enumerate(results_sorted[:20], 1):
        diff = rel - baseline_relevance
        marker = " ***" if rel > baseline_relevance else ""
        print(f"{i:<5} {name:<30} {rel:>10.4f} {diff:>+11.4f}{marker} {lat:>8.2f}ms")

    # =========================================================================
    # WINNER SUMMARY
    # =========================================================================
    print()
    print("=" * 80)
    print("APPROACHES THAT BEAT BASELINE (> 0.8227)")
    print("=" * 80)

    if winners:
        print(f"\nFound {len(winners)} winning approach(es):\n")
        for name, rel, std, lat in winners:
            improvement = ((rel - baseline_relevance) / baseline_relevance) * 100
            print(f"  [{name}]")
            print(f"    Relevance:   {rel:.4f} (+{improvement:.2f}%)")
            print(f"    Std Dev:     {std:.4f}")
            print(f"    Latency:     {lat:.2f}ms")
            print()
    else:
        print("\nNo approaches beat the baseline in this run.")
        print("Top 3 closest approaches:")
        for name, rel, std, lat in results_sorted[:3]:
            print(f"  {name}: {rel:.4f} (baseline - {baseline_relevance - rel:.4f})")

    # Save results
    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config": {
            "num_decisions": num_decisions,
            "num_queries": len(queries),
            "num_iterations": num_iterations,
            "baseline": baseline_relevance
        },
        "baseline_actual": {
            "relevance": b_rel,
            "std_dev": b_std,
            "latency_ms": b_lat
        },
        "winners": [
            {"name": n, "relevance": r, "std_dev": s, "latency_ms": l}
            for n, r, s, l in winners
        ],
        "all_results": [
            {"name": n, "relevance": r, "std_dev": s, "latency_ms": l}
            for n, r, s, l in results_sorted
        ]
    }

    output_path = "/mnt/f/WINDSURF/neliti_code/signate/ARSAKA_MANTRA/backend/tests/agent6_unconventional_results.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to: {output_path}")
    print("=" * 80)

    return len(winners) > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
