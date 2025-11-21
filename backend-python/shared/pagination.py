"""
Standardized Pagination for FastAPI

Provides consistent pagination across all endpoints with:
- Consistent parameter naming (skip, limit)
- Standardized defaults and limits
- Pagination metadata in responses
- Type-safe pagination models

Usage:
    from shared.pagination import PaginationParams, paginate_response

    @router.get("/items", response_model=PaginatedResponse[ItemResponse])
    async def get_items(pagination: PaginationParams = Depends()):
        items = await repo.get_items(skip=pagination.skip, limit=pagination.limit)
        total = await repo.count_items()
        return paginate_response(items, total, pagination)
"""

from typing import Generic, List, TypeVar, Optional
from pydantic import BaseModel, Field
from fastapi import Query

# Type variable for generic response
T = TypeVar('T')


class PaginationParams(BaseModel):
    """
    Standardized pagination parameters

    Use as dependency in FastAPI routes:
        pagination: PaginationParams = Depends()
    """
    skip: int = Field(
        default=0,
        ge=0,
        description="Number of records to skip (offset)"
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of records to return (max: 1000)"
    )

    @classmethod
    def as_query(
        cls,
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(50, ge=1, le=1000, description="Max records to return")
    ) -> 'PaginationParams':
        """
        Use as FastAPI dependency directly in route

        Usage:
            @router.get("/items")
            async def get_items(pagination: PaginationParams = Depends(PaginationParams.as_query)):
                ...
        """
        return cls(skip=skip, limit=limit)


class PaginationMeta(BaseModel):
    """Pagination metadata for responses"""
    skip: int = Field(..., description="Records skipped")
    limit: int = Field(..., description="Max records requested")
    total: int = Field(..., description="Total records available")
    count: int = Field(..., description="Records returned in this response")
    has_next: bool = Field(..., description="Whether more records are available")
    has_prev: bool = Field(..., description="Whether previous page exists")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standardized paginated response wrapper

    Generic type allows type-safe responses:
        PaginatedResponse[DeviceResponse]
        PaginatedResponse[ContentResponse]
    """
    items: List[T] = Field(..., description="Data items for current page")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")

    class Config:
        # Allow arbitrary types for generic
        arbitrary_types_allowed = True


def paginate_response(
    items: List[T],
    total: int,
    pagination: PaginationParams
) -> PaginatedResponse[T]:
    """
    Create standardized paginated response

    Args:
        items: List of items for current page
        total: Total count of all items (before pagination)
        pagination: Pagination parameters used

    Returns:
        PaginatedResponse with items and metadata

    Example:
        items = await repo.get_devices(skip=0, limit=50)
        total = await repo.count_devices()
        return paginate_response(items, total, pagination)
    """
    count = len(items)
    has_next = (pagination.skip + count) < total
    has_prev = pagination.skip > 0

    meta = PaginationMeta(
        skip=pagination.skip,
        limit=pagination.limit,
        total=total,
        count=count,
        has_next=has_next,
        has_prev=has_prev
    )

    return PaginatedResponse(items=items, pagination=meta)


def calculate_page_info(skip: int, limit: int, total: int) -> dict:
    """
    Calculate pagination information

    Args:
        skip: Records skipped
        limit: Records per page
        total: Total records

    Returns:
        Dictionary with page information:
            - current_page: Current page number (1-indexed)
            - total_pages: Total number of pages
            - has_next: Whether next page exists
            - has_prev: Whether previous page exists
    """
    current_page = (skip // limit) + 1 if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 1

    return {
        'current_page': current_page,
        'total_pages': total_pages,
        'has_next': (skip + limit) < total,
        'has_prev': skip > 0
    }


# Preset pagination configs for different use cases
class PaginationPresets:
    """Common pagination configurations"""

    @staticmethod
    def small() -> PaginationParams:
        """Small page size for UI lists (10 items)"""
        return PaginationParams(skip=0, limit=10)

    @staticmethod
    def medium() -> PaginationParams:
        """Medium page size for tables (50 items) - DEFAULT"""
        return PaginationParams(skip=0, limit=50)

    @staticmethod
    def large() -> PaginationParams:
        """Large page size for exports (100 items)"""
        return PaginationParams(skip=0, limit=100)

    @staticmethod
    def xlarge() -> PaginationParams:
        """Extra large for batch operations (500 items)"""
        return PaginationParams(skip=0, limit=500)

    @staticmethod
    def max() -> PaginationParams:
        """Maximum allowed (1000 items)"""
        return PaginationParams(skip=0, limit=1000)


# Backward compatibility helpers (for gradual migration)
def get_pagination_params(skip: int = 0, limit: int = 50) -> PaginationParams:
    """
    Helper to create pagination params from raw values

    Use during migration from old pagination style
    """
    return PaginationParams(skip=skip, limit=limit)


# Export all
__all__ = [
    'PaginationParams',
    'PaginationMeta',
    'PaginatedResponse',
    'paginate_response',
    'calculate_page_info',
    'PaginationPresets',
    'get_pagination_params',
]
