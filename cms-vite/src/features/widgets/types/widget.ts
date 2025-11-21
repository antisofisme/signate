/**
 * Widget Domain Types
 * Generated from backend-python/services/widget/dtos.py
 */

// ============================================================================
// Widget Types
// ============================================================================

export interface CreateWidgetRequest {
  name: string;
  description?: string;
  widget_type: string;
  config: Record<string, any>;
  layout?: Record<string, any>;
  is_active?: boolean;
}

export interface UpdateWidgetRequest {
  name?: string;
  description?: string;
  widget_type?: string;
  config?: Record<string, any>;
  layout?: Record<string, any>;
  is_active?: boolean;
}

export interface Widget {
  id: number;
  organization_id: number;
  name: string;
  description?: string;
  widget_type: string;
  config: Record<string, any>;
  layout?: Record<string, any>;
  is_active: boolean;
  created_by?: number;
  created_at: string;
  updated_at: string;
}

export interface WidgetListResponse {
  widgets: Widget[];
  total: number;
}

// ============================================================================
// Playlist Widget Types
// ============================================================================

export interface AssignWidgetToPlaylistRequest {
  widget_id: number;
  position?: number;
  display_duration?: number;
  z_index?: number;
}

export interface UpdatePlaylistWidgetRequest {
  position?: number;
  display_duration?: number;
  z_index?: number;
}

export interface PlaylistWidget {
  id: number;
  playlist_id: number;
  widget_id: number;
  position: number;
  display_duration?: number;
  z_index: number;
  created_at: string;
  widget?: Widget;
}

export interface PlaylistWidgetListResponse {
  playlist_widgets: PlaylistWidget[];
  total: number;
}

// ============================================================================
// Widget Type Configuration Schemas
// ============================================================================

export interface ClockWidgetConfig {
  format?: string;
  show_seconds?: boolean;
  timezone?: string;
  font_size?: number;
  color?: string;
  background_color?: string;
}

export interface WeatherWidgetConfig {
  location: string;
  api_key?: string;
  units?: string;
  refresh_interval?: number;
  show_forecast?: boolean;
  font_size?: number;
}

export interface HotelInfoWidgetConfig {
  info_type: string;
  title: string;
  content: string;
  icon?: string;
  font_size?: number;
  auto_rotate?: boolean;
  rotate_interval?: number;
}

export interface NewsTickerWidgetConfig {
  source?: string;
  items?: string[];
  rss_url?: string;
  scroll_speed?: number;
  direction?: string;
  font_size?: number;
}

export interface CustomWidgetConfig {
  html_content?: string;
  css_styles?: string;
  javascript?: string;
  data_source?: string;
}
