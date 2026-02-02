#!/usr/bin/env python3
"""
MANTRA Advanced Reranking Strategy Explorer (Agent 3)

Explores advanced reranking strategies to find optimal configuration:
1. Different rerank_top_n values: 10, 15, 20, 25, 30, 40, 50, 75, 100
2. Cascaded reranking (TF-IDF first, then CrossEncoder on top N)
3. Rerank score blending ratios (original vs rerank): 0.1/0.9 to 0.5/0.5
4. Minimum candidates threshold before reranking
5. BM25-style reranking simulation (k1=1.2, b=0.75)

Base: Linear-10/90 fusion (best from previous tests)

Output: Best reranking configuration with exact parameters
"""

import sys
import time
import random
import math
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
from enum import Enum
import json
from itertools import product
from collections import defaultdict

# Set seed for reproducibility
random.seed(42)

# ============================================================================
# TEST DATA GENERATION (Same as previous tests for consistency)
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
    rationale = (
        f"This decision ensures consistency in {purpose} across the codebase. "
        f"Using {tech1} with {tech2} provides better maintainability and "
        f"aligns with industry best practices for {domain.value} layer."
    )
    tags = list(set([tech1, tech2, purpose.split()[0]]))

    # Calculate document length for BM25
    doc_length = len(statement.split()) + len(rationale.split())

    return {
        "decision_id": f"decision-{idx:05d}",
        "code": f"{domain.value}-F{(idx % 16) + 1:02d}",
        "domain_id": domain.value,
        "statement": statement,
        "rationale": rationale,
        "tags": tags,
        "doc_length": doc_length,
    }


def generate_queries() -> List[Dict]:
    """Generate test queries with expected terms."""
    return [
        {"query": "react components", "expected": ["react"], "type": "short"},
        {"query": "database caching", "expected": ["database", "caching"], "type": "short"},
        {"query": "api authentication", "expected": ["api", "authentication"], "type": "short"},
        {"query": "react state management redux", "expected": ["react", "state"], "type": "medium"},
        {"query": "jwt authentication fastapi", "expected": ["jwt", "authentication"], "type": "medium"},
        {"query": "postgresql indexing optimization", "expected": ["postgresql", "indexing"], "type": "technical"},
        {"query": "kubernetes docker deployment", "expected": ["kubernetes", "docker"], "type": "technical"},
        {"query": "microservices architecture patterns", "expected": ["microservices", "architecture"], "type": "conceptual"},
        {"query": "event-driven design principles", "expected": ["event-driven"], "type": "conceptual"},
        {"query": "security authorization policies rbac", "expected": ["security", "authorization", "rbac"], "type": "long"},
    ]


# ============================================================================
# SEARCH SIMULATION (Base search - same as previous tests)
# ============================================================================

def simulate_vector_search(query: str, decisions: List[Dict]) -> Dict[str, float]:
    """Simulate vector search scores."""
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


def simulate_keyword_search(query: str, decisions: List[Dict]) -> Dict[str, float]:
    """Simulate keyword search scores."""
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


def linear_fusion(
    scores_list: List[Dict[str, float]],
    weights: List[float]
) -> List[Tuple[str, float]]:
    """Weighted linear fusion - use 10/90 as base."""
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


def calculate_relevance(
    results: List[Tuple[str, float]],
    decisions: List[Dict],
    expected: List[str]
) -> float:
    """Calculate relevance score for results."""
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
    max_possible = sum(weights[:len(results)])
    return total / max_possible if max_possible > 0 else 0


# ============================================================================
# ADVANCED RERANKING METHODS
# ============================================================================

def tfidf_rerank(
    query: str,
    results: List[Tuple[str, float]],
    decisions: List[Dict],
    top_n: int,
    blend_ratio: float = 0.3,  # original score weight (rerank weight = 1 - blend_ratio)
) -> List[Tuple[str, float]]:
    """
    TF-IDF style reranking.

    Args:
        blend_ratio: Weight for original score (0.3 means 30% original, 70% rerank)
    """
    decision_map = {d["decision_id"]: d for d in decisions}
    query_terms = query.lower().split()
    query_term_set = set(query_terms)

    # Calculate IDF (simple: log(N/df))
    N = len(decisions)
    doc_freq = defaultdict(int)
    for d in decisions:
        text = d["statement"].lower() + " " + d["rationale"].lower()
        doc_terms = set(text.split())
        for term in query_term_set:
            if term in doc_terms:
                doc_freq[term] += 1

    idf = {}
    for term in query_term_set:
        df = doc_freq.get(term, 0)
        idf[term] = math.log((N + 1) / (df + 1)) if df > 0 else 0

    reranked = []
    for doc_id, orig_score in results[:top_n * 2]:
        if doc_id not in decision_map:
            continue
        d = decision_map[doc_id]
        text = d["statement"].lower() + " " + d["rationale"].lower()
        text_terms = text.split()
        text_term_count = defaultdict(int)
        for t in text_terms:
            text_term_count[t] += 1

        # Calculate TF-IDF score
        tfidf_score = 0.0
        for term in query_term_set:
            tf = text_term_count.get(term, 0) / len(text_terms) if text_terms else 0
            tfidf_score += tf * idf.get(term, 0)

        # Normalize
        if query_term_set:
            tfidf_score /= len(query_term_set)

        # Blend with original
        final = blend_ratio * orig_score + (1 - blend_ratio) * tfidf_score
        reranked.append((doc_id, final))

    reranked.sort(key=lambda x: x[1], reverse=True)
    return reranked[:top_n]


def crossencoder_rerank(
    query: str,
    results: List[Tuple[str, float]],
    decisions: List[Dict],
    top_n: int,
    blend_ratio: float = 0.3,  # original score weight
) -> List[Tuple[str, float]]:
    """
    Simulated Cross-Encoder reranking.

    Simulates cross-encoder behavior with:
    - Term overlap score
    - Phrase matching bonus
    - Tag matching bonus
    - Semantic similarity simulation
    """
    decision_map = {d["decision_id"]: d for d in decisions}
    query_terms = set(query.lower().split())
    query_words = query.lower().split()

    reranked = []
    for doc_id, orig_score in results[:top_n * 3]:
        if doc_id not in decision_map:
            continue
        d = decision_map[doc_id]
        text = d["statement"].lower() + " " + d["rationale"].lower()
        doc_terms = set(text.split())

        # 1. Term overlap
        term_overlap = len(query_terms & doc_terms) / len(query_terms) if query_terms else 0

        # 2. Phrase bonus (bigram matching)
        phrase_bonus = 0.0
        for i in range(len(query_words) - 1):
            phrase = " ".join(query_words[i:i+2])
            if phrase in text:
                phrase_bonus += 0.15

        # 3. Tag bonus
        tag_bonus = sum(0.1 for t in d.get("tags", []) if t.lower() in query.lower())

        # 4. Semantic similarity simulation (domain alignment)
        domain_bonus = 0.0
        if d.get("domain_id", "").lower() in query.lower():
            domain_bonus = 0.1

        # Simulate cross-encoder score
        ce_score = min(1.0, term_overlap + phrase_bonus + tag_bonus + domain_bonus + random.uniform(0, 0.05))

        # Blend
        final = blend_ratio * orig_score + (1 - blend_ratio) * ce_score
        reranked.append((doc_id, final))

    reranked.sort(key=lambda x: x[1], reverse=True)
    return reranked[:top_n]


def bm25_rerank(
    query: str,
    results: List[Tuple[str, float]],
    decisions: List[Dict],
    top_n: int,
    k1: float = 1.2,
    b: float = 0.75,
    blend_ratio: float = 0.3,
) -> List[Tuple[str, float]]:
    """
    BM25 reranking simulation.

    BM25 formula: sum(IDF(qi) * (f(qi,D) * (k1+1)) / (f(qi,D) + k1*(1-b+b*|D|/avgdl)))

    Args:
        k1: Term frequency saturation parameter (typical: 1.2-2.0)
        b: Length normalization parameter (typical: 0.75)
    """
    decision_map = {d["decision_id"]: d for d in decisions}
    query_terms = query.lower().split()
    query_term_set = set(query_terms)

    # Calculate avgdl (average document length)
    avgdl = sum(d.get("doc_length", 20) for d in decisions) / len(decisions) if decisions else 20

    # Calculate IDF for each query term
    N = len(decisions)
    doc_freq = defaultdict(int)
    for d in decisions:
        text = d["statement"].lower() + " " + d["rationale"].lower()
        doc_terms = set(text.split())
        for term in query_term_set:
            if term in doc_terms:
                doc_freq[term] += 1

    # BM25 IDF: log((N - n(qi) + 0.5) / (n(qi) + 0.5))
    idf = {}
    for term in query_term_set:
        n_qi = doc_freq.get(term, 0)
        idf[term] = math.log((N - n_qi + 0.5) / (n_qi + 0.5) + 1)

    reranked = []
    for doc_id, orig_score in results[:top_n * 2]:
        if doc_id not in decision_map:
            continue
        d = decision_map[doc_id]
        text = d["statement"].lower() + " " + d["rationale"].lower()
        text_terms = text.split()
        doc_len = d.get("doc_length", len(text_terms))

        # Count term frequencies
        term_freq = defaultdict(int)
        for t in text_terms:
            term_freq[t] += 1

        # Calculate BM25 score
        bm25_score = 0.0
        for term in query_term_set:
            f_qi = term_freq.get(term, 0)
            if f_qi > 0:
                numerator = f_qi * (k1 + 1)
                denominator = f_qi + k1 * (1 - b + b * (doc_len / avgdl))
                bm25_score += idf.get(term, 0) * (numerator / denominator)

        # Normalize to 0-1 range (approximate)
        max_possible = len(query_term_set) * (k1 + 1) * max(idf.values()) if idf else 1
        bm25_score = min(1.0, bm25_score / max_possible) if max_possible > 0 else 0

        # Blend
        final = blend_ratio * orig_score + (1 - blend_ratio) * bm25_score
        reranked.append((doc_id, final))

    reranked.sort(key=lambda x: x[1], reverse=True)
    return reranked[:top_n]


def cascaded_rerank(
    query: str,
    results: List[Tuple[str, float]],
    decisions: List[Dict],
    stage1_top_n: int,
    stage2_top_n: int,
    stage1_method: str = "tfidf",
    stage2_method: str = "crossencoder",
    blend_ratio: float = 0.3,
) -> List[Tuple[str, float]]:
    """
    Cascaded reranking: Stage 1 filters, Stage 2 refines.

    Example: TF-IDF first (fast, broad), then CrossEncoder on top results (slow, precise)
    """
    # Stage 1: Broad filtering
    if stage1_method == "tfidf":
        stage1_results = tfidf_rerank(query, results, decisions, stage1_top_n, blend_ratio=0.4)
    elif stage1_method == "bm25":
        stage1_results = bm25_rerank(query, results, decisions, stage1_top_n, blend_ratio=0.4)
    else:
        stage1_results = results[:stage1_top_n]

    # Stage 2: Precise reranking on filtered set
    if stage2_method == "crossencoder":
        final_results = crossencoder_rerank(query, stage1_results, decisions, stage2_top_n, blend_ratio)
    elif stage2_method == "bm25":
        final_results = bm25_rerank(query, stage1_results, decisions, stage2_top_n, blend_ratio=blend_ratio)
    else:
        final_results = tfidf_rerank(query, stage1_results, decisions, stage2_top_n, blend_ratio)

    return final_results


# ============================================================================
# RERANKING CONFIGURATION
# ============================================================================

@dataclass
class RerankConfig:
    """Reranking configuration."""
    name: str
    method: str  # "none", "tfidf", "crossencoder", "bm25", "cascaded"
    top_n: int = 30
    blend_ratio: float = 0.3  # Weight for original score
    min_candidates: int = 5  # Minimum candidates before reranking
    # BM25 specific
    bm25_k1: float = 1.2
    bm25_b: float = 0.75
    # Cascaded specific
    cascade_stage1_method: str = "tfidf"
    cascade_stage1_top_n: int = 50
    cascade_stage2_method: str = "crossencoder"


def apply_reranking(
    config: RerankConfig,
    query: str,
    results: List[Tuple[str, float]],
    decisions: List[Dict],
) -> List[Tuple[str, float]]:
    """Apply reranking based on configuration."""
    # Check minimum candidates threshold
    if len(results) < config.min_candidates:
        return results[:config.top_n]

    if config.method == "none":
        return results[:config.top_n]
    elif config.method == "tfidf":
        return tfidf_rerank(query, results, decisions, config.top_n, config.blend_ratio)
    elif config.method == "crossencoder":
        return crossencoder_rerank(query, results, decisions, config.top_n, config.blend_ratio)
    elif config.method == "bm25":
        return bm25_rerank(
            query, results, decisions, config.top_n,
            k1=config.bm25_k1, b=config.bm25_b, blend_ratio=config.blend_ratio
        )
    elif config.method == "cascaded":
        return cascaded_rerank(
            query, results, decisions,
            stage1_top_n=config.cascade_stage1_top_n,
            stage2_top_n=config.top_n,
            stage1_method=config.cascade_stage1_method,
            stage2_method=config.cascade_stage2_method,
            blend_ratio=config.blend_ratio,
        )
    else:
        return results[:config.top_n]


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_config(
    config: RerankConfig,
    decisions: List[Dict],
    queries: List[Dict],
    runs_per_query: int = 5,
) -> Tuple[float, float, float]:
    """Run configuration and return (avg_relevance, std_dev, avg_latency)."""
    relevances = []
    latencies = []

    for q in queries:
        for _ in range(runs_per_query):
            start = time.time()

            # Base search with Linear 10/90 fusion
            vector = simulate_vector_search(q["query"], decisions)
            keyword = simulate_keyword_search(q["query"], decisions)
            fused = linear_fusion([vector, keyword], [0.1, 0.9])

            # Apply reranking
            results = apply_reranking(config, q["query"], fused, decisions)

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
    print("MANTRA Advanced Reranking Strategy Explorer (Agent 3)")
    print("=" * 80)
    print()
    print("Base Configuration: Linear-10/90 Fusion (Vector 10%, Keyword 90%)")
    print()

    # Generate test data
    print("Generating test data...")
    decisions = [generate_decision(i) for i in range(1000)]
    queries = generate_queries()
    print(f"  Decisions: {len(decisions)}")
    print(f"  Queries: {len(queries)}")
    print()

    all_results = []

    # =========================================================================
    # PHASE 1: rerank_top_n Sweep
    # =========================================================================
    print("=" * 60)
    print("PHASE 1: Rerank Top-N Sweep")
    print("-" * 60)

    top_n_values = [10, 15, 20, 25, 30, 40, 50, 75, 100]

    for top_n in top_n_values:
        config = RerankConfig(
            name=f"CrossEncoder@{top_n}",
            method="crossencoder",
            top_n=top_n,
            blend_ratio=0.3,
        )
        rel, std, lat = run_config(config, decisions, queries)
        all_results.append((config.name, rel, std, lat, config))
        print(f"  top_n={top_n:3d}: Relevance={rel:.4f} +/- {std:.4f} | Latency={lat:.2f}ms")

    best_top_n = max(all_results, key=lambda x: x[1])
    optimal_top_n = best_top_n[4].top_n
    print(f"\n  BEST top_n: {optimal_top_n} (Relevance: {best_top_n[1]:.4f})")

    # =========================================================================
    # PHASE 2: Blend Ratio Sweep
    # =========================================================================
    print("\n" + "=" * 60)
    print("PHASE 2: Blend Ratio Sweep (Original vs Rerank)")
    print("-" * 60)
    print("  blend_ratio = weight for original score")
    print("  (1 - blend_ratio) = weight for rerank score")
    print()

    blend_ratios = [0.1, 0.2, 0.3, 0.4, 0.5]  # original score weight

    blend_results = []
    for blend in blend_ratios:
        config = RerankConfig(
            name=f"CE@{optimal_top_n}+blend{int(blend*100)}/{int((1-blend)*100)}",
            method="crossencoder",
            top_n=optimal_top_n,
            blend_ratio=blend,
        )
        rel, std, lat = run_config(config, decisions, queries)
        blend_results.append((config.name, rel, std, lat, config))
        print(f"  {int(blend*100)}/{int((1-blend)*100)} (orig/rerank): Relevance={rel:.4f} | Latency={lat:.2f}ms")

    best_blend = max(blend_results, key=lambda x: x[1])
    optimal_blend = best_blend[4].blend_ratio
    all_results.extend(blend_results)
    print(f"\n  BEST blend: {int(optimal_blend*100)}/{int((1-optimal_blend)*100)} (Relevance: {best_blend[1]:.4f})")

    # =========================================================================
    # PHASE 3: BM25 Parameter Tuning
    # =========================================================================
    print("\n" + "=" * 60)
    print("PHASE 3: BM25 Parameter Tuning")
    print("-" * 60)
    print("  k1 = term frequency saturation (typical: 1.2-2.0)")
    print("  b = length normalization (typical: 0.5-0.9)")
    print()

    k1_values = [0.5, 1.0, 1.2, 1.5, 2.0]
    b_values = [0.5, 0.65, 0.75, 0.85, 0.95]

    bm25_results = []
    best_bm25_score = 0
    best_bm25_params = (1.2, 0.75)

    for k1 in k1_values:
        for b in b_values:
            config = RerankConfig(
                name=f"BM25(k1={k1},b={b})",
                method="bm25",
                top_n=optimal_top_n,
                blend_ratio=optimal_blend,
                bm25_k1=k1,
                bm25_b=b,
            )
            rel, std, lat = run_config(config, decisions, queries, runs_per_query=3)
            bm25_results.append((config.name, rel, std, lat, config))
            if rel > best_bm25_score:
                best_bm25_score = rel
                best_bm25_params = (k1, b)

    # Print top 5 BM25 configs
    bm25_sorted = sorted(bm25_results, key=lambda x: x[1], reverse=True)[:5]
    print("  Top 5 BM25 configurations:")
    for name, rel, std, lat, _ in bm25_sorted:
        print(f"    {name}: Relevance={rel:.4f}")

    all_results.extend(bm25_results)
    print(f"\n  BEST BM25: k1={best_bm25_params[0]}, b={best_bm25_params[1]} (Relevance: {best_bm25_score:.4f})")

    # =========================================================================
    # PHASE 4: Cascaded Reranking
    # =========================================================================
    print("\n" + "=" * 60)
    print("PHASE 4: Cascaded Reranking Strategies")
    print("-" * 60)
    print("  Stage 1: Fast filter (TF-IDF or BM25)")
    print("  Stage 2: Precise rerank (CrossEncoder)")
    print()

    cascade_configs = [
        ("TF-IDF->CE", "tfidf", "crossencoder", 50, 20),
        ("TF-IDF->CE", "tfidf", "crossencoder", 75, 30),
        ("TF-IDF->CE", "tfidf", "crossencoder", 100, 30),
        ("BM25->CE", "bm25", "crossencoder", 50, 20),
        ("BM25->CE", "bm25", "crossencoder", 75, 30),
        ("BM25->TF-IDF", "bm25", "tfidf", 75, 30),
    ]

    cascade_results = []
    for name_prefix, s1_method, s2_method, s1_top_n, s2_top_n in cascade_configs:
        config = RerankConfig(
            name=f"Cascade-{name_prefix}@{s1_top_n}->{s2_top_n}",
            method="cascaded",
            top_n=s2_top_n,
            blend_ratio=optimal_blend,
            cascade_stage1_method=s1_method,
            cascade_stage1_top_n=s1_top_n,
            cascade_stage2_method=s2_method,
            bm25_k1=best_bm25_params[0],
            bm25_b=best_bm25_params[1],
        )
        rel, std, lat = run_config(config, decisions, queries)
        cascade_results.append((config.name, rel, std, lat, config))
        print(f"  {config.name}: Relevance={rel:.4f} | Latency={lat:.2f}ms")

    best_cascade = max(cascade_results, key=lambda x: x[1])
    all_results.extend(cascade_results)
    print(f"\n  BEST Cascade: {best_cascade[0]} (Relevance: {best_cascade[1]:.4f})")

    # =========================================================================
    # PHASE 5: Minimum Candidates Threshold
    # =========================================================================
    print("\n" + "=" * 60)
    print("PHASE 5: Minimum Candidates Threshold")
    print("-" * 60)
    print("  Skip reranking if candidates < threshold (use original ranking)")
    print()

    min_candidates_values = [3, 5, 10, 15, 20]

    min_cand_results = []
    for min_cand in min_candidates_values:
        config = RerankConfig(
            name=f"CE@{optimal_top_n}+minCand{min_cand}",
            method="crossencoder",
            top_n=optimal_top_n,
            blend_ratio=optimal_blend,
            min_candidates=min_cand,
        )
        rel, std, lat = run_config(config, decisions, queries)
        min_cand_results.append((config.name, rel, std, lat, config))
        print(f"  min_candidates={min_cand:2d}: Relevance={rel:.4f} | Latency={lat:.2f}ms")

    best_min_cand = max(min_cand_results, key=lambda x: x[1])
    all_results.extend(min_cand_results)
    print(f"\n  BEST min_candidates: {best_min_cand[4].min_candidates}")

    # =========================================================================
    # PHASE 6: Method Comparison with Optimal Parameters
    # =========================================================================
    print("\n" + "=" * 60)
    print("PHASE 6: Final Method Comparison")
    print("-" * 60)

    final_configs = [
        RerankConfig(
            name="Baseline (No Rerank)",
            method="none",
            top_n=optimal_top_n,
        ),
        RerankConfig(
            name="TF-IDF (Optimized)",
            method="tfidf",
            top_n=optimal_top_n,
            blend_ratio=optimal_blend,
        ),
        RerankConfig(
            name="CrossEncoder (Optimized)",
            method="crossencoder",
            top_n=optimal_top_n,
            blend_ratio=optimal_blend,
            min_candidates=best_min_cand[4].min_candidates,
        ),
        RerankConfig(
            name="BM25 (Optimized)",
            method="bm25",
            top_n=optimal_top_n,
            blend_ratio=optimal_blend,
            bm25_k1=best_bm25_params[0],
            bm25_b=best_bm25_params[1],
        ),
        RerankConfig(
            name="Cascaded (Optimized)",
            method="cascaded",
            top_n=best_cascade[4].top_n,
            blend_ratio=optimal_blend,
            cascade_stage1_method=best_cascade[4].cascade_stage1_method,
            cascade_stage1_top_n=best_cascade[4].cascade_stage1_top_n,
            cascade_stage2_method=best_cascade[4].cascade_stage2_method,
            bm25_k1=best_bm25_params[0],
            bm25_b=best_bm25_params[1],
        ),
    ]

    final_results = []
    for config in final_configs:
        rel, std, lat = run_config(config, decisions, queries, runs_per_query=10)
        final_results.append((config.name, rel, std, lat, config))
        print(f"  {config.name:30}: Relevance={rel:.4f} +/- {std:.4f} | Latency={lat:.2f}ms")

    all_results.extend(final_results)

    # =========================================================================
    # FINAL RANKING & BEST CONFIGURATION
    # =========================================================================
    print("\n" + "=" * 80)
    print("FINAL RANKING: TOP 15 CONFIGURATIONS")
    print("=" * 80)

    all_sorted = sorted(all_results, key=lambda x: x[1], reverse=True)

    print(f"\n{'Rank':<5} {'Config':<50} {'Relevance':>10} {'StdDev':>10} {'Latency':>10}")
    print("-" * 85)

    for i, (name, rel, std, lat, _) in enumerate(all_sorted[:15], 1):
        print(f"{i:<5} {name:<50} {rel:>10.4f} {std:>10.4f} {lat:>8.2f}ms")

    # Best overall
    best = all_sorted[0]
    best_config = best[4]

    print("\n" + "=" * 80)
    print("OPTIMAL RERANKING CONFIGURATION")
    print("=" * 80)
    print(f"""
Configuration Name: {best[0]}
Relevance Score:    {best[1]:.4f} (+/- {best[2]:.4f})
Average Latency:    {best[3]:.2f}ms

Exact Parameters:
  - Rerank Method:       {best_config.method}
  - Top-N:               {best_config.top_n}
  - Blend Ratio:         {best_config.blend_ratio} ({int(best_config.blend_ratio*100)}% original, {int((1-best_config.blend_ratio)*100)}% rerank)
  - Min Candidates:      {best_config.min_candidates}
""")

    if best_config.method == "bm25":
        print(f"  - BM25 k1:             {best_config.bm25_k1}")
        print(f"  - BM25 b:              {best_config.bm25_b}")
    elif best_config.method == "cascaded":
        print(f"  - Stage 1 Method:      {best_config.cascade_stage1_method}")
        print(f"  - Stage 1 Top-N:       {best_config.cascade_stage1_top_n}")
        print(f"  - Stage 2 Method:      {best_config.cascade_stage2_method}")

    print(f"""
Python Configuration:
```python
# Base search: Linear fusion with 10% vector, 90% keyword
SearchConfig(
    fusion_mode=FusionMode.LINEAR,
    vector_weight=0.1,
    keyword_weight=0.9,
)

# Reranking configuration
RerankerConfig(
    method=RerankerMethod.{best_config.method.upper()},
    top_n={best_config.top_n},
    blend_ratio={best_config.blend_ratio},
    min_candidates={best_config.min_candidates},
""")

    if best_config.method == "bm25":
        print(f"    bm25_k1={best_config.bm25_k1},")
        print(f"    bm25_b={best_config.bm25_b},")
    elif best_config.method == "cascaded":
        print(f"    cascade_stage1_method=\"{best_config.cascade_stage1_method}\",")
        print(f"    cascade_stage1_top_n={best_config.cascade_stage1_top_n},")
        print(f"    cascade_stage2_method=\"{best_config.cascade_stage2_method}\",")

    print(")")
    print("```")

    # Compare with baseline
    baseline = next((r for r in final_results if "No Rerank" in r[0]), None)
    if baseline:
        improvement = ((best[1] - baseline[1]) / baseline[1]) * 100 if baseline[1] > 0 else 0
        print(f"\nImprovement over baseline: +{improvement:.1f}%")

    # Save results
    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "base_fusion": {
            "method": "linear",
            "vector_weight": 0.1,
            "keyword_weight": 0.9,
        },
        "best_reranking_config": {
            "name": best[0],
            "relevance": best[1],
            "std_dev": best[2],
            "latency_ms": best[3],
            "parameters": {
                "method": best_config.method,
                "top_n": best_config.top_n,
                "blend_ratio": best_config.blend_ratio,
                "min_candidates": best_config.min_candidates,
                "bm25_k1": best_config.bm25_k1,
                "bm25_b": best_config.bm25_b,
                "cascade_stage1_method": best_config.cascade_stage1_method,
                "cascade_stage1_top_n": best_config.cascade_stage1_top_n,
                "cascade_stage2_method": best_config.cascade_stage2_method,
            }
        },
        "phase_winners": {
            "top_n_sweep": {
                "best_top_n": optimal_top_n,
                "relevance": best_top_n[1],
            },
            "blend_ratio_sweep": {
                "best_blend": optimal_blend,
                "relevance": best_blend[1],
            },
            "bm25_tuning": {
                "best_k1": best_bm25_params[0],
                "best_b": best_bm25_params[1],
                "relevance": best_bm25_score,
            },
            "cascaded": {
                "best_config": best_cascade[0],
                "relevance": best_cascade[1],
            },
        },
        "top_15_results": [
            {"name": n, "relevance": r, "std": s, "latency": l}
            for n, r, s, l, _ in all_sorted[:15]
        ],
    }

    with open("/mnt/f/WINDSURF/neliti_code/signate/ARSAKA_MANTRA/backend/reranking_optimization_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to reranking_optimization_results.json")
    print("=" * 80)


if __name__ == "__main__":
    main()
