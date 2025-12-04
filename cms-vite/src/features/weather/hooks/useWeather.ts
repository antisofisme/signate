/**
 * Weather React Hooks
 *
 * Custom hooks for weather service using TanStack Query
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from '@/shared/utils/toast'
import * as weatherApi from '../api/weatherApi'
import type {
  WeatherConfig,
  WeatherLocation,
  WeatherData,
  CreateWeatherConfigRequest,
  UpdateWeatherConfigRequest,
  CreateLocationRequest,
  UpdateLocationRequest,
  TestWeatherAPIRequest,
} from '../types/weather.types'
import { getApiErrorMessage } from '@/shared/utils/types'

// ===================================
// Query Keys
// ===================================

export const WEATHER_KEYS = {
  all: ['weather'] as const,
  config: () => [...WEATHER_KEYS.all, 'config'] as const,
  locations: () => [...WEATHER_KEYS.all, 'locations'] as const,
  location: (id: number) => [...WEATHER_KEYS.all, 'location', id] as const,
  data: (locationId: number) => [...WEATHER_KEYS.all, 'data', locationId] as const,
  dataByCoords: (lat: number, lon: number) => [...WEATHER_KEYS.all, 'data', lat, lon] as const,
}

// ===================================
// Configuration Hooks
// ===================================

/**
 * Get weather configuration
 */
export function useWeatherConfig() {
  return useQuery({
    queryKey: WEATHER_KEYS.config(),
    queryFn: weatherApi.getWeatherConfig,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Create weather configuration
 */
export function useCreateWeatherConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateWeatherConfigRequest) => weatherApi.createWeatherConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WEATHER_KEYS.config() })
      toast.success('Weather configuration created successfully')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to create weather configuration'))
    },
  })
}

/**
 * Update weather configuration
 */
export function useUpdateWeatherConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateWeatherConfigRequest) => weatherApi.updateWeatherConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WEATHER_KEYS.config() })
      toast.success('Weather configuration updated successfully')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to update weather configuration'))
    },
  })
}

/**
 * Delete weather configuration
 */
export function useDeleteWeatherConfig() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: weatherApi.deleteWeatherConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WEATHER_KEYS.config() })
      toast.success('Weather configuration deleted successfully')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to delete weather configuration'))
    },
  })
}

/**
 * Test weather API
 */
export function useTestWeatherAPI() {
  return useMutation({
    mutationFn: (data: TestWeatherAPIRequest) => weatherApi.testWeatherAPI(data),
    onSuccess: (data) => {
      if (data.success) {
        toast.success(`API test successful! Response time: ${data.response_time_ms}ms`)
      } else {
        toast.error(`API test failed: ${data.message}`)
      }
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'API test failed'))
    },
  })
}

// ===================================
// Location Hooks
// ===================================

/**
 * Get weather locations
 */
export function useWeatherLocations() {
  return useQuery({
    queryKey: WEATHER_KEYS.locations(),
    queryFn: weatherApi.getLocations,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

/**
 * Get single location
 */
export function useWeatherLocation(locationId: number) {
  return useQuery({
    queryKey: WEATHER_KEYS.location(locationId),
    queryFn: () => weatherApi.getLocation(locationId),
    enabled: !!locationId,
  })
}

/**
 * Create location
 */
export function useCreateLocation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateLocationRequest) => weatherApi.createLocation(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WEATHER_KEYS.locations() })
      toast.success('Location added successfully')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to add location'))
    },
  })
}

/**
 * Update location
 */
export function useUpdateLocation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ locationId, data }: { locationId: number; data: UpdateLocationRequest }) =>
      weatherApi.updateLocation(locationId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WEATHER_KEYS.locations() })
      toast.success('Location updated successfully')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to update location'))
    },
  })
}

/**
 * Delete location
 */
export function useDeleteLocation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (locationId: number) => weatherApi.deleteLocation(locationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: WEATHER_KEYS.locations() })
      toast.success('Location deleted successfully')
    },
    onError: (error: unknown) => {
      toast.error(getApiErrorMessage(error, 'Failed to delete location'))
    },
  })
}

// ===================================
// Weather Data Hooks
// ===================================

/**
 * Get weather data for location
 */
export function useWeatherData(locationId: number) {
  return useQuery({
    queryKey: WEATHER_KEYS.data(locationId),
    queryFn: () => weatherApi.getWeatherData(locationId),
    enabled: !!locationId,
    staleTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: 10 * 60 * 1000, // Auto-refresh every 10 minutes
  })
}

/**
 * Get weather data by coordinates
 */
export function useWeatherByCoords(latitude: number, longitude: number, enabled: boolean = true) {
  return useQuery({
    queryKey: WEATHER_KEYS.dataByCoords(latitude, longitude),
    queryFn: () => weatherApi.getWeatherByCoords(latitude, longitude),
    enabled: enabled && !!latitude && !!longitude,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

/**
 * Search locations (geocoding)
 */
export function useSearchLocations(query: string) {
  return useQuery({
    queryKey: [...WEATHER_KEYS.all, 'search', query] as const,
    queryFn: () => weatherApi.searchLocations(query),
    enabled: query.length >= 3, // Only search if query is at least 3 characters
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// ===================================
// Helper Hooks
// ===================================

/**
 * Check if weather is configured
 */
export function useHasWeatherConfig() {
  const { data: config, isLoading } = useWeatherConfig()
  return {
    hasConfig: !!config,
    isActive: config?.is_active || false,
    isLoading,
  }
}

/**
 * Get default location
 */
export function useDefaultLocation() {
  const { data: locations } = useWeatherLocations()
  return locations?.find((loc) => loc.is_default)
}
