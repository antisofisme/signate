"""Pydantic DTOs for Digital Menu feature"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ==============================================================================
# Menu DTOs
# ==============================================================================

class MenuCreateDTO(BaseModel):
    """DTO for creating a new menu"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    menu_type: str = Field(..., pattern="^(restaurant|laundry|spa|room_service|other)$")

    # Display settings
    is_active: bool = True
    show_prices: bool = True
    display_mode: str = Field(default='grid', pattern="^(grid|list|carousel)$")
    theme_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")

    # Contact buttons
    whatsapp_number: Optional[str] = Field(None, max_length=20)
    phone_number: Optional[str] = Field(None, max_length=20)
    contact_label: Optional[str] = Field(None, max_length=100)

    # Scheduling (future)
    available_days: Optional[str] = None
    available_hours: Optional[str] = None

    # Multi-language (future)
    translations: Optional[Dict[str, Any]] = None


class MenuUpdateDTO(BaseModel):
    """DTO for updating a menu"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    menu_type: Optional[str] = Field(None, pattern="^(restaurant|laundry|spa|room_service|other)$")

    # Display settings
    is_active: Optional[bool] = None
    show_prices: Optional[bool] = None
    display_mode: Optional[str] = Field(None, pattern="^(grid|list|carousel)$")
    theme_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")

    # Contact buttons
    whatsapp_number: Optional[str] = Field(None, max_length=20)
    phone_number: Optional[str] = Field(None, max_length=20)
    contact_label: Optional[str] = Field(None, max_length=100)

    # Scheduling
    available_days: Optional[str] = None
    available_hours: Optional[str] = None

    # Multi-language
    translations: Optional[Dict[str, Any]] = None


class MenuResponseDTO(BaseModel):
    """DTO for menu response"""
    id: int
    organization_id: int
    name: str
    description: Optional[str]
    menu_type: str

    # Display settings
    is_active: bool
    show_prices: bool
    display_mode: str
    theme_color: Optional[str]

    # Contact buttons
    whatsapp_number: Optional[str]
    phone_number: Optional[str]
    contact_label: Optional[str]

    # Scheduling
    available_days: Optional[str]
    available_hours: Optional[str]

    # Public access
    public_url_code: str
    public_url: Optional[str] = None  # Computed field
    qr_code_path: Optional[str]
    qr_code_url: Optional[str] = None  # Computed field
    qr_code_generated_at: Optional[datetime]

    # Multi-language
    translations: Optional[Dict[str, Any]]

    # Counts
    items_count: int = 0

    # Audit trail
    created_by_id: Optional[int]
    updated_by_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class MenuListResponseDTO(BaseModel):
    """DTO for paginated menu list"""
    items: List[MenuResponseDTO]
    total: int
    skip: int
    limit: int


# ==============================================================================
# Menu Item DTOs
# ==============================================================================

class MenuItemCreateDTO(BaseModel):
    """DTO for creating a menu item"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default='IDR', pattern="^[A-Z]{3}$")

    # Media
    image_url: Optional[str] = Field(None, max_length=500)
    video_url: Optional[str] = Field(None, max_length=500)
    content_id: Optional[int] = None

    # Categorization
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=200)

    # Display
    display_order: int = Field(default=0, ge=0)
    is_active: bool = True
    is_featured: bool = False
    is_available: bool = True

    # Multi-language
    translations: Optional[Dict[str, Any]] = None


class MenuItemUpdateDTO(BaseModel):
    """DTO for updating a menu item"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, pattern="^[A-Z]{3}$")

    # Media
    image_url: Optional[str] = Field(None, max_length=500)
    video_url: Optional[str] = Field(None, max_length=500)
    content_id: Optional[int] = None

    # Categorization
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=200)

    # Display
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_available: Optional[bool] = None

    # Multi-language
    translations: Optional[Dict[str, Any]] = None


class MenuItemResponseDTO(BaseModel):
    """DTO for menu item response"""
    id: int
    menu_id: int
    organization_id: int

    # Item details
    name: str
    description: Optional[str]
    price: Optional[Decimal]
    currency: str

    # Media
    image_url: Optional[str]
    video_url: Optional[str]
    content_id: Optional[int]

    # Categorization
    category: Optional[str]
    subcategory: Optional[str]
    tags: Optional[str]

    # Display
    display_order: int
    is_active: bool
    is_featured: bool
    is_available: bool

    # Multi-language
    translations: Optional[Dict[str, Any]]

    # Metadata
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class MenuItemListResponseDTO(BaseModel):
    """DTO for paginated menu item list"""
    items: List[MenuItemResponseDTO]
    total: int
    skip: int
    limit: int
    has_next: bool


class MenuItemReorderDTO(BaseModel):
    """DTO for reordering menu items"""
    item_orders: List[Dict[str, int]] = Field(..., min_length=1)
    # Example: [{"id": 1, "display_order": 0}, {"id": 2, "display_order": 1}]

    @field_validator('item_orders')
    @classmethod
    def validate_item_orders(cls, v):
        """Validate that each item has id and display_order"""
        for item in v:
            if 'id' not in item or 'display_order' not in item:
                raise ValueError("Each item must have 'id' and 'display_order'")
            if not isinstance(item['id'], int) or not isinstance(item['display_order'], int):
                raise ValueError("'id' and 'display_order' must be integers")
            if item['display_order'] < 0:
                raise ValueError("'display_order' must be non-negative")
        return v


# ==============================================================================
# Import/Export DTOs
# ==============================================================================

class MenuImportResultDTO(BaseModel):
    """DTO for Excel import result"""
    id: int
    menu_id: int
    filename: str
    file_size: Optional[int]
    rows_total: int
    rows_success: int
    rows_failed: int
    errors: Optional[List[Dict[str, Any]]]
    imported_by_id: Optional[int]
    imported_at: datetime

    class Config:
        from_attributes = True


class MenuImportHistoryListDTO(BaseModel):
    """DTO for import history list"""
    items: List[MenuImportResultDTO]
    total: int


# ==============================================================================
# Public Viewer DTOs
# ==============================================================================

class PublicMenuResponseDTO(BaseModel):
    """DTO for public menu view (no sensitive data)"""
    name: str
    description: Optional[str]
    menu_type: str

    # Display settings
    show_prices: bool
    display_mode: str
    theme_color: Optional[str]

    # Contact buttons
    whatsapp_number: Optional[str]
    phone_number: Optional[str]
    contact_label: Optional[str]

    # Multi-language
    translations: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class PublicMenuItemResponseDTO(BaseModel):
    """DTO for public menu item (no sensitive data)"""
    id: int
    name: str
    description: Optional[str]
    price: Optional[Decimal]
    currency: str

    # Media
    image_url: Optional[str]
    video_url: Optional[str]

    # Categorization
    category: Optional[str]
    subcategory: Optional[str]
    tags: Optional[str]

    # Display
    is_featured: bool
    is_available: bool

    # Multi-language
    translations: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class PublicMenuItemListDTO(BaseModel):
    """DTO for public menu item list with pagination"""
    menu: PublicMenuResponseDTO
    items: List[PublicMenuItemResponseDTO]
    total: int
    skip: int
    limit: int
    has_next: bool


# ==============================================================================
# Analytics DTOs
# ==============================================================================

class MenuViewTrackDTO(BaseModel):
    """DTO for tracking menu view"""
    viewer_ip: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = Field(None, pattern="^(mobile|tablet|desktop)$")
    contact_clicked: bool = False
    contact_type: Optional[str] = Field(None, pattern="^(whatsapp|phone)$")


class MenuAnalyticsDTO(BaseModel):
    """DTO for menu analytics summary"""
    menu_id: int
    total_views: int
    total_contact_clicks: int
    views_by_device: Dict[str, int]
    views_by_date: List[Dict[str, Any]]
    popular_times: List[Dict[str, Any]]


# ==============================================================================
# Category DTOs
# ==============================================================================

class MenuCategoryCreateDTO(BaseModel):
    """DTO for creating a menu category preset"""
    menu_type: str = Field(..., pattern="^(restaurant|laundry|spa|room_service|other)$")
    name: str = Field(..., min_length=1, max_length=100)
    display_order: int = Field(default=0, ge=0)
    icon: Optional[str] = Field(None, max_length=50)
    translations: Optional[Dict[str, Any]] = None


class MenuCategoryResponseDTO(BaseModel):
    """DTO for menu category response"""
    id: int
    organization_id: int
    menu_type: str
    name: str
    display_order: int
    icon: Optional[str]
    translations: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class MenuCategoryListDTO(BaseModel):
    """DTO for menu category list"""
    items: List[MenuCategoryResponseDTO]
    total: int
