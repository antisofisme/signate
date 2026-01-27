"""
Check Alignment Use Case - Verify proposal alignment with existing decisions.

This use case checks if a proposed decision aligns with or conflicts with
existing decisions in the MANTRA system.

Usage:
    use_case = CheckAlignmentUseCase(vector_store, cache, embedding, repository)
    result = await use_case.execute(statement="Use MongoDB", rationale="For flexibility")
"""

import time
import logging
from dataclasses import dataclass
from typing import List, Optional

from core.ports.vector_store import VectorStoreProtocol
from core.ports.cache import CacheProtocol
from core.ports.embedding_service import EmbeddingProtocol
from core.repositories.decision_repository import DecisionRepository
from core.domain.search_result import (
    AlignmentCheckResult,
    AlignmentStatus,
    SearchHit,
)
from core.domain.embedding import create_embedding_text

logger = logging.getLogger(__name__)


@dataclass
class CheckAlignmentInput:
    """Input for alignment check."""
    statement: str
    rationale: str = ""
    group_id: Optional[str] = None  # Scope check to specific group
    min_score: float = 0.6  # Threshold for related decisions


# Keywords that indicate potential conflicts
CONFLICT_KEYWORDS = [
    # Database choices
    ("mongodb", "postgresql"),
    ("mysql", "postgresql"),
    ("nosql", "sql"),
    # Architecture choices
    ("monolith", "microservice"),
    ("serverless", "kubernetes"),
    ("rest", "graphql"),
    # Technology choices
    ("react", "vue"),
    ("angular", "react"),
    ("python", "node"),
    # Patterns
    ("sync", "async"),
    ("push", "pull"),
]


class CheckAlignmentUseCase:
    """
    Check alignment of proposed decision with existing decisions.

    Workflow:
    1. Generate embedding for proposal
    2. Find similar existing decisions
    3. Analyze for potential conflicts
    4. Generate recommendations
    """

    def __init__(
        self,
        vector_store: VectorStoreProtocol,
        cache: CacheProtocol,
        embedding_service: EmbeddingProtocol,
        repository: DecisionRepository,
    ):
        self.vector_store = vector_store
        self.cache = cache
        self.embedding = embedding_service
        self.repository = repository

    def _detect_keyword_conflict(self, text1: str, text2: str) -> bool:
        """Detect conflicts based on opposing keywords."""
        text1_lower = text1.lower()
        text2_lower = text2.lower()

        for kw1, kw2 in CONFLICT_KEYWORDS:
            if (kw1 in text1_lower and kw2 in text2_lower) or \
               (kw2 in text1_lower and kw1 in text2_lower):
                return True
        return False

    def _analyze_similarity(
        self,
        proposal_text: str,
        hits: List[SearchHit],
    ) -> tuple[List[SearchHit], List[SearchHit], List[SearchHit]]:
        """
        Analyze hits and categorize into aligned, conflicting, and related.

        Returns:
            Tuple of (aligned, conflicting, related) lists
        """
        aligned = []
        conflicting = []
        related = []

        for hit in hits:
            decision_text = f"{hit.statement} {hit.rationale}"

            # High similarity could mean alignment or conflict
            if hit.score >= 0.85:
                # Very similar - check for keyword conflicts
                if self._detect_keyword_conflict(proposal_text, decision_text):
                    conflicting.append(hit)
                else:
                    aligned.append(hit)
            elif hit.score >= 0.7:
                # Moderately similar - potentially related
                if self._detect_keyword_conflict(proposal_text, decision_text):
                    conflicting.append(hit)
                else:
                    related.append(hit)
            else:
                # Lower similarity but still relevant
                related.append(hit)

        return aligned, conflicting, related

    def _generate_recommendations(
        self,
        proposal_statement: str,
        aligned: List[SearchHit],
        conflicting: List[SearchHit],
        related: List[SearchHit],
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if conflicting:
            recommendations.append(
                f"⚠️ Found {len(conflicting)} potentially conflicting decision(s). "
                "Review before proceeding."
            )
            for c in conflicting[:2]:  # Show top 2 conflicts
                recommendations.append(
                    f"  - Conflict with {c.decision_code}: \"{c.statement[:100]}...\""
                )

        if aligned:
            recommendations.append(
                f"✅ Aligns with {len(aligned)} existing decision(s). "
                "Consider referencing them."
            )

        if related and not conflicting:
            recommendations.append(
                f"📎 Found {len(related)} related decision(s) for context."
            )

        if not aligned and not conflicting and not related:
            recommendations.append(
                "🆕 No similar decisions found. This appears to be a new area."
            )

        return recommendations

    async def execute(self, input: CheckAlignmentInput) -> AlignmentCheckResult:
        """
        Execute alignment check.

        Args:
            input: Alignment check parameters

        Returns:
            AlignmentCheckResult with analysis
        """
        start_time = time.time()

        try:
            # 1. Create embedding text
            proposal_text = create_embedding_text(
                statement=input.statement,
                rationale=input.rationale,
            )

            # 2. Generate embedding
            query_vector = await self.embedding.embed(proposal_text)

            # 3. Build filters
            filters = {}
            if input.group_id:
                filters["group_id"] = input.group_id

            # 4. Search for similar decisions
            vector_results = await self.vector_store.search(
                query_vector=query_vector,
                limit=20,  # Get more results for analysis
                min_score=input.min_score,
                filters=filters if filters else None,
            )

            # 5. Build search hits with full decision data
            hits = []
            for vr in vector_results:
                decision = self.repository.find_by_id(vr.id)
                if decision:
                    hits.append(SearchHit(
                        decision_id=vr.id,
                        decision_code=decision.decision_code,
                        statement=decision.statement,
                        rationale=decision.rationale,
                        score=vr.score,
                        group_id=decision.group_id.value if hasattr(decision.group_id, 'value') else str(decision.group_id),
                        feature_id=decision.feature_id.value if hasattr(decision.feature_id, 'value') else str(decision.feature_id),
                        version=decision.version,
                        tags=[t.value if hasattr(t, 'value') else str(t) for t in (decision.tags or [])],
                    ))
                else:
                    payload = vr.payload
                    hits.append(SearchHit(
                        decision_id=vr.id,
                        decision_code=payload.get("decision_code", vr.id),
                        statement=payload.get("statement", ""),
                        rationale=payload.get("rationale", ""),
                        score=vr.score,
                        group_id=payload.get("group_id", ""),
                        feature_id=payload.get("feature_id", ""),
                        version=payload.get("version", "1.0.0"),
                        tags=payload.get("tags", []),
                    ))

            # 6. Analyze alignment
            aligned, conflicting, related = self._analyze_similarity(proposal_text, hits)

            # 7. Determine status
            if conflicting:
                status = AlignmentStatus.CONFLICTING
            elif aligned:
                status = AlignmentStatus.ALIGNED
            elif related:
                status = AlignmentStatus.PARTIAL
            else:
                status = AlignmentStatus.ALIGNED  # No conflicts found

            # 8. Generate recommendations
            recommendations = self._generate_recommendations(
                input.statement,
                aligned,
                conflicting,
                related,
            )

            result = AlignmentCheckResult(
                status=status,
                aligned_with=aligned,
                conflicts_with=conflicting,
                related_decisions=related,
                recommendations=recommendations,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

            logger.info(
                f"Alignment check: status={status.value}, "
                f"aligned={len(aligned)}, conflicts={len(conflicting)}, related={len(related)}"
            )
            return result

        except Exception as e:
            logger.error(f"Alignment check error: {e}")
            return AlignmentCheckResult(
                status=AlignmentStatus.UNKNOWN,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e),
            )


async def check_alignment(
    statement: str,
    vector_store: VectorStoreProtocol,
    cache: CacheProtocol,
    embedding_service: EmbeddingProtocol,
    repository: DecisionRepository,
    rationale: str = "",
    group_id: Optional[str] = None,
    min_score: float = 0.6,
) -> AlignmentCheckResult:
    """
    Convenience function for alignment check.

    Args:
        statement: Proposed decision statement
        vector_store: Vector store implementation
        cache: Cache implementation
        embedding_service: Embedding service implementation
        repository: Decision repository
        rationale: Proposed rationale
        group_id: Scope to specific group
        min_score: Minimum similarity threshold

    Returns:
        AlignmentCheckResult
    """
    use_case = CheckAlignmentUseCase(
        vector_store=vector_store,
        cache=cache,
        embedding_service=embedding_service,
        repository=repository,
    )
    return await use_case.execute(CheckAlignmentInput(
        statement=statement,
        rationale=rationale,
        group_id=group_id,
        min_score=min_score,
    ))
