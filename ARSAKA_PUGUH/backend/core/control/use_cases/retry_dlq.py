"""
Retry DLQ Event Use Case
"""

from uuid import UUID

from ..interfaces import IControlRepository


class RetryDLQUseCase:
    """Use case for retrying dead-letter queue events."""

    def __init__(self, repository: IControlRepository):
        self._repository = repository

    async def execute(self, tenant_id: UUID, dlq_entry_id: UUID) -> dict:
        """
        Retry a DLQ event by resetting it for reprocessing.

        Args:
            tenant_id: The tenant ID
            dlq_entry_id: The DLQ entry ID to retry

        Returns:
            dict with retry status

        Raises:
            ValueError: If DLQ entry not found or already reprocessed
        """
        result = await self._repository.retry_dlq_event(
            tenant_id=tenant_id,
            dlq_entry_id=dlq_entry_id,
        )
        return result

    async def get_dlq_event(self, tenant_id: UUID, dlq_entry_id: UUID) -> dict:
        """Get a single DLQ event."""
        result = await self._repository.get_dlq_event(
            tenant_id=tenant_id,
            dlq_entry_id=dlq_entry_id,
        )
        if not result:
            raise ValueError(f"DLQ entry {dlq_entry_id} not found")
        return result
