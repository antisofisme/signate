"""SQLAlchemy models for Digital Menu feature"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text,
    DECIMAL, ARRAY
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from shared.database import Base


class MenuModel(Base):
    """Digital Menu database model"""
    __tablename__ = "menus"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Menu identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    menu_type = Column(String(50), nullable=False, index=True)
    tab_name = Column(String(100), nullable=True)  # Custom tab label for portal

    # Display settings
    is_active = Column(Boolean, default=True, nullable=False)
    show_prices = Column(Boolean, default=True, nullable=False)
    display_mode = Column(String(20), default='grid', nullable=False)

    # Color scheme (60-30-10 principle)
    primary_color = Column(String(7), default='#ffffff', nullable=True)  # 60% - Background
    secondary_color = Column(String(7), default='#f3f4f6', nullable=True)  # 30% - Header/Categories
    theme_color = Column(String(7), nullable=True)  # 10% - Accent (CTAs, highlights)

    # Contact buttons
    whatsapp_number = Column(String(20), nullable=True)
    phone_number = Column(String(20), nullable=True)
    contact_label = Column(String(100), nullable=True)
    outlet_extension = Column(String(50), nullable=True)  # Phone extension badge

    # Footer customization
    footer_description = Column(Text, nullable=True)

    # Multi-language support (future)
    translations = Column(JSONB, nullable=True)

    # Scheduling (future)
    available_days = Column(String(50), nullable=True)
    available_hours = Column(String(20), nullable=True)

    # Public access
    public_url_code = Column(String(12), unique=True, nullable=False, index=True)
    qr_code_path = Column(String(500), nullable=True)
    qr_code_generated_at = Column(DateTime(timezone=True), nullable=True)

    # Audit trail
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relationships
    organization = relationship("OrganizationModel", foreign_keys=[organization_id])
    items = relationship("MenuItemModel", back_populates="menu", cascade="all, delete-orphan")
    import_history = relationship("MenuImportHistoryModel", back_populates="menu", cascade="all, delete-orphan")
    views = relationship("MenuViewModel", back_populates="menu", cascade="all, delete-orphan")
    creator = relationship("UserModel", foreign_keys=[created_by_id])
    updater = relationship("UserModel", foreign_keys=[updated_by_id])


class MenuItemModel(Base):
    """Menu Item database model"""
    __tablename__ = "menu_items"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    menu_id = Column(
        Integer,
        ForeignKey("menus.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="SET NULL"), nullable=True)
    menu_media_id = Column(Integer, ForeignKey("menu_media.id", ondelete="SET NULL"), nullable=True)

    # Item details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(12, 2), nullable=True)
    currency = Column(String(3), default='IDR', nullable=False)

    # Media URLs
    image_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)

    # Categorization
    category = Column(String(100), nullable=True, index=True)
    subcategory = Column(String(100), nullable=True)
    variant = Column(String(200), nullable=True)  # Item variations: Hot, Cold, Large, Small
    tags = Column(String(200), nullable=True)

    # Display
    display_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False, index=True)

    # Availability
    is_available = Column(Boolean, default=True, nullable=False)

    # Multi-language support (future)
    translations = Column(JSONB, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relationships
    menu = relationship("MenuModel", back_populates="items", foreign_keys=[menu_id])
    organization = relationship("OrganizationModel", foreign_keys=[organization_id])
    content = relationship("ContentModel", foreign_keys=[content_id])
    menu_media = relationship("MenuMediaModel", foreign_keys=[menu_media_id])
    media_items = relationship("MenuItemMediaModel", back_populates="menu_item", foreign_keys="MenuItemMediaModel.menu_item_id", lazy="selectin")


class MenuImportHistoryModel(Base):
    """Menu Import History database model"""
    __tablename__ = "menu_import_history"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    menu_id = Column(
        Integer,
        ForeignKey("menus.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    imported_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Import details
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    rows_total = Column(Integer, nullable=False)
    rows_success = Column(Integer, nullable=False)
    rows_failed = Column(Integer, nullable=False)

    # Error tracking
    errors = Column(JSONB, nullable=True)

    # Metadata
    imported_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    menu = relationship("MenuModel", back_populates="import_history", foreign_keys=[menu_id])
    organization = relationship("OrganizationModel", foreign_keys=[organization_id])
    importer = relationship("UserModel", foreign_keys=[imported_by_id])


class MenuViewModel(Base):
    """Menu View Analytics database model"""
    __tablename__ = "menu_views"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    menu_id = Column(
        Integer,
        ForeignKey("menus.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # View details
    viewer_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(20), nullable=True)

    # Interaction
    contact_clicked = Column(Boolean, default=False, nullable=False)
    contact_type = Column(String(20), nullable=True)

    # Timestamp
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    menu = relationship("MenuModel", back_populates="views", foreign_keys=[menu_id])
    organization = relationship("OrganizationModel", foreign_keys=[organization_id])


class MenuMediaModel(Base):
    """Menu Media database model - images specifically for menus"""
    __tablename__ = "menu_media"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    uploaded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    deleted_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 for deduplication

    # Image metadata
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    # Thumbnail
    thumbnail_path = Column(String(500), nullable=True)

    # Display
    title = Column(String(200), nullable=True)
    alt_text = Column(String(255), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Image optimization (WebP variants)
    variants = Column(JSONB, nullable=True)  # {thumb, small, hd, 4k, original, fallback}
    content_hash = Column(String(64), nullable=True, index=True)  # For cache invalidation
    processing_status = Column(String(20), default='pending')  # pending, processing, completed, failed
    optimized_at = Column(DateTime(timezone=True), nullable=True)
    original_width = Column(Integer, nullable=True)  # Original dimensions before processing
    original_height = Column(Integer, nullable=True)
    is_animated = Column(Boolean, default=False)  # True for animated GIFs

    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relationships
    organization = relationship("OrganizationModel", foreign_keys=[organization_id])
    uploader = relationship("UserModel", foreign_keys=[uploaded_by_id])
    deleter = relationship("UserModel", foreign_keys=[deleted_by_id])


class MenuCategoryModel(Base):
    """Menu Category Preset database model"""
    __tablename__ = "menu_categories"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    menu_id = Column(
        Integer,
        ForeignKey("menus.id", ondelete="CASCADE"),
        nullable=True,  # Nullable for backward compatibility
        index=True
    )

    # Category details
    menu_type = Column(String(50), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    icon = Column(String(50), nullable=True)

    # Multi-language
    translations = Column(JSONB, nullable=True)

    # Subcategories - array of subcategory names
    subcategories = Column(JSONB, default=[], nullable=False)  # ["Nasi", "Mie", "Ayam"]

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    organization = relationship("OrganizationModel", foreign_keys=[organization_id])
    menu = relationship("MenuModel", foreign_keys=[menu_id])


class MenuItemMediaModel(Base):
    """Junction table for multiple media per menu item"""
    __tablename__ = "menu_item_media"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    menu_item_id = Column(
        Integer,
        ForeignKey("menu_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    menu_media_id = Column(
        Integer,
        ForeignKey("menu_media.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Display settings
    display_order = Column(Integer, default=0, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    menu_item = relationship("MenuItemModel", foreign_keys=[menu_item_id], back_populates="media_items")
    menu_media = relationship("MenuMediaModel", foreign_keys=[menu_media_id], lazy="selectin")
