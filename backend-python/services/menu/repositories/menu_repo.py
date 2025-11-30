"""Menu Repository Implementation"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, func
from datetime import datetime

from .models import MenuModel, MenuItemModel
from shared.cache import cache
import logging

logger = logging.getLogger(__name__)


class MenuRepository:
    """Menu repository with organization isolation"""

    def __init__(self, db: Session):
        self.db = db

    # ========== Menu CRUD ==========

    def create(
        self,
        organization_id: int,
        name: str,
        menu_type: str,
        public_url_code: str,
        created_by_id: int,
        **kwargs
    ) -> MenuModel:
        """Create new menu"""
        menu = MenuModel(
            organization_id=organization_id,
            name=name,
            menu_type=menu_type,
            public_url_code=public_url_code,
            created_by_id=created_by_id,
            **kwargs
        )
        self.db.add(menu)
        self.db.commit()
        self.db.refresh(menu)

        logger.info(f"Created menu {menu.id} for organization {organization_id}")
        return menu

    def find_by_id(
        self,
        menu_id: int,
        organization_id: int,
        include_deleted: bool = False
    ) -> Optional[MenuModel]:
        """Find menu by ID with organization filtering"""
        query = self.db.query(MenuModel).filter(
            MenuModel.id == menu_id,
            MenuModel.organization_id == organization_id
        )

        if not include_deleted:
            query = query.filter(MenuModel.deleted_at.is_(None))

        return query.first()

    def find_all(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 50,
        menu_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_deleted: bool = False
    ) -> Tuple[List[MenuModel], int]:
        """Find all menus for organization with filters"""
        query = self.db.query(MenuModel).filter(
            MenuModel.organization_id == organization_id
        )

        if not include_deleted:
            query = query.filter(MenuModel.deleted_at.is_(None))

        if menu_type:
            query = query.filter(MenuModel.menu_type == menu_type)

        if is_active is not None:
            query = query.filter(MenuModel.is_active == is_active)

        # Count total
        total = query.count()

        # Apply pagination and order
        menus = query.order_by(MenuModel.created_at.desc()).offset(skip).limit(limit).all()

        return menus, total

    def find_by_public_code(self, public_url_code: str) -> Optional[MenuModel]:
        """Find menu by public URL code (no organization filtering, for public access)"""
        return self.db.query(MenuModel).filter(
            MenuModel.public_url_code == public_url_code,
            MenuModel.deleted_at.is_(None),
            MenuModel.is_active == True
        ).first()

    def update(self, menu: MenuModel, updated_by_id: int, **kwargs) -> MenuModel:
        """Update menu"""
        for key, value in kwargs.items():
            if hasattr(menu, key):
                setattr(menu, key, value)

        menu.updated_by_id = updated_by_id
        menu.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(menu)

        logger.info(f"Updated menu {menu.id}")
        return menu

    def soft_delete(self, menu: MenuModel) -> MenuModel:
        """Soft delete menu"""
        menu.deleted_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(menu)

        logger.info(f"Soft deleted menu {menu.id}")
        return menu

    def exists_by_public_code(self, public_url_code: str) -> bool:
        """Check if public URL code exists"""
        return self.db.query(MenuModel).filter(
            MenuModel.public_url_code == public_url_code
        ).count() > 0

    def get_items_count(self, menu_id: int) -> int:
        """Get count of active items in menu"""
        return self.db.query(MenuItemModel).filter(
            MenuItemModel.menu_id == menu_id,
            MenuItemModel.deleted_at.is_(None)
        ).count()


class MenuItemRepository:
    """Menu Item repository with organization isolation"""

    def __init__(self, db: Session):
        self.db = db

    # ========== Menu Item CRUD ==========

    def create(
        self,
        menu_id: int,
        organization_id: int,
        name: str,
        **kwargs
    ) -> MenuItemModel:
        """Create new menu item"""
        item = MenuItemModel(
            menu_id=menu_id,
            organization_id=organization_id,
            name=name,
            **kwargs
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        logger.info(f"Created menu item {item.id} for menu {menu_id}")
        return item

    def bulk_create(
        self,
        items: List[MenuItemModel]
    ) -> List[MenuItemModel]:
        """Bulk create menu items"""
        self.db.bulk_save_objects(items, return_defaults=True)
        self.db.commit()

        logger.info(f"Bulk created {len(items)} menu items")
        return items

    def find_by_id(
        self,
        item_id: int,
        menu_id: int,
        organization_id: int,
        include_deleted: bool = False
    ) -> Optional[MenuItemModel]:
        """Find menu item by ID with organization filtering"""
        query = self.db.query(MenuItemModel).filter(
            MenuItemModel.id == item_id,
            MenuItemModel.menu_id == menu_id,
            MenuItemModel.organization_id == organization_id
        )

        if not include_deleted:
            query = query.filter(MenuItemModel.deleted_at.is_(None))

        return query.first()

    def find_by_menu(
        self,
        menu_id: int,
        skip: int = 0,
        limit: int = 50,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_featured: Optional[bool] = None,
        include_deleted: bool = False
    ) -> Tuple[List[MenuItemModel], int]:
        """Find all items for menu with filters"""
        query = self.db.query(MenuItemModel).filter(
            MenuItemModel.menu_id == menu_id
        )

        if not include_deleted:
            query = query.filter(MenuItemModel.deleted_at.is_(None))

        if category:
            query = query.filter(MenuItemModel.category == category)

        if is_active is not None:
            query = query.filter(MenuItemModel.is_active == is_active)

        if is_featured is not None:
            query = query.filter(MenuItemModel.is_featured == is_featured)

        # Count total
        total = query.count()

        # Apply pagination and order by display_order
        items = query.order_by(
            MenuItemModel.display_order.asc(),
            MenuItemModel.created_at.asc()
        ).offset(skip).limit(limit).all()

        return items, total

    def find_all_for_export(
        self,
        menu_id: int,
        organization_id: int
    ) -> List[MenuItemModel]:
        """Find all active items for menu export (no pagination)"""
        return self.db.query(MenuItemModel).filter(
            MenuItemModel.menu_id == menu_id,
            MenuItemModel.organization_id == organization_id,
            MenuItemModel.deleted_at.is_(None),
            MenuItemModel.is_active == True
        ).order_by(
            MenuItemModel.display_order.asc(),
            MenuItemModel.created_at.asc()
        ).all()

    def update(self, item: MenuItemModel, **kwargs) -> MenuItemModel:
        """Update menu item"""
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)

        item.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(item)

        logger.info(f"Updated menu item {item.id}")
        return item

    def soft_delete(self, item: MenuItemModel) -> MenuItemModel:
        """Soft delete menu item"""
        item.deleted_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(item)

        logger.info(f"Soft deleted menu item {item.id}")
        return item

    def reorder_items(self, item_orders: List[dict]) -> int:
        """Bulk update display_order for items"""
        updated_count = 0

        for order_data in item_orders:
            item_id = order_data['id']
            display_order = order_data['display_order']

            self.db.query(MenuItemModel).filter(
                MenuItemModel.id == item_id
            ).update({
                'display_order': display_order,
                'updated_at': datetime.utcnow()
            })

            updated_count += 1

        self.db.commit()
        logger.info(f"Reordered {updated_count} menu items")

        return updated_count

    def delete_all_by_menu(self, menu_id: int, organization_id: int) -> int:
        """Soft delete all items in menu (for bulk replace during import)"""
        deleted_count = self.db.query(MenuItemModel).filter(
            MenuItemModel.menu_id == menu_id,
            MenuItemModel.organization_id == organization_id,
            MenuItemModel.deleted_at.is_(None)
        ).update({
            'deleted_at': datetime.utcnow()
        })

        self.db.commit()
        logger.info(f"Soft deleted {deleted_count} items from menu {menu_id}")

        return deleted_count

    def get_categories(self, menu_id: int) -> List[str]:
        """Get distinct categories for menu"""
        categories = self.db.query(MenuItemModel.category).filter(
            MenuItemModel.menu_id == menu_id,
            MenuItemModel.deleted_at.is_(None),
            MenuItemModel.category.isnot(None)
        ).distinct().all()

        return [cat[0] for cat in categories if cat[0]]
