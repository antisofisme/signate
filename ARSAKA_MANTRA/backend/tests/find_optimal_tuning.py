#!/usr/bin/env python3
"""
MANTRA Optimal Tuning Finder

Grid search untuk menemukan konfigurasi TERBAIK:
1. Vector/Keyword weight: 0.0 - 1.0 (step 0.1)
2. RRF k: 10, 30, 60, 100, 200, 500
3. Rerank top_n: 10, 20, 30, 50
4. Min score threshold: 0.1, 0.2, 0.3, 0.4
5. Boost multi-source: 1.0, 1.1, 1.2, 1.3, 1.5

Output: Best configuration dengan confidence interval
"""

import sys
import time
import random
import hashlib
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from enum import Enum
import json
from itertools import product

# Set seed for reproducibility
random.seed(42)

# ============================================================================
# TEST DATA (Same as stress test)
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
        {"query": "security authorization", "expected": ["security", "authorization"]},
    ]

# ============================================================================
# SEARCH SIMULATION
# ============================================================================

def simulate_vector_search(query: str, decisions: List[Dict]) -> Dict[str, float]:
    query_terms = set(query.lower().split())
    scores = {}
    for d in decisions:
        doc_terms = set(d["statement"].lower().split() + d["rationale"].lower().split() + d.get("tags", []))
        overlap = len(query_terms & doc_terms)
        total = len(query_terms | doc_terms)
        score = overlap / total if total > 0 else 0
        noise = random.uniform(-0.1, 0.1)
        score = max(0, min(1, score + noise))
        if score > 0.05:
            scores[d["decision_id"]] = score
    return scores

def simulate_keyword_search(query: str, decisions: List[Dict]) -> Dict[str, float]:
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
# FUSION METHODS
# ============================================================================

def rrf_fusion(scores_list: List[Dict[str, float]], k: int = 60) -> List[Tuple[str, float]]:
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

def linear_fusion(scores_list: List[Dict[str, float]], weights: List[float]) -> List[Tuple[str, float]]:
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
# RERANKING
# ============================================================================

def tfidf_rerank(query: str, results: List[Tuple[str, float]], decisions: List[Dict], top_k: int) -> List[Tuple[str, float]]:
    decision_map = {d["decision_id"]: d for d in decisions}
    query_terms = set(query.lower().split())

    reranked = []
    for doc_id, orig_score in results[:top_k * 2]:
        if doc_id not in decision_map:
            continue
        d = decision_map[doc_id]
        text = d["statement"].lower() + " " + d["rationale"].lower()
        doc_terms = set(text.split())
        overlap = len(query_terms & doc_terms)
        tf_score = overlap / len(query_terms) if query_terms else 0
        final = 0.6 * tf_score + 0.4 * orig_score
        reranked.append((doc_id, final))

    reranked.sort(key=lambda x: x[1], reverse=True)
    return reranked[:top_k]

def crossencoder_rerank(query: str, results: List[Tuple[str, float]], decisions: List[Dict], top_k: int) -> List[Tuple[str, float]]:
    decision_map = {d["decision_id"]: d for d in decisions}
    query_terms = set(query.lower().split())

    reranked = []
    for doc_id, orig_score in results[:top_k * 3]:
        if doc_id not in decision_map:
            continue
        d = decision_map[doc_id]
        text = d["statement"].lower() + " " + d["rationale"].lower()
        doc_terms = set(text.split())

        term_overlap = len(query_terms & doc_terms) / len(query_terms) if query_terms else 0

        # Phrase bonus
        phrase_bonus = 0.0
        words = query.lower().split()
        for i in range(len(words) - 1):
            phrase = " ".join(words[i:i+2])
            if phrase in text:
                phrase_bonus += 0.15

        # Tag bonus
        tag_bonus = sum(0.1 for t in d.get("tags", []) if t.lower() in query.lower())

        ce_score = min(1.0, term_overlap + phrase_bonus + tag_bonus + random.uniform(0, 0.05))
        final = 0.7 * ce_score + 0.3 * orig_score
        reranked.append((doc_id, final))

    reranked.sort(key=lambda x: x[1], reverse=True)
    return reranked[:top_k]

# ============================================================================
# GRID SEARCH
# ============================================================================

@dataclass
class Config:
    name: str
    fusion: str  # "rrf" or "linear"
    vector_weight: float = 0.5
    keyword_weight: float = 0.5
    rrf_k: int = 60
    rerank: str = "none"  # "none", "tfidf", "crossencoder"
    rerank_top_n: int = 30
    min_score: float = 0.3
    boost_multi: float = 1.2

def run_config(config: Config, decisions: List[Dict], queries: List[Dict]) -> Tuple[float, float, float]:
    """Run config and return (avg_relevance, std_dev, avg_latency)"""
    relevances = []
    latencies = []

    for q in queries:
        for _ in range(3):  # 3 runs per query
            start = time.time()

            # Search
            vector = simulate_vector_search(q["query"], decisions)
            keyword = simulate_keyword_search(q["query"], decisions)

            # Fusion
            if config.fusion == "rrf":
                fused = rrf_fusion([vector, keyword], k=config.rrf_k)
            else:
                fused = linear_fusion([vector, keyword], [config.vector_weight, config.keyword_weight])

            # Apply min_score filter
            fused = [(d, s) for d, s in fused if s >= config.min_score * 0.01]  # Scale threshold

            # Boost multi-source
            vector_ids = set(vector.keys())
            keyword_ids = set(keyword.keys())
            boosted = []
            for doc_id, score in fused:
                if doc_id in vector_ids and doc_id in keyword_ids:
                    score *= config.boost_multi
                boosted.append((doc_id, score))
            boosted.sort(key=lambda x: x[1], reverse=True)

            # Rerank
            if config.rerank == "tfidf":
                results = tfidf_rerank(q["query"], boosted, decisions, config.rerank_top_n)
            elif config.rerank == "crossencoder":
                results = crossencoder_rerank(q["query"], boosted, decisions, config.rerank_top_n)
            else:
                results = boosted[:config.rerank_top_n]

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
    print("MANTRA Optimal Tuning Finder - Grid Search")
    print("=" * 80)
    print()

    # Generate test data
    print("Generating test data...")
    decisions = [generate_decision(i) for i in range(1000)]
    queries = generate_queries()
    print(f"  Decisions: {len(decisions)}")
    print(f"  Queries: {len(queries)}")
    print()

    # Define search space
    vector_weights = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    rrf_k_values = [10, 30, 60, 100, 200, 500]
    rerank_methods = ["none", "tfidf", "crossencoder"]
    rerank_top_n = [20, 30, 50]
    boost_multi_values = [1.0, 1.1, 1.2, 1.3, 1.5]

    results = []

    # =========================================================================
    # PHASE 1: Linear Fusion Weight Sweep
    # =========================================================================
    print("PHASE 1: Linear Fusion Weight Sweep")
    print("-" * 60)

    for vw in vector_weights:
        kw = 1.0 - vw
        config = Config(
            name=f"Linear-{int(vw*100)}/{int(kw*100)}",
            fusion="linear",
            vector_weight=vw,
            keyword_weight=kw,
        )
        rel, std, lat = run_config(config, decisions, queries)
        results.append((config.name, rel, std, lat, config))
        print(f"  {config.name:20} | Relevance: {rel:.4f} ± {std:.4f} | Latency: {lat:.2f}ms")

    # Find best linear weight
    best_linear = max(results, key=lambda x: x[1])
    print(f"\n  BEST LINEAR: {best_linear[0]} (Relevance: {best_linear[1]:.4f})")

    # =========================================================================
    # PHASE 2: RRF k-value Sweep
    # =========================================================================
    print("\n" + "=" * 60)
    print("PHASE 2: RRF k-value Sweep")
    print("-" * 60)

    rrf_results = []
    for k in rrf_k_values:
        config = Config(
            name=f"RRF-k{k}",
            fusion="rrf",
            rrf_k=k,
        )
        rel, std, lat = run_config(config, decisions, queries)
        rrf_results.append((config.name, rel, std, lat, config))
        print(f"  {config.name:20} | Relevance: {rel:.4f} ± {std:.4f} | Latency: {lat:.2f}ms")

    best_rrf = max(rrf_results, key=lambda x: x[1])
    print(f"\n  BEST RRF: {best_rrf[0]} (Relevance: {best_rrf[1]:.4f})")
    results.extend(rrf_results)

    # =========================================================================
    # PHASE 3: Reranking Impact (on best configs)
    # =========================================================================
    print("\n" + "=" * 60)
    print("PHASE 3: Reranking Impact")
    print("-" * 60)

    # Test reranking on best linear config
    best_vw = best_linear[4].vector_weight
    best_kw = best_linear[4].keyword_weight

    rerank_results = []
    for rerank in rerank_methods:
        for top_n in rerank_top_n:
            config = Config(
                name=f"Linear-{int(best_vw*100)}/{int(best_kw*100)}+{rerank}@{top_n}",
                fusion="linear",
                vector_weight=best_vw,
                keyword_weight=best_kw,
                rerank=rerank,
                rerank_top_n=top_n,
            )
            rel, std, lat = run_config(config, decisions, queries)
            rerank_results.append((config.name, rel, std, lat, config))
            print(f"  {config.name:40} | Rel: {rel:.4f} | Lat: {lat:.2f}ms")

    best_rerank = max(rerank_results, key=lambda x: x[1])
    print(f"\n  BEST RERANK: {best_rerank[0]} (Relevance: {best_rerank[1]:.4f})")
    results.extend(rerank_results)

    # =========================================================================
    # PHASE 4: Boost Multi-Source Tuning
    # =========================================================================
    print("\n" + "=" * 60)
    print("PHASE 4: Boost Multi-Source Tuning")
    print("-" * 60)

    best_config = best_rerank[4]
    boost_results = []
    for boost in boost_multi_values:
        config = Config(
            name=f"{best_config.name}+boost{boost}",
            fusion=best_config.fusion,
            vector_weight=best_config.vector_weight,
            keyword_weight=best_config.keyword_weight,
            rerank=best_config.rerank,
            rerank_top_n=best_config.rerank_top_n,
            boost_multi=boost,
        )
        rel, std, lat = run_config(config, decisions, queries)
        boost_results.append((config.name, rel, std, lat, config))
        print(f"  boost={boost}: Relevance: {rel:.4f}")

    best_boost = max(boost_results, key=lambda x: x[1])
    print(f"\n  BEST BOOST: {best_boost[4].boost_multi} (Relevance: {best_boost[1]:.4f})")
    results.extend(boost_results)

    # =========================================================================
    # FINAL: Combined Best Configuration
    # =========================================================================
    print("\n" + "=" * 80)
    print("FINAL RESULTS: TOP 10 CONFIGURATIONS")
    print("=" * 80)

    # Sort all results
    all_sorted = sorted(results, key=lambda x: x[1], reverse=True)

    print(f"\n{'Rank':<5} {'Config':<45} {'Relevance':>10} {'StdDev':>10} {'Latency':>10}")
    print("-" * 80)

    for i, (name, rel, std, lat, _) in enumerate(all_sorted[:10], 1):
        print(f"{i:<5} {name:<45} {rel:>10.4f} {std:>10.4f} {lat:>8.2f}ms")

    # Best overall
    best = all_sorted[0]
    best_config = best[4]

    print("\n" + "=" * 80)
    print("OPTIMAL CONFIGURATION")
    print("=" * 80)
    print(f"""
Config Name: {best[0]}
Relevance:   {best[1]:.4f} (± {best[2]:.4f})
Latency:     {best[3]:.2f}ms

Settings:
  - Fusion Method:    {best_config.fusion}
  - Vector Weight:    {best_config.vector_weight}
  - Keyword Weight:   {best_config.keyword_weight}
  - RRF k:            {best_config.rrf_k}
  - Rerank Method:    {best_config.rerank}
  - Rerank Top-N:     {best_config.rerank_top_n}
  - Boost Multi:      {best_config.boost_multi}
  - Min Score:        {best_config.min_score}

Python Configuration:
```python
SearchConfig(
    fusion_mode = FusionMode.{"RRF" if best_config.fusion == "rrf" else "LINEAR"},
    vector_weight = {best_config.vector_weight},
    keyword_weight = {best_config.keyword_weight},
    rrf_k = {best_config.rrf_k},
    min_score = {best_config.min_score},
    boost_multi_source = {best_config.boost_multi},
)

RerankerConfig(
    method = RerankerMethod.{best_config.rerank.upper() if best_config.rerank != "none" else "NONE"},
    top_k = {best_config.rerank_top_n},
)
```
""")

    # Save results
    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "best_config": {
            "name": best[0],
            "relevance": best[1],
            "std_dev": best[2],
            "latency_ms": best[3],
            "settings": {
                "fusion": best_config.fusion,
                "vector_weight": best_config.vector_weight,
                "keyword_weight": best_config.keyword_weight,
                "rrf_k": best_config.rrf_k,
                "rerank": best_config.rerank,
                "rerank_top_n": best_config.rerank_top_n,
                "boost_multi": best_config.boost_multi,
            }
        },
        "all_results": [
            {"name": n, "relevance": r, "std": s, "latency": l}
            for n, r, s, l, _ in all_sorted[:20]
        ]
    }

    with open("optimal_tuning_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to optimal_tuning_results.json")
    print("=" * 80)

if __name__ == "__main__":
    main()
