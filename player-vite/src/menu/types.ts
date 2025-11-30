/**
 * Menu Viewer Types
 * TypeScript interfaces for public menu data
 */

export interface PublicMenu {
  name: string;
  description: string | null;
  menu_type: 'restaurant' | 'laundry' | 'spa' | 'room_service' | 'other';
  show_prices: boolean;
  display_mode: 'grid' | 'list' | 'carousel';
  theme_color: string | null;
  whatsapp_number: string | null;
  phone_number: string | null;
  contact_label: string | null;
  translations: Record<string, unknown> | null;
}

export interface PublicMenuItem {
  id: number;
  name: string;
  description: string | null;
  price: number | null;
  currency: string;
  image_url: string | null;
  video_url: string | null;
  category: string | null;
  subcategory: string | null;
  tags: string | null;
  is_featured: boolean;
  is_available: boolean;
  translations: Record<string, unknown> | null;
}

export interface PublicMenuResponse {
  menu: PublicMenu;
  items: PublicMenuItem[];
  total: number;
  skip: number;
  limit: number;
  has_next: boolean;
}

export interface MenuViewerConfig {
  apiBaseUrl: string;
  publicCode: string;
}
