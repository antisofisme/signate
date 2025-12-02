/**
 * Portal Viewer Types
 * TypeScript interfaces for menu portal data
 */

export interface PortalOrganization {
  id: number;
  name: string;
  portal_slug: string;
  logo_url: string | null;
}

export interface PortalMenu {
  id: number;
  name: string;
  menu_type: 'restaurant' | 'laundry' | 'spa' | 'room_service' | 'other';
  public_url_code: string;
  public_url: string;
  description: string | null;
  display_mode: 'grid' | 'list' | 'carousel' | 'minimalist';
  primary_color: string | null;
  secondary_color: string | null;
  theme_color: string | null;
}

export interface PortalResponse {
  organization: PortalOrganization;
  menus: PortalMenu[];
  total: number;
}

export interface PortalViewerConfig {
  apiBaseUrl: string;
  portalSlug: string;
}

// Menu type icons mapping
export const MENU_TYPE_ICONS: Record<string, string> = {
  restaurant: '🍽️',
  laundry: '👔',
  spa: '💆',
  room_service: '🛎️',
  other: '📋'
};

// Menu type display labels
export const MENU_TYPE_LABELS: Record<string, string> = {
  restaurant: 'Restaurant',
  laundry: 'Laundry',
  spa: 'Spa',
  room_service: 'Room Service',
  other: 'Other'
};
