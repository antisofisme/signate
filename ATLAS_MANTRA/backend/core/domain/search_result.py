"""
Search Result Domain Entity - Represents semantic search results.

This entity encapsulates the results of semantic search operations,
including relevance scoring and matched decisions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class SearchStatus(str, Enum):
    """Status of a search operation."""
    FOUND = "FOUND"           # Results found
    NOT_FOUND = "NOT_FOUND"   # No results matched
    ERROR = "ERROR"           # Search failed
    PARTIAL = "PARTIAL"       # Some results, but search may be incomplete


class AlignmentStatus(str, Enum):
    """Status of alignment check."""
    ALIGNED = "ALIGNED"       # Proposal aligns with existing decisions
    CONFLICTING = "CONFLICTING"  # Conflicts detected
    PARTIAL = "PARTIAL"       # Partially aligned
    UNKNOWN = "UNKNOWN"       # Cannot determine alignment


@dataclass
class SearchHit:
    """
    A single search result hit.

    Attributes:
        decision_id: ID of the matched decision
        decision_code: Human-readable code (e.g., INT-F01-001-v1.0.0)
        statement: Decision statement
        rationale: Decision rationale
        score: Similarity score (0.0 to 1.0)
        group_id: Decision group (INT, ARCH, CTL, EVO)
        feature_id: Decision feature (F01-F16)
        version: Decision version
        tags: Decision tags
        matched_fields: Which fields contributed to the match
    """
    decision_id: str
    decision_code: str
    statement: str
    rationale: str
    score: float
    group_id: str
    feature_id: str
    version: str
    tags: List[str] = field(default_factory=list)
    matched_fields: List[str] = field(default_factory=lambda: ["statement", "rationale"])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "decision_id": self.decision_id,
            "decision_code": self.decision_code,
            "statement": self.statement,
            "rationale": self.rationale,
            "score": self.score,
            "group_id": self.group_id,
            "feature_id": self.feature_id,
            "version": self.version,
            "tags": self.tags,
            "matched_fields": self.matched_fields,
        }


@dataclass
class SemanticSearchResult:
    """
    Result of a semantic search operation.

    Attributes:
        status: Search status (FOUND, NOT_FOUND, ERROR, PARTIAL)
        hits: List of matched decisions with scores
        total_count: Total number of results
        query: The original search query
        filters_applied: Filters that were applied
        execution_time_ms: Search execution time in milliseconds
        cached: Whether result was served from cache
        error_message: Error message if status is ERROR
    """
    status: SearchStatus
    hits: List[SearchHit]
    total_count: int
    query: str
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    cached: bool = False
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status.value,
            "hits": [hit.to_dict() for hit in self.hits],
            "total_count": self.total_count,
            "query": self.query,
            "filters_applied": self.filters_applied,
            "execution_time_ms": self.execution_time_ms,
            "cached": self.cached,
            "error_message": self.error_message,
        }


@dataclass
class AlignmentCheckResult:
    """
    Result of an alignment check operation.

    Used to check if a proposed decision aligns with existing decisions.

    Attributes:
        status: Alignment status
        aligned_with: Decisions that align with the proposal
        conflicts_with: Decisions that conflict with the proposal
        related_decisions: Related but not conflicting decisions
        recommendations: Suggested actions or modifications
        execution_time_ms: Check execution time in milliseconds
        error_message: Error message if status is UNKNOWN due to error
    """
    status: AlignmentStatus
    aligned_with: List[SearchHit] = field(default_factory=list)
    conflicts_with: List[SearchHit] = field(default_factory=list)
    related_decisions: List[SearchHit] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status.value,
            "aligned_with": [h.to_dict() for h in self.aligned_with],
            "conflicts_with": [h.to_dict() for h in self.conflicts_with],
            "related_decisions": [h.to_dict() for h in self.related_decisions],
            "recommendations": self.recommendations,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message,
        }


@dataclass
class SyncResult:
    """
    Result of an embedding sync operation.

    Attributes:
        synced_count: Number of decisions synced
        skipped_count: Number of decisions skipped (already synced)
        failed_count: Number of decisions that failed to sync
        total_decisions: Total decisions in repository
        execution_time_ms: Sync execution time in milliseconds
        errors: List of error messages for failed syncs
    """
    synced_count: int
    skipped_count: int
    failed_count: int
    total_decisions: int
    execution_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "synced_count": self.synced_count,
            "skipped_count": self.skipped_count,
            "failed_count": self.failed_count,
            "total_decisions": self.total_decisions,
            "execution_time_ms": self.execution_time_ms,
            "errors": self.errors,
        }
