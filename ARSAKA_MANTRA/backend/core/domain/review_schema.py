"""
Per-Field Review Schema for MANTRA Decisions

Memungkinkan AI mengisi semua field, lalu user review per-field:
- OK → field approved
- NO → user edit field tersebut

Workflow:
1. AI fills all fields based on context
2. Save as DRAFT with needs_review=true
3. User opens review UI
4. User clicks OK/NO per field
5. If NO → user edits that field
6. When ALL fields approved → decision finalized

MANTRA Compliance:
- AI still cannot APPROVE (only suggest)
- Human still has final say per field
- approved_by set when ALL fields reviewed
"""

from dataclasses import dataclass, field as dc_field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import uuid


class FieldReviewStatus(Enum):
    """Status review per field."""
    PENDING = "pending"          # Belum direview user
    APPROVED = "approved"        # User klik OK
    REJECTED = "rejected"        # User klik NO (perlu edit)
    EDITED = "edited"            # User sudah edit setelah reject


class FieldSource(Enum):
    """Sumber nilai field."""
    AI_SUGGESTED = "ai_suggested"    # AI yang suggest
    AI_DETECTED = "ai_detected"      # AI detect dari context
    FORMULA = "formula"              # Dari perhitungan
    SYSTEM = "system"                # Auto-generated
    HUMAN = "human"                  # User input langsung


@dataclass
class FieldReview:
    """Review status untuk satu field."""
    field_name: str
    value: Any
    source: FieldSource
    status: FieldReviewStatus = FieldReviewStatus.PENDING
    source_explanation: Optional[str] = None  # "Detected from: security keyword"
    reviewed_at: Optional[datetime] = None
    edited_value: Optional[Any] = None  # Nilai baru jika user edit
    rejection_reason: Optional[str] = None

    @property
    def final_value(self) -> Any:
        """Nilai final (edited jika ada, else original)."""
        if self.edited_value is not None:
            return self.edited_value
        return self.value

    @property
    def is_reviewed(self) -> bool:
        """Apakah field sudah direview."""
        return self.status in [
            FieldReviewStatus.APPROVED,
            FieldReviewStatus.EDITED
        ]

    def approve(self) -> None:
        """User klik OK."""
        self.status = FieldReviewStatus.APPROVED
        self.reviewed_at = datetime.now()

    def reject(self, reason: Optional[str] = None) -> None:
        """User klik NO."""
        self.status = FieldReviewStatus.REJECTED
        self.rejection_reason = reason
        self.reviewed_at = datetime.now()

    def edit(self, new_value: Any) -> None:
        """User edit setelah reject."""
        self.edited_value = new_value
        self.status = FieldReviewStatus.EDITED
        self.reviewed_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "value": self.value,
            "source": self.source.value,
            "status": self.status.value,
            "source_explanation": self.source_explanation,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "edited_value": self.edited_value,
            "final_value": self.final_value,
            "is_reviewed": self.is_reviewed,
        }


@dataclass
class DecisionDraft:
    """
    Draft decision dengan per-field review.

    Ini yang disimpan ke database saat AI create decision.
    User akan review per-field di UI.
    """
    draft_id: str
    created_at: datetime
    created_by_ai: str  # AI model yang create (e.g., "claude-opus-4-5")
    user_id: str  # User yang request
    original_request: str  # Request asli user

    # Field reviews
    fields: Dict[str, FieldReview] = dc_field(default_factory=dict)

    # Overall status
    needs_review: bool = True
    finalized: bool = False
    finalized_at: Optional[datetime] = None
    approved_by: Optional[str] = None  # Human yang finalize

    @property
    def pending_fields(self) -> List[str]:
        """Fields yang belum direview."""
        return [
            name for name, review in self.fields.items()
            if not review.is_reviewed
        ]

    @property
    def rejected_fields(self) -> List[str]:
        """Fields yang direject (perlu edit)."""
        return [
            name for name, review in self.fields.items()
            if review.status == FieldReviewStatus.REJECTED
        ]

    @property
    def all_reviewed(self) -> bool:
        """Semua field sudah direview."""
        return all(review.is_reviewed for review in self.fields.values())

    @property
    def review_progress(self) -> Dict[str, Any]:
        """Progress review."""
        total = len(self.fields)
        reviewed = sum(1 for r in self.fields.values() if r.is_reviewed)
        return {
            "total_fields": total,
            "reviewed": reviewed,
            "pending": total - reviewed,
            "percentage": int((reviewed / total) * 100) if total > 0 else 0,
        }

    def add_field(
        self,
        field_name: str,
        value: Any,
        source: FieldSource,
        explanation: Optional[str] = None,
    ) -> FieldReview:
        """Add field dengan review status PENDING."""
        review = FieldReview(
            field_name=field_name,
            value=value,
            source=source,
            source_explanation=explanation,
        )
        self.fields[field_name] = review
        return review

    def review_field(
        self,
        field_name: str,
        approved: bool,
        new_value: Optional[Any] = None,
        rejection_reason: Optional[str] = None,
    ) -> FieldReview:
        """
        Review satu field.

        Args:
            field_name: Nama field
            approved: True = OK, False = NO
            new_value: Nilai baru jika user edit (saat NO)
            rejection_reason: Alasan reject
        """
        if field_name not in self.fields:
            raise ValueError(f"Field '{field_name}' not found")

        review = self.fields[field_name]

        if approved:
            review.approve()
        else:
            review.reject(rejection_reason)
            if new_value is not None:
                review.edit(new_value)

        return review

    def finalize(self, approved_by: str) -> Dict[str, Any]:
        """
        Finalize decision setelah semua field direview.

        Args:
            approved_by: Human user yang finalize (BUKAN AI!)

        Returns:
            Final decision dict
        """
        # Check cannot be AI
        if approved_by.startswith("ai:"):
            raise ValueError("approved_by CANNOT be AI - MANTRA-LAW-001 §6")

        # Check all reviewed
        if not self.all_reviewed:
            pending = self.pending_fields
            raise ValueError(f"Cannot finalize - pending fields: {pending}")

        # Check no rejected without edit
        rejected = self.rejected_fields
        if rejected:
            raise ValueError(f"Cannot finalize - rejected fields need edit: {rejected}")

        # Build final decision
        decision = {
            "decision_id": f"DEC-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            "created_at": datetime.now().isoformat(),
            "draft_id": self.draft_id,
            "approved_by": approved_by,
            "author_id": self.user_id,
        }

        # Add all field final values
        for name, review in self.fields.items():
            decision[name] = review.final_value

        # Update draft status
        self.finalized = True
        self.finalized_at = datetime.now()
        self.approved_by = approved_by
        self.needs_review = False

        return decision

    def to_dict(self) -> Dict[str, Any]:
        return {
            "draft_id": self.draft_id,
            "created_at": self.created_at.isoformat(),
            "created_by_ai": self.created_by_ai,
            "user_id": self.user_id,
            "original_request": self.original_request,
            "needs_review": self.needs_review,
            "finalized": self.finalized,
            "review_progress": self.review_progress,
            "fields": {name: r.to_dict() for name, r in self.fields.items()},
        }


class AIDecisionDrafter:
    """
    AI creates decision draft untuk user review.

    Usage:
        drafter = AIDecisionDrafter(
            user_id="human:john@example.com",
            ai_model="claude-opus-4-5"
        )

        # AI fills semua field
        draft = drafter.create_draft(
            request="implement rate limiting for API",
            context={"files": ["api.py"], "domain_hint": "security"}
        )

        # Save draft ke DB (needs_review=true)
        save_draft(draft)

        # User review di UI...
        # draft.review_field("title", approved=True)
        # draft.review_field("domain_id", approved=False, new_value="CTL")

        # Finalize saat semua reviewed
        decision = draft.finalize(approved_by="human:john@example.com")
    """

    def __init__(self, user_id: str, ai_model: str = "claude-opus-4-5"):
        self.user_id = user_id
        self.ai_model = ai_model

    def create_draft(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> DecisionDraft:
        """
        Create decision draft dari user request.

        AI fills semua field, saved dengan needs_review=true.
        """
        context = context or {}

        draft = DecisionDraft(
            draft_id=f"DRAFT-{uuid.uuid4().hex[:8].upper()}",
            created_at=datetime.now(),
            created_by_ai=f"ai:{self.ai_model}",
            user_id=self.user_id,
            original_request=request,
        )

        # AI fills each field
        self._fill_title(draft, request)
        self._fill_statement(draft, request)
        self._fill_rationale(draft, request)
        self._fill_domain(draft, request, context)
        self._fill_aspect(draft, request, context)
        self._fill_scope(draft, request, context)
        self._fill_blast_radius(draft)
        self._fill_constraints(draft, request)
        self._fill_trigger(draft, context)
        self._fill_code_artifacts(draft, context)

        return draft

    def _fill_title(self, draft: DecisionDraft, request: str):
        title = f"Decision: {request[:60]}"
        draft.add_field(
            "title", title, FieldSource.AI_SUGGESTED,
            explanation=f"Generated from request: '{request[:30]}...'"
        )

    def _fill_statement(self, draft: DecisionDraft, request: str):
        statement = f"We will {request} to improve system quality and maintainability."
        draft.add_field(
            "statement", statement, FieldSource.AI_SUGGESTED,
            explanation="Generated based on request pattern"
        )

    def _fill_rationale(self, draft: DecisionDraft, request: str):
        rationale = (
            f"This decision is needed because {request} will help maintain "
            "consistency, improve quality, and reduce technical debt."
        )
        draft.add_field(
            "rationale", rationale, FieldSource.AI_SUGGESTED,
            explanation="Generated standard rationale pattern"
        )

    def _fill_domain(self, draft: DecisionDraft, request: str, context: Dict):
        # Detect domain
        request_lower = request.lower()

        if any(w in request_lower for w in ["goal", "vision", "purpose", "objective"]):
            domain = "INT"
            explanation = "Detected intent-related keywords"
        elif any(w in request_lower for w in ["security", "auth", "policy", "compliance", "rate limit"]):
            domain = "CTL"
            explanation = "Detected control/security keywords"
        elif any(w in request_lower for w in ["deploy", "release", "migrate", "version"]):
            domain = "EVO"
            explanation = "Detected evolution/deployment keywords"
        else:
            domain = "ARCH"
            explanation = "Default to architecture (no specific keywords detected)"

        # Override with context hint if provided
        if context.get("domain_hint"):
            domain = context["domain_hint"]
            explanation = f"Using domain hint from context"

        draft.add_field("domain_id", domain, FieldSource.AI_DETECTED, explanation)

    def _fill_aspect(self, draft: DecisionDraft, request: str, context: Dict):
        domain = draft.fields.get("domain_id")
        domain_val = domain.value if domain else "ARCH"

        aspect_map = {
            "INT": ("A02", "Objective/Goal aspect"),
            "ARCH": ("A06", "Component/Module aspect"),
            "CTL": ("A10", "Security/Auth aspect"),
            "EVO": ("A14", "Deployment/Release aspect"),
        }

        aspect, explanation = aspect_map.get(domain_val, ("A06", "Default aspect"))
        draft.add_field("aspect_id", aspect, FieldSource.AI_DETECTED, explanation)

    def _fill_scope(self, draft: DecisionDraft, request: str, context: Dict):
        # Detect scope from context
        files = context.get("files", [])
        modules = set()

        for f in files:
            if "api" in f.lower():
                modules.add("api")
            if "frontend" in f.lower() or "ui" in f.lower():
                modules.add("frontend")
            if "backend" in f.lower() or "service" in f.lower():
                modules.add("backend")
            if "db" in f.lower() or "database" in f.lower():
                modules.add("database")

        if not modules:
            modules = {"backend"}  # Default

        scope = {
            "modules": list(modules),
            "severity": "medium",
        }

        draft.add_field(
            "scope", scope, FieldSource.AI_DETECTED,
            explanation=f"Detected modules from context files: {files}"
        )

    def _fill_blast_radius(self, draft: DecisionDraft):
        # Calculate from domain + scope
        domain_field = draft.fields.get("domain_id")
        scope_field = draft.fields.get("scope")

        domain = domain_field.value if domain_field else "ARCH"
        scope = scope_field.value if scope_field else {"severity": "medium"}

        domain_scores = {"INT": 2, "ARCH": 3, "CTL": 4, "EVO": 2}
        severity_mod = {"low": -1, "medium": 0, "high": 1, "critical": 2}

        base = domain_scores.get(domain, 3)
        mod = severity_mod.get(scope.get("severity", "medium"), 0)
        blast_radius = max(1, min(5, base + mod))

        draft.add_field(
            "blast_radius", blast_radius, FieldSource.FORMULA,
            explanation=f"Formula: domain_score({base}) + severity_mod({mod}) = {blast_radius}"
        )

    def _fill_constraints(self, draft: DecisionDraft, request: str):
        # Generate basic constraints
        constraints = [
            "Must not break existing functionality",
            "Must include tests for new code",
            "Must be documented",
        ]

        draft.add_field(
            "constraints", constraints, FieldSource.AI_SUGGESTED,
            explanation="Standard constraint template"
        )

    def _fill_trigger(self, draft: DecisionDraft, context: Dict):
        trigger = context.get("trigger", "User request via Claude CLI")
        draft.add_field(
            "trigger_event", trigger, FieldSource.AI_DETECTED,
            explanation="Captured from request context"
        )

    def _fill_code_artifacts(self, draft: DecisionDraft, context: Dict):
        files = context.get("files", [])
        if files:
            draft.add_field(
                "code_artifacts", files, FieldSource.AI_DETECTED,
                explanation=f"Detected {len(files)} related files from context"
            )


# ============================================================================
# API Response Format untuk UI
# ============================================================================

def format_for_ui(draft: DecisionDraft) -> Dict[str, Any]:
    """
    Format draft untuk UI review.

    Returns struktur yang mudah di-render di frontend.
    Includes field specs for guidelines, validation, examples.
    """
    # Try to load field specs
    try:
        from core.domain.field_specs import FIELD_SPECS, FieldSpec
        has_specs = True
    except ImportError:
        FIELD_SPECS = {}
        has_specs = False

    fields_for_review = []

    for name, review in draft.fields.items():
        field_data = {
            "name": name,
            "label": name.replace("_", " ").title(),
            "value": review.value,
            "display_value": _format_display_value(review.value),
            "source": review.source.value,
            "source_label": _get_source_label(review.source),
            "source_explanation": review.source_explanation,
            "status": review.status.value,
            "status_label": _get_status_label(review.status),
            "is_reviewed": review.is_reviewed,
            "can_edit": review.source not in [FieldSource.SYSTEM, FieldSource.FORMULA],
            "edited_value": review.edited_value,
            "final_value": review.final_value,
        }

        # Add field spec info if available
        if has_specs and name in FIELD_SPECS:
            spec = FIELD_SPECS[name]
            field_data["spec"] = {
                "description": spec.description,
                "purpose": spec.purpose,
                "guidelines": spec.guidelines,
                "writing_tips": spec.writing_tips,
                "common_mistakes": spec.common_mistakes,
                "validation_rules": spec.validation_rules,
                "min_length": spec.min_length,
                "max_length": spec.max_length,
                "allowed_values": spec.allowed_values,
                "good_examples": [
                    {"value": ex.value, "explanation": ex.explanation}
                    for ex in (spec.good_examples or [])
                ],
                "bad_examples": [
                    {"value": ex.value, "explanation": ex.explanation}
                    for ex in (spec.bad_examples or [])
                ],
            }

        fields_for_review.append(field_data)

    return {
        "draft_id": draft.draft_id,
        "created_at": draft.created_at.isoformat(),
        "created_by_ai": draft.created_by_ai,
        "original_request": draft.original_request,
        "review_progress": draft.review_progress,
        "needs_review": draft.needs_review,
        "can_finalize": draft.all_reviewed and not draft.rejected_fields,
        "fields": fields_for_review,
        "pending_fields": draft.pending_fields,
        "rejected_fields": draft.rejected_fields,
    }


def _format_display_value(value: Any) -> str:
    """Format value untuk display di UI."""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, dict):
        return ", ".join(f"{k}: {v}" for k, v in value.items())
    return str(value)


def _get_source_label(source: FieldSource) -> str:
    """Human-readable source label."""
    labels = {
        FieldSource.AI_SUGGESTED: "AI Suggested",
        FieldSource.AI_DETECTED: "AI Detected",
        FieldSource.FORMULA: "Calculated",
        FieldSource.SYSTEM: "System Generated",
        FieldSource.HUMAN: "User Input",
    }
    return labels.get(source, source.value)


def _get_status_label(status: FieldReviewStatus) -> str:
    """Human-readable status label."""
    labels = {
        FieldReviewStatus.PENDING: "Pending Review",
        FieldReviewStatus.APPROVED: "Approved",
        FieldReviewStatus.REJECTED: "Rejected - Edit Required",
        FieldReviewStatus.EDITED: "Edited & Approved",
    }
    return labels.get(status, status.value)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "FieldReviewStatus",
    "FieldSource",
    "FieldReview",
    "DecisionDraft",
    "AIDecisionDrafter",
    "format_for_ui",
]
