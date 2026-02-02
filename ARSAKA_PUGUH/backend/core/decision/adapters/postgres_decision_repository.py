"""
PostgreSQL Decision Repository Implementation

Concrete implementation of IDecisionRepository for PostgreSQL.
Uses existing tables from 001_initial_schema.sql:
- rules
- decisions
- event_log
"""

from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..interfaces import IDecisionRepository
from ..domain import Rule, RuleStatus, Decision, DecisionOutcome


class PostgresDecisionRepository(IDecisionRepository):
    """PostgreSQL implementation of Decision repository."""

    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory

    # =========================================================================
    # Rule Operations
    # =========================================================================

    async def list_rules(
        self,
        tenant_id: UUID,
        status: Optional[RuleStatus] = None,
        decision_type: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[List[Rule], int]:
        """List rules in a tenant."""
        async with self._session_factory() as session:
            base_query = """
                SELECT
                    rule_id, tenant_id, decision_type, rule_name, description,
                    conditions, action, extension_hooks, version, status,
                    evaluation_sequence, created_by_user_id, created_at,
                    activated_at, deactivated_at, deactivation_reason
                FROM rules
                WHERE tenant_id = :tenant_id
                  AND deleted_at IS NULL
            """
            params = {"tenant_id": str(tenant_id)}

            if status:
                base_query += " AND status = :status"
                params["status"] = status.value

            if decision_type:
                base_query += " AND decision_type = :decision_type"
                params["decision_type"] = decision_type

            # Count total
            count_query = f"SELECT COUNT(*) FROM ({base_query}) sub"
            result = await session.execute(text(count_query), params)
            total = result.scalar() or 0

            # Add pagination
            offset = (page - 1) * limit
            paginated_query = f"{base_query} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = await session.execute(text(paginated_query), params)
            rows = result.fetchall()

            rules = [
                Rule(
                    id=row.rule_id,
                    tenant_id=row.tenant_id,
                    decision_type=row.decision_type,
                    rule_name=row.rule_name,
                    description=row.description,
                    conditions=row.conditions or {},
                    action=row.action or {},
                    extension_hooks=row.extension_hooks,
                    version=row.version,
                    status=RuleStatus(row.status),
                    evaluation_sequence=row.evaluation_sequence,
                    created_by_user_id=row.created_by_user_id,
                    created_at=row.created_at,
                    activated_at=row.activated_at,
                    deactivated_at=row.deactivated_at,
                    deactivation_reason=row.deactivation_reason,
                )
                for row in rows
            ]

            return rules, total

    async def get_rule(self, tenant_id: UUID, rule_id: UUID) -> Optional[Rule]:
        """Get rule by ID."""
        async with self._session_factory() as session:
            query = """
                SELECT
                    rule_id, tenant_id, decision_type, rule_name, description,
                    conditions, action, extension_hooks, version, status,
                    evaluation_sequence, created_by_user_id, created_at,
                    activated_at, deactivated_at, deactivation_reason
                FROM rules
                WHERE rule_id = :rule_id AND tenant_id = :tenant_id
                  AND deleted_at IS NULL
            """
            result = await session.execute(
                text(query),
                {"rule_id": str(rule_id), "tenant_id": str(tenant_id)}
            )
            row = result.fetchone()

            if not row:
                return None

            return Rule(
                id=row.rule_id,
                tenant_id=row.tenant_id,
                decision_type=row.decision_type,
                rule_name=row.rule_name,
                description=row.description,
                conditions=row.conditions or {},
                action=row.action or {},
                extension_hooks=row.extension_hooks,
                version=row.version,
                status=RuleStatus(row.status),
                evaluation_sequence=row.evaluation_sequence,
                created_by_user_id=row.created_by_user_id,
                created_at=row.created_at,
                activated_at=row.activated_at,
                deactivated_at=row.deactivated_at,
                deactivation_reason=row.deactivation_reason,
            )

    async def get_rule_versions(
        self, tenant_id: UUID, rule_id: UUID
    ) -> List[dict]:
        """Get version history for a rule (from event_log)."""
        async with self._session_factory() as session:
            # Get events related to this rule
            query = """
                SELECT
                    event_id, event_type, payload, occurred_at
                FROM event_log
                WHERE tenant_id = :tenant_id
                  AND aggregate_id = :rule_id
                  AND aggregate_type = 'rule'
                ORDER BY occurred_at DESC
            """
            result = await session.execute(
                text(query),
                {"rule_id": str(rule_id), "tenant_id": str(tenant_id)}
            )
            rows = result.fetchall()

            # Also get current rule info
            rule = await self.get_rule(tenant_id, rule_id)

            versions = []
            if rule:
                versions.append({
                    "version": rule.version,
                    "status": rule.status.value,
                    "created_at": rule.created_at.isoformat() if rule.created_at else None,
                    "activated_at": rule.activated_at.isoformat() if rule.activated_at else None,
                })

            # Add historical events
            for row in rows:
                versions.append({
                    "event_type": row.event_type,
                    "payload": row.payload,
                    "occurred_at": row.occurred_at.isoformat() if row.occurred_at else None,
                })

            return versions

    async def create_rule(
        self,
        tenant_id: UUID,
        rule_name: str,
        decision_type: str,
        conditions: dict,
        action: dict,
        created_by: UUID,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Rule:
        """Create a new rule in DRAFT status."""
        async with self._session_factory() as session:
            rule_id = uuid4()
            query = """
                INSERT INTO rules (
                    rule_id, tenant_id, decision_type, rule_name, description,
                    conditions, action, version, status, created_by_user_id
                )
                VALUES (
                    :rule_id, :tenant_id, :decision_type, :rule_name, :description,
                    :conditions, :action, '1.0', 'DRAFT', :created_by
                )
                RETURNING
                    rule_id, tenant_id, decision_type, rule_name, description,
                    conditions, action, version, status, evaluation_sequence,
                    created_by_user_id, created_at
            """
            result = await session.execute(
                text(query),
                {
                    "rule_id": str(rule_id),
                    "tenant_id": str(tenant_id),
                    "decision_type": decision_type,
                    "rule_name": rule_name,
                    "description": description,
                    "conditions": conditions,
                    "action": action,
                    "created_by": str(created_by),
                }
            )
            await session.commit()
            row = result.fetchone()

            return Rule(
                id=row.rule_id,
                tenant_id=row.tenant_id,
                decision_type=row.decision_type,
                rule_name=row.rule_name,
                description=row.description,
                conditions=row.conditions or {},
                action=row.action or {},
                version=row.version,
                status=RuleStatus(row.status),
                evaluation_sequence=row.evaluation_sequence,
                created_by_user_id=row.created_by_user_id,
                created_at=row.created_at,
            )

    async def activate_rule(
        self,
        tenant_id: UUID,
        rule_id: UUID,
        activated_by: UUID,
    ) -> Rule:
        """Activate a draft rule (set status to ACTIVE)."""
        async with self._session_factory() as session:
            query = """
                UPDATE rules
                SET status = 'ACTIVE', activated_at = NOW()
                WHERE rule_id = :rule_id
                  AND tenant_id = :tenant_id
                  AND status = 'DRAFT'
                RETURNING
                    rule_id, tenant_id, decision_type, rule_name, description,
                    conditions, action, version, status, evaluation_sequence,
                    created_by_user_id, created_at, activated_at
            """
            result = await session.execute(
                text(query),
                {"rule_id": str(rule_id), "tenant_id": str(tenant_id)}
            )
            await session.commit()
            row = result.fetchone()

            if not row:
                raise ValueError(f"Rule {rule_id} not found or not in DRAFT status")

            return Rule(
                id=row.rule_id,
                tenant_id=row.tenant_id,
                decision_type=row.decision_type,
                rule_name=row.rule_name,
                description=row.description,
                conditions=row.conditions or {},
                action=row.action or {},
                version=row.version,
                status=RuleStatus(row.status),
                evaluation_sequence=row.evaluation_sequence,
                created_by_user_id=row.created_by_user_id,
                created_at=row.created_at,
                activated_at=row.activated_at,
            )

    async def deactivate_rule(
        self,
        tenant_id: UUID,
        rule_id: UUID,
        deactivated_by: UUID,
        reason: Optional[str] = None,
    ) -> Rule:
        """Deactivate an active rule (set status to DEPRECATED)."""
        async with self._session_factory() as session:
            query = """
                UPDATE rules
                SET status = 'DEPRECATED',
                    deactivated_at = NOW(),
                    deactivation_reason = :reason
                WHERE rule_id = :rule_id
                  AND tenant_id = :tenant_id
                  AND status = 'ACTIVE'
                RETURNING
                    rule_id, tenant_id, decision_type, rule_name, description,
                    conditions, action, version, status, evaluation_sequence,
                    created_by_user_id, created_at, activated_at,
                    deactivated_at, deactivation_reason
            """
            result = await session.execute(
                text(query),
                {
                    "rule_id": str(rule_id),
                    "tenant_id": str(tenant_id),
                    "reason": reason,
                }
            )
            await session.commit()
            row = result.fetchone()

            if not row:
                raise ValueError(f"Rule {rule_id} not found or not in ACTIVE status")

            return Rule(
                id=row.rule_id,
                tenant_id=row.tenant_id,
                decision_type=row.decision_type,
                rule_name=row.rule_name,
                description=row.description,
                conditions=row.conditions or {},
                action=row.action or {},
                version=row.version,
                status=RuleStatus(row.status),
                evaluation_sequence=row.evaluation_sequence,
                created_by_user_id=row.created_by_user_id,
                created_at=row.created_at,
                activated_at=row.activated_at,
                deactivated_at=row.deactivated_at,
                deactivation_reason=row.deactivation_reason,
            )

    async def update_rule(
        self,
        tenant_id: UUID,
        rule_id: UUID,
        updated_by: UUID,
        rule_name: Optional[str] = None,
        description: Optional[str] = None,
        conditions: Optional[dict] = None,
        action: Optional[dict] = None,
    ) -> Rule:
        """Update a draft rule. Only DRAFT status rules can be updated."""
        async with self._session_factory() as session:
            # Build dynamic UPDATE query based on provided fields
            # Auto-increment version on each update (e.g., 1.0 -> 1.1 -> 1.2)
            set_clauses = [
                "updated_at = NOW()",
                "version = CONCAT(SPLIT_PART(version, '.', 1), '.', (SPLIT_PART(version, '.', 2)::int + 1)::text)",
            ]
            params = {
                "rule_id": str(rule_id),
                "tenant_id": str(tenant_id),
            }

            if rule_name is not None:
                set_clauses.append("rule_name = :rule_name")
                params["rule_name"] = rule_name

            if description is not None:
                set_clauses.append("description = :description")
                params["description"] = description

            if conditions is not None:
                set_clauses.append("conditions = :conditions")
                params["conditions"] = conditions

            if action is not None:
                set_clauses.append("action = :action")
                params["action"] = action

            query = f"""
                UPDATE rules
                SET {', '.join(set_clauses)}
                WHERE rule_id = :rule_id
                  AND tenant_id = :tenant_id
                  AND status = 'DRAFT'
                  AND deleted_at IS NULL
                RETURNING
                    rule_id, tenant_id, decision_type, rule_name, description,
                    conditions, action, extension_hooks, version, status,
                    evaluation_sequence, created_by_user_id, created_at,
                    activated_at, deactivated_at, deactivation_reason
            """
            result = await session.execute(text(query), params)
            await session.commit()
            row = result.fetchone()

            if not row:
                raise ValueError(
                    f"Rule {rule_id} not found, not in DRAFT status, or already deleted"
                )

            return Rule(
                id=row.rule_id,
                tenant_id=row.tenant_id,
                decision_type=row.decision_type,
                rule_name=row.rule_name,
                description=row.description,
                conditions=row.conditions or {},
                action=row.action or {},
                extension_hooks=row.extension_hooks,
                version=row.version,
                status=RuleStatus(row.status),
                evaluation_sequence=row.evaluation_sequence,
                created_by_user_id=row.created_by_user_id,
                created_at=row.created_at,
                activated_at=row.activated_at,
                deactivated_at=row.deactivated_at,
                deactivation_reason=row.deactivation_reason,
            )

    async def delete_rule(
        self,
        tenant_id: UUID,
        rule_id: UUID,
        deleted_by: UUID,
    ) -> bool:
        """Soft delete a rule. Sets deleted_at timestamp."""
        async with self._session_factory() as session:
            query = """
                UPDATE rules
                SET deleted_at = NOW(),
                    status = 'DELETED'
                WHERE rule_id = :rule_id
                  AND tenant_id = :tenant_id
                  AND deleted_at IS NULL
                  AND status IN ('DRAFT', 'DEPRECATED')
                RETURNING rule_id
            """
            result = await session.execute(
                text(query),
                {
                    "rule_id": str(rule_id),
                    "tenant_id": str(tenant_id),
                }
            )
            await session.commit()
            row = result.fetchone()

            if not row:
                raise ValueError(
                    f"Rule {rule_id} not found, already deleted, or cannot be deleted (only DRAFT/DEPRECATED rules can be deleted)"
                )

            return True

    # =========================================================================
    # Decision Operations
    # =========================================================================

    async def list_decisions(
        self,
        tenant_id: UUID,
        decision_type: Optional[str] = None,
        outcome: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[List[Decision], int]:
        """List decisions in a tenant."""
        async with self._session_factory() as session:
            base_query = """
                SELECT
                    decision_id, tenant_id, decision_type, context, outcome,
                    rule_matched_id, rule_version, approval_workflow_id,
                    idempotency_key, latency_ms, created_at, metadata
                FROM decisions
                WHERE tenant_id = :tenant_id
            """
            params = {"tenant_id": str(tenant_id)}

            if decision_type:
                base_query += " AND decision_type = :decision_type"
                params["decision_type"] = decision_type

            if outcome:
                base_query += " AND outcome = :outcome"
                params["outcome"] = outcome

            # Count total
            count_query = f"SELECT COUNT(*) FROM ({base_query}) sub"
            result = await session.execute(text(count_query), params)
            total = result.scalar() or 0

            # Add pagination
            offset = (page - 1) * limit
            paginated_query = f"{base_query} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = await session.execute(text(paginated_query), params)
            rows = result.fetchall()

            decisions = [
                Decision(
                    id=row.decision_id,
                    tenant_id=row.tenant_id,
                    decision_type=row.decision_type,
                    context=row.context or {},
                    outcome=DecisionOutcome(row.outcome),
                    rule_matched_id=row.rule_matched_id,
                    rule_version=row.rule_version,
                    approval_workflow_id=row.approval_workflow_id,
                    idempotency_key=row.idempotency_key,
                    latency_ms=row.latency_ms,
                    created_at=row.created_at,
                    metadata=row.metadata,
                )
                for row in rows
            ]

            return decisions, total

    async def get_decision(
        self, tenant_id: UUID, decision_id: UUID
    ) -> Optional[Decision]:
        """Get decision by ID."""
        async with self._session_factory() as session:
            query = """
                SELECT
                    decision_id, tenant_id, decision_type, context, outcome,
                    rule_matched_id, rule_version, approval_workflow_id,
                    idempotency_key, latency_ms, created_at, metadata
                FROM decisions
                WHERE decision_id = :decision_id AND tenant_id = :tenant_id
            """
            result = await session.execute(
                text(query),
                {"decision_id": str(decision_id), "tenant_id": str(tenant_id)}
            )
            row = result.fetchone()

            if not row:
                return None

            return Decision(
                id=row.decision_id,
                tenant_id=row.tenant_id,
                decision_type=row.decision_type,
                context=row.context or {},
                outcome=DecisionOutcome(row.outcome),
                rule_matched_id=row.rule_matched_id,
                rule_version=row.rule_version,
                approval_workflow_id=row.approval_workflow_id,
                idempotency_key=row.idempotency_key,
                latency_ms=row.latency_ms,
                created_at=row.created_at,
                metadata=row.metadata,
            )

    async def get_decision_events(
        self, tenant_id: UUID, decision_id: UUID
    ) -> List[dict]:
        """Get events for a decision."""
        async with self._session_factory() as session:
            query = """
                SELECT
                    event_id, event_type, payload, metadata, occurred_at
                FROM event_log
                WHERE tenant_id = :tenant_id
                  AND aggregate_id = :decision_id
                  AND aggregate_type = 'decision'
                ORDER BY occurred_at ASC
            """
            result = await session.execute(
                text(query),
                {"decision_id": str(decision_id), "tenant_id": str(tenant_id)}
            )
            rows = result.fetchall()

            return [
                {
                    "id": str(row.event_id),
                    "event_type": row.event_type,
                    "payload": row.payload,
                    "metadata": row.metadata,
                    "occurred_at": row.occurred_at.isoformat() if row.occurred_at else None,
                }
                for row in rows
            ]

    async def get_decision_types(self, tenant_id: UUID) -> List[str]:
        """Get distinct decision types available in tenant."""
        async with self._session_factory() as session:
            query = """
                SELECT DISTINCT decision_type
                FROM rules
                WHERE tenant_id = :tenant_id
                  AND deleted_at IS NULL
                ORDER BY decision_type
            """
            result = await session.execute(
                text(query),
                {"tenant_id": str(tenant_id)}
            )
            rows = result.fetchall()
            return [row.decision_type for row in rows]
