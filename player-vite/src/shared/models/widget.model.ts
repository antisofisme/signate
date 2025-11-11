/**
 * Widget Models for Player
 */

export enum WidgetType {
  CLOCK = 'clock',
  WEATHER = 'weather',
  TEXT = 'text',
  CALENDAR = 'calendar',
  HTML = 'html',
}

export interface WidgetPosition {
  x: number;
  y: number;
  width: number;
  height: number;
  z_index?: number;
}

export interface BaseWidget {
  id: string;
  type: WidgetType;
  name: string;
  position: WidgetPosition;
  is_visible: boolean;
  animation?: {
    type: 'fade' | 'slide' | 'none';
    duration: number;
  };
}

// Clock Widget Configuration
export interface ClockConfig {
  format: '12h' | '24h';
  show_seconds: boolean;
  timezone?: string;
  style: 'digital' | 'analog';
  font_size?: number;
  color?: string;
}

export interface ClockWidget extends BaseWidget {
  type: WidgetType.CLOCK;
  config: ClockConfig;
}

// Weather Widget Configuration
export interface WeatherConfig {
  location: string;
  api_key?: string;
  units: 'metric' | 'imperial';
  show_forecast: boolean;
  forecast_days?: number;
  update_interval: number; // minutes
  style: 'minimal' | 'detailed' | 'forecast';
}

export interface WeatherWidget extends BaseWidget {
  type: WidgetType.WEATHER;
  config: WeatherConfig;
}

// Text Widget Configuration
export interface TextConfig {
  content: string;
  font_family?: string;
  font_size?: number;
  color?: string;
  background_color?: string;
  text_align?: 'left' | 'center' | 'right';
  scroll?: {
    enabled: boolean;
    direction: 'left' | 'right' | 'up' | 'down';
    speed: number;
  };
  template_variables?: boolean; // Enable template processing
}

export interface TextWidget extends BaseWidget {
  type: WidgetType.TEXT;
  config: TextConfig;
}

// Calendar Widget Configuration
export interface CalendarConfig {
  view: 'month' | 'week' | 'day';
  show_events: boolean;
  calendar_url?: string; // iCal URL
  theme: 'light' | 'dark';
  highlight_today: boolean;
  show_week_numbers?: boolean;
}

export interface CalendarWidget extends BaseWidget {
  type: WidgetType.CALENDAR;
  config: CalendarConfig;
}

// HTML/iFrame Widget Configuration
export interface HtmlConfig {
  content?: string; // HTML content
  url?: string; // External URL
  refresh_interval?: number; // seconds
  allow_interaction: boolean;
  sandbox_options?: string[];
}

export interface HtmlWidget extends BaseWidget {
  type: WidgetType.HTML;
  config: HtmlConfig;
}

// Union type for all widgets
export type Widget = ClockWidget | WeatherWidget | TextWidget | CalendarWidget | HtmlWidget;

// Widget content (from API)
export interface WidgetContent {
  id: number;
  content_id: number;
  widget_data: Widget;
  created_at: string;
  updated_at: string;
}

// Widget render context
export interface WidgetRenderContext {
  container: HTMLElement;
  variables?: Record<string, any>; // Template variables
  locale?: string;
  theme?: 'light' | 'dark';
}

// Widget renderer interface
export interface IWidgetRenderer {
  render(widget: Widget, context: WidgetRenderContext): Promise<void>;
  update(widget: Widget, context: WidgetRenderContext): Promise<void>;
  destroy(): void;
}