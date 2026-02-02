"""
Project Interfaces Layer

Repository and service contracts.
"""

from .project_repository import IProjectRepository
from .membership_repository import IProjectMembershipRepository

__all__ = [
    "IProjectRepository",
    "IProjectMembershipRepository",
]
