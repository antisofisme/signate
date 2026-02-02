"""
MANTRA Gate 3: Human Approval

HARD BLOCK - Final human authority per MANTRA-LAW-001 §6.

Per LAW §6: AI has ZERO authority for:
- Creating decisions
- Modifying decisions
- Approving decisions
- Rejecting decisions

Gate 3 ensures human approval BEFORE any decision becomes active.

APPROVAL WORKFLOW:
1. Decision submitted (status: PENDING_REVIEW)
2. Human reviewer assigned
3. Human reviews Gate 1 & Gate 2 results
4. Human approves/rejects/requests changes
5. If approved: Decision becomes ACTIVE
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
import uuid


# ============================================================================
# ENUMS
# ============================================================================

class ApprovalStatus(str, Enum):
    """Approval workflow status."""
    PENDING_REVIEW = "PENDING_REVIEW"     # Awaiting human review
    IN_REVIEW = "IN_REVIEW"               # Human is reviewing
    CHANGES_REQUESTED = "CHANGES_REQUESTED"  # Human requests changes
    APPROVED = "APPROVED"                 # Human approved
    REJECTED = "REJECTED"                 # Human rejected


class ReviewerRole(str, Enum):
    """Role of the reviewer."""
    AUTHOR = "AUTHOR"           # Original author (can't self-approve)
    PEER = "PEER"               # Peer reviewer
    LEAD = "LEAD"               # Technical lead
    ARCHITECT = "ARCHITECT"     # Architect (final authority)
    ADMIN = "ADMIN"             # System admin


class RejectionReason(str, Enum):
    """Standard rejection reasons."""
    INCOMPLETE = "INCOMPLETE"           # Missing required information
    UNCLEAR = "UNCLEAR"                 # Statement or rationale unclear
    CONFLICTS = "CONFLICTS"             # Conflicts with existing decisions
    DUPLICATE = "DUPLICATE"             # Duplicates existing decision
    OUT_OF_SCOPE = "OUT_OF_SCOPE"       # Outside decision scope
    TECHNICAL_ISSUE = "TECHNICAL_ISSUE" # Technical problems identified
    POLICY_VIOLATION = "POLICY_VIOLATION"  # Violates policies
    OTHER = "OTHER"                     # Other reason (requires comment)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ReviewComment:
    """A comment from a reviewer."""
    comment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    reviewer_id: str = ""
    reviewer_role: ReviewerRole = ReviewerRole.PEER
    comment: str = ""
    field_reference: Optional[str] = None  # Which field this relates to
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_blocking: bool = False  # Must be resolved before approval

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "reviewer_id": self.reviewer_id,
            "reviewer_role": self.reviewer_role.value,
            "comment": self.comment,
            "field_reference": self.field_reference,
            "created_at": self.created_at.isoformat(),
            "is_blocking": self.is_blocking,
        }


@dataclass
class ApprovalRequest:
    """Request for human approval."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str = ""
    decision_code: str = ""

    # Submitter
    submitted_by: str = ""
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Status
    status: ApprovalStatus = ApprovalStatus.PENDING_REVIEW

    # Assigned reviewer
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None

    # Gate results (for reviewer reference)
    gate1_passed: bool = False
    gate2_passed: bool = False
    gate1_warnings: int = 0
    gate2_warnings: int = 0

    # Review
    comments: List[ReviewComment] = field(default_factory=list)

    # Resolution
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_comment: Optional[str] = None
    rejection_reason: Optional[RejectionReason] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "decision_id": self.decision_id,
            "decision_code": self.decision_code,
            "submitted_by": self.submitted_by,
            "submitted_at": self.submitted_at.isoformat(),
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "gate1_passed": self.gate1_passed,
            "gate2_passed": self.gate2_passed,
            "gate1_warnings": self.gate1_warnings,
            "gate2_warnings": self.gate2_warnings,
            "comments": [c.to_dict() for c in self.comments],
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_comment": self.resolution_comment,
            "rejection_reason": self.rejection_reason.value if self.rejection_reason else None,
        }


@dataclass
class ApprovalResult:
    """Result of approval action."""
    success: bool
    status: ApprovalStatus
    message: str
    request_id: str = ""
    decision_id: str = ""
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status.value,
            "message": self.message,
            "request_id": self.request_id,
            "decision_id": self.decision_id,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
        }


# ============================================================================
# APPROVAL RULES
# ============================================================================

@dataclass
class ApprovalPolicy:
    """Policy for approval requirements."""
    # Minimum reviewers required
    min_reviewers: int = 1

    # Required roles (at least one from each)
    required_roles: List[List[ReviewerRole]] = field(default_factory=lambda: [
        [ReviewerRole.PEER, ReviewerRole.LEAD, ReviewerRole.ARCHITECT]
    ])

    # Self-approval allowed?
    allow_self_approval: bool = False

    # Gate requirements
    require_gate1_pass: bool = True
    require_gate2_pass: bool = False  # Gate 2 is advisory

    # Time limits (hours)
    max_review_time_hours: Optional[int] = None

    # Auto-escalation
    escalate_after_hours: Optional[int] = 48


# Default policies by impact level
DEFAULT_POLICIES = {
    "CRITICAL": ApprovalPolicy(
        min_reviewers=2,
        required_roles=[
            [ReviewerRole.LEAD, ReviewerRole.ARCHITECT],
            [ReviewerRole.PEER, ReviewerRole.LEAD, ReviewerRole.ARCHITECT],
        ],
        allow_self_approval=False,
        require_gate1_pass=True,
        require_gate2_pass=True,  # Critical decisions need Gate 2 pass
        escalate_after_hours=24,
    ),
    "IMPORTANT": ApprovalPolicy(
        min_reviewers=1,
        required_roles=[[ReviewerRole.PEER, ReviewerRole.LEAD, ReviewerRole.ARCHITECT]],
        allow_self_approval=False,
        require_gate1_pass=True,
        require_gate2_pass=False,
        escalate_after_hours=48,
    ),
    "REFERENCE": ApprovalPolicy(
        min_reviewers=1,
        required_roles=[[ReviewerRole.PEER, ReviewerRole.LEAD, ReviewerRole.ARCHITECT, ReviewerRole.AUTHOR]],
        allow_self_approval=True,  # Reference can be self-approved
        require_gate1_pass=True,
        require_gate2_pass=False,
        escalate_after_hours=72,
    ),
}


# ============================================================================
# HUMAN APPROVAL MANAGER
# ============================================================================

class HumanApprovalManager:
    """
    Manages human approval workflow for decisions.

    Per LAW §6: AI has ZERO authority for approval.
    This class only FACILITATES the workflow - humans make all decisions.
    """

    def __init__(
        self,
        storage: Optional[Any] = None,  # ApprovalRequestRepository
        notification_service: Optional[Any] = None,
    ):
        self.storage = storage
        self.notification_service = notification_service
        self._pending_requests: Dict[str, ApprovalRequest] = {}

    def create_request(
        self,
        decision_id: str,
        decision_code: str,
        submitted_by: str,
        impact_level: str = "IMPORTANT",
        gate1_passed: bool = False,
        gate2_passed: bool = False,
        gate1_warnings: int = 0,
        gate2_warnings: int = 0,
    ) -> ApprovalRequest:
        """
        Create a new approval request.

        Args:
            decision_id: UUID of the decision
            decision_code: Human-readable code
            submitted_by: Human who submitted
            impact_level: CRITICAL/IMPORTANT/REFERENCE
            gate1_passed: Did Gate 1 pass?
            gate2_passed: Did Gate 2 pass?
            gate1_warnings: Number of Gate 1 warnings
            gate2_warnings: Number of Gate 2 warnings

        Returns:
            ApprovalRequest for tracking
        """
        # Validate submitter is human
        if submitted_by.lower().startswith("ai:"):
            raise ValueError("AI cannot submit decisions per LAW §6")

        # Get policy for impact level
        policy = DEFAULT_POLICIES.get(impact_level, DEFAULT_POLICIES["IMPORTANT"])

        # Check Gate 1 requirement
        if policy.require_gate1_pass and not gate1_passed:
            raise ValueError("Gate 1 must pass before requesting approval")

        request = ApprovalRequest(
            decision_id=decision_id,
            decision_code=decision_code,
            submitted_by=submitted_by,
            gate1_passed=gate1_passed,
            gate2_passed=gate2_passed,
            gate1_warnings=gate1_warnings,
            gate2_warnings=gate2_warnings,
        )

        # Store request
        self._pending_requests[request.request_id] = request

        # Notify if service available
        if self.notification_service:
            self.notification_service.notify_new_approval_request(request)

        return request

    def assign_reviewer(
        self,
        request_id: str,
        reviewer_id: str,
        reviewer_role: ReviewerRole,
        assigned_by: str,
    ) -> ApprovalRequest:
        """
        Assign a reviewer to an approval request.

        Args:
            request_id: The approval request ID
            reviewer_id: Human reviewer to assign
            reviewer_role: Role of the reviewer
            assigned_by: Human who made the assignment

        Returns:
            Updated ApprovalRequest
        """
        if reviewer_id.lower().startswith("ai:"):
            raise ValueError("AI cannot be assigned as reviewer per LAW §6")

        if assigned_by.lower().startswith("ai:"):
            raise ValueError("AI cannot assign reviewers per LAW §6")

        request = self._get_request(request_id)

        request.assigned_to = reviewer_id
        request.assigned_at = datetime.now(timezone.utc)
        request.status = ApprovalStatus.IN_REVIEW

        return request

    def add_comment(
        self,
        request_id: str,
        reviewer_id: str,
        reviewer_role: ReviewerRole,
        comment: str,
        field_reference: Optional[str] = None,
        is_blocking: bool = False,
    ) -> ReviewComment:
        """
        Add a review comment.

        Args:
            request_id: The approval request ID
            reviewer_id: Human reviewer
            reviewer_role: Role of the reviewer
            comment: The comment text
            field_reference: Which field this relates to
            is_blocking: Must be resolved before approval

        Returns:
            The created ReviewComment
        """
        if reviewer_id.lower().startswith("ai:"):
            raise ValueError("AI cannot add review comments per LAW §6")

        request = self._get_request(request_id)

        review_comment = ReviewComment(
            reviewer_id=reviewer_id,
            reviewer_role=reviewer_role,
            comment=comment,
            field_reference=field_reference,
            is_blocking=is_blocking,
        )

        request.comments.append(review_comment)

        return review_comment

    def request_changes(
        self,
        request_id: str,
        reviewer_id: str,
        reviewer_role: ReviewerRole,
        comment: str,
    ) -> ApprovalResult:
        """
        Request changes to the decision.

        Args:
            request_id: The approval request ID
            reviewer_id: Human reviewer
            reviewer_role: Role of the reviewer
            comment: What changes are needed

        Returns:
            ApprovalResult
        """
        if reviewer_id.lower().startswith("ai:"):
            raise ValueError("AI cannot request changes per LAW §6")

        request = self._get_request(request_id)

        # Add blocking comment
        self.add_comment(
            request_id=request_id,
            reviewer_id=reviewer_id,
            reviewer_role=reviewer_role,
            comment=comment,
            is_blocking=True,
        )

        request.status = ApprovalStatus.CHANGES_REQUESTED

        return ApprovalResult(
            success=True,
            status=ApprovalStatus.CHANGES_REQUESTED,
            message="Changes requested",
            request_id=request_id,
            decision_id=request.decision_id,
        )

    def approve(
        self,
        request_id: str,
        approver_id: str,
        approver_role: ReviewerRole,
        comment: Optional[str] = None,
        impact_level: str = "IMPORTANT",
    ) -> ApprovalResult:
        """
        Approve the decision.

        THIS IS THE CRITICAL FUNCTION - Only humans can call this.

        Args:
            request_id: The approval request ID
            approver_id: Human approver
            approver_role: Role of the approver
            comment: Optional approval comment
            impact_level: Decision impact level

        Returns:
            ApprovalResult
        """
        # CRITICAL: Validate approver is human
        if approver_id.lower().startswith("ai:"):
            raise ValueError(
                "AI CANNOT approve decisions per MANTRA-LAW-001 §6. "
                "AI has ZERO authority for approval."
            )

        request = self._get_request(request_id)
        policy = DEFAULT_POLICIES.get(impact_level, DEFAULT_POLICIES["IMPORTANT"])

        # Check self-approval
        if not policy.allow_self_approval and approver_id == request.submitted_by:
            return ApprovalResult(
                success=False,
                status=request.status,
                message="Self-approval not allowed for this impact level",
                request_id=request_id,
                decision_id=request.decision_id,
            )

        # Check Gate 2 requirement for CRITICAL
        if policy.require_gate2_pass and not request.gate2_passed:
            return ApprovalResult(
                success=False,
                status=request.status,
                message="Gate 2 must pass for CRITICAL decisions",
                request_id=request_id,
                decision_id=request.decision_id,
            )

        # Check no blocking comments unresolved
        blocking_comments = [c for c in request.comments if c.is_blocking]
        if blocking_comments:
            return ApprovalResult(
                success=False,
                status=request.status,
                message=f"{len(blocking_comments)} blocking comments must be resolved",
                request_id=request_id,
                decision_id=request.decision_id,
            )

        # All checks passed - APPROVE
        now = datetime.now(timezone.utc)

        request.status = ApprovalStatus.APPROVED
        request.resolved_by = approver_id
        request.resolved_at = now
        request.resolution_comment = comment

        # Add approval comment
        self.add_comment(
            request_id=request_id,
            reviewer_id=approver_id,
            reviewer_role=approver_role,
            comment=comment or "Approved",
            is_blocking=False,
        )

        return ApprovalResult(
            success=True,
            status=ApprovalStatus.APPROVED,
            message="Decision approved",
            request_id=request_id,
            decision_id=request.decision_id,
            approved_by=approver_id,
            approved_at=now,
        )

    def reject(
        self,
        request_id: str,
        rejector_id: str,
        rejector_role: ReviewerRole,
        reason: RejectionReason,
        comment: str,
    ) -> ApprovalResult:
        """
        Reject the decision.

        Args:
            request_id: The approval request ID
            rejector_id: Human rejector
            rejector_role: Role of the rejector
            reason: Standard rejection reason
            comment: Detailed explanation

        Returns:
            ApprovalResult
        """
        if rejector_id.lower().startswith("ai:"):
            raise ValueError("AI cannot reject decisions per LAW §6")

        request = self._get_request(request_id)

        now = datetime.now(timezone.utc)

        request.status = ApprovalStatus.REJECTED
        request.resolved_by = rejector_id
        request.resolved_at = now
        request.resolution_comment = comment
        request.rejection_reason = reason

        # Add rejection comment
        self.add_comment(
            request_id=request_id,
            reviewer_id=rejector_id,
            reviewer_role=rejector_role,
            comment=f"REJECTED ({reason.value}): {comment}",
            is_blocking=True,
        )

        return ApprovalResult(
            success=True,
            status=ApprovalStatus.REJECTED,
            message=f"Decision rejected: {reason.value}",
            request_id=request_id,
            decision_id=request.decision_id,
        )

    def get_pending_requests(
        self,
        reviewer_id: Optional[str] = None,
    ) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        pending = [
            r for r in self._pending_requests.values()
            if r.status in [ApprovalStatus.PENDING_REVIEW, ApprovalStatus.IN_REVIEW]
        ]

        if reviewer_id:
            pending = [r for r in pending if r.assigned_to == reviewer_id]

        return sorted(pending, key=lambda r: r.submitted_at)

    def get_request_status(self, request_id: str) -> ApprovalRequest:
        """Get status of an approval request."""
        return self._get_request(request_id)

    def _get_request(self, request_id: str) -> ApprovalRequest:
        """Get request or raise error."""
        if request_id not in self._pending_requests:
            raise ValueError(f"Approval request not found: {request_id}")
        return self._pending_requests[request_id]


# ============================================================================
# GATE 3 VALIDATOR
# ============================================================================

@dataclass
class Gate3Result:
    """Result of Gate 3 validation."""
    can_activate: bool
    status: ApprovalStatus
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    message: str = ""
    request_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "can_activate": self.can_activate,
            "status": self.status.value,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "message": self.message,
            "request_id": self.request_id,
        }


class Gate3Validator:
    """
    Gate 3: Human Approval Validation

    Checks if a decision has been properly approved by a human.
    Does NOT perform approval - only validates approval status.
    """

    def __init__(self, approval_manager: HumanApprovalManager):
        self.approval_manager = approval_manager

    def validate(self, decision_id: str) -> Gate3Result:
        """
        Validate that a decision has human approval.

        Args:
            decision_id: The decision to check

        Returns:
            Gate3Result indicating if decision can be activated
        """
        # Find approval request for this decision
        for request in self.approval_manager._pending_requests.values():
            if request.decision_id == decision_id:
                if request.status == ApprovalStatus.APPROVED:
                    return Gate3Result(
                        can_activate=True,
                        status=ApprovalStatus.APPROVED,
                        approved_by=request.resolved_by,
                        approved_at=request.resolved_at,
                        message="Human approval confirmed",
                        request_id=request.request_id,
                    )
                else:
                    return Gate3Result(
                        can_activate=False,
                        status=request.status,
                        message=f"Decision status: {request.status.value}",
                        request_id=request.request_id,
                    )

        # No approval request found
        return Gate3Result(
            can_activate=False,
            status=ApprovalStatus.PENDING_REVIEW,
            message="No approval request found - human approval required",
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_approval_manager() -> HumanApprovalManager:
    """Create a new approval manager instance."""
    return HumanApprovalManager()


def validate_gate3(
    decision_id: str,
    approval_manager: HumanApprovalManager,
) -> Gate3Result:
    """
    Validate Gate 3 (human approval) for a decision.

    Args:
        decision_id: The decision to check
        approval_manager: The approval manager instance

    Returns:
        Gate3Result indicating approval status
    """
    validator = Gate3Validator(approval_manager)
    return validator.validate(decision_id)


__all__ = [
    # Enums
    "ApprovalStatus",
    "ReviewerRole",
    "RejectionReason",
    # Data structures
    "ReviewComment",
    "ApprovalRequest",
    "ApprovalResult",
    "ApprovalPolicy",
    "Gate3Result",
    # Manager
    "HumanApprovalManager",
    "Gate3Validator",
    # Defaults
    "DEFAULT_POLICIES",
    # Functions
    "create_approval_manager",
    "validate_gate3",
]
