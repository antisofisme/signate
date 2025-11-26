/**
 * Menu Types for Digital Menu Feature
 */

export type MenuType = 'restaurant' | 'laundry' | 'spa' | 'room_service' | 'other';
export type DisplayMode = 'grid' | 'list' | 'carousel';
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
