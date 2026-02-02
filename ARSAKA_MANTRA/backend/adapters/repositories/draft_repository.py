"""
Draft Repository - Store and manage decision drafts for review.

Drafts are stored separately from finalized decisions.
Each field has its own review status (pending/approved/rejected/edited).
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

# Optional asyncpg for DB operations
try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    asyncpg = None
    HAS_ASYNCPG = False

# Import from review schema (avoid pydantic chain)
import sys
import os
import importlib.util

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_review_schema = _load_module(
    "review_schema",
    os.path.join(backend_dir, "core", "domain", "review_schema.py")
)

DecisionDraft = _review_schema.DecisionDraft
FieldReview = _review_schema.FieldReview
FieldReviewStatus = _review_schema.FieldReviewStatus
FieldSource = _review_schema.FieldSource
AIDecisionDrafter = _review_schema.AIDecisionDrafter
format_for_ui = _review_schema.format_for_ui


class DraftRepository:
    """
    Repository for decision drafts awaiting review.

    Table: decision_drafts
    - draft_id: Primary key
    - user_id: User who requested
    - created_by_ai: AI model that created draft
    - original_request: Original user request
    - fields_json: JSON of all fields with review status
    - needs_review: Boolean flag
    - finalized: Boolean flag
    - finalized_at: Timestamp when finalized
    - approved_by: Human who finalized
    - created_at: Creation timestamp
    - updated_at: Last update timestamp

    Requires asyncpg to be installed for database operations.
    """

    def __init__(self, pool):
        self.pool = pool

    async def create_table(self):
        """Create drafts table if not exists."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS decision_drafts (
                    draft_id VARCHAR(50) PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    created_by_ai VARCHAR(100) NOT NULL,
                    original_request TEXT NOT NULL,
                    fields_json JSONB NOT NULL,
                    needs_review BOOLEAN DEFAULT TRUE,
                    finalized BOOLEAN DEFAULT FALSE,
                    finalized_at TIMESTAMPTZ,
                    approved_by VARCHAR(255),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_drafts_user
                    ON decision_drafts(user_id);
                CREATE INDEX IF NOT EXISTS idx_drafts_needs_review
                    ON decision_drafts(needs_review) WHERE needs_review = TRUE;
                CREATE INDEX IF NOT EXISTS idx_drafts_finalized
                    ON decision_drafts(finalized);
            """)

    async def save_draft(self, draft: DecisionDraft) -> str:
        """
        Save a new draft or update existing.

        Returns draft_id.
        """
        fields_json = self._serialize_fields(draft.fields)

        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO decision_drafts (
                    draft_id, user_id, created_by_ai, original_request,
                    fields_json, needs_review, finalized, finalized_at, approved_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (draft_id) DO UPDATE SET
                    fields_json = EXCLUDED.fields_json,
                    needs_review = EXCLUDED.needs_review,
                    finalized = EXCLUDED.finalized,
                    finalized_at = EXCLUDED.finalized_at,
                    approved_by = EXCLUDED.approved_by,
                    updated_at = NOW()
            """,
                draft.draft_id,
                draft.user_id,
                draft.created_by_ai,
                draft.original_request,
                json.dumps(fields_json),
                draft.needs_review,
                draft.finalized,
                draft.finalized_at,
                draft.approved_by,
            )

        return draft.draft_id

    async def get_draft(self, draft_id: str) -> Optional[DecisionDraft]:
        """Get draft by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM decision_drafts WHERE draft_id = $1",
                draft_id
            )

        if not row:
            return None

        return self._row_to_draft(row)

    async def get_user_drafts(
        self,
        user_id: str,
        include_finalized: bool = False
    ) -> List[DecisionDraft]:
        """Get all drafts for a user."""
        async with self.pool.acquire() as conn:
            if include_finalized:
                rows = await conn.fetch(
                    "SELECT * FROM decision_drafts WHERE user_id = $1 ORDER BY created_at DESC",
                    user_id
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM decision_drafts WHERE user_id = $1 AND finalized = FALSE ORDER BY created_at DESC",
                    user_id
                )

        return [self._row_to_draft(row) for row in rows]

    async def get_pending_drafts(self, user_id: str) -> List[DecisionDraft]:
        """Get drafts that need review."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM decision_drafts WHERE user_id = $1 AND needs_review = TRUE ORDER BY created_at DESC",
                user_id
            )

        return [self._row_to_draft(row) for row in rows]

    async def update_field_review(
        self,
        draft_id: str,
        field_name: str,
        approved: bool,
        new_value: Optional[Any] = None,
        rejection_reason: Optional[str] = None,
    ) -> Optional[DecisionDraft]:
        """
        Update review status for a single field.

        Args:
            draft_id: Draft ID
            field_name: Field to review
            approved: True = OK, False = NO
            new_value: New value if editing after rejection
            rejection_reason: Reason for rejection

        Returns:
            Updated draft
        """
        draft = await self.get_draft(draft_id)
        if not draft:
            return None

        if field_name not in draft.fields:
            raise ValueError(f"Field '{field_name}' not found in draft")

        # Update field review
        draft.review_field(
            field_name,
            approved=approved,
            new_value=new_value,
            rejection_reason=rejection_reason,
        )

        # Check if all reviewed
        if draft.all_reviewed and not draft.rejected_fields:
            draft.needs_review = False

        # Save updated draft
        await self.save_draft(draft)

        return draft

    async def finalize_draft(
        self,
        draft_id: str,
        approved_by: str,
    ) -> Dict[str, Any]:
        """
        Finalize a draft after all fields reviewed.

        Args:
            draft_id: Draft ID
            approved_by: Human user who approves (CANNOT be AI!)

        Returns:
            Final decision dict
        """
        draft = await self.get_draft(draft_id)
        if not draft:
            raise ValueError(f"Draft '{draft_id}' not found")

        # Finalize (this validates all rules)
        decision = draft.finalize(approved_by=approved_by)

        # Save finalized draft
        await self.save_draft(draft)

        return decision

    async def delete_draft(self, draft_id: str) -> bool:
        """Delete a draft (only if not finalized)."""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM decision_drafts WHERE draft_id = $1 AND finalized = FALSE",
                draft_id
            )
        return result == "DELETE 1"

    def _serialize_fields(self, fields: Dict[str, FieldReview]) -> Dict[str, Any]:
        """Serialize fields to JSON-compatible dict."""
        result = {}
        for name, review in fields.items():
            result[name] = {
                "field_name": review.field_name,
                "value": review.value,
                "source": review.source.value,
                "status": review.status.value,
                "source_explanation": review.source_explanation,
                "reviewed_at": review.reviewed_at.isoformat() if review.reviewed_at else None,
                "edited_value": review.edited_value,
                "rejection_reason": review.rejection_reason,
            }
        return result

    def _deserialize_fields(self, fields_json: Dict[str, Any]) -> Dict[str, FieldReview]:
        """Deserialize fields from JSON."""
        result = {}
        for name, data in fields_json.items():
            review = FieldReview(
                field_name=data["field_name"],
                value=data["value"],
                source=FieldSource(data["source"]),
                status=FieldReviewStatus(data["status"]),
                source_explanation=data.get("source_explanation"),
                edited_value=data.get("edited_value"),
                rejection_reason=data.get("rejection_reason"),
            )
            if data.get("reviewed_at"):
                review.reviewed_at = datetime.fromisoformat(data["reviewed_at"])
            result[name] = review
        return result

    def _row_to_draft(self, row) -> DecisionDraft:
        """Convert database row to DecisionDraft."""
        fields_json = json.loads(row["fields_json"]) if isinstance(row["fields_json"], str) else row["fields_json"]

        draft = DecisionDraft(
            draft_id=row["draft_id"],
            created_at=row["created_at"],
            created_by_ai=row["created_by_ai"],
            user_id=row["user_id"],
            original_request=row["original_request"],
            needs_review=row["needs_review"],
            finalized=row["finalized"],
            finalized_at=row["finalized_at"],
            approved_by=row["approved_by"],
        )

        draft.fields = self._deserialize_fields(fields_json)

        return draft


# ============================================================================
# In-Memory Implementation (for testing without DB)
# ============================================================================

class InMemoryDraftRepository:
    """In-memory draft repository for testing."""

    def __init__(self):
        self._drafts: Dict[str, DecisionDraft] = {}

    async def save_draft(self, draft: DecisionDraft) -> str:
        self._drafts[draft.draft_id] = draft
        return draft.draft_id

    async def get_draft(self, draft_id: str) -> Optional[DecisionDraft]:
        return self._drafts.get(draft_id)

    async def get_user_drafts(
        self,
        user_id: str,
        include_finalized: bool = False
    ) -> List[DecisionDraft]:
        drafts = [d for d in self._drafts.values() if d.user_id == user_id]
        if not include_finalized:
            drafts = [d for d in drafts if not d.finalized]
        return sorted(drafts, key=lambda d: d.created_at, reverse=True)

    async def get_pending_drafts(self, user_id: str) -> List[DecisionDraft]:
        return [
            d for d in self._drafts.values()
            if d.user_id == user_id and d.needs_review
        ]

    async def update_field_review(
        self,
        draft_id: str,
        field_name: str,
        approved: bool,
        new_value: Optional[Any] = None,
        rejection_reason: Optional[str] = None,
    ) -> Optional[DecisionDraft]:
        draft = self._drafts.get(draft_id)
        if not draft:
            return None

        draft.review_field(field_name, approved, new_value, rejection_reason)

        if draft.all_reviewed and not draft.rejected_fields:
            draft.needs_review = False

        return draft

    async def finalize_draft(
        self,
        draft_id: str,
        approved_by: str,
    ) -> Dict[str, Any]:
        draft = self._drafts.get(draft_id)
        if not draft:
            raise ValueError(f"Draft '{draft_id}' not found")

        return draft.finalize(approved_by=approved_by)

    async def delete_draft(self, draft_id: str) -> bool:
        if draft_id in self._drafts and not self._drafts[draft_id].finalized:
            del self._drafts[draft_id]
            return True
        return False


__all__ = [
    "DraftRepository",
    "InMemoryDraftRepository",
]
