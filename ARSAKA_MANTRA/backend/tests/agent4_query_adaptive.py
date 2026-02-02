#!/usr/bin/env python3
"""
MANTRA Query-Adaptive Retrieval Configuration Finder

Finds optimal retrieval configurations per QUERY TYPE:

Query Types Tested:
1. Short queries (1-2 words): "react", "api auth"
2. Long queries (5+ words): "how to implement jwt authentication in fastapi"
3. Technical queries: "postgresql indexing optimization"
4. Conceptual queries: "architecture patterns microservices"
5. Domain-specific: "ARCH frontend", "CTL security"
6. Exact match queries: "MUST use typescript"
7. Fuzzy queries: "databse caching" (typo)

For each query type:
- Test vector weights 0.0 to 0.5 (step 0.1)
- Test keyword weights 0.5 to 1.0 (step 0.1)
- Test with/without reranking
- Find the BEST config for that specific type

Output: mapping of query_type -> optimal_config with relevance scores
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
from collections import defaultdict

# Set seed for reproducibility
random.seed(42)


# ============================================================================
# QUERY TYPE DEFINITIONS
# ============================================================================

class QueryType(str, Enum):
    """Query types for adaptive configuration."""
    SHORT = "short"              # 1-2 words
    LONG = "long"                # 5+ words
    TECHNICAL = "technical"      # Technical terms
    CONCEPTUAL = "conceptual"    # Abstract concepts
    DOMAIN_SPECIFIC = "domain"   # Domain prefixes (ARCH, CTL, etc)
    EXACT_MATCH = "exact"        # Modal verbs (MUST, SHALL)
    FUZZY = "fuzzy"              # Contains typos


@dataclass
class QueryTestCase:
    """Test case for a specific query type."""
    query: str
    query_type: QueryType
    expected_keywords: List[str]
    expected_domain: Optional[str] = None
    has_typo: bool = False
    priority: str = "normal"  # "normal", "high", "critical"


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

ARCH_TERMS = [
    "architecture", "pattern", "design", "structure", "layer",
    "module", "component", "interface", "abstraction", "dependency",
]

CTL_TERMS = [
    "security", "validation", "constraint", "policy", "rule",
    "permission", "access", "control", "audit", "compliance",
]

MODAL_VERBS = ["MUST", "SHALL", "SHOULD", "MAY", "MUST NOT"]

STATEMENT_TEMPLATES = [
    "All {tech1} components MUST use {tech2} for {purpose}",
    "When implementing {purpose}, developers SHALL use {tech1}",
    "{tech1} services MUST implement {tech2} patterns",
    "Database operations MUST use {tech1} with {tech2} caching",
    "Frontend {purpose} SHALL follow {tech1} conventions",
    "API endpoints MUST implement {tech2} for {purpose}",
    "Security policies MUST enforce {tech1} for all {purpose}",
    "Architecture decisions SHALL consider {tech1} and {tech2}",
]

PURPOSES = [
    "data fetching", "state management", "error handling",
    "form validation", "routing", "authorization",
    "caching", "logging", "monitoring", "testing",
]


def generate_decisions(count: int = 1000) -> List[Dict[str, Any]]:
    """Generate test decisions."""
    decisions = []
    for idx in range(count):
        domain = random.choice(list(DecisionDomain))
        tech1 = random.choice(TECH_TERMS)
        tech2 = random.choice(TECH_TERMS)
        purpose = random.choice(PURPOSES)

        statement = random.choice(STATEMENT_TEMPLATES).format(
            tech1=tech1, tech2=tech2, purpose=purpose
        )
        rationale = f"This decision ensures consistency in {purpose}. Using {tech1} with {tech2} provides better maintainability."

        # Add domain-specific terms
        if domain == DecisionDomain.ARCH:
            arch_term = random.choice(ARCH_TERMS)
            statement += f" Following {arch_term} principles."
        elif domain == DecisionDomain.CTL:
            ctl_term = random.choice(CTL_TERMS)
            statement += f" Enforcing {ctl_term} requirements."

        decisions.append({
            "decision_id": f"decision-{idx:05d}",
            "code": f"{domain.value}-F{(idx % 16) + 1:02d}",
            "domain_id": domain.value,
            "statement": statement,
            "rationale": rationale,
            "tags": list(set([tech1, tech2, purpose.split()[0]])),
            "constraints": [{"rule": f"Use {tech1} for all {purpose}"}],
        })
    return decisions


def generate_query_test_cases() -> Dict[QueryType, List[QueryTestCase]]:
    """Generate test cases for each query type."""
    return {
        QueryType.SHORT: [
            QueryTestCase("react", QueryType.SHORT, ["react"]),
            QueryTestCase("api auth", QueryType.SHORT, ["api", "auth"]),
            QueryTestCase("jwt", QueryType.SHORT, ["jwt"]),
            QueryTestCase("redis", QueryType.SHORT, ["redis"]),
            QueryTestCase("caching", QueryType.SHORT, ["caching"]),
            QueryTestCase("testing", QueryType.SHORT, ["testing"]),
        ],

        QueryType.LONG: [
            QueryTestCase(
                "how to implement jwt authentication in fastapi",
                QueryType.LONG,
                ["jwt", "authentication", "fastapi"]
            ),
            QueryTestCase(
                "best practices for react state management with redux",
                QueryType.LONG,
                ["react", "state", "management", "redux"]
            ),
            QueryTestCase(
                "configuring postgresql database indexing for performance optimization",
                QueryType.LONG,
                ["postgresql", "database", "indexing", "performance", "optimization"]
            ),
            QueryTestCase(
                "implementing secure api authentication with oauth and jwt tokens",
                QueryType.LONG,
                ["api", "authentication", "oauth", "jwt"]
            ),
        ],

        QueryType.TECHNICAL: [
            QueryTestCase(
                "postgresql indexing optimization",
                QueryType.TECHNICAL,
                ["postgresql", "indexing", "optimization"]
            ),
            QueryTestCase(
                "kubernetes docker deployment",
                QueryType.TECHNICAL,
                ["kubernetes", "docker", "deployment"]
            ),
            QueryTestCase(
                "graphql api schema design",
                QueryType.TECHNICAL,
                ["graphql", "api", "schema"]
            ),
            QueryTestCase(
                "redis caching strategy",
                QueryType.TECHNICAL,
                ["redis", "caching"]
            ),
            QueryTestCase(
                "jwt token validation",
                QueryType.TECHNICAL,
                ["jwt", "token", "validation"]
            ),
        ],

        QueryType.CONCEPTUAL: [
            QueryTestCase(
                "architecture patterns microservices",
                QueryType.CONCEPTUAL,
                ["architecture", "patterns", "microservices"]
            ),
            QueryTestCase(
                "design principles clean code",
                QueryType.CONCEPTUAL,
                ["design", "principles"]
            ),
            QueryTestCase(
                "domain driven design concepts",
                QueryType.CONCEPTUAL,
                ["domain", "design", "ddd"]
            ),
            QueryTestCase(
                "event driven architecture patterns",
                QueryType.CONCEPTUAL,
                ["event-driven", "architecture", "patterns"]
            ),
        ],

        QueryType.DOMAIN_SPECIFIC: [
            QueryTestCase(
                "ARCH frontend components",
                QueryType.DOMAIN_SPECIFIC,
                ["frontend", "component"],
                expected_domain="ARCH"
            ),
            QueryTestCase(
                "CTL security validation",
                QueryType.DOMAIN_SPECIFIC,
                ["security", "validation"],
                expected_domain="CTL"
            ),
            QueryTestCase(
                "INT api integration",
                QueryType.DOMAIN_SPECIFIC,
                ["api", "integration"],
                expected_domain="INT"
            ),
            QueryTestCase(
                "EVO migration strategy",
                QueryType.DOMAIN_SPECIFIC,
                ["migration"],
                expected_domain="EVO"
            ),
        ],

        QueryType.EXACT_MATCH: [
            QueryTestCase(
                "MUST use typescript",
                QueryType.EXACT_MATCH,
                ["MUST", "typescript"],
                priority="critical"
            ),
            QueryTestCase(
                "SHALL implement authentication",
                QueryType.EXACT_MATCH,
                ["SHALL", "authentication"],
                priority="high"
            ),
            QueryTestCase(
                "MUST NOT bypass security",
                QueryType.EXACT_MATCH,
                ["MUST NOT", "security"],
                priority="critical"
            ),
            QueryTestCase(
                "SHOULD use caching",
                QueryType.EXACT_MATCH,
                ["SHOULD", "caching"],
                priority="normal"
            ),
        ],

        QueryType.FUZZY: [
            QueryTestCase(
                "databse caching",  # typo: database
                QueryType.FUZZY,
                ["database", "caching"],
                has_typo=True
            ),
            QueryTestCase(
                "authentiction jwt",  # typo: authentication
                QueryType.FUZZY,
                ["authentication", "jwt"],
                has_typo=True
            ),
            QueryTestCase(
                "kubernets docker",  # typo: kubernetes
                QueryType.FUZZY,
                ["kubernetes", "docker"],
                has_typo=True
            ),
            QueryTestCase(
                "postgrsql indexing",  # typo: postgresql
                QueryType.FUZZY,
                ["postgresql", "indexing"],
                has_typo=True
            ),
        ],
    }


# ============================================================================
# SEARCH SIMULATION
# ============================================================================

def simulate_vector_search(query: str, decisions: List[Dict], config: 'SearchConfig') -> Dict[str, float]:
    """Simulate vector/semantic search."""
    query_terms = set(query.lower().split())
    scores = {}

    for d in decisions:
        doc_terms = set(
            d["statement"].lower().split() +
            d["rationale"].lower().split() +
            d.get("tags", [])
        )

        # Jaccard similarity
        overlap = len(query_terms & doc_terms)
        total = len(query_terms | doc_terms)
        score = overlap / total if total > 0 else 0

        # Add noise to simulate embedding variations
        noise = random.uniform(-0.08, 0.08)
        score = max(0, min(1, score + noise))

        # Fuzzy matching bonus (semantic similarity would catch typos)
        if config.fuzzy_boost > 0:
            for qt in query_terms:
                for dt in doc_terms:
                    if len(qt) > 3 and len(dt) > 3:
                        # Simple edit distance approximation
                        if qt[:3] == dt[:3] or qt[-3:] == dt[-3:]:
                            score += config.fuzzy_boost * 0.1

        if score > 0.05:
            scores[d["decision_id"]] = min(1.0, score)

    return scores


def simulate_keyword_search(query: str, decisions: List[Dict], config: 'SearchConfig') -> Dict[str, float]:
    """Simulate keyword/BM25 search."""
    query_terms = set(query.lower().split())
    query_original = set(query.split())  # Preserve case for modal verbs
    scores = {}

    for d in decisions:
        score = 0.0
        text = d["statement"].lower() + " " + d["rationale"].lower() + " " + " ".join(d.get("tags", []))
        text_original = d["statement"]  # Case-sensitive for modal verbs

        # Term matching
        for term in query_terms:
            if f" {term} " in f" {text} ":
                score += 0.35  # Exact word match
            elif term in text:
                score += 0.15  # Partial match

        # Tag matching (high weight)
        for tag in d.get("tags", []):
            if tag.lower() in query_terms:
                score += 0.4

        # Domain matching
        if any(d["domain_id"].lower() in qt.lower() for qt in query_terms):
            score += 0.3

        # Modal verb matching (exact, case-sensitive)
        for modal in MODAL_VERBS:
            if modal in query_original and modal in text_original:
                score += config.exact_match_boost * 0.5

        score = min(1.0, score / max(1, len(query_terms)))

        if score > 0.05:
            scores[d["decision_id"]] = score

    return scores


# ============================================================================
# FUSION & RERANKING
# ============================================================================

def rrf_fusion(scores_list: List[Dict[str, float]], k: int = 60) -> List[Tuple[str, float]]:
    """Reciprocal Rank Fusion."""
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
    """Weighted linear fusion."""
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


def tfidf_rerank(
    query: str,
    results: List[Tuple[str, float]],
    decisions: List[Dict],
    top_k: int
) -> List[Tuple[str, float]]:
    """TF-IDF based reranking."""
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

        # Blend: 60% TF-IDF, 40% original
        final = 0.6 * tf_score + 0.4 * orig_score
        reranked.append((doc_id, final))

    reranked.sort(key=lambda x: x[1], reverse=True)
    return reranked[:top_k]


def crossencoder_rerank(
    query: str,
    results: List[Tuple[str, float]],
    decisions: List[Dict],
    top_k: int
) -> List[Tuple[str, float]]:
    """Simulated cross-encoder reranking."""
    decision_map = {d["decision_id"]: d for d in decisions}
    query_terms = set(query.lower().split())

    reranked = []
    for doc_id, orig_score in results[:top_k * 3]:
        if doc_id not in decision_map:
            continue
        d = decision_map[doc_id]
        text = d["statement"].lower() + " " + d["rationale"].lower()
        doc_terms = set(text.split())

        # Term overlap
        term_overlap = len(query_terms & doc_terms) / len(query_terms) if query_terms else 0

        # Phrase bonus
        phrase_bonus = 0.0
        words = query.lower().split()
        for i in range(len(words) - 1):
            phrase = " ".join(words[i:i+2])
            if phrase in text:
                phrase_bonus += 0.12

        # Tag bonus
        tag_bonus = sum(0.1 for t in d.get("tags", []) if t.lower() in query.lower())

        # Simulate cross-encoder score
        ce_score = min(1.0, term_overlap + phrase_bonus + tag_bonus + random.uniform(0, 0.03))

        # Blend: 70% cross-encoder, 30% original
        final = 0.7 * ce_score + 0.3 * orig_score
        reranked.append((doc_id, final))

    reranked.sort(key=lambda x: x[1], reverse=True)
    return reranked[:top_k]


# ============================================================================
# RELEVANCE SCORING
# ============================================================================

def calculate_relevance(
    results: List[Tuple[str, float]],
    decisions: List[Dict],
    test_case: QueryTestCase
) -> float:
    """Calculate relevance score for a query."""
    if not results:
        return 0.0

    decision_map = {d["decision_id"]: d for d in decisions}
    expected_lower = [t.lower() for t in test_case.expected_keywords]

    # DCG-like weights (position matters)
    weights = [1.0, 0.85, 0.7, 0.55, 0.45, 0.35, 0.28, 0.22, 0.18, 0.15]

    total = 0.0
    domain_bonus = 0.0

    for i, (doc_id, _) in enumerate(results[:10]):
        weight = weights[i] if i < len(weights) else 0.1

        if doc_id in decision_map:
            d = decision_map[doc_id]
            text = (
                d["statement"].lower() + " " +
                d["rationale"].lower() + " " +
                " ".join(d.get("tags", []))
            )

            # Keyword matches
            matches = sum(1 for t in expected_lower if t in text)
            keyword_score = matches / len(expected_lower) if expected_lower else 0

            # Domain match bonus
            if test_case.expected_domain:
                if d["domain_id"] == test_case.expected_domain:
                    domain_bonus += weight * 0.3

            total += weight * keyword_score

    max_possible = sum(weights[:min(len(results), 10)])
    base_score = total / max_possible if max_possible > 0 else 0

    return min(1.0, base_score + domain_bonus)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class SearchConfig:
    """Search configuration for testing."""
    name: str
    fusion: str = "linear"  # "rrf" or "linear"
    vector_weight: float = 0.3
    keyword_weight: float = 0.7
    rrf_k: int = 60
    rerank: str = "none"  # "none", "tfidf", "crossencoder"
    rerank_top_n: int = 30
    min_score: float = 0.1
    boost_multi: float = 1.2
    exact_match_boost: float = 1.0
    fuzzy_boost: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fusion": self.fusion,
            "vector_weight": self.vector_weight,
            "keyword_weight": self.keyword_weight,
            "rrf_k": self.rrf_k,
            "rerank": self.rerank,
            "rerank_top_n": self.rerank_top_n,
            "min_score": self.min_score,
            "boost_multi": self.boost_multi,
            "exact_match_boost": self.exact_match_boost,
            "fuzzy_boost": self.fuzzy_boost,
        }


def generate_configs_for_type(query_type: QueryType) -> List[SearchConfig]:
    """Generate configuration grid for a specific query type."""
    configs = []

    # Vector weights: 0.0 to 0.5 (step 0.1)
    vector_weights = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    rerank_methods = ["none", "tfidf", "crossencoder"]

    # Base configs
    for vw in vector_weights:
        kw = 1.0 - vw

        for rerank in rerank_methods:
            # Configure based on query type
            config = SearchConfig(
                name=f"V{int(vw*100)}/K{int(kw*100)}-{rerank}",
                fusion="linear",
                vector_weight=vw,
                keyword_weight=kw,
                rerank=rerank,
            )

            # Type-specific adjustments
            if query_type == QueryType.EXACT_MATCH:
                config.exact_match_boost = 1.5
            elif query_type == QueryType.FUZZY:
                config.fuzzy_boost = 0.3
            elif query_type == QueryType.DOMAIN_SPECIFIC:
                config.boost_multi = 1.3

            configs.append(config)

    # Add RRF configs
    for rrf_k in [30, 60, 100]:
        for rerank in rerank_methods:
            config = SearchConfig(
                name=f"RRF-k{rrf_k}-{rerank}",
                fusion="rrf",
                rrf_k=rrf_k,
                rerank=rerank,
            )
            configs.append(config)

    return configs


# ============================================================================
# EVALUATION
# ============================================================================

def run_config(
    config: SearchConfig,
    decisions: List[Dict],
    test_cases: List[QueryTestCase],
    runs_per_query: int = 3
) -> Tuple[float, float, float]:
    """Run config and return (avg_relevance, std_dev, avg_latency)."""
    relevances = []
    latencies = []

    for tc in test_cases:
        for _ in range(runs_per_query):
            start = time.time()

            # Search
            vector = simulate_vector_search(tc.query, decisions, config)
            keyword = simulate_keyword_search(tc.query, decisions, config)

            # Fusion
            if config.fusion == "rrf":
                fused = rrf_fusion([vector, keyword], k=config.rrf_k)
            else:
                fused = linear_fusion(
                    [vector, keyword],
                    [config.vector_weight, config.keyword_weight]
                )

            # Filter by min score
            fused = [(d, s) for d, s in fused if s >= config.min_score * 0.01]

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
                results = tfidf_rerank(tc.query, boosted, decisions, config.rerank_top_n)
            elif config.rerank == "crossencoder":
                results = crossencoder_rerank(tc.query, boosted, decisions, config.rerank_top_n)
            else:
                results = boosted[:config.rerank_top_n]

            latency = (time.time() - start) * 1000
            relevance = calculate_relevance(results, decisions, tc)

            relevances.append(relevance)
            latencies.append(latency)

    avg_rel = statistics.mean(relevances)
    std_rel = statistics.stdev(relevances) if len(relevances) > 1 else 0
    avg_lat = statistics.mean(latencies)

    return avg_rel, std_rel, avg_lat


def find_optimal_for_type(
    query_type: QueryType,
    test_cases: List[QueryTestCase],
    decisions: List[Dict],
) -> Tuple[SearchConfig, Dict[str, Any]]:
    """Find optimal configuration for a specific query type."""
    configs = generate_configs_for_type(query_type)
    results = []

    print(f"  Testing {len(configs)} configurations...")

    for config in configs:
        rel, std, lat = run_config(config, decisions, test_cases)
        results.append({
            "config": config,
            "relevance": rel,
            "std_dev": std,
            "latency_ms": lat,
        })

    # Sort by relevance
    results.sort(key=lambda x: x["relevance"], reverse=True)

    best = results[0]

    return best["config"], {
        "relevance": best["relevance"],
        "std_dev": best["std_dev"],
        "latency_ms": best["latency_ms"],
        "top_5": [
            {
                "name": r["config"].name,
                "relevance": round(r["relevance"], 4),
            }
            for r in results[:5]
        ],
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("MANTRA Query-Adaptive Configuration Finder")
    print("=" * 80)
    print()

    # Generate test data
    print("Generating test data...")
    decisions = generate_decisions(1000)
    query_cases = generate_query_test_cases()
    print(f"  Decisions: {len(decisions)}")
    print(f"  Query Types: {len(query_cases)}")
    for qt, cases in query_cases.items():
        print(f"    - {qt.value}: {len(cases)} test cases")
    print()

    # Find optimal config for each query type
    optimal_configs: Dict[str, Dict[str, Any]] = {}

    print("=" * 80)
    print("PHASE 1: Finding Optimal Configurations Per Query Type")
    print("=" * 80)

    for query_type, test_cases in query_cases.items():
        print(f"\n{'='*60}")
        print(f"Query Type: {query_type.value.upper()}")
        print(f"{'='*60}")

        best_config, metrics = find_optimal_for_type(
            query_type, test_cases, decisions
        )

        optimal_configs[query_type.value] = {
            "config": best_config.to_dict(),
            "config_name": best_config.name,
            "metrics": metrics,
        }

        print(f"\n  BEST CONFIG: {best_config.name}")
        print(f"  Relevance:   {metrics['relevance']:.4f} (+/- {metrics['std_dev']:.4f})")
        print(f"  Latency:     {metrics['latency_ms']:.2f}ms")
        print(f"\n  Top 5 configs:")
        for i, cfg in enumerate(metrics['top_5'], 1):
            print(f"    {i}. {cfg['name']}: {cfg['relevance']:.4f}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY: OPTIMAL CONFIGURATIONS BY QUERY TYPE")
    print("=" * 80)

    print(f"\n{'Query Type':<20} {'Best Config':<30} {'Relevance':>12} {'Latency':>10}")
    print("-" * 72)

    for qt, data in optimal_configs.items():
        print(f"{qt:<20} {data['config_name']:<30} {data['metrics']['relevance']:>12.4f} {data['metrics']['latency_ms']:>8.2f}ms")

    # Generate adaptive config code
    print("\n" + "=" * 80)
    print("GENERATED ADAPTIVE CONFIGURATION")
    print("=" * 80)

    print("""
# Python Configuration for Query-Adaptive Retrieval

from dataclasses import dataclass
from typing import Optional
from enum import Enum

class QueryType(str, Enum):
    SHORT = "short"
    LONG = "long"
    TECHNICAL = "technical"
    CONCEPTUAL = "conceptual"
    DOMAIN_SPECIFIC = "domain"
    EXACT_MATCH = "exact"
    FUZZY = "fuzzy"

OPTIMAL_CONFIGS = {""")

    for qt, data in optimal_configs.items():
        cfg = data['config']
        print(f"""    QueryType.{qt.upper()}: SearchConfig(
        fusion="{cfg['fusion']}",
        vector_weight={cfg['vector_weight']},
        keyword_weight={cfg['keyword_weight']},
        rrf_k={cfg['rrf_k']},
        rerank="{cfg['rerank']}",
        rerank_top_n={cfg['rerank_top_n']},
    ),  # Relevance: {data['metrics']['relevance']:.4f}""")

    print("}")

    print("""

def detect_query_type(query: str) -> QueryType:
    '''Detect query type for adaptive config selection.'''
    words = query.split()

    # Short queries (1-2 words)
    if len(words) <= 2:
        return QueryType.SHORT

    # Long queries (5+ words)
    if len(words) >= 5:
        return QueryType.LONG

    # Domain-specific (ARCH, CTL, INT, EVO prefix)
    if words[0].upper() in ['ARCH', 'CTL', 'INT', 'EVO']:
        return QueryType.DOMAIN_SPECIFIC

    # Exact match (contains modal verbs)
    if any(modal in query for modal in ['MUST', 'SHALL', 'SHOULD', 'MAY']):
        return QueryType.EXACT_MATCH

    # Conceptual (contains abstract terms)
    conceptual_terms = ['architecture', 'pattern', 'design', 'principle', 'concept']
    if any(term in query.lower() for term in conceptual_terms):
        return QueryType.CONCEPTUAL

    # Default to technical
    return QueryType.TECHNICAL

def get_optimal_config(query: str) -> SearchConfig:
    '''Get optimal config for query.'''
    query_type = detect_query_type(query)
    return OPTIMAL_CONFIGS[query_type]
""")

    # Save results
    output = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_params": {
            "decisions_count": len(decisions),
            "vector_weights_tested": "0.0 to 0.5 (step 0.1)",
            "keyword_weights_tested": "0.5 to 1.0 (step 0.1)",
            "rerank_methods": ["none", "tfidf", "crossencoder"],
        },
        "optimal_configs": optimal_configs,
    }

    output_path = "/mnt/f/WINDSURF/neliti_code/signate/ARSAKA_MANTRA/backend/tests/query_adaptive_results.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to: {output_path}")
    print("=" * 80)

    # Return results for programmatic use
    return optimal_configs


if __name__ == "__main__":
    main()
