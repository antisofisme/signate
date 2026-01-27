"""
Quality Scoring Module for MANTRA Validator

Implements Q-001 to Q-025 quality rules:
- Statement Quality (20 pts): Q-001 to Q-005
- Rationale Quality (20 pts): Q-006 to Q-010
- Constraint Quality (20 pts): Q-011 to Q-015
- Metadata Quality (20 pts): Q-016 to Q-020
- Advanced Quality (40 pts): Q-021 to Q-025 (Readability, Coherence, Objectivity)

REBALANCED: Advanced metrics now contribute more (40%) because they measure
SUBSTANCE (semantic coherence, readability) vs FORM (length, keywords).
Total: 120 points (scaled to 100)
Grades: EXCELLENT (90+), GOOD (70-89), FAIR (50-69), POOR (30-49), REJECT (<30)

Phase 2 Upgrade:
- Q-023 (Coherence) now uses semantic similarity via Sentence-BERT
- Falls back to TF-IDF hybrid if sentence-transformers not installed
- Thresholds adjusted for semantic vs lexical similarity methods
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
from enum import Enum
import re

from .readability_metrics import (
    calculate_readability,
    calculate_domain_aware_readability,
    ReadabilityScore
)


class QualityGrade(str, Enum):
    """Quality grade based on overall score."""
    EXCELLENT = "EXCELLENT"  # 90-100
    GOOD = "GOOD"            # 70-89
    FAIR = "FAIR"            # 50-69
    POOR = "POOR"            # 30-49
    REJECT = "REJECT"        # 0-29


@dataclass
class QualityDimension:
    """Quality score for a single dimension."""
    dimension: str
    score: int
    max_score: int
    rules_passed: List[str]
    rules_failed: List[str]
    suggestions: List[str]


@dataclass
class QualityAssessment:
    """Complete quality assessment result."""
    overall_score: int
    grade: QualityGrade
    statement_score: int
    rationale_score: int
    constraint_score: int
    metadata_score: int
    advanced_score: int  # NEW: Q-021 to Q-025
    dimensions: List[QualityDimension]
    improvement_suggestions: List[str]
    can_store: bool  # False if score < 30

    # NEW: Advanced metrics
    readability: Optional[dict] = None  # Readability metrics for statement/rationale
    coherence_score: float = 0.0        # Statement-rationale coherence (0-1)
    objectivity_issues: List[str] = field(default_factory=list)  # Detected bias


# =============================================================================
# Keyword Databases
# =============================================================================

# Action verbs that indicate a clear decision
ACTION_VERBS = {
    'use', 'implement', 'adopt', 'require', 'enforce', 'ensure', 'maintain',
    'establish', 'define', 'create', 'build', 'deploy', 'migrate', 'integrate',
    'standardize', 'prohibit', 'restrict', 'limit', 'mandate', 'support'
}

# Vague words that reduce specificity
VAGUE_WORDS = {
    'something', 'stuff', 'thing', 'somehow', 'maybe', 'possibly', 'perhaps',
    'sort of', 'kind of', 'a bit', 'somewhat', 'various', 'etc', 'and so on',
    'good', 'better', 'best', 'nice', 'great', 'awesome', 'cool'
}

# Technical terminology (domain keywords)
TECHNICAL_KEYWORDS = {
    # Database
    'database', 'postgresql', 'mongodb', 'mysql', 'redis', 'schema', 'table',
    'index', 'query', 'transaction', 'acid', 'replication', 'sharding',
    # Architecture
    'microservice', 'monolith', 'api', 'rest', 'graphql', 'grpc', 'service',
    'module', 'component', 'layer', 'boundary', 'contract', 'interface',
    # Infrastructure
    'docker', 'kubernetes', 'nomad', 'terraform', 'cloud', 'aws', 'gcp',
    'azure', 'container', 'pod', 'deployment', 'scaling', 'load balancer',
    # Security
    'authentication', 'authorization', 'encryption', 'ssl', 'tls', 'jwt',
    'oauth', 'rbac', 'acl', 'security', 'compliance', 'audit',
    # Frontend
    'react', 'vue', 'angular', 'typescript', 'javascript', 'css', 'html',
    'component', 'state', 'hooks', 'redux', 'ui', 'ux',
    # Backend
    'fastapi', 'django', 'flask', 'node', 'express', 'endpoint', 'route',
    'middleware', 'handler', 'controller', 'service layer'
}

# Causal keywords indicating explanation
CAUSAL_KEYWORDS = {
    'because', 'since', 'therefore', 'thus', 'hence', 'as a result',
    'due to', 'owing to', 'in order to', 'so that', 'enables', 'allows',
    'provides', 'ensures', 'prevents', 'reduces', 'improves', 'increases'
}

# Alternative consideration keywords
ALTERNATIVE_KEYWORDS = {
    'instead of', 'rather than', 'compared to', 'unlike', 'alternative',
    'option', 'considered', 'evaluated', 'rejected', 'chose', 'selected',
    'over', 'versus', 'vs', 'trade-off', 'tradeoff'
}

# Ambiguous phrases
AMBIGUOUS_PHRASES = [
    r'\bas needed\b', r'\bwhen appropriate\b', r'\bif necessary\b',
    r'\bas required\b', r'\bin some cases\b', r'\bsometimes\b',
    r'\bshould be\b.*\bgood\b', r'\bmay\s+or\s+may\s+not\b'
]

# Scope keywords
SCOPE_KEYWORDS = {
    'ORGANIZATION': ['all', 'every', 'company', 'enterprise', 'organization', 'entire', 'global'],
    'DOMAIN': ['domain', 'bounded', 'service', 'team', 'department', 'module'],
    'APPLICATION': ['application', 'app', 'this', 'specific', 'local', 'single']
}

# Blast radius keywords
BLAST_RADIUS_KEYWORDS = {
    'CRITICAL': ['database', 'auth', 'security', 'all services', 'entire', 'foundation', 'core'],
    'HIGH': ['api', 'integration', 'service', 'backend', 'infrastructure'],
    'MEDIUM': ['module', 'component', 'feature', 'frontend', 'ui'],
    'LOW': ['utility', 'helper', 'tool', 'script', 'minor', 'small']
}

# =============================================================================
# NEW: Bias Detection Keywords (for Q-024)
# =============================================================================

# Cognitive bias indicators in rationale
BIAS_PHRASES = {
    # Confirmation bias
    'confirmation': [
        r'\bas expected\b', r'\bobviously\b', r'\bclearly\b', r'\bof course\b',
        r'\bnaturally\b', r'\beveryone knows\b', r'\bcommon knowledge\b'
    ],
    # Overconfidence bias
    'overconfidence': [
        r'\bdefinitely\b', r'\bguaranteed\b', r'\b100%\b', r'\babsolutely\b',
        r'\bno doubt\b', r'\bcertainly\b', r'\bwithout fail\b', r'\bperfect\b'
    ],
    # Groupthink
    'groupthink': [
        r'\beveryone agrees\b', r'\bteam consensus\b', r'\bunanimous\b',
        r'\bno objections\b', r'\ball stakeholders agree\b'
    ],
    # Anchoring bias (relying too much on first info)
    'anchoring': [
        r'\bfirst option\b', r'\binitial choice\b', r'\boriginal plan\b'
    ],
    # Sunk cost fallacy
    'sunk_cost': [
        r'\balready invested\b', r'\btoo late to change\b', r'\bcan\'t go back\b',
        r'\bcome too far\b', r'\bwasted effort\b'
    ],
    # Appeal to authority (without evidence)
    'authority': [
        r'\bexpert says\b', r'\bguru\b', r'\bbest practice\b(?!.*because)',
        r'\bindustry standard\b(?!.*because)'
    ]
}

# Objectivity indicators (positive - these are good)
OBJECTIVITY_KEYWORDS = {
    'evidence', 'data', 'metrics', 'benchmark', 'test', 'proven',
    'measured', 'quantified', 'analysis', 'research', 'study',
    'comparison', 'evaluation', 'assessment', 'criteria'
}


# =============================================================================
# Scoring Functions
# =============================================================================

def score_statement_quality(record: Dict[str, Any]) -> Tuple[int, QualityDimension]:
    """
    Score statement quality (Q-001 to Q-005).
    Max: 20 points (REBALANCED: was 25 - Advanced dimensions now weighted higher)
    """
    statement = record.get('statement') or ''  # Handle None values
    score = 0
    rules_passed = []
    rules_failed = []
    suggestions = []

    words = statement.lower().split()
    word_count = len(words)

    # Q-001: Length (10-200 words) - 4 points (REBALANCED: was 5)
    if 10 <= word_count <= 200:
        score += 4
        rules_passed.append('Q-001')
    elif 5 <= word_count < 10:
        score += 2
        rules_failed.append('Q-001')
        suggestions.append(f'Statement is too short ({word_count} words). Aim for 10-200 words for clarity.')
    elif word_count < 5:
        score += 0
        rules_failed.append('Q-001')
        suggestions.append(f'Statement is very short ({word_count} words). Add more detail.')
    else:
        score += 2
        rules_failed.append('Q-001')
        suggestions.append(f'Statement is too long ({word_count} words). Consider being more concise.')

    # Q-002: Contains action verb - 4 points (REBALANCED: was 5)
    has_action_verb = any(verb in words for verb in ACTION_VERBS)
    if has_action_verb:
        score += 4
        rules_passed.append('Q-002')
    else:
        score += 0
        rules_failed.append('Q-002')
        suggestions.append('Add an action verb (use, implement, require, enforce, etc.) for clarity.')

    # Q-003: Specificity (no vague words) - 4 points (REBALANCED: was 5)
    vague_count = sum(1 for word in words if word in VAGUE_WORDS)
    if vague_count == 0:
        score += 4
        rules_passed.append('Q-003')
    elif vague_count <= 2:
        score += 2
        rules_failed.append('Q-003')
        suggestions.append('Reduce vague language for more precise statement.')
    else:
        score += 0
        rules_failed.append('Q-003')
        suggestions.append('Statement contains too many vague words. Be more specific.')

    # Q-004: Technical terminology present - 4 points (REBALANCED: was 5)
    tech_count = sum(1 for word in words if word in TECHNICAL_KEYWORDS)
    if tech_count >= 2:
        score += 4
        rules_passed.append('Q-004')
    elif tech_count == 1:
        score += 2
        rules_failed.append('Q-004')
        suggestions.append('Add more technical specificity (technologies, patterns, etc.).')
    else:
        score += 0
        rules_failed.append('Q-004')
        suggestions.append('Statement lacks technical terminology. Specify technologies or patterns.')

    # Q-005: No ambiguity (no ambiguous phrases) - 4 points (REBALANCED: was 5)
    text_lower = statement.lower()
    has_ambiguity = any(re.search(pattern, text_lower) for pattern in AMBIGUOUS_PHRASES)
    if not has_ambiguity:
        score += 4
        rules_passed.append('Q-005')
    else:
        score += 2
        rules_failed.append('Q-005')
        suggestions.append('Remove ambiguous phrases like "as needed", "if necessary", etc.')

    return score, QualityDimension(
        dimension='statement',
        score=score,
        max_score=20,  # REBALANCED: was 25
        rules_passed=rules_passed,
        rules_failed=rules_failed,
        suggestions=suggestions
    )


def score_rationale_quality(record: Dict[str, Any]) -> Tuple[int, QualityDimension]:
    """
    Score rationale quality (Q-006 to Q-010).
    Max: 20 points (REBALANCED: was 25 - Advanced dimensions now weighted higher)
    """
    rationale = record.get('rationale') or ''  # Handle None values
    statement = record.get('statement') or ''  # Handle None values
    score = 0
    rules_passed = []
    rules_failed = []
    suggestions = []

    words = rationale.lower().split()
    word_count = len(words)

    # Q-006: Length (20-500 words) - 4 points (REBALANCED: was 5)
    if 20 <= word_count <= 500:
        score += 4
        rules_passed.append('Q-006')
    elif 10 <= word_count < 20:
        score += 2
        rules_failed.append('Q-006')
        suggestions.append(f'Rationale is short ({word_count} words). Expand to explain the decision better.')
    elif word_count < 10:
        score += 0
        rules_failed.append('Q-006')
        suggestions.append(f'Rationale is too brief ({word_count} words). Provide meaningful explanation.')
    else:
        score += 2
        rules_failed.append('Q-006')
        suggestions.append('Rationale is too long. Focus on key points.')

    # Q-007: Explains "why" (causal keywords) - 4 points (REBALANCED: was 5)
    text_lower = rationale.lower()
    has_causal = any(kw in text_lower for kw in CAUSAL_KEYWORDS)
    if has_causal:
        score += 4
        rules_passed.append('Q-007')
    else:
        score += 0
        rules_failed.append('Q-007')
        suggestions.append('Explain WHY this decision was made using words like "because", "enables", "provides".')

    # Q-008: References context/problem - 4 points (REBALANCED: was 5)
    context_keywords = ['problem', 'issue', 'challenge', 'requirement', 'need', 'context', 'currently', 'existing']
    has_context = any(kw in text_lower for kw in context_keywords)
    if has_context:
        score += 4
        rules_passed.append('Q-008')
    else:
        score += 2
        rules_failed.append('Q-008')
        suggestions.append('Reference the problem or context that led to this decision.')

    # Q-009: Considers alternatives - 4 points (REBALANCED: was 5)
    has_alternatives = any(kw in text_lower for kw in ALTERNATIVE_KEYWORDS)
    if has_alternatives:
        score += 4
        rules_passed.append('Q-009')
    else:
        score += 2
        rules_failed.append('Q-009')
        suggestions.append('Mention alternatives considered and why they were rejected.')

    # Q-010: Coherent with statement (keyword overlap) - 4 points (REBALANCED: was 5)
    statement_keywords = set(statement.lower().split()) - {'the', 'a', 'an', 'is', 'are', 'to', 'for', 'and', 'or', 'in', 'on', 'with'}
    rationale_keywords = set(words) - {'the', 'a', 'an', 'is', 'are', 'to', 'for', 'and', 'or', 'in', 'on', 'with'}
    overlap = len(statement_keywords & rationale_keywords)

    if overlap >= 3:
        score += 4
        rules_passed.append('Q-010')
    elif overlap >= 1:
        score += 2
        rules_failed.append('Q-010')
        suggestions.append('Rationale should directly reference terms from the statement.')
    else:
        score += 0
        rules_failed.append('Q-010')
        suggestions.append('Rationale seems disconnected from statement. Ensure coherence.')

    return score, QualityDimension(
        dimension='rationale',
        score=score,
        max_score=20,  # REBALANCED: was 25
        rules_passed=rules_passed,
        rules_failed=rules_failed,
        suggestions=suggestions
    )


def score_constraint_quality(record: Dict[str, Any]) -> Tuple[int, QualityDimension]:
    """
    Score constraint quality (Q-011 to Q-015).
    Max: 20 points (REBALANCED: was 25 - Advanced dimensions now weighted higher)
    """
    constraints = record.get('constraints', [])
    invariants = record.get('invariants', [])
    score = 0
    rules_passed = []
    rules_failed = []
    suggestions = []

    # Q-011: Has at least 1 constraint - 4 points (REBALANCED: was 5)
    if len(constraints) >= 1 or len(invariants) >= 1:
        score += 4
        rules_passed.append('Q-011')
    else:
        score += 0
        rules_failed.append('Q-011')
        suggestions.append('Add at least one constraint or invariant to make the decision enforceable.')

    # Q-012: Type diversity (multiple constraint types) - 4 points (REBALANCED: was 5)
    types_used = set()
    for c in constraints:
        if isinstance(c, dict):
            types_used.add(c.get('type', ''))

    if len(types_used) >= 2:
        score += 4
        rules_passed.append('Q-012')
    elif len(types_used) == 1:
        score += 2
        rules_failed.append('Q-012')
        suggestions.append('Consider adding different constraint types (REQUIREMENT, PROHIBITION, LIMITATION).')
    else:
        score += 0
        rules_failed.append('Q-012')

    # Q-013: Constraints are actionable (have verbs) - 4 points (REBALANCED: was 5)
    actionable_count = 0
    for c in constraints:
        if isinstance(c, dict):
            stmt = c.get('statement', '').lower()
            if any(verb in stmt for verb in ACTION_VERBS | {'must', 'shall', 'cannot', 'should'}):
                actionable_count += 1

    if actionable_count == len(constraints) and len(constraints) > 0:
        score += 4
        rules_passed.append('Q-013')
    elif actionable_count > 0:
        score += 2
        rules_failed.append('Q-013')
        suggestions.append('Make all constraints actionable with clear verbs (must, shall, cannot).')
    else:
        score += 0
        rules_failed.append('Q-013')
        if len(constraints) > 0:
            suggestions.append('Constraints should be actionable statements.')

    # Q-014: Constraints are verifiable (measurable terms) - 4 points (REBALANCED: was 5)
    verifiable_keywords = ['all', 'every', 'no', 'none', 'only', 'exactly', 'at least', 'at most', 'within', 'before', 'after']
    verifiable_count = 0
    for c in constraints:
        if isinstance(c, dict):
            stmt = c.get('statement', '').lower()
            if any(kw in stmt for kw in verifiable_keywords):
                verifiable_count += 1

    if verifiable_count == len(constraints) and len(constraints) > 0:
        score += 4
        rules_passed.append('Q-014')
    elif verifiable_count > 0:
        score += 2
        rules_failed.append('Q-014')
        suggestions.append('Make constraints verifiable with measurable terms.')
    else:
        score += 0
        rules_failed.append('Q-014')

    # Q-015: Non-contradicting constraints - 4 points (REBALANCED: was 5)
    # Simple check: no "must" and "must not" for same subject
    has_contradiction = False
    must_subjects = []
    must_not_subjects = []

    for c in constraints:
        if isinstance(c, dict):
            stmt = c.get('statement', '').lower()
            if 'must not' in stmt or 'cannot' in stmt:
                # Extract subject (simplified)
                words = stmt.split()
                if len(words) > 2:
                    must_not_subjects.append(words[-1])
            elif 'must' in stmt:
                words = stmt.split()
                if len(words) > 1:
                    must_subjects.append(words[-1])

    # Check for overlap (simplified)
    if set(must_subjects) & set(must_not_subjects):
        has_contradiction = True

    if not has_contradiction and len(constraints) > 0:
        score += 4
        rules_passed.append('Q-015')
    elif has_contradiction:
        score += 0
        rules_failed.append('Q-015')
        suggestions.append('Constraints may be contradicting. Review for consistency.')
    else:
        score += 4  # No constraints = no contradictions
        rules_passed.append('Q-015')

    return score, QualityDimension(
        dimension='constraints',
        score=score,
        max_score=20,  # REBALANCED: was 25
        rules_passed=rules_passed,
        rules_failed=rules_failed,
        suggestions=suggestions
    )


def score_metadata_quality(record: Dict[str, Any]) -> Tuple[int, QualityDimension]:
    """
    Score metadata quality (Q-016 to Q-020).
    Max: 20 points (REBALANCED: was 25 - Advanced dimensions now weighted higher)
    """
    statement = (record.get('statement') or '').lower()  # Handle None values
    scope = record.get('scope') or ''
    blast_radius = record.get('blast_radius') or ''
    tags = record.get('tags') or []
    relations = record.get('relations') or []
    related_decisions = record.get('related_decisions') or []
    tech_stack = record.get('tech_stack') or []

    score = 0
    rules_passed = []
    rules_failed = []
    suggestions = []

    # Q-016: Scope matches content - 4 points (REBALANCED: was 5)
    scope_match = False
    for scope_level, keywords in SCOPE_KEYWORDS.items():
        if scope == scope_level:
            if any(kw in statement for kw in keywords):
                scope_match = True
                break

    # Also check if there's no mismatch
    if scope == 'APPLICATION' and any(kw in statement for kw in SCOPE_KEYWORDS['ORGANIZATION']):
        scope_match = False
        suggestions.append('Scope may be too narrow. Statement suggests ORGANIZATION scope.')

    if scope_match or (scope and not suggestions):
        score += 4
        rules_passed.append('Q-016')
    else:
        score += 2
        rules_failed.append('Q-016')
        if not suggestions:
            suggestions.append('Verify scope matches the decision content.')

    # Q-017: Blast radius justified - 4 points (REBALANCED: was 5)
    radius_match = False
    for radius_level, keywords in BLAST_RADIUS_KEYWORDS.items():
        if blast_radius == radius_level:
            if any(kw in statement for kw in keywords):
                radius_match = True
                break

    if radius_match or blast_radius:
        score += 4
        rules_passed.append('Q-017')
    else:
        score += 2
        rules_failed.append('Q-017')
        suggestions.append('Verify blast_radius accurately reflects potential impact.')

    # Q-018: Tags relevant - 4 points (REBALANCED: was 5)
    if tags and len(tags) >= 1:
        score += 4
        rules_passed.append('Q-018')
    else:
        score += 0
        rules_failed.append('Q-018')
        suggestions.append('Add relevant tags (FE, BE, DB, INFRA, SECURITY, etc.) for categorization.')

    # Q-019: Relations defined - 4 points (REBALANCED: was 5)
    has_relations = len(relations) > 0 or len(related_decisions) > 0
    if has_relations:
        score += 4
        rules_passed.append('Q-019')
    else:
        score += 2
        rules_failed.append('Q-019')
        suggestions.append('Consider adding relations to other decisions (depends_on, informed_by).')

    # Q-020: Tech stack specified - 4 points (REBALANCED: was 5)
    if tech_stack and len(tech_stack) >= 1:
        score += 4
        rules_passed.append('Q-020')
    else:
        score += 2
        rules_failed.append('Q-020')
        suggestions.append('Specify tech_stack for traceability (PostgreSQL, React, Docker, etc.).')

    return score, QualityDimension(
        dimension='metadata',
        score=score,
        max_score=20,  # REBALANCED: was 25
        rules_passed=rules_passed,
        rules_failed=rules_failed,
        suggestions=suggestions
    )


# =============================================================================
# Advanced Quality Scoring (Q-021 to Q-025)
# =============================================================================

def detect_bias(text: str) -> List[str]:
    """Detect cognitive bias indicators in text."""
    text_lower = text.lower()
    found_biases = []

    for bias_type, patterns in BIAS_PHRASES.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                found_biases.append(bias_type)
                break  # One match per bias type is enough

    return found_biases


def calculate_coherence(statement: str, rationale: str) -> Tuple[float, str]:
    """
    Calculate semantic coherence between statement and rationale.

    Uses Sentence-BERT if available, falls back to TF-IDF hybrid.
    Phase 2 upgrade: Now uses semantic_similarity module for true semantic matching.

    Returns:
        (coherence_score, method_used)
    """
    if not statement or not rationale:
        return 0.0, "empty"

    try:
        from .semantic_similarity import calculate_coherence_score
        score, assessment, method = calculate_coherence_score(statement, rationale)
        return score, method
    except ImportError:
        # Fallback to basic keyword overlap if module not available
        stmt_words = set(w.lower() for w in re.findall(r'\b\w{4,}\b', statement))
        rat_words = set(w.lower() for w in re.findall(r'\b\w{4,}\b', rationale))

        common_words = {'that', 'this', 'with', 'from', 'have', 'will', 'been', 'would',
                        'should', 'could', 'which', 'their', 'there', 'these', 'those'}
        stmt_words -= common_words
        rat_words -= common_words

        if not stmt_words or not rat_words:
            return 0.0, "keyword"

        intersection = len(stmt_words & rat_words)
        union = len(stmt_words | rat_words)

        return (intersection / union if union > 0 else 0.0), "keyword"


def score_advanced_quality(record: Dict[str, Any]) -> Tuple[int, QualityDimension, dict, float, List[str]]:
    """
    Score advanced quality metrics (Q-021 to Q-025).
    Max: 40 points (REBALANCED: was 20 - Advanced dimensions now weighted higher)

    These metrics capture SUBSTANCE (semantic coherence, readability) vs FORM (length, keywords).
    Substance should matter more for decision quality.

    Returns:
        (score, dimension, readability_dict, coherence_score, bias_issues)
    """
    statement = record.get('statement') or ''
    rationale = record.get('rationale') or ''

    score = 0
    rules_passed = []
    rules_failed = []
    suggestions = []

    # Calculate readability with domain-aware adjustment
    # Technical vocabulary doesn't penalize readability
    stmt_readability = calculate_domain_aware_readability(statement) if len(statement) > 20 else None
    rat_readability = calculate_domain_aware_readability(rationale) if len(rationale) > 20 else None

    readability_dict = {
        'statement': {
            'flesch_kincaid_grade': stmt_readability.flesch_kincaid_grade if stmt_readability else None,
            'flesch_reading_ease': stmt_readability.flesch_reading_ease if stmt_readability else None,
            'gunning_fog': stmt_readability.gunning_fog if stmt_readability else None,
            'grade_level': stmt_readability.grade_level if stmt_readability else None,
            'is_appropriate': stmt_readability.is_appropriate if stmt_readability else None,
            'complexity_warning': stmt_readability.complexity_warning if stmt_readability else None,
        } if stmt_readability else None,
        'rationale': {
            'flesch_kincaid_grade': rat_readability.flesch_kincaid_grade if rat_readability else None,
            'flesch_reading_ease': rat_readability.flesch_reading_ease if rat_readability else None,
            'gunning_fog': rat_readability.gunning_fog if rat_readability else None,
            'grade_level': rat_readability.grade_level if rat_readability else None,
            'is_appropriate': rat_readability.is_appropriate if rat_readability else None,
            'complexity_warning': rat_readability.complexity_warning if rat_readability else None,
        } if rat_readability else None,
    }

    # Q-021: Statement Readability (8 points - REBALANCED: was 4)
    if stmt_readability:
        if stmt_readability.is_appropriate:
            score += 8
            rules_passed.append('Q-021')
        elif stmt_readability.flesch_kincaid_grade > 16:
            score += 2
            rules_failed.append('Q-021')
            suggestions.append(f"Statement too complex (Grade {stmt_readability.flesch_kincaid_grade}). Simplify language.")
        elif stmt_readability.flesch_kincaid_grade < 6:
            score += 4
            rules_failed.append('Q-021')
            suggestions.append(f"Statement too simple (Grade {stmt_readability.flesch_kincaid_grade}). Add technical precision.")
        else:
            score += 6
            rules_passed.append('Q-021')
    else:
        score += 4  # Can't assess, give partial credit
        rules_failed.append('Q-021')

    # Q-022: Rationale Readability (8 points - REBALANCED: was 4)
    if rat_readability:
        if rat_readability.is_appropriate:
            score += 8
            rules_passed.append('Q-022')
        elif rat_readability.flesch_kincaid_grade > 16:
            score += 2
            rules_failed.append('Q-022')
            suggestions.append(f"Rationale too complex (Grade {rat_readability.flesch_kincaid_grade}). Use clearer language.")
        elif rat_readability.flesch_kincaid_grade < 6:
            score += 4
            rules_failed.append('Q-022')
            suggestions.append(f"Rationale too simple (Grade {rat_readability.flesch_kincaid_grade}). Add technical depth.")
        else:
            score += 6
            rules_passed.append('Q-022')
    else:
        score += 4  # Can't assess
        rules_failed.append('Q-022')

    # Q-023: Statement-Rationale Coherence (10 points - REBALANCED: was 4)
    # This is the MOST IMPORTANT metric - semantic alignment is critical
    # Using semantic similarity (SBERT if available, TF-IDF fallback)
    coherence, coherence_method = calculate_coherence(statement, rationale)

    # Thresholds adjusted for semantic similarity:
    # SBERT typically gives higher scores than keyword overlap
    if coherence_method == "sbert":
        threshold_high, threshold_mid = 0.5, 0.3
    else:
        threshold_high, threshold_mid = 0.35, 0.2

    if coherence >= threshold_high:
        score += 10
        rules_passed.append('Q-023')
    elif coherence >= threshold_mid:
        score += 5
        rules_failed.append('Q-023')
        suggestions.append("Rationale should more directly relate to statement meaning.")
    else:
        score += 0
        rules_failed.append('Q-023')
        suggestions.append(f"Rationale seems disconnected from statement (coherence: {coherence:.2f}). Ensure semantic alignment.")

    # Q-024: Rationale Objectivity (6 points - REBALANCED: was 4)
    biases = detect_bias(rationale)
    if not biases:
        score += 6
        rules_passed.append('Q-024')
    elif len(biases) == 1:
        score += 3
        rules_failed.append('Q-024')
        suggestions.append(f"Potential {biases[0]} bias detected. Add evidence-based justification.")
    else:
        score += 0
        rules_failed.append('Q-024')
        suggestions.append(f"Multiple biases detected ({', '.join(biases)}). Use objective, evidence-based language.")

    # Q-025: Evidence-Based Language (8 points - REBALANCED: was 4)
    rat_lower = rationale.lower()
    evidence_count = sum(1 for kw in OBJECTIVITY_KEYWORDS if kw in rat_lower)
    if evidence_count >= 3:
        score += 8
        rules_passed.append('Q-025')
    elif evidence_count >= 1:
        score += 4
        rules_failed.append('Q-025')
        suggestions.append("Add more evidence-based language (data, metrics, benchmarks).")
    else:
        score += 0
        rules_failed.append('Q-025')
        suggestions.append("Include evidence or data to support the decision rationale.")

    dimension = QualityDimension(
        dimension='advanced',
        score=score,
        max_score=40,  # REBALANCED: was 20
        rules_passed=rules_passed,
        rules_failed=rules_failed,
        suggestions=suggestions
    )

    # Include coherence method in readability dict for transparency
    readability_dict['coherence_method'] = coherence_method

    return score, dimension, readability_dict, coherence, biases


def determine_grade(score: int, max_score: int = 120) -> QualityGrade:
    """
    Determine quality grade from score.

    Grades are based on percentage of max_score:
    - EXCELLENT: 90%+
    - GOOD: 70-89%
    - FAIR: 50-69%
    - POOR: 30-49%
    - REJECT: <30%
    """
    percentage = (score / max_score) * 100 if max_score > 0 else 0

    if percentage >= 90:
        return QualityGrade.EXCELLENT
    elif percentage >= 70:
        return QualityGrade.GOOD
    elif percentage >= 50:
        return QualityGrade.FAIR
    elif percentage >= 30:
        return QualityGrade.POOR
    else:
        return QualityGrade.REJECT


# =============================================================================
# Main Scoring Function
# =============================================================================

def assess_quality(record: Dict[str, Any]) -> QualityAssessment:
    """
    Perform complete quality assessment.

    Scoring breakdown (120 points total, REBALANCED):
    - Statement Quality (Q-001 to Q-005): 20 points (was 25)
    - Rationale Quality (Q-006 to Q-010): 20 points (was 25)
    - Constraint Quality (Q-011 to Q-015): 20 points (was 25)
    - Metadata Quality (Q-016 to Q-020): 20 points (was 25)
    - Advanced Quality (Q-021 to Q-025): 40 points (was 20) - NOW WEIGHTED HIGHER

    Advanced metrics measure SUBSTANCE (coherence, readability, objectivity)
    while basic metrics measure FORM (length, keywords). Substance matters more.

    Args:
        record: Decision record dictionary

    Returns:
        QualityAssessment with scores, suggestions, and advanced metrics
    """
    dimensions = []
    all_suggestions = []

    # Score each dimension
    stmt_score, stmt_dim = score_statement_quality(record)
    dimensions.append(stmt_dim)
    all_suggestions.extend(stmt_dim.suggestions)

    rat_score, rat_dim = score_rationale_quality(record)
    dimensions.append(rat_dim)
    all_suggestions.extend(rat_dim.suggestions)

    con_score, con_dim = score_constraint_quality(record)
    dimensions.append(con_dim)
    all_suggestions.extend(con_dim.suggestions)

    meta_score, meta_dim = score_metadata_quality(record)
    dimensions.append(meta_dim)
    all_suggestions.extend(meta_dim.suggestions)

    # Score advanced quality (Q-021 to Q-025)
    adv_score, adv_dim, readability, coherence, biases = score_advanced_quality(record)
    dimensions.append(adv_dim)
    all_suggestions.extend(adv_dim.suggestions)

    # Calculate overall score (120 points max)
    overall_score = stmt_score + rat_score + con_score + meta_score + adv_score
    grade = determine_grade(overall_score, max_score=120)

    # Scale overall_score to 0-100 for consistency
    scaled_score = round((overall_score / 120) * 100)

    return QualityAssessment(
        overall_score=scaled_score,
        grade=grade,
        statement_score=stmt_score,
        rationale_score=rat_score,
        constraint_score=con_score,
        metadata_score=meta_score,
        advanced_score=adv_score,
        dimensions=dimensions,
        improvement_suggestions=all_suggestions[:10],  # Limit to top 10
        can_store=scaled_score >= 30,
        readability=readability,
        coherence_score=coherence,
        objectivity_issues=biases
    )
