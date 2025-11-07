"""
Tag Repository Interface - CONTRACT
Defines what a Tag repository must do
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from .tag import Tag


class ITagRepository(ABC):
    """
    Tag Repository Interface

    Contract that any Tag repository implementation must follow
    Enables dependency inversion - use cases depend on this interface,
    not on concrete implementations
    """

    @abstractmethod
    def create(self, tag: Tag) -> Tag:
        """Create a new tag"""
        pass

    @abstractmethod
    def find_by_id(self, tag_id: int, organization_id: int) -> Optional[Tag]:
        """Find tag by ID within organization"""
        pass

    @abstractmethod
    def find_by_name(self, tag_name: str, organization_id: int) -> Optional[Tag]:
        """Find tag by name within organization"""
        pass

    @abstractmethod
    def find_all(self, organization_id: int, sort_by: str = "newest") -> List[Tag]:
        """
        Find all tags for organization

        sort_by options:
        - newest: created_at DESC
        - oldest: created_at ASC
        - name_asc: tag_name ASC
        - name_desc: tag_name DESC
        """
        pass

    @abstractmethod
    def update(self, tag: Tag) -> Tag:
        """Update existing tag"""
        pass

    @abstractmethod
    def delete(self, tag_id: int, organization_id: int) -> bool:
        """Delete tag by ID"""
        pass

    @abstractmethod
    def get_tag_usage_count(self, tag_id: int, organization_id: int) -> dict:
        """
        Get usage statistics for a tag
        Returns: {
            "device_count": int,
            "content_count": int,
        }
        """
        pass

    @abstractmethod
    def assign_to_content(self, tag_id: int, content_id: int, organization_id: int) -> bool:
        """Assign tag to a content item"""
        pass

    @abstractmethod
    def unassign_from_content(self, tag_id: int, content_id: int, organization_id: int) -> bool:
        """Unassign tag from a content item"""
        pass

    @abstractmethod
    def assign_to_contents(self, tag_id: int, content_ids: List[int], organization_id: int) -> dict:
        """
        Bulk assign tag to multiple content items
        Returns: {
            "assigned": int (count of successful assignments),
            "skipped": int (count of items already tagged),
            "failed": int (count of failed assignments)
        }
        """
        pass

    @abstractmethod
    def unassign_from_contents(self, tag_id: int, content_ids: List[int], organization_id: int) -> dict:
        """
        Bulk unassign tag from multiple content items
        Returns: {
            "unassigned": int (count of successful unassignments),
            "not_found": int (count of items not tagged)
        }
        """
        pass

    @abstractmethod
    def get_content_tags(self, content_id: int, organization_id: int) -> List[Tag]:
        """Get all tags assigned to a content item"""
        pass
