/**
 * Weather API Client
 *
 * API functions for weather service integration
 */

import { apiClient } from '@/lib/api/client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import type {
  WeatherConfig,
  WeatherLocation,
  WeatherData,
  CreateWeatherConfigRequest,
  UpdateWeatherConfigRequest,
  CreateLocationRequest,
  UpdateLocationRequest,
  TestWeatherAPIRequest,
  TestWeatherAPIResponse,
  GeocodingResult,
} from '../types/weather.types'

/**
 * Get weather configuration
 */
export const getWeatherConfig = async (): Promise<WeatherConfig | null> => {
  const response = await apiClient.get<WeatherConfig>(API_ENDPOINTS.WEATHER.CONFIG)
  return response.data
}

/**
 * Create weather configuration
 */
export const createWeatherConfig = async (
  data: CreateWeatherConfigRequest
): Promise<WeatherConfig> => {
  const response = await apiClient.post<WeatherConfig>(API_ENDPOINTS.WEATHER.CONFIG, data)
  return response.data
}

/**
 * Update weather configuration
 */
export const updateWeatherConfig = async (
  data: UpdateWeatherConfigRequest
): Promise<WeatherConfig> => {
  const response = await apiClient.put<WeatherConfig>(API_ENDPOINTS.WEATHER.CONFIG, data)
  return response.data
}

/**
 * Delete weather configuration
 */
export const deleteWeatherConfig = async (): Promise<void> => {
  await apiClient.delete(API_ENDPOINTS.WEATHER.CONFIG)
}

/**
 * Test weather API connection
 */
export const testWeatherAPI = async (
  data: TestWeatherAPIRequest
): Promise<TestWeatherAPIResponse> => {
  const response = await apiClient.post<TestWeatherAPIResponse>(
    API_ENDPOINTS.WEATHER.TEST_API,
    data
  )
  return response.data
}

/**
 * Get weather locations
 */
export const getLocations = async (): Promise<WeatherLocation[]> => {
  const response = await apiClient.get<WeatherLocation[]>(API_ENDPOINTS.WEATHER.LOCATIONS)
  return response.data
}

/**
 * Get single location
 */
export const getLocation = async (locationId: number): Promise<WeatherLocation> => {
  const response = await apiClient.get<WeatherLocation>(API_ENDPOINTS.WEATHER.LOCATION(locationId))
  return response.data
}

/**
 * Create location
 */
export const createLocation = async (data: CreateLocationRequest): Promise<WeatherLocation> => {
  const response = await apiClient.post<WeatherLocation>(API_ENDPOINTS.WEATHER.LOCATIONS, data)
  return response.data
}

/**
 * Update location
 */
export const updateLocation = async (
  locationId: number,
  data: UpdateLocationRequest
): Promise<WeatherLocation> => {
  const response = await apiClient.put<WeatherLocation>(
    API_ENDPOINTS.WEATHER.LOCATION(locationId),
    data
  )
  return response.data
}

/**
 * Delete location
 */
export const deleteLocation = async (locationId: number): Promise<void> => {
  await apiClient.delete(API_ENDPOINTS.WEATHER.LOCATION(locationId))
}

/**
 * Get weather data for location
 */
export const getWeatherData = async (locationId: number): Promise<WeatherData> => {
  const response = await apiClient.get<WeatherData>(API_ENDPOINTS.WEATHER.DATA(locationId))
  return response.data
}

/**
 * Get weather data for coordinates
 */
export const getWeatherByCoords = async (
  latitude: number,
  longitude: number
): Promise<WeatherData> => {
  const response = await apiClient.get<WeatherData>(API_ENDPOINTS.WEATHER.BY_COORDS, {
    params: { latitude, longitude },
  })
  return response.data
}

/**
 * Search locations by name (geocoding)
 */
export const searchLocations = async (query: string): Promise<GeocodingResult[]> => {
  const response = await apiClient.get<GeocodingResult[]>(API_ENDPOINTS.WEATHER.GEOCODING, {
    params: { q: query },
  })
  return response.data
}
