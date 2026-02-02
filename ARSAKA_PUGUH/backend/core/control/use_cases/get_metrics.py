"""
Get Metrics Use Case
"""

from uuid import UUID

from ..interfaces import IControlRepository


class GetMetricsUseCase:
    def __init__(self, repository: IControlRepository):
        self._repository = repository

    async def execute(self, tenant_id: UUID) -> dict:
        return await self._repository.get_metrics(tenant_id)

    async def get_decision_metrics(self, tenant_id: UUID) -> dict:
        return await self._repository.get_decision_metrics(tenant_id)

    async def get_workflow_metrics(self, tenant_id: UUID) -> dict:
        return await self._repository.get_workflow_metrics(tenant_id)

    async def get_trends(self, tenant_id: UUID, period: str = "7d") -> list:
        return await self._repository.get_metrics_trends(tenant_id, period)
