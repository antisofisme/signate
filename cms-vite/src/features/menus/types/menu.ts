/**
 * Menu Types for Digital Menu Feature
 */

export type MenuType = 'restaurant' | 'laundry' | 'spa' | 'room_service' | 'other';
export type DisplayMode = 'grid' | 'list' | 'carousel' | 'minimalist';
export type DeviceType = 'mobile' | 'tablet' | 'desktop';
export type ContactType = 'whatsapp' | 'phone';

export interface Menu {
  id: number;
  organization_id: number;
  name: string;
  description?: string;
  menu_type: MenuType;

  // Display settings
  is_active: boolean;
  show_prices: boolean;
  display_mode: DisplayMode;
  theme_color?: string;

  // Contact buttons
  whatsapp_number?: string;
  phone_number?: string;
  contact_label?: string;
  outlet_extension?: string;

  // Footer customization
  footer_description?: string;

  // Scheduling (future)
  available_days?: string;
  available_hours?: string;

  // Public access
  public_url_code: string;
  public_url?: string;
  qr_code_path?: string;
  qr_code_url?: string;
  qr_code_generated_at?: string;

  // Multi-language (future)
  translations?: Record<string, any>;

  // Counts
  items_count: number;

  // Audit trail
  created_by_id?: number;
  updated_by_id?: number;
  created_at: string;
  updated_at?: string;
}

export interface MenuItemMedia {
  id: number;
  url: string;
  type: 'image' | 'video';
  is_primary: boolean;
}

export interface MenuItem {
  id: number;
  menu_id: number;
  organization_id: number;

  // Item details
  name: string;
  description?: string;
  price?: number;
  currency: string;

  // Media
  image_url?: string;
  video_url?: string;
  content_id?: number;
  media?: MenuItemMedia[]; // Multiple media items

  // Categorization
  category?: string;
  subcategory?: string;
  tags?: string;

  // Display
  display_order: number;
  is_active: boolean;
  is_featured: boolean;
  is_available: boolean;

  // Multi-language
  translations?: Record<string, any>;

  // Metadata
  created_at: string;
  updated_at?: string;
}

export interface MenuImportHistory {
  id: number;
  menu_id: number;
  filename: string;
  file_size?: number;
  rows_total: number;
  rows_success: number;
  rows_failed: number;
  errors?: Array<{ row: number; error: string }>;
  imported_by_id?: number;
  imported_at: string;
}

// API Request/Response types

export interface MenuCreateRequest {
  name: string;
  menu_type: MenuType;
  description?: string;
  is_active?: boolean;
  show_prices?: boolean;
  display_mode?: DisplayMode;
  theme_color?: string;
  whatsapp_number?: string;
  phone_number?: string;
  contact_label?: string;
  outlet_extension?: string;
  footer_description?: string;
  available_days?: string;
  available_hours?: string;
  translations?: Record<string, any>;
}

export interface MenuUpdateRequest {
  name?: string;
  menu_type?: MenuType;
  description?: string;
  is_active?: boolean;
  show_prices?: boolean;
  display_mode?: DisplayMode;
  theme_color?: string;
  whatsapp_number?: string;
  phone_number?: string;
  contact_label?: string;
  outlet_extension?: string;
  footer_description?: string;
  available_days?: string;
  available_hours?: string;
  translations?: Record<string, any>;
}

export interface MenuListResponse {
  items: Menu[];
  total: number;
  skip: number;
  limit: number;
}

export interface MenuItemCreateRequest {
  name: string;
  description?: string;
  price?: number;
  currency?: string;
  image_url?: string;
  video_url?: string;
  content_id?: number;
  category?: string;
  subcategory?: string;
  tags?: string;
  display_order?: number;
  is_active?: boolean;
  is_featured?: boolean;
  is_available?: boolean;
  translations?: Record<string, any>;
}

export interface MenuItemUpdateRequest {
  name?: string;
  description?: string;
  price?: number;
  currency?: string;
  image_url?: string;
  video_url?: string;
  content_id?: number;
  category?: string;
  subcategory?: string;
  tags?: string;
  display_order?: number;
  is_active?: boolean;
  is_featured?: boolean;
  is_available?: boolean;
  translations?: Record<string, any>;
}

export interface MenuItemListResponse {
  items: MenuItem[];
  total: number;
  skip: number;
  limit: number;
  has_next: boolean;
}

export interface MenuImportResult {
  id: number;
  filename: string;
  rows_total: number;
  rows_success: number;
  rows_failed: number;
  errors: Array<{ row: number; error: string }>;
  status: 'success' | 'partial' | 'failed';
}

export interface MenuListParams {
  skip?: number;
  limit?: number;
  menu_type?: MenuType;
  is_active?: boolean;
}

export interface MenuItemListParams {
  skip?: number;
  limit?: number;
  category?: string;
  is_active?: boolean;
  is_featured?: boolean;
}

// Menu Media types
export interface MenuMedia {
  id: number;
  organization_id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  file_hash?: string;  // SHA-256 hash for deduplication
  width?: number;
  height?: number;
  thumbnail_path?: string;
  title?: string;
  alt_text?: string;
  is_active: boolean;
  uploaded_by_id?: number;
  deleted_by_id?: number;
  created_at: string;
  updated_at?: string;
  deleted_at?: string;
  url?: string;
  is_duplicate?: boolean;  // Flag when uploaded file is duplicate
}

// Menu Media Duplicate types
export interface MenuMediaDuplicateUsage {
  menu_items: Array<{
    id: number;
    name: string;
    menu_id: number;
    menu_name: string;
  }>;
  used_count: number;
}

export interface MenuMediaDuplicateItem {
  id: number;
  title: string;
  original_filename: string;
  created_at: string;
  is_active: boolean;
  usage: MenuMediaDuplicateUsage;
}

export interface MenuMediaDuplicateGroup {
  file_hash: string;
  file_size: number;
  mime_type: string;
  duplicate_count: number;
  wasted_storage: number;
  media: MenuMediaDuplicateItem[];
}

export interface MenuMediaDuplicatesResponse {
  duplicates: MenuMediaDuplicateGroup[];
  total_groups: number;
  total_wasted_bytes: number;
  total_wasted_readable: string;
}

export interface MenuMediaListResponse {
  items: MenuMedia[];
  total: number;
  skip: number;
  limit: number;
  has_next: boolean;
}

export interface MenuMediaFilters {
  skip?: number;
  limit?: number;
  search?: string;
  mime_type?: string;
  is_active?: boolean;
}

// Menu Category types (per-menu categories)
export interface MenuCategory {
  id: number;
  organization_id: number;
  menu_id?: number;
  menu_type: MenuType;
  name: string;
  display_order: number;
  icon?: string;
  translations?: Record<string, any>;
  created_at: string;
}

export interface MenuCategoryCreateRequest {
  menu_type: MenuType;
  name: string;
  display_order?: number;
  icon?: string;
  translations?: Record<string, any>;
  menu_id?: number;
}

export interface MenuCategoryUpdateRequest {
  name?: string;
  display_order?: number;
  icon?: string;
  translations?: Record<string, any>;
}

export interface MenuCategoryListResponse {
  items: MenuCategory[];
  total: number;
}

export interface MenuCategoryReorderRequest {
  category_orders: Array<{ id: number; display_order: number }>;
}

// Menu Item Media types (multiple media per item)
export interface MenuItemMedia {
  id: number;
  menu_item_id: number;
  menu_media_id: number;
  display_order: number;
  is_primary: boolean;
  created_at: string;
  media?: MenuMedia;
}

export interface MenuItemMediaAddRequest {
  menu_media_id: number;
  display_order?: number;
  is_primary?: boolean;
}

export interface MenuItemMediaListResponse {
  items: MenuItemMedia[];
  total: number;
}

export interface MenuItemMediaBulkSetRequest {
  media_ids: number[];
  primary_media_id?: number;
}

export interface MenuItemMediaReorderRequest {
  media_orders: Array<{ menu_media_id: number; display_order: number }>;
}

// PIN Verification types
export interface PINVerifyRequest {
  pin: string;
}

export interface PINVerifyResponse {
  verified: boolean;
  message: string;
}
