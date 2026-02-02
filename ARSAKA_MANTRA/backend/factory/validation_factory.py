"""
Validation Factory - Creates validation pipeline and approval manager instances.

Handles:
- ValidationPipeline (3-gate validation)
- HumanApprovalManager (Gate 3 workflow)

Usage:
    from factory.validation_factory import ValidationFactory

    pipeline = ValidationFactory.get_validation_pipeline()
    approval_manager = ValidationFactory.get_approval_manager()
"""

import logging
from typing import Optional, TYPE_CHECKING

from factory.base import FactoryMixin

if TYPE_CHECKING:
    from core.validation.pipeline import ValidationPipeline
    from core.validation.gate3_human_approval import HumanApprovalManager

logger = logging.getLogger(__name__)


class ValidationFactory(FactoryMixin):
    """Factory for creating validation-related instances."""

    _validation_pipeline: Optional["ValidationPipeline"] = None
    _approval_manager: Optional["HumanApprovalManager"] = None

    @classmethod
    def get_validation_pipeline(cls) -> "ValidationPipeline":
        """
        Get validation pipeline instance (singleton).

        The pipeline orchestrates the 3-gate validation process:
        - Gate 1: Deterministic validation (S-rules, D-rules)
        - Gate 2: AI heuristic validation (quality scoring)
        - Gate 3: Human approval workflow

        Returns:
            ValidationPipeline instance
        """
        if cls._validation_pipeline is None:
            from core.validation import create_pipeline
            cls._validation_pipeline = create_pipeline()
            cls.log_using("Validation", "3-Gate Pipeline")
        return cls._validation_pipeline

    @classmethod
    def get_approval_manager(cls) -> "HumanApprovalManager":
        """
        Get human approval manager instance (singleton).

        Manages the Gate 3 approval workflow:
        - Pending approvals tracking
        - Approval/rejection actions
        - Review comments

        Per MANTRA LAW §6: AI has ZERO authority for approval.

        Returns:
            HumanApprovalManager instance
        """
        if cls._approval_manager is None:
            from core.validation import create_approval_manager
            cls._approval_manager = create_approval_manager()
            cls.log_using("ApprovalManager", "HumanApproval")
        return cls._approval_manager

    @classmethod
    def reset(cls) -> None:
        """Reset all cached instances."""
        cls._validation_pipeline = None
        cls._approval_manager = None
