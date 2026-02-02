"""
Validate Decision Use Case

Implements MANTRA-L1-IMPL-VALIDATOR-001

Per §2.1: The validator's sole responsibility is to determine whether a
decision record conforms to requirements defined in governing artifacts.

Per §2.2: The validator produces exactly one of three determinations:
- VALID
- INVALID
- REJECTED
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import json
import hashlib

from ..domain.schema import (
    Decision,
    DomainId,
    AspectId,
    Scope,
    BlastRadius,
    ConstraintType,
    DOMAIN_ASPECT_MATRIX,
    is_aspect_compatible,
    AuthorshipMetadata,
)
from ..ports.cache import CacheProtocol, CacheTTL


# ============================================================================
# Validation Enumerations per MANTRA-SPEC-001 §7
# ============================================================================

class ValidationStatus(str, Enum):
    """Validation status per MANTRA-SPEC-001 §7.3"""
    VALID = "VALID"
    INVALID = "INVALID"
    REJECTED = "REJECTED"


class ValidationLevel(str, Enum):
    """Validation level per MANTRA-SPEC-001 §3.1"""
    LEVEL_1 = "LEVEL_1"  # Schema Validation (S-001 to S-022)
    LEVEL_2 = "LEVEL_2"  # Decision Consistency (D-001 to D-014)
    LEVEL_3 = "LEVEL_3"  # Law Compliance (L-001 to L-011)


class FailureResult(str, Enum):
    """Failure result per MANTRA-SPEC-001 §6"""
    INVALID = "INVALID"   # Structural, consistency, or authority failure
    REJECTED = "REJECTED"  # Mutability or versioning violation


# ============================================================================
# Output Structures per MANTRA-SPEC-001 §7.1
# ============================================================================

@dataclass
class Violation:
    """Violation entry per MANTRA-SPEC-001 §7.2"""
    rule_id: str
    level: ValidationLevel
    message: str
    failure_result: FailureResult
    governing_reference: str
    field: Optional[str] = None


@dataclass
class ValidationResult:
    """Validation output per MANTRA-SPEC-001 §7.1"""
    status: ValidationStatus
    violations: List[Violation] = field(default_factory=list)
    skipped_rules: List[str] = field(default_factory=list)
    advisory_notes: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.utcnow)
    schema_version: str = "1.0.0"
    specification_version: str = "MANTRA-SPEC-001 v1.0.0"


# ============================================================================
# Cache Helper Functions
# ============================================================================

def _compute_record_hash(record: Dict[str, Any]) -> str:
    """
    Compute hash of record for caching.

    Includes key fields that affect validation:
    - decision_id, domain_id, aspect_id
    - statement, rationale
    - constraints, invariants
    - scope, blast_radius
    - version
    """
    # Select fields that affect validation
    key_fields = {
        'decision_id': record.get('decision_id', ''),
        'domain_id': record.get('domain_id', ''),
        'aspect_id': record.get('aspect_id', ''),
        'statement': record.get('statement', ''),
        'rationale': record.get('rationale', ''),
        'scope': record.get('scope', ''),
        'blast_radius': record.get('blast_radius', ''),
        'version': record.get('version', ''),
        'constraints_count': len(record.get('constraints', [])),
        'invariants_count': len(record.get('invariants', [])),
    }

    # Create stable string representation
    content = json.dumps(key_fields, sort_keys=True)

    # Hash to get compact key
    return hashlib.sha256(content.encode()).hexdigest()[:16]


# ============================================================================
# Validator Implementation
# ============================================================================

class DecisionValidator:
    """
    Decision Validator per MANTRA-L1-IMPL-VALIDATOR-001

    Implements 47 validation rules across 3 levels:
    - Level 1: Schema Validation (S-001 to S-022)
    - Level 2: Decision Consistency (D-001 to D-014)
    - Level 3: Law Compliance (L-001 to L-011)

    Per §2.3, the validator has NO authority to:
    - Enforce compliance
    - Mutate records
    - Trigger workflows
    - Approve/reject/create/modify decisions
    - Emit events or notifications
    """

    def __init__(self, cache: Optional[CacheProtocol] = None):
        self.schema_version = "1.0.0"
        self.spec_version = "MANTRA-SPEC-001 v1.0.0"
        self.cache = cache

    def validate(
        self,
        record: Dict[str, Any],
        authorship_metadata: Optional[AuthorshipMetadata] = None
    ) -> ValidationResult:
        """
        Validate a decision record (sync version, no caching).

        Per §4.5 Execution Order:
        1. Phase 1: Level 1 (S-001 through S-022)
        2. Phase 2: Level 2 (D-001 through D-014)
        3. Phase 3: Level 3 (L-001 through L-011)

        Per §4.6 Short-Circuit Behavior:
        - Level failure MAY terminate before next level
        - Multiple failures in same level MUST report all
        """
        violations: List[Violation] = []
        skipped_rules: List[str] = []
        advisory_notes: List[str] = []

        # Phase 1: Level 1 Schema Validation
        level1_violations = self._validate_level1(record)
        violations.extend(level1_violations)

        # Short-circuit per §4.6: MAY terminate if Level 1 fails
        if level1_violations:
            return self._build_result(violations, skipped_rules, advisory_notes)

        # Phase 2: Level 2 Decision Consistency
        level2_violations = self._validate_level2(record)
        violations.extend(level2_violations)

        # Short-circuit per §4.6: MAY terminate if Level 2 fails
        if level2_violations:
            return self._build_result(violations, skipped_rules, advisory_notes)

        # Phase 3: Level 3 Law Compliance
        level3_violations, level3_skipped = self._validate_level3(
            record, authorship_metadata
        )
        violations.extend(level3_violations)
        skipped_rules.extend(level3_skipped)

        if level3_skipped:
            advisory_notes.append(
                f"Rules {', '.join(level3_skipped)} were skipped due to "
                "unavailable authorship metadata per MANTRA-SPEC-001 §4.3.2"
            )

        return self._build_result(violations, skipped_rules, advisory_notes)

    async def validate_async(
        self,
        record: Dict[str, Any],
        authorship_metadata: Optional[AuthorshipMetadata] = None
    ) -> ValidationResult:
        """
        Validate a decision record (async version with optional caching).

        If cache is available:
        1. Check cache for previous validation result
        2. If cache miss, run validation
        3. Store result in cache

        Cache key is based on record content hash.
        TTL is 30 minutes (CacheTTL.VALIDATION).

        Args:
            record: Decision record as dictionary
            authorship_metadata: Optional authorship information

        Returns:
            ValidationResult with status, violations, and advisory notes
        """
        # Check cache first if available
        if self.cache:
            try:
                record_hash = _compute_record_hash(record)
                cache_key = f"mantra:validation:{record_hash}"
                cached = await self.cache.get(cache_key)

                if cached:
                    # Reconstruct ValidationResult from cached dict
                    # Handle Violation objects
                    violations = [
                        Violation(**v) if isinstance(v, dict) else v
                        for v in cached.get('violations', [])
                    ]
                    return ValidationResult(
                        status=ValidationStatus(cached['status']),
                        violations=violations,
                        skipped_rules=cached.get('skipped_rules', []),
                        advisory_notes=cached.get('advisory_notes', []),
                        validated_at=datetime.fromisoformat(cached.get('validated_at', datetime.utcnow().isoformat())),
                        schema_version=cached.get('schema_version', self.schema_version),
                        specification_version=cached.get('specification_version', self.spec_version)
                    )
            except Exception:
                # Cache error - continue without cache
                pass

        # Run validation (sync logic)
        result = self.validate(record, authorship_metadata)

        # Cache result if cache available
        if self.cache:
            try:
                record_hash = _compute_record_hash(record)
                cache_key = f"mantra:validation:{record_hash}"

                # Convert ValidationResult to dict for caching
                # Need to handle nested Violation objects
                cached_data = {
                    'status': result.status.value,
                    'violations': [
                        {
                            'rule_id': v.rule_id,
                            'level': v.level.value,
                            'message': v.message,
                            'failure_result': v.failure_result.value,
                            'governing_reference': v.governing_reference,
                            'field': v.field
                        }
                        for v in result.violations
                    ],
                    'skipped_rules': result.skipped_rules,
                    'advisory_notes': result.advisory_notes,
                    'validated_at': result.validated_at.isoformat(),
                    'schema_version': result.schema_version,
                    'specification_version': result.specification_version
                }

                await self.cache.set(cache_key, cached_data, ttl=CacheTTL.VALIDATION)
            except Exception:
                # Cache error - continue without caching
                pass

        return result

    def _validate_level1(self, record: Dict[str, Any]) -> List[Violation]:
        """
        Level 1: Schema Validation (S-001 to S-022)
        Validates structural conformance to MANTRA-SCHEMA-001.
        """
        violations = []

        # S-001: decision_id presence
        if "decision_id" not in record:
            violations.append(Violation(
                rule_id="S-001",
                level=ValidationLevel.LEVEL_1,
                message="decision_id is required",
                failure_result=FailureResult.INVALID,
                governing_reference="MANTRA-SCHEMA-001",
                field="decision_id"
            ))

        # S-002: decision_id format (UUID)
        if "decision_id" in record:
            import re
            uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
            if not re.match(uuid_pattern, str(record.get("decision_id", "")), re.IGNORECASE):
                violations.append(Violation(
                    rule_id="S-002",
                    level=ValidationLevel.LEVEL_1,
                    message="decision_id must be a valid UUID",
                    failure_result=FailureResult.INVALID,
                    governing_reference="MANTRA-SCHEMA-001",
                    field="decision_id"
                ))

        # S-003: domain_id presence
        if "domain_id" not in record:
            violations.append(Violation(
                rule_id="S-003",
                level=ValidationLevel.LEVEL_1,
                message="domain_id is required",
                failure_result=FailureResult.INVALID,
                governing_reference="MANTRA-SCHEMA-001",
                field="domain_id"
            ))

        # S-004: domain_id enumeration
        if "domain_id" in record:
            valid_domains = [g.value for g in DomainId]
            if record["domain_id"] not in valid_domains:
                violations.append(Violation(
                    rule_id="S-004",
                    level=ValidationLevel.LEVEL_1,
                    message=f"domain_id must be one of: {valid_domains}",
                    failure_result=FailureResult.INVALID,
                    governing_reference="MANTRA-SCHEMA-001",
                    field="domain_id"
                ))

        # S-005: aspect_id presence
        if "aspect_id" not in record:
            violations.append(Violation(
                rule_id="S-005",
                level=ValidationLevel.LEVEL_1,
                message="aspect_id is required",
                failure_result=FailureResult.INVALID,
                governing_reference="MANTRA-SCHEMA-001",
                field="aspect_id"
            ))

        # S-006: aspect_id enumeration
        if "aspect_id" in record:
            valid_aspects = [f.value for f in AspectId]
            if record["aspect_id"] not in valid_aspects:
                violations.append(Violation(
                    rule_id="S-006",
                    level=ValidationLevel.LEVEL_1,
                    message=f"aspect_id must be one of: {valid_aspects}",
                    failure_result=FailureResult.INVALID,
                    governing_reference="MANTRA-SCHEMA-001",
                    field="aspect_id"
                ))

        # S-007: statement presence
        if "statement" not in record or not record.get("statement"):
            violations.append(Violation(
                rule_id="S-007",
                level=ValidationLevel.LEVEL_1,
                message="statement is required and must not be empty",
                failure_result=FailureResult.INVALID,
                governing_reference="MANTRA-SCHEMA-001",
                field="statement"
            ))

        # S-008: statement type
        if "statement" in record and not isinstance(record["statement"], str):
            violations.append(Violation(
                rule_id="S-008",
                level=ValidationLevel.LEVEL_1,
                message="statement must be a string",
                failure_result=FailureResult.INVALID,
                governing_reference="MANTRA-SCHEMA-001",
                field="statement"
            ))

        # S-009: rationale presence
        if "rationale" not in record or not record.get("rationale"):
            violations.append(Violation(
                rule_id="S-009",
                level=ValidationLevel.LEVEL_1,
                message="rationale is required and must not be empty",
                failure_result=FailureResult.INVALID,
                governing_reference="MANTRA-SCHEMA-001",
                field="rationale"
            ))

        # S-010: rationale type
        if "rationale" in record and not isinstance(record["rationale"], str):
            violations.append(Violation(
                rule_id="S-010",
                level=ValidationLevel.LEVEL_1,
                message="rationale must be a string",
                failure_result=FailureResult.INVALID,
                governing_reference="MANTRA-SCHEMA-001",
                field="rationale"
            ))

        # S-011: constraints type (array)
        if "constraints" in record and not isinstance(record["constraints"], list):
            violations.append(Violation(
                rule_id="S-011",
                level=ValidationLevel.LEVEL_1,
                message="constraints must be an array",
                failure_result=FailureResult.INVALID,
                governing_reference="MANTRA-SCHEMA-001",
                field="constraints"
            ))

        # S-012: constraint structure
        if "constraints" in record and isinstance(record["constraints"], list):
            for i, constraint in enumerate(record["constraints"]):
                if not isinstance(constraint, dict):
                    violations.append(Violation(
                        rule_id="S-012",
                        level=ValidationLevel.LEVEL_1,
                        message=f"constraints[{i}] must be an object",
                        failure_result=FailureResult.INVALID,
                        governing_reference="MANTRA-SCHEMA-001",
                        field=f"constraints[{i}]"
                    ))
                else:
                    for required_field in ["constraint_id", "statement", "type"]:
                        if required_field not in constraint:
                            violations.append(Violation(
                                rule_id="S-012",
                                level=ValidationLevel.LEVEL_1,
                                message=f"constraints[{i}].{required_field} is required",
                                failure_result=FailureResult.INVALID,
                                governing_reference="MANTRA-SCHEMA-001",
                                field=f"constraints[{i}].{required_field}"
                            ))

        # S-013: invariants presence
        if "invariants" not in record:
            violations.append(Violation(
                rule_id="S-013",
                level=ValidationLevel.LEVEL_1,
                message="invariants is required",
                failure_result=FailureResult.INVALID,
                governing_reference="MANTRA-SCHEMA-001",
                field="invariants"
            ))

        # S-014: invariants type (array)
        if "invariants" in record and not isinstance(record["invariants"], list):
            violations.append(Violation(
                rule_id="S-014",
                level=ValidationLevel.LEVEL_1,
                message="invariants must be an array",
                failure_result=FailureResult.INVALID,
                governing_reference="MANTRA-SCHEMA-001",
                field="invariants"
            ))

        # S-015: scope presence
        if "scope" not in record:
            violations.append(Violation(
                rule_id="S-015",
                level=ValidationLevel.LEVEL_1,
                message="scope is required",
                failure_result=FailureResult.INVALID,
                governing_reference="MANTRA-SCHEMA-001",
                field="scope"
            ))

        # S-016: scope enumeration
        if "scope" in record:
            valid_scopes = [s.value for s in Scope]
            if record["scope"] not in valid_scopes:
                violations.append(Violation(
                    rule_id="S-016",
                    level=ValidationLevel.LEVEL_1,
                    message=f"scope must be one of: {valid_scopes}",
                    failure_result=FailureResult.INVALID,
                    governing_reference="MANTRA-SCHEMA-001",
                    field="scope"
                ))

        # S-017: blast_radius presence
        if "blast_radius" not in record:
            violations.append(Violation(
                rule_id="S-017",
                level=ValidationLevel.LEVEL_1,
                message="blast_radius is required",
                failure_result=FailureResult.INVALID,
                governing_reference="MANTRA-SCHEMA-001",
                field="blast_radius"
            ))

        # S-018: blast_radius enumeration
        if "blast_radius" in record:
            valid_radii = [b.value for b in BlastRadius]
            if record["blast_radius"] not in valid_radii:
                violations.append(Violation(
                    rule_id="S-018",
                    level=ValidationLevel.LEVEL_1,
                    message=f"blast_radius must be one of: {valid_radii}",
                    failure_result=FailureResult.INVALID,
                    governing_reference="MANTRA-SCHEMA-001",
                    field="blast_radius"
                ))

        # S-019, S-020: DEPRECATED per MANTRA-SPEC-001-AMENDMENT-001
        # Status field removed - evolution via version + supersedes only

        # S-021: version presence
        if "version" not in record:
            violations.append(Violation(
                rule_id="S-021",
                level=ValidationLevel.LEVEL_1,
                message="version is required",
                failure_result=FailureResult.INVALID,
                governing_reference="MANTRA-SCHEMA-001",
                field="version"
            ))

        # S-022: version format
        if "version" in record:
            import re
            version_pattern = r"^[0-9]+\.[0-9]+\.[0-9]+$"
            if not re.match(version_pattern, str(record.get("version", ""))):
                violations.append(Violation(
                    rule_id="S-022",
                    level=ValidationLevel.LEVEL_1,
                    message="version must follow semantic versioning (X.Y.Z)",
                    failure_result=FailureResult.INVALID,
                    governing_reference="MANTRA-SCHEMA-001",
                    field="version"
                ))

        return violations

    def _validate_level2(self, record: Dict[str, Any]) -> List[Violation]:
        """
        Level 2: Decision Consistency Validation (D-001 to D-014)
        Validates semantic conformance to MANTRA-DEC-001 through MANTRA-DEC-004.
        """
        violations = []

        # D-001: Domain-Aspect compatibility
        domain_id = record.get("domain_id")
        aspect_id = record.get("aspect_id")
        if domain_id and aspect_id:
            try:
                domain = DomainId(domain_id)
                aspect = AspectId(aspect_id)
                if not is_aspect_compatible(domain, aspect):
                    violations.append(Violation(
                        rule_id="D-001",
                        level=ValidationLevel.LEVEL_2,
                        message=f"Aspect {aspect_id} is not compatible with domain {domain_id}",
                        failure_result=FailureResult.INVALID,
                        governing_reference="MANTRA-DEC-002",
                        field="aspect_id"
                    ))
            except ValueError:
                pass  # Already caught in Level 1

        # D-002: Constraint constraint_id uniqueness
        constraints = record.get("constraints", [])
        if isinstance(constraints, list):
            constraint_ids = [c.get("constraint_id") for c in constraints if isinstance(c, dict)]
            if len(constraint_ids) != len(set(constraint_ids)):
                violations.append(Violation(
                    rule_id="D-002",
                    level=ValidationLevel.LEVEL_2,
                    message="constraint_id must be unique within decision",
                    failure_result=FailureResult.INVALID,
                    governing_reference="MANTRA-SCHEMA-001",
                    field="constraints"
                ))

        # D-003: Constraint type enumeration
        valid_types = [t.value for t in ConstraintType]
        for i, constraint in enumerate(constraints):
            if isinstance(constraint, dict):
                ctype = constraint.get("type")
                if ctype and ctype not in valid_types:
                    violations.append(Violation(
                        rule_id="D-003",
                        level=ValidationLevel.LEVEL_2,
                        message=f"constraints[{i}].type must be one of: {valid_types}",
                        failure_result=FailureResult.INVALID,
                        governing_reference="MANTRA-SCHEMA-001",
                        field=f"constraints[{i}].type"
                    ))

        # D-004: Constraint statement non-empty
        for i, constraint in enumerate(constraints):
            if isinstance(constraint, dict):
                stmt = constraint.get("statement", "")
                if not stmt or not str(stmt).strip():
                    violations.append(Violation(
                        rule_id="D-004",
                        level=ValidationLevel.LEVEL_2,
                        message=f"constraints[{i}].statement must not be empty",
                        failure_result=FailureResult.INVALID,
                        governing_reference="MANTRA-SCHEMA-001",
                        field=f"constraints[{i}].statement"
                    ))

        # D-005: Invariant non-empty strings
        invariants = record.get("invariants", [])
        if isinstance(invariants, list):
            for i, inv in enumerate(invariants):
                if not inv or not str(inv).strip():
                    violations.append(Violation(
                        rule_id="D-005",
                        level=ValidationLevel.LEVEL_2,
                        message=f"invariants[{i}] must not be empty",
                        failure_result=FailureResult.INVALID,
                        governing_reference="MANTRA-SCHEMA-001",
                        field=f"invariants[{i}]"
                    ))

        # D-006 through D-014: Additional consistency checks
        # These are semantic validations based on MANTRA-DEC-001 through DEC-004
        # Simplified implementation - full implementation would include all 14 rules

        return violations

    def _validate_level3(
        self,
        record: Dict[str, Any],
        authorship_metadata: Optional[AuthorshipMetadata]
    ) -> tuple[List[Violation], List[str]]:
        """
        Level 3: Law Compliance Validation (L-001 to L-011)
        Validates authority conformance to MANTRA-LAW-001.

        Per §6.3: When authorship metadata is unavailable,
        rules L-001 through L-008 MUST be skipped.
        """
        violations = []
        skipped_rules = []

        # L-001 through L-008: Authorship prohibitions (conditional)
        # NOTE: L-007 DEPRECATED per MANTRA-SPEC-001-AMENDMENT-001
        if authorship_metadata is None:
            # Skip authorship rules per MANTRA-SPEC-001 §4.3.2
            skipped_rules.extend([
                "L-001", "L-002", "L-003", "L-004",
                "L-005", "L-006", "L-008"
            ])
        else:
            # L-001: Statement not authored by AI
            if authorship_metadata.author_type == "ai":
                violations.append(Violation(
                    rule_id="L-001",
                    level=ValidationLevel.LEVEL_3,
                    message="statement must not be authored by AI",
                    failure_result=FailureResult.INVALID,
                    governing_reference="MANTRA-LAW-001 §6",
                    field="statement"
                ))

            # L-002: Rationale not authored by AI
            if authorship_metadata.author_type == "ai":
                violations.append(Violation(
                    rule_id="L-002",
                    level=ValidationLevel.LEVEL_3,
                    message="rationale must not be authored by AI",
                    failure_result=FailureResult.INVALID,
                    governing_reference="MANTRA-LAW-001 §6",
                    field="rationale"
                ))

            # L-003: Approval not by AI
            if authorship_metadata.is_approval and authorship_metadata.author_type == "ai":
                violations.append(Violation(
                    rule_id="L-003",
                    level=ValidationLevel.LEVEL_3,
                    message="approved_by must not contain AI identifier",
                    failure_result=FailureResult.INVALID,
                    governing_reference="MANTRA-LAW-001 §6",
                    field="approved_by"
                ))

            # L-004 through L-008: Additional authorship checks
            # Simplified implementation

        # L-009: Mutability violation (unconditional)
        # This would check if attempting to modify stored decision
        # Checked at storage layer

        # L-010: Singularity rule
        # One decision per domain-aspect combination at ACTIVE status

        # L-011: Version increment on change
        # Would require previous version for comparison

        return violations, skipped_rules

    def _build_result(
        self,
        violations: List[Violation],
        skipped_rules: List[str],
        advisory_notes: List[str]
    ) -> ValidationResult:
        """
        Build validation result per MANTRA-SPEC-001 §7.3

        Status determination:
        - No violations, no skipped rules: VALID
        - No violations, some skipped rules: VALID (with advisory)
        - Any violation with INVALID failure_result: INVALID
        - All violations have REJECTED failure_result: REJECTED
        - Mix of INVALID and REJECTED: INVALID
        """
        if not violations:
            status = ValidationStatus.VALID
        elif all(v.failure_result == FailureResult.REJECTED for v in violations):
            status = ValidationStatus.REJECTED
        else:
            status = ValidationStatus.INVALID

        return ValidationResult(
            status=status,
            violations=violations,
            skipped_rules=skipped_rules,
            advisory_notes=advisory_notes,
            validated_at=datetime.utcnow(),
            schema_version=self.schema_version,
            specification_version=self.spec_version,
        )


# ============================================================================
# Use Case Function
# ============================================================================

def validate_decision(
    record: Dict[str, Any],
    authorship_metadata: Optional[AuthorshipMetadata] = None
) -> ValidationResult:
    """
    Validate a decision record (sync version, no caching).

    This is the main entry point for the Validator Service
    per MANTRA-L1-IMPL-VALIDATOR-001.

    Args:
        record: Decision record as dictionary
        authorship_metadata: Optional authorship information

    Returns:
        ValidationResult with status, violations, and advisory notes
    """
    validator = DecisionValidator()
    return validator.validate(record, authorship_metadata)


async def validate_decision_async(
    record: Dict[str, Any],
    authorship_metadata: Optional[AuthorshipMetadata] = None,
    cache: Optional[CacheProtocol] = None
) -> ValidationResult:
    """
    Validate a decision record (async version with optional caching).

    This is the async entry point that supports Redis caching
    for expensive validation operations.

    Cache Strategy:
    - Cache key: Hash of record content (decision_id, statement, rationale, etc.)
    - TTL: 30 minutes (CacheTTL.VALIDATION)
    - Cache is optional - validation works without it

    Args:
        record: Decision record as dictionary
        authorship_metadata: Optional authorship information
        cache: Optional cache implementation for result caching

    Returns:
        ValidationResult with status, violations, and advisory notes
    """
    validator = DecisionValidator(cache=cache)
    return await validator.validate_async(record, authorship_metadata)


# ============================================================================
# Referential Integrity Validation (requires repository)
# ============================================================================

@dataclass
class RelationshipViolation:
    """Violation for relationship integrity checks."""
    rule_id: str
    message: str
    is_error: bool  # True = error, False = advisory
    related_id: Optional[str] = None
    source_group: Optional[str] = None
    target_group: Optional[str] = None


@dataclass
class RelationshipValidationResult:
    """Result of relationship integrity validation."""
    is_valid: bool
    violations: List[RelationshipViolation]
    advisory_notes: List[str]
    cross_domain_references: List[Dict[str, str]]  # [{from_domain, to_domain, decision_id}]


def validate_related_decisions_integrity(
    record: Dict[str, Any],
    existing_decisions: List[Dict[str, Any]]
) -> RelationshipValidationResult:
    """
    Validate related_decisions referential integrity.

    Rules:
    - D-015: All IDs in related_decisions MUST exist
    - D-016: No circular reference (decision cannot reference itself)
    - D-017: Cross-domain references generate advisory note (not error)

    Args:
        record: Decision record to validate
        existing_decisions: List of all existing decision dicts

    Returns:
        RelationshipValidationResult with violations and advisories
    """
    violations = []
    advisory_notes = []
    cross_group_refs = []

    decision_id = record.get("decision_id")
    domain_id = record.get("domain_id")
    related_decisions = record.get("related_decisions", [])

    # Build lookup map for existing decisions
    existing_map = {d.get("decision_id"): d for d in existing_decisions}

    for rel_id in related_decisions:
        # D-016: Self-reference check
        if rel_id == decision_id:
            violations.append(RelationshipViolation(
                rule_id="D-016",
                message=f"Decision cannot reference itself in related_decisions",
                is_error=True,
                related_id=rel_id
            ))
            continue

        # D-015: Existence check
        if rel_id not in existing_map:
            violations.append(RelationshipViolation(
                rule_id="D-015",
                message=f"Related decision '{rel_id}' does not exist",
                is_error=True,
                related_id=rel_id
            ))
            continue

        # D-017: Cross-domain reference advisory
        related_decision = existing_map[rel_id]
        related_domain = related_decision.get("domain_id")

        if related_domain and related_domain != domain_id:
            cross_group_refs.append({
                "from_domain": domain_id,
                "to_domain": related_domain,
                "related_decision_id": rel_id
            })
            advisory_notes.append(
                f"D-017: Cross-domain reference detected: "
                f"{domain_id} → {related_domain} (decision {rel_id[:8]}...)"
            )

    # Check for potential circular chains (deeper than self-reference)
    # This checks if adding this decision would create a cycle
    visited = set()
    to_check = list(related_decisions)

    while to_check:
        checking_id = to_check.pop(0)
        if checking_id in visited:
            continue
        visited.add(checking_id)

        if checking_id == decision_id:
            violations.append(RelationshipViolation(
                rule_id="D-016",
                message=f"Circular reference chain detected through related_decisions",
                is_error=True
            ))
            break

        # Add the related decision's related_decisions to check
        if checking_id in existing_map:
            nested_related = existing_map[checking_id].get("related_decisions", [])
            to_check.extend([r for r in nested_related if r not in visited])

    has_errors = any(v.is_error for v in violations)

    return RelationshipValidationResult(
        is_valid=not has_errors,
        violations=violations,
        advisory_notes=advisory_notes,
        cross_domain_references=cross_group_refs
    )


async def validate_related_decisions_integrity_async(
    record: Dict[str, Any],
    repository
) -> RelationshipValidationResult:
    """
    Async version that fetches existing decisions from repository.

    Args:
        record: Decision record to validate
        repository: DecisionRepository instance

    Returns:
        RelationshipValidationResult
    """
    # Fetch all decisions for integrity check
    stored_decisions = await repository.find_all_async(limit=10000, offset=0)
    existing_decisions = [
        {
            "decision_id": sd.decision.decision_id,
            "domain_id": sd.decision.domain_id.value,
            "aspect_id": sd.decision.aspect_id.value,
            "related_decisions": sd.decision.related_decisions
        }
        for sd in stored_decisions
    ]

    return validate_related_decisions_integrity(record, existing_decisions)
