"""
Create Tag Use Case
Business logic for creating a new tag
"""

from ..domain.interfaces import ITagRepository
from ..domain.tag import Tag
from shared.errors import ValidationError, ConflictError


class CreateTagUseCase:
    """Create a new tag within an organization"""

    def __init__(self, tag_repo: ITagRepository):
        self.tag_repo = tag_repo

    def execute(
        self,
        tag_name: str,
        organization_id: int,
        description: str = None,
        color: str = "#3B82F6",
    ) -> Tag:
        """
        Execute create tag use case

        Args:
            tag_name: Name of the tag (unique within organization)
            organization_id: Organization ID
            description: Optional description
            color: Hex color code (default: #3B82F6)

        Returns:
            Created Tag entity

        Raises:
            AppError: If tag_name already exists in organization
        """
        # Business rule: tag_name must be unique within organization
        existing_tag = self.tag_repo.find_by_name(tag_name, organization_id)
        if existing_tag:
            raise ConflictError(
                f"Tag with name '{tag_name}' already exists"
            )

        # Create new tag entity (validation happens in constructor)
        tag = Tag(
            id=None,  # Will be assigned by database
            tag_name=tag_name,
            description=description,
            color=color,
            organization_id=organization_id,
        )

        # Persist to database
        created_tag = self.tag_repo.create(tag)

        return created_tag
