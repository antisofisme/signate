"""
PostgreSQL Decision Repository

Production-ready implementation of DecisionRepository using PostgreSQL.
Per MANTRA-LAW-001: Decisions are immutable once stored.

Usage:
    repo = PostgresDecisionRepository(database_url)
    await repo.initialize()
    repo.save(stored_decision)
"""

import logging
import json
from typing import List, Optional
from datetime import datetime

import asyncpg

from core.repositories.decision_repository import DecisionRepository
from core.domain.schema import (
    Decision, GroupId, FeatureId, Constraint, ConstraintType, Scope, BlastRadius,
    Relation, RelationType, ContentSection, SectionType
)
from core.domain.decision import StoredDecision, DecisionEvent, AuditEntry, AuditEventType

logger = logging.getLogger(__name__)


class PostgresDecisionRepository(DecisionRepository):
    """
    PostgreSQL implementation of DecisionRepository.

    Provides persistent storage with ACID guarantees.
    Per MANTRA-LAW-001: Enforces immutability of stored decisions.
    """

    def __init__(self, database_url: str):
        """
        Initialize repository with database URL.

        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url
        self._pool: Optional[asyncpg.Pool] = None
        logger.info("PostgresDecisionRepository initialized")

    async def initialize(self) -> None:
        """Create connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=30,
            )
            logger.info("Database connection pool created")

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database connection pool closed")

    def _ensure_pool(self) -> asyncpg.Pool:
        """Ensure pool is initialized."""
        if self._pool is None:
            raise RuntimeError("Repository not initialized. Call initialize() first.")
        return self._pool

    def _row_to_stored_decision(self, row: asyncpg.Record, sequence: int = None) -> StoredDecision:
        """Convert database row to StoredDecision.

        Args:
            row: Database row
            sequence: Optional sequence number for decision_code generation
        """
        # Parse JSONB columns (handle both string and parsed values)
        raw_constraints = row['constraints'] or []
        if isinstance(raw_constraints, str):
            raw_constraints = json.loads(raw_constraints)

        raw_invariants = row['invariants'] or []
        if isinstance(raw_invariants, str):
            raw_invariants = json.loads(raw_invariants)

        raw_related = row['related_decisions'] or []
        if isinstance(raw_related, str):
            raw_related = json.loads(raw_related)

        raw_tags = row.get('tags', []) or []
        if isinstance(raw_tags, str):
            raw_tags = json.loads(raw_tags)

        raw_tech_stack = row.get('tech_stack', []) or []
        if isinstance(raw_tech_stack, str):
            raw_tech_stack = json.loads(raw_tech_stack)

        raw_relations = row.get('relations', []) or []
        if isinstance(raw_relations, str):
            raw_relations = json.loads(raw_relations)

        # Parse constraints
        constraints = []
        for c in raw_constraints:
            constraints.append(Constraint(
                constraint_id=c['constraint_id'],
                statement=c['statement'],
                type=ConstraintType(c['type']),
            ))

        # Parse typed relations
        relations = []
        for r in raw_relations:
            relations.append(Relation(
                target_id=r['target_id'],
                type=RelationType(r['type']),
            ))

        # Parse Layer B sections
        raw_sections = row.get('sections', []) or []
        if isinstance(raw_sections, str):
            raw_sections = json.loads(raw_sections)

        sections = []
        for s in raw_sections:
            sections.append(ContentSection(
                section_id=s.get('section_id', ''),
                section_type=SectionType(s.get('section_type', 'OVERVIEW')),
                title=s.get('title', ''),
                content=s.get('content', ''),
                order=s.get('order', 0),
            ))

        # Generate decision_code if not set
        decision_code = row.get('decision_code')
        if not decision_code and sequence is not None:
            # Format: {group}-{feature}-{seq:03d}-v{version}
            decision_code = f"{row['group_id']}-{row['feature_id']}-{sequence:03d}-v{row['version']}"

        # Create Decision object
        decision = Decision(
            decision_id=str(row['decision_id']),
            decision_code=decision_code,
            group_id=GroupId(row['group_id']),
            feature_id=FeatureId(row['feature_id']),
            statement=row['statement'],
            rationale=row['rationale'],
            constraints=constraints,
            invariants=raw_invariants,
            scope=Scope(row['scope']),
            blast_radius=BlastRadius(row['blast_radius']),
            version=row['version'],
            created_by=row['created_by'],
            created_at=row['created_at'],
            approved_by=row['approved_by'],
            approved_at=row['approved_at'],
            supersedes=str(row['supersedes']) if row['supersedes'] else None,
            related_decisions=raw_related,
            relations=relations,
            tags=raw_tags,
            tech_stack=raw_tech_stack,
            # Layer B Content
            detailed_content=row.get('detailed_content'),
            sections=sections,
            content_summary=row.get('content_summary'),
        )

        return StoredDecision(
            decision=decision,
            stored_at=row['stored_at'],
            stored_by=row['stored_by'],
            storage_version=row['storage_version'],
        )

    def save(self, stored_decision: StoredDecision) -> None:
        """
        Save a decision (synchronous wrapper).

        WARNING: This method should NOT be used in FastAPI routes.
        Use save_async() instead for proper async database access.

        In async context (FastAPI), this creates a fire-and-forget task
        which may not complete before response is sent.
        """
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # We're in async context - log warning and create task
            logger.warning(
                "save() called in async context. Use save_async() instead. "
                "Creating background task - data persistence not guaranteed."
            )
            asyncio.create_task(self.save_async(stored_decision))
        except RuntimeError:
            # No running loop - safe to use sync
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(self.save_async(stored_decision))
            finally:
                loop.close()

    async def save_async(self, stored_decision: StoredDecision) -> None:
        """
        Save a decision to PostgreSQL.

        Per MANTRA-LAW-001 §10: MUST fail if decision already exists.
        """
        pool = self._ensure_pool()
        decision = stored_decision.decision

        # Convert constraints to JSONB-compatible format
        constraints_json = [
            {
                'constraint_id': c.constraint_id,
                'statement': c.statement,
                'type': c.type.value,
            }
            for c in decision.constraints
        ]

        # Convert typed relations to JSONB-compatible format
        relations_json = [
            {
                'target_id': r.target_id,
                'type': r.type.value,
            }
            for r in decision.relations
        ]

        # Convert sections to JSONB-compatible format
        sections_json = [
            {
                'section_id': s.section_id,
                'section_type': s.section_type.value if hasattr(s.section_type, 'value') else s.section_type,
                'title': s.title,
                'content': s.content,
                'order': s.order,
            }
            for s in (decision.sections or [])
        ]

        query = """
            INSERT INTO decisions (
                decision_id, group_id, feature_id, statement, rationale,
                constraints, invariants, scope, blast_radius, version,
                created_by, created_at, approved_by, approved_at,
                supersedes, related_decisions, relations,
                stored_at, stored_by, storage_version,
                detailed_content, sections, content_summary,
                tags, tech_stack
            ) VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9, $10,
                $11, $12, $13, $14,
                $15, $16, $17,
                $18, $19, $20,
                $21, $22, $23,
                $24, $25
            )
        """

        try:
            await pool.execute(
                query,
                decision.decision_id,
                decision.group_id.value,
                decision.feature_id.value,
                decision.statement,
                decision.rationale,
                json.dumps(constraints_json),
                json.dumps(decision.invariants),
                decision.scope.value,
                decision.blast_radius.value,
                decision.version,
                decision.created_by,
                decision.created_at or datetime.utcnow(),
                decision.approved_by,
                decision.approved_at,
                decision.supersedes,
                json.dumps(decision.related_decisions),
                json.dumps(relations_json),
                stored_decision.stored_at or datetime.utcnow(),
                stored_decision.stored_by,
                stored_decision.storage_version,
                # Layer B Content
                decision.detailed_content,
                json.dumps(sections_json) if sections_json else '[]',
                getattr(decision, 'content_summary', None),
                # Metadata fields
                json.dumps(decision.tags) if decision.tags else '[]',
                json.dumps(decision.tech_stack) if decision.tech_stack else '[]',
            )
            logger.info(f"Decision {decision.decision_id} saved to PostgreSQL")
        except asyncpg.UniqueViolationError:
            raise ValueError(
                f"Decision {decision.decision_id} already exists. "
                "Per MANTRA-LAW-001 §10, stored decisions are immutable."
            )

    def find_by_id(self, decision_id: str) -> Optional[StoredDecision]:
        """
        Find decision by ID (synchronous wrapper).

        WARNING: Returns None in async context (FastAPI).
        Use find_by_id_async() instead for routes.
        """
        import asyncio
        try:
            asyncio.get_running_loop()
            # We're in async context - cannot block
            logger.warning(
                f"find_by_id({decision_id}) called in async context. "
                "Returning None. Use find_by_id_async() instead."
            )
            return None
        except RuntimeError:
            # No running loop - safe to use sync
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self.find_by_id_async(decision_id))
            finally:
                loop.close()

    async def find_by_id_async(self, decision_id: str) -> Optional[StoredDecision]:
        """Find decision by ID with auto-generated decision_code."""
        pool = self._ensure_pool()

        # Use subquery to calculate sequence for this decision
        query = """
            SELECT d.*,
                (SELECT COUNT(*) FROM decisions d2
                 WHERE d2.feature_id = d.feature_id
                 AND d2.created_at <= d.created_at) as seq
            FROM decisions d
            WHERE d.decision_id = $1
        """

        row = await pool.fetchrow(query, decision_id)
        if row is None:
            return None

        return self._row_to_stored_decision(row, sequence=row['seq'])

    def find_all(self, limit: int = 100, offset: int = 0) -> List[StoredDecision]:
        """
        Find all decisions (synchronous wrapper).

        WARNING: Returns [] in async context (FastAPI).
        Use find_all_async() instead for routes.
        """
        import asyncio
        try:
            asyncio.get_running_loop()
            logger.warning(
                "find_all() called in async context. "
                "Returning []. Use find_all_async() instead."
            )
            return []
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self.find_all_async(limit, offset))
            finally:
                loop.close()

    async def find_all_async(self, limit: int = 100, offset: int = 0) -> List[StoredDecision]:
        """Find all decisions with pagination and auto-generated decision_code."""
        pool = self._ensure_pool()

        # Use window function to calculate sequence per feature
        query = """
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY feature_id
                    ORDER BY created_at ASC
                ) as seq
            FROM decisions
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """

        rows = await pool.fetch(query, limit, offset)
        return [self._row_to_stored_decision(row, sequence=row['seq']) for row in rows]

    def find_by_group(
        self,
        group_id: GroupId,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """
        Find decisions by group (synchronous wrapper).

        WARNING: Returns [] in async context (FastAPI).
        Use find_by_group_async() instead for routes.
        """
        import asyncio
        try:
            asyncio.get_running_loop()
            logger.warning(
                f"find_by_group({group_id}) called in async context. "
                "Returning []. Use find_by_group_async() instead."
            )
            return []
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self.find_by_group_async(group_id, limit, offset))
            finally:
                loop.close()

    async def find_by_group_async(
        self,
        group_id: GroupId,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredDecision]:
        """Find decisions by group with auto-generated decision_code."""
        pool = self._ensure_pool()

        # Use window function to calculate sequence per feature
        query = """
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY feature_id
                    ORDER BY created_at ASC
                ) as seq
            FROM decisions
            WHERE group_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """

        rows = await pool.fetch(query, group_id.value, limit, offset)
        return [self._row_to_stored_decision(row, sequence=row['seq']) for row in rows]

    def count(self) -> int:
        """
        Count total decisions (synchronous wrapper).

        WARNING: Returns 0 in async context (FastAPI).
        Use count_async() instead for routes.
        """
        import asyncio
        try:
            asyncio.get_running_loop()
            logger.warning(
                "count() called in async context. "
                "Returning 0. Use count_async() instead."
            )
            return 0
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self.count_async())
            finally:
                loop.close()

    async def count_async(self) -> int:
        """Count total decisions."""
        pool = self._ensure_pool()
        result = await pool.fetchval("SELECT COUNT(*) FROM decisions")
        return result or 0

    def count_by_feature(self, feature_id: FeatureId) -> int:
        """
        Count decisions by feature (synchronous wrapper).

        WARNING: Returns 0 in async context (FastAPI).
        Use count_by_feature_async() instead for routes.
        """
        import asyncio
        try:
            asyncio.get_running_loop()
            logger.warning(
                f"count_by_feature({feature_id}) called in async context. "
                "Returning 0. Use count_by_feature_async() instead."
            )
            return 0
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self.count_by_feature_async(feature_id))
            finally:
                loop.close()

    async def count_by_feature_async(self, feature_id: FeatureId) -> int:
        """Count decisions by feature."""
        pool = self._ensure_pool()
        result = await pool.fetchval(
            "SELECT COUNT(*) FROM decisions WHERE feature_id = $1",
            feature_id.value
        )
        return result or 0

    def record_event(self, event: DecisionEvent) -> None:
        """
        Record domain event (synchronous wrapper).

        WARNING: In async context, creates background task (not guaranteed to complete).
        Use record_event_async() instead for routes.
        """
        import asyncio
        try:
            asyncio.get_running_loop()
            logger.warning(
                "record_event() called in async context. "
                "Creating background task. Use record_event_async() instead."
            )
            asyncio.create_task(self.record_event_async(event))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(self.record_event_async(event))
            finally:
                loop.close()

    async def record_event_async(self, event: DecisionEvent) -> None:
        """Record a domain event."""
        pool = self._ensure_pool()

        query = """
            INSERT INTO decision_events (
                event_id, event_type, decision_id, actor, metadata, recorded_at
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """

        await pool.execute(
            query,
            event.event_id,
            event.event_type.value,
            event.decision_id,
            event.actor,
            json.dumps(event.metadata or {}),
            event.timestamp,
        )

    def record_audit(self, entry: AuditEntry) -> None:
        """
        Record audit entry (synchronous wrapper).

        WARNING: In async context, creates background task (not guaranteed to complete).
        Use record_audit_async() instead for routes.
        """
        import asyncio
        try:
            asyncio.get_running_loop()
            logger.warning(
                "record_audit() called in async context. "
                "Creating background task. Use record_audit_async() instead."
            )
            asyncio.create_task(self.record_audit_async(entry))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(self.record_audit_async(entry))
            finally:
                loop.close()

    async def record_audit_async(self, entry: AuditEntry) -> None:
        """Record an audit entry."""
        pool = self._ensure_pool()

        query = """
            INSERT INTO decision_events (
                event_id, event_type, decision_id, actor, metadata, recorded_at
            ) VALUES ($1, $2, $3, $4, $5, $6)
        """

        await pool.execute(
            query,
            entry.event_id,
            entry.event_type.value,
            entry.decision_id,
            entry.actor,
            json.dumps(entry.metadata or {}),
            entry.timestamp,
        )

    def get_audit_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> List[AuditEntry]:
        """
        Get audit entries (synchronous wrapper).

        WARNING: Returns [] in async context (FastAPI).
        Use get_audit_entries_async() instead for routes.
        """
        import asyncio
        try:
            asyncio.get_running_loop()
            logger.warning(
                "get_audit_entries() called in async context. "
                "Returning []. Use get_audit_entries_async() instead."
            )
            return []
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    self.get_audit_entries_async(limit, offset, decision_id, event_type, actor)
                )
            finally:
                loop.close()

    async def get_audit_entries_async(
        self,
        limit: int = 100,
        offset: int = 0,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> List[AuditEntry]:
        """Get audit entries with filtering."""
        pool = self._ensure_pool()

        # Build query with optional filters
        conditions = []
        params = []
        param_idx = 1

        if decision_id:
            conditions.append(f"decision_id = ${param_idx}")
            params.append(decision_id)
            param_idx += 1

        if event_type:
            conditions.append(f"event_type = ${param_idx}")
            params.append(event_type.value)
            param_idx += 1

        if actor:
            conditions.append(f"actor = ${param_idx}")
            params.append(actor)
            param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT * FROM decision_events
            WHERE {where_clause}
            ORDER BY recorded_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])

        rows = await pool.fetch(query, *params)

        return [
            AuditEntry(
                entry_id=str(row['event_id']),
                decision_id=str(row['decision_id']),
                event_type=AuditEventType(row['event_type']),
                actor=row['actor'],
                timestamp=row['recorded_at'],
                details=row['metadata'],
            )
            for row in rows
        ]

    def count_audit_entries(
        self,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> int:
        """
        Count audit entries (synchronous wrapper).

        WARNING: Returns 0 in async context (FastAPI).
        Use count_audit_entries_async() instead for routes.
        """
        import asyncio
        try:
            asyncio.get_running_loop()
            logger.warning(
                "count_audit_entries() called in async context. "
                "Returning 0. Use count_audit_entries_async() instead."
            )
            return 0
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    self.count_audit_entries_async(decision_id, event_type, actor)
                )
            finally:
                loop.close()

    async def count_audit_entries_async(
        self,
        decision_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
    ) -> int:
        """Count audit entries with filtering."""
        pool = self._ensure_pool()

        conditions = []
        params = []
        param_idx = 1

        if decision_id:
            conditions.append(f"decision_id = ${param_idx}")
            params.append(decision_id)
            param_idx += 1

        if event_type:
            conditions.append(f"event_type = ${param_idx}")
            params.append(event_type.value)
            param_idx += 1

        if actor:
            conditions.append(f"actor = ${param_idx}")
            params.append(actor)
            param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"SELECT COUNT(*) FROM decision_events WHERE {where_clause}"
        result = await pool.fetchval(query, *params)
        return result or 0

    def find_supersedes_chain(self, decision_id: str) -> List[StoredDecision]:
        """
        Find supersedes chain (synchronous wrapper).

        WARNING: Returns [] in async context (FastAPI).
        Use find_supersedes_chain_async() instead for routes.
        """
        import asyncio
        try:
            asyncio.get_running_loop()
            logger.warning(
                f"find_supersedes_chain({decision_id}) called in async context. "
                "Returning []. Use find_supersedes_chain_async() instead."
            )
            return []
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self.find_supersedes_chain_async(decision_id))
            finally:
                loop.close()

    async def find_supersedes_chain_async(self, decision_id: str) -> List[StoredDecision]:
        """Find the complete supersedes chain for a decision."""
        pool = self._ensure_pool()

        # Use recursive CTE to find the chain
        query = """
            WITH RECURSIVE chain AS (
                -- Start with the given decision
                SELECT d.*, 0 as depth
                FROM decisions d
                WHERE d.decision_id = $1

                UNION ALL

                -- Follow supersedes backward (older versions)
                SELECT d.*, c.depth + 1
                FROM decisions d
                JOIN chain c ON d.decision_id = c.supersedes
                WHERE c.depth < 100  -- Prevent infinite loops
            )
            SELECT * FROM chain ORDER BY depth DESC
        """

        rows = await pool.fetch(query, decision_id)
        chain = [self._row_to_stored_decision(row) for row in rows]

        # Also find decisions that supersede this one (newer versions)
        newer_query = """
            WITH RECURSIVE newer AS (
                SELECT d.*, 0 as depth
                FROM decisions d
                WHERE d.supersedes = $1

                UNION ALL

                SELECT d.*, n.depth + 1
                FROM decisions d
                JOIN newer n ON d.supersedes = n.decision_id
                WHERE n.depth < 100
            )
            SELECT * FROM newer ORDER BY depth ASC
        """

        newer_rows = await pool.fetch(newer_query, decision_id)
        newer_decisions = [self._row_to_stored_decision(row) for row in newer_rows]

        chain.extend(newer_decisions)
        return chain
