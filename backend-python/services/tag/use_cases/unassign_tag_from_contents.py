"""
Bulk Unassign Tag from Contents Use Case
Business logic for bulk unassigning tags from multiple content items
"""

from typing import List
from ..domain.interfaces import ITagRepository


class UnassignTagFromContentsUseCase:
    """Bulk unassign a tag from multiple content items"""

    def __init__(self, tag_repo: ITagRepository):
        self.tag_repo = tag_repo

    def execute(self, tag_id: int, content_ids: List[int], organization_id: int) -> dict:
        """
        Bulk unassign tag from multiple contents

        Returns:
            {
                "unassigned": int,
                "not_found": int,
                "message": str
            }
        """
        if not content_ids:
            raise ValueError("content_ids cannot be empty")

        try:
            result = self.tag_repo.unassign_from_contents(tag_id, content_ids, organization_id)

            message = f"Unassigned tag from {result['unassigned']} content(s)"
            if result['not_found'] > 0:
                message += f", {result['not_found']} were not tagged"

            return {
                **result,
                "message": message
            }

        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise Exception(f"Failed to bulk unassign tag: {str(e)}")
