"""
PUGUH SDK - Tenant Module

Multi-tenant management for PUGUH Platform.
Handles organization creation, member management, and invitations.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from enum import Enum
import httpx

from .exceptions import (
    PuguhError,
    TenantError,
    ValidationError,
    NetworkError,
)


class TenantPlan(str, Enum):
    """Tenant subscription plans."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class MemberRole(str, Enum):
    """Member role in tenant."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class InvitationStatus(str, Enum):
    """Invitation status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


@dataclass
class Tenant:
    """Tenant (organization) data."""
    tenant_id: str
    name: str
    slug: str
    owner_user_id: str
    plan: TenantPlan = TenantPlan.FREE
    status: TenantStatus = TenantStatus.ACTIVE
    billing_email: Optional[str] = None
    settings: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Plan limits
    max_members: int = 3
    max_projects: int = 1
    current_members: int = 0
    current_projects: int = 0


@dataclass
class Member:
    """Tenant member."""
    user_id: str
    tenant_id: str
    email: str
    display_name: str
    role: MemberRole
    joined_at: Optional[datetime] = None
    avatar_url: Optional[str] = None


@dataclass
class Invitation:
    """Member invitation."""
    invitation_id: str
    tenant_id: str
    email: str
    role: MemberRole
    status: InvitationStatus = InvitationStatus.PENDING
    invited_by_user_id: Optional[str] = None
    invited_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class TenantClient:
    """
    Tenant (organization) management client.

    Handles:
    - Creating and managing organizations
    - Inviting and managing members
    - Role management

    Example:
        ```python
        from puguh_sdk import PuguhClient

        client = PuguhClient(
            base_url="https://api.puguh.io",
            access_token="user_jwt_token"
        )

        # Create organization
        tenant = await client.tenants.create(
            name="My Company",
            billing_email="billing@mycompany.com"
        )

        # Invite member
        invitation = await client.tenants.invite_member(
            tenant_id=tenant.tenant_id,
            email="colleague@example.com",
            role=MemberRole.ADMIN
        )

        # List members
        members = await client.tenants.list_members(tenant.tenant_id)
        ```
    """

    def __init__(self, http_client: httpx.AsyncClient):
        """
        Initialize tenant client.

        Args:
            http_client: Shared HTTP client from PuguhClient
        """
        self._client = http_client

    def _handle_error(self, response: httpx.Response):
        """Handle error response and raise appropriate exception."""
        try:
            data = response.json()
            error_code = data.get("error", {}).get("code", "UNKNOWN_ERROR")
            message = data.get("error", {}).get("message", "An error occurred")
            details = data.get("error", {}).get("details", {})
        except Exception:
            error_code = "UNKNOWN_ERROR"
            message = response.text or f"HTTP {response.status_code}"
            details = {}

        if response.status_code == 404:
            raise TenantError(message, error_code, details)
        elif response.status_code == 403:
            raise TenantError(message, "FORBIDDEN", details)
        elif response.status_code == 422:
            raise ValidationError(message, details)
        else:
            raise PuguhError(message, error_code, details, response.status_code)

    def _parse_tenant(self, data: dict) -> Tenant:
        """Parse tenant from API response."""
        return Tenant(
            tenant_id=data["tenant_id"],
            name=data["name"],
            slug=data["slug"],
            owner_user_id=data["owner_user_id"],
            plan=TenantPlan(data.get("plan", "free")),
            status=TenantStatus(data.get("status", "active")),
            billing_email=data.get("billing_email"),
            settings=data.get("settings", {}),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
                if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
                if data.get("updated_at") else None,
            max_members=data.get("max_members", 3),
            max_projects=data.get("max_projects", 1),
            current_members=data.get("current_members", 0),
            current_projects=data.get("current_projects", 0),
        )

    def _parse_member(self, data: dict) -> Member:
        """Parse member from API response."""
        return Member(
            user_id=data["user_id"],
            tenant_id=data["tenant_id"],
            email=data["email"],
            display_name=data.get("display_name", ""),
            role=MemberRole(data.get("role", "member")),
            joined_at=datetime.fromisoformat(data["joined_at"].replace("Z", "+00:00"))
                if data.get("joined_at") else None,
            avatar_url=data.get("avatar_url"),
        )

    def _parse_invitation(self, data: dict) -> Invitation:
        """Parse invitation from API response."""
        return Invitation(
            invitation_id=data["invitation_id"],
            tenant_id=data["tenant_id"],
            email=data["email"],
            role=MemberRole(data.get("role", "member")),
            status=InvitationStatus(data.get("status", "pending")),
            invited_by_user_id=data.get("invited_by_user_id"),
            invited_at=datetime.fromisoformat(data["invited_at"].replace("Z", "+00:00"))
                if data.get("invited_at") else None,
            expires_at=datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
                if data.get("expires_at") else None,
        )

    async def create(
        self,
        name: str,
        billing_email: Optional[str] = None,
        settings: Optional[dict] = None,
    ) -> Tenant:
        """
        Create a new tenant (organization).

        Args:
            name: Organization name
            billing_email: Email for billing communications
            settings: Optional settings dictionary

        Returns:
            Created tenant

        Raises:
            ValidationError: If input validation fails
            NetworkError: If network request fails
        """
        try:
            payload = {"name": name}
            if billing_email:
                payload["billing_email"] = billing_email
            if settings:
                payload["settings"] = settings

            response = await self._client.post(
                "/api/v1/tenants",
                json=payload
            )

            if response.status_code not in (200, 201):
                self._handle_error(response)

            data = response.json()
            tenant_data = data.get("data", data)
            return self._parse_tenant(tenant_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def list(self) -> List[Tenant]:
        """
        List tenants (organizations) user belongs to.

        Returns:
            List of tenants

        Raises:
            NetworkError: If network request fails
        """
        try:
            response = await self._client.get("/api/v1/tenants")

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            tenants_data = data.get("data", [])
            return [self._parse_tenant(t) for t in tenants_data]
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def get(self, tenant_id: str) -> Tenant:
        """
        Get tenant details by ID.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Tenant details

        Raises:
            TenantError: If tenant not found or access denied
            NetworkError: If network request fails
        """
        try:
            response = await self._client.get(f"/api/v1/tenants/{tenant_id}")

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            tenant_data = data.get("data", data)
            return self._parse_tenant(tenant_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def update(
        self,
        tenant_id: str,
        name: Optional[str] = None,
        billing_email: Optional[str] = None,
        settings: Optional[dict] = None,
    ) -> Tenant:
        """
        Update tenant details.

        Args:
            tenant_id: Tenant UUID
            name: New organization name
            billing_email: New billing email
            settings: Updated settings

        Returns:
            Updated tenant

        Raises:
            TenantError: If tenant not found or access denied
            ValidationError: If input validation fails
            NetworkError: If network request fails
        """
        try:
            payload = {}
            if name is not None:
                payload["name"] = name
            if billing_email is not None:
                payload["billing_email"] = billing_email
            if settings is not None:
                payload["settings"] = settings

            response = await self._client.patch(
                f"/api/v1/tenants/{tenant_id}",
                json=payload
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            tenant_data = data.get("data", data)
            return self._parse_tenant(tenant_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def delete(self, tenant_id: str) -> bool:
        """
        Delete (soft delete) tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            True if deleted successfully

        Raises:
            TenantError: If tenant not found or access denied
            NetworkError: If network request fails
        """
        try:
            response = await self._client.delete(f"/api/v1/tenants/{tenant_id}")

            if response.status_code not in (200, 204):
                self._handle_error(response)

            return True
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    # -------------------------------------------------------------------------
    # Member Management
    # -------------------------------------------------------------------------

    async def invite_member(
        self,
        tenant_id: str,
        email: str,
        role: MemberRole = MemberRole.MEMBER,
    ) -> Invitation:
        """
        Invite a new member to tenant.

        Args:
            tenant_id: Tenant UUID
            email: Email of person to invite
            role: Role to assign (owner, admin, member, viewer)

        Returns:
            Created invitation

        Raises:
            TenantError: If tenant not found or access denied
            ValidationError: If input validation fails
            NetworkError: If network request fails
        """
        try:
            response = await self._client.post(
                f"/api/v1/tenants/{tenant_id}/invitations",
                json={
                    "email": email,
                    "role": role.value,
                }
            )

            if response.status_code not in (200, 201):
                self._handle_error(response)

            data = response.json()
            invitation_data = data.get("data", data)
            return self._parse_invitation(invitation_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def list_members(self, tenant_id: str) -> List[Member]:
        """
        List all members of a tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            List of members

        Raises:
            TenantError: If tenant not found or access denied
            NetworkError: If network request fails
        """
        try:
            response = await self._client.get(
                f"/api/v1/tenants/{tenant_id}/members"
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            members_data = data.get("data", [])
            return [self._parse_member(m) for m in members_data]
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def get_member(self, tenant_id: str, user_id: str) -> Member:
        """
        Get specific member details.

        Args:
            tenant_id: Tenant UUID
            user_id: User UUID

        Returns:
            Member details

        Raises:
            TenantError: If member not found
            NetworkError: If network request fails
        """
        try:
            response = await self._client.get(
                f"/api/v1/tenants/{tenant_id}/members/{user_id}"
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            member_data = data.get("data", data)
            return self._parse_member(member_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def update_member_role(
        self,
        tenant_id: str,
        user_id: str,
        role: MemberRole,
    ) -> Member:
        """
        Update member's role.

        Args:
            tenant_id: Tenant UUID
            user_id: User UUID
            role: New role

        Returns:
            Updated member

        Raises:
            TenantError: If member not found or access denied
            NetworkError: If network request fails
        """
        try:
            response = await self._client.patch(
                f"/api/v1/tenants/{tenant_id}/members/{user_id}",
                json={"role": role.value}
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            member_data = data.get("data", data)
            return self._parse_member(member_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def remove_member(self, tenant_id: str, user_id: str) -> bool:
        """
        Remove member from tenant.

        Args:
            tenant_id: Tenant UUID
            user_id: User UUID to remove

        Returns:
            True if removed successfully

        Raises:
            TenantError: If member not found or access denied
            NetworkError: If network request fails
        """
        try:
            response = await self._client.delete(
                f"/api/v1/tenants/{tenant_id}/members/{user_id}"
            )

            if response.status_code not in (200, 204):
                self._handle_error(response)

            return True
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    # -------------------------------------------------------------------------
    # Invitation Management
    # -------------------------------------------------------------------------

    async def list_invitations(self, tenant_id: str) -> List[Invitation]:
        """
        List pending invitations for tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            List of invitations

        Raises:
            TenantError: If tenant not found or access denied
            NetworkError: If network request fails
        """
        try:
            response = await self._client.get(
                f"/api/v1/tenants/{tenant_id}/invitations"
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            invitations_data = data.get("data", [])
            return [self._parse_invitation(i) for i in invitations_data]
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def accept_invitation(
        self,
        tenant_id: str,
        invitation_id: str,
    ) -> Member:
        """
        Accept an invitation to join tenant.

        Args:
            tenant_id: Tenant UUID
            invitation_id: Invitation UUID

        Returns:
            New member record

        Raises:
            TenantError: If invitation not found or expired
            NetworkError: If network request fails
        """
        try:
            response = await self._client.post(
                f"/api/v1/tenants/{tenant_id}/invitations/{invitation_id}/accept"
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            member_data = data.get("data", data)
            return self._parse_member(member_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def decline_invitation(
        self,
        tenant_id: str,
        invitation_id: str,
    ) -> bool:
        """
        Decline an invitation.

        Args:
            tenant_id: Tenant UUID
            invitation_id: Invitation UUID

        Returns:
            True if declined successfully

        Raises:
            TenantError: If invitation not found
            NetworkError: If network request fails
        """
        try:
            response = await self._client.post(
                f"/api/v1/tenants/{tenant_id}/invitations/{invitation_id}/decline"
            )

            if response.status_code not in (200, 204):
                self._handle_error(response)

            return True
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def revoke_invitation(
        self,
        tenant_id: str,
        invitation_id: str,
    ) -> bool:
        """
        Revoke (cancel) a pending invitation.

        Args:
            tenant_id: Tenant UUID
            invitation_id: Invitation UUID

        Returns:
            True if revoked successfully

        Raises:
            TenantError: If invitation not found or access denied
            NetworkError: If network request fails
        """
        try:
            response = await self._client.delete(
                f"/api/v1/tenants/{tenant_id}/invitations/{invitation_id}"
            )

            if response.status_code not in (200, 204):
                self._handle_error(response)

            return True
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")
