/**
 * Template Types
 * TypeScript interfaces for Template System
 */

export type TemplateType = 'text' | 'image' | 'video' | 'html' | 'greeting'

export interface Template {
  id: number
  organization_id: number
  name: string
  description?: string
  content: string
  template_type: TemplateType
  variables: Record<string, string>
  preview_data?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface CreateTemplateRequest {
  name: string
  description?: string
  content: string
  template_type: TemplateType
  variables?: Record<string, string>
  preview_data?: Record<string, any>
}

export interface UpdateTemplateRequest {
  name?: string
  description?: string
  content?: string
  template_type?: TemplateType
  variables?: Record<string, string>
  preview_data?: Record<string, any>
}

export interface TemplateListResponse {
  templates: Template[]
  total: number
}

export interface TemplateFilters {
  template_type?: TemplateType
  search?: string
  skip?: number
  limit?: number
}

export interface RenderTemplateRequest {
  data: Record<string, any>
}

export interface RenderTemplateResponse {
  rendered_content: string
  variables_used: string[]
  render_time_ms: number
}

export interface ValidateTemplateRequest {
  content: string
}

export interface ValidateTemplateResponse {
  is_valid: boolean
  errors: string[]
  variables: string[]
}

export interface ExtractVariablesRequest {
  content: string
}

export interface ExtractVariablesResponse {
  variables: string[]
}

// Template type metadata for UI
export interface TemplateTypeInfo {
  type: TemplateType
  label: string
  description: string
  icon: string
  exampleContent: string
  exampleVariables: Record<string, string>
}

export const TEMPLATE_TYPES: Record<TemplateType, TemplateTypeInfo> = {
  text: {
    type: 'text',
    label: 'Text Template',
    description: 'Plain text with variable substitution',
    icon: '📝',
    exampleContent: 'Welcome {{guest_name}} to {{hotel_name}}!\n\nYour room: {{room_number}}\nCheck-in: {{checkin_date}}\nCheck-out: {{checkout_date}}',
    exampleVariables: {
      guest_name: 'string',
      hotel_name: 'string',
      room_number: 'string',
      checkin_date: 'string',
      checkout_date: 'string'
    }
  },
  image: {
    type: 'image',
    label: 'Image Template',
    description: 'Image with text overlay',
    icon: '🖼️',
    exampleContent: '<div class="image-overlay">\n  <h1>{{title}}</h1>\n  <p>{{subtitle}}</p>\n</div>',
    exampleVariables: {
      title: 'string',
      subtitle: 'string',
      background_url: 'string'
    }
  },
  video: {
    type: 'video',
    label: 'Video Template',
    description: 'Video with text overlay',
    icon: '🎥',
    exampleContent: '<div class="video-overlay">\n  <h2>{{message}}</h2>\n  <span>{{timestamp}}</span>\n</div>',
    exampleVariables: {
      message: 'string',
      timestamp: 'string',
      video_url: 'string'
    }
  },
  html: {
    type: 'html',
    label: 'HTML Template',
    description: 'Full HTML template with styling',
    icon: '🌐',
    exampleContent: '<!DOCTYPE html>\n<html>\n<head>\n  <title>{{page_title}}</title>\n</head>\n<body>\n  <h1>{{heading}}</h1>\n  <p>{{content}}</p>\n</body>\n</html>',
    exampleVariables: {
      page_title: 'string',
      heading: 'string',
      content: 'string'
    }
  },
  greeting: {
    type: 'greeting',
    label: 'Greeting Message',
    description: 'Welcome/greeting messages for guests',
    icon: '👋',
    exampleContent: 'Good {{time_of_day}}, {{guest_name}}!\n\nWelcome to {{hotel_name}}.\nYour room {{room_number}} is ready.\n\nEnjoy your stay!',
    exampleVariables: {
      time_of_day: 'string',
      guest_name: 'string',
      hotel_name: 'string',
      room_number: 'string'
    }
  }
}

// Variable type definitions
export type VariableType = 'string' | 'number' | 'boolean' | 'date'

export interface VariableDefinition {
  name: string
  type: VariableType
  required: boolean
  default_value?: any
  description?: string
}

// Preview data for testing
export const DEFAULT_PREVIEW_DATA: Record<string, any> = {
  guest_name: 'John Smith',
  hotel_name: 'Grand Hotel',
  room_number: '305',
  checkin_date: '2025-01-13',
  checkout_date: '2025-01-16',
  time_of_day: 'Morning',
  title: 'Welcome',
  subtitle: 'Enjoy your stay',
  heading: 'Hello',
  content: 'This is a sample content',
  message: 'Important Message',
  timestamp: '2025-01-11 10:30',
  page_title: 'Guest Portal'
}
