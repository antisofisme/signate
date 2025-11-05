"""Get AuditLog Use Case"""

from ..domain.audit_log import AuditLog
from ..domain.interfaces import IAuditLogRepository
from shared.errors import NotFoundError


class GetAuditLogUseCase:
    """Use case for getting single audit log by ID"""

    def __init__(self, audit_log_repo: IAuditLogRepository):
        self.audit_log_repo = audit_log_repo

    def execute(self, log_id: int) -> AuditLog:
        """
        Get audit log by ID

        Args:
            log_id: Audit log ID

        Returns:
            AuditLog entity

        Raises:
            NotFoundError: If audit log not found
        """

        audit_log = self.audit_log_repo.find_by_id(log_id)

        if not audit_log:
            raise NotFoundError(
                message=f"Audit log dengan ID {log_id} tidak ditemukan",
                details={"resource_type": "audit_log", "resource_id": log_id}
            )

        return audit_log
