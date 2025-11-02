"""
Base Repository Pattern - Centralized Database Access Layer
============================================================

PRINSIP CENTRALIZATION:
- Semua query database WAJIB melalui repository
- API endpoints TIDAK BOLEH query langsung
- Service layer call repository untuk data access
- Repository = PINTU KELUAR ke database

Pattern: API → Service → Repository → Database
"""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, func

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Base Repository dengan CRUD operations standard

    Setiap entity (Device, Content, dll) extend class ini
    untuk mendapatkan fungsi dasar CRUD
    """

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    # =========================================================================
    # CREATE - Insert data baru
    # =========================================================================

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """
        Insert single record

        Example:
            device_repo.create({
                "name": "TV-001",
                "organization_id": 1
            })
        """
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def create_many(self, objs_in: List[Dict[str, Any]]) -> List[ModelType]:
        """Insert multiple records (bulk insert)"""
        db_objs = [self.model(**obj) for obj in objs_in]
        self.db.add_all(db_objs)
        self.db.commit()
        return db_objs

    # =========================================================================
    # READ - Query data
    # =========================================================================

    def get(self, id: int) -> Optional[ModelType]:
        """Get by primary key"""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """
        Get by any field

        Example:
            device_repo.get_by_field("device_id", "abc123")
        """
        return self.db.query(self.model).filter(
            getattr(self.model, field) == value
        ).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and filters

        Example:
            devices = device_repo.get_all(
                skip=0,
                limit=10,
                filters={"organization_id": 1, "status": "active"},
                order_by="created_at"
            )
        """
        query = self.db.query(self.model)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by).desc())

        # Apply pagination
        return query.offset(skip).limit(limit).all()

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters"""
        query = self.db.query(func.count(self.model.id))

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        return query.scalar()

    def exists(self, id: int) -> bool:
        """Check if record exists"""
        return self.db.query(
            self.db.query(self.model).filter(self.model.id == id).exists()
        ).scalar()

    # =========================================================================
    # UPDATE - Modify data
    # =========================================================================

    def update(self, id: int, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        """
        Update single record by ID

        Example:
            device_repo.update(1, {"name": "TV-001-Updated"})
        """
        db_obj = self.get(id)
        if not db_obj:
            return None

        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_many(self, filters: Dict[str, Any], updates: Dict[str, Any]) -> int:
        """
        Bulk update records

        Example:
            device_repo.update_many(
                filters={"status": "inactive"},
                updates={"status": "archived"}
            )

        Returns: Number of rows updated
        """
        stmt = update(self.model)

        for field, value in filters.items():
            if hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)

        stmt = stmt.values(**updates)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    # =========================================================================
    # DELETE - Remove data
    # =========================================================================

    def delete(self, id: int) -> bool:
        """
        Delete single record by ID

        Returns: True if deleted, False if not found
        """
        db_obj = self.get(id)
        if not db_obj:
            return False

        self.db.delete(db_obj)
        self.db.commit()
        return True

    def delete_many(self, filters: Dict[str, Any]) -> int:
        """
        Bulk delete records

        Example:
            device_repo.delete_many({"status": "archived"})

        Returns: Number of rows deleted
        """
        stmt = delete(self.model)

        for field, value in filters.items():
            if hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)

        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    # =========================================================================
    # ADVANCED QUERIES - Override di child repository sesuai kebutuhan
    # =========================================================================

    def search(self, search_term: str, fields: List[str]) -> List[ModelType]:
        """
        Search across multiple text fields

        Example:
            devices = device_repo.search("TV", ["name", "description"])
        """
        query = self.db.query(self.model)

        conditions = []
        for field in fields:
            if hasattr(self.model, field):
                conditions.append(
                    getattr(self.model, field).ilike(f"%{search_term}%")
                )

        if conditions:
            from sqlalchemy import or_
            query = query.filter(or_(*conditions))

        return query.all()
