"""
Organization Service - Multi-Tenant Organization Management
==========================================================

CRITICAL SERVICE LAYER untuk Multi-Tenant Functionality

Business Logic:
- Organization CRUD dengan validation
- PIN generation & validation (8-digit unique)
- Quota management (devices, users, storage)
- User-organization membership
- Organization switching
- Statistics & reporting
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ForbiddenException
)

logger = logging.getLogger(__name__)


class OrganizationService:
    """
    Organization Service untuk Multi-Tenant Management

    CRITICAL FUNCTIONALITY:
    - Organization lifecycle management
    - Multi-tenant data isolation
    - Quota enforcement
    - User membership management
    """

    def __init__(self, db: Session):
        self.db = db
        self.org_repo = OrganizationRepository(db)
        self.user_repo = UserRepository(db)

    # =========================================================================
    # ORGANIZATION CRUD
    # =========================================================================

    def create_organization(
        self,
        name: str,
        slug: str,
        description: Optional[str] = None,
        max_devices: int = 10,
        max_users: int = 5,
        max_storage_gb: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create new organization dengan auto-generated PIN

        Business Rules:
        - Name required (min 3 chars)
        - Slug must be unique & URL-friendly
        - Auto-generate 8-digit unique PIN
        - Set default quotas

        Example:
            org = org_service.create_organization(
                name="Acme Corp",
                slug="acme-corp",
                max_devices=50
            )
        """
        # Validation
        if not name or len(name.strip()) < 3:
            raise BadRequestException("Organization name must be at least 3 characters")

        if not slug or len(slug.strip()) < 3:
            raise BadRequestException("Organization slug must be at least 3 characters")

        # Check slug uniqueness
        existing = self.org_repo.get_by_slug(slug)
        if existing:
            raise BadRequestException(f"Organization with slug '{slug}' already exists")

        # Generate unique PIN
        organization_pin = self.org_repo.generate_unique_pin()

        org_data = {
            "name": name.strip(),
            "slug": slug.strip().lower(),
            "description": description,
            "organization_pin": organization_pin,
            "max_devices": max_devices,
            "max_users": max_users,
            "max_storage_gb": max_storage_gb,
            "is_active": True,
            **kwargs
        }

        org = self.org_repo.create(org_data)

        logger.info(f"Organization created: {org.id} - {org.name} (PIN: {organization_pin})")

        return {
            **org.to_dict(),
            "organization_pin": organization_pin  # Return PIN only on creation
        }

    def get_organization(self, organization_id: int) -> Dict[str, Any]:
        """
        Get organization by ID dengan enrichment

        Returns organization with stats
        """
        org = self.org_repo.get(organization_id)
        if not org:
            raise NotFoundException(f"Organization {organization_id} not found")

        # Enrich with stats
        stats = self.org_repo.get_organization_stats(organization_id)

        return {
            **org.to_dict(),
            "stats": stats
        }

    def update_organization(
        self,
        organization_id: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update organization

        Business Rules:
        - Cannot change PIN after creation
        - Cannot change slug after creation
        - Quota changes take effect immediately
        """
        org = self.org_repo.get(organization_id)
        if not org:
            raise NotFoundException(f"Organization {organization_id} not found")

        # Validation
        if "organization_pin" in updates:
            raise BadRequestException("Cannot change organization PIN")

        if "slug" in updates and updates["slug"] != org.slug:
            raise BadRequestException("Cannot change organization slug")

        updated_org = self.org_repo.update(organization_id, updates)

        logger.info(f"Organization updated: {organization_id}")

        return updated_org.to_dict()

    def delete_organization(self, organization_id: int) -> bool:
        """
        Delete (deactivate) organization

        Business Rule:
        - Soft delete only (set is_active = False)
        - Check if has active resources
        """
        org = self.org_repo.get(organization_id)
        if not org:
            raise NotFoundException(f"Organization {organization_id} not found")

        # Check quotas - warn if has active resources
        stats = self.org_repo.get_organization_stats(organization_id)
        if stats.get("active_devices", 0) > 0:
            logger.warning(f"Deactivating org {organization_id} with {stats['active_devices']} active devices")

        success = self.org_repo.deactivate(organization_id)

        logger.warning(f"Organization deactivated: {organization_id} - {org.name}")

        return success

    # =========================================================================
    # PIN MANAGEMENT
    # =========================================================================

    def verify_pin(self, pin: str) -> Optional[Dict[str, Any]]:
        """
        Verify organization PIN

        Returns organization if PIN is valid, None otherwise

        Example:
            org = org_service.verify_pin("12345678")
        """
        if not pin or len(pin) != 8:
            return None

        org = self.org_repo.get_by_pin(pin)
        if not org:
            return None

        if not org.is_active:
            logger.warning(f"Attempted to use PIN for inactive org: {org.id}")
            return None

        return org.to_dict()

    def regenerate_pin(self, organization_id: int) -> str:
        """
        Regenerate organization PIN

        Business Rule:
        - Only super admin can regenerate PIN
        - Old PIN immediately invalid

        Returns: New PIN
        """
        org = self.org_repo.get(organization_id)
        if not org:
            raise NotFoundException(f"Organization {organization_id} not found")

        # Generate new PIN
        new_pin = self.org_repo.generate_unique_pin()

        self.org_repo.update(organization_id, {"organization_pin": new_pin})

        logger.warning(f"PIN regenerated for organization: {organization_id}")

        return new_pin

    # =========================================================================
    # QUOTA MANAGEMENT
    # =========================================================================

    def check_device_quota(
        self,
        organization_id: int,
        raise_if_exceeded: bool = False
    ) -> Dict[str, Any]:
        """
        Check if organization can add more devices

        Args:
            organization_id: Organization ID
            raise_if_exceeded: If True, raise exception if quota exceeded

        Returns:
            Quota info dict

        Raises:
            ForbiddenException if raise_if_exceeded=True and quota exceeded
        """
        quota = self.org_repo.check_device_quota(organization_id)

        if raise_if_exceeded and not quota["can_add"]:
            raise ForbiddenException(
                f"Device quota exceeded. Max: {quota['max_devices']}, "
                f"Current: {quota['current_devices']}"
            )

        return quota

    def check_user_quota(
        self,
        organization_id: int,
        raise_if_exceeded: bool = False
    ) -> Dict[str, Any]:
        """
        Check if organization can add more users

        Args:
            organization_id: Organization ID
            raise_if_exceeded: If True, raise exception if quota exceeded

        Returns:
            Quota info dict

        Raises:
            ForbiddenException if raise_if_exceeded=True and quota exceeded
        """
        quota = self.org_repo.check_user_quota(organization_id)

        if raise_if_exceeded and not quota["can_add"]:
            raise ForbiddenException(
                f"User quota exceeded. Max: {quota['max_users']}, "
                f"Current: {quota['current_users']}"
            )

        return quota

    def check_storage_quota(
        self,
        organization_id: int,
        additional_gb: float = 0,
        raise_if_exceeded: bool = False
    ) -> Dict[str, Any]:
        """
        Check storage quota

        Args:
            organization_id: Organization ID
            additional_gb: Additional storage to check (in GB)
            raise_if_exceeded: If True, raise exception if quota exceeded

        Returns:
            Storage info dict

        Raises:
            ForbiddenException if raise_if_exceeded=True and quota exceeded
        """
        storage = self.org_repo.get_storage_usage(organization_id)

        can_add = (storage["available_gb"] - additional_gb) >= 0

        if raise_if_exceeded and not can_add:
            raise ForbiddenException(
                f"Storage quota exceeded. Max: {storage['max_storage_gb']} GB, "
                f"Used: {storage['used_storage_gb']} GB, "
                f"Trying to add: {additional_gb} GB"
            )

        storage["can_add_gb"] = additional_gb
        storage["would_exceed"] = not can_add

        return storage

    # =========================================================================
    # USER MEMBERSHIP
    # =========================================================================

    def add_user_to_organization(
        self,
        organization_id: int,
        user_id: int,
        role_id: int,
        is_default: bool = False
    ) -> bool:
        """
        Add user to organization

        Business Rules:
        - Check user quota first
        - User can be in multiple organizations
        - Only one default organization per user
        """
        # Check quota
        self.check_user_quota(organization_id, raise_if_exceeded=True)

        # TODO: Implement via UserOrganization model
        # For now, this is a placeholder
        logger.info(f"User {user_id} added to organization {organization_id}")

        return True

    def remove_user_from_organization(
        self,
        organization_id: int,
        user_id: int
    ) -> bool:
        """
        Remove user from organization

        Business Rule:
        - Cannot remove last admin
        """
        # TODO: Check if last admin
        # TODO: Implement via UserOrganization model

        logger.info(f"User {user_id} removed from organization {organization_id}")

        return True

    # =========================================================================
    # STATISTICS & REPORTING
    # =========================================================================

    def get_organization_stats(self, organization_id: int) -> Dict[str, Any]:
        """
        Get comprehensive organization statistics

        Returns:
            Complete stats including quotas, usage, resources
        """
        org = self.org_repo.get(organization_id)
        if not org:
            raise NotFoundException(f"Organization {organization_id} not found")

        stats = self.org_repo.get_organization_stats(organization_id)

        # Add subscription info
        stats["subscription_active"] = self.org_repo.is_subscription_active(organization_id)

        return stats

    def list_organizations(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List organizations with filters and search

        Args:
            skip: Pagination offset
            limit: Pagination limit
            filters: Filter criteria (e.g., {"is_active": True})
            search: Search query for name/slug

        Returns:
            List of organizations with basic info
        """
        from app.models.organization import Organization

        query = self.db.query(Organization)

        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(Organization, key):
                    query = query.filter(getattr(Organization, key) == value)
        else:
            # Default: only show active organizations
            query = query.filter(Organization.is_active == True)

        # Apply search
        if search and len(search.strip()) >= 2:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                (Organization.name.ilike(search_term)) |
                (Organization.slug.ilike(search_term))
            )

        # Apply pagination
        orgs = query.offset(skip).limit(limit).all()

        return [org.to_dict() for org in orgs]

    def search_organizations(self, query: str) -> List[Dict[str, Any]]:
        """
        Search organizations by name or slug

        Example:
            results = org_service.search_organizations("acme")
        """
        if not query or len(query.strip()) < 2:
            raise BadRequestException("Search query must be at least 2 characters")

        orgs = self.org_repo.search_organizations(query.strip())

        return [org.to_dict() for org in orgs]

    def get_organization_with_stats(self, organization_id: int) -> Dict[str, Any]:
        """
        Get organization with comprehensive statistics

        Combines get_organization() and get_organization_stats()

        Returns:
            Organization data with embedded stats
        """
        org_data = self.get_organization(organization_id)
        stats = self.get_organization_stats(organization_id)

        # Merge org data with stats
        return {
            **org_data,
            "stats": stats
        }

    def count_organizations(
        self,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None
    ) -> int:
        """
        Count organizations with filters

        Args:
            filters: Filter criteria (e.g., {"is_active": True})
            search: Search query for name/slug

        Returns:
            Total count of matching organizations
        """
        from sqlalchemy import func
        from app.models.organization import Organization

        query = self.db.query(func.count(Organization.id))

        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(Organization, key):
                    query = query.filter(getattr(Organization, key) == value)

        # Apply search
        if search and len(search.strip()) >= 2:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                (Organization.name.ilike(search_term)) |
                (Organization.slug.ilike(search_term))
            )

        return query.scalar() or 0

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _validate_quota_update(
        self,
        organization_id: int,
        quota_type: str,
        new_value: int
    ) -> bool:
        """
        Validate quota update

        Business Rule:
        - Cannot set quota lower than current usage
        """
        if quota_type == "max_devices":
            current = self.org_repo.check_device_quota(organization_id)
            if new_value < current["current_devices"]:
                raise BadRequestException(
                    f"Cannot set max_devices to {new_value}. "
                    f"Current usage: {current['current_devices']}"
                )

        elif quota_type == "max_users":
            current = self.org_repo.check_user_quota(organization_id)
            if new_value < current["current_users"]:
                raise BadRequestException(
                    f"Cannot set max_users to {new_value}. "
                    f"Current usage: {current['current_users']}"
                )

        elif quota_type == "max_storage_gb":
            current = self.org_repo.get_storage_usage(organization_id)
            if new_value < current["used_storage_gb"]:
                raise BadRequestException(
                    f"Cannot set max_storage_gb to {new_value}. "
                    f"Current usage: {current['used_storage_gb']} GB"
                )

        return True
