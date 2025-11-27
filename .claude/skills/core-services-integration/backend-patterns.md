# Backend Integration Patterns

Complete templates and patterns for integrating core services in backend features.

## Directory Structure Template

```
backend-python/services/[feature]/
├── __init__.py
├── models.py           # SQLAlchemy models
├── dtos.py             # Pydantic DTOs (request/response)
├── routes.py           # FastAPI routes
├── repositories/
│   ├── __init__.py
│   └── [feature]_repo.py
└── use_cases/
    ├── __init__.py
    ├── create_[item].py
    ├── update_[item].py
    ├── delete_[item].py
    └── get_[items].py
```

## Model Template (models.py)

```python
"""
[Feature] Database Models
"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, JSON, Index
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from shared.database import Base


class [Feature]Model(Base):
    """[Feature] database model"""
    __tablename__ = "[features]"  # plural, snake_case

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Organization (multi-tenancy) - REQUIRED
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Core fields
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Status (use is_ prefix for booleans)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps (use _at suffix)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Audit trail - REQUIRED for all user-modifiable tables
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    organization = relationship("OrganizationModel", foreign_keys=[organization_id])
    created_by = relationship("UserModel", foreign_keys=[created_by_id])
    updated_by = relationship("UserModel", foreign_keys=[updated_by_id])

    # Table constraints
    __table_args__ = (
        Index('idx_[features]_org_name', 'organization_id', 'name'),
    )
```

## DTO Template (dtos.py)

```python
"""
[Feature] DTOs (Data Transfer Objects)
Request and Response models for API endpoints
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


# =============================================================================
# REQUEST DTOs
# =============================================================================

class Create[Feature]Request(BaseModel):
    """Request to create a new [feature]"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    is_active: bool = Field(default=True)

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Example Item",
                "description": "This is an example",
                "is_active": True
            }
        }


class Update[Feature]Request(BaseModel):
    """Request to update an existing [feature]"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    is_active: Optional[bool] = None

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v


class [Feature]QueryParams(BaseModel):
    """Query parameters for listing [features]"""
    page: int = Field(default=1, ge=1, le=1000)
    limit: int = Field(default=20, ge=1, le=100)
    search: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc")

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ('asc', 'desc'):
            raise ValueError('sort_order must be asc or desc')
        return v


# =============================================================================
# RESPONSE DTOs
# =============================================================================

class [Feature]Response(BaseModel):
    """Single [feature] response"""
    id: int
    organization_id: int
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by_id: Optional[int]
    updated_by_id: Optional[int]

    class Config:
        from_attributes = True


class [Feature]ListResponse(BaseModel):
    """Paginated list of [features]"""
    items: List[[Feature]Response]
    total: int
    page: int
    limit: int
    pages: int

    class Config:
        from_attributes = True


class [Feature]BulkResponse(BaseModel):
    """Response for bulk operations"""
    success_count: int
    failed_count: int
    errors: List[dict] = []
```

## Repository Template (repositories/[feature]_repo.py)

```python
"""
[Feature] Repository
Data access layer for [features]
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..models import [Feature]Model
from shared.errors import NotFoundError, ConflictError


class [Feature]Repository:
    """Repository for [feature] data access"""

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # READ OPERATIONS
    # =========================================================================

    def get_by_id(self, id: int, org_id: int) -> Optional[[Feature]Model]:
        """Get [feature] by ID, scoped to organization"""
        return self.db.query([Feature]Model).filter(
            and_(
                [Feature]Model.id == id,
                [Feature]Model.organization_id == org_id
            )
        ).first()

    def get_by_id_or_raise(self, id: int, org_id: int) -> [Feature]Model:
        """Get [feature] by ID or raise NotFoundError"""
        item = self.get_by_id(id, org_id)
        if not item:
            raise NotFoundError(f"[Feature] with ID {id} not found")
        return item

    def get_by_name(self, name: str, org_id: int) -> Optional[[Feature]Model]:
        """Get [feature] by name (for duplicate checking)"""
        return self.db.query([Feature]Model).filter(
            and_(
                [Feature]Model.name == name,
                [Feature]Model.organization_id == org_id
            )
        ).first()

    def get_list(
        self,
        org_id: int,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[[Feature]Model], int]:
        """Get paginated list of [features] for organization"""
        query = self.db.query([Feature]Model).filter(
            [Feature]Model.organization_id == org_id
        )

        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    [Feature]Model.name.ilike(search_term),
                    [Feature]Model.description.ilike(search_term)
                )
            )

        if is_active is not None:
            query = query.filter([Feature]Model.is_active == is_active)

        # Get total count
        total = query.count()

        # Apply sorting
        sort_column = getattr([Feature]Model, sort_by, [Feature]Model.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * limit
        items = query.offset(offset).limit(limit).all()

        return items, total

    def bulk_get_by_ids(self, ids: List[int], org_id: int) -> List[[Feature]Model]:
        """Get multiple [features] by IDs"""
        return self.db.query([Feature]Model).filter(
            and_(
                [Feature]Model.id.in_(ids),
                [Feature]Model.organization_id == org_id
            )
        ).all()

    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================

    def create(self, data: dict, org_id: int, user_id: int) -> [Feature]Model:
        """Create new [feature]"""
        # Check for duplicate
        existing = self.get_by_name(data.get("name"), org_id)
        if existing:
            raise ConflictError(f"[Feature] with name '{data['name']}' already exists")

        item = [Feature]Model(
            **data,
            organization_id=org_id,
            created_by_id=user_id
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, id: int, org_id: int, data: dict, user_id: int) -> [Feature]Model:
        """Update existing [feature]"""
        item = self.get_by_id_or_raise(id, org_id)

        # Check for duplicate name if name is being changed
        if "name" in data and data["name"] != item.name:
            existing = self.get_by_name(data["name"], org_id)
            if existing:
                raise ConflictError(f"[Feature] with name '{data['name']}' already exists")

        # Update fields
        for key, value in data.items():
            if value is not None:
                setattr(item, key, value)

        item.updated_by_id = user_id
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, id: int, org_id: int) -> bool:
        """Delete [feature]"""
        item = self.get_by_id_or_raise(id, org_id)
        self.db.delete(item)
        self.db.commit()
        return True

    def bulk_delete(self, ids: List[int], org_id: int) -> int:
        """Delete multiple [features]"""
        result = self.db.query([Feature]Model).filter(
            and_(
                [Feature]Model.id.in_(ids),
                [Feature]Model.organization_id == org_id
            )
        ).delete(synchronize_session=False)
        self.db.commit()
        return result

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def count_by_organization(self, org_id: int) -> int:
        """Count [features] in organization"""
        return self.db.query([Feature]Model).filter(
            [Feature]Model.organization_id == org_id
        ).count()
```

## Routes Template (routes.py)

```python
"""
[Feature] API Routes
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import List

from shared.database import get_db
from shared.auth import get_current_user, require_permission
from shared.errors import not_found_error, validation_error, forbidden_error
from shared.validators import sanitize_input
from shared.cache import cache

from services.audit.use_cases.log_action import LogActionUseCase
from services.audit.repositories.audit_log_repo import AuditLogRepository

from .dtos import (
    Create[Feature]Request,
    Update[Feature]Request,
    [Feature]Response,
    [Feature]ListResponse,
    [Feature]QueryParams
)
from .repositories.[feature]_repo import [Feature]Repository

router = APIRouter(prefix="/[features]", tags=["[Features]"])


# =============================================================================
# LIST / GET ENDPOINTS
# =============================================================================

@router.get("", response_model=[Feature]ListResponse)
async def list_[features](
    page: int = Query(default=1, ge=1, le=1000),
    limit: int = Query(default=20, ge=1, le=100),
    search: str = Query(default=None, max_length=100),
    is_active: bool = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all [features] for current organization"""
    org_id = current_user["organization_id"]
    repo = [Feature]Repository(db)

    items, total = repo.get_list(
        org_id=org_id,
        page=page,
        limit=limit,
        search=search,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return [Feature]ListResponse(
        items=[Feature]Response.model_validate(item) for item in items],
        total=total,
        page=page,
        limit=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/{id}", response_model=[Feature]Response)
async def get_[feature](
    id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single [feature] by ID"""
    org_id = current_user["organization_id"]
    repo = [Feature]Repository(db)

    item = repo.get_by_id(id, org_id)
    if not item:
        raise not_found_error("[Feature]", id)

    return [Feature]Response.model_validate(item)


# =============================================================================
# CREATE / UPDATE / DELETE ENDPOINTS
# =============================================================================

@router.post("", response_model=[Feature]Response, status_code=201)
async def create_[feature](
    data: Create[Feature]Request,
    request: Request,
    current_user: dict = Depends(require_permission("[features].create")),
    db: Session = Depends(get_db)
):
    """Create new [feature]"""
    org_id = current_user["organization_id"]
    user_id = int(current_user["sub"])
    repo = [Feature]Repository(db)

    # Sanitize input
    item_data = {
        "name": sanitize_input(data.name),
        "description": sanitize_input(data.description) if data.description else None,
        "is_active": data.is_active
    }

    # Create item
    item = repo.create(item_data, org_id, user_id)

    # Audit log
    audit_repo = AuditLogRepository(db)
    audit = LogActionUseCase(audit_repo)
    audit.execute(
        user_id=user_id,
        action="CREATE",
        resource_type="[feature]",
        resource_id=item.id,
        details={"name": item.name},
        ip_address=request.client.host if request.client else None
    )

    # Invalidate cache
    cache.clear_pattern(f"org:{org_id}:[features]:*")

    return [Feature]Response.model_validate(item)


@router.put("/{id}", response_model=[Feature]Response)
async def update_[feature](
    id: int,
    data: Update[Feature]Request,
    request: Request,
    current_user: dict = Depends(require_permission("[features].update")),
    db: Session = Depends(get_db)
):
    """Update existing [feature]"""
    org_id = current_user["organization_id"]
    user_id = int(current_user["sub"])
    repo = [Feature]Repository(db)

    # Build update data (only non-None values)
    update_data = {}
    if data.name is not None:
        update_data["name"] = sanitize_input(data.name)
    if data.description is not None:
        update_data["description"] = sanitize_input(data.description)
    if data.is_active is not None:
        update_data["is_active"] = data.is_active

    # Update item
    item = repo.update(id, org_id, update_data, user_id)

    # Audit log
    audit_repo = AuditLogRepository(db)
    audit = LogActionUseCase(audit_repo)
    audit.execute(
        user_id=user_id,
        action="UPDATE",
        resource_type="[feature]",
        resource_id=item.id,
        details={"changes": update_data},
        ip_address=request.client.host if request.client else None
    )

    # Invalidate cache
    cache.delete(f"[feature]:{id}")
    cache.clear_pattern(f"org:{org_id}:[features]:*")

    return [Feature]Response.model_validate(item)


@router.delete("/{id}", status_code=204)
async def delete_[feature](
    id: int,
    request: Request,
    current_user: dict = Depends(require_permission("[features].delete")),
    db: Session = Depends(get_db)
):
    """Delete [feature]"""
    org_id = current_user["organization_id"]
    user_id = int(current_user["sub"])
    repo = [Feature]Repository(db)

    # Get item first for audit
    item = repo.get_by_id(id, org_id)
    if not item:
        raise not_found_error("[Feature]", id)

    # Delete
    repo.delete(id, org_id)

    # Audit log
    audit_repo = AuditLogRepository(db)
    audit = LogActionUseCase(audit_repo)
    audit.execute(
        user_id=user_id,
        action="DELETE",
        resource_type="[feature]",
        resource_id=id,
        details={"name": item.name},
        ip_address=request.client.host if request.client else None
    )

    # Invalidate cache
    cache.delete(f"[feature]:{id}")
    cache.clear_pattern(f"org:{org_id}:[features]:*")


# =============================================================================
# BULK OPERATIONS
# =============================================================================

@router.post("/bulk/delete", status_code=200)
async def bulk_delete_[features](
    ids: List[int],
    request: Request,
    current_user: dict = Depends(require_permission("[features].delete")),
    db: Session = Depends(get_db)
):
    """Bulk delete [features]"""
    if len(ids) > 100:
        raise validation_error("Cannot delete more than 100 items at once")

    org_id = current_user["organization_id"]
    user_id = int(current_user["sub"])
    repo = [Feature]Repository(db)

    # Delete
    deleted_count = repo.bulk_delete(ids, org_id)

    # Audit log
    audit_repo = AuditLogRepository(db)
    audit = LogActionUseCase(audit_repo)
    audit.execute(
        user_id=user_id,
        action="BULK_DELETE",
        resource_type="[feature]",
        resource_id=None,
        details={"ids": ids, "deleted_count": deleted_count},
        ip_address=request.client.host if request.client else None
    )

    # Invalidate cache
    for id in ids:
        cache.delete(f"[feature]:{id}")
    cache.clear_pattern(f"org:{org_id}:[features]:*")

    return {"deleted_count": deleted_count}


# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get("/health", include_in_schema=False)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {"status": "healthy", "service": "[features]"}
    except Exception as e:
        return {"status": "unhealthy", "service": "[features]", "error": str(e)}
```

## Use Case Template (use_cases/create_[item].py)

```python
"""
Create [Feature] Use Case
Business logic for creating a new [feature]
"""
from typing import Optional
from shared.validators import sanitize_input, validate_required
from shared.errors import ValidationError, ConflictError

from ..repositories.[feature]_repo import [Feature]Repository
from ..dtos import Create[Feature]Request, [Feature]Response


class Create[Feature]UseCase:
    """Use case for creating a new [feature]"""

    def __init__(self, repo: [Feature]Repository):
        self.repo = repo

    def execute(
        self,
        data: Create[Feature]Request,
        org_id: int,
        user_id: int
    ) -> [Feature]Response:
        """
        Execute the create [feature] use case

        Args:
            data: Request data
            org_id: Organization ID
            user_id: ID of user creating the [feature]

        Returns:
            Created [feature] response

        Raises:
            ValidationError: If validation fails
            ConflictError: If [feature] with same name exists
        """
        # Validate required fields
        if not data.name or not data.name.strip():
            raise ValidationError("Name is required")

        # Sanitize input
        item_data = {
            "name": sanitize_input(data.name),
            "description": sanitize_input(data.description) if data.description else None,
            "is_active": data.is_active
        }

        # Business validation
        self._validate_business_rules(item_data, org_id)

        # Create
        item = self.repo.create(item_data, org_id, user_id)

        return [Feature]Response.model_validate(item)

    def _validate_business_rules(self, data: dict, org_id: int):
        """Validate business rules"""
        # Check for duplicate name
        existing = self.repo.get_by_name(data["name"], org_id)
        if existing:
            raise ConflictError(f"[Feature] with name '{data['name']}' already exists")

        # Add more business validations as needed
        # Example: Check organization quota
        # count = self.repo.count_by_organization(org_id)
        # if count >= MAX_ITEMS_PER_ORG:
        #     raise ValidationError("Organization has reached maximum [features] limit")
```

## Permission Constants

```python
# Add to backend-python/services/rbac/constants.py

[FEATURES]_PERMISSIONS = {
    "[features].read": "View [features]",
    "[features].create": "Create [features]",
    "[features].update": "Update [features]",
    "[features].delete": "Delete [features]",
    "[features].export": "Export [features]",
}

# Add to DEFAULT_ROLE_PERMISSIONS
DEFAULT_ROLE_PERMISSIONS = {
    "SUPER_ADMIN": [..., *[FEATURES]_PERMISSIONS.keys()],
    "ADMIN": [..., "[features].read", "[features].create", "[features].update", "[features].delete"],
    "MANAGER": [..., "[features].read", "[features].create", "[features].update"],
    "VIEWER": [..., "[features].read"],
}
```

## Register Routes

```python
# In backend-python/main.py, add:

from services.[feature].routes import router as [feature]_router

app.include_router([feature]_router, prefix="/api")
```
