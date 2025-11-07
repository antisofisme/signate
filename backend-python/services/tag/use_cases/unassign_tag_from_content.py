"""
Unassign Tag from Content Use Case
Business logic for unassigning tags from content items
"""

from ..domain.interfaces import ITagRepository


class UnassignTagFromContentUseCase:
    """Unassign a tag from a single content item"""

    def __init__(self, tag_repo: ITagRepository):
        self.tag_repo = tag_repo

    def execute(self, tag_id: int, content_id: int, organization_id: int) -> dict:
        """
        Unassign tag from content

        Returns:
            {"success": bool, "message": str}
        """
        try:
            unassigned = self.tag_repo.unassign_from_content(tag_id, content_id, organization_id)

            if unassigned:
                return {
                    "success": True,
                    "message": f"Tag {tag_id} unassigned from content {content_id}"
                }
            else:
                return {
                    "success": False,
                    "message": f"Tag {tag_id} was not assigned to content {content_id}"
                }

        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise Exception(f"Failed to unassign tag: {str(e)}")
