"""
Update Tag Use Case
Business logic for updating an existing tag
"""

from typing import Optional
from ..domain.interfaces import ITagRepository
from ..domain.tag import Tag
from shared.errors import ValidationError, ConflictError, NotFoundError


class UpdateTagUseCase:
    """Update an existing tag within an organization"""

    def __init__(self, tag_repo: ITagRepository):
        self.tag_repo = tag_repo

    def execute(
        self,
        tag_id: int,
        organization_id: int,
        tag_name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Tag:
        """
        Execute update tag use case

        Args:
            tag_id: Tag ID to update
            organization_id: Organization ID
            tag_name: New tag name (optional)
            description: New description (optional)
            color: New color (optional)

        Returns:
            Updated Tag entity

        Raises:
            AppError: If tag not found or name already exists
        """
        # Find existing tag
        existing_tag = self.tag_repo.find_by_id(tag_id, organization_id)
        if not existing_tag:
            raise NotFoundError(
                f"Tag with ID {tag_id} not found"
            )

        # If tag_name is being updated, check uniqueness
        if tag_name and tag_name != existing_tag.tag_name:
            duplicate = self.tag_repo.find_by_name(tag_name, organization_id)
            if duplicate:
                raise ConflictError(
                    f"Tag with name '{tag_name}' already exists"
                )

        # Update fields (only if provided)
        if tag_name is not None:
            existing_tag.tag_name = tag_name
        if description is not None:
            existing_tag.description = description
        if color is not None:
            existing_tag.color = color

        # Validate updated tag (business rules in Tag entity)
        existing_tag._validate()

        # Persist changes
        updated_tag = self.tag_repo.update(existing_tag)

        return updated_tag
