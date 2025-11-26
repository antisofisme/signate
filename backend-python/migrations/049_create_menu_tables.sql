-- Migration: 049
-- Description: Create digital menu tables (menus, menu_items, menu_import_history, menu_views, menu_categories)
-- Date: 2025-11-26
-- Feature: Digital Menu System for hotel services (restaurant, laundry, spa, etc.)

BEGIN;

-- ==============================================================================
-- Table: menus (Primary entity for digital menus)
-- ==============================================================================

CREATE TABLE menus (
  id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

  -- Menu identification
  name VARCHAR(255) NOT NULL,
  description TEXT,
  menu_type VARCHAR(50) NOT NULL,  -- 'restaurant', 'laundry', 'spa', 'room_service'

  -- Display settings
  is_active BOOLEAN DEFAULT TRUE NOT NULL,
  show_prices BOOLEAN DEFAULT TRUE NOT NULL,  -- Toggle price visibility
  display_mode VARCHAR(20) DEFAULT 'grid',     -- 'grid', 'list', 'carousel'
  theme_color VARCHAR(7),                      -- Hex color for branding (e.g., '#FF5733')

  -- Contact buttons
  whatsapp_number VARCHAR(20),
  phone_number VARCHAR(20),
  contact_label VARCHAR(100),

  -- Multi-language support (future)
  translations JSONB,  -- {"en": {"name": "...", "description": "..."}, "id": {...}}

  -- Scheduling (future)
  available_days VARCHAR(50),    -- '1,2,3,4,5' (Mon-Fri)
  available_hours VARCHAR(20),   -- '08:00-22:00'

  -- Public access
  public_url_code VARCHAR(12) UNIQUE NOT NULL,  -- Random code for public URL
  qr_code_path VARCHAR(500),                    -- Path to generated QR code image
  qr_code_generated_at TIMESTAMP WITH TIME ZONE,

  -- Audit trail
  created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  updated_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE,
  deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for menus
CREATE INDEX idx_menus_org ON menus(organization_id);
CREATE INDEX idx_menus_org_active ON menus(organization_id, is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_menus_public_url ON menus(public_url_code) WHERE deleted_at IS NULL;
CREATE INDEX idx_menus_type ON menus(organization_id, menu_type);
CREATE INDEX idx_menus_deleted ON menus(deleted_at) WHERE deleted_at IS NOT NULL;

-- Check constraints
ALTER TABLE menus ADD CONSTRAINT check_menus_menu_type
  CHECK (menu_type IN ('restaurant', 'laundry', 'spa', 'room_service', 'other'));

ALTER TABLE menus ADD CONSTRAINT check_menus_display_mode
  CHECK (display_mode IN ('grid', 'list', 'carousel'));

ALTER TABLE menus ADD CONSTRAINT check_menus_theme_color_format
  CHECK (theme_color IS NULL OR theme_color ~ '^#[0-9A-Fa-f]{6}$');

-- Comments
COMMENT ON TABLE menus IS 'Digital menus for hotel services (restaurant, laundry, spa, etc.)';
COMMENT ON COLUMN menus.public_url_code IS 'Unique code for public URL access (e.g., https://player.zhmhotels.online/menu/ABC123XYZ)';
COMMENT ON COLUMN menus.show_prices IS 'Toggle to show/hide prices in public view';
COMMENT ON COLUMN menus.display_mode IS 'Layout mode for public viewer (grid, list, carousel)';
COMMENT ON COLUMN menus.translations IS 'Multi-language translations stored as JSONB';

-- ==============================================================================
-- Table: menu_items (Individual items within a menu)
-- ==============================================================================

CREATE TABLE menu_items (
  id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  menu_id INTEGER NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

  -- Item details
  name VARCHAR(255) NOT NULL,
  description TEXT,
  price DECIMAL(12, 2),  -- Nullable for "Market Price" or free items
  currency VARCHAR(3) DEFAULT 'IDR',

  -- Media (URLs from Content Library)
  image_url VARCHAR(500),      -- Reference to uploaded content
  video_url VARCHAR(500),      -- Reference to uploaded content
  content_id INTEGER REFERENCES contents(id) ON DELETE SET NULL,  -- Link to content library

  -- Categorization
  category VARCHAR(100),       -- 'Appetizer', 'Main Course', 'Dessert', 'Beverages'
  subcategory VARCHAR(100),    -- 'Pizza', 'Pasta', 'Seafood'
  tags VARCHAR(200),           -- 'vegetarian,spicy,halal' (comma-separated)

  -- Display
  display_order INTEGER DEFAULT 0 NOT NULL,
  is_active BOOLEAN DEFAULT TRUE NOT NULL,
  is_featured BOOLEAN DEFAULT FALSE NOT NULL,  -- Highlight on menu

  -- Availability (future extension)
  is_available BOOLEAN DEFAULT TRUE NOT NULL,  -- Stock/availability toggle

  -- Multi-language support (future)
  translations JSONB,  -- {"en": {"name": "...", "description": "..."}}

  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE,
  deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for menu_items
CREATE INDEX idx_menu_items_menu ON menu_items(menu_id);
CREATE INDEX idx_menu_items_org ON menu_items(organization_id);
CREATE INDEX idx_menu_items_menu_order ON menu_items(menu_id, display_order, is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_menu_items_category ON menu_items(menu_id, category) WHERE deleted_at IS NULL;
CREATE INDEX idx_menu_items_featured ON menu_items(menu_id, is_featured) WHERE is_featured = TRUE AND deleted_at IS NULL;
CREATE INDEX idx_menu_items_content ON menu_items(content_id);
CREATE INDEX idx_menu_items_deleted ON menu_items(deleted_at) WHERE deleted_at IS NOT NULL;

-- Check constraints
ALTER TABLE menu_items ADD CONSTRAINT check_menu_items_price_positive
  CHECK (price IS NULL OR price >= 0);

ALTER TABLE menu_items ADD CONSTRAINT check_menu_items_currency_format
  CHECK (currency ~ '^[A-Z]{3}$');

ALTER TABLE menu_items ADD CONSTRAINT check_menu_items_display_order_non_negative
  CHECK (display_order >= 0);

-- Comments
COMMENT ON TABLE menu_items IS 'Individual items within a digital menu';
COMMENT ON COLUMN menu_items.content_id IS 'Optional link to content library for better media management';
COMMENT ON COLUMN menu_items.price IS 'Price in specified currency; NULL for market price or free items';
COMMENT ON COLUMN menu_items.display_order IS 'Sort order within menu (0-indexed)';
COMMENT ON COLUMN menu_items.is_featured IS 'Highlight this item in public viewer';

-- ==============================================================================
-- Table: menu_import_history (Excel import tracking)
-- ==============================================================================

CREATE TABLE menu_import_history (
  id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  menu_id INTEGER NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

  -- Import details
  filename VARCHAR(255) NOT NULL,
  file_size INTEGER,
  rows_total INTEGER NOT NULL,
  rows_success INTEGER NOT NULL,
  rows_failed INTEGER NOT NULL,

  -- Error tracking
  errors JSONB,  -- [{"row": 5, "error": "Invalid price format"}]

  -- Import metadata
  imported_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for menu_import_history
CREATE INDEX idx_import_history_menu ON menu_import_history(menu_id);
CREATE INDEX idx_import_history_org ON menu_import_history(organization_id);
CREATE INDEX idx_import_history_imported_at ON menu_import_history(imported_at DESC);

-- Check constraints
ALTER TABLE menu_import_history ADD CONSTRAINT check_import_history_rows_non_negative
  CHECK (rows_total >= 0 AND rows_success >= 0 AND rows_failed >= 0);

ALTER TABLE menu_import_history ADD CONSTRAINT check_import_history_rows_sum
  CHECK (rows_total = rows_success + rows_failed);

ALTER TABLE menu_import_history ADD CONSTRAINT check_import_history_file_size_positive
  CHECK (file_size IS NULL OR file_size > 0);

-- Comments
COMMENT ON TABLE menu_import_history IS 'Audit trail for Excel imports with error tracking';
COMMENT ON COLUMN menu_import_history.errors IS 'Array of error objects with row numbers and messages';

-- ==============================================================================
-- Table: menu_views (Analytics tracking)
-- ==============================================================================

CREATE TABLE menu_views (
  id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  menu_id INTEGER NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

  -- View details
  viewer_ip VARCHAR(45),       -- IPv4 or IPv6
  user_agent TEXT,
  device_type VARCHAR(20),     -- 'mobile', 'tablet', 'desktop'

  -- Interaction
  contact_clicked BOOLEAN DEFAULT FALSE,
  contact_type VARCHAR(20),    -- 'whatsapp', 'phone'

  -- Timestamp
  viewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for menu_views (partitioning recommended for large datasets)
CREATE INDEX idx_menu_views_menu_date ON menu_views(menu_id, viewed_at DESC);
CREATE INDEX idx_menu_views_org_date ON menu_views(organization_id, viewed_at DESC);
CREATE INDEX idx_menu_views_date ON menu_views(viewed_at DESC);

-- Check constraints
ALTER TABLE menu_views ADD CONSTRAINT check_menu_views_device_type
  CHECK (device_type IS NULL OR device_type IN ('mobile', 'tablet', 'desktop'));

ALTER TABLE menu_views ADD CONSTRAINT check_menu_views_contact_type
  CHECK (contact_type IS NULL OR contact_type IN ('whatsapp', 'phone'));

-- Comments
COMMENT ON TABLE menu_views IS 'Analytics tracking for menu views and interactions';
COMMENT ON COLUMN menu_views.viewer_ip IS 'IP address of viewer (for analytics)';
COMMENT ON COLUMN menu_views.contact_clicked IS 'Whether contact button was clicked during this view';

-- ==============================================================================
-- Table: menu_categories (Category presets for menu types)
-- ==============================================================================

CREATE TABLE menu_categories (
  id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  menu_type VARCHAR(50) NOT NULL,  -- 'restaurant', 'laundry', 'spa'

  -- Category details
  name VARCHAR(100) NOT NULL,
  display_order INTEGER DEFAULT 0,
  icon VARCHAR(50),  -- Icon name for UI

  -- Multi-language
  translations JSONB,  -- {"en": "Appetizers", "id": "Makanan Pembuka"}

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for menu_categories
CREATE INDEX idx_menu_categories_org_type ON menu_categories(organization_id, menu_type);
CREATE INDEX idx_menu_categories_org_type_order ON menu_categories(organization_id, menu_type, display_order);

-- Unique constraint
ALTER TABLE menu_categories ADD CONSTRAINT unique_menu_categories_org_type_name
  UNIQUE (organization_id, menu_type, name);

-- Check constraints
ALTER TABLE menu_categories ADD CONSTRAINT check_menu_categories_menu_type
  CHECK (menu_type IN ('restaurant', 'laundry', 'spa', 'room_service', 'other'));

ALTER TABLE menu_categories ADD CONSTRAINT check_menu_categories_display_order
  CHECK (display_order >= 0);

-- Comments
COMMENT ON TABLE menu_categories IS 'Reusable category templates for menu items';
COMMENT ON COLUMN menu_categories.menu_type IS 'Type of menu this category applies to';
COMMENT ON COLUMN menu_categories.icon IS 'Icon identifier for frontend rendering';

COMMIT;
