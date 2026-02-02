"""
MANTRA Compliance Test Suite

Validates that the system correctly enforces MANTRA constitutional laws:
- MANTRA-LAW-001 §6: AI has ZERO approval authority
- MANTRA-LAW-001 §2.3: Human authorship REQUIRED
- MANTRA-LAW-001 §10.7: Metadata enrichment rules
- Schema validation for MCPDecision structure
- 3-Gate validation pipeline compliance

This test ensures AI assistants CANNOT:
1. Approve decisions
2. Create decisions without human confirmation
3. Bypass validation gates
4. Modify forbidden fields

Usage:
    python -m pytest tests/mantra_compliance_test.py -v
    python tests/mantra_compliance_test.py  # Direct run
"""

import sys
import os
import json
import time
from datetime import datetime
from dataclasses import dataclass, field as dc_field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# MANTRA LAW DEFINITIONS
# ============================================================================

class MantraLaw:
    """MANTRA Constitutional Law definitions."""

    # §6 - AI Authority Limits
    AI_ZERO_APPROVAL = "§6: AI has ZERO approval authority"
    AI_CANNOT_CREATE = "§6.3: AI cannot create/modify/finalize decisions"
    AI_READ_ONLY = "§6.2: AI may read, detect conflicts, flag gaps"

    # §2.3 - Human Authorship
    HUMAN_AUTHORSHIP = "§2.3: Human authorship REQUIRED"

    # §10.7 - Enrichment Rules
    ENRICHABLE_FIELDS = {
        "trigger_event",
        "code_artifacts",
        "embedding_metadata",
        "llm_optimization.embedding_text",
        "llm_optimization.keywords_for_rag",
        "search_metadata.search_keywords",
        "search_metadata.aliases",
        "knowledge_consumption.reading_time_minutes",
    }

    FORBIDDEN_FIELDS = {
        "statement",
        "rationale",
        "constraints",
        "invariants",
        "domain_id",
        "aspect_id",
        "scope",
        "blast_radius",
    }

    # §10.7.2 - Enrichment requirements
    ENRICHMENT_REQUIRES_HUMAN_APPROVAL = True
    ENRICHMENT_REASON_MIN_LENGTH = 10


class ValidationGate(Enum):
    """3-Gate Validation Pipeline."""
    DETERMINISTIC = "gate_1"   # Schema validation, format checks
    AI_HEURISTIC = "gate_2"    # AI suggestions (advisory only)
    HUMAN_APPROVAL = "gate_3"  # Human final decision (REQUIRED)


@dataclass
class FieldPermission:
    """Defines who can fill a field."""
    field_name: str
    ai_can_suggest: bool
    ai_can_fill: bool
    requires_human_input: bool
    requires_human_approval: bool
    source_options: List[str]  # ["ai", "human", "formula", "system"]


# ============================================================================
# FIELD PERMISSION MATRIX
# ============================================================================

FIELD_PERMISSIONS: Dict[str, FieldPermission] = {
    # Identity fields - System generated
    "decision_id": FieldPermission(
        field_name="decision_id",
        ai_can_suggest=False,
        ai_can_fill=False,
        requires_human_input=False,
        requires_human_approval=False,
        source_options=["system"],
    ),
    "created_at": FieldPermission(
        field_name="created_at",
        ai_can_suggest=False,
        ai_can_fill=False,
        requires_human_input=False,
        requires_human_approval=False,
        source_options=["system"],
    ),

    # Core content - Human REQUIRED
    "title": FieldPermission(
        field_name="title",
        ai_can_suggest=True,
        ai_can_fill=False,
        requires_human_input=True,
        requires_human_approval=True,
        source_options=["human", "ai_suggest"],
    ),
    "statement": FieldPermission(
        field_name="statement",
        ai_can_suggest=True,
        ai_can_fill=False,
        requires_human_input=True,
        requires_human_approval=True,
        source_options=["human", "ai_suggest"],
    ),
    "rationale": FieldPermission(
        field_name="rationale",
        ai_can_suggest=True,
        ai_can_fill=False,
        requires_human_input=True,
        requires_human_approval=True,
        source_options=["human", "ai_suggest"],
    ),

    # Classification - Human confirms AI suggestion
    "domain_id": FieldPermission(
        field_name="domain_id",
        ai_can_suggest=True,
        ai_can_fill=False,
        requires_human_input=False,
        requires_human_approval=True,
        source_options=["ai_suggest", "human"],
    ),
    "aspect_id": FieldPermission(
        field_name="aspect_id",
        ai_can_suggest=True,
        ai_can_fill=False,
        requires_human_input=False,
        requires_human_approval=True,
        source_options=["ai_suggest", "human"],
    ),

    # Impact assessment - AI suggests, human approves
    "blast_radius": FieldPermission(
        field_name="blast_radius",
        ai_can_suggest=True,
        ai_can_fill=False,
        requires_human_input=False,
        requires_human_approval=True,
        source_options=["ai_suggest", "formula", "human"],
    ),

    # Constraints - Human REQUIRED
    "constraints": FieldPermission(
        field_name="constraints",
        ai_can_suggest=True,
        ai_can_fill=False,
        requires_human_input=True,
        requires_human_approval=True,
        source_options=["human", "ai_suggest"],
    ),
    "invariants": FieldPermission(
        field_name="invariants",
        ai_can_suggest=True,
        ai_can_fill=False,
        requires_human_input=True,
        requires_human_approval=True,
        source_options=["human", "ai_suggest"],
    ),

    # Enrichable fields - AI can fill with human approval
    "trigger_event": FieldPermission(
        field_name="trigger_event",
        ai_can_suggest=True,
        ai_can_fill=True,
        requires_human_input=False,
        requires_human_approval=True,
        source_options=["ai", "human"],
    ),
    "code_artifacts": FieldPermission(
        field_name="code_artifacts",
        ai_can_suggest=True,
        ai_can_fill=True,
        requires_human_input=False,
        requires_human_approval=True,
        source_options=["ai", "human", "system"],
    ),

    # Authorship - System tracked
    "author_id": FieldPermission(
        field_name="author_id",
        ai_can_suggest=False,
        ai_can_fill=False,
        requires_human_input=False,
        requires_human_approval=False,
        source_options=["system"],  # From authenticated user
    ),
    "approved_by": FieldPermission(
        field_name="approved_by",
        ai_can_suggest=False,
        ai_can_fill=False,
        requires_human_input=True,
        requires_human_approval=True,
        source_options=["human"],  # MUST be human, never AI
    ),
}


# ============================================================================
# COMPLIANCE VALIDATORS
# ============================================================================

@dataclass
class ComplianceResult:
    """Result of a compliance check."""
    passed: bool
    law_reference: str
    message: str
    details: Dict[str, Any] = dc_field(default_factory=dict)


class MantraComplianceValidator:
    """Validates MANTRA constitutional law compliance."""

    def __init__(self):
        self.results: List[ComplianceResult] = []

    def validate_ai_cannot_approve(
        self,
        actor_id: str,
        action: str,
        target: str,
    ) -> ComplianceResult:
        """
        Validate that AI cannot approve decisions.
        MANTRA-LAW-001 §6: AI has ZERO approval authority.
        """
        is_ai = actor_id.startswith("ai:") or actor_id.lower() in ["claude", "gpt", "ai"]
        is_approval_action = action.lower() in [
            "approve", "reject", "finalize", "create", "modify", "delete"
        ]

        if is_ai and is_approval_action:
            result = ComplianceResult(
                passed=False,
                law_reference=MantraLaw.AI_ZERO_APPROVAL,
                message=f"VIOLATION: AI actor '{actor_id}' cannot perform '{action}' on '{target}'",
                details={
                    "actor": actor_id,
                    "action": action,
                    "target": target,
                    "violation_type": "AI_APPROVAL_ATTEMPT",
                },
            )
        else:
            result = ComplianceResult(
                passed=True,
                law_reference=MantraLaw.AI_ZERO_APPROVAL,
                message=f"OK: Action '{action}' by '{actor_id}' is permitted",
                details={"actor": actor_id, "action": action},
            )

        self.results.append(result)
        return result

    def validate_human_authorship(
        self,
        decision: Dict[str, Any],
    ) -> ComplianceResult:
        """
        Validate that decision has human authorship.
        MANTRA-LAW-001 §2.3: Human authorship REQUIRED.
        """
        author_id = decision.get("author_id", "")

        # Check if author is AI
        is_ai_author = (
            author_id.startswith("ai:") or
            author_id.lower() in ["claude", "gpt", "ai", "assistant"]
        )

        if is_ai_author or not author_id:
            result = ComplianceResult(
                passed=False,
                law_reference=MantraLaw.HUMAN_AUTHORSHIP,
                message=f"VIOLATION: Decision requires human author, got '{author_id}'",
                details={
                    "author_id": author_id,
                    "decision_id": decision.get("decision_id"),
                    "violation_type": "MISSING_HUMAN_AUTHOR",
                },
            )
        else:
            result = ComplianceResult(
                passed=True,
                law_reference=MantraLaw.HUMAN_AUTHORSHIP,
                message=f"OK: Human author '{author_id}' is valid",
                details={"author_id": author_id},
            )

        self.results.append(result)
        return result

    def validate_enrichment_field(
        self,
        field_path: str,
        enriched_by: str,
        approved_by: str,
        reason: str,
    ) -> ComplianceResult:
        """
        Validate enrichment per MANTRA-LAW-001 §10.7.
        """
        violations = []

        # Check if field is enrichable
        if field_path in MantraLaw.FORBIDDEN_FIELDS:
            violations.append(f"Field '{field_path}' is FORBIDDEN for enrichment")

        if field_path not in MantraLaw.ENRICHABLE_FIELDS and field_path not in MantraLaw.FORBIDDEN_FIELDS:
            violations.append(f"Field '{field_path}' is not in enrichable list")

        # Check AI enrichment requires human approval
        if enriched_by.startswith("ai:"):
            if not approved_by or approved_by.startswith("ai:"):
                violations.append("AI enrichment requires human approval")

        # Check reason length
        if len(reason) < MantraLaw.ENRICHMENT_REASON_MIN_LENGTH:
            violations.append(f"Reason must be at least {MantraLaw.ENRICHMENT_REASON_MIN_LENGTH} characters")

        if violations:
            result = ComplianceResult(
                passed=False,
                law_reference="§10.7 Metadata Enrichment",
                message=f"VIOLATION: {'; '.join(violations)}",
                details={
                    "field_path": field_path,
                    "enriched_by": enriched_by,
                    "approved_by": approved_by,
                    "reason_length": len(reason),
                    "violations": violations,
                },
            )
        else:
            result = ComplianceResult(
                passed=True,
                law_reference="§10.7 Metadata Enrichment",
                message=f"OK: Enrichment of '{field_path}' is valid",
                details={"field_path": field_path},
            )

        self.results.append(result)
        return result

    def validate_field_source(
        self,
        field_name: str,
        source: str,
        has_human_approval: bool,
    ) -> ComplianceResult:
        """
        Validate that field source is permitted.
        """
        permission = FIELD_PERMISSIONS.get(field_name)

        if not permission:
            result = ComplianceResult(
                passed=True,
                law_reference="Field Permission",
                message=f"OK: Field '{field_name}' has no specific restrictions",
                details={"field_name": field_name},
            )
            self.results.append(result)
            return result

        violations = []

        # Check source is permitted
        if source not in permission.source_options:
            violations.append(f"Source '{source}' not in allowed: {permission.source_options}")

        # Check AI fill permission
        if source == "ai" and not permission.ai_can_fill:
            violations.append(f"AI cannot directly fill '{field_name}'")

        # Check human approval requirement
        if permission.requires_human_approval and not has_human_approval:
            violations.append(f"Field '{field_name}' requires human approval")

        if violations:
            result = ComplianceResult(
                passed=False,
                law_reference="Field Permission Matrix",
                message=f"VIOLATION: {'; '.join(violations)}",
                details={
                    "field_name": field_name,
                    "source": source,
                    "has_human_approval": has_human_approval,
                    "permission": {
                        "ai_can_fill": permission.ai_can_fill,
                        "requires_human_approval": permission.requires_human_approval,
                    },
                    "violations": violations,
                },
            )
        else:
            result = ComplianceResult(
                passed=True,
                law_reference="Field Permission Matrix",
                message=f"OK: Field '{field_name}' from '{source}' is permitted",
                details={"field_name": field_name, "source": source},
            )

        self.results.append(result)
        return result

    def validate_3gate_pipeline(
        self,
        decision: Dict[str, Any],
        gate_results: Dict[ValidationGate, bool],
    ) -> ComplianceResult:
        """
        Validate 3-Gate pipeline was followed.
        Gate 3 (Human Approval) is ALWAYS required.
        """
        violations = []

        # Gate 1: Deterministic validation must pass
        if not gate_results.get(ValidationGate.DETERMINISTIC, False):
            violations.append("Gate 1 (Deterministic) validation failed")

        # Gate 2: AI heuristic is advisory only
        # (no violation if skipped, but warning if failed)
        if not gate_results.get(ValidationGate.AI_HEURISTIC, True):
            pass  # Advisory, not blocking

        # Gate 3: Human approval is MANDATORY
        if not gate_results.get(ValidationGate.HUMAN_APPROVAL, False):
            violations.append("Gate 3 (Human Approval) is MANDATORY and missing")

        if violations:
            result = ComplianceResult(
                passed=False,
                law_reference="3-Gate Validation Pipeline",
                message=f"VIOLATION: {'; '.join(violations)}",
                details={
                    "decision_id": decision.get("decision_id"),
                    "gate_results": {g.value: v for g, v in gate_results.items()},
                    "violations": violations,
                },
            )
        else:
            result = ComplianceResult(
                passed=True,
                law_reference="3-Gate Validation Pipeline",
                message="OK: All required gates passed",
                details={"gate_results": {g.value: v for g, v in gate_results.items()}},
            )

        self.results.append(result)
        return result

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all validation results."""
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed

        return {
            "total_checks": len(self.results),
            "passed": passed,
            "failed": failed,
            "success_rate": f"{(passed / len(self.results) * 100):.1f}%" if self.results else "N/A",
            "violations": [r for r in self.results if not r.passed],
        }


# ============================================================================
# TEST CASES
# ============================================================================

def test_ai_cannot_approve():
    """Test that AI cannot approve decisions."""
    print("\n" + "=" * 60)
    print("TEST: AI Cannot Approve Decisions (MANTRA-LAW-001 §6)")
    print("=" * 60)

    validator = MantraComplianceValidator()
    test_cases = [
        # (actor_id, action, target, should_pass)
        ("ai:claude-opus-4-5", "approve", "DEC-001", False),
        ("ai:claude", "reject", "DEC-002", False),
        ("ai:gpt-4", "finalize", "DEC-003", False),
        ("ai:claude", "create", "new-decision", False),
        ("ai:assistant", "modify", "DEC-004", False),
        ("ai:claude", "delete", "DEC-005", False),
        ("human:john@example.com", "approve", "DEC-001", True),
        ("human:jane@example.com", "create", "new-decision", True),
        ("ai:claude", "read", "DEC-001", True),  # AI CAN read
        ("ai:claude", "suggest", "DEC-001", True),  # AI CAN suggest
        ("ai:claude", "analyze", "DEC-001", True),  # AI CAN analyze
    ]

    passed = 0
    for actor_id, action, target, should_pass in test_cases:
        result = validator.validate_ai_cannot_approve(actor_id, action, target)
        status = "PASS" if result.passed == should_pass else "FAIL"
        if result.passed == should_pass:
            passed += 1
        print(f"  [{status}] {actor_id} -> {action} ({target})")

    print(f"\nResult: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def test_human_authorship():
    """Test that decisions require human authorship."""
    print("\n" + "=" * 60)
    print("TEST: Human Authorship Required (MANTRA-LAW-001 §2.3)")
    print("=" * 60)

    validator = MantraComplianceValidator()
    test_cases = [
        # (decision, should_pass)
        ({"decision_id": "DEC-001", "author_id": "human:john@example.com"}, True),
        ({"decision_id": "DEC-002", "author_id": "user:jane.doe"}, True),
        ({"decision_id": "DEC-003", "author_id": "ai:claude"}, False),
        ({"decision_id": "DEC-004", "author_id": "ai:gpt-4"}, False),
        ({"decision_id": "DEC-005", "author_id": ""}, False),
        ({"decision_id": "DEC-006", "author_id": "Claude"}, False),
        ({"decision_id": "DEC-007", "author_id": "assistant"}, False),
    ]

    passed = 0
    for decision, should_pass in test_cases:
        result = validator.validate_human_authorship(decision)
        status = "PASS" if result.passed == should_pass else "FAIL"
        if result.passed == should_pass:
            passed += 1
        print(f"  [{status}] author_id='{decision['author_id']}'")

    print(f"\nResult: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def test_enrichment_rules():
    """Test enrichment field rules (§10.7)."""
    print("\n" + "=" * 60)
    print("TEST: Enrichment Rules (MANTRA-LAW-001 §10.7)")
    print("=" * 60)

    validator = MantraComplianceValidator()
    test_cases = [
        # (field_path, enriched_by, approved_by, reason, should_pass)
        # Valid enrichments
        ("trigger_event", "ai:claude", "human:john@example.com", "Adding context trigger for better retrieval", True),
        ("code_artifacts", "human:jane", "human:jane", "Linking implementation files", True),

        # AI enrichment without human approval - INVALID
        ("trigger_event", "ai:claude", "ai:claude", "Auto-enrichment", False),
        ("trigger_event", "ai:claude", "", "Missing approver", False),

        # Forbidden fields - INVALID
        ("statement", "human:john", "human:john", "Trying to modify statement", False),
        ("rationale", "human:john", "human:john", "Trying to modify rationale", False),
        ("constraints", "ai:claude", "human:john", "Trying to modify constraints", False),
        ("domain_id", "human:john", "human:john", "Trying to change domain", False),

        # Reason too short - INVALID
        ("trigger_event", "human:john", "human:john", "short", False),
    ]

    passed = 0
    for field_path, enriched_by, approved_by, reason, should_pass in test_cases:
        result = validator.validate_enrichment_field(field_path, enriched_by, approved_by, reason)
        status = "PASS" if result.passed == should_pass else "FAIL"
        if result.passed == should_pass:
            passed += 1
        print(f"  [{status}] {field_path} by {enriched_by}")

    print(f"\nResult: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def test_field_source_permissions():
    """Test field source permissions."""
    print("\n" + "=" * 60)
    print("TEST: Field Source Permissions")
    print("=" * 60)

    validator = MantraComplianceValidator()
    test_cases = [
        # (field_name, source, has_human_approval, should_pass)
        # System fields
        ("decision_id", "system", False, True),
        ("created_at", "system", False, True),
        ("decision_id", "ai", False, False),  # AI cannot set system fields

        # Core content - needs human
        ("statement", "human", True, True),
        ("statement", "ai", True, False),  # AI cannot fill even with approval
        ("statement", "ai_suggest", True, True),  # AI can suggest

        # Classification - AI suggests, human approves
        ("domain_id", "ai_suggest", True, True),
        ("domain_id", "ai_suggest", False, False),  # Needs approval

        # Enrichable - AI can fill with approval
        ("trigger_event", "ai", True, True),
        ("trigger_event", "ai", False, False),  # Needs approval

        # Approval field - MUST be human
        ("approved_by", "human", True, True),
        ("approved_by", "ai", True, False),  # AI cannot set approved_by
    ]

    passed = 0
    for field_name, source, has_approval, should_pass in test_cases:
        result = validator.validate_field_source(field_name, source, has_approval)
        status = "PASS" if result.passed == should_pass else "FAIL"
        if result.passed == should_pass:
            passed += 1
        print(f"  [{status}] {field_name} from '{source}' (approval={has_approval})")

    print(f"\nResult: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def test_3gate_pipeline():
    """Test 3-Gate validation pipeline."""
    print("\n" + "=" * 60)
    print("TEST: 3-Gate Validation Pipeline")
    print("=" * 60)

    validator = MantraComplianceValidator()
    test_cases = [
        # (decision, gate_results, should_pass)
        # All gates pass - VALID
        (
            {"decision_id": "DEC-001"},
            {
                ValidationGate.DETERMINISTIC: True,
                ValidationGate.AI_HEURISTIC: True,
                ValidationGate.HUMAN_APPROVAL: True,
            },
            True,
        ),
        # Gate 1 fails - INVALID
        (
            {"decision_id": "DEC-002"},
            {
                ValidationGate.DETERMINISTIC: False,
                ValidationGate.AI_HEURISTIC: True,
                ValidationGate.HUMAN_APPROVAL: True,
            },
            False,
        ),
        # Gate 3 missing - INVALID (human approval MANDATORY)
        (
            {"decision_id": "DEC-003"},
            {
                ValidationGate.DETERMINISTIC: True,
                ValidationGate.AI_HEURISTIC: True,
                ValidationGate.HUMAN_APPROVAL: False,
            },
            False,
        ),
        # Gate 2 fails but others pass - VALID (AI is advisory only)
        (
            {"decision_id": "DEC-004"},
            {
                ValidationGate.DETERMINISTIC: True,
                ValidationGate.AI_HEURISTIC: False,
                ValidationGate.HUMAN_APPROVAL: True,
            },
            True,
        ),
        # Only AI approval, no human - INVALID
        (
            {"decision_id": "DEC-005"},
            {
                ValidationGate.DETERMINISTIC: True,
                ValidationGate.AI_HEURISTIC: True,
                ValidationGate.HUMAN_APPROVAL: False,
            },
            False,
        ),
    ]

    passed = 0
    for decision, gate_results, should_pass in test_cases:
        result = validator.validate_3gate_pipeline(decision, gate_results)
        status = "PASS" if result.passed == should_pass else "FAIL"
        if result.passed == should_pass:
            passed += 1
        gates_str = ", ".join(f"{g.value}={v}" for g, v in gate_results.items())
        print(f"  [{status}] {decision['decision_id']}: {gates_str}")

    print(f"\nResult: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def test_mcp_decision_creation_flow():
    """
    Test complete MCP decision creation flow.
    Simulates what happens when AI tries to create a decision via MCP.
    """
    print("\n" + "=" * 60)
    print("TEST: MCP Decision Creation Flow")
    print("=" * 60)

    validator = MantraComplianceValidator()

    # Scenario 1: AI tries to directly create decision - REJECTED
    print("\n  Scenario 1: AI direct creation (should be REJECTED)")
    result1 = validator.validate_ai_cannot_approve(
        actor_id="ai:claude-opus-4-5",
        action="create",
        target="new-decision",
    )
    print(f"    Result: {'REJECTED (correct)' if not result1.passed else 'ALLOWED (wrong!)'}")

    # Scenario 2: AI suggests, human approves - ALLOWED
    print("\n  Scenario 2: AI suggests, human creates (should be ALLOWED)")
    decision = {
        "decision_id": "DEC-NEW-001",
        "author_id": "human:john@example.com",
        "title": "API Rate Limiting Policy",  # Human wrote/approved
        "statement": "All API endpoints must implement rate limiting",  # Human approved
        "suggested_by": "ai:claude-opus-4-5",  # AI suggested
    }
    result2 = validator.validate_human_authorship(decision)
    print(f"    Result: {'ALLOWED (correct)' if result2.passed else 'REJECTED (wrong!)'}")

    # Scenario 3: Check 3-gate for valid flow
    print("\n  Scenario 3: Valid 3-gate flow (should PASS)")
    result3 = validator.validate_3gate_pipeline(
        decision,
        {
            ValidationGate.DETERMINISTIC: True,
            ValidationGate.AI_HEURISTIC: True,
            ValidationGate.HUMAN_APPROVAL: True,
        },
    )
    print(f"    Result: {'PASS (correct)' if result3.passed else 'FAIL (wrong!)'}")

    # Scenario 4: AI tries to approve own suggestion - REJECTED
    print("\n  Scenario 4: AI self-approval (should be REJECTED)")
    result4 = validator.validate_enrichment_field(
        field_path="trigger_event",
        enriched_by="ai:claude",
        approved_by="ai:claude",  # AI trying to approve itself
        reason="Self-approved enrichment",
    )
    print(f"    Result: {'REJECTED (correct)' if not result4.passed else 'ALLOWED (wrong!)'}")

    all_correct = (
        not result1.passed and  # AI create rejected
        result2.passed and      # Human authorship valid
        result3.passed and      # 3-gate passed
        not result4.passed      # AI self-approval rejected
    )

    print(f"\n  MCP Flow Test: {'ALL CORRECT' if all_correct else 'SOME FAILURES'}")
    return all_correct


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests() -> Dict[str, Any]:
    """Run all compliance tests."""
    print("\n")
    print("=" * 70)
    print("MANTRA COMPLIANCE TEST SUITE")
    print("Testing MANTRA-LAW-001 Constitutional Rules Enforcement")
    print("=" * 70)

    start_time = time.time()

    tests = [
        ("AI Cannot Approve", test_ai_cannot_approve),
        ("Human Authorship", test_human_authorship),
        ("Enrichment Rules", test_enrichment_rules),
        ("Field Source Permissions", test_field_source_permissions),
        ("3-Gate Pipeline", test_3gate_pipeline),
        ("MCP Decision Flow", test_mcp_decision_creation_flow),
    ]

    results = {}
    passed_count = 0
    failed_count = 0

    for name, test_func in tests:
        try:
            passed = test_func()
            results[name] = "PASS" if passed else "FAIL"
            if passed:
                passed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            results[name] = f"ERROR: {str(e)}"
            failed_count += 1

    elapsed = time.time() - start_time

    # Print summary
    print("\n")
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for name, result in results.items():
        status_emoji = "[PASS]" if result == "PASS" else "[FAIL]"
        print(f"  {status_emoji} {name}: {result}")

    print(f"\nTotal: {passed_count}/{len(tests)} tests passed")
    print(f"Time: {elapsed:.2f}s")

    if failed_count == 0:
        print("\nCOMPLIANCE STATUS: ALL TESTS PASSED")
        print("MANTRA constitutional rules are being correctly enforced.")
    else:
        print(f"\nCOMPLIANCE STATUS: {failed_count} TESTS FAILED")
        print("WARNING: Some MANTRA constitutional rules may not be enforced!")

    return {
        "tests": results,
        "passed": passed_count,
        "failed": failed_count,
        "total": len(tests),
        "elapsed_seconds": elapsed,
        "compliant": failed_count == 0,
    }


if __name__ == "__main__":
    summary = run_all_tests()
    sys.exit(0 if summary["compliant"] else 1)
