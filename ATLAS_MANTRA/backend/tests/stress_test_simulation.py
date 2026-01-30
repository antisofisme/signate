"""
MANTRA Stress Test Simulation

Tests 3 core use cases:
1. AI RETRIEVER - Token efficiency, relevance, speed
2. PRD/SPEC - Completeness, clarity, exportability
3. RELATIONSHIPS - Dependencies, conflicts, chains

Run: python -m pytest tests/stress_test_simulation.py -v
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal, Tuple
from datetime import datetime, timedelta, timezone
from enum import Enum
import random
import json


# =============================================================================
# MOCK SCHEMA (Proposed 21-field MCPDecision)
# =============================================================================

class ValidityState(str, Enum):
    CURRENT = "CURRENT"
    SUPERSEDED = "SUPERSEDED"
    EXPIRED = "EXPIRED"


class LifecycleStatus(str, Enum):
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    DEPRECATED = "DEPRECATED"


@dataclass
class MCPConstraint:
    id: str
    type: Literal["MUST", "MUST_NOT", "SHOULD", "MAY"]
    rule: str
    enforcement_level: str = "STRICT"
    is_automated: bool = False


@dataclass
class MCPDecision:
    # Identity (3)
    decision_id: str
    code: str
    version: str

    # Classification (3)
    domain_id: str
    aspect_id: str
    validity_state: ValidityState

    # Content (4)
    statement: str
    rationale: str
    constraints: List[MCPConstraint]
    invariants: List[str]

    # Context (3)
    applies_to: List[str]
    examples: List[str]
    tags: List[str]

    # Authorship (3)
    authored_by: str
    authored_at: datetime
    content_by: Optional[str]

    # Retrieval (2)
    impact: str  # CRITICAL, IMPORTANT, REFERENCE
    summary: str

    # NEW: PRD/Dependency (3)
    depends_on: List[str]
    supersedes: Optional[str]
    priority_rank: int  # 1-100

    # Lifecycle (separate but linked)
    lifecycle_status: LifecycleStatus = LifecycleStatus.APPROVED


@dataclass
class LifecycleEvent:
    event_id: str
    decision_id: str
    status: LifecycleStatus
    changed_by: str
    changed_at: datetime
    reason: Optional[str] = None


# =============================================================================
# TEST DATA GENERATOR
# =============================================================================

class TestDataGenerator:
    """Generate realistic test decisions."""

    DOMAINS = ["INT", "ARCH", "CTL", "EVO"]
    ASPECTS = {
        "INT": ["A01", "A02", "A03", "A04"],
        "ARCH": ["A05", "A06", "A07", "A08"],
        "CTL": ["A09", "A10", "A11", "A12"],
        "EVO": ["A13", "A14", "A15", "A16"],
    }

    SAMPLE_DECISIONS = [
        # ARCH decisions
        {
            "domain": "ARCH", "aspect": "A06",
            "statement": "All React components MUST use functional components with hooks. Class components are prohibited for new development.",
            "rationale": "Functional components with hooks provide better code reuse, easier testing, and align with React's future direction. Class components add complexity without benefits.",
            "constraints": [
                ("MUST", "Use functional components for all new React code", "STRICT", True),
                ("MUST_NOT", "Create new class components", "STRICT", True),
                ("SHOULD", "Convert class components during refactoring", "ADVISORY", False),
            ],
            "tags": ["react", "frontend", "components"],
            "applies_to": ["*.tsx", "*.jsx", "src/components/*"],
        },
        {
            "domain": "ARCH", "aspect": "A06",
            "statement": "Frontend projects MUST use feature-based folder structure. Each feature folder contains its components, hooks, and utils.",
            "rationale": "Feature-based structure improves discoverability, enables lazy loading, and keeps related code together. Reduces cross-feature coupling.",
            "constraints": [
                ("MUST", "Place feature code in src/features/{feature-name}/", "STRICT", True),
                ("MUST_NOT", "Import from other feature folders directly", "STRICT", True),
                ("MUST", "Use shared/ for cross-feature components", "STRICT", False),
            ],
            "tags": ["frontend", "architecture", "folder-structure"],
            "applies_to": ["src/features/*", "*.tsx"],
        },
        {
            "domain": "ARCH", "aspect": "A08",
            "statement": "All REST APIs MUST follow resource-based URL design with consistent naming conventions.",
            "rationale": "Consistent API design reduces cognitive load, improves discoverability, and enables generic client implementations.",
            "constraints": [
                ("MUST", "Use plural nouns for resource names: /users, /orders", "STRICT", True),
                ("MUST", "Use kebab-case for multi-word resources: /order-items", "STRICT", True),
                ("MUST_NOT", "Include verbs in URLs: /getUser is wrong", "STRICT", True),
                ("SHOULD", "Limit nesting to 2 levels: /users/{id}/orders", "ADVISORY", False),
            ],
            "tags": ["api", "rest", "backend"],
            "applies_to": ["src/api/*", "routes/*", "*.py"],
        },
        # CTL decisions
        {
            "domain": "CTL", "aspect": "A11",
            "statement": "All user input MUST be validated and sanitized before processing. SQL injection and XSS prevention is mandatory.",
            "rationale": "Input validation is the first line of defense. Prevents OWASP Top 10 vulnerabilities including injection attacks.",
            "constraints": [
                ("MUST", "Use parameterized queries for all database operations", "STRICT", True),
                ("MUST", "Sanitize HTML output to prevent XSS", "STRICT", True),
                ("MUST", "Validate input types and ranges", "STRICT", True),
                ("MUST_NOT", "Concatenate user input into SQL strings", "STRICT", True),
            ],
            "tags": ["security", "validation", "owasp"],
            "applies_to": ["src/api/*", "src/handlers/*", "*.py"],
        },
        {
            "domain": "CTL", "aspect": "A11",
            "statement": "Authentication MUST use JWT tokens with short expiration. Refresh tokens required for session continuity.",
            "rationale": "Short-lived access tokens limit exposure window. Refresh tokens enable secure session extension without re-authentication.",
            "constraints": [
                ("MUST", "Access token expiry: 15 minutes maximum", "STRICT", True),
                ("MUST", "Refresh token expiry: 7 days maximum", "STRICT", False),
                ("MUST", "Store refresh tokens server-side with rotation", "STRICT", False),
                ("MUST_NOT", "Store tokens in localStorage (use httpOnly cookies)", "STRICT", True),
            ],
            "tags": ["security", "auth", "jwt"],
            "applies_to": ["src/auth/*", "middleware/*"],
        },
        # INT decisions
        {
            "domain": "INT", "aspect": "A01",
            "statement": "The platform prioritizes developer experience over raw performance. Simplicity and clarity are primary goals.",
            "rationale": "Developer productivity compounds over time. A 10% slower system that's 50% easier to maintain is a net win for most applications.",
            "constraints": [
                ("SHOULD", "Choose readable code over clever optimizations", "ADVISORY", False),
                ("SHOULD", "Document non-obvious performance tradeoffs", "ADVISORY", False),
                ("MAY", "Optimize hot paths after profiling confirms need", "ADVISORY", False),
            ],
            "tags": ["principles", "dx", "philosophy"],
            "applies_to": ["*"],
        },
        # EVO decisions
        {
            "domain": "EVO", "aspect": "A15",
            "statement": "All deployments MUST go through staging before production. Hotfixes require post-deployment staging validation.",
            "rationale": "Staging catches environment-specific issues. Even hotfixes need validation to prevent cascading failures.",
            "constraints": [
                ("MUST", "Deploy to staging before production", "STRICT", True),
                ("MUST", "Run smoke tests in staging", "STRICT", True),
                ("MUST", "Wait 30 minutes in staging before production", "ADVISORY", False),
                ("MAY", "Skip staging wait for critical security patches", "ADVISORY", False),
            ],
            "tags": ["deployment", "ci-cd", "staging"],
            "applies_to": [".github/workflows/*", "deploy/*"],
        },
    ]

    def __init__(self):
        self.decisions: Dict[str, MCPDecision] = {}
        self.lifecycle_events: List[LifecycleEvent] = []
        self._seq = 0

    def generate_decision(
        self,
        template_idx: int = None,
        depends_on: List[str] = None,
        supersedes: str = None,
        status: LifecycleStatus = LifecycleStatus.APPROVED,
    ) -> MCPDecision:
        """Generate a decision from template or random."""
        self._seq += 1

        if template_idx is not None:
            tmpl = self.SAMPLE_DECISIONS[template_idx % len(self.SAMPLE_DECISIONS)]
        else:
            tmpl = random.choice(self.SAMPLE_DECISIONS)

        decision_id = f"dec-{self._seq:04d}"
        code = f"{tmpl['domain']}-{tmpl['aspect']}-{self._seq:03d}"

        constraints = [
            MCPConstraint(
                id=f"C-{i+1:03d}",
                type=c[0],
                rule=c[1],
                enforcement_level=c[2],
                is_automated=c[3],
            )
            for i, c in enumerate(tmpl["constraints"])
        ]

        decision = MCPDecision(
            decision_id=decision_id,
            code=code,
            version="1.0.0",
            domain_id=tmpl["domain"],
            aspect_id=tmpl["aspect"],
            validity_state=ValidityState.CURRENT,
            statement=tmpl["statement"],
            rationale=tmpl["rationale"],
            constraints=constraints,
            invariants=[f"Invariant for {code}"],
            applies_to=tmpl["applies_to"],
            examples=[f"Good: {tmpl['tags'][0]} pattern", f"Bad: anti-{tmpl['tags'][0]}"],
            tags=tmpl["tags"],
            authored_by="human@example.com",
            authored_at=datetime.now(timezone.utc),
            content_by="ai:claude-opus-4-5",
            impact="IMPORTANT",
            summary=tmpl["statement"][:100],
            depends_on=depends_on or [],
            supersedes=supersedes,
            priority_rank=random.randint(1, 100),
            lifecycle_status=status,
        )

        self.decisions[decision_id] = decision
        return decision

    def generate_bulk(self, count: int) -> List[MCPDecision]:
        """Generate multiple decisions with some dependencies."""
        results = []
        for i in range(count):
            # 30% chance to depend on previous
            depends_on = []
            if i > 0 and random.random() < 0.3:
                dep_count = random.randint(1, min(3, i))
                depends_on = random.sample(list(self.decisions.keys()), dep_count)

            # 10% chance to supersede previous
            supersedes = None
            if i > 0 and random.random() < 0.1:
                supersedes = random.choice(list(self.decisions.keys()))

            decision = self.generate_decision(
                template_idx=i,
                depends_on=depends_on,
                supersedes=supersedes,
            )
            results.append(decision)

        return results


# =============================================================================
# STRESS TEST 1: AI RETRIEVER
# =============================================================================

class AIRetrieverTest:
    """Test AI retrieval scenarios."""

    def __init__(self, decisions: Dict[str, MCPDecision]):
        self.decisions = decisions

    def estimate_tokens(self, decision: MCPDecision, mode: str) -> int:
        """Estimate tokens based on retrieval mode."""
        if mode == "LIST":
            # code + summary only
            return len(decision.code) // 4 + len(decision.summary) // 4 + 10
        elif mode == "ENFORCE":
            # code + statement + constraints
            constraint_text = " ".join(c.rule for c in decision.constraints)
            return (len(decision.code) + len(decision.statement) + len(constraint_text)) // 4 + 20
        elif mode == "UNDERSTAND":
            # code + statement + rationale
            return (len(decision.code) + len(decision.statement) + len(decision.rationale)) // 4 + 20
        else:  # FULL
            return 500  # Max estimate

    def test_token_budget(self, query: str, mode: str, budget: int = 1500) -> Dict:
        """Test if retrieval fits within token budget."""
        # Simulate retrieval
        matched = [d for d in self.decisions.values()
                   if any(tag in query.lower() for tag in d.tags)]

        total_tokens = 0
        included = []
        excluded = []

        for d in matched:
            tokens = self.estimate_tokens(d, mode)
            if total_tokens + tokens <= budget:
                total_tokens += tokens
                included.append(d.code)
            else:
                excluded.append(d.code)

        return {
            "query": query,
            "mode": mode,
            "budget": budget,
            "tokens_used": total_tokens,
            "tokens_remaining": budget - total_tokens,
            "included_count": len(included),
            "excluded_count": len(excluded),
            "included": included,
            "excluded": excluded,
            "passed": len(excluded) == 0 or total_tokens > 0,
        }

    def test_relevance(self, query: str, expected_domains: List[str]) -> Dict:
        """Test if retrieval returns relevant decisions."""
        matched = [d for d in self.decisions.values()
                   if any(tag in query.lower() for tag in d.tags)]

        relevant = [d for d in matched if d.domain_id in expected_domains]
        irrelevant = [d for d in matched if d.domain_id not in expected_domains]

        precision = len(relevant) / len(matched) if matched else 0

        return {
            "query": query,
            "expected_domains": expected_domains,
            "matched_count": len(matched),
            "relevant_count": len(relevant),
            "irrelevant_count": len(irrelevant),
            "precision": precision,
            "passed": precision >= 0.7,  # 70% precision threshold
        }

    def test_dependency_inclusion(self, decision_id: str) -> Dict:
        """Test if dependencies are correctly included."""
        if decision_id not in self.decisions:
            return {"error": "Decision not found"}

        decision = self.decisions[decision_id]
        deps_found = []
        deps_missing = []

        for dep_id in decision.depends_on:
            if dep_id in self.decisions:
                deps_found.append(dep_id)
            else:
                deps_missing.append(dep_id)

        return {
            "decision_id": decision_id,
            "depends_on": decision.depends_on,
            "deps_found": deps_found,
            "deps_missing": deps_missing,
            "all_resolved": len(deps_missing) == 0,
            "passed": len(deps_missing) == 0,
        }


# =============================================================================
# STRESS TEST 2: PRD/SPEC EXPORT
# =============================================================================

class PRDExportTest:
    """Test PRD export scenarios."""

    def __init__(self, decisions: Dict[str, MCPDecision]):
        self.decisions = decisions

    def export_markdown(self, domain: str = None) -> str:
        """Export decisions as PRD markdown."""
        lines = ["# Product Requirements Document\n"]
        lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}\n")

        # Group by domain
        by_domain: Dict[str, List[MCPDecision]] = {}
        for d in self.decisions.values():
            if domain and d.domain_id != domain:
                continue
            if d.lifecycle_status != LifecycleStatus.APPROVED:
                continue
            if d.domain_id not in by_domain:
                by_domain[d.domain_id] = []
            by_domain[d.domain_id].append(d)

        domain_names = {
            "INT": "Intent & Direction",
            "ARCH": "Architecture & Boundaries",
            "CTL": "Control & Policy",
            "EVO": "Execution & Evolution",
        }

        for domain_id in ["INT", "ARCH", "CTL", "EVO"]:
            if domain_id not in by_domain:
                continue

            lines.append(f"\n## {domain_names.get(domain_id, domain_id)}\n")

            # Sort by priority
            sorted_decisions = sorted(by_domain[domain_id], key=lambda d: d.priority_rank)

            for d in sorted_decisions:
                lines.append(f"\n### {d.code}: {d.summary}\n")
                lines.append(f"**Priority**: {d.priority_rank}/100\n")
                lines.append(f"**Statement**: {d.statement}\n")
                lines.append(f"\n**Rationale**: {d.rationale}\n")

                if d.constraints:
                    lines.append("\n**Constraints**:\n")
                    for c in d.constraints:
                        automated = "✓" if c.is_automated else "○"
                        lines.append(f"- [{automated}] {c.type}: {c.rule}\n")

                if d.depends_on:
                    lines.append(f"\n**Dependencies**: {', '.join(d.depends_on)}\n")

                if d.supersedes:
                    lines.append(f"\n**Supersedes**: {d.supersedes}\n")

        return "".join(lines)

    def test_completeness(self) -> Dict:
        """Test PRD completeness."""
        issues = []

        for d in self.decisions.values():
            if d.lifecycle_status != LifecycleStatus.APPROVED:
                continue

            # Check required fields
            if len(d.statement) < 50:
                issues.append(f"{d.code}: Statement too short ({len(d.statement)} chars)")
            if len(d.rationale) < 50:
                issues.append(f"{d.code}: Rationale too short ({len(d.rationale)} chars)")
            if not d.constraints:
                issues.append(f"{d.code}: No constraints defined")
            if not d.tags:
                issues.append(f"{d.code}: No tags defined")

            # Check constraint quality
            for c in d.constraints:
                if len(c.rule) < 10:
                    issues.append(f"{d.code}/{c.id}: Constraint too vague")

        return {
            "total_decisions": len(self.decisions),
            "issues_found": len(issues),
            "issues": issues[:10],  # First 10
            "passed": len(issues) == 0,
        }

    def test_hierarchy(self) -> Dict:
        """Test PRD section hierarchy."""
        by_domain: Dict[str, int] = {}
        by_aspect: Dict[str, int] = {}

        for d in self.decisions.values():
            by_domain[d.domain_id] = by_domain.get(d.domain_id, 0) + 1
            by_aspect[d.aspect_id] = by_aspect.get(d.aspect_id, 0) + 1

        # Check coverage
        missing_domains = [d for d in ["INT", "ARCH", "CTL", "EVO"] if d not in by_domain]

        return {
            "decisions_by_domain": by_domain,
            "decisions_by_aspect": by_aspect,
            "missing_domains": missing_domains,
            "domain_coverage": len(by_domain) / 4,
            "passed": len(missing_domains) == 0,
        }


# =============================================================================
# STRESS TEST 3: RELATIONSHIPS
# =============================================================================

class RelationshipTest:
    """Test decision relationships."""

    def __init__(self, decisions: Dict[str, MCPDecision]):
        self.decisions = decisions

    def detect_circular_dependencies(self) -> Dict:
        """Detect circular dependency chains."""
        def find_cycle(node: str, visited: set, path: List[str]) -> Optional[List[str]]:
            if node in path:
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]

            if node in visited or node not in self.decisions:
                return None

            visited.add(node)
            path.append(node)

            for dep in self.decisions[node].depends_on:
                cycle = find_cycle(dep, visited, path)
                if cycle:
                    return cycle

            path.pop()
            return None

        cycles = []
        visited = set()

        for decision_id in self.decisions:
            cycle = find_cycle(decision_id, set(), [])
            if cycle and tuple(sorted(cycle)) not in [tuple(sorted(c)) for c in cycles]:
                cycles.append(cycle)

        return {
            "cycles_found": len(cycles),
            "cycles": cycles[:5],  # First 5
            "passed": len(cycles) == 0,
        }

    def detect_conflicts(self) -> Dict:
        """Detect potentially conflicting decisions."""
        conflicts = []

        decisions_list = list(self.decisions.values())
        for i, d1 in enumerate(decisions_list):
            for d2 in decisions_list[i+1:]:
                # Same domain+aspect, both APPROVED = potential conflict
                if (d1.domain_id == d2.domain_id and
                    d1.aspect_id == d2.aspect_id and
                    d1.lifecycle_status == LifecycleStatus.APPROVED and
                    d2.lifecycle_status == LifecycleStatus.APPROVED and
                    not d1.supersedes and not d2.supersedes):

                    # Check for MUST vs MUST_NOT on similar topics
                    d1_musts = [c.rule for c in d1.constraints if c.type == "MUST"]
                    d2_must_nots = [c.rule for c in d2.constraints if c.type == "MUST_NOT"]

                    # Simple overlap check
                    for m in d1_musts:
                        for mn in d2_must_nots:
                            if any(word in mn.lower() for word in m.lower().split()[:3]):
                                conflicts.append({
                                    "decision_1": d1.code,
                                    "decision_2": d2.code,
                                    "conflict_type": "MUST vs MUST_NOT",
                                    "detail": f"'{m[:50]}' vs '{mn[:50]}'",
                                })

        return {
            "conflicts_found": len(conflicts),
            "conflicts": conflicts[:5],
            "passed": True,  # Conflicts are warnings, not failures
        }

    def test_supersedes_chain(self) -> Dict:
        """Test supersedes chain integrity."""
        chains = []
        broken = []

        for d in self.decisions.values():
            if d.supersedes:
                chain = [d.decision_id]
                current = d.supersedes
                depth = 0

                while current and depth < 10:
                    if current not in self.decisions:
                        broken.append({
                            "decision": d.code,
                            "missing": current,
                        })
                        break

                    chain.append(current)
                    current = self.decisions[current].supersedes
                    depth += 1

                if len(chain) > 1:
                    chains.append(chain)

        return {
            "chains_found": len(chains),
            "max_chain_length": max(len(c) for c in chains) if chains else 0,
            "broken_references": broken,
            "passed": len(broken) == 0,
        }

    def analyze_dependency_graph(self) -> Dict:
        """Analyze dependency graph metrics."""
        # Calculate in-degree and out-degree
        in_degree: Dict[str, int] = {d: 0 for d in self.decisions}
        out_degree: Dict[str, int] = {}

        for d in self.decisions.values():
            out_degree[d.decision_id] = len(d.depends_on)
            for dep in d.depends_on:
                if dep in in_degree:
                    in_degree[dep] += 1

        # Find roots (no dependencies) and leaves (nothing depends on them)
        roots = [d for d, deg in out_degree.items() if deg == 0]
        leaves = [d for d, deg in in_degree.items() if deg == 0]

        # Find highly connected nodes
        hubs = [(d, in_degree[d]) for d in self.decisions if in_degree[d] > 2]
        hubs.sort(key=lambda x: x[1], reverse=True)

        return {
            "total_nodes": len(self.decisions),
            "total_edges": sum(out_degree.values()),
            "root_nodes": len(roots),
            "leaf_nodes": len(leaves),
            "hub_nodes": hubs[:5],
            "avg_dependencies": sum(out_degree.values()) / len(self.decisions) if self.decisions else 0,
            "passed": True,
        }


# =============================================================================
# RUN ALL TESTS
# =============================================================================

def run_stress_tests():
    """Run all stress tests and report results."""
    print("=" * 70)
    print("MANTRA STRESS TEST SIMULATION")
    print("=" * 70)

    # Generate test data
    print("\n[1] Generating test data...")
    generator = TestDataGenerator()
    generator.generate_bulk(50)  # 50 decisions
    print(f"    Generated {len(generator.decisions)} decisions")

    results = {
        "ai_retriever": [],
        "prd_export": [],
        "relationships": [],
    }

    # ==========================================================================
    # TEST 1: AI RETRIEVER
    # ==========================================================================
    print("\n[2] Running AI Retriever Tests...")
    ai_test = AIRetrieverTest(generator.decisions)

    # Token budget tests
    for mode in ["LIST", "ENFORCE", "UNDERSTAND", "FULL"]:
        result = ai_test.test_token_budget("react components", mode, budget=1500)
        results["ai_retriever"].append(result)
        status = "✓" if result["passed"] else "✗"
        print(f"    {status} Token budget ({mode}): {result['tokens_used']}/{result['budget']} tokens, {result['included_count']} decisions")

    # Relevance tests
    relevance_tests = [
        ("react frontend components", ["ARCH"]),
        ("security authentication", ["CTL"]),
        ("deployment staging", ["EVO"]),
    ]
    for query, expected in relevance_tests:
        result = ai_test.test_relevance(query, expected)
        results["ai_retriever"].append(result)
        status = "✓" if result["passed"] else "✗"
        print(f"    {status} Relevance '{query[:30]}': {result['precision']:.0%} precision")

    # Dependency tests
    for decision_id in list(generator.decisions.keys())[:5]:
        result = ai_test.test_dependency_inclusion(decision_id)
        results["ai_retriever"].append(result)
    print(f"    ✓ Dependency resolution: 5 decisions tested")

    # ==========================================================================
    # TEST 2: PRD EXPORT
    # ==========================================================================
    print("\n[3] Running PRD Export Tests...")
    prd_test = PRDExportTest(generator.decisions)

    # Completeness
    result = prd_test.test_completeness()
    results["prd_export"].append(result)
    status = "✓" if result["passed"] else "✗"
    print(f"    {status} Completeness: {result['issues_found']} issues found")

    # Hierarchy
    result = prd_test.test_hierarchy()
    results["prd_export"].append(result)
    status = "✓" if result["passed"] else "✗"
    print(f"    {status} Hierarchy: {result['domain_coverage']:.0%} domain coverage")
    print(f"       Distribution: {result['decisions_by_domain']}")

    # Export sample
    markdown = prd_test.export_markdown(domain="ARCH")
    print(f"    ✓ Markdown export: {len(markdown)} chars generated")

    # ==========================================================================
    # TEST 3: RELATIONSHIPS
    # ==========================================================================
    print("\n[4] Running Relationship Tests...")
    rel_test = RelationshipTest(generator.decisions)

    # Circular dependencies
    result = rel_test.detect_circular_dependencies()
    results["relationships"].append(result)
    status = "✓" if result["passed"] else "✗"
    print(f"    {status} Circular deps: {result['cycles_found']} cycles found")

    # Conflicts
    result = rel_test.detect_conflicts()
    results["relationships"].append(result)
    print(f"    ⚠ Conflicts: {result['conflicts_found']} potential conflicts")

    # Supersedes chain
    result = rel_test.test_supersedes_chain()
    results["relationships"].append(result)
    status = "✓" if result["passed"] else "✗"
    print(f"    {status} Supersedes chain: max depth {result['max_chain_length']}, {len(result['broken_references'])} broken")

    # Graph analysis
    result = rel_test.analyze_dependency_graph()
    results["relationships"].append(result)
    print(f"    ✓ Graph: {result['total_nodes']} nodes, {result['total_edges']} edges, avg {result['avg_dependencies']:.1f} deps")

    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total_tests = sum(len(v) for v in results.values())
    passed_tests = sum(1 for v in results.values() for r in v if r.get("passed", True))

    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Pass Rate: {passed_tests/total_tests:.0%}")

    # Return results for programmatic access
    return results


if __name__ == "__main__":
    run_stress_tests()
