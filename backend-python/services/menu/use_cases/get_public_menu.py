"""Get Public Menu Use Case"""

from typing import Dict, Any, Tuple, List, Optional
import asyncio

from ..repositories import MenuRepository, MenuItemRepository, MenuViewRepository
from ..repositories.models import MenuModel, MenuItemModel
import logging

logger = logging.getLogger(__name__)


class GetPublicMenuUseCase:
    """Use case for retrieving menu for public viewer (no authentication)"""

    def __init__(
        self,
        menu_repo: MenuRepository,
        menu_item_repo: MenuItemRepository,
        menu_view_repo: MenuViewRepository
    ):
        self.menu_repo = menu_repo
        self.menu_item_repo = menu_item_repo
        self.menu_view_repo = menu_view_repo

    async def execute(
        self,
        public_url_code: str,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        viewer_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get menu and items by public URL code

        Args:
            public_url_code: Public URL code (e.g., 'ABC123XYZ456')
            skip: Pagination offset
            limit: Pagination limit (max 100)
            category: Filter by category (optional)
            viewer_ip: Viewer IP address for analytics
            user_agent: User agent string for analytics
            device_type: Device type (mobile, tablet, desktop) for analytics

        Returns:
            Dict with menu data and paginated items

        Raises:
            ValueError: If menu not found or inactive
        """
        try:
            # Find menu by public code
            menu = self.menu_repo.find_by_public_code(public_url_code)

            if not menu:
                raise ValueError(f"Menu not found or inactive")

            logger.info(f"Public access to menu {menu.id} ({public_url_code})")

            # Get menu items (paginated)
            items, total = self.menu_item_repo.find_by_menu(
                menu_id=menu.id,
                skip=skip,
                limit=min(limit, 100),  # Max 100 items per page
                category=category,
                is_active=True,  # Only show active items to public
                include_deleted=False
            )

            # Track view asynchronously (non-blocking)
            asyncio.create_task(
                self._track_view(
                    menu_id=menu.id,
                    organization_id=menu.organization_id,
                    viewer_ip=viewer_ip,
                    user_agent=user_agent,
                    device_type=device_type
                )
            )

            # Build response
            return {
                "menu": {
                    "name": menu.name,
                    "description": menu.description,
                    "menu_type": menu.menu_type,
                    "show_prices": menu.show_prices,
                    "display_mode": menu.display_mode,
                    "theme_color": menu.theme_color,
                    "whatsapp_number": menu.whatsapp_number,
                    "phone_number": menu.phone_number,
                    "contact_label": menu.contact_label,
                    "translations": menu.translations,
                },
                "items": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "description": item.description,
                        "price": float(item.price) if item.price else None,
                        "currency": item.currency,
                        "image_url": item.image_url,
                        "video_url": item.video_url,
                        "category": item.category,
                        "subcategory": item.subcategory,
                        "tags": item.tags,
                        "is_featured": item.is_featured,
                        "is_available": item.is_available,
                        "translations": item.translations,
                    }
                    for item in items
                ],
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_next": (skip + limit) < total
            }

        except Exception as e:
            logger.error(f"Failed to get public menu: {e}")
            raise

    async def _track_view(
        self,
        menu_id: int,
        organization_id: int,
        viewer_ip: Optional[str],
        user_agent: Optional[str],
        device_type: Optional[str]
    ):
        """Track menu view asynchronously"""
        try:
            self.menu_view_repo.track_view(
                menu_id=menu_id,
                organization_id=organization_id,
                viewer_ip=viewer_ip,
                user_agent=user_agent,
                device_type=device_type
            )
        except Exception as e:
            # Don't fail the request if analytics tracking fails
            logger.warning(f"Failed to track menu view: {e}")
