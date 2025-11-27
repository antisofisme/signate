"""
Bulk Assign Tag to Contents Use Case
Business logic for bulk assigning tags to multiple content items
"""

from typing import List, Optional
from ..domain.interfaces import ITagRepository


class AssignTagToContentsUseCase:
    """Bulk assign a tag to multiple content items"""

    def __init__(self, tag_repo: ITagRepository):
        self.tag_repo = tag_repo

    def execute(
        self,
        tag_id: int,
        content_ids: List[int],
        organization_id: int,
        assigned_by_id: Optional[int] = None,
    ) -> dict:
        """
        Bulk assign tag to multiple contents

        Args:
            tag_id: Tag ID to assign
            content_ids: List of content IDs to assign to
            organization_id: Organization ID
            assigned_by_id: User ID who assigned the tags (audit trail)

        Returns:
            {
                "assigned": int,
                "skipped": int,
                "failed": int,
                "message": str
            }
        """
        if not content_ids:
            raise ValueError("content_ids cannot be empty")

        try:
            result = self.tag_repo.assign_to_contents(
                tag_id, content_ids, organization_id, assigned_by_id=assigned_by_id
            )

            message = f"Assigned tag to {result['assigned']} content(s)"
            if result['skipped'] > 0:
                message += f", skipped {result['skipped']} (already tagged)"
            if result['failed'] > 0:
                message += f", failed {result['failed']} (not found or access denied)"

            return {
                **result,
                "message": message
            }

        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise Exception(f"Failed to bulk assign tag: {str(e)}")
