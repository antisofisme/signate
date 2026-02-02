"""
PUGUH SDK - Project Module

Project management within tenants.
Handles project CRUD and project member management.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from enum import Enum
import httpx

from .exceptions import (
    PuguhError,
    ProjectError,
    ProjectNotFoundError,
    ValidationError,
    NetworkError,
)


class ProjectVisibility(str, Enum):
    """Project visibility settings."""
    PRIVATE = "private"  # Only project members
    TEAM = "team"        # All tenant members
    PUBLIC = "public"    # Public (for open source)


class ProjectMemberRole(str, Enum):
    """Member role within a project."""
    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


@dataclass
class Project:
    """Project data."""
    project_id: str
    tenant_id: str
    name: str
    slug: str
    description: Optional[str] = None
    visibility: ProjectVisibility = ProjectVisibility.PRIVATE
    created_by_user_id: Optional[str] = None
    archived_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def is_archived(self) -> bool:
        """Check if project is archived."""
        return self.archived_at is not None


@dataclass
class ProjectMember:
    """Project member."""
    user_id: str
    project_id: str
    email: str
    display_name: str
    role: ProjectMemberRole
    added_at: Optional[datetime] = None
    avatar_url: Optional[str] = None


class ProjectClient:
    """
    Project management client.

    Projects provide additional isolation within tenants.
    Each project can have its own members and settings.

    Example:
        ```python
        from puguh_sdk import PuguhClient

        client = PuguhClient(
            base_url="https://api.puguh.io",
            access_token="user_jwt_token"
        )

        # Create project
        project = await client.projects.create(
            tenant_id="tenant_uuid",
            name="Project Alpha",
            description="Main project"
        )

        # Add member
        await client.projects.add_member(
            project_id=project.project_id,
            user_id="user_uuid",
            role=ProjectMemberRole.DEVELOPER
        )
        ```
    """

    def __init__(self, http_client: httpx.AsyncClient):
        """
        Initialize project client.

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
            project_id = details.get("project_id", "unknown")
            raise ProjectNotFoundError(project_id, message)
        elif response.status_code == 422:
            raise ValidationError(message, details)
        else:
            raise PuguhError(message, error_code, details, response.status_code)

    def _parse_project(self, data: dict) -> Project:
        """Parse project from API response."""
        return Project(
            project_id=data["project_id"],
            tenant_id=data["tenant_id"],
            name=data["name"],
            slug=data["slug"],
            description=data.get("description"),
            visibility=ProjectVisibility(data.get("visibility", "private")),
            created_by_user_id=data.get("created_by_user_id"),
            archived_at=datetime.fromisoformat(data["archived_at"].replace("Z", "+00:00"))
                if data.get("archived_at") else None,
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
                if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
                if data.get("updated_at") else None,
        )

    def _parse_member(self, data: dict) -> ProjectMember:
        """Parse project member from API response."""
        return ProjectMember(
            user_id=data["user_id"],
            project_id=data["project_id"],
            email=data["email"],
            display_name=data.get("display_name", ""),
            role=ProjectMemberRole(data.get("role", "viewer")),
            added_at=datetime.fromisoformat(data["added_at"].replace("Z", "+00:00"))
                if data.get("added_at") else None,
            avatar_url=data.get("avatar_url"),
        )

    async def create(
        self,
        tenant_id: str,
        name: str,
        description: Optional[str] = None,
        visibility: ProjectVisibility = ProjectVisibility.PRIVATE,
    ) -> Project:
        """
        Create a new project.

        Args:
            tenant_id: Parent tenant UUID
            name: Project name
            description: Project description
            visibility: Project visibility setting

        Returns:
            Created project

        Raises:
            ValidationError: If input validation fails
            TenantError: If tenant limit exceeded
            NetworkError: If network request fails
        """
        try:
            payload = {
                "tenant_id": tenant_id,
                "name": name,
                "visibility": visibility.value,
            }
            if description:
                payload["description"] = description

            response = await self._client.post(
                "/api/v1/projects",
                json=payload
            )

            if response.status_code not in (200, 201):
                self._handle_error(response)

            data = response.json()
            project_data = data.get("data", data)
            return self._parse_project(project_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def list(
        self,
        tenant_id: str,
        include_archived: bool = False,
    ) -> List[Project]:
        """
        List projects in a tenant.

        Args:
            tenant_id: Tenant UUID
            include_archived: Include archived projects

        Returns:
            List of projects

        Raises:
            NetworkError: If network request fails
        """
        try:
            params = {"tenant_id": tenant_id}
            if include_archived:
                params["include_archived"] = "true"

            response = await self._client.get(
                "/api/v1/projects",
                params=params
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            projects_data = data.get("data", [])
            return [self._parse_project(p) for p in projects_data]
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def get(self, project_id: str) -> Project:
        """
        Get project by ID.

        Args:
            project_id: Project UUID

        Returns:
            Project details

        Raises:
            ProjectNotFoundError: If project not found
            NetworkError: If network request fails
        """
        try:
            response = await self._client.get(f"/api/v1/projects/{project_id}")

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            project_data = data.get("data", data)
            return self._parse_project(project_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def update(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        visibility: Optional[ProjectVisibility] = None,
    ) -> Project:
        """
        Update project.

        Args:
            project_id: Project UUID
            name: New name
            description: New description
            visibility: New visibility setting

        Returns:
            Updated project

        Raises:
            ProjectNotFoundError: If project not found
            ValidationError: If input validation fails
            NetworkError: If network request fails
        """
        try:
            payload = {}
            if name is not None:
                payload["name"] = name
            if description is not None:
                payload["description"] = description
            if visibility is not None:
                payload["visibility"] = visibility.value

            response = await self._client.patch(
                f"/api/v1/projects/{project_id}",
                json=payload
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            project_data = data.get("data", data)
            return self._parse_project(project_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def archive(self, project_id: str) -> Project:
        """
        Archive project (soft delete).

        Args:
            project_id: Project UUID

        Returns:
            Archived project

        Raises:
            ProjectNotFoundError: If project not found
            NetworkError: If network request fails
        """
        try:
            response = await self._client.post(
                f"/api/v1/projects/{project_id}/archive"
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            project_data = data.get("data", data)
            return self._parse_project(project_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def unarchive(self, project_id: str) -> Project:
        """
        Unarchive project.

        Args:
            project_id: Project UUID

        Returns:
            Unarchived project

        Raises:
            ProjectNotFoundError: If project not found
            NetworkError: If network request fails
        """
        try:
            response = await self._client.post(
                f"/api/v1/projects/{project_id}/unarchive"
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            project_data = data.get("data", data)
            return self._parse_project(project_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    # -------------------------------------------------------------------------
    # Member Management
    # -------------------------------------------------------------------------

    async def add_member(
        self,
        project_id: str,
        user_id: str,
        role: ProjectMemberRole = ProjectMemberRole.DEVELOPER,
    ) -> ProjectMember:
        """
        Add member to project.

        Args:
            project_id: Project UUID
            user_id: User UUID to add
            role: Role to assign

        Returns:
            Created project member

        Raises:
            ProjectNotFoundError: If project not found
            ValidationError: If user not in tenant
            NetworkError: If network request fails
        """
        try:
            response = await self._client.post(
                f"/api/v1/projects/{project_id}/members",
                json={
                    "user_id": user_id,
                    "role": role.value,
                }
            )

            if response.status_code not in (200, 201):
                self._handle_error(response)

            data = response.json()
            member_data = data.get("data", data)
            return self._parse_member(member_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def list_members(self, project_id: str) -> List[ProjectMember]:
        """
        List project members.

        Args:
            project_id: Project UUID

        Returns:
            List of project members

        Raises:
            ProjectNotFoundError: If project not found
            NetworkError: If network request fails
        """
        try:
            response = await self._client.get(
                f"/api/v1/projects/{project_id}/members"
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            members_data = data.get("data", [])
            return [self._parse_member(m) for m in members_data]
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def update_member_role(
        self,
        project_id: str,
        user_id: str,
        role: ProjectMemberRole,
    ) -> ProjectMember:
        """
        Update project member's role.

        Args:
            project_id: Project UUID
            user_id: User UUID
            role: New role

        Returns:
            Updated member

        Raises:
            ProjectNotFoundError: If project not found
            NetworkError: If network request fails
        """
        try:
            response = await self._client.patch(
                f"/api/v1/projects/{project_id}/members/{user_id}",
                json={"role": role.value}
            )

            if response.status_code != 200:
                self._handle_error(response)

            data = response.json()
            member_data = data.get("data", data)
            return self._parse_member(member_data)
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")

    async def remove_member(self, project_id: str, user_id: str) -> bool:
        """
        Remove member from project.

        Args:
            project_id: Project UUID
            user_id: User UUID to remove

        Returns:
            True if removed successfully

        Raises:
            ProjectNotFoundError: If project not found
            NetworkError: If network request fails
        """
        try:
            response = await self._client.delete(
                f"/api/v1/projects/{project_id}/members/{user_id}"
            )

            if response.status_code not in (200, 204):
                self._handle_error(response)

            return True
        except httpx.RequestError as e:
            raise NetworkError(f"Network request failed: {str(e)}")
