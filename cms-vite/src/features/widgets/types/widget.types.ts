/**
 * Widget Types
 * TypeScript interfaces for Widget System
 */

export type WidgetType = 'clock' | 'weather' | 'news' | 'hotel_info' | 'custom'

export interface WidgetLayout {
  x: number
  y: number
  width: number
  height: number
}

export interface ClockWidgetConfig {
  format: '12h' | '24h'
  timezone: string
  show_date: boolean
  show_seconds: boolean
  font_size?: number
  color?: string
}

export interface WeatherWidgetConfig {
  location: string
  units: 'metric' | 'imperial'
  show_forecast: boolean
  api_key?: string
}

export interface NewsWidgetConfig {
  rss_feed_url: string
  scroll_speed: number
  max_items: number
  show_images: boolean
}

export interface HotelInfoWidgetConfig {
  fields: string[]
  refresh_interval: number
  template?: string
}

export interface CustomWidgetConfig {
  html_content?: string
  css_styles?: string
  javascript?: string
}

export type WidgetConfig =
  | ClockWidgetConfig
  | WeatherWidgetConfig
  | NewsWidgetConfig
  | HotelInfoWidgetConfig
  | CustomWidgetConfig

export interface Widget {
  id: number
  organization_id: number
  name: string
  description?: string
  widget_type: WidgetType
  config: WidgetConfig
  layout: WidgetLayout
  created_at: string
  updated_at: string
}

export interface CreateWidgetRequest {
  name: string
  description?: string
  widget_type: WidgetType
  config: WidgetConfig
  layout: WidgetLayout
}

export interface UpdateWidgetRequest {
  name?: string
  description?: string
  widget_type?: WidgetType
  config?: WidgetConfig
  layout?: WidgetLayout
}

export interface PlaylistWidget {
  id: number
  playlist_id: number
  widget_id: number
  z_index: number
  is_enabled: boolean
  created_at: string
  widget?: Widget
}

export interface AssignWidgetToPlaylistRequest {
  widget_id: number
  z_index: number
  is_enabled: boolean
}

export interface UpdatePlaylistWidgetRequest {
  z_index?: number
  is_enabled?: boolean
}

export interface WidgetListResponse {
  widgets: Widget[]
  total: number
}

export interface WidgetFilters {
  widget_type?: WidgetType
  search?: string
  skip?: number
  limit?: number
}

// Widget type metadata for UI
export interface WidgetTypeInfo {
  type: WidgetType
  label: string
  description: string
  icon: string
  defaultConfig: WidgetConfig
  configSchema: any // JSON Schema for dynamic form
}

export const WIDGET_TYPES: Record<WidgetType, WidgetTypeInfo> = {
  clock: {
    type: 'clock',
    label: 'Digital Clock',
    description: 'Display current time with customizable format',
    icon: 'Clock',
    defaultConfig: {
      format: '24h',
      timezone: 'Asia/Jakarta',
      show_date: true,
      show_seconds: true,
      font_size: 48,
      color: '#ffffff'
    },
    configSchema: {
      format: { type: 'select', options: ['12h', '24h'], label: 'Time Format' },
      timezone: { type: 'text', label: 'Timezone' },
      show_date: { type: 'boolean', label: 'Show Date' },
      show_seconds: { type: 'boolean', label: 'Show Seconds' },
      font_size: { type: 'number', label: 'Font Size (px)', min: 12, max: 120 },
      color: { type: 'color', label: 'Text Color' }
    }
  },
  weather: {
    type: 'weather',
    label: 'Weather',
    description: 'Display current weather and forecast',
    icon: 'CloudSun',
    defaultConfig: {
      location: 'Jakarta',
      units: 'metric',
      show_forecast: true,
      api_key: ''
    },
    configSchema: {
      location: { type: 'text', label: 'Location' },
      units: { type: 'select', options: ['metric', 'imperial'], label: 'Units' },
      show_forecast: { type: 'boolean', label: 'Show Forecast' },
      api_key: { type: 'password', label: 'API Key (optional)' }
    }
  },
  news: {
    type: 'news',
    label: 'News Ticker',
    description: 'Scrolling news ticker from RSS feed',
    icon: 'Newspaper',
    defaultConfig: {
      rss_feed_url: '',
      scroll_speed: 50,
      max_items: 10,
      show_images: false
    },
    configSchema: {
      rss_feed_url: { type: 'url', label: 'RSS Feed URL' },
      scroll_speed: { type: 'number', label: 'Scroll Speed', min: 1, max: 100 },
      max_items: { type: 'number', label: 'Max Items', min: 1, max: 50 },
      show_images: { type: 'boolean', label: 'Show Images' }
    }
  },
  hotel_info: {
    type: 'hotel_info',
    label: 'Hotel Information',
    description: 'Display hotel information from PMS',
    icon: 'Hotel',
    defaultConfig: {
      fields: ['guest_name', 'room_number', 'checkout_date'],
      refresh_interval: 60,
      template: 'Welcome {{guest_name}} to Room {{room_number}}'
    },
    configSchema: {
      fields: { type: 'multiselect', label: 'Fields to Display', options: [
        'guest_name', 'room_number', 'checkin_date', 'checkout_date', 'room_type'
      ]},
      refresh_interval: { type: 'number', label: 'Refresh Interval (seconds)', min: 10, max: 3600 },
      template: { type: 'textarea', label: 'Display Template' }
    }
  },
  custom: {
    type: 'custom',
    label: 'Custom Widget',
    description: 'Custom HTML/CSS/JS widget',
    icon: 'Wrench',
    defaultConfig: {
      html_content: '<div>Custom Widget</div>',
      css_styles: '',
      javascript: ''
    },
    configSchema: {
      html_content: { type: 'code', label: 'HTML Content', language: 'html' },
      css_styles: { type: 'code', label: 'CSS Styles', language: 'css' },
      javascript: { type: 'code', label: 'JavaScript', language: 'javascript' }
    }
  }
}

// Canvas dimensions for layout editor
export const CANVAS_WIDTH = 1920
export const CANVAS_HEIGHT = 1080

// Default layout
export const DEFAULT_LAYOUT: WidgetLayout = {
  x: 10,
  y: 10,
  width: 200,
  height: 100
}
