"""
Assign Tag to Content Use Case
Business logic for assigning tags to content items
"""

from ..domain.interfaces import ITagRepository


class AssignTagToContentUseCase:
    """Assign a tag to a single content item"""

    def __init__(self, tag_repo: ITagRepository):
        self.tag_repo = tag_repo

    def execute(self, tag_id: int, content_id: int, organization_id: int) -> dict:
        """
        Assign tag to content

        Returns:
            {"success": bool, "message": str}
        """
        try:
            assigned = self.tag_repo.assign_to_content(tag_id, content_id, organization_id)

            if assigned:
                return {
                    "success": True,
                    "message": f"Tag {tag_id} assigned to content {content_id}"
                }
            else:
                return {
                    "success": False,
                    "message": f"Tag {tag_id} already assigned to content {content_id}"
                }

        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise Exception(f"Failed to assign tag: {str(e)}")
