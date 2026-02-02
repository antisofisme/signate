"""
Conflict Detection Module for MANTRA Validator

Detects potential conflicts between decisions:
1. Technology conflicts (postgresql vs mongodb, react vs vue)
2. Architecture conflicts (microservice vs monolith)
3. Pattern conflicts (sync vs async, rest vs graphql)
4. Direct contradictions (must X vs must not X)

Severity levels:
- ERROR: Same feature, conflicting decisions → BLOCK
- WARNING: Cross-feature, potential conflict → REQUIRE REVIEW
- INFO: Possible tension, worth noting → ADVISORY
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
import re


class ConflictSeverity(str, Enum):
    """Severity of detected conflict."""
    ERROR = "ERROR"      # Same feature conflict - block storage
    WARNING = "WARNING"  # Cross-feature conflict - require review
    INFO = "INFO"        # Tension - advisory only


class ConflictType(str, Enum):
    """Type of conflict detected."""
    EXCLUSIVE_TECHNOLOGY = "exclusive_technology"
    ARCHITECTURE_CONFLICT = "architecture_conflict"
    DEPLOYMENT_CONFLICT = "deployment_conflict"
    API_STYLE_CONFLICT = "api_style_conflict"
    PATTERN_CONFLICT = "pattern_conflict"
    DIRECT_CONTRADICTION = "direct_contradiction"
    SCOPE_OVERLAP = "scope_overlap"


@dataclass
class ConflictMatch:
    """A detected conflict."""
    decision_id: str
    decision_code: Optional[str]
    domain_id: str
    aspect_id: str
    statement_preview: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    description: str
    conflicting_keywords: Tuple[str, str]  # (keyword in new, keyword in existing)


@dataclass
class ConflictDetectionResult:
    """Result of conflict detection."""
    has_blocking_conflict: bool
    has_warning_conflict: bool
    conflicts: List[ConflictMatch]
    should_block: bool
    requires_review: bool
    resolution_suggestions: List[str]


# =============================================================================
# Conflict Databases
# =============================================================================

# Mutually exclusive technology pairs
# Format: (keyword1, keyword2, conflict_type, description)
CONFLICT_PAIRS: List[Tuple[str, str, ConflictType, str]] = [
    # Database conflicts
    ('postgresql', 'mongodb', ConflictType.EXCLUSIVE_TECHNOLOGY,
     'PostgreSQL (relational) conflicts with MongoDB (document store)'),
    ('postgresql', 'mysql', ConflictType.EXCLUSIVE_TECHNOLOGY,
     'PostgreSQL conflicts with MySQL - choose one primary database'),
    ('mysql', 'mongodb', ConflictType.EXCLUSIVE_TECHNOLOGY,
     'MySQL (relational) conflicts with MongoDB (document store)'),
    ('sql', 'nosql', ConflictType.EXCLUSIVE_TECHNOLOGY,
     'SQL and NoSQL are fundamentally different paradigms'),
    ('relational', 'document store', ConflictType.EXCLUSIVE_TECHNOLOGY,
     'Relational and document stores have different data models'),

    # Architecture conflicts
    ('microservice', 'monolith', ConflictType.ARCHITECTURE_CONFLICT,
     'Microservices and monolithic architecture are mutually exclusive'),
    ('microservices', 'monolithic', ConflictType.ARCHITECTURE_CONFLICT,
     'Microservices and monolithic architecture are mutually exclusive'),
    ('distributed', 'centralized', ConflictType.ARCHITECTURE_CONFLICT,
     'Distributed and centralized architectures conflict'),
    ('event-driven', 'request-response', ConflictType.ARCHITECTURE_CONFLICT,
     'Event-driven and request-response are different patterns'),
    ('cqrs', 'crud', ConflictType.ARCHITECTURE_CONFLICT,
     'CQRS and simple CRUD have different architectural implications'),

    # Deployment conflicts
    ('serverless', 'kubernetes', ConflictType.DEPLOYMENT_CONFLICT,
     'Serverless and Kubernetes represent different deployment models'),
    ('serverless', 'container', ConflictType.DEPLOYMENT_CONFLICT,
     'Serverless and container-based deployments differ fundamentally'),
    ('on-premise', 'cloud-native', ConflictType.DEPLOYMENT_CONFLICT,
     'On-premise and cloud-native have different infrastructure assumptions'),

    # API style conflicts
    ('rest', 'graphql', ConflictType.API_STYLE_CONFLICT,
     'REST and GraphQL are different API paradigms'),
    ('rest', 'grpc', ConflictType.API_STYLE_CONFLICT,
     'REST and gRPC have different use cases and trade-offs'),
    ('graphql', 'grpc', ConflictType.API_STYLE_CONFLICT,
     'GraphQL and gRPC serve different purposes'),

    # Communication pattern conflicts
    ('synchronous', 'asynchronous', ConflictType.PATTERN_CONFLICT,
     'Synchronous and asynchronous patterns have different guarantees'),
    ('sync', 'async', ConflictType.PATTERN_CONFLICT,
     'Sync and async patterns have different characteristics'),
    ('push', 'pull', ConflictType.PATTERN_CONFLICT,
     'Push and pull patterns have different implications'),
    ('polling', 'websocket', ConflictType.PATTERN_CONFLICT,
     'Polling and WebSocket represent different real-time approaches'),

    # Frontend framework conflicts
    ('react', 'vue', ConflictType.EXCLUSIVE_TECHNOLOGY,
     'React and Vue are competing frontend frameworks'),
    ('react', 'angular', ConflictType.EXCLUSIVE_TECHNOLOGY,
     'React and Angular are competing frontend frameworks'),
    ('vue', 'angular', ConflictType.EXCLUSIVE_TECHNOLOGY,
     'Vue and Angular are competing frontend frameworks'),
    ('svelte', 'react', ConflictType.EXCLUSIVE_TECHNOLOGY,
     'Svelte and React are competing frontend frameworks'),

    # Backend framework conflicts (within same language)
    ('django', 'flask', ConflictType.EXCLUSIVE_TECHNOLOGY,
     'Django and Flask are competing Python web frameworks'),
    ('fastapi', 'django', ConflictType.EXCLUSIVE_TECHNOLOGY,
     'FastAPI and Django have different design philosophies'),
    ('express', 'nestjs', ConflictType.EXCLUSIVE_TECHNOLOGY,
     'Express and NestJS have different approaches'),

    # State management conflicts
    ('redux', 'mobx', ConflictType.EXCLUSIVE_TECHNOLOGY,
     'Redux and MobX are competing state management solutions'),
    ('vuex', 'pinia', ConflictType.EXCLUSIVE_TECHNOLOGY,
     'Vuex and Pinia are competing Vue state solutions'),

    # Testing strategy conflicts
    ('unit-test-only', 'integration-test-only', ConflictType.PATTERN_CONFLICT,
     'Testing strategy should include both unit and integration tests'),
    ('manual-testing', 'automated-testing', ConflictType.PATTERN_CONFLICT,
     'Manual and automated testing have different trade-offs'),
]

# Direct contradiction patterns
# Format: (positive_pattern, negative_pattern)
CONTRADICTION_PATTERNS: List[Tuple[str, str]] = [
    (r'\bmust\s+use\s+(\w+)', r'\bmust\s+not\s+use\s+\1'),
    (r'\brequire[sd]?\s+(\w+)', r'\bprohibit[sd]?\s+\1'),
    (r'\balways\s+(\w+)', r'\bnever\s+\1'),
    (r'\benable[sd]?\s+(\w+)', r'\bdisable[sd]?\s+\1'),
    (r'\ballow[sd]?\s+(\w+)', r'\bforbid[sd]?\s+\1'),
    (r'\bshall\s+(\w+)', r'\bshall\s+not\s+\1'),
    (r'\bwill\s+(\w+)', r'\bwill\s+not\s+\1'),
]


# =============================================================================
# Conflict Detection Functions
# =============================================================================

def extract_tech_keywords(text: str) -> Set[str]:
    """Extract technology-related keywords from text."""
    text_lower = text.lower()
    keywords = set()

    # Extract from conflict pairs
    all_tech_keywords = set()
    for kw1, kw2, _, _ in CONFLICT_PAIRS:
        all_tech_keywords.add(kw1)
        all_tech_keywords.add(kw2)

    # Check each keyword
    for kw in all_tech_keywords:
        if kw in text_lower:
            keywords.add(kw)

    return keywords


def check_keyword_conflict(
    record: Dict[str, Any],
    existing: Dict[str, Any]
) -> List[ConflictMatch]:
    """
    Check for keyword-based conflicts.

    Returns list of conflicts found.
    """
    conflicts = []

    new_statement = (record.get('statement') or '').lower()  # Handle None
    existing_statement = (existing.get('statement') or '').lower()  # Handle None

    new_keywords = extract_tech_keywords(new_statement)
    existing_keywords = extract_tech_keywords(existing_statement)

    # Check each conflict pair
    for kw1, kw2, conflict_type, description in CONFLICT_PAIRS:
        # Check if new has kw1 and existing has kw2 (or vice versa)
        has_conflict = False
        conflicting_pair = None

        if kw1 in new_keywords and kw2 in existing_keywords:
            has_conflict = True
            conflicting_pair = (kw1, kw2)
        elif kw2 in new_keywords and kw1 in existing_keywords:
            has_conflict = True
            conflicting_pair = (kw2, kw1)

        if has_conflict:
            # Determine severity based on aspect match
            same_aspect = (record.get('aspect_id') == existing.get('aspect_id'))
            same_domain = (record.get('domain_id') == existing.get('domain_id'))

            if same_aspect:
                severity = ConflictSeverity.ERROR
            elif same_domain:
                severity = ConflictSeverity.WARNING
            else:
                severity = ConflictSeverity.INFO

            conflicts.append(ConflictMatch(
                decision_id=existing.get('decision_id') or '',
                decision_code=existing.get('decision_code'),
                domain_id=existing.get('domain_id') or '',
                aspect_id=existing.get('aspect_id') or '',
                statement_preview=(existing.get('statement') or '')[:100],
                conflict_type=conflict_type,
                severity=severity,
                description=description,
                conflicting_keywords=conflicting_pair
            ))

    return conflicts


def check_contradiction(
    record: Dict[str, Any],
    existing: Dict[str, Any]
) -> List[ConflictMatch]:
    """
    Check for direct contradictions using pattern matching.

    E.g., "must use X" vs "must not use X"
    """
    conflicts = []

    new_statement = (record.get('statement') or '').lower()  # Handle None
    existing_statement = (existing.get('statement') or '').lower()  # Handle None

    for pos_pattern, neg_pattern_template in CONTRADICTION_PATTERNS:
        # Check if new has positive form
        pos_match_new = re.search(pos_pattern, new_statement)

        if pos_match_new:
            try:
                # Get the captured word from positive match
                captured_word = pos_match_new.group(1)
                # Build actual negative pattern by replacing \1 with the word
                neg_pattern = neg_pattern_template.replace(r'\1', re.escape(captured_word))

                # Check if existing has the negative form
                neg_match_existing = re.search(neg_pattern, existing_statement)

                if neg_match_existing:
                    same_aspect = (record.get('aspect_id') == existing.get('aspect_id'))

                    conflicts.append(ConflictMatch(
                        decision_id=existing.get('decision_id') or '',
                        decision_code=existing.get('decision_code'),
                        domain_id=existing.get('domain_id') or '',
                        aspect_id=existing.get('aspect_id') or '',
                        statement_preview=(existing.get('statement') or '')[:100],
                        conflict_type=ConflictType.DIRECT_CONTRADICTION,
                        severity=ConflictSeverity.ERROR if same_aspect else ConflictSeverity.WARNING,
                        description=f"Direct contradiction: '{pos_match_new.group(0)}' vs '{neg_match_existing.group(0)}'",
                        conflicting_keywords=(captured_word, f"not {captured_word}")
                    ))
            except (IndexError, AttributeError, re.error):
                pass

        # Check reverse (existing has positive, new has negative)
        pos_match_existing = re.search(pos_pattern, existing_statement)

        if pos_match_existing:
            try:
                # Get the captured word from existing's positive match
                captured_word = pos_match_existing.group(1)
                # Build actual negative pattern
                neg_pattern = neg_pattern_template.replace(r'\1', re.escape(captured_word))

                # Check if new has the negative form
                neg_match_new = re.search(neg_pattern, new_statement)

                if neg_match_new:
                    same_aspect = (record.get('aspect_id') == existing.get('aspect_id'))

                    conflicts.append(ConflictMatch(
                        decision_id=existing.get('decision_id') or '',
                        decision_code=existing.get('decision_code'),
                        domain_id=existing.get('domain_id') or '',
                        aspect_id=existing.get('aspect_id') or '',
                        statement_preview=(existing.get('statement') or '')[:100],
                        conflict_type=ConflictType.DIRECT_CONTRADICTION,
                        severity=ConflictSeverity.ERROR if same_aspect else ConflictSeverity.WARNING,
                        description=f"Direct contradiction: new prohibits what existing requires ('{captured_word}')",
                        conflicting_keywords=(f"not {captured_word}", captured_word)
                    ))
            except (IndexError, AttributeError, re.error):
                pass

    return conflicts


def check_scope_overlap(
    record: Dict[str, Any],
    existing: Dict[str, Any]
) -> Optional[ConflictMatch]:
    """
    Check for scope overlap without supersedes relationship.

    Same domain + aspect + scope without supersedes = potential conflict.
    """
    same_domain = record.get('domain_id') == existing.get('domain_id')
    same_aspect = record.get('aspect_id') == existing.get('aspect_id')
    same_scope = record.get('scope') == existing.get('scope')

    # Check if there's a supersedes relationship
    supersedes = record.get('supersedes')
    is_superseding = supersedes == existing.get('decision_id')

    if same_domain and same_aspect and same_scope and not is_superseding:
        return ConflictMatch(
            decision_id=existing.get('decision_id') or '',
            decision_code=existing.get('decision_code'),
            domain_id=existing.get('domain_id') or '',
            aspect_id=existing.get('aspect_id') or '',
            statement_preview=(existing.get('statement') or '')[:100],
            conflict_type=ConflictType.SCOPE_OVERLAP,
            severity=ConflictSeverity.WARNING,
            description=f"Same domain/aspect/scope without supersedes relationship",
            conflicting_keywords=(record.get('scope') or '', existing.get('scope') or '')
        )

    return None


def generate_resolution_suggestions(conflicts: List[ConflictMatch]) -> List[str]:
    """Generate suggestions for resolving conflicts."""
    suggestions = []

    for conflict in conflicts:
        if conflict.conflict_type == ConflictType.DIRECT_CONTRADICTION:
            suggestions.append(
                f"Review contradiction with {conflict.decision_code or conflict.decision_id[:8]}. "
                f"Consider using 'supersedes' if replacing the decision."
            )
        elif conflict.conflict_type == ConflictType.EXCLUSIVE_TECHNOLOGY:
            suggestions.append(
                f"Technology conflict detected with {conflict.decision_code or conflict.decision_id[:8]}. "
                f"Ensure decisions are for different use cases or update with 'supersedes'."
            )
        elif conflict.conflict_type == ConflictType.SCOPE_OVERLAP:
            suggestions.append(
                f"Scope overlap with {conflict.decision_code or conflict.decision_id[:8]}. "
                f"Consider using 'supersedes' or adjusting scope."
            )
        elif conflict.severity == ConflictSeverity.ERROR:
            suggestions.append(
                f"Critical conflict with {conflict.decision_code or conflict.decision_id[:8]} "
                f"in same aspect. Must resolve before storing."
            )

    return suggestions[:5]  # Limit to top 5


# =============================================================================
# Main Detection Function
# =============================================================================

def detect_conflicts(
    record: Dict[str, Any],
    existing_decisions: List[Dict[str, Any]]
) -> ConflictDetectionResult:
    """
    Detect conflicts against existing decisions.

    Args:
        record: New decision record
        existing_decisions: List of existing decision dicts

    Returns:
        ConflictDetectionResult with all conflicts
    """
    all_conflicts: List[ConflictMatch] = []

    decision_id = record.get('decision_id', '')

    for existing in existing_decisions:
        # Skip self-comparison
        if existing.get('decision_id') == decision_id:
            continue

        # Check keyword-based conflicts
        keyword_conflicts = check_keyword_conflict(record, existing)
        all_conflicts.extend(keyword_conflicts)

        # Check direct contradictions
        contradiction_conflicts = check_contradiction(record, existing)
        all_conflicts.extend(contradiction_conflicts)

        # Check scope overlap
        scope_conflict = check_scope_overlap(record, existing)
        if scope_conflict:
            all_conflicts.append(scope_conflict)

    # Remove duplicates (same decision_id + conflict_type)
    seen = set()
    unique_conflicts = []
    for conflict in all_conflicts:
        key = (conflict.decision_id, conflict.conflict_type)
        if key not in seen:
            seen.add(key)
            unique_conflicts.append(conflict)

    # Sort by severity (ERROR first)
    severity_order = {
        ConflictSeverity.ERROR: 0,
        ConflictSeverity.WARNING: 1,
        ConflictSeverity.INFO: 2
    }
    unique_conflicts.sort(key=lambda c: severity_order.get(c.severity, 3))

    # Determine blocking status
    has_error = any(c.severity == ConflictSeverity.ERROR for c in unique_conflicts)
    has_warning = any(c.severity == ConflictSeverity.WARNING for c in unique_conflicts)

    # Generate resolution suggestions
    suggestions = generate_resolution_suggestions(unique_conflicts)

    return ConflictDetectionResult(
        has_blocking_conflict=has_error,
        has_warning_conflict=has_warning,
        conflicts=unique_conflicts[:10],  # Limit to top 10
        should_block=has_error,
        requires_review=has_warning and not has_error,
        resolution_suggestions=suggestions
    )


# =============================================================================
# Async Helper for Repository Integration
# =============================================================================

async def detect_conflicts_async(
    record: Dict[str, Any],
    repository
) -> ConflictDetectionResult:
    """
    Async version that fetches existing decisions from repository.

    Args:
        record: Decision record to check
        repository: DecisionRepository instance

    Returns:
        ConflictDetectionResult
    """
    # Fetch all decisions for conflict check
    stored_decisions = await repository.find_all_async(limit=10000, offset=0)

    existing_decisions = [
        {
            'decision_id': sd.decision.decision_id,
            'decision_code': sd.decision.decision_code,
            'domain_id': sd.decision.domain_id.value,
            'aspect_id': sd.decision.aspect_id.value,
            'statement': sd.decision.statement,
            'scope': sd.decision.scope.value,
            'supersedes': sd.decision.supersedes,
        }
        for sd in stored_decisions
    ]

    return detect_conflicts(record, existing_decisions)
