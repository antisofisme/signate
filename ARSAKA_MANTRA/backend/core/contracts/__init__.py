"""
MANTRA API Contracts - Module Interfaces

This module defines clear interfaces (protocols) for each MANTRA module.
Teams can work independently by implementing these contracts.

Benefits:
1. Clear boundaries - Teams know their responsibility
2. No tight coupling - Modules only depend on contracts, not implementations
3. Easy testing - Mock implementations for unit tests
4. Parallel development - Teams can work simultaneously

Modules:
- Validation: 3-gate validation pipeline
- Retrieval: Search and context retrieval
- Analysis: Conflict detection, impact analysis
- Export: Document generation and integrations

Usage:
    from core.contracts import (
        ValidationContract,
        RetrievalContract,
        AnalysisContract,
        ExportContract,
    )

    # Type hint your dependencies
    def my_function(validator: ValidationContract): ...

    # Create mock implementations for testing
    class MockValidator(ValidationContract): ...
"""

from .validation import (
    ValidationContract,
    ValidationRequest,
    ValidationResponse,
    Gate1Contract,
    Gate2Contract,
    Gate3Contract,
)

from .retrieval import (
    RetrievalContract,
    RetrievalRequest,
    RetrievalResponse,
    SearchContract,
    RankerContract,
)

from .analysis import (
    AnalysisContract,
    ConflictDetectionContract,
    ImpactAnalysisContract,
    ConflictResult,
    ImpactResult,
)

from .export import (
    ExportContract,
    DocumentGeneratorContract,
    ExportRequest,
    ExportResult,
)

__all__ = [
    # Validation
    "ValidationContract",
    "ValidationRequest",
    "ValidationResponse",
    "Gate1Contract",
    "Gate2Contract",
    "Gate3Contract",
    # Retrieval
    "RetrievalContract",
    "RetrievalRequest",
    "RetrievalResponse",
    "SearchContract",
    "RankerContract",
    # Analysis
    "AnalysisContract",
    "ConflictDetectionContract",
    "ImpactAnalysisContract",
    "ConflictResult",
    "ImpactResult",
    # Export
    "ExportContract",
    "DocumentGeneratorContract",
    "ExportRequest",
    "ExportResult",
]
