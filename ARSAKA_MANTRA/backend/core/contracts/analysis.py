"""
Analysis Module Contract

Defines the interface for conflict detection and impact analysis.
Teams implementing analysis must conform to this contract.

Owner: Analysis & Intelligence Team
Dependencies: Domain models, retrieval service
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from enum import Enum


# =============================================================================
# DATA TRANSFER OBJECTS
# =============================================================================

class ConflictType(str, Enum):
    """Type of conflict between decisions."""
    DIRECT = "direct"               # Explicit contradiction
    INDIRECT = "indirect"           # Implicit through dependencies
    SCOPE_OVERLAP = "scope_overlap" # Same scope, different rules
    CONSTRAINT = "constraint"       # Constraint conflicts
    TEMPORAL = "temporal"           # Time-based conflict


class ConflictSeverity(str, Enum):
    """Severity of the conflict."""
    CRITICAL = "critical"   # Must be resolved before storing
    WARNING = "warning"     # Should review but can proceed
    INFO = "info"           # Informational only


class ImpactScope(str, Enum):
    """Scope of impact."""
    LOCAL = "local"               # Single component
    MODULE = "module"             # Multiple components in module
    SERVICE = "service"           # Entire service
    CROSS_SERVICE = "cross_service"  # Multiple services
    PLATFORM = "platform"         # Platform-wide


@dataclass
class ConflictResult:
    """Result of conflict detection."""
    has_conflicts: bool
    conflicts: List["Conflict"] = field(default_factory=list)
    warnings: List["Conflict"] = field(default_factory=list)
    analysis_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_conflicts": self.has_conflicts,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "warnings": [w.to_dict() for w in self.warnings],
            "analysis_time_ms": self.analysis_time_ms,
        }


@dataclass
class Conflict:
    """A detected conflict between two decisions."""
    decision_a_id: str
    decision_a_code: str
    decision_b_id: str
    decision_b_code: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    description: str
    resolution_suggestion: Optional[str] = None
    conflicting_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_a_id": self.decision_a_id,
            "decision_a_code": self.decision_a_code,
            "decision_b_id": self.decision_b_id,
            "decision_b_code": self.decision_b_code,
            "conflict_type": self.conflict_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "resolution_suggestion": self.resolution_suggestion,
            "conflicting_fields": self.conflicting_fields,
        }


@dataclass
class ImpactResult:
    """Result of impact analysis."""
    decision_id: str
    impact_scope: ImpactScope
    affected_decisions: List["AffectedDecision"] = field(default_factory=list)
    affected_components: List[str] = field(default_factory=list)
    risk_factors: List["RiskFactor"] = field(default_factory=list)
    mitigation_suggestions: List[str] = field(default_factory=list)
    overall_risk_score: float = 0.0
    analysis_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "impact_scope": self.impact_scope.value,
            "affected_decisions": [a.to_dict() for a in self.affected_decisions],
            "affected_components": self.affected_components,
            "risk_factors": [r.to_dict() for r in self.risk_factors],
            "mitigation_suggestions": self.mitigation_suggestions,
            "overall_risk_score": self.overall_risk_score,
            "analysis_time_ms": self.analysis_time_ms,
        }


@dataclass
class AffectedDecision:
    """A decision affected by a change."""
    decision_id: str
    decision_code: str
    relation_type: str  # depends_on, implements, extends, etc.
    impact_level: str   # direct, indirect
    requires_review: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_code": self.decision_code,
            "relation_type": self.relation_type,
            "impact_level": self.impact_level,
            "requires_review": self.requires_review,
        }


@dataclass
class RiskFactor:
    """A risk factor identified in impact analysis."""
    name: str
    description: str
    severity: str  # high, medium, low
    mitigation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
            "mitigation": self.mitigation,
        }


# =============================================================================
# CONFLICT DETECTION CONTRACT
# =============================================================================

class ConflictDetectionContract(ABC):
    """
    Conflict Detection Contract

    Responsibilities:
    - Detect conflicts between decisions
    - Identify scope overlaps
    - Find constraint contradictions
    """

    @abstractmethod
    async def detect_conflicts(
        self,
        decision: Dict[str, Any],
        existing_decisions: Optional[List[Dict[str, Any]]] = None,
    ) -> ConflictResult:
        """
        Detect conflicts for a decision against existing decisions.

        Args:
            decision: Decision to check
            existing_decisions: Optional list to check against (defaults to all)

        Returns:
            ConflictResult with any detected conflicts
        """
        pass

    @abstractmethod
    async def detect_conflicts_between(
        self,
        decision_a: Dict[str, Any],
        decision_b: Dict[str, Any],
    ) -> List[Conflict]:
        """
        Detect conflicts between two specific decisions.

        Args:
            decision_a: First decision
            decision_b: Second decision

        Returns:
            List of conflicts found
        """
        pass

    @abstractmethod
    async def get_conflicting_decisions(
        self,
        decision_id: str,
    ) -> List[str]:
        """
        Get IDs of decisions that conflict with the given decision.

        Args:
            decision_id: Decision to check

        Returns:
            List of conflicting decision IDs
        """
        pass


# =============================================================================
# IMPACT ANALYSIS CONTRACT
# =============================================================================

class ImpactAnalysisContract(ABC):
    """
    Impact Analysis Contract

    Responsibilities:
    - Analyze impact of decision changes
    - Identify affected decisions and components
    - Calculate risk scores
    """

    @abstractmethod
    async def analyze_impact(
        self,
        decision_id: str,
        change_type: str = "update",  # update, supersede, deprecate
    ) -> ImpactResult:
        """
        Analyze impact of changing a decision.

        Args:
            decision_id: Decision being changed
            change_type: Type of change

        Returns:
            ImpactResult with affected entities and risk factors
        """
        pass

    @abstractmethod
    async def analyze_new_decision_impact(
        self,
        decision: Dict[str, Any],
    ) -> ImpactResult:
        """
        Analyze impact of adding a new decision.

        Args:
            decision: New decision being added

        Returns:
            ImpactResult with potential impacts
        """
        pass

    @abstractmethod
    async def get_affected_by(
        self,
        decision_id: str,
    ) -> List[AffectedDecision]:
        """
        Get decisions affected by a change to the given decision.

        Args:
            decision_id: Decision that is changing

        Returns:
            List of affected decisions
        """
        pass

    @abstractmethod
    async def calculate_blast_radius(
        self,
        decision_id: str,
    ) -> ImpactScope:
        """
        Calculate the blast radius of a decision.

        Args:
            decision_id: Decision to analyze

        Returns:
            ImpactScope indicating the reach
        """
        pass


# =============================================================================
# COMBINED ANALYSIS CONTRACT
# =============================================================================

class AnalysisContract(ABC):
    """
    Combined Analysis Contract

    Provides unified access to conflict detection and impact analysis.

    Usage:
        analyzer = AnalysisEngine()

        # Check conflicts
        conflicts = await analyzer.check_conflicts(decision)

        # Analyze impact
        impact = await analyzer.analyze_impact(decision_id)
    """

    @property
    @abstractmethod
    def conflict_detector(self) -> ConflictDetectionContract:
        """Get conflict detection component."""
        pass

    @property
    @abstractmethod
    def impact_analyzer(self) -> ImpactAnalysisContract:
        """Get impact analysis component."""
        pass

    @abstractmethod
    async def full_analysis(
        self,
        decision: Dict[str, Any],
        check_conflicts: bool = True,
        analyze_impact: bool = True,
    ) -> Dict[str, Any]:
        """
        Run full analysis on a decision.

        Args:
            decision: Decision to analyze
            check_conflicts: Whether to check for conflicts
            analyze_impact: Whether to analyze impact

        Returns:
            Combined analysis results
        """
        pass


__all__ = [
    "ConflictType",
    "ConflictSeverity",
    "ImpactScope",
    "ConflictResult",
    "Conflict",
    "ImpactResult",
    "AffectedDecision",
    "RiskFactor",
    "ConflictDetectionContract",
    "ImpactAnalysisContract",
    "AnalysisContract",
]
