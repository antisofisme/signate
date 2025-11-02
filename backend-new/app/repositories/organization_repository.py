"""
Organization Repository - Database Access untuk Multi-Tenant Organization
========================================================================

CENTRALIZED QUERIES untuk organizations table
Ini adalah CRITICAL repository untuk multi-tenant functionality
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.repositories.base import BaseRepository
from app.models.organization import Organization


class OrganizationRepository(BaseRepository):
    """
    Organization Repository untuk multi-tenant management

    CRITICAL FUNCTIONALITY:
    - Organization CRUD
    - PIN management (8-digit unique)
    - User membership management
    - Data isolation enforcement
    - Quota & subscription management
    """

    def __init__(self, db: Session):
        super().__init__(Organization, db)
        self.db = db

    # =========================================================================
    # ORGANIZATION-SPECIFIC QUERIES
    # =========================================================================

    def get_by_slug(self, slug: str) -> Optional[Organization]:
        """
        Get organization by slug (unique URL-friendly identifier)

        Example:
            org = org_repo.get_by_slug("acme-corp")
        """
        return self.db.query(self.model).filter(
            self.model.slug == slug
        ).first()

    def get_by_pin(self, pin: str) -> Optional[Organization]:
        """
        Get organization by PIN (untuk device/user registration)

        Business rule: PIN adalah 8-digit unique code

        Example:
            org = org_repo.get_by_pin("12345678")
        """
        return self.db.query(self.model).filter(
            self.model.organization_pin == pin
        ).first()

    def get_active_organizations(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Organization]:
        """
        Get all active organizations

        Example:
            orgs = org_repo.get_active_organizations()
        """
        return self.db.query(self.model).filter(
            self.model.is_active == True
        ).offset(skip).limit(limit).all()

    def get_user_organizations(self, user_id: int) -> List[Organization]:
        """
        Get all organizations that a user is member of

        Joins through user_organizations table

        Example:
            user_orgs = org_repo.get_user_organizations(user_id=123)
        """
        from app.models.user_organization import UserOrganization

        return self.db.query(self.model).join(
            UserOrganization,
            UserOrganization.organization_id == self.model.id
        ).filter(
            UserOrganization.user_id == user_id
        ).all()

    def check_device_quota(self, organization_id: int) -> Dict[str, Any]:
        """
        Check device quota untuk organization

        Returns:
            {
                "max_devices": 10,
                "current_devices": 5,
                "available": 5,
                "can_add": True
            }
        """
        from app.models.device import Device

        org = self.get(organization_id)
        if not org:
            return {
                "max_devices": 0,
                "current_devices": 0,
                "available": 0,
                "can_add": False
            }

        current = self.db.query(func.count(Device.id)).filter(
            Device.organization_id == organization_id,
            Device.status.in_(["active", "pending"])
        ).scalar() or 0

        return {
            "max_devices": org.max_devices,
            "current_devices": current,
            "available": org.max_devices - current,
            "can_add": current < org.max_devices
        }

    def check_user_quota(self, organization_id: int) -> Dict[str, Any]:
        """
        Check user quota untuk organization

        Returns:
            {
                "max_users": 5,
                "current_users": 3,
                "available": 2,
                "can_add": True
            }
        """
        from app.models.user_organization import UserOrganization

        org = self.get(organization_id)
        if not org:
            return {
                "max_users": 0,
                "current_users": 0,
                "available": 0,
                "can_add": False
            }

        current = self.db.query(func.count(UserOrganization.id)).filter(
            UserOrganization.organization_id == organization_id
        ).scalar() or 0

        return {
            "max_users": org.max_users,
            "current_users": current,
            "available": org.max_users - current,
            "can_add": current < org.max_users
        }

    def get_storage_usage(self, organization_id: int) -> Dict[str, Any]:
        """
        Get storage usage statistics untuk organization

        Returns:
            {
                "max_storage_gb": 10,
                "used_storage_gb": 2.5,
                "available_gb": 7.5,
                "usage_percentage": 25.0
            }
        """
        from app.models.content import Content

        org = self.get(organization_id)
        if not org:
            return {
                "max_storage_gb": 0,
                "used_storage_gb": 0,
                "available_gb": 0,
                "usage_percentage": 0
            }

        # Sum file sizes (assuming file_size is in bytes)
        total_bytes = self.db.query(
            func.coalesce(func.sum(Content.file_size), 0)
        ).filter(
            Content.organization_id == organization_id
        ).scalar() or 0

        used_gb = total_bytes / (1024 ** 3)  # Convert bytes to GB
        max_gb = org.max_storage_gb
        available_gb = max_gb - used_gb
        usage_pct = (used_gb / max_gb * 100) if max_gb > 0 else 0

        return {
            "max_storage_gb": max_gb,
            "used_storage_gb": round(used_gb, 2),
            "available_gb": round(available_gb, 2),
            "usage_percentage": round(usage_pct, 1)
        }

    def get_organization_stats(self, organization_id: int) -> Dict[str, Any]:
        """
        Get comprehensive statistics untuk organization

        Returns complete overview of organization resources
        """
        from app.models.device import Device
        from app.models.content import Content
        from app.models.playlist import Playlist
        from app.models.user_organization import UserOrganization

        org = self.get(organization_id)
        if not org:
            return {}

        stats = {
            "organization_id": organization_id,
            "name": org.name,
            "slug": org.slug,
            "is_active": org.is_active,
            "subscription_tier": org.subscription_tier,

            # Device stats
            "total_devices": self.db.query(func.count(Device.id)).filter(
                Device.organization_id == organization_id
            ).scalar() or 0,

            "active_devices": self.db.query(func.count(Device.id)).filter(
                Device.organization_id == organization_id,
                Device.status == "active"
            ).scalar() or 0,

            # Content stats
            "total_content": self.db.query(func.count(Content.id)).filter(
                Content.organization_id == organization_id
            ).scalar() or 0,

            # Playlist stats
            "total_playlists": self.db.query(func.count(Playlist.id)).filter(
                Playlist.organization_id == organization_id
            ).scalar() or 0,

            # User stats
            "total_users": self.db.query(func.count(UserOrganization.id)).filter(
                UserOrganization.organization_id == organization_id
            ).scalar() or 0,

            # Quotas
            "device_quota": self.check_device_quota(organization_id),
            "user_quota": self.check_user_quota(organization_id),
            "storage": self.get_storage_usage(organization_id)
        }

        return stats

    def search_organizations(self, query: str) -> List[Organization]:
        """
        Search organizations by name or slug

        Example:
            results = org_repo.search_organizations("acme")
        """
        search_pattern = f"%{query}%"
        return self.db.query(self.model).filter(
            or_(
                self.model.name.ilike(search_pattern),
                self.model.slug.ilike(search_pattern)
            )
        ).all()

    def generate_unique_pin(self) -> str:
        """
        Generate unique 8-digit PIN for organization

        Business rule: PIN must be unique across all organizations
        """
        import random

        max_attempts = 100
        for _ in range(max_attempts):
            # Generate 8-digit PIN
            pin = ''.join([str(random.randint(0, 9)) for _ in range(8)])

            # Check if unique
            existing = self.get_by_pin(pin)
            if not existing:
                return pin

        raise ValueError("Could not generate unique PIN after 100 attempts")

    def is_subscription_active(self, organization_id: int) -> bool:
        """
        Check if organization subscription is active

        Returns True if:
        - No expiry date (lifetime)
        - Expiry date is in the future
        """
        org = self.get(organization_id)
        if not org:
            return False

        if not org.subscription_expires_at:
            return True  # No expiry = active

        from datetime import datetime
        return datetime.utcnow() < org.subscription_expires_at

    def deactivate(self, organization_id: int) -> bool:
        """
        Deactivate organization (soft delete)

        Sets is_active = False
        """
        return self.update(organization_id, {"is_active": False}) is not None
