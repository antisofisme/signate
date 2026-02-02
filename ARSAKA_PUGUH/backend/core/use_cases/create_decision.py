"""
CreateDecisionUseCase

Orchestrates decision creation with rule evaluation and idempotency.
Source: INFRA-LAY3-002 §2 (Decision Creation Transaction Standards)
"""

import hashlib
import json
from typing import Optional

from ..domain import (
    Decision,
    Workflow,
    TenantId,
    Context,
    IdempotencyKey,
    Metadata
)
from .interfaces import (
    IUnitOfWork,
    IDecisionRepository,
    IWorkflowRepository,
    IRuleRepository,
    IIdempotencyRepository,
    IRuleEvaluationService
)
from .dtos import CreateDecisionInput, CreateDecisionOutput
from .exceptions import IdempotencyConflictError


class CreateDecisionUseCase:
    """
    Use case: Create decision with rule evaluation
    Source: INFRA-LAY3-002 §2.3
    """

    def __init__(
        self,
        uow: IUnitOfWork,
        decision_repository: IDecisionRepository,
        workflow_repository: IWorkflowRepository,
        rule_repository: IRuleRepository,
        idempotency_repository: IIdempotencyRepository,
        rule_evaluation_service: IRuleEvaluationService
    ):
        self._uow = uow
        self._decision_repo = decision_repository
        self._workflow_repo = workflow_repository
        self._rule_repo = rule_repository
        self._idempotency_repo = idempotency_repository
        self._rule_eval_service = rule_evaluation_service

    async def execute(self, input_dto: CreateDecisionInput) -> CreateDecisionOutput:
        """
        Execute decision creation
        Transaction steps per INFRA-LAY3-002 §2.3
        """
        tenant_id = TenantId(input_dto.tenant_id)
        context = Context(input_dto.context)

        idempotency_key = None
        if input_dto.idempotency_key:
            idempotency_key = IdempotencyKey(input_dto.idempotency_key)

        metadata = Metadata(
            trace_id=input_dto.trace_id,
            requester_user_id=input_dto.requester_user_id,
            source='core'
        )

        if idempotency_key:
            cached_decision_id = await self._idempotency_repo.find(
                tenant_id,
                idempotency_key
            )
            if cached_decision_id:
                context_hash = self._compute_context_hash(context)
                cached_hash = await self._idempotency_repo.get_context_hash(
                    tenant_id,
                    idempotency_key
                )
                if cached_hash and cached_hash != context_hash:
                    raise IdempotencyConflictError(
                        existing_decision_id=cached_decision_id.value
                    )

                cached_decision = await self._decision_repo.find_by_id(
                    cached_decision_id,
                    tenant_id
                )
                if cached_decision:
                    return CreateDecisionOutput(
                        decision_id=cached_decision.decision_id.value,
                        outcome=cached_decision.outcome.value,
                        rule_matched_id=cached_decision.rule_matched_id.value if cached_decision.rule_matched_id else None,
                        rule_version=str(cached_decision.rule_version) if cached_decision.rule_version else None,
                        workflow_id=None,
                        created_at=cached_decision.created_at,
                        events=[]
                    )

        async with self._uow:
            rules = await self._rule_repo.find_active_rules(
                tenant_id,
                input_dto.decision_type
            )

            eval_result = await self._rule_eval_service.evaluate(rules, context)

            decision = Decision.create(
                tenant_id=tenant_id,
                decision_type=input_dto.decision_type,
                context=context,
                outcome=eval_result.outcome,
                rule_matched_id=eval_result.rule_matched_id,
                rule_version=eval_result.rule_version,
                idempotency_key=idempotency_key,
                metadata=metadata
            )

            await self._decision_repo.save(decision)

            workflow_id = None
            if decision.requires_workflow():
                approver_role = eval_result.outcome.value
                if hasattr(eval_result, 'approver_role'):
                    approver_role = eval_result.approver_role

                workflow = Workflow.create(
                    decision_id=decision.decision_id,
                    tenant_id=tenant_id,
                    approver_role=approver_role,
                    metadata=metadata
                )
                await self._workflow_repo.save(workflow)
                workflow_id = workflow.workflow_id.value

                decision_events = decision.collect_events()
                workflow_events = workflow.collect_events()
                all_events = decision_events + workflow_events
            else:
                all_events = decision.collect_events()

            if idempotency_key:
                context_hash = self._compute_context_hash(context)
                await self._idempotency_repo.save(
                    tenant_id,
                    idempotency_key,
                    decision.decision_id,
                    context_hash
                )

            await self._uow.commit()

        return CreateDecisionOutput(
            decision_id=decision.decision_id.value,
            outcome=decision.outcome.value,
            rule_matched_id=decision.rule_matched_id.value if decision.rule_matched_id else None,
            rule_version=str(decision.rule_version) if decision.rule_version else None,
            workflow_id=workflow_id,
            created_at=decision.created_at,
            events=all_events
        )

    def _compute_context_hash(self, context: Context) -> str:
        """
        Compute SHA-256 hash of canonicalized context
        Source: Architecture Layer 2.6 (Idempotency Model)
        """
        canonical_json = json.dumps(context.to_dict(), sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
