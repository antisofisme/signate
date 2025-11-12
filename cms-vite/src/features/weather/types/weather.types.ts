/**
 * Weather Service Types
 *
 * Types for weather service integration
 */

export type WeatherProvider = 'openweathermap' | 'weatherapi' | 'tomorrow' | 'visualcrossing' | 'custom'

export type TemperatureUnit = 'celsius' | 'fahrenheit' | 'kelvin'
export type SpeedUnit = 'kmh' | 'mph' | 'ms'
export type PressureUnit = 'hpa' | 'inhg' | 'mmhg'

export interface WeatherConfig {
  id?: number
  organization_id: number
  provider: WeatherProvider
  api_key: string
  is_active: boolean
  default_location?: WeatherLocation
  units: WeatherUnits
  cache_duration_minutes: number
  created_at?: string
  updated_at?: string
}

export interface WeatherLocation {
  id?: number
  organization_id: number
  name: string
  latitude: number
  longitude: number
  city?: string
  country?: string
  timezone?: string
  is_default: boolean
  created_at?: string
  updated_at?: string
}

export interface WeatherUnits {
  temperature: TemperatureUnit
  speed: SpeedUnit
  pressure: PressureUnit
}

export interface WeatherData {
  location: WeatherLocation
  current: CurrentWeather
  forecast?: WeatherForecast[]
  alerts?: WeatherAlert[]
  last_updated: string
  provider: WeatherProvider
}

export interface CurrentWeather {
  temperature: number
  feels_like: number
  condition: string
  condition_code: string
  icon: string
  humidity: number
  wind_speed: number
  wind_direction: number
  wind_direction_text: string
  pressure: number
  visibility: number
  uv_index: number
  cloud_cover: number
  is_day: boolean
}

export interface WeatherForecast {
  date: string
  day_of_week: string
  temperature_max: number
  temperature_min: number
  condition: string
  condition_code: string
  icon: string
  precipitation_probability: number
  precipitation_amount: number
  humidity: number
  wind_speed: number
  sunrise?: string
  sunset?: string
}

export interface WeatherAlert {
  id: string
  severity: 'extreme' | 'severe' | 'moderate' | 'minor'
  title: string
  description: string
  start_time: string
  end_time: string
  source: string
}

// Request/Response types
export interface CreateWeatherConfigRequest {
  provider: WeatherProvider
  api_key: string
  default_location?: {
    name: string
    latitude: number
    longitude: number
  }
  units?: WeatherUnits
  cache_duration_minutes?: number
}

export interface UpdateWeatherConfigRequest {
  provider?: WeatherProvider
  api_key?: string
  is_active?: boolean
  default_location?: {
    name: string
    latitude: number
    longitude: number
  }
  units?: WeatherUnits
  cache_duration_minutes?: number
}

export interface CreateLocationRequest {
  name: string
  latitude: number
  longitude: number
  city?: string
  country?: string
  timezone?: string
  is_default?: boolean
}

export interface UpdateLocationRequest {
  name?: string
  latitude?: number
  longitude?: number
  city?: string
  country?: string
  timezone?: string
  is_default?: boolean
}

export interface TestWeatherAPIRequest {
  provider: WeatherProvider
  api_key: string
  latitude: number
  longitude: number
}

export interface TestWeatherAPIResponse {
  success: boolean
  message: string
  response_time_ms?: number
  sample_data?: {
    temperature: number
    condition: string
    location: string
  }
}

export interface GeocodingResult {
  name: string
  latitude: number
  longitude: number
  country: string
  state?: string
  display_name: string
}

// Provider metadata
export interface WeatherProviderInfo {
  id: WeatherProvider
  name: string
  description: string
  logo?: string
  features: string[]
  pricing: string
  free_tier: boolean
  free_tier_limit?: string
  requires_api_key: boolean
  documentation_url?: string
  signup_url?: string
}

export const WEATHER_PROVIDERS: WeatherProviderInfo[] = [
  {
    id: 'openweathermap',
    name: 'OpenWeatherMap',
    description: 'Popular weather API with global coverage',
    features: ['Current weather', '7-day forecast', 'Weather alerts', 'Historical data'],
    pricing: 'Free tier available',
    free_tier: true,
    free_tier_limit: '1,000 calls/day',
    requires_api_key: true,
    documentation_url: 'https://openweathermap.org/api',
    signup_url: 'https://home.openweathermap.org/users/sign_up',
  },
  {
    id: 'weatherapi',
    name: 'WeatherAPI.com',
    description: 'Comprehensive weather data with astronomy',
    features: ['Real-time weather', '14-day forecast', 'Astronomy', 'Air quality'],
    pricing: 'Free tier available',
    free_tier: true,
    free_tier_limit: '1 million calls/month',
    requires_api_key: true,
    documentation_url: 'https://www.weatherapi.com/docs/',
    signup_url: 'https://www.weatherapi.com/signup.aspx',
  },
  {
    id: 'tomorrow',
    name: 'Tomorrow.io',
    description: 'Hyperlocal weather forecasting',
    features: ['Minute forecast', 'Hyperlocal data', 'Weather layers', 'Climate data'],
    pricing: 'Free tier available',
    free_tier: true,
    free_tier_limit: '500 calls/day',
    requires_api_key: true,
    documentation_url: 'https://docs.tomorrow.io/',
    signup_url: 'https://www.tomorrow.io/weather-api/',
  },
  {
    id: 'visualcrossing',
    name: 'Visual Crossing',
    description: 'Historical and forecast weather data',
    features: ['15-day forecast', 'Historical data', 'Climate statistics', 'Weather graphs'],
    pricing: 'Free tier available',
    free_tier: true,
    free_tier_limit: '1,000 records/day',
    requires_api_key: true,
    documentation_url: 'https://www.visualcrossing.com/resources/documentation/weather-api/',
    signup_url: 'https://www.visualcrossing.com/weather-api',
  },
  {
    id: 'custom',
    name: 'Custom API',
    description: 'Custom weather API integration',
    features: ['Custom Integration'],
    pricing: 'Variable',
    free_tier: false,
    requires_api_key: true,
  },
]

export const TEMPERATURE_UNITS: Array<{ value: TemperatureUnit; label: string; symbol: string }> = [
  { value: 'celsius', label: 'Celsius', symbol: '°C' },
  { value: 'fahrenheit', label: 'Fahrenheit', symbol: '°F' },
  { value: 'kelvin', label: 'Kelvin', symbol: 'K' },
]

export const SPEED_UNITS: Array<{ value: SpeedUnit; label: string; symbol: string }> = [
  { value: 'kmh', label: 'Kilometers per hour', symbol: 'km/h' },
  { value: 'mph', label: 'Miles per hour', symbol: 'mph' },
  { value: 'ms', label: 'Meters per second', symbol: 'm/s' },
]

export const PRESSURE_UNITS: Array<{ value: PressureUnit; label: string; symbol: string }> = [
  { value: 'hpa', label: 'Hectopascals', symbol: 'hPa' },
  { value: 'inhg', label: 'Inches of mercury', symbol: 'inHg' },
  { value: 'mmhg', label: 'Millimeters of mercury', symbol: 'mmHg' },
]
