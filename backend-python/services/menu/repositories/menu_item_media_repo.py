"""Menu Item Media Repository - Multiple media per menu item"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import MenuItemMediaModel, MenuMediaModel, MenuItemModel
import logging

logger = logging.getLogger(__name__)


class MenuItemMediaRepository:
    """Repository for menu item media junction table"""

    def __init__(self, db: Session):
        self.db = db

    def add_media_to_item(
        self,
        menu_item_id: int,
        menu_media_id: int,
        display_order: int = 0,
        is_primary: bool = False
    ) -> MenuItemMediaModel:
        """Add media to menu item"""
        # If setting as primary, unset other primaries
        if is_primary:
            self._unset_primary(menu_item_id)

        item_media = MenuItemMediaModel(
            menu_item_id=menu_item_id,
            menu_media_id=menu_media_id,
            display_order=display_order,
            is_primary=is_primary
        )

        self.db.add(item_media)
        self.db.commit()
        self.db.refresh(item_media)

        logger.info(f"Added media {menu_media_id} to item {menu_item_id}")
        return item_media

    def remove_media_from_item(
        self,
        menu_item_id: int,
        menu_media_id: int
    ) -> bool:
        """Remove media from menu item"""
        item_media = self.db.query(MenuItemMediaModel).filter(
            MenuItemMediaModel.menu_item_id == menu_item_id,
            MenuItemMediaModel.menu_media_id == menu_media_id
        ).first()

        if not item_media:
            return False

        self.db.delete(item_media)
        self.db.commit()

        logger.info(f"Removed media {menu_media_id} from item {menu_item_id}")
        return True

    def get_media_for_item(
        self,
        menu_item_id: int
    ) -> List[MenuItemMediaModel]:
        """Get all media for a menu item, ordered by display_order"""
        return self.db.query(MenuItemMediaModel).filter(
            MenuItemMediaModel.menu_item_id == menu_item_id
        ).order_by(
            MenuItemMediaModel.is_primary.desc(),
            MenuItemMediaModel.display_order.asc()
        ).all()

    def get_media_for_item_with_details(
        self,
        menu_item_id: int
    ) -> List[dict]:
        """Get all media for item with full media details"""
        results = self.db.query(
            MenuItemMediaModel,
            MenuMediaModel
        ).join(
            MenuMediaModel,
            MenuItemMediaModel.menu_media_id == MenuMediaModel.id
        ).filter(
            MenuItemMediaModel.menu_item_id == menu_item_id,
            MenuMediaModel.deleted_at.is_(None)
        ).order_by(
            MenuItemMediaModel.is_primary.desc(),
            MenuItemMediaModel.display_order.asc()
        ).all()

        return [
            {
                "id": item_media.id,
                "menu_item_id": item_media.menu_item_id,
                "menu_media_id": item_media.menu_media_id,
                "display_order": item_media.display_order,
                "is_primary": item_media.is_primary,
                "created_at": item_media.created_at,
                "media": media
            }
            for item_media, media in results
        ]

    def set_primary(
        self,
        menu_item_id: int,
        menu_media_id: int
    ) -> bool:
        """Set a media as primary for menu item"""
        # Unset all primaries
        self._unset_primary(menu_item_id)

        # Set the new primary
        item_media = self.db.query(MenuItemMediaModel).filter(
            MenuItemMediaModel.menu_item_id == menu_item_id,
            MenuItemMediaModel.menu_media_id == menu_media_id
        ).first()

        if not item_media:
            return False

        item_media.is_primary = True
        self.db.commit()

        logger.info(f"Set media {menu_media_id} as primary for item {menu_item_id}")
        return True

    def update_display_order(
        self,
        menu_item_id: int,
        media_orders: List[dict]
    ) -> bool:
        """Update display order for multiple media items

        Args:
            menu_item_id: The menu item ID
            media_orders: List of {"menu_media_id": int, "display_order": int}
        """
        for order in media_orders:
            item_media = self.db.query(MenuItemMediaModel).filter(
                MenuItemMediaModel.menu_item_id == menu_item_id,
                MenuItemMediaModel.menu_media_id == order["menu_media_id"]
            ).first()

            if item_media:
                item_media.display_order = order["display_order"]

        self.db.commit()
        logger.info(f"Updated display order for item {menu_item_id}")
        return True

    def _unset_primary(self, menu_item_id: int) -> None:
        """Unset all primary flags for a menu item"""
        self.db.query(MenuItemMediaModel).filter(
            MenuItemMediaModel.menu_item_id == menu_item_id,
            MenuItemMediaModel.is_primary == True
        ).update({"is_primary": False})
        self.db.flush()

    def get_primary_media(
        self,
        menu_item_id: int
    ) -> Optional[MenuMediaModel]:
        """Get the primary media for a menu item"""
        result = self.db.query(MenuMediaModel).join(
            MenuItemMediaModel,
            MenuItemMediaModel.menu_media_id == MenuMediaModel.id
        ).filter(
            MenuItemMediaModel.menu_item_id == menu_item_id,
            MenuItemMediaModel.is_primary == True,
            MenuMediaModel.deleted_at.is_(None)
        ).first()

        return result

    def clear_item_media(self, menu_item_id: int) -> int:
        """Remove all media from a menu item"""
        count = self.db.query(MenuItemMediaModel).filter(
            MenuItemMediaModel.menu_item_id == menu_item_id
        ).delete()
        self.db.commit()
        logger.info(f"Cleared {count} media from item {menu_item_id}")
        return count

    def bulk_set_media(
        self,
        menu_item_id: int,
        media_ids: List[int],
        primary_media_id: Optional[int] = None
    ) -> List[MenuItemMediaModel]:
        """Replace all media for a menu item with new list

        Args:
            menu_item_id: The menu item ID
            media_ids: List of menu_media_id to set
            primary_media_id: Optional ID of primary media
        """
        # Clear existing
        self.clear_item_media(menu_item_id)

        # Add new media
        results = []
        for idx, media_id in enumerate(media_ids):
            is_primary = media_id == primary_media_id if primary_media_id else (idx == 0)
            item_media = MenuItemMediaModel(
                menu_item_id=menu_item_id,
                menu_media_id=media_id,
                display_order=idx,
                is_primary=is_primary
            )
            self.db.add(item_media)
            results.append(item_media)

        self.db.commit()
        for r in results:
            self.db.refresh(r)

        logger.info(f"Bulk set {len(media_ids)} media for item {menu_item_id}")
        return results
