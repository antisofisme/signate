"""
Duplicate Detection Module for MANTRA Validator

Implements 4-level duplicate detection:
- EXACT (100%): Same group + feature + normalized statement → BLOCK
- NEAR (85-99%): High similarity in same group/feature → REQUIRE ACK
- SEMANTIC (70-84%): Similar meaning → WARNING
- RELATED (50-69%): Topic overlap → SUGGEST RELATION

Uses Jaccard similarity and keyword overlap for detection.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
from enum import Enum
import re
from collections import Counter
import math


class DuplicateLevel(str, Enum):
    """Duplicate severity level."""
    EXACT = "EXACT"        # 100% match - block storage
    NEAR = "NEAR"          # 85-99% - require acknowledgment
    SEMANTIC = "SEMANTIC"  # 70-84% - show warning
    RELATED = "RELATED"    # 50-69% - suggest relation


@dataclass
class DuplicateMatch:
    """A detected duplicate match."""
    decision_id: str
    decision_code: Optional[str]
    domain_id: str
    aspect_id: str
    statement_preview: str  # First 100 chars
    similarity: float  # 0.0 to 1.0
    level: DuplicateLevel
    reason: str  # Human-readable explanation


@dataclass
class SupersedesGuidance:
    """
    Guidance for superseding an existing decision.

    When a near-duplicate (85%+) is detected in the same group/feature,
    it likely represents an evolution of an existing decision.
    """
    detected_duplicate_id: str
    detected_duplicate_code: Optional[str]
    similarity: float
    recommendation: str  # "SUPERSEDES" or "RELATION"
    message: str
    auto_populate: Dict[str, Any]  # Suggested field values


@dataclass
class DuplicateDetectionResult:
    """Result of duplicate detection."""
    has_blocking_duplicate: bool
    has_near_duplicate: bool
    matches: List[DuplicateMatch]
    should_block: bool
    requires_acknowledgment: bool
    suggested_relations: List[str]  # Decision IDs to suggest as relations
    supersedes_guidance: Optional[SupersedesGuidance] = None  # Auto-supersedes suggestion


# =============================================================================
# Text Processing
# =============================================================================

# Common stop words to exclude from similarity
STOP_WORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
    'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
    'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'between', 'under', 'again', 'further', 'then', 'once', 'here',
    'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
    'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't',
    'just', 'don', 'now', 'and', 'or', 'but', 'if', 'while', 'this',
    'that', 'these', 'those', 'it', 'its'
}


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.

    - Lowercase
    - Remove special characters
    - Collapse whitespace
    """
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_keywords(text: str) -> Set[str]:
    """Extract meaningful keywords from text."""
    normalized = normalize_text(text)
    words = normalized.split()
    return {w for w in words if w not in STOP_WORDS and len(w) > 2}


def tokenize_for_ngrams(text: str, n: int = 2) -> List[str]:
    """Create character n-grams for fuzzy matching."""
    normalized = normalize_text(text)
    normalized = normalized.replace(' ', '')  # Remove spaces for n-grams
    if len(normalized) < n:
        return [normalized]
    return [normalized[i:i+n] for i in range(len(normalized) - n + 1)]


# =============================================================================
# Similarity Functions
# =============================================================================

def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def cosine_similarity(text1: str, text2: str) -> float:
    """Calculate cosine similarity between two texts using word frequency."""
    words1 = normalize_text(text1).split()
    words2 = normalize_text(text2).split()

    # Filter stop words
    words1 = [w for w in words1 if w not in STOP_WORDS]
    words2 = [w for w in words2 if w not in STOP_WORDS]

    # Count frequencies
    freq1 = Counter(words1)
    freq2 = Counter(words2)

    # Get all unique words
    all_words = set(freq1.keys()) | set(freq2.keys())

    if not all_words:
        return 0.0

    # Calculate dot product and magnitudes
    dot_product = sum(freq1.get(w, 0) * freq2.get(w, 0) for w in all_words)
    magnitude1 = math.sqrt(sum(v ** 2 for v in freq1.values()))
    magnitude2 = math.sqrt(sum(v ** 2 for v in freq2.values()))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def ngram_similarity(text1: str, text2: str, n: int = 2) -> float:
    """Calculate similarity using character n-grams."""
    ngrams1 = set(tokenize_for_ngrams(text1, n))
    ngrams2 = set(tokenize_for_ngrams(text2, n))
    return jaccard_similarity(ngrams1, ngrams2)


def combined_similarity(text1: str, text2: str) -> float:
    """
    Calculate combined similarity using multiple methods.

    Weighted combination:
    - 40% Jaccard (keyword overlap)
    - 40% Cosine (word frequency)
    - 20% N-gram (fuzzy character match)
    """
    keywords1 = extract_keywords(text1)
    keywords2 = extract_keywords(text2)

    jaccard = jaccard_similarity(keywords1, keywords2)
    cosine = cosine_similarity(text1, text2)
    ngram = ngram_similarity(text1, text2, n=3)

    return 0.4 * jaccard + 0.4 * cosine + 0.2 * ngram


# =============================================================================
# Duplicate Detection
# =============================================================================

def check_exact_duplicate(
    record: Dict[str, Any],
    existing: Dict[str, Any]
) -> Optional[DuplicateMatch]:
    """
    Check for exact duplicate (100% match).

    Exact match criteria:
    - Same domain_id AND aspect_id
    - Normalized statement is identical
    """
    if (record.get('domain_id') == existing.get('domain_id') and
        record.get('aspect_id') == existing.get('aspect_id')):

        norm_new = normalize_text(record.get('statement') or '')  # Handle None
        norm_existing = normalize_text(existing.get('statement') or '')  # Handle None

        if norm_new == norm_existing:
            return DuplicateMatch(
                decision_id=existing.get('decision_id') or '',
                decision_code=existing.get('decision_code'),
                domain_id=existing.get('domain_id') or '',
                aspect_id=existing.get('aspect_id') or '',
                statement_preview=(existing.get('statement') or '')[:100],
                similarity=1.0,
                level=DuplicateLevel.EXACT,
                reason=f"Exact duplicate in {existing.get('domain_id')}-{existing.get('aspect_id')}"
            )

    return None


def check_similarity_duplicate(
    record: Dict[str, Any],
    existing: Dict[str, Any],
    min_threshold: float = 0.50
) -> Optional[DuplicateMatch]:
    """
    Check for similarity-based duplicate.

    Returns match if similarity >= min_threshold.
    """
    new_statement = record.get('statement') or ''  # Handle None
    existing_statement = existing.get('statement') or ''  # Handle None

    similarity = combined_similarity(new_statement, existing_statement)

    if similarity < min_threshold:
        return None

    # Determine level based on similarity and domain/aspect match
    same_domain = record.get('domain_id') == existing.get('domain_id')
    same_aspect = record.get('aspect_id') == existing.get('aspect_id')

    if similarity >= 0.85:
        if same_domain and same_aspect:
            level = DuplicateLevel.NEAR
            reason = f"Very similar ({similarity:.0%}) in same {existing.get('domain_id')}-{existing.get('aspect_id')}"
        else:
            level = DuplicateLevel.SEMANTIC
            reason = f"Very similar ({similarity:.0%}) to {existing.get('domain_id')}-{existing.get('aspect_id')}"
    elif similarity >= 0.70:
        level = DuplicateLevel.SEMANTIC
        reason = f"Similar meaning ({similarity:.0%}) to existing decision"
    else:  # 0.50 - 0.69
        level = DuplicateLevel.RELATED
        reason = f"Related topic ({similarity:.0%}) - consider adding as relation"

    return DuplicateMatch(
        decision_id=existing.get('decision_id') or '',
        decision_code=existing.get('decision_code'),
        domain_id=existing.get('domain_id') or '',
        aspect_id=existing.get('aspect_id') or '',
        statement_preview=(existing.get('statement') or '')[:100],
        similarity=similarity,
        level=level,
        reason=reason
    )


def suggest_supersedes(
    record: Dict[str, Any],
    near_duplicate: DuplicateMatch
) -> Optional[SupersedesGuidance]:
    """
    If near-duplicate detected (85%+), provide supersedes guidance.

    When a decision is highly similar to an existing one:
    - If same domain+aspect: likely an EVOLUTION (suggest supersedes)
    - If different domain/aspect: likely RELATED (suggest relation)

    Args:
        record: The new decision record
        near_duplicate: The detected near-duplicate match

    Returns:
        SupersedesGuidance if similarity >= 85%, None otherwise
    """
    # Only provide guidance for near-duplicates (85%+)
    if near_duplicate.similarity < 0.85:
        return None

    # Check if same domain+aspect (likely evolution)
    same_cell = (
        record.get('domain_id') == near_duplicate.domain_id and
        record.get('aspect_id') == near_duplicate.aspect_id
    )

    if same_cell:
        # This appears to be an update/evolution of an existing decision
        return SupersedesGuidance(
            detected_duplicate_id=near_duplicate.decision_id,
            detected_duplicate_code=near_duplicate.decision_code,
            similarity=near_duplicate.similarity,
            recommendation="SUPERSEDES",
            message=(
                f"This decision is {near_duplicate.similarity:.0%} similar to "
                f"{near_duplicate.decision_code or near_duplicate.decision_id}. "
                f"This appears to be an UPDATE of an existing decision. "
                f"Add 'supersedes: {near_duplicate.decision_id}' to indicate evolution."
            ),
            auto_populate={
                "supersedes": near_duplicate.decision_id,
                "supersedes_code": near_duplicate.decision_code
            }
        )
    else:
        # Different domain/aspect - suggest relation instead
        return SupersedesGuidance(
            detected_duplicate_id=near_duplicate.decision_id,
            detected_duplicate_code=near_duplicate.decision_code,
            similarity=near_duplicate.similarity,
            recommendation="RELATION",
            message=(
                f"This decision is {near_duplicate.similarity:.0%} similar to "
                f"{near_duplicate.decision_code or near_duplicate.decision_id} "
                f"but in a different category ({near_duplicate.domain_id}-{near_duplicate.aspect_id}). "
                f"Consider adding as 'informed_by' relation."
            ),
            auto_populate={
                "relations": [{
                    "target_id": near_duplicate.decision_id,
                    "target_code": near_duplicate.decision_code,
                    "type": "informed_by"
                }]
            }
        )


def detect_duplicates(
    record: Dict[str, Any],
    existing_decisions: List[Dict[str, Any]],
    check_same_feature_only: bool = False
) -> DuplicateDetectionResult:
    """
    Detect duplicates against existing decisions.

    Args:
        record: New decision record
        existing_decisions: List of existing decision dicts
        check_same_feature_only: If True, only check within same group/feature

    Returns:
        DuplicateDetectionResult with all matches and supersedes guidance
    """
    matches: List[DuplicateMatch] = []
    suggested_relations: List[str] = []
    supersedes_guidance: Optional[SupersedesGuidance] = None

    decision_id = record.get('decision_id', '')
    domain_id = record.get('domain_id', '')
    aspect_id = record.get('aspect_id', '')

    for existing in existing_decisions:
        # Skip self-comparison
        if existing.get('decision_id') == decision_id:
            continue

        # Skip if checking same aspect only
        if check_same_feature_only:
            if (existing.get('domain_id') != domain_id or
                existing.get('aspect_id') != aspect_id):
                continue

        # Check exact duplicate first
        exact_match = check_exact_duplicate(record, existing)
        if exact_match:
            matches.append(exact_match)
            continue

        # Check similarity-based duplicate
        sim_match = check_similarity_duplicate(record, existing)
        if sim_match:
            matches.append(sim_match)

            # Suggest as relation if RELATED level
            if sim_match.level == DuplicateLevel.RELATED:
                suggested_relations.append(existing.get('decision_id', ''))

    # Sort matches by similarity (highest first)
    matches.sort(key=lambda m: m.similarity, reverse=True)

    # Determine blocking status
    has_exact = any(m.level == DuplicateLevel.EXACT for m in matches)
    has_near = any(m.level == DuplicateLevel.NEAR for m in matches)

    # Generate supersedes guidance for the highest-similarity near-duplicate
    if has_near and not has_exact:
        # Find the highest similarity near-duplicate
        near_matches = [m for m in matches if m.level == DuplicateLevel.NEAR]
        if near_matches:
            highest_near = near_matches[0]  # Already sorted by similarity
            supersedes_guidance = suggest_supersedes(record, highest_near)

    return DuplicateDetectionResult(
        has_blocking_duplicate=has_exact,
        has_near_duplicate=has_near,
        matches=matches[:10],  # Limit to top 10 matches
        should_block=has_exact,
        requires_acknowledgment=has_near and not has_exact,
        suggested_relations=suggested_relations[:5],  # Limit suggestions
        supersedes_guidance=supersedes_guidance
    )


# =============================================================================
# Async Helper for Repository Integration
# =============================================================================

async def detect_duplicates_async(
    record: Dict[str, Any],
    repository
) -> DuplicateDetectionResult:
    """
    Async version that fetches existing decisions from repository.

    Args:
        record: Decision record to check
        repository: DecisionRepository instance

    Returns:
        DuplicateDetectionResult
    """
    # Fetch all decisions for duplicate check
    stored_decisions = await repository.find_all_async(limit=10000, offset=0)

    existing_decisions = [
        {
            'decision_id': sd.decision.decision_id,
            'decision_code': sd.decision.decision_code,
            'domain_id': sd.decision.domain_id.value,
            'aspect_id': sd.decision.aspect_id.value,
            'statement': sd.decision.statement,
        }
        for sd in stored_decisions
    ]

    return detect_duplicates(record, existing_decisions)
