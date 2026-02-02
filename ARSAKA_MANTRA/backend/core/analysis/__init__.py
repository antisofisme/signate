"""
MANTRA Analysis Module

Field-level analysis tools:
- Conflict Detection: Find MUST vs MUST_NOT, strengthens, weakens
- Impact Analysis: What breaks if I change X?
"""

from .conflict_detector import (
    ConflictSeverity,
    DetectedConflict,
    ConflictDetectionResult,
    FieldConflictDetector,
    detect_conflicts_for_decision,
)

from .impact_analyzer import (
    ImpactType,
    ImpactSeverity,
    ImpactedField,
    ImpactAnalysisResult,
    ImpactAnalyzer,
    analyze_field_impact,
    analyze_deprecation_impact,
)

__all__ = [
    # Conflict Detection
    "ConflictSeverity",
    "DetectedConflict",
    "ConflictDetectionResult",
    "FieldConflictDetector",
    "detect_conflicts_for_decision",
    # Impact Analysis
    "ImpactType",
    "ImpactSeverity",
    "ImpactedField",
    "ImpactAnalysisResult",
    "ImpactAnalyzer",
    "analyze_field_impact",
    "analyze_deprecation_impact",
]
