"""
Enhanced Validation Use Case

Integrates 10 phases of validation (OPTIMIZED ORDER - fail-fast pattern):

1. Schema Validation (CHEAP) - fail fast on invalid structure
2. Exact Duplicate Check (CHEAP) - fast hash comparison, STOP if 100% match
3. Blocking Conflict Check (CHEAP) - STOP if critical conflict
4. Law Compliance (CHEAP) - governance check from schema validation
5. Quality Scoring (EXPENSIVE) - SBERT coherence, readability metrics
6. Semantic Duplicate Detection (reuses Quality embeddings)
7. Conflict Detection (full analysis)
8. Impact Analysis (graph-based)
9. AI Arbitration Detection (DELEGATED mode - returns context for client AI)
10. Metadata Inference (auto-suggest tags, tech_stack, blast_radius)

KEY OPTIMIZATION: Cheap checks run BEFORE expensive SBERT-based quality scoring.
This saves ~200ms for records that would be rejected anyway.

Produces comprehensive EnhancedValidationResponse with:
- result: READY | INVALID | BLOCKED
- quality: QualityAssessment
- duplicates: DuplicateDetectionResult
- conflicts: ConflictDetectionResult
- impact: ImpactAnalysisResult
- violations: List[Violation]
- warnings, advisory_notes, skipped_rules
- arbitration_contexts: For delegated AI arbitration
- metadata_suggestions: Auto-inferred metadata suggestions
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from .validate_decision import (
    DecisionValidator,
    ValidationResult,
    ValidationStatus,
    Violation,
    validate_related_decisions_integrity_async
)
from .quality_scoring import QualityAssessment, assess_quality, QualityGrade
from .duplicate_detection import (
    DuplicateDetectionResult,
    DuplicateMatch,
    DuplicateLevel,
    detect_duplicates,
    detect_duplicates_async,
    check_exact_duplicate,
    normalize_text
)
from .conflict_detection import (
    ConflictDetectionResult,
    ConflictMatch,
    ConflictSeverity,
    detect_conflicts,
    detect_conflicts_async
)
from .impact_analysis import (
    ImpactAnalysisResult,
    ImpactLevel,
    DependencyChain,
    AffectedDecision,
    analyze_impact,
    analyze_impact_async,
    serialize_impact_result
)
from .ai_arbiter import (
    ArbitrationMode,
    ArbitrationContext,
    ArbiterVerdict,
    ArbiterResult,
    QualityArbiter,
    DuplicateClassifier,
    ConflictArbiter,
)
from .metadata_inference import (
    InferredMetadata,
    infer_metadata,
    suggest_missing_metadata,
)
from ..domain.schema import AuthorshipMetadata


class EnhancedValidationStatus(str, Enum):
    """Enhanced validation result status."""
    READY = "READY"      # Can be stored
    INVALID = "INVALID"  # Has issues, can store with acknowledgment
    BLOCKED = "BLOCKED"  # Cannot be stored


@dataclass
class EnhancedValidationResponse:
    """
    Complete enhanced validation response.

    Includes all validation phases with detailed feedback.
    """
    # Overall result
    result: EnhancedValidationStatus
    proposal_id: str
    decision_id: str

    # Phase 2: Quality Assessment
    quality: QualityAssessment

    # Phase 3 & 4: Consistency Assessment
    duplicates: DuplicateDetectionResult
    conflicts: ConflictDetectionResult

    # Phase 6: Impact Analysis
    impact: ImpactAnalysisResult

    # Phase 1 & 5: Schema and Law Compliance
    schema_validation: ValidationResult
    violations: List[Violation]

    # Additional feedback
    warnings: List[str]
    advisory_notes: List[str]
    skipped_rules: List[str]

    # Metadata
    validated_at: datetime
    can_store: bool
    requires_acknowledgment: bool
    blocking_reasons: List[str]

    # AI Arbitration (Phase 9)
    arbitration_required: bool = False
    arbitration_contexts: Optional[List[ArbitrationContext]] = None
    ai_verdicts: Optional[Dict[str, ArbiterResult]] = None

    # Metadata Inference (Phase 10)
    metadata_suggestions: Optional[InferredMetadata] = None


def determine_result(
    schema_result: ValidationResult,
    quality: QualityAssessment,
    duplicates: DuplicateDetectionResult,
    conflicts: ConflictDetectionResult,
    relationship_valid: bool
) -> tuple[EnhancedValidationStatus, List[str], bool]:
    """
    Determine overall validation result.

    Returns:
        (status, blocking_reasons, requires_acknowledgment)
    """
    blocking_reasons = []
    requires_ack = False

    # Check schema violations
    if schema_result.status == ValidationStatus.INVALID:
        blocking_reasons.append("Schema validation failed")
    elif schema_result.status == ValidationStatus.REJECTED:
        blocking_reasons.append("Law compliance rejected")

    # Check quality
    if not quality.can_store:
        blocking_reasons.append(f"Quality score too low ({quality.overall_score}/100, grade: {quality.grade.value})")

    # Check duplicates
    if duplicates.should_block:
        blocking_reasons.append("Exact duplicate detected")
    elif duplicates.requires_acknowledgment:
        requires_ack = True

    # Check conflicts
    if conflicts.should_block:
        blocking_reasons.append("Critical conflict detected")
    elif conflicts.requires_review:
        requires_ack = True

    # Check relationships
    if not relationship_valid:
        blocking_reasons.append("Invalid relationship references")

    # Determine final status
    if blocking_reasons:
        return EnhancedValidationStatus.BLOCKED, blocking_reasons, False
    elif requires_ack:
        return EnhancedValidationStatus.INVALID, [], True
    else:
        return EnhancedValidationStatus.READY, [], False


def generate_warnings(
    quality: QualityAssessment,
    duplicates: DuplicateDetectionResult,
    conflicts: ConflictDetectionResult
) -> List[str]:
    """Generate warning messages."""
    warnings = []

    # Quality warnings
    if quality.grade == QualityGrade.FAIR:
        warnings.append(f"Decision quality is FAIR ({quality.overall_score}/100). Consider improvements.")
    elif quality.grade == QualityGrade.POOR:
        warnings.append(f"Decision quality is POOR ({quality.overall_score}/100). Significant improvement needed.")

    # Duplicate warnings
    near_dupes = [d for d in duplicates.matches if d.level == DuplicateLevel.NEAR]
    if near_dupes:
        warnings.append(f"Near duplicate detected: {near_dupes[0].decision_code or near_dupes[0].decision_id[:8]} ({near_dupes[0].similarity:.0%} similar)")

    semantic_dupes = [d for d in duplicates.matches if d.level == DuplicateLevel.SEMANTIC]
    if semantic_dupes:
        warnings.append(f"Semantically similar decision exists: {semantic_dupes[0].decision_code or semantic_dupes[0].decision_id[:8]}")

    # Conflict warnings
    warning_conflicts = [c for c in conflicts.conflicts if c.severity == ConflictSeverity.WARNING]
    for conflict in warning_conflicts[:2]:
        warnings.append(f"Potential conflict with {conflict.decision_code or conflict.decision_id[:8]}: {conflict.description}")

    return warnings


def generate_advisory_notes(
    quality: QualityAssessment,
    duplicates: DuplicateDetectionResult,
    conflicts: ConflictDetectionResult,
    skipped_rules: List[str]
) -> List[str]:
    """Generate advisory notes."""
    notes = []

    # Quality suggestions
    if quality.improvement_suggestions:
        notes.append(f"Quality improvement suggestions: {'; '.join(quality.improvement_suggestions[:3])}")

    # Supersedes guidance (Phase 6: Auto-Supersedes Detection)
    if duplicates.supersedes_guidance:
        sg = duplicates.supersedes_guidance
        if sg.recommendation == "SUPERSEDES":
            notes.append(
                f"Supersedes suggestion: This appears to be an update of "
                f"{sg.detected_duplicate_code or sg.detected_duplicate_id}. "
                f"Consider adding 'supersedes' field."
            )
        else:
            notes.append(
                f"Relation suggestion: Similar to {sg.detected_duplicate_code or sg.detected_duplicate_id}. "
                f"Consider adding as 'informed_by' relation."
            )

    # Suggested relations
    if duplicates.suggested_relations:
        notes.append(f"Consider adding relations to: {', '.join(duplicates.suggested_relations[:3])}")

    # Conflict resolution
    if conflicts.resolution_suggestions:
        notes.extend(conflicts.resolution_suggestions[:2])

    # Skipped rules note
    if skipped_rules:
        notes.append(f"Validation rules {', '.join(skipped_rules[:5])} were skipped due to missing metadata")

    return notes


# =============================================================================
# AI Arbitration Detection (Phase 9)
# =============================================================================

def detect_arbitration_needs(
    quality: QualityAssessment,
    duplicates: DuplicateDetectionResult,
    conflicts: ConflictDetectionResult,
    record: Dict[str, Any]
) -> tuple[bool, List[ArbitrationContext]]:
    """
    Detect if AI arbitration is needed and generate contexts.

    This function checks all validation results for ambiguous cases
    that would benefit from AI judgment.

    Args:
        quality: Quality assessment result
        duplicates: Duplicate detection result
        conflicts: Conflict detection result
        record: Original decision record

    Returns:
        (arbitration_required, arbitration_contexts)
    """
    contexts = []

    # Quality Arbitration (borderline scores 50-80)
    quality_arbiter = QualityArbiter()
    quality_context = {
        'quality_score': quality.overall_score,
        'statement': record.get('statement', ''),
        'rationale': record.get('rationale', ''),
        'statement_score': quality.statement_score,
        'rationale_score': quality.rationale_score,
        'suggestions': quality.improvement_suggestions,
        'coherence_score': quality.coherence_score,
        'readability': quality.readability,
    }
    if quality_arbiter.should_invoke(quality_context):
        contexts.append(quality_arbiter.generate_context(quality_context))

    # Duplicate Classification (near-duplicates 85-95%)
    if duplicates.has_near_duplicate and duplicates.matches:
        dup_classifier = DuplicateClassifier()
        highest_match = duplicates.matches[0]  # Already sorted by similarity
        dup_context = {
            'max_similarity': highest_match.similarity,
            'new_statement': record.get('statement', ''),
            'group_id': record.get('group_id', ''),
            'feature_id': record.get('feature_id', ''),
            'existing_id': highest_match.decision_id,
            'existing_code': highest_match.decision_code,
            'existing_statement': highest_match.statement_preview,
            'existing_created_at': 'Unknown',  # Would need to fetch from DB
            'similarity': highest_match.similarity,
            'same_cell': (
                record.get('group_id') == highest_match.group_id and
                record.get('feature_id') == highest_match.feature_id
            ),
        }
        if dup_classifier.should_invoke(dup_context):
            contexts.append(dup_classifier.generate_context(dup_context))

    # Conflict Arbitration (medium-severity conflicts)
    conflict_arbiter = ConflictArbiter()
    medium_conflicts = [c for c in conflicts.conflicts if c.severity.value == 'MEDIUM']
    if medium_conflicts:
        # Generate context for the most significant medium conflict
        first_conflict = medium_conflicts[0]
        conflict_context = {
            'conflicts': [{'severity': c.severity.value} for c in conflicts.conflicts],
            'new_statement': record.get('statement', ''),
            'new_rationale': record.get('rationale', ''),
            'conflict': {
                'code': first_conflict.decision_code,
                'statement': first_conflict.statement_preview,
                'group_id': first_conflict.group_id,
                'feature_id': first_conflict.feature_id,
                'type': first_conflict.conflict_type.value,
                'description': first_conflict.description,
                'keywords': first_conflict.conflicting_keywords,
            },
        }
        if conflict_arbiter.should_invoke(conflict_context):
            contexts.append(conflict_arbiter.generate_context(conflict_context))

    return len(contexts) > 0, contexts if contexts else None


# =============================================================================
# Fast Pre-Checks (Run BEFORE expensive SBERT operations)
# =============================================================================

def fast_exact_duplicate_check(
    record: Dict[str, Any],
    existing_decisions: List[Dict[str, Any]]
) -> Optional[DuplicateMatch]:
    """
    FAST exact duplicate check - runs BEFORE quality scoring.

    This saves ~200ms SBERT inference if exact duplicate is found.
    Only checks for 100% match (same group + feature + normalized statement).

    Returns:
        DuplicateMatch if exact duplicate found, None otherwise.
    """
    decision_id = record.get('decision_id', '')

    for existing in existing_decisions:
        # Skip self-comparison
        if existing.get('decision_id') == decision_id:
            continue

        # Use imported check_exact_duplicate from duplicate_detection
        exact_match = check_exact_duplicate(record, existing)
        if exact_match:
            return exact_match

    return None


def fast_blocking_conflict_check(
    record: Dict[str, Any],
    existing_decisions: List[Dict[str, Any]]
) -> Optional[str]:
    """
    FAST blocking conflict check - runs BEFORE quality scoring.

    Checks for critical conflicts that would block storage anyway.
    Only checks if new decision explicitly supersedes an active decision
    without proper status handling.

    Returns:
        Blocking reason string if critical conflict, None otherwise.
    """
    supersedes_id = record.get('supersedes')
    if not supersedes_id:
        return None

    # Check if superseded decision exists
    superseded = None
    for existing in existing_decisions:
        if existing.get('decision_id') == supersedes_id:
            superseded = existing
            break

    if superseded is None:
        return f"Supersedes references non-existent decision: {supersedes_id}"

    # Check if trying to supersede a decision in different group/feature
    # This would be a critical conflict
    if (record.get('group_id') != superseded.get('group_id') or
        record.get('feature_id') != superseded.get('feature_id')):
        return (
            f"Cannot supersede decision from different category. "
            f"New: {record.get('group_id')}-{record.get('feature_id')}, "
            f"Target: {superseded.get('group_id')}-{superseded.get('feature_id')}"
        )

    return None


# =============================================================================
# Main Enhanced Validation Function
# =============================================================================

def validate_enhanced(
    record: Dict[str, Any],
    existing_decisions: List[Dict[str, Any]],
    authorship_metadata: Optional[AuthorshipMetadata] = None,
    proposal_id: Optional[str] = None,
    client_verdicts: Optional[List[Dict[str, Any]]] = None,
) -> EnhancedValidationResponse:
    """
    Perform enhanced validation with OPTIMIZED phase order.

    OPTIMIZATION: Cheap checks run BEFORE expensive SBERT operations.
    This saves ~200ms for records that would be rejected anyway.

    Phase Order (fail-fast):
    1. Schema Validation (CHEAP)
    2. Fast Exact Duplicate (CHEAP) - STOP if found
    3. Fast Blocking Conflict (CHEAP) - STOP if found
    4. Quality Scoring (EXPENSIVE - SBERT)
    5. Full Duplicate Detection
    6. Full Conflict Detection
    7. Relationship Integrity
    8. Impact Analysis

    Args:
        record: Decision record dictionary
        existing_decisions: List of existing decision dicts for comparison
        authorship_metadata: Optional authorship info for L-rules
        proposal_id: Optional proposal ID (generated if not provided)
        client_verdicts: Optional client AI verdicts for delegated arbitration

    Returns:
        EnhancedValidationResponse with comprehensive feedback
    """
    import uuid

    # Generate IDs
    if not proposal_id:
        proposal_id = str(uuid.uuid4())
    decision_id = record.get('decision_id', str(uuid.uuid4()))

    # Inject decision_id into record for validation (if not provided)
    if 'decision_id' not in record:
        record['decision_id'] = decision_id

    # =========================================================================
    # PHASE 1: Schema Validation (CHEAP - ~1ms)
    # =========================================================================
    validator = DecisionValidator()
    schema_result = validator.validate(record, authorship_metadata)

    # FAST EXIT: If schema is completely invalid, no need to continue
    if schema_result.status == ValidationStatus.INVALID:
        # Return minimal response - skip expensive operations
        return _create_early_exit_response(
            proposal_id=proposal_id,
            decision_id=decision_id,
            schema_result=schema_result,
            blocking_reason="Schema validation failed",
            validated_at=datetime.utcnow()
        )

    # =========================================================================
    # PHASE 2: Fast Exact Duplicate Check (CHEAP - ~5ms)
    # =========================================================================
    exact_dup = fast_exact_duplicate_check(record, existing_decisions)
    if exact_dup:
        # Return minimal response - skip expensive SBERT operations
        return _create_early_exit_response(
            proposal_id=proposal_id,
            decision_id=decision_id,
            schema_result=schema_result,
            blocking_reason=f"Exact duplicate of {exact_dup.decision_code or exact_dup.decision_id[:8]}",
            validated_at=datetime.utcnow(),
            exact_duplicate=exact_dup
        )

    # =========================================================================
    # PHASE 3: Fast Blocking Conflict Check (CHEAP - ~2ms)
    # =========================================================================
    blocking_conflict = fast_blocking_conflict_check(record, existing_decisions)
    if blocking_conflict:
        return _create_early_exit_response(
            proposal_id=proposal_id,
            decision_id=decision_id,
            schema_result=schema_result,
            blocking_reason=blocking_conflict,
            validated_at=datetime.utcnow()
        )

    # =========================================================================
    # PHASE 4: Quality Scoring (EXPENSIVE - SBERT ~200ms)
    # Only runs if record passed cheap pre-checks
    # =========================================================================
    quality = assess_quality(record)

    # =========================================================================
    # PHASE 5: Full Duplicate Detection
    # =========================================================================
    duplicates = detect_duplicates(record, existing_decisions)

    # =========================================================================
    # PHASE 6: Full Conflict Detection
    # =========================================================================
    conflicts = detect_conflicts(record, existing_decisions)

    # =========================================================================
    # PHASE 7: Relationship Integrity
    # =========================================================================
    relationship_result = validate_related_decisions_integrity(
        record, existing_decisions
    ) if existing_decisions else None
    relationship_valid = relationship_result.is_valid if relationship_result else True

    # =========================================================================
    # PHASE 8: Impact Analysis
    # =========================================================================
    impact = analyze_impact(record, existing_decisions)

    # Determine overall result
    result, blocking_reasons, requires_ack = determine_result(
        schema_result, quality, duplicates, conflicts, relationship_valid
    )

    # Generate feedback
    warnings = generate_warnings(quality, duplicates, conflicts)
    advisory_notes = generate_advisory_notes(
        quality, duplicates, conflicts, schema_result.skipped_rules
    )

    # Add relationship advisories
    if relationship_result and relationship_result.advisory_notes:
        advisory_notes.extend(relationship_result.advisory_notes)

    # Add impact warnings and recommendations
    if impact.risk_factors:
        warnings.extend([f"Impact: {rf}" for rf in impact.risk_factors[:3]])
    if impact.recommendations:
        advisory_notes.extend([f"Impact: {r}" for r in impact.recommendations[:3]])

    # =========================================================================
    # PHASE 9: AI Arbitration Detection
    # Detect if any validation results need AI judgment (DELEGATED mode)
    # =========================================================================
    arbitration_required, arbitration_contexts = detect_arbitration_needs(
        quality, duplicates, conflicts, record
    )

    # =========================================================================
    # PHASE 10: Metadata Inference
    # Auto-suggest tags, tech_stack, blast_radius from statement/rationale text
    # Helps with bootstrap problem: users can score well even without metadata
    # =========================================================================
    metadata_suggestions = infer_metadata(
        statement=record.get('statement', ''),
        rationale=record.get('rationale', '')
    )

    # Add missing metadata suggestions to advisory notes
    missing_metadata_notes = suggest_missing_metadata(record, metadata_suggestions)
    if missing_metadata_notes:
        advisory_notes.extend(missing_metadata_notes)

    # =========================================================================
    # PHASE 11: Apply Client Verdicts (if provided)
    # In DELEGATED mode, client AI submits verdicts for arbitration.
    # These verdicts override the borderline decisions.
    # =========================================================================
    ai_verdicts = None
    if client_verdicts:
        ai_verdicts = {}
        for cv in client_verdicts:
            arb_type = cv.get('arbitration_type', '').upper()
            verdict = cv.get('verdict', '').upper()
            ai_verdicts[arb_type] = {
                'verdict': verdict,
                'confidence': cv.get('confidence', 0.5),
                'reason': cv.get('reason', ''),
                'suggestions': cv.get('suggestions', []),
                'source': 'CLIENT_AI',
            }

            # Apply verdict effects
            if arb_type == 'QUALITY':
                if verdict == 'APPROVE':
                    # Client approved borderline quality → allow storage
                    if result == EnhancedValidationStatus.INVALID:
                        result = EnhancedValidationStatus.READY
                    advisory_notes.append(f"Quality approved by client AI: {cv.get('reason', 'No reason given')}")
                elif verdict == 'REJECT':
                    # Client rejected → block storage
                    result = EnhancedValidationStatus.BLOCKED
                    blocking_reasons.append(f"Rejected by client AI: {cv.get('reason', 'No reason given')}")
                elif verdict == 'NEEDS_IMPROVEMENT':
                    # Needs improvement → stay INVALID, add suggestions
                    if result == EnhancedValidationStatus.READY:
                        result = EnhancedValidationStatus.INVALID
                    warnings.extend(cv.get('suggestions', []))

            elif arb_type == 'DUPLICATE':
                if verdict == 'DUPLICATE':
                    # Confirmed duplicate → block
                    result = EnhancedValidationStatus.BLOCKED
                    blocking_reasons.append(f"Confirmed duplicate by client AI: {cv.get('reason', '')}")
                elif verdict == 'EVOLUTION':
                    # Evolution → suggest supersedes, allow
                    advisory_notes.append(f"Client AI: This is an evolution. Consider adding supersedes relation.")
                elif verdict == 'DIFFERENT':
                    # Different → allow, suggest relation
                    advisory_notes.append(f"Client AI: Similar but different. Consider adding informed_by relation.")

            elif arb_type == 'CONFLICT':
                if verdict == 'BLOCKING':
                    # Real conflict → block
                    result = EnhancedValidationStatus.BLOCKED
                    blocking_reasons.append(f"Conflict confirmed by client AI: {cv.get('reason', '')}")
                elif verdict == 'WARNING':
                    # Warning → allow with caution
                    warnings.append(f"Potential conflict (client AI): {cv.get('reason', '')}")
                elif verdict == 'NOT_CONFLICT':
                    # False positive → clear it
                    advisory_notes.append(f"Conflict dismissed by client AI: {cv.get('reason', '')}")

        # If client provided verdicts, arbitration is resolved
        arbitration_required = False
        arbitration_contexts = None

    return EnhancedValidationResponse(
        result=result,
        proposal_id=proposal_id,
        decision_id=decision_id,
        quality=quality,
        duplicates=duplicates,
        conflicts=conflicts,
        impact=impact,
        schema_validation=schema_result,
        violations=schema_result.violations,
        warnings=warnings,
        advisory_notes=advisory_notes,
        skipped_rules=schema_result.skipped_rules,
        validated_at=datetime.utcnow(),
        can_store=result != EnhancedValidationStatus.BLOCKED,
        requires_acknowledgment=requires_ack,
        blocking_reasons=blocking_reasons,
        # AI Arbitration (Phase 9)
        arbitration_required=arbitration_required,
        arbitration_contexts=arbitration_contexts,
        ai_verdicts=ai_verdicts,
        # Metadata Inference (Phase 10)
        metadata_suggestions=metadata_suggestions,
    )


def _create_early_exit_response(
    proposal_id: str,
    decision_id: str,
    schema_result: ValidationResult,
    blocking_reason: str,
    validated_at: datetime,
    exact_duplicate: Optional[DuplicateMatch] = None
) -> EnhancedValidationResponse:
    """
    Create minimal response for early exit (failed pre-checks).

    This avoids running expensive SBERT operations when record
    would be rejected anyway.
    """
    # Create minimal quality assessment
    minimal_quality = QualityAssessment(
        overall_score=0,
        grade=QualityGrade.POOR,
        statement_score=0,
        rationale_score=0,
        constraint_score=0,
        metadata_score=0,
        advanced_score=0,
        dimensions=[],
        improvement_suggestions=["Record blocked before quality assessment"],
        can_store=False,
        readability=None,
        coherence_score=None,
        objectivity_issues=[]
    )

    # Create minimal duplicate result
    if exact_duplicate:
        minimal_duplicates = DuplicateDetectionResult(
            has_blocking_duplicate=True,
            has_near_duplicate=False,
            matches=[exact_duplicate],
            should_block=True,
            requires_acknowledgment=False,
            suggested_relations=[]
        )
    else:
        minimal_duplicates = DuplicateDetectionResult(
            has_blocking_duplicate=False,
            has_near_duplicate=False,
            matches=[],
            should_block=False,
            requires_acknowledgment=False,
            suggested_relations=[]
        )

    # Create minimal conflict result
    minimal_conflicts = ConflictDetectionResult(
        has_blocking_conflict=blocking_reason.startswith("Cannot supersede"),
        has_warning_conflict=False,
        conflicts=[],
        should_block=blocking_reason.startswith("Cannot supersede"),
        requires_review=False,
        resolution_suggestions=[]
    )

    # Create minimal impact result
    minimal_impact = ImpactAnalysisResult(
        overall_risk=ImpactLevel.MINIMAL,
        risk_score=0,
        affected_decisions=[],
        affected_count=0,
        dependency_chains=[],
        reverse_dependencies=[],
        max_dependency_depth=0,
        breaking_changes=[],
        has_breaking_changes=False,
        affected_areas=[],
        affected_tech_stack=[],
        blast_radius_accurate=True,
        blast_radius_warning=None,
        risk_factors=[],
        recommendations=["Record blocked before impact analysis"],
        summary="Validation terminated early - record blocked"
    )

    return EnhancedValidationResponse(
        result=EnhancedValidationStatus.BLOCKED,
        proposal_id=proposal_id,
        decision_id=decision_id,
        quality=minimal_quality,
        duplicates=minimal_duplicates,
        conflicts=minimal_conflicts,
        impact=minimal_impact,
        schema_validation=schema_result,
        violations=schema_result.violations,
        warnings=[],
        advisory_notes=[f"Early exit: {blocking_reason}"],
        skipped_rules=schema_result.skipped_rules,
        validated_at=validated_at,
        can_store=False,
        requires_acknowledgment=False,
        blocking_reasons=[blocking_reason]
    )


# Import for relationship validation
from .validate_decision import validate_related_decisions_integrity


# =============================================================================
# Async Version for Repository Integration
# =============================================================================

async def validate_enhanced_async(
    record: Dict[str, Any],
    repository,
    authorship_metadata: Optional[AuthorshipMetadata] = None,
    proposal_id: Optional[str] = None,
    client_verdicts: Optional[List[Dict[str, Any]]] = None,
    arbitration_mode: str = "DELEGATED",
) -> EnhancedValidationResponse:
    """
    Async version that fetches existing decisions from repository.

    Args:
        record: Decision record dictionary
        repository: DecisionRepository instance
        authorship_metadata: Optional authorship info
        proposal_id: Optional proposal ID
        client_verdicts: Optional list of client AI verdicts for delegated arbitration
        arbitration_mode: "SERVER" | "DELEGATED" | "SKIP"
            - SERVER: MANTRA's AI performs arbitration (costs $)
            - DELEGATED: Returns context for client AI to arbitrate
            - SKIP: No AI arbitration

    Returns:
        EnhancedValidationResponse
    """
    import uuid

    # Generate IDs
    if not proposal_id:
        proposal_id = str(uuid.uuid4())
    decision_id = record.get('decision_id', str(uuid.uuid4()))

    # Inject decision_id into record for validation (if not provided)
    if 'decision_id' not in record:
        record['decision_id'] = decision_id

    # Fetch existing decisions
    stored_decisions = await repository.find_all_async(limit=10000, offset=0)
    existing_decisions = [
        {
            'decision_id': sd.decision.decision_id,
            'decision_code': sd.decision.decision_code,
            'group_id': sd.decision.group_id.value,
            'feature_id': sd.decision.feature_id.value,
            'statement': sd.decision.statement,
            'scope': sd.decision.scope.value,
            'supersedes': sd.decision.supersedes,
            'related_decisions': sd.decision.related_decisions,
        }
        for sd in stored_decisions
    ]

    # Run validation (sync version - handles most logic)
    result = validate_enhanced(
        record, existing_decisions, authorship_metadata, proposal_id, client_verdicts
    )

    # ==========================================================================
    # SERVER MODE: Perform AI arbitration if needed
    # Only called when arbitration_required=True and mode is SERVER
    # ==========================================================================
    if arbitration_mode == "SERVER" and result.arbitration_required and result.arbitration_contexts:
        result = await _perform_server_arbitration(result, record)
    elif arbitration_mode == "SKIP":
        # Clear arbitration fields - no AI involvement
        result.arbitration_required = False
        result.arbitration_contexts = None

    return result


async def _perform_server_arbitration(
    result: EnhancedValidationResponse,
    record: Dict[str, Any]
) -> EnhancedValidationResponse:
    """
    Perform server-side AI arbitration.

    Called when arbitration_mode is SERVER and arbitration is needed.
    Uses the configured AI provider (Anthropic, OpenAI, DeepSeek, Groq, xAI, OpenRouter).

    Args:
        result: Current validation result with arbitration_contexts
        record: Original decision record

    Returns:
        Updated EnhancedValidationResponse with AI verdicts applied
    """
    from .ai_arbiter import (
        get_ai_client,
        QualityArbiter,
        DuplicateClassifier,
        ConflictArbiter,
        ArbiterResult,
        ArbiterVerdict,
    )

    ai_client = get_ai_client()
    if not ai_client.is_configured:
        # AI not configured - fall back to quick judgment or keep as-is
        result.advisory_notes.append(
            "Server-side AI arbitration requested but not configured. "
            "Set AI_API_KEY or provider-specific key."
        )
        return result

    ai_verdicts = {}

    for ctx in result.arbitration_contexts:
        arb_type = ctx.arbitration_type.value if hasattr(ctx.arbitration_type, 'value') else ctx.arbitration_type

        try:
            # Call AI with the prompt from context
            response = await ai_client.complete(ctx.prompt_template)
            parsed = ai_client.parse_json_response(response)

            verdict = parsed.get('verdict', 'NEEDS_IMPROVEMENT')
            confidence = float(parsed.get('confidence', 0.7))
            reason = parsed.get('reason', 'AI evaluation complete')
            suggestions = parsed.get('suggestions', [])

            ai_verdicts[arb_type] = {
                'verdict': verdict,
                'confidence': confidence,
                'reason': reason,
                'suggestions': suggestions,
                'source': 'SERVER_AI',
                'provider': ai_client.provider_name,
            }

            # Apply verdict effects
            if arb_type == 'QUALITY':
                if verdict == 'APPROVE':
                    if result.result == EnhancedValidationStatus.INVALID:
                        result.result = EnhancedValidationStatus.READY
                    result.advisory_notes.append(f"Quality approved by AI: {reason}")
                elif verdict == 'REJECT':
                    result.result = EnhancedValidationStatus.BLOCKED
                    result.blocking_reasons.append(f"Rejected by AI: {reason}")
                elif verdict == 'NEEDS_IMPROVEMENT':
                    if result.result == EnhancedValidationStatus.READY:
                        result.result = EnhancedValidationStatus.INVALID
                    result.warnings.extend(suggestions)

            elif arb_type == 'DUPLICATE':
                if verdict == 'DUPLICATE':
                    result.result = EnhancedValidationStatus.BLOCKED
                    result.blocking_reasons.append(f"Confirmed duplicate by AI: {reason}")
                elif verdict == 'EVOLUTION':
                    result.advisory_notes.append(f"AI: This is an evolution. Add supersedes relation.")
                elif verdict == 'DIFFERENT':
                    result.advisory_notes.append(f"AI: Similar but different. Consider informed_by relation.")

            elif arb_type == 'CONFLICT':
                if verdict == 'BLOCKING':
                    result.result = EnhancedValidationStatus.BLOCKED
                    result.blocking_reasons.append(f"Conflict confirmed by AI: {reason}")
                elif verdict == 'WARNING':
                    result.warnings.append(f"Potential conflict (AI): {reason}")
                elif verdict == 'NOT_CONFLICT':
                    result.advisory_notes.append(f"Conflict dismissed by AI: {reason}")

        except Exception as e:
            # AI call failed - record error but don't block
            ai_verdicts[arb_type] = {
                'verdict': 'ERROR',
                'confidence': 0,
                'reason': f"AI arbitration failed: {str(e)}",
                'suggestions': [],
                'source': 'SERVER_AI',
            }
            result.advisory_notes.append(f"AI arbitration for {arb_type} failed: {str(e)}")

    # Update result with AI verdicts
    result.ai_verdicts = ai_verdicts
    result.arbitration_required = False  # Resolved by server AI
    result.arbitration_contexts = None  # No longer needed

    # Update can_store based on final result
    result.can_store = result.result != EnhancedValidationStatus.BLOCKED

    return result


# =============================================================================
# Response Serialization Helpers
# =============================================================================

def serialize_quality_assessment(quality: QualityAssessment) -> Dict[str, Any]:
    """Serialize QualityAssessment to dict."""
    return {
        'overall_score': quality.overall_score,
        'grade': quality.grade.value,
        'statement_score': quality.statement_score,
        'rationale_score': quality.rationale_score,
        'constraint_score': quality.constraint_score,
        'metadata_score': quality.metadata_score,
        'advanced_score': quality.advanced_score,  # Q-021 to Q-025
        'improvement_suggestions': quality.improvement_suggestions,
        'can_store': quality.can_store,
        'dimensions': [
            {
                'dimension': d.dimension,
                'score': d.score,
                'max_score': d.max_score,
                'rules_passed': d.rules_passed,
                'rules_failed': d.rules_failed,
                'suggestions': d.suggestions,
            }
            for d in quality.dimensions
        ],
        # Advanced metrics for transparency
        'readability': quality.readability,  # Flesch-Kincaid, Gunning Fog, etc.
        'coherence_score': quality.coherence_score,  # Statement-rationale coherence (0-1)
        'objectivity_issues': quality.objectivity_issues,  # Detected cognitive biases
    }


def serialize_duplicate_result(duplicates: DuplicateDetectionResult) -> Dict[str, Any]:
    """Serialize DuplicateDetectionResult to dict."""
    result = {
        'has_blocking_duplicate': duplicates.has_blocking_duplicate,
        'has_near_duplicate': duplicates.has_near_duplicate,
        'should_block': duplicates.should_block,
        'requires_acknowledgment': duplicates.requires_acknowledgment,
        'suggested_relations': duplicates.suggested_relations,
        'matches': [
            {
                'decision_id': m.decision_id,
                'decision_code': m.decision_code,
                'group_id': m.group_id,
                'feature_id': m.feature_id,
                'statement_preview': m.statement_preview,
                'similarity': m.similarity,
                'level': m.level.value,
                'reason': m.reason,
            }
            for m in duplicates.matches
        ]
    }

    # Add supersedes guidance if available (Phase 6: Auto-Supersedes Detection)
    if duplicates.supersedes_guidance:
        sg = duplicates.supersedes_guidance
        result['supersedes_guidance'] = {
            'detected_duplicate_id': sg.detected_duplicate_id,
            'detected_duplicate_code': sg.detected_duplicate_code,
            'similarity': sg.similarity,
            'recommendation': sg.recommendation,
            'message': sg.message,
            'auto_populate': sg.auto_populate,
        }

    return result


def serialize_conflict_result(conflicts: ConflictDetectionResult) -> Dict[str, Any]:
    """Serialize ConflictDetectionResult to dict."""
    return {
        'has_blocking_conflict': conflicts.has_blocking_conflict,
        'has_warning_conflict': conflicts.has_warning_conflict,
        'should_block': conflicts.should_block,
        'requires_review': conflicts.requires_review,
        'resolution_suggestions': conflicts.resolution_suggestions,
        'conflicts': [
            {
                'decision_id': c.decision_id,
                'decision_code': c.decision_code,
                'group_id': c.group_id,
                'feature_id': c.feature_id,
                'statement_preview': c.statement_preview,
                'conflict_type': c.conflict_type.value,
                'severity': c.severity.value,
                'description': c.description,
                'conflicting_keywords': c.conflicting_keywords,
            }
            for c in conflicts.conflicts
        ]
    }


def serialize_enhanced_response(response: EnhancedValidationResponse) -> Dict[str, Any]:
    """Serialize full EnhancedValidationResponse to dict."""
    result = {
        'result': response.result.value,
        'proposal_id': response.proposal_id,
        'decision_id': response.decision_id,
        'quality': serialize_quality_assessment(response.quality),
        'duplicates': serialize_duplicate_result(response.duplicates),
        'conflicts': serialize_conflict_result(response.conflicts),
        'impact': serialize_impact_result(response.impact),
        'violations': [
            {
                'rule_id': v.rule_id,
                'level': v.level.value,
                'message': v.message,
                'field': v.field,
                'failure_result': v.failure_result.value,
                'governing_reference': v.governing_reference,
            }
            for v in response.violations
        ],
        'warnings': response.warnings,
        'advisory_notes': response.advisory_notes,
        'skipped_rules': response.skipped_rules,
        'validated_at': response.validated_at.isoformat(),
        'can_store': response.can_store,
        'requires_acknowledgment': response.requires_acknowledgment,
        'blocking_reasons': response.blocking_reasons,
    }

    # Add AI Arbitration fields (Phase 9)
    result['arbitration_required'] = response.arbitration_required
    if response.arbitration_contexts:
        result['arbitration_contexts'] = [
            ctx.to_dict() for ctx in response.arbitration_contexts
        ]
    if response.ai_verdicts:
        # Handle both dict (from client) and ArbiterResult (from server) formats
        result['ai_verdicts'] = {}
        for arb_type, v in response.ai_verdicts.items():
            if isinstance(v, dict):
                # Already a dict (from client verdicts)
                result['ai_verdicts'][arb_type] = v
            else:
                # ArbiterResult object (from server arbitration)
                result['ai_verdicts'][arb_type] = {
                    'verdict': v.verdict.value if hasattr(v.verdict, 'value') else v.verdict,
                    'confidence': v.confidence,
                    'reason': v.reason,
                    'suggestions': v.suggestions,
                }

    # Add Metadata Inference fields (Phase 10)
    if response.metadata_suggestions:
        result['metadata_suggestions'] = response.metadata_suggestions.to_dict()

    # Add User Approval Flow fields
    result['requires_user_approval'] = True  # Always require user approval
    result['approval_summary'] = generate_approval_summary(response)

    return result


# =============================================================================
# User Approval Flow
# =============================================================================

def generate_approval_summary(response: EnhancedValidationResponse) -> Dict[str, Any]:
    """
    Generate a human-readable summary for user approval.

    This summary helps users understand:
    - What the decision is about
    - Quality assessment
    - Any issues or warnings
    - What happens if they approve

    Returns:
        Dict with approval summary
    """
    # Build action items based on result
    action_items = []
    if response.blocking_reasons:
        action_items.append({
            'type': 'BLOCKER',
            'message': 'This decision cannot be stored due to blocking issues.',
            'details': response.blocking_reasons,
        })

    if response.requires_acknowledgment:
        action_items.append({
            'type': 'ACKNOWLEDGE',
            'message': 'This decision requires acknowledgment of potential issues.',
            'details': response.warnings[:3] if response.warnings else [],
        })

    if response.ai_verdicts:
        for arb_type, verdict in response.ai_verdicts.items():
            v_dict = verdict if isinstance(verdict, dict) else {
                'verdict': verdict.verdict.value if hasattr(verdict.verdict, 'value') else verdict.verdict,
                'reason': verdict.reason,
            }
            action_items.append({
                'type': 'AI_VERDICT',
                'category': arb_type,
                'verdict': v_dict.get('verdict'),
                'reason': v_dict.get('reason'),
            })

    # Quality summary
    quality_summary = {
        'score': response.quality.overall_score,
        'grade': response.quality.grade.value,
        'can_improve': len(response.quality.improvement_suggestions) > 0,
        'top_suggestions': response.quality.improvement_suggestions[:3],
    }

    # Risk summary
    risk_summary = {
        'level': response.impact.overall_risk.value,
        'score': response.impact.risk_score,
        'affected_count': response.impact.affected_count,
        'has_breaking_changes': response.impact.has_breaking_changes,
    }

    # Consistency summary
    consistency_summary = {
        'has_duplicates': response.duplicates.has_blocking_duplicate or response.duplicates.has_near_duplicate,
        'has_conflicts': response.conflicts.has_blocking_conflict or response.conflicts.has_warning_conflict,
        'duplicate_count': len(response.duplicates.matches),
        'conflict_count': len(response.conflicts.conflicts),
    }

    return {
        'proposal_id': response.proposal_id,
        'decision_id': response.decision_id,
        'result': response.result.value,
        'can_approve': response.can_store,
        'quality': quality_summary,
        'risk': risk_summary,
        'consistency': consistency_summary,
        'action_items': action_items,
        'warnings_count': len(response.warnings),
        'advisory_count': len(response.advisory_notes),
        'approval_message': _get_approval_message(response),
    }


def _get_approval_message(response: EnhancedValidationResponse) -> str:
    """Generate approval message based on result."""
    if response.result == EnhancedValidationStatus.BLOCKED:
        return "This decision CANNOT be approved. Please fix the blocking issues first."
    elif response.result == EnhancedValidationStatus.INVALID:
        return "This decision has issues. You can still approve, but please acknowledge the warnings."
    else:
        return "This decision is ready for approval. Click approve to store it permanently."
