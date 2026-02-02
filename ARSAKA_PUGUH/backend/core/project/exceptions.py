"""
Project Module Exceptions
"""

from typing import Optional


class ProjectError(Exception):
    """Base exception for project module"""

    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code or "PROJECT_ERROR"
        super().__init__(self.message)


class ProjectNotFoundError(ProjectError):
    """Project does not exist"""

    def __init__(self, project_id: str):
        super().__init__(f"Project '{project_id}' not found", "PROJECT_NOT_FOUND")
        self.project_id = project_id


class ProjectSlugExistsError(ProjectError):
    """Project slug already exists in tenant"""

    def __init__(self, slug: str, tenant_id: str):
        super().__init__(
            f"Project with slug '{slug}' already exists in this tenant",
            "PROJECT_SLUG_EXISTS",
        )
        self.slug = slug
        self.tenant_id = tenant_id


class ProjectLimitExceededError(ProjectError):
    """Tenant has reached project limit for plan"""

    def __init__(self, current_count: int, limit: int):
        super().__init__(
            f"Project limit reached ({current_count}/{limit}). Upgrade your plan to create more projects.",
            "PROJECT_LIMIT_EXCEEDED",
        )
        self.current_count = current_count
        self.limit = limit


class ProjectAccessDeniedError(ProjectError):
    """User does not have access to project"""

    def __init__(self, project_id: str):
        super().__init__(
            f"Access denied to project '{project_id}'",
            "PROJECT_ACCESS_DENIED",
        )
        self.project_id = project_id


class CannotDeleteActiveProjectError(ProjectError):
    """Cannot delete project with active resources"""

    def __init__(self, project_id: str, reason: str):
        super().__init__(
            f"Cannot delete project: {reason}",
            "CANNOT_DELETE_PROJECT",
        )
        self.project_id = project_id
        self.reason = reason
