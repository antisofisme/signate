export interface Template {
  id: string;
  name: string;
  description?: string;
  content: string;
  category: TemplateCategory;
  variables: TemplateVariable[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by?: string;
  usage_count?: number;
}

export type TemplateCategory = 'text' | 'weather' | 'firebird' | 'custom' | 'system';

export interface TemplateVariable {
  name: string;
  type: VariableType;
  category: VariableCategory;
  description: string;
  example?: string;
  required?: boolean;
  default_value?: string;
}

export type VariableType = 'string' | 'number' | 'date' | 'boolean' | 'object' | 'array';

export type VariableCategory = 'system' | 'weather' | 'firebird' | 'custom' | 'device';

export interface TemplatePreviewRequest {
  template_id?: string;
  content?: string;
  device_id?: string;
  sample_data?: Record<string, any>;
}

export interface TemplatePreviewResponse {
  rendered: string;
  variables_used: string[];
  errors?: string[];
  warnings?: string[];
}

export interface TemplateValidationRequest {
  content: string;
}

export interface TemplateValidationResponse {
  valid: boolean;
  errors?: string[];
  warnings?: string[];
  variables_found: string[];
  security_issues?: string[];
}

export interface CreateTemplateRequest {
  name: string;
  description?: string;
  content: string;
  category: TemplateCategory;
  is_active?: boolean;
}

export interface UpdateTemplateRequest {
  name?: string;
  description?: string;
  content?: string;
  category?: TemplateCategory;
  is_active?: boolean;
}

export interface TemplateListParams {
  category?: TemplateCategory;
  search?: string;
  is_active?: boolean;
  page?: number;
  limit?: number;
}

export const SYSTEM_VARIABLES: TemplateVariable[] = [
  {
    name: 'current_date',
    type: 'date',
    category: 'system',
    description: 'Current date in various formats',
    example: '{{ current_date | format_date("%Y-%m-%d") }}',
  },
  {
    name: 'current_time',
    type: 'string',
    category: 'system',
    description: 'Current time in HH:MM:SS format',
    example: '{{ current_time }}',
  },
  {
    name: 'current_datetime',
    type: 'date',
    category: 'system',
    description: 'Current date and time',
    example: '{{ current_datetime }}',
  },
  {
    name: 'day_name',
    type: 'string',
    category: 'system',
    description: 'Current day name (Monday, Tuesday, etc.)',
    example: '{{ day_name }}',
  },
  {
    name: 'month_name',
    type: 'string',
    category: 'system',
    description: 'Current month name (January, February, etc.)',
    example: '{{ month_name }}',
  },
  {
    name: 'year',
    type: 'number',
    category: 'system',
    description: 'Current year',
    example: '{{ year }}',
  },
];

export const WEATHER_VARIABLES: TemplateVariable[] = [
  {
    name: 'weather.temperature',
    type: 'number',
    category: 'weather',
    description: 'Current temperature in Celsius',
    example: '{{ weather.temperature }}°C',
  },
  {
    name: 'weather.condition',
    type: 'string',
    category: 'weather',
    description: 'Weather condition (Sunny, Cloudy, Rainy, etc.)',
    example: '{{ weather.condition }}',
  },
  {
    name: 'weather.humidity',
    type: 'number',
    category: 'weather',
    description: 'Humidity percentage',
    example: '{{ weather.humidity }}%',
  },
  {
    name: 'weather.wind_speed',
    type: 'number',
    category: 'weather',
    description: 'Wind speed in km/h',
    example: '{{ weather.wind_speed }} km/h',
  },
  {
    name: 'weather.location',
    type: 'string',
    category: 'weather',
    description: 'Weather location/city',
    example: '{{ weather.location }}',
  },
  {
    name: 'weather.icon',
    type: 'string',
    category: 'weather',
    description: 'Weather icon URL or code',
    example: '<img src="{{ weather.icon }}" />',
  },
];

export const DEVICE_VARIABLES: TemplateVariable[] = [
  {
    name: 'device.name',
    type: 'string',
    category: 'device',
    description: 'Device display name',
    example: '{{ device.name }}',
  },
  {
    name: 'device.location',
    type: 'string',
    category: 'device',
    description: 'Device location',
    example: '{{ device.location }}',
  },
  {
    name: 'device.ip_address',
    type: 'string',
    category: 'device',
    description: 'Device IP address',
    example: '{{ device.ip_address }}',
  },
  {
    name: 'device.tags',
    type: 'array',
    category: 'device',
    description: 'Device tags',
    example: '{% for tag in device.tags %}{{ tag }}{% endfor %}',
  },
];

export const FIREBIRD_VARIABLES: TemplateVariable[] = [
  {
    name: 'firebird.query_result',
    type: 'array',
    category: 'firebird',
    description: 'Results from Firebird SQL query',
    example: '{% for row in firebird.query_result %}{{ row.column_name }}{% endfor %}',
  },
  {
    name: 'firebird.connection_status',
    type: 'string',
    category: 'firebird',
    description: 'Firebird database connection status',
    example: '{{ firebird.connection_status }}',
  },
];

export const ALL_VARIABLES = [
  ...SYSTEM_VARIABLES,
  ...WEATHER_VARIABLES,
  ...DEVICE_VARIABLES,
  ...FIREBIRD_VARIABLES,
];
