/**
 * Weather Widget Renderer
 */

import { WeatherWidget, WidgetRenderContext, IWidgetRenderer } from '../../models/widget.model';
import { logger } from '../../logger';

interface WeatherData {
  temperature: number;
  condition: string;
  icon: string;
  humidity: number;
  wind_speed: number;
  forecast?: Array<{
    date: string;
    temp_min: number;
    temp_max: number;
    condition: string;
    icon: string;
  }>;
}

export class WeatherRenderer implements IWidgetRenderer {
  private container?: HTMLElement;
  private updateInterval?: number;
  private currentWidget?: WeatherWidget;
  private cachedData?: WeatherData;
  private lastUpdate?: Date;

  async render(widget: WeatherWidget, context: WidgetRenderContext): Promise<void> {
    this.container = context.container;
    this.currentWidget = widget;

    // Clear existing content
    this.container.innerHTML = '';

    const { config } = widget;

    // Create weather container
    const weatherEl = document.createElement('div');
    weatherEl.className = `widget-weather ${config.style}`;
    weatherEl.style.cssText = `
      width: 100%;
      height: 100%;
      padding: 15px;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      color: #ffffff;
      font-family: 'Segoe UI', Arial, sans-serif;
      background: linear-gradient(135deg, rgba(0,0,0,0.2) 0%, rgba(0,0,0,0.4) 100%);
      border-radius: 10px;
      overflow: hidden;
    `;

    // Initial render with cached data or loading state
    if (this.cachedData && this.isDataFresh()) {
      this.renderWeatherContent(weatherEl, this.cachedData, config);
    } else {
      this.renderLoading(weatherEl);
      await this.fetchWeatherData(widget.config);
    }

    this.container.appendChild(weatherEl);
    
    // Start update interval
    this.startUpdateInterval();
  }

  async update(widget: WeatherWidget, context: WidgetRenderContext): Promise<void> {
    this.currentWidget = widget;
    await this.render(widget, context);
  }

  destroy(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = undefined;
    }
    if (this.container) {
      this.container.innerHTML = '';
    }
    logger.debug('[WeatherRenderer] Destroyed');
  }

  private renderLoading(container: HTMLElement): void {
    container.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: center; height: 100%;">
        <div style="text-align: center;">
          <div class="weather-loading" style="
            width: 50px;
            height: 50px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
          "></div>
          <div>Loading weather...</div>
        </div>
      </div>
      <style>
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      </style>
    `;
  }

  private renderWeatherContent(container: HTMLElement, data: WeatherData, config: WeatherWidget['config']): void {
    container.innerHTML = '';

    switch (config.style) {
      case 'minimal':
        this.renderMinimalStyle(container, data, config);
        break;
      
      case 'detailed':
        this.renderDetailedStyle(container, data, config);
        break;
      
      case 'forecast':
        this.renderForecastStyle(container, data, config);
        break;
      
      default:
        this.renderMinimalStyle(container, data, config);
    }
  }

  private renderMinimalStyle(container: HTMLElement, data: WeatherData, config: WeatherWidget['config']): void {
    const temp = this.formatTemperature(data.temperature, config.units);
    
    container.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: space-between; height: 100%;">
        <div style="display: flex; align-items: center; gap: 15px;">
          <div class="weather-icon" style="font-size: 48px;">
            ${this.getWeatherIcon(data.icon)}
          </div>
          <div>
            <div style="font-size: 42px; font-weight: 300; line-height: 1;">
              ${temp}
            </div>
            <div style="font-size: 16px; opacity: 0.8; margin-top: 5px;">
              ${data.condition}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  private renderDetailedStyle(container: HTMLElement, data: WeatherData, config: WeatherWidget['config']): void {
    const temp = this.formatTemperature(data.temperature, config.units);
    const windSpeed = this.formatWindSpeed(data.wind_speed, config.units);
    
    container.innerHTML = `
      <div style="height: 100%; display: flex; flex-direction: column;">
        <div style="text-align: center; margin-bottom: 20px;">
          <div style="font-size: 14px; opacity: 0.7; margin-bottom: 5px;">
            ${config.location}
          </div>
          <div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
            <div class="weather-icon" style="font-size: 64px;">
              ${this.getWeatherIcon(data.icon)}
            </div>
            <div>
              <div style="font-size: 48px; font-weight: 300;">
                ${temp}
              </div>
              <div style="font-size: 18px; opacity: 0.8;">
                ${data.condition}
              </div>
            </div>
          </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: auto;">
          <div style="text-align: center;">
            <div style="font-size: 14px; opacity: 0.7;">Humidity</div>
            <div style="font-size: 20px; margin-top: 5px;">${data.humidity}%</div>
          </div>
          <div style="text-align: center;">
            <div style="font-size: 14px; opacity: 0.7;">Wind</div>
            <div style="font-size: 20px; margin-top: 5px;">${windSpeed}</div>
          </div>
        </div>
      </div>
    `;
  }

  private renderForecastStyle(container: HTMLElement, data: WeatherData, config: WeatherWidget['config']): void {
    const temp = this.formatTemperature(data.temperature, config.units);
    const forecast = data.forecast || [];
    const daysToShow = Math.min(config.forecast_days || 3, forecast.length);
    
    container.innerHTML = `
      <div style="height: 100%; display: flex; flex-direction: column;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
          <div>
            <div style="font-size: 14px; opacity: 0.7;">${config.location}</div>
            <div style="font-size: 32px; font-weight: 300; margin-top: 5px;">${temp}</div>
          </div>
          <div class="weather-icon" style="font-size: 48px;">
            ${this.getWeatherIcon(data.icon)}
          </div>
        </div>
        
        <div style="flex: 1; overflow-y: auto;">
          <div style="display: flex; gap: 10px; justify-content: space-between;">
            ${forecast.slice(0, daysToShow).map(day => `
              <div style="flex: 1; text-align: center; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 8px;">
                <div style="font-size: 12px; opacity: 0.7; margin-bottom: 8px;">
                  ${this.formatDayName(day.date)}
                </div>
                <div class="weather-icon" style="font-size: 32px; margin-bottom: 8px;">
                  ${this.getWeatherIcon(day.icon)}
                </div>
                <div style="font-size: 14px;">
                  ${this.formatTemperature(day.temp_max, config.units)}
                </div>
                <div style="font-size: 12px; opacity: 0.7;">
                  ${this.formatTemperature(day.temp_min, config.units)}
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  }

  private async fetchWeatherData(config: WeatherWidget['config']): Promise<void> {
    try {
      // In a real implementation, this would call a weather API
      // For demo purposes, using mock data
      logger.debug(`[WeatherRenderer] Fetching weather for: ${config.location}`);

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Mock weather data
      this.cachedData = {
        temperature: 22,
        condition: 'Partly Cloudy',
        icon: 'partly-cloudy',
        humidity: 65,
        wind_speed: 12,
        forecast: [
          {
            date: new Date().toISOString(),
            temp_min: 18,
            temp_max: 25,
            condition: 'Sunny',
            icon: 'sunny'
          },
          {
            date: new Date(Date.now() + 86400000).toISOString(),
            temp_min: 19,
            temp_max: 24,
            condition: 'Cloudy',
            icon: 'cloudy'
          },
          {
            date: new Date(Date.now() + 172800000).toISOString(),
            temp_min: 17,
            temp_max: 22,
            condition: 'Rainy',
            icon: 'rainy'
          }
        ]
      };

      this.lastUpdate = new Date();

      // Re-render with fetched data
      if (this.container && this.currentWidget) {
        const weatherEl = this.container.querySelector('.widget-weather');
        if (weatherEl) {
          this.renderWeatherContent(weatherEl as HTMLElement, this.cachedData, config);
        }
      }

    } catch (error) {
      logger.error('[WeatherRenderer] Error fetching weather data:', error);
      if (this.container) {
        this.container.innerHTML = `
          <div style="display: flex; align-items: center; justify-content: center; height: 100%; text-align: center;">
            <div>
              <div style="font-size: 48px; margin-bottom: 10px;">⚠️</div>
              <div>Weather data unavailable</div>
            </div>
          </div>
        `;
      }
    }
  }

  private getWeatherIcon(iconCode: string): string {
    // Map weather conditions to emoji icons
    const iconMap: Record<string, string> = {
      'sunny': '☀️',
      'partly-cloudy': '⛅',
      'cloudy': '☁️',
      'rainy': '🌧️',
      'stormy': '⛈️',
      'snowy': '🌨️',
      'foggy': '🌫️',
      'windy': '💨',
      'clear-night': '🌙',
      'partly-cloudy-night': '☁️'
    };

    return iconMap[iconCode] || '❓';
  }

  private formatTemperature(temp: number, units: 'metric' | 'imperial'): string {
    if (units === 'imperial') {
      return `${Math.round(temp * 9/5 + 32)}°F`;
    }
    return `${Math.round(temp)}°C`;
  }

  private formatWindSpeed(speed: number, units: 'metric' | 'imperial'): string {
    if (units === 'imperial') {
      return `${Math.round(speed * 0.621371)} mph`;
    }
    return `${Math.round(speed)} km/h`;
  }

  private formatDayName(dateStr: string): string {
    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    } else {
      return date.toLocaleDateString('en-US', { weekday: 'short' });
    }
  }

  private isDataFresh(): boolean {
    if (!this.lastUpdate) return false;
    const now = new Date();
    const diff = now.getTime() - this.lastUpdate.getTime();
    const minutes = diff / 60000;
    return minutes < (this.currentWidget?.config.update_interval || 30);
  }

  private startUpdateInterval(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }

    const interval = (this.currentWidget?.config.update_interval || 30) * 60 * 1000; // Convert to ms

    this.updateInterval = window.setInterval(async () => {
      if (this.currentWidget) {
        await this.fetchWeatherData(this.currentWidget.config);
      }
    }, interval);

    logger.debug(`[WeatherRenderer] Update interval started (${interval}ms)`);
  }
}