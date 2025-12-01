"""Get Public Menu Use Case"""

from typing import Dict, Any, Tuple, List, Optional
import asyncio

from ..repositories import MenuRepository, MenuItemRepository, MenuViewRepository, MenuItemMediaRepository
from ..repositories.models import MenuModel, MenuItemModel
from shared.config import settings
import logging

logger = logging.getLogger(__name__)


class GetPublicMenuUseCase:
    """Use case for retrieving menu for public viewer (no authentication)"""

    def __init__(
        self,
        menu_repo: MenuRepository,
        menu_item_repo: MenuItemRepository,
        menu_view_repo: MenuViewRepository,
        menu_item_media_repo: MenuItemMediaRepository
    ):
        self.menu_repo = menu_repo
        self.menu_item_repo = menu_item_repo
        self.menu_view_repo = menu_view_repo
        self.menu_item_media_repo = menu_item_media_repo

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

            # Build items with media
            items_with_media = []
            for item in items:
                # Get multiple media for this item
                media_list = self._get_item_media(item.id)

                # Determine optimized image_url
                # Priority: 1) Primary from media_list, 2) menu_media relation, 3) legacy image_url
                optimized_image_url = None

                # Try to get from media_list (primary image)
                if media_list:
                    primary_media = next((m for m in media_list if m.get("is_primary")), None)
                    if primary_media:
                        optimized_image_url = primary_media.get("url")
                    elif media_list:
                        optimized_image_url = media_list[0].get("url")

                # Try menu_media relation if available
                if not optimized_image_url and hasattr(item, 'menu_media') and item.menu_media:
                    optimized_image_url = self._get_optimized_url(item.menu_media, "hd")

                # Fallback to legacy image_url
                if not optimized_image_url:
                    optimized_image_url = item.image_url

                items_with_media.append({
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "price": float(item.price) if item.price else None,
                    "currency": item.currency,
                    "image_url": optimized_image_url,
                    "video_url": item.video_url,
                    "category": item.category,
                    "subcategory": item.subcategory,
                    "tags": item.tags,
                    "is_featured": item.is_featured,
                    "is_available": item.is_available,
                    "translations": item.translations,
                    "media": media_list,  # Array of media for carousel
                })

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
                    "outlet_extension": menu.outlet_extension,
                    "footer_description": menu.footer_description,
                    "translations": menu.translations,
                },
                "items": items_with_media,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_next": (skip + limit) < total
            }

        except Exception as e:
            logger.error(f"Failed to get public menu: {e}")
            raise

    def _get_media_url(self, file_path: str) -> str:
        """Build full URL for media file"""
        if not file_path:
            return ""
        # Already a full URL
        if file_path.startswith("http://") or file_path.startswith("https://"):
            return file_path
        # Build full URL from relative path
        base_url = settings.PUBLIC_BASE_URL.rstrip("/")
        return f"{base_url}/menu-media-files/{file_path}"

    def _get_optimized_url(self, media, variant: str = "hd") -> str:
        """
        Get optimized image URL from variants.
        Falls back to original file if variants not available.

        Args:
            media: MenuMediaModel instance
            variant: Preferred variant (thumb, small, hd, 4k, original)

        Returns:
            Full URL to the optimized or original image
        """
        base_url = settings.PUBLIC_BASE_URL.rstrip("/")

        # Check if optimized variants are available
        if media.variants and isinstance(media.variants, dict):
            # Try requested variant first, then fallbacks
            for try_variant in [variant, 'hd', 'small', 'original']:
                if try_variant in media.variants:
                    variant_info = media.variants[try_variant]
                    if variant_info and 'url' in variant_info:
                        return f"{base_url}{variant_info['url']}"

        # Fallback to original file
        return self._get_media_url(media.file_path)

    def _get_thumbnail_url(self, media) -> Optional[str]:
        """Get thumbnail URL - use optimized thumb variant if available"""
        base_url = settings.PUBLIC_BASE_URL.rstrip("/")

        # Check if optimized variants are available
        if media.variants and isinstance(media.variants, dict):
            if 'thumb' in media.variants:
                variant_info = media.variants['thumb']
                if variant_info and 'url' in variant_info:
                    return f"{base_url}{variant_info['url']}"

        # Fallback to thumbnail_path
        if media.thumbnail_path:
            return self._get_media_url(media.thumbnail_path)

        return None

    def _get_item_media(self, menu_item_id: int) -> List[Dict[str, Any]]:
        """Get all media for a menu item with optimized URLs"""
        try:
            media_details = self.menu_item_media_repo.get_media_for_item_with_details(menu_item_id)
            return [
                {
                    "id": m["media"].id,
                    "url": self._get_optimized_url(m["media"], "hd"),  # Use HD variant for main display
                    "thumbnail_url": self._get_thumbnail_url(m["media"]),  # Use thumb variant
                    "type": "video" if m["media"].mime_type.startswith("video/") else "image",
                    "title": m["media"].title,
                    "is_primary": m["is_primary"],
                    "display_order": m["display_order"],
                }
                for m in media_details
            ]
        except Exception as e:
            logger.warning(f"Failed to get media for item {menu_item_id}: {e}")
            return []

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
