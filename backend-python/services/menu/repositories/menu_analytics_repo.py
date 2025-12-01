"""Menu Analytics and Import History Repositories"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta

from .models import MenuImportHistoryModel, MenuViewModel, MenuCategoryModel
import logging

logger = logging.getLogger(__name__)


class MenuImportHistoryRepository:
    """Repository for menu import history"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        menu_id: int,
        organization_id: int,
        filename: str,
        rows_total: int,
        rows_success: int,
        rows_failed: int,
        imported_by_id: int,
        file_size: Optional[int] = None,
        errors: Optional[List[Dict[str, Any]]] = None
    ) -> MenuImportHistoryModel:
        """Create import history record"""
        history = MenuImportHistoryModel(
            menu_id=menu_id,
            organization_id=organization_id,
            filename=filename,
            file_size=file_size,
            rows_total=rows_total,
            rows_success=rows_success,
            rows_failed=rows_failed,
            errors=errors,
            imported_by_id=imported_by_id
        )

        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)

        logger.info(f"Created import history {history.id} for menu {menu_id}")
        return history

    def find_by_menu(
        self,
        menu_id: int,
        organization_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[MenuImportHistoryModel], int]:
        """Find import history for menu"""
        query = self.db.query(MenuImportHistoryModel).filter(
            MenuImportHistoryModel.menu_id == menu_id,
            MenuImportHistoryModel.organization_id == organization_id
        )

        total = query.count()

        history = query.order_by(
            MenuImportHistoryModel.imported_at.desc()
        ).offset(skip).limit(limit).all()

        return history, total

    def get_latest(self, menu_id: int) -> Optional[MenuImportHistoryModel]:
        """Get latest import for menu"""
        return self.db.query(MenuImportHistoryModel).filter(
            MenuImportHistoryModel.menu_id == menu_id
        ).order_by(
            MenuImportHistoryModel.imported_at.desc()
        ).first()


class MenuViewRepository:
    """Repository for menu view analytics"""

    def __init__(self, db: Session):
        self.db = db

    def track_view(
        self,
        menu_id: int,
        organization_id: int,
        viewer_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_type: Optional[str] = None,
        contact_clicked: bool = False,
        contact_type: Optional[str] = None
    ) -> MenuViewModel:
        """Track menu view"""
        view = MenuViewModel(
            menu_id=menu_id,
            organization_id=organization_id,
            viewer_ip=viewer_ip,
            user_agent=user_agent,
            device_type=device_type,
            contact_clicked=contact_clicked,
            contact_type=contact_type
        )

        self.db.add(view)
        self.db.commit()
        self.db.refresh(view)

        logger.debug(f"Tracked view for menu {menu_id}")
        return view

    def get_total_views(self, menu_id: int) -> int:
        """Get total views for menu"""
        return self.db.query(MenuViewModel).filter(
            MenuViewModel.menu_id == menu_id
        ).count()

    def get_total_contact_clicks(self, menu_id: int) -> int:
        """Get total contact clicks for menu"""
        return self.db.query(MenuViewModel).filter(
            MenuViewModel.menu_id == menu_id,
            MenuViewModel.contact_clicked == True
        ).count()

    def get_views_by_device_type(self, menu_id: int) -> Dict[str, int]:
        """Get view count grouped by device type"""
        results = self.db.query(
            MenuViewModel.device_type,
            func.count(MenuViewModel.id).label('count')
        ).filter(
            MenuViewModel.menu_id == menu_id,
            MenuViewModel.device_type.isnot(None)
        ).group_by(
            MenuViewModel.device_type
        ).all()

        return {device_type: count for device_type, count in results}

    def get_views_by_date(
        self,
        menu_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get daily view counts for last N days"""
        start_date = datetime.utcnow() - timedelta(days=days)

        results = self.db.query(
            func.date(MenuViewModel.viewed_at).label('date'),
            func.count(MenuViewModel.id).label('views')
        ).filter(
            MenuViewModel.menu_id == menu_id,
            MenuViewModel.viewed_at >= start_date
        ).group_by(
            func.date(MenuViewModel.viewed_at)
        ).order_by(
            func.date(MenuViewModel.viewed_at).asc()
        ).all()

        return [
            {'date': str(date), 'views': views}
            for date, views in results
        ]

    def get_popular_hours(self, menu_id: int) -> List[Dict[str, Any]]:
        """Get view counts by hour of day"""
        results = self.db.query(
            func.extract('hour', MenuViewModel.viewed_at).label('hour'),
            func.count(MenuViewModel.id).label('views')
        ).filter(
            MenuViewModel.menu_id == menu_id
        ).group_by(
            func.extract('hour', MenuViewModel.viewed_at)
        ).order_by(
            func.extract('hour', MenuViewModel.viewed_at).asc()
        ).all()

        return [
            {'hour': int(hour), 'views': views}
            for hour, views in results
        ]


class MenuCategoryRepository:
    """Repository for menu category presets"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        organization_id: int,
        menu_type: str,
        name: str,
        display_order: int = 0,
        icon: Optional[str] = None,
        translations: Optional[Dict[str, Any]] = None,
        subcategories: Optional[List[str]] = None,
        menu_id: Optional[int] = None
    ) -> MenuCategoryModel:
        """Create category preset"""
        category = MenuCategoryModel(
            organization_id=organization_id,
            menu_type=menu_type,
            name=name,
            display_order=display_order,
            icon=icon,
            translations=translations,
            subcategories=subcategories or [],
            menu_id=menu_id
        )

        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)

        logger.info(f"Created category preset {category.id} for menu {menu_id} ({menu_type})")
        return category

    def find_by_menu_type(
        self,
        organization_id: int,
        menu_type: str
    ) -> List[MenuCategoryModel]:
        """Find all categories for menu type (legacy - global categories)"""
        return self.db.query(MenuCategoryModel).filter(
            MenuCategoryModel.organization_id == organization_id,
            MenuCategoryModel.menu_type == menu_type,
            MenuCategoryModel.menu_id.is_(None)  # Only global categories
        ).order_by(
            MenuCategoryModel.display_order.asc(),
            MenuCategoryModel.name.asc()
        ).all()

    def find_by_menu(
        self,
        menu_id: int,
        organization_id: int
    ) -> List[MenuCategoryModel]:
        """Find all categories for a specific menu"""
        return self.db.query(MenuCategoryModel).filter(
            MenuCategoryModel.organization_id == organization_id,
            MenuCategoryModel.menu_id == menu_id
        ).order_by(
            MenuCategoryModel.display_order.asc(),
            MenuCategoryModel.name.asc()
        ).all()

    def find_by_id(
        self,
        category_id: int,
        organization_id: int
    ) -> Optional[MenuCategoryModel]:
        """Find category by ID"""
        return self.db.query(MenuCategoryModel).filter(
            MenuCategoryModel.id == category_id,
            MenuCategoryModel.organization_id == organization_id
        ).first()

    def find_by_name(
        self,
        menu_id: int,
        name: str
    ) -> Optional[MenuCategoryModel]:
        """Find category by name within a menu"""
        return self.db.query(MenuCategoryModel).filter(
            MenuCategoryModel.menu_id == menu_id,
            MenuCategoryModel.name == name
        ).first()

    def update(
        self,
        category: MenuCategoryModel,
        name: Optional[str] = None,
        display_order: Optional[int] = None,
        icon: Optional[str] = None,
        translations: Optional[Dict[str, Any]] = None,
        subcategories: Optional[List[str]] = None
    ) -> MenuCategoryModel:
        """Update category"""
        if name is not None:
            category.name = name
        if display_order is not None:
            category.display_order = display_order
        if icon is not None:
            category.icon = icon
        if translations is not None:
            category.translations = translations
        if subcategories is not None:
            category.subcategories = subcategories

        self.db.commit()
        self.db.refresh(category)
        logger.info(f"Updated category preset {category.id}")
        return category

    def delete(self, category: MenuCategoryModel) -> None:
        """Delete category preset"""
        self.db.delete(category)
        self.db.commit()
        logger.info(f"Deleted category preset {category.id}")

    def reorder(
        self,
        menu_id: int,
        category_orders: List[Dict[str, int]]
    ) -> bool:
        """Reorder categories for a menu

        Args:
            menu_id: The menu ID
            category_orders: List of {"id": int, "display_order": int}
        """
        for order in category_orders:
            category = self.db.query(MenuCategoryModel).filter(
                MenuCategoryModel.id == order["id"],
                MenuCategoryModel.menu_id == menu_id
            ).first()
            if category:
                category.display_order = order["display_order"]

        self.db.commit()
        logger.info(f"Reordered categories for menu {menu_id}")
        return True
