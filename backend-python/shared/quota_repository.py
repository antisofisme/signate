"""
Shared Quota Repository
Handles cross-service resource counting for quota enforcement
"""

from typing import Dict
from sqlalchemy import func, Table, MetaData, Column, Integer, BigInteger
from sqlalchemy.orm import Session


class QuotaRepository:
    """
    Repository for quota-related queries across services

    This is a shared repository that performs read-only queries
    to count resources across different services without violating
    Clean Architecture principles (no direct model imports from services).

    Uses SQLAlchemy Core (table reflection) instead of ORM models
    to avoid coupling with service-specific repository layers.
    """

    def __init__(self, db: Session):
        self.db = db

    def count_devices(self, organization_id: int) -> int:
        """Count active devices for an organization"""
        # Use raw SQL to avoid importing DeviceModel
        result = self.db.execute(
            """
            SELECT COUNT(*)
            FROM devices
            WHERE organization_id = :org_id
            """,
            {"org_id": organization_id}
        ).scalar()

        return result or 0

    def count_users(self, organization_id: int, active_only: bool = True) -> int:
        """Count users for an organization"""
        if active_only:
            result = self.db.execute(
                """
                SELECT COUNT(*)
                FROM users
                WHERE organization_id = :org_id
                  AND is_active = true
                """,
                {"org_id": organization_id}
            ).scalar()
        else:
            result = self.db.execute(
                """
                SELECT COUNT(*)
                FROM users
                WHERE organization_id = :org_id
                """,
                {"org_id": organization_id}
            ).scalar()

        return result or 0

    def get_content_stats(self, organization_id: int) -> Dict[str, int]:
        """
        Get content statistics for an organization

        Returns:
            Dict with 'count' (number of items) and 'total_size' (bytes)
        """
        result = self.db.execute(
            """
            SELECT
                COUNT(*) as count,
                COALESCE(SUM(file_size), 0) as total_size
            FROM contents
            WHERE organization_id = :org_id
              AND deleted_at IS NULL
            """,
            {"org_id": organization_id}
        ).first()

        return {
            'count': result.count if result else 0,
            'total_size': int(result.total_size) if result else 0
        }

    def count_playlists(self, organization_id: int) -> int:
        """Count active playlists for an organization"""
        result = self.db.execute(
            """
            SELECT COUNT(*)
            FROM playlists
            WHERE organization_id = :org_id
              AND deleted_at IS NULL
            """,
            {"org_id": organization_id}
        ).scalar()

        return result or 0

    def count_devices_with_lock(self, organization_id: int) -> int:
        """
        Count devices with row-level lock for atomic quota enforcement

        This uses SELECT ... FOR UPDATE to prevent race conditions
        during concurrent device creation.
        """
        result = self.db.execute(
            """
            SELECT COUNT(*)
            FROM devices
            WHERE organization_id = :org_id
            FOR UPDATE
            """,
            {"org_id": organization_id}
        ).scalar()

        return result or 0

    def count_users_with_lock(self, organization_id: int) -> int:
        """
        Count active users with row-level lock for atomic quota enforcement
        """
        result = self.db.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE organization_id = :org_id
              AND is_active = true
            FOR UPDATE
            """,
            {"org_id": organization_id}
        ).scalar()

        return result or 0

    def get_content_stats_with_lock(self, organization_id: int) -> Dict[str, int]:
        """
        Get content statistics with row-level lock for atomic quota enforcement
        """
        result = self.db.execute(
            """
            SELECT
                COUNT(*) as count,
                COALESCE(SUM(file_size), 0) as total_size
            FROM contents
            WHERE organization_id = :org_id
              AND deleted_at IS NULL
            FOR UPDATE
            """,
            {"org_id": organization_id}
        ).first()

        return {
            'count': result.count if result else 0,
            'total_size': int(result.total_size) if result else 0
        }

    def count_playlists_with_lock(self, organization_id: int) -> int:
        """
        Count playlists with row-level lock for atomic quota enforcement
        """
        result = self.db.execute(
            """
            SELECT COUNT(*)
            FROM playlists
            WHERE organization_id = :org_id
              AND deleted_at IS NULL
            FOR UPDATE
            """,
            {"org_id": organization_id}
        ).scalar()

        return result or 0
