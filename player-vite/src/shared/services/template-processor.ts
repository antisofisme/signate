/**
 * Template Processor Service
 * Processes template variables from various sources
 */

import { logger } from '@shared/logger';
import { SharedAPIClient } from '@shared/api';

export interface TemplateVariable {
  key: string;
  value: any;
  source: 'system' | 'device' | 'pms' | 'custom' | 'weather' | 'api';
  refreshInterval?: number; // in seconds
}

export interface PMSData {
  guest_name?: string;
  room_number?: string;
  check_in_date?: string;
  check_out_date?: string;
  balance?: number;
  loyalty_level?: string;
  language?: string;
  [key: string]: any;
}

export interface WeatherData {
  temperature?: number;
  temperature_unit?: 'C' | 'F';
  condition?: string;
  humidity?: number;
  wind_speed?: number;
  [key: string]: any;
}

export class TemplateProcessor {
  private variables: Map<string, TemplateVariable> = new Map();
  private refreshTimers: Map<string, number> = new Map();
  private systemIntervals: number[] = []; // Track system variable refresh intervals
  private pmsData: PMSData | null = null;
  private weatherData: WeatherData | null = null;
  private deviceId: string | null = null;

  constructor() {
    logger.info('[TemplateProcessor] Service initialized');
    this.initializeSystemVariables();
  }

  /**
   * Initialize the template processor with device context
   */
  async initialize(deviceId: string): Promise<void> {
    this.deviceId = deviceId;
    
    // Load device-specific data
    await this.loadDeviceData();
    
    // Start auto-refresh for time-based variables
    this.startSystemVariableRefresh();
    
    // Load initial PMS and weather data
    await Promise.all([
      this.refreshPMSData(),
      this.refreshWeatherData()
    ]);

    logger.info('[TemplateProcessor] Initialization complete');
  }

  /**
   * Process a template string, replacing variables with their values
   */
  processTemplate(template: string, additionalVariables?: Record<string, any>): string {
    // Get all current variables
    const allVariables = this.getAllVariables();
    
    // Merge with additional variables if provided
    if (additionalVariables) {
      Object.assign(allVariables, additionalVariables);
    }

    // Replace {{variable}} patterns
    return template.replace(/\{\{(\w+(?:\.\w+)*)\}\}/g, (match, path) => {
      const value = this.getNestedValue(allVariables, path);
      return value !== undefined ? String(value) : match;
    });
  }

  /**
   * Process template with specific context (async for data fetching)
   */
  async processTemplateAsync(
    template: string, 
    context?: {
      refreshPMS?: boolean;
      refreshWeather?: boolean;
      locale?: string;
    }
  ): Promise<string> {
    // Refresh data if requested
    if (context?.refreshPMS) {
      await this.refreshPMSData();
    }
    
    if (context?.refreshWeather) {
      await this.refreshWeatherData();
    }

    return this.processTemplate(template);
  }

  /**
   * Get all current template variables
   */
  getAllVariables(): Record<string, any> {
    const result: Record<string, any> = {};
    
    // Add all registered variables
    this.variables.forEach((variable, key) => {
      result[key] = variable.value;
    });

    // Add PMS data if available
    if (this.pmsData) {
      Object.entries(this.pmsData).forEach(([key, value]) => {
        result[`pms_${key}`] = value;
      });
    }

    // Add weather data if available
    if (this.weatherData) {
      Object.entries(this.weatherData).forEach(([key, value]) => {
        result[`weather_${key}`] = value;
      });
    }

    return result;
  }

  /**
   * Register a custom variable
   */
  registerVariable(variable: TemplateVariable): void {
    this.variables.set(variable.key, variable);
    
    // Set up refresh if interval specified
    if (variable.refreshInterval && variable.refreshInterval > 0) {
      this.setupVariableRefresh(variable);
    }

    logger.debug(`[TemplateProcessor] Registered variable: ${variable.key}`);
  }

  /**
   * Update PMS data
   */
  updatePMSData(data: PMSData): void {
    this.pmsData = { ...this.pmsData, ...data };
    logger.debug('[TemplateProcessor] PMS data updated', data);
  }

  /**
   * Initialize system variables
   */
  private initializeSystemVariables(): void {
    // Date/Time variables
    this.registerVariable({
      key: 'current_time',
      value: new Date().toLocaleTimeString(),
      source: 'system',
      refreshInterval: 1
    });

    this.registerVariable({
      key: 'current_date',
      value: new Date().toLocaleDateString(),
      source: 'system',
      refreshInterval: 60
    });

    this.registerVariable({
      key: 'day_of_week',
      value: new Date().toLocaleDateString('en-US', { weekday: 'long' }),
      source: 'system',
      refreshInterval: 60
    });

    this.registerVariable({
      key: 'month',
      value: new Date().toLocaleDateString('en-US', { month: 'long' }),
      source: 'system',
      refreshInterval: 3600
    });

    this.registerVariable({
      key: 'year',
      value: new Date().getFullYear(),
      source: 'system',
      refreshInterval: 3600
    });
  }

  /**
   * Start refreshing system variables
   */
  private startSystemVariableRefresh(): void {
    // Update time every second - track interval
    const timeInterval = window.setInterval(() => {
      this.updateVariable('current_time', new Date().toLocaleTimeString());
    }, 1000);
    this.systemIntervals.push(timeInterval);

    // Update date variables every minute - track interval
    const dateInterval = window.setInterval(() => {
      const now = new Date();
      this.updateVariable('current_date', now.toLocaleDateString());
      this.updateVariable('day_of_week', now.toLocaleDateString('en-US', { weekday: 'long' }));
    }, 60000);
    this.systemIntervals.push(dateInterval);

    // Update month/year every hour - track interval
    const monthYearInterval = window.setInterval(() => {
      const now = new Date();
      this.updateVariable('month', now.toLocaleDateString('en-US', { month: 'long' }));
      this.updateVariable('year', now.getFullYear());
    }, 3600000);
    this.systemIntervals.push(monthYearInterval);
  }

  /**
   * Load device-specific data
   */
  private async loadDeviceData(): Promise<void> {
    try {
      if (!this.deviceId) return;

      // Get device info from API
      const response = await SharedAPIClient.get<any>(`/api/v1/devices/${this.deviceId}`);
      const device = response.success ? response.data : response;

      // Register device variables
      this.registerVariable({
        key: 'device_id',
        value: device.device_id,
        source: 'device'
      });

      this.registerVariable({
        key: 'device_name',
        value: device.name,
        source: 'device'
      });

      this.registerVariable({
        key: 'device_location',
        value: device.location || 'Unknown',
        source: 'device'
      });

      this.registerVariable({
        key: 'organization_name',
        value: device.organization?.name || '',
        source: 'device'
      });

    } catch (error) {
      logger.error('[TemplateProcessor] Error loading device data:', error);
    }
  }

  /**
   * Refresh PMS data from backend
   */
  private async refreshPMSData(): Promise<void> {
    try {
      if (!this.deviceId) return;

      const response = await SharedAPIClient.get<PMSData>(`/api/v1/pms/device/${this.deviceId}/current-guest`);
      
      if (response.success && response.data) {
        this.pmsData = response.data;
        logger.debug('[TemplateProcessor] PMS data refreshed:', this.pmsData);
      }
    } catch (error) {
      logger.error('[TemplateProcessor] Error refreshing PMS data:', error);
    }
  }

  /**
   * Refresh weather data
   */
  private async refreshWeatherData(): Promise<void> {
    try {
      // Get location from device or use default
      const location = this.variables.get('device_location')?.value || 'Jakarta';
      
      const response = await SharedAPIClient.get<WeatherData>(`/api/v1/weather/current?location=${encodeURIComponent(location)}`);
      
      if (response.success && response.data) {
        this.weatherData = response.data;
        logger.debug('[TemplateProcessor] Weather data refreshed:', this.weatherData);
      }
    } catch (error) {
      logger.error('[TemplateProcessor] Error refreshing weather data:', error);
    }
  }

  /**
   * Update a variable value
   */
  private updateVariable(key: string, value: any): void {
    const variable = this.variables.get(key);
    if (variable) {
      variable.value = value;
    }
  }

  /**
   * Set up refresh timer for a variable
   */
  private setupVariableRefresh(variable: TemplateVariable): void {
    if (!variable.refreshInterval) return;

    // Clear existing timer
    const existingTimer = this.refreshTimers.get(variable.key);
    if (existingTimer) {
      clearInterval(existingTimer);
    }

    // Set up new timer
    const timer = window.setInterval(async () => {
      try {
        // Refresh based on source
        switch (variable.source) {
          case 'pms':
            await this.refreshPMSData();
            break;
          case 'weather':
            await this.refreshWeatherData();
            break;
          case 'api':
            // Custom API refresh logic
            break;
        }
      } catch (error) {
        logger.error(`[TemplateProcessor] Error refreshing ${variable.key}:`, error);
      }
    }, variable.refreshInterval * 1000);

    this.refreshTimers.set(variable.key, timer);
  }

  /**
   * Get nested value from object using dot notation
   */
  private getNestedValue(obj: Record<string, any>, path: string): any {
    const keys = path.split('.');
    let value = obj;
    
    for (const key of keys) {
      if (value && typeof value === 'object' && key in value) {
        value = value[key];
      } else {
        return undefined;
      }
    }
    
    return value;
  }

  /**
   * Format variable value based on type
   */
  formatValue(value: any, format?: string): string {
    if (value === null || value === undefined) {
      return '';
    }

    // Date formatting
    if (value instanceof Date) {
      if (format) {
        // Use format string (simplified)
        switch (format) {
          case 'time':
            return value.toLocaleTimeString();
          case 'date':
            return value.toLocaleDateString();
          case 'datetime':
            return value.toLocaleString();
          default:
            return value.toString();
        }
      }
      return value.toLocaleDateString();
    }

    // Number formatting
    if (typeof value === 'number') {
      if (format) {
        switch (format) {
          case 'currency':
            return new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD'
            }).format(value);
          case 'percent':
            return `${Math.round(value * 100)}%`;
          default:
            return value.toString();
        }
      }
      return value.toString();
    }

    // Default string conversion
    return String(value);
  }

  /**
   * Clean up resources
   */
  destroy(): void {
    // Clear all refresh timers
    this.refreshTimers.forEach(timer => clearInterval(timer));
    this.refreshTimers.clear();

    // Clear system variable intervals
    this.systemIntervals.forEach(intervalId => clearInterval(intervalId));
    this.systemIntervals = [];

    // Clear data
    this.variables.clear();
    this.pmsData = null;
    this.weatherData = null;

    logger.info('[TemplateProcessor] Service destroyed');
  }
}

// Export singleton instance
export const templateProcessor = new TemplateProcessor();