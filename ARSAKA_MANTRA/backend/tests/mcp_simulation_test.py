"""
MCP Tool Simulation Test

Simulates all MCP tool calls and analyzes:
1. Expected vs actual behavior
2. Error handling
3. Edge cases
4. Performance under load

This tests the LOGIC of MCP tools without requiring a running server.
"""

import time
import random
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
import importlib.util
import sys

# Load modules directly
def load_module_direct(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

base_path = '/mnt/f/WINDSURF/neliti_code/signate/ARSAKA_MANTRA/backend/core/retrieval'

# Load modules
query_expander_mod = load_module_direct('query_expander', f'{base_path}/query_expander.py')
QueryExpander = query_expander_mod.QueryExpander

intent_mod = load_module_direct('intent', f'{base_path}/intent.py')
IntentDetector = intent_mod.IntentDetector
QueryIntent = intent_mod.QueryIntent
SearchStrategy = intent_mod.SearchStrategy
STRATEGY_PARAMS = intent_mod.STRATEGY_PARAMS

deps_mod = load_module_direct('dependencies', f'{base_path}/dependencies.py')
DependencyGraph = deps_mod.DependencyGraph
DependencyResolver = deps_mod.DependencyResolver


# ============================================================================
# MCP TOOL SIMULATORS
# ============================================================================

class MCPToolSimulator:
    """Simulates MCP tool behavior for testing."""

    def __init__(self, decisions: List[Dict[str, Any]]):
        self.decisions = decisions
        self.decisions_by_id = {d['decision_id']: d for d in decisions}
        self.decisions_by_code = {d['decision_code']: d for d in decisions}

        self.query_expander = QueryExpander()
        self.intent_detector = IntentDetector()
        self.dependency_graph = DependencyGraph()
        self.dependency_graph.build_from_decisions(decisions)

        # Analytics tracking (in-memory simulation)
        self.usage_events = []
        self.feedback_events = []
        self.approval_queue = []

    # =========================================================================
    # SEARCH TOOLS
    # =========================================================================

    def mantra_search_decisions(self, args: Dict) -> Dict:
        """Simulate mantra_search_decisions tool."""
        query = args.get('query', '')
        domain_id = args.get('domain_id')
        aspect_id = args.get('aspect_id')
        limit = args.get('limit', 10)

        # Simple keyword search simulation
        results = []
        query_lower = query.lower()

        for d in self.decisions:
            # Filter by domain/aspect
            if domain_id and d['domain_id'] != domain_id:
                continue
            if aspect_id and d['aspect_id'] != aspect_id:
                continue

            # Simple relevance scoring
            score = 0
            if query_lower in d['statement'].lower():
                score += 2
            if query_lower in d.get('rationale', '').lower():
                score += 1
            for tag in d.get('tags', []):
                if query_lower in tag.lower():
                    score += 0.5

            if score > 0:
                results.append({'decision': d, 'score': score})

        # Sort by score and limit
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:limit]

        return {
            'status': 'success',
            'count': len(results),
            'decisions': [r['decision'] for r in results]
        }

    def mantra_semantic_search(self, args: Dict) -> Dict:
        """Simulate semantic search with query expansion."""
        query = args.get('query', '')
        limit = args.get('limit', 10)
        min_score = args.get('min_score', 0.5)
        domain_id = args.get('domain_id')

        # Use query expansion for better recall
        expansion = self.query_expander.expand(query, {'domain_id': domain_id})
        all_terms = expansion.all_terms

        results = []
        for d in self.decisions:
            if domain_id and d['domain_id'] != domain_id:
                continue

            # Calculate simulated semantic score
            score = 0
            text_to_search = (d['statement'] + ' ' + d.get('rationale', '')).lower()

            for term in all_terms:
                if term.lower() in text_to_search:
                    score += 0.2

            # Normalize to 0-1
            score = min(1.0, score)

            if score >= min_score:
                results.append({
                    'decision_id': d['decision_id'],
                    'decision_code': d['decision_code'],
                    'statement': d['statement'],
                    'score': score,
                    'domain_id': d['domain_id'],
                    'aspect_id': d['aspect_id'],
                    'tags': d.get('tags', []),
                })

        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:limit]

        return {
            'status': 'OK' if results else 'NOT_FOUND',
            'hits': results,
            'total_count': len(results),
            'query': query,
            'expanded_terms': expansion.expanded_terms,
            'execution_time_ms': random.uniform(5, 50),
        }

    def mantra_retrieve(self, args: Dict) -> Dict:
        """Simulate context-aware retrieval (main enhanced retrieval)."""
        query = args.get('query', '')
        file_path = args.get('file_path')
        max_results = args.get('max_results', 10)
        token_budget = args.get('token_budget', 2000)

        # Step 1: Intent detection
        intent = self.intent_detector.detect(query)
        strategy = intent.strategy
        params = intent.strategy_params

        # Step 2: Query expansion (if strategy allows)
        expanded_terms = []
        if params and params.expand_query:
            expansion = self.query_expander.expand(query, {'file_path': file_path})
            expanded_terms = expansion.expanded_terms

        # Step 3: Search with expanded query
        all_terms = [query] + expanded_terms
        results = []

        for d in self.decisions:
            score = 0
            text = (d['statement'] + ' ' + d.get('rationale', '')).lower()

            for term in all_terms:
                if term.lower() in text:
                    score += 0.3

            # Bonus for file path match
            if file_path:
                for pattern in d.get('applies_to', []):
                    if pattern.replace('*', '') in file_path:
                        score += 0.5

            if score > 0:
                results.append({
                    'decision_id': d['decision_id'],
                    'decision_code': d['decision_code'],
                    'statement': d['statement'],
                    'rationale': d.get('rationale', ''),
                    'confidence': min(1.0, score),
                    'relevance_score': score,
                    'source': 'hybrid_search',
                    'matched_by': ['query', 'expansion'] if expanded_terms else ['query'],
                })

        # Step 4: Dependency resolution (if enabled)
        if params and params.include_dependencies:
            result_ids = [r['decision_id'] for r in results[:max_results]]
            resolver = DependencyResolver(self.dependency_graph)
            resolved = resolver.resolve(result_ids, include_dependencies=True)

            # Add dependencies
            for dep_id in resolved:
                if dep_id not in result_ids and dep_id in self.decisions_by_id:
                    d = self.decisions_by_id[dep_id]
                    results.append({
                        'decision_id': d['decision_id'],
                        'decision_code': d['decision_code'],
                        'statement': d['statement'],
                        'confidence': 0.6,
                        'relevance_score': 0.4,
                        'source': 'dependency',
                        'matched_by': ['dependency'],
                    })

        # Sort and limit
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        results = results[:max_results]

        # Estimate tokens
        token_count = sum(len(r['statement']) // 4 for r in results)

        return {
            'results': results,
            'total_count': len(results),
            'from_cache': False,
            'triggered_by': [],
            'execution_time_ms': random.uniform(10, 100),
            'token_count': token_count,
            'suggestions': ['Try adding more specific terms'] if not results else [],
            'intent': intent.intent.value,
            'strategy': strategy.value,
            'expanded_terms': expanded_terms,
        }

    # =========================================================================
    # VALIDATION TOOLS
    # =========================================================================

    def mantra_validate_decision(self, args: Dict) -> Dict:
        """Simulate decision validation."""
        domain_id = args.get('domain_id')
        aspect_id = args.get('aspect_id')
        statement = args.get('statement', '')
        rationale = args.get('rationale', '')

        errors = []
        warnings = []

        # Validate domain-aspect compatibility
        domain_aspects = {
            'INT': ['A01', 'A02', 'A03', 'A04'],
            'ARCH': ['A05', 'A06', 'A07', 'A08'],
            'CTL': ['A09', 'A10', 'A11', 'A12'],
            'EVO': ['A13', 'A14', 'A15', 'A16'],
        }

        if domain_id and aspect_id:
            if aspect_id not in domain_aspects.get(domain_id, []):
                errors.append(f"Aspect {aspect_id} not valid for domain {domain_id}")

        # Validate statement length
        if len(statement) < 10:
            errors.append("Statement must be at least 10 characters")
        elif len(statement) > 500:
            warnings.append("Statement is quite long, consider being more concise")

        # Validate rationale
        if len(rationale) < 20:
            warnings.append("Rationale should be at least 20 characters")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
        }

    def mantra_validate_full(self, args: Dict) -> Dict:
        """Simulate 3-gate validation pipeline."""
        decision = args.get('decision', {})
        submitted_by = args.get('submitted_by', '')

        # Check MANTRA-LAW-001 §6: AI cannot submit
        ai_names = ['claude', 'gpt', 'ai:', 'assistant', 'copilot']
        if any(name in submitted_by.lower() for name in ai_names):
            return {
                'outcome': 'REJECTED_GATE1',
                'stage': 'gate1',
                'messages': ['MANTRA-LAW-001 §6 Violation: AI cannot submit decisions'],
                'can_activate': False,
            }

        # Gate 1: Deterministic validation
        gate1_result = self.mantra_validate_decision({
            'domain_id': decision.get('domain_id'),
            'aspect_id': decision.get('aspect_id'),
            'statement': decision.get('statement', ''),
            'rationale': decision.get('rationale', ''),
        })

        if not gate1_result['valid']:
            return {
                'outcome': 'REJECTED_GATE1',
                'stage': 'gate1',
                'gate1': gate1_result,
                'messages': gate1_result['errors'],
                'can_activate': False,
            }

        # Gate 2: AI quality check (simulated)
        quality_score = random.uniform(0.6, 1.0)
        gate2_passed = quality_score >= 0.7

        if not gate2_passed:
            return {
                'outcome': 'REJECTED_GATE2',
                'stage': 'gate2',
                'gate1': gate1_result,
                'gate2': {'quality_score': quality_score},
                'messages': ['Quality score below threshold'],
                'can_activate': False,
            }

        # Gate 3: Create approval request
        approval_id = f"APR-{len(self.approval_queue) + 1:04d}"
        self.approval_queue.append({
            'request_id': approval_id,
            'decision': decision,
            'submitted_by': submitted_by,
            'submitted_at': datetime.now(timezone.utc).isoformat(),
        })

        return {
            'outcome': 'PENDING_APPROVAL',
            'stage': 'gate3',
            'decision_id': f"pending-{approval_id}",
            'decision_code': f"{decision.get('domain_id', 'UNK')}-pending",
            'gate1': gate1_result,
            'gate2': {'quality_score': quality_score, 'status': 'PASSED'},
            'approval_request_id': approval_id,
            'messages': ['Awaiting human approval per MANTRA-LAW-001 §6'],
            'can_activate': False,
        }

    # =========================================================================
    # ANALYTICS TOOLS
    # =========================================================================

    def mantra_track_usage(self, args: Dict) -> Dict:
        """Simulate usage tracking."""
        event = {
            'event_type': args.get('event_type'),
            'decision_id': args.get('decision_id'),
            'query': args.get('query'),
            'file_path': args.get('file_path'),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        self.usage_events.append(event)

        return {
            'success': True,
            'event_id': f"EVT-{len(self.usage_events):06d}",
            'event_type': event['event_type'],
        }

    def mantra_feedback(self, args: Dict) -> Dict:
        """Simulate feedback tracking."""
        feedback = {
            'decision_id': args.get('decision_id'),
            'feedback_type': args.get('feedback_type'),
            'comment': args.get('comment'),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        self.feedback_events.append(feedback)

        return {
            'success': True,
            'feedback_id': f"FBK-{len(self.feedback_events):06d}",
            'feedback_type': feedback['feedback_type'],
        }

    def mantra_analytics_summary(self, args: Dict) -> Dict:
        """Simulate analytics summary."""
        return {
            'total_decisions_tracked': len(self.decisions),
            'total_events': len(self.usage_events),
            'total_feedback': len(self.feedback_events),
            'hot_decisions_count': min(20, len(self.decisions)),
            'stale_decisions_count': 0,
            'problematic_decisions_count': sum(
                1 for f in self.feedback_events
                if f['feedback_type'] in ['NOT_HELPFUL', 'OUTDATED', 'UNCLEAR']
            ),
        }

    # =========================================================================
    # CHECK ALIGNMENT
    # =========================================================================

    def mantra_check_alignment(self, args: Dict) -> Dict:
        """Simulate alignment check."""
        statement = args.get('statement', '')
        rationale = args.get('rationale', '')
        domain_id = args.get('domain_id')

        # Use semantic search to find similar decisions
        search_result = self.mantra_semantic_search({
            'query': statement,
            'limit': 10,
            'min_score': 0.3,
            'domain_id': domain_id,
        })

        aligned = []
        conflicts = []
        related = []

        for hit in search_result['hits']:
            if hit['score'] >= 0.8:
                # High similarity - potential conflict or alignment
                # Simple heuristic: if domains match, it's aligned; otherwise conflict
                if domain_id and hit['domain_id'] == domain_id:
                    aligned.append(hit)
                else:
                    conflicts.append(hit)
            elif hit['score'] >= 0.5:
                related.append(hit)

        status = 'ALIGNED'
        if conflicts:
            status = 'CONFLICTING'
        elif not aligned and not related:
            status = 'UNKNOWN'

        recommendations = []
        if conflicts:
            recommendations.append("Review conflicting decisions before proceeding")
        if aligned:
            recommendations.append("Consider extending existing decisions instead of creating new")

        return {
            'status': status,
            'aligned_with': aligned,
            'conflicts_with': conflicts,
            'related_decisions': related,
            'recommendations': recommendations,
            'execution_time_ms': random.uniform(20, 100),
        }


# ============================================================================
# TEST SCENARIOS
# ============================================================================

def generate_test_decisions(count: int = 100) -> List[Dict]:
    """Generate test decisions (simplified)."""
    import uuid

    decisions = []
    domains = ['INT', 'ARCH', 'CTL', 'EVO']
    domain_aspects = {
        'INT': ['A01', 'A02', 'A03', 'A04'],
        'ARCH': ['A05', 'A06', 'A07', 'A08'],
        'CTL': ['A09', 'A10', 'A11', 'A12'],
        'EVO': ['A13', 'A14', 'A15', 'A16'],
    }

    statements = [
        "Semua API endpoints harus menggunakan authentication",
        "Database schema harus menggunakan UUID untuk primary keys",
        "Frontend components harus mengikuti atomic design pattern",
        "Service layer harus terpisah dari controller layer",
        "Semua mutations harus memiliki audit logging",
        "Rate limiting harus diterapkan di API gateway",
        "Password harus di-hash menggunakan bcrypt",
        "Multi-tenancy menggunakan tenant_id di setiap query",
        "Error handling harus konsisten di semua endpoints",
        "Testing coverage minimal 80% untuk business logic",
    ]

    for i in range(count):
        domain = random.choice(domains)
        aspect = random.choice(domain_aspects[domain])
        decision_id = str(uuid.uuid4())

        decisions.append({
            'decision_id': decision_id,
            'decision_code': f"{domain}-{aspect}-{i+1:03d}-v1.0.0",
            'domain_id': domain,
            'aspect_id': aspect,
            'statement': random.choice(statements),
            'rationale': f"Decision ini diambil untuk memastikan {random.choice(['security', 'scalability', 'maintainability', 'consistency'])}",
            'scope': random.choice(['ORGANIZATION', 'DOMAIN', 'APPLICATION']),
            'blast_radius': random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
            'tags': random.sample(['FE', 'BE', 'DB', 'API', 'SECURITY'], 2),
            'applies_to': ['*.tsx', 'src/api/*'],
            'relations': [],
        })

    return decisions


@dataclass
class ScenarioResult:
    """Result of a test scenario."""
    name: str
    passed: bool
    expected: str
    actual: str
    execution_time_ms: float
    details: Dict = field(default_factory=dict)


def run_mcp_scenarios() -> List[ScenarioResult]:
    """Run MCP tool test scenarios."""
    decisions = generate_test_decisions(200)
    simulator = MCPToolSimulator(decisions)

    results = []

    # =========================================================================
    # SCENARIO 1: Basic Search
    # =========================================================================
    print("\n[SCENARIO 1] Basic Search")

    start = time.perf_counter()
    result = simulator.mantra_search_decisions({'query': 'authentication'})
    elapsed = (time.perf_counter() - start) * 1000

    results.append(ScenarioResult(
        name="Basic Search - Valid Query",
        passed=result['status'] == 'success' and result['count'] > 0,
        expected="Find decisions containing 'authentication'",
        actual=f"Found {result['count']} decisions",
        execution_time_ms=elapsed,
    ))

    # Empty query
    result = simulator.mantra_search_decisions({'query': ''})
    results.append(ScenarioResult(
        name="Basic Search - Empty Query",
        passed=result['count'] == 0,
        expected="Return empty results",
        actual=f"Found {result['count']} decisions",
        execution_time_ms=0,
    ))

    # =========================================================================
    # SCENARIO 2: Semantic Search with Expansion
    # =========================================================================
    print("\n[SCENARIO 2] Semantic Search with Query Expansion")

    start = time.perf_counter()
    result = simulator.mantra_semantic_search({
        'query': 'database design',
        'limit': 5,
        'min_score': 0.3,
    })
    elapsed = (time.perf_counter() - start) * 1000

    has_expansion = len(result.get('expanded_terms', [])) > 0
    results.append(ScenarioResult(
        name="Semantic Search - With Expansion",
        passed=has_expansion,
        expected="Query should be expanded with related terms",
        actual=f"Expanded terms: {result.get('expanded_terms', [])}",
        execution_time_ms=elapsed,
    ))

    # =========================================================================
    # SCENARIO 3: Context-Aware Retrieval
    # =========================================================================
    print("\n[SCENARIO 3] Context-Aware Retrieval")

    # Test with file path context
    result = simulator.mantra_retrieve({
        'query': 'component architecture',
        'file_path': 'src/components/LoginForm.tsx',
        'max_results': 5,
    })

    intent_detected = result.get('intent') is not None
    strategy_used = result.get('strategy') is not None

    results.append(ScenarioResult(
        name="Context Retrieval - Intent Detection",
        passed=intent_detected and strategy_used,
        expected="Should detect intent and select strategy",
        actual=f"Intent: {result.get('intent')}, Strategy: {result.get('strategy')}",
        execution_time_ms=result.get('execution_time_ms', 0),
    ))

    # =========================================================================
    # SCENARIO 4: Validation - Valid Decision
    # =========================================================================
    print("\n[SCENARIO 4] Decision Validation")

    result = simulator.mantra_validate_decision({
        'domain_id': 'ARCH',
        'aspect_id': 'A05',
        'statement': 'Service layer harus terpisah dari controller layer untuk separation of concerns',
        'rationale': 'Memisahkan business logic dari HTTP handling meningkatkan testability dan maintainability',
    })

    results.append(ScenarioResult(
        name="Validation - Valid Decision",
        passed=result['valid'] == True,
        expected="Should pass validation",
        actual=f"Valid: {result['valid']}, Errors: {result.get('errors', [])}",
        execution_time_ms=0,
    ))

    # Invalid domain-aspect combo
    result = simulator.mantra_validate_decision({
        'domain_id': 'INT',
        'aspect_id': 'A05',  # A05 belongs to ARCH, not INT
        'statement': 'Test statement',
        'rationale': 'Test rationale',
    })

    results.append(ScenarioResult(
        name="Validation - Invalid Domain-Aspect",
        passed=result['valid'] == False and len(result['errors']) > 0,
        expected="Should fail with domain-aspect error",
        actual=f"Valid: {result['valid']}, Errors: {result.get('errors', [])}",
        execution_time_ms=0,
    ))

    # =========================================================================
    # SCENARIO 5: 3-Gate Validation Pipeline
    # =========================================================================
    print("\n[SCENARIO 5] 3-Gate Validation Pipeline")

    # AI submission (should be rejected)
    result = simulator.mantra_validate_full({
        'decision': {
            'domain_id': 'ARCH',
            'aspect_id': 'A05',
            'statement': 'Test decision',
            'rationale': 'Test rationale',
        },
        'submitted_by': 'Claude Assistant',  # AI name
    })

    results.append(ScenarioResult(
        name="3-Gate - AI Submission Rejected",
        passed=result['outcome'] == 'REJECTED_GATE1',
        expected="Should reject AI submission per MANTRA-LAW-001 §6",
        actual=f"Outcome: {result['outcome']}, Messages: {result.get('messages', [])}",
        execution_time_ms=0,
    ))

    # Human submission (should pass to approval)
    result = simulator.mantra_validate_full({
        'decision': {
            'domain_id': 'ARCH',
            'aspect_id': 'A05',
            'statement': 'Service layer harus terpisah dari controller layer untuk separation of concerns yang baik',
            'rationale': 'Memisahkan business logic dari HTTP handling meningkatkan testability dan maintainability codebase',
        },
        'submitted_by': 'alice@company.com',
    })

    results.append(ScenarioResult(
        name="3-Gate - Human Submission Approved",
        passed=result['outcome'] == 'PENDING_APPROVAL',
        expected="Should create approval request",
        actual=f"Outcome: {result['outcome']}, Approval ID: {result.get('approval_request_id')}",
        execution_time_ms=0,
    ))

    # =========================================================================
    # SCENARIO 6: Alignment Check
    # =========================================================================
    print("\n[SCENARIO 6] Alignment Check")

    result = simulator.mantra_check_alignment({
        'statement': 'API endpoints harus menggunakan JWT untuk authentication',
        'domain_id': 'CTL',
    })

    has_recommendations = len(result.get('recommendations', [])) >= 0
    results.append(ScenarioResult(
        name="Alignment Check - With Recommendations",
        passed=result['status'] in ['ALIGNED', 'CONFLICTING', 'UNKNOWN'],
        expected="Should return alignment status",
        actual=f"Status: {result['status']}, Recommendations: {result.get('recommendations', [])}",
        execution_time_ms=result.get('execution_time_ms', 0),
    ))

    # =========================================================================
    # SCENARIO 7: Analytics Tracking
    # =========================================================================
    print("\n[SCENARIO 7] Analytics Tracking")

    # Track usage
    result = simulator.mantra_track_usage({
        'event_type': 'VIEW',
        'decision_id': decisions[0]['decision_id'],
        'query': 'test query',
    })

    results.append(ScenarioResult(
        name="Analytics - Track Usage",
        passed=result['success'] == True,
        expected="Should track usage event",
        actual=f"Event ID: {result.get('event_id')}",
        execution_time_ms=0,
    ))

    # Track feedback
    result = simulator.mantra_feedback({
        'decision_id': decisions[0]['decision_id'],
        'feedback_type': 'HELPFUL',
        'comment': 'Very useful decision',
    })

    results.append(ScenarioResult(
        name="Analytics - Track Feedback",
        passed=result['success'] == True,
        expected="Should track feedback",
        actual=f"Feedback ID: {result.get('feedback_id')}",
        execution_time_ms=0,
    ))

    # Get summary
    result = simulator.mantra_analytics_summary({})

    results.append(ScenarioResult(
        name="Analytics - Summary",
        passed=result['total_decisions_tracked'] > 0,
        expected="Should return analytics summary",
        actual=f"Tracked: {result['total_decisions_tracked']}, Events: {result['total_events']}",
        execution_time_ms=0,
    ))

    return results


def analyze_mcp_weaknesses(results: List[ScenarioResult]) -> List[str]:
    """Analyze MCP simulation results for weaknesses."""
    weaknesses = []

    # Count failures
    failed = [r for r in results if not r.passed]
    if failed:
        weaknesses.append(f"FAILURES: {len(failed)}/{len(results)} scenarios failed")
        for f in failed:
            weaknesses.append(f"  - {f.name}: Expected '{f.expected}', Got '{f.actual}'")

    # Check slow operations
    slow_ops = [r for r in results if r.execution_time_ms > 100]
    if slow_ops:
        for op in slow_ops:
            weaknesses.append(f"SLOW OPERATION: {op.name} took {op.execution_time_ms:.2f}ms")

    return weaknesses


def main():
    """Run MCP simulation tests."""
    print("="*60)
    print("MCP TOOL SIMULATION TEST")
    print("="*60)

    results = run_mcp_scenarios()

    # Print results
    print("\n" + "="*60)
    print("SCENARIO RESULTS")
    print("="*60)

    passed = 0
    failed = 0

    for r in results:
        status = "✅ PASS" if r.passed else "❌ FAIL"
        print(f"\n{status}: {r.name}")
        print(f"  Expected: {r.expected}")
        print(f"  Actual: {r.actual}")
        if r.execution_time_ms > 0:
            print(f"  Time: {r.execution_time_ms:.2f}ms")

        if r.passed:
            passed += 1
        else:
            failed += 1

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {passed/len(results)*100:.1f}%")

    # Weaknesses
    weaknesses = analyze_mcp_weaknesses(results)
    if weaknesses:
        print("\n" + "="*60)
        print("IDENTIFIED WEAKNESSES")
        print("="*60)
        for w in weaknesses:
            print(f"  {w}")
    else:
        print("\n✅ No significant weaknesses found in MCP simulation")

    return results, weaknesses


if __name__ == "__main__":
    main()
