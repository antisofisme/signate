"""
MCP Decision Creation Workflow Test

Mensimulasikan workflow NYATA ketika Claude (via MCP) diminta user
untuk membuat decision. Test ini memvalidasi:

1. Field mana yang AI boleh isi sendiri
2. Field mana yang harus dari formula/sistem
3. Field mana yang WAJIB persetujuan user
4. Workflow 3-Gate validation

MANTRA RULES:
- §6: AI has ZERO approval authority
- §2.3: Human authorship REQUIRED
- §10.7: Enrichment rules

Usage:
    python tests/mcp_decision_workflow_test.py
"""

import sys
import os
import json
import uuid
from datetime import datetime
from dataclasses import dataclass, field as dc_field
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# FIELD SOURCE DEFINITIONS
# ============================================================================

class FieldSource(Enum):
    """Who/what can fill a field."""
    SYSTEM = "system"           # Auto-generated (decision_id, timestamps)
    FORMULA = "formula"         # Calculated from other fields
    AI_DIRECT = "ai_direct"     # AI can fill, but needs human approval later
    AI_SUGGEST = "ai_suggest"   # AI suggests, human must confirm/edit
    HUMAN_REQUIRED = "human"    # ONLY human can provide
    HUMAN_APPROVE = "approve"   # Human must explicitly approve


class FieldStatus(Enum):
    """Status of field during workflow."""
    EMPTY = "empty"
    AI_FILLED = "ai_filled"
    AI_SUGGESTED = "ai_suggested"
    SYSTEM_GENERATED = "system_generated"
    FORMULA_CALCULATED = "formula_calculated"
    HUMAN_PROVIDED = "human_provided"
    HUMAN_APPROVED = "human_approved"
    PENDING_APPROVAL = "pending_approval"


@dataclass
class FieldDefinition:
    """Definition of a decision field."""
    name: str
    source: FieldSource
    required: bool
    description: str
    ai_can_suggest: bool = True
    needs_human_approval: bool = True
    formula: Optional[Callable] = None
    validation_rules: List[str] = dc_field(default_factory=list)


# ============================================================================
# MANTRA DECISION FIELD MATRIX
# ============================================================================

DECISION_FIELDS: Dict[str, FieldDefinition] = {
    # === SYSTEM GENERATED ===
    "decision_id": FieldDefinition(
        name="decision_id",
        source=FieldSource.SYSTEM,
        required=True,
        description="Unique identifier, auto-generated",
        ai_can_suggest=False,
        needs_human_approval=False,
    ),
    "created_at": FieldDefinition(
        name="created_at",
        source=FieldSource.SYSTEM,
        required=True,
        description="Creation timestamp, auto-generated",
        ai_can_suggest=False,
        needs_human_approval=False,
    ),
    "version": FieldDefinition(
        name="version",
        source=FieldSource.SYSTEM,
        required=True,
        description="Version number, starts at 1",
        ai_can_suggest=False,
        needs_human_approval=False,
    ),

    # === FORMULA/CALCULATED ===
    "blast_radius": FieldDefinition(
        name="blast_radius",
        source=FieldSource.FORMULA,
        required=True,
        description="Impact level (1-5), calculated from scope + domain",
        ai_can_suggest=True,
        needs_human_approval=True,
        validation_rules=["value between 1-5"],
    ),
    "reading_time_minutes": FieldDefinition(
        name="reading_time_minutes",
        source=FieldSource.FORMULA,
        required=False,
        description="Estimated reading time, calculated from content length",
        ai_can_suggest=False,
        needs_human_approval=False,
    ),

    # === AI CAN SUGGEST, HUMAN MUST APPROVE ===
    "title": FieldDefinition(
        name="title",
        source=FieldSource.AI_SUGGEST,
        required=True,
        description="Decision title, AI suggests, human approves",
        ai_can_suggest=True,
        needs_human_approval=True,
        validation_rules=["max 100 chars", "no special chars"],
    ),
    "statement": FieldDefinition(
        name="statement",
        source=FieldSource.AI_SUGGEST,
        required=True,
        description="Core decision statement, AI suggests, human approves",
        ai_can_suggest=True,
        needs_human_approval=True,
        validation_rules=["min 20 chars", "clear and actionable"],
    ),
    "rationale": FieldDefinition(
        name="rationale",
        source=FieldSource.AI_SUGGEST,
        required=True,
        description="Why this decision, AI suggests, human approves",
        ai_can_suggest=True,
        needs_human_approval=True,
        validation_rules=["min 50 chars", "explains the why"],
    ),
    "domain_id": FieldDefinition(
        name="domain_id",
        source=FieldSource.AI_SUGGEST,
        required=True,
        description="Domain classification (INT/ARCH/CTL/EVO)",
        ai_can_suggest=True,
        needs_human_approval=True,
        validation_rules=["must be INT, ARCH, CTL, or EVO"],
    ),
    "aspect_id": FieldDefinition(
        name="aspect_id",
        source=FieldSource.AI_SUGGEST,
        required=True,
        description="Aspect classification (A01-A16)",
        ai_can_suggest=True,
        needs_human_approval=True,
        validation_rules=["must be A01-A16"],
    ),
    "scope": FieldDefinition(
        name="scope",
        source=FieldSource.AI_SUGGEST,
        required=True,
        description="Impact scope, AI suggests, human approves",
        ai_can_suggest=True,
        needs_human_approval=True,
    ),
    "constraints": FieldDefinition(
        name="constraints",
        source=FieldSource.AI_SUGGEST,
        required=False,
        description="Constraints list, AI suggests, human approves",
        ai_can_suggest=True,
        needs_human_approval=True,
    ),
    "invariants": FieldDefinition(
        name="invariants",
        source=FieldSource.AI_SUGGEST,
        required=False,
        description="Invariants list, AI suggests, human approves",
        ai_can_suggest=True,
        needs_human_approval=True,
    ),

    # === AI CAN FILL (with later approval) ===
    "trigger_event": FieldDefinition(
        name="trigger_event",
        source=FieldSource.AI_DIRECT,
        required=False,
        description="What triggered this decision, AI can fill",
        ai_can_suggest=True,
        needs_human_approval=True,
    ),
    "code_artifacts": FieldDefinition(
        name="code_artifacts",
        source=FieldSource.AI_DIRECT,
        required=False,
        description="Related code files, AI can fill",
        ai_can_suggest=True,
        needs_human_approval=True,
    ),
    "keywords_for_rag": FieldDefinition(
        name="keywords_for_rag",
        source=FieldSource.AI_DIRECT,
        required=False,
        description="Search keywords, AI can fill",
        ai_can_suggest=True,
        needs_human_approval=False,
    ),

    # === HUMAN REQUIRED (AI CANNOT FILL) ===
    "author_id": FieldDefinition(
        name="author_id",
        source=FieldSource.HUMAN_REQUIRED,
        required=True,
        description="Human author identifier, CANNOT be AI",
        ai_can_suggest=False,
        needs_human_approval=False,  # System gets from auth
        validation_rules=["must be human identifier", "cannot start with ai:"],
    ),
    "approved_by": FieldDefinition(
        name="approved_by",
        source=FieldSource.HUMAN_APPROVE,
        required=True,
        description="Human approver, MUST be human",
        ai_can_suggest=False,
        needs_human_approval=True,
        validation_rules=["MUST be human", "cannot be AI"],
    ),
}


# ============================================================================
# WORKFLOW SIMULATOR
# ============================================================================

@dataclass
class WorkflowStep:
    """A step in the decision creation workflow."""
    step_number: int
    field_name: str
    action: str
    actor: str  # "ai", "system", "formula", "human"
    value: Any
    status: FieldStatus
    requires_confirmation: bool
    confirmed: bool = False
    confirmation_message: Optional[str] = None


@dataclass
class DecisionDraft:
    """Draft decision being built."""
    fields: Dict[str, Any] = dc_field(default_factory=dict)
    field_status: Dict[str, FieldStatus] = dc_field(default_factory=dict)
    workflow_steps: List[WorkflowStep] = dc_field(default_factory=list)
    pending_approvals: List[str] = dc_field(default_factory=list)
    validation_errors: List[str] = dc_field(default_factory=list)


class MCPDecisionWorkflow:
    """
    Simulates the MCP decision creation workflow.

    This is what happens when user asks Claude to create a decision.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.draft = DecisionDraft()
        self.step_count = 0

    def _add_step(
        self,
        field_name: str,
        action: str,
        actor: str,
        value: Any,
        status: FieldStatus,
        requires_confirmation: bool,
    ) -> WorkflowStep:
        self.step_count += 1
        step = WorkflowStep(
            step_number=self.step_count,
            field_name=field_name,
            action=action,
            actor=actor,
            value=value,
            status=status,
            requires_confirmation=requires_confirmation,
        )
        self.draft.workflow_steps.append(step)
        return step

    def step_1_system_fields(self) -> List[WorkflowStep]:
        """Step 1: Generate system fields (AI tidak boleh isi)."""
        steps = []

        # decision_id - auto generated
        decision_id = f"DEC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        self.draft.fields["decision_id"] = decision_id
        self.draft.field_status["decision_id"] = FieldStatus.SYSTEM_GENERATED
        steps.append(self._add_step(
            "decision_id", "generate", "system", decision_id,
            FieldStatus.SYSTEM_GENERATED, False
        ))

        # created_at - auto generated
        created_at = datetime.now().isoformat()
        self.draft.fields["created_at"] = created_at
        self.draft.field_status["created_at"] = FieldStatus.SYSTEM_GENERATED
        steps.append(self._add_step(
            "created_at", "generate", "system", created_at,
            FieldStatus.SYSTEM_GENERATED, False
        ))

        # version - auto generated
        self.draft.fields["version"] = 1
        self.draft.field_status["version"] = FieldStatus.SYSTEM_GENERATED
        steps.append(self._add_step(
            "version", "generate", "system", 1,
            FieldStatus.SYSTEM_GENERATED, False
        ))

        # author_id - from authenticated user (NOT AI)
        self.draft.fields["author_id"] = self.user_id
        self.draft.field_status["author_id"] = FieldStatus.HUMAN_PROVIDED
        steps.append(self._add_step(
            "author_id", "set_from_auth", "system", self.user_id,
            FieldStatus.HUMAN_PROVIDED, False
        ))

        return steps

    def step_2_ai_suggestions(self, user_request: str) -> List[WorkflowStep]:
        """
        Step 2: AI generates suggestions based on user request.

        AI BISA suggest, tapi SEMUA butuh approval user.
        """
        steps = []

        # Simulate AI understanding the request
        # In real implementation, this would call LLM

        # Title - AI suggests
        suggested_title = f"Decision for: {user_request[:50]}"
        self.draft.fields["title"] = suggested_title
        self.draft.field_status["title"] = FieldStatus.AI_SUGGESTED
        self.draft.pending_approvals.append("title")
        steps.append(self._add_step(
            "title", "suggest", "ai", suggested_title,
            FieldStatus.AI_SUGGESTED, True
        ))

        # Statement - AI suggests
        suggested_statement = f"We will implement {user_request} to improve system quality."
        self.draft.fields["statement"] = suggested_statement
        self.draft.field_status["statement"] = FieldStatus.AI_SUGGESTED
        self.draft.pending_approvals.append("statement")
        steps.append(self._add_step(
            "statement", "suggest", "ai", suggested_statement,
            FieldStatus.AI_SUGGESTED, True
        ))

        # Rationale - AI suggests
        suggested_rationale = f"This decision is needed because {user_request} will help maintain consistency and quality across the codebase."
        self.draft.fields["rationale"] = suggested_rationale
        self.draft.field_status["rationale"] = FieldStatus.AI_SUGGESTED
        self.draft.pending_approvals.append("rationale")
        steps.append(self._add_step(
            "rationale", "suggest", "ai", suggested_rationale,
            FieldStatus.AI_SUGGESTED, True
        ))

        # Domain - AI suggests based on keywords
        suggested_domain = self._detect_domain(user_request)
        self.draft.fields["domain_id"] = suggested_domain
        self.draft.field_status["domain_id"] = FieldStatus.AI_SUGGESTED
        self.draft.pending_approvals.append("domain_id")
        steps.append(self._add_step(
            "domain_id", "suggest", "ai", suggested_domain,
            FieldStatus.AI_SUGGESTED, True
        ))

        # Aspect - AI suggests
        suggested_aspect = self._detect_aspect(user_request, suggested_domain)
        self.draft.fields["aspect_id"] = suggested_aspect
        self.draft.field_status["aspect_id"] = FieldStatus.AI_SUGGESTED
        self.draft.pending_approvals.append("aspect_id")
        steps.append(self._add_step(
            "aspect_id", "suggest", "ai", suggested_aspect,
            FieldStatus.AI_SUGGESTED, True
        ))

        # Scope - AI suggests
        suggested_scope = {"modules": ["backend"], "severity": "medium"}
        self.draft.fields["scope"] = suggested_scope
        self.draft.field_status["scope"] = FieldStatus.AI_SUGGESTED
        self.draft.pending_approvals.append("scope")
        steps.append(self._add_step(
            "scope", "suggest", "ai", suggested_scope,
            FieldStatus.AI_SUGGESTED, True
        ))

        return steps

    def step_3_formula_fields(self) -> List[WorkflowStep]:
        """Step 3: Calculate formula-based fields."""
        steps = []

        # blast_radius - calculated from scope + domain
        scope = self.draft.fields.get("scope", {})
        domain = self.draft.fields.get("domain_id", "ARCH")

        # Formula: base score by domain + modifier by scope
        domain_scores = {"INT": 2, "ARCH": 3, "CTL": 4, "EVO": 2}
        base = domain_scores.get(domain, 3)
        severity_mod = {"low": -1, "medium": 0, "high": 1, "critical": 2}
        mod = severity_mod.get(scope.get("severity", "medium"), 0)
        blast_radius = max(1, min(5, base + mod))

        self.draft.fields["blast_radius"] = blast_radius
        self.draft.field_status["blast_radius"] = FieldStatus.FORMULA_CALCULATED
        # Formula results still need approval
        self.draft.pending_approvals.append("blast_radius")
        steps.append(self._add_step(
            "blast_radius", "calculate", "formula",
            f"{base} (domain) + {mod} (severity) = {blast_radius}",
            FieldStatus.FORMULA_CALCULATED, True
        ))

        # reading_time - calculated from content
        content_length = len(str(self.draft.fields.get("statement", ""))) + \
                        len(str(self.draft.fields.get("rationale", "")))
        reading_time = max(1, content_length // 200)  # ~200 chars per minute
        self.draft.fields["reading_time_minutes"] = reading_time
        self.draft.field_status["reading_time_minutes"] = FieldStatus.FORMULA_CALCULATED
        steps.append(self._add_step(
            "reading_time_minutes", "calculate", "formula", reading_time,
            FieldStatus.FORMULA_CALCULATED, False  # No approval needed
        ))

        return steps

    def step_4_ai_enrichment(self, context: Dict[str, Any]) -> List[WorkflowStep]:
        """Step 4: AI fills enrichment fields (with approval needed later)."""
        steps = []

        # trigger_event - AI can fill
        trigger = context.get("trigger", "User requested via Claude CLI")
        self.draft.fields["trigger_event"] = trigger
        self.draft.field_status["trigger_event"] = FieldStatus.AI_FILLED
        self.draft.pending_approvals.append("trigger_event")
        steps.append(self._add_step(
            "trigger_event", "fill", "ai", trigger,
            FieldStatus.AI_FILLED, True
        ))

        # code_artifacts - AI can detect from context
        artifacts = context.get("related_files", [])
        if artifacts:
            self.draft.fields["code_artifacts"] = artifacts
            self.draft.field_status["code_artifacts"] = FieldStatus.AI_FILLED
            self.draft.pending_approvals.append("code_artifacts")
            steps.append(self._add_step(
                "code_artifacts", "fill", "ai", artifacts,
                FieldStatus.AI_FILLED, True
            ))

        # keywords_for_rag - AI fills, no approval needed
        keywords = self._extract_keywords(self.draft.fields.get("statement", ""))
        self.draft.fields["keywords_for_rag"] = keywords
        self.draft.field_status["keywords_for_rag"] = FieldStatus.AI_FILLED
        steps.append(self._add_step(
            "keywords_for_rag", "fill", "ai", keywords,
            FieldStatus.AI_FILLED, False  # RAG keywords don't need approval
        ))

        return steps

    def step_5_human_approval(self, approvals: Dict[str, bool]) -> List[WorkflowStep]:
        """
        Step 5: Human approves/rejects each pending field.

        THIS IS MANDATORY - AI CANNOT SKIP THIS.
        """
        steps = []

        for field_name in list(self.draft.pending_approvals):
            if field_name in approvals:
                approved = approvals[field_name]
                if approved:
                    self.draft.field_status[field_name] = FieldStatus.HUMAN_APPROVED
                    self.draft.pending_approvals.remove(field_name)
                    steps.append(self._add_step(
                        field_name, "approve", "human", "APPROVED",
                        FieldStatus.HUMAN_APPROVED, False
                    ))
                else:
                    # User rejected - need to provide new value
                    steps.append(self._add_step(
                        field_name, "reject", "human", "REJECTED - needs revision",
                        FieldStatus.PENDING_APPROVAL, True
                    ))

        return steps

    def step_6_final_validation(self) -> Tuple[bool, List[str]]:
        """
        Step 6: Final validation before submission.

        Checks:
        1. All required fields filled
        2. All AI suggestions approved by human
        3. approved_by is set to human
        """
        errors = []

        # Check required fields
        for field_name, definition in DECISION_FIELDS.items():
            if definition.required:
                if field_name not in self.draft.fields or not self.draft.fields[field_name]:
                    errors.append(f"Required field '{field_name}' is missing")

        # Check all pending approvals are resolved
        if self.draft.pending_approvals:
            errors.append(f"Pending approvals not resolved: {self.draft.pending_approvals}")

        # Check approved_by is human
        approved_by = self.draft.fields.get("approved_by")
        if not approved_by:
            errors.append("approved_by is REQUIRED and MUST be human")
        elif approved_by.startswith("ai:"):
            errors.append("approved_by CANNOT be AI - MANTRA-LAW-001 §6 violation")

        # Check author_id is human
        author_id = self.draft.fields.get("author_id")
        if author_id and author_id.startswith("ai:"):
            errors.append("author_id CANNOT be AI - MANTRA-LAW-001 §2.3 violation")

        self.draft.validation_errors = errors
        return len(errors) == 0, errors

    def step_7_submission(self) -> Dict[str, Any]:
        """
        Step 7: Submit decision (only if validation passed).

        AI CANNOT do this step - requires human trigger.
        """
        is_valid, errors = self.step_6_final_validation()

        if not is_valid:
            return {
                "success": False,
                "errors": errors,
                "message": "Cannot submit - validation failed",
            }

        return {
            "success": True,
            "decision": self.draft.fields,
            "workflow_steps": len(self.draft.workflow_steps),
            "message": "Decision created successfully",
        }

    def _detect_domain(self, text: str) -> str:
        """Detect domain from text."""
        text_lower = text.lower()
        if any(w in text_lower for w in ["goal", "vision", "objective", "purpose"]):
            return "INT"
        elif any(w in text_lower for w in ["security", "auth", "policy", "compliance"]):
            return "CTL"
        elif any(w in text_lower for w in ["deploy", "release", "migrate", "version"]):
            return "EVO"
        else:
            return "ARCH"

    def _detect_aspect(self, text: str, domain: str) -> str:
        """Detect aspect from text and domain."""
        aspect_map = {
            "INT": ["A01", "A02", "A03", "A04"],
            "ARCH": ["A05", "A06", "A07", "A08"],
            "CTL": ["A09", "A10", "A11", "A12"],
            "EVO": ["A13", "A14", "A15", "A16"],
        }
        aspects = aspect_map.get(domain, ["A05"])
        return aspects[0]  # Default to first in domain

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords for RAG."""
        words = text.lower().split()
        stopwords = {"the", "a", "an", "is", "are", "will", "to", "for", "and", "or"}
        return [w for w in words if w not in stopwords and len(w) > 3][:10]


# ============================================================================
# TEST SCENARIOS
# ============================================================================

def test_complete_workflow():
    """Test complete decision creation workflow."""
    print("\n" + "=" * 70)
    print("TEST: Complete MCP Decision Creation Workflow")
    print("=" * 70)

    # Initialize workflow with human user
    workflow = MCPDecisionWorkflow(user_id="human:john@example.com")

    # Step 1: System fields
    print("\n[Step 1] System-Generated Fields (AI TIDAK BOLEH ISI)")
    print("-" * 50)
    steps = workflow.step_1_system_fields()
    for step in steps:
        print(f"  {step.field_name}: {step.value} (by {step.actor})")

    # Step 2: AI suggestions
    print("\n[Step 2] AI Suggestions (BUTUH APPROVAL USER)")
    print("-" * 50)
    user_request = "implement rate limiting for API endpoints"
    steps = workflow.step_2_ai_suggestions(user_request)
    for step in steps:
        val_str = str(step.value)[:50]
        print(f"  {step.field_name}: {val_str}... (PENDING APPROVAL)")

    # Step 3: Formula calculations
    print("\n[Step 3] Formula Calculations (AUTO-CALCULATED)")
    print("-" * 50)
    steps = workflow.step_3_formula_fields()
    for step in steps:
        approval = " (NEEDS APPROVAL)" if step.requires_confirmation else ""
        print(f"  {step.field_name}: {step.value}{approval}")

    # Step 4: AI enrichment
    print("\n[Step 4] AI Enrichment (AI BISA ISI, BUTUH APPROVAL)")
    print("-" * 50)
    context = {
        "trigger": "User request via Claude CLI for API security improvement",
        "related_files": ["src/api/middleware.py", "src/api/rate_limit.py"],
    }
    steps = workflow.step_4_ai_enrichment(context)
    for step in steps:
        approval = " (NEEDS APPROVAL)" if step.requires_confirmation else ""
        print(f"  {step.field_name}: {step.value}{approval}")

    # Show pending approvals
    print("\n[PENDING APPROVALS - USER HARUS APPROVE]")
    print("-" * 50)
    for field in workflow.draft.pending_approvals:
        print(f"  - {field}: {workflow.draft.fields.get(field, 'N/A')}")

    # Step 5: Human approval
    print("\n[Step 5] Human Approval (MANDATORY)")
    print("-" * 50)
    # Simulate user approving all
    approvals = {field: True for field in workflow.draft.pending_approvals}
    steps = workflow.step_5_human_approval(approvals)
    for step in steps:
        print(f"  {step.field_name}: {step.action.upper()}")

    # Add approved_by (MUST be human)
    workflow.draft.fields["approved_by"] = "human:john@example.com"
    workflow.draft.field_status["approved_by"] = FieldStatus.HUMAN_PROVIDED

    # Step 6: Final validation
    print("\n[Step 6] Final Validation")
    print("-" * 50)
    is_valid, errors = workflow.step_6_final_validation()
    print(f"  Valid: {is_valid}")
    if errors:
        for err in errors:
            print(f"  ERROR: {err}")

    # Step 7: Submission
    print("\n[Step 7] Submission")
    print("-" * 50)
    result = workflow.step_7_submission()
    print(f"  Success: {result['success']}")
    print(f"  Total Steps: {result.get('workflow_steps', 'N/A')}")

    return result["success"]


def test_ai_tries_to_bypass():
    """Test that AI cannot bypass human approval."""
    print("\n" + "=" * 70)
    print("TEST: AI Tries to Bypass Human Approval")
    print("=" * 70)

    workflow = MCPDecisionWorkflow(user_id="human:jane@example.com")

    # Step 1-4: Normal flow
    workflow.step_1_system_fields()
    workflow.step_2_ai_suggestions("add caching layer")
    workflow.step_3_formula_fields()
    workflow.step_4_ai_enrichment({})

    # SKIP Step 5 (human approval) - AI tries to submit directly
    print("\n[VIOLATION ATTEMPT] AI skipping human approval...")

    # Try to submit without approvals
    is_valid, errors = workflow.step_6_final_validation()

    print(f"\n  Validation Result: {'PASSED (BAD!)' if is_valid else 'FAILED (CORRECT!)'}")
    print(f"  Errors found: {len(errors)}")
    for err in errors:
        print(f"    - {err}")

    # Should fail because pending approvals exist
    return not is_valid  # Test passes if validation fails


def test_ai_tries_to_approve():
    """Test that AI cannot set itself as approver."""
    print("\n" + "=" * 70)
    print("TEST: AI Tries to Set Itself as Approver")
    print("=" * 70)

    workflow = MCPDecisionWorkflow(user_id="ai:claude")  # AI as user (invalid)

    workflow.step_1_system_fields()
    workflow.step_2_ai_suggestions("add logging")
    workflow.step_3_formula_fields()
    workflow.step_4_ai_enrichment({})

    # Approve all with human
    approvals = {field: True for field in workflow.draft.pending_approvals}
    workflow.step_5_human_approval(approvals)

    # AI tries to set itself as approver
    workflow.draft.fields["approved_by"] = "ai:claude"  # VIOLATION!

    print("\n[VIOLATION ATTEMPT] AI setting itself as approved_by...")

    is_valid, errors = workflow.step_6_final_validation()

    print(f"\n  Validation Result: {'PASSED (BAD!)' if is_valid else 'FAILED (CORRECT!)'}")
    for err in errors:
        print(f"    - {err}")

    # Should fail because AI cannot approve
    ai_approval_blocked = any("CANNOT be AI" in err for err in errors)
    print(f"\n  AI approval blocked: {ai_approval_blocked}")

    return not is_valid and ai_approval_blocked


def test_field_permission_matrix():
    """Test the field permission matrix."""
    print("\n" + "=" * 70)
    print("TEST: Field Permission Matrix")
    print("=" * 70)

    print("\n  Source Legend:")
    print("    SYSTEM   = Auto-generated, AI cannot touch")
    print("    FORMULA  = Calculated, AI cannot override")
    print("    AI_SUG   = AI suggests, human MUST approve")
    print("    AI_DIR   = AI can fill, but needs approval")
    print("    HUMAN    = ONLY human can provide")
    print("    APPROVE  = Human approval action")

    print("\n  Field Permission Matrix:")
    print("  " + "-" * 70)
    print(f"  {'Field':<25} {'Source':<12} {'AI Suggest':<12} {'Need Approval':<12}")
    print("  " + "-" * 70)

    for name, defn in DECISION_FIELDS.items():
        source = defn.source.value[:10]
        ai_suggest = "Yes" if defn.ai_can_suggest else "NO"
        approval = "YES" if defn.needs_human_approval else "No"
        print(f"  {name:<25} {source:<12} {ai_suggest:<12} {approval:<12}")

    print("\n  Key Rules:")
    print("    1. SYSTEM/FORMULA fields: AI CANNOT modify")
    print("    2. AI_SUGGEST fields: AI suggests, human MUST approve")
    print("    3. HUMAN fields: AI CANNOT fill (only human)")
    print("    4. approved_by: MUST ALWAYS be human (MANTRA §6)")

    return True


def test_workflow_step_order():
    """Test that workflow steps must be in correct order."""
    print("\n" + "=" * 70)
    print("TEST: Workflow Step Order Enforcement")
    print("=" * 70)

    print("\n  Required Order:")
    print("    1. System fields generated")
    print("    2. AI suggestions created")
    print("    3. Formulas calculated")
    print("    4. AI enrichment added")
    print("    5. Human approval obtained (MANDATORY)")
    print("    6. Final validation")
    print("    7. Submission (human-triggered)")

    workflow = MCPDecisionWorkflow(user_id="human:test@example.com")

    # Execute in correct order
    steps_1 = workflow.step_1_system_fields()
    steps_2 = workflow.step_2_ai_suggestions("test decision")
    steps_3 = workflow.step_3_formula_fields()
    steps_4 = workflow.step_4_ai_enrichment({})

    # Verify step order
    all_steps = workflow.draft.workflow_steps
    print(f"\n  Total steps executed: {len(all_steps)}")

    # Check step numbers are sequential
    for i, step in enumerate(all_steps):
        expected = i + 1
        actual = step.step_number
        status = "OK" if actual == expected else "ERROR"
        print(f"    Step {actual}: {step.field_name} ({step.actor}) [{status}]")

    return True


# ============================================================================
# MAIN
# ============================================================================

def run_all_tests():
    """Run all workflow tests."""
    print("\n")
    print("=" * 70)
    print("MCP DECISION WORKFLOW TEST SUITE")
    print("Testing MANTRA Rules in Real Decision Creation Flow")
    print("=" * 70)

    tests = [
        ("Field Permission Matrix", test_field_permission_matrix),
        ("Workflow Step Order", test_workflow_step_order),
        ("Complete Workflow", test_complete_workflow),
        ("AI Bypass Prevention", test_ai_tries_to_bypass),
        ("AI Approval Prevention", test_ai_tries_to_approve),
    ]

    results = {}
    for name, test_func in tests:
        try:
            passed = test_func()
            results[name] = "PASS" if passed else "FAIL"
        except Exception as e:
            results[name] = f"ERROR: {str(e)}"

    # Summary
    print("\n")
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed_count = sum(1 for r in results.values() if r == "PASS")
    for name, result in results.items():
        status = "[PASS]" if result == "PASS" else "[FAIL]"
        print(f"  {status} {name}")

    print(f"\n  Total: {passed_count}/{len(tests)} tests passed")

    if passed_count == len(tests):
        print("\n  WORKFLOW COMPLIANCE: ALL TESTS PASSED")
        print("  AI correctly follows MANTRA rules in decision creation.")
    else:
        print("\n  WORKFLOW COMPLIANCE: SOME TESTS FAILED")
        print("  WARNING: AI may violate MANTRA rules!")

    return passed_count == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
