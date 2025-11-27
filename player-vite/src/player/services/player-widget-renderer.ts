/**
 * Player Widget Renderer
 * Integrates widget rendering with the HLS player
 */

import { Widget } from '@shared/models';
import { widgetRenderer } from '@shared/services/widget-renderer';
import { logger } from '@shared/logger';
import { SharedEventBus as eventBus } from '@shared/events/shared-event-bus';
import { templateProcessor } from '@shared/services/template-processor';
import { SharedDeviceState } from '@shared/device';

export class PlayerWidgetRenderer {
  private widgetContainer?: HTMLElement;
  private currentWidgets: Map<string, Widget> = new Map();
  private isActive = false;

  constructor() {
    logger.info('[PlayerWidgetRenderer] Service initialized');
    this.setupEventListeners();
  }

  /**
   * Initialize widget container in the player
   */
  initialize(playerContainer: HTMLElement): void {
    // Create widget overlay container
    this.widgetContainer = document.createElement('div');
    this.widgetContainer.id = 'widget-overlay';
    this.widgetContainer.style.cssText = `
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 10;
    `;

    // Add custom styles for widgets
    this.injectWidgetStyles();

    playerContainer.style.position = 'relative';
    playerContainer.appendChild(this.widgetContainer);

    // Initialize template processor with device ID
    const deviceId = SharedDeviceState.getDeviceId();
    if (deviceId) {
      // Initialize template processor
      templateProcessor.initialize(deviceId).catch(error => {
        logger.error('[PlayerWidgetRenderer] Failed to initialize template processor:', error);
      });
    }

    logger.info('[PlayerWidgetRenderer] Widget container initialized');
  }

  /**
   * Render widgets for content
   */
  async renderWidgets(content: any): Promise<void> {
    try {
      // Check if content has widgets
      if (content.type !== 'widget' || !content.widget_data) {
        this.clearWidgets();
        return;
      }

      logger.debug(`[PlayerWidgetRenderer] Rendering widgets for content: ${content.id}`);

      // Parse widget data
      const widgetData = typeof content.widget_data === 'string' 
        ? JSON.parse(content.widget_data) 
        : content.widget_data;

      // Handle single widget or array of widgets
      const widgets = Array.isArray(widgetData) ? widgetData : [widgetData];

      // Clear existing widgets
      this.clearWidgets();

      // Render each widget
      for (const widget of widgets) {
        await this.renderWidget(widget);
      }

      this.isActive = true;
      logger.info(`[PlayerWidgetRenderer] Rendered ${widgets.length} widgets`);

    } catch (error) {
      logger.error('[PlayerWidgetRenderer] Error rendering widgets:', error);
      this.clearWidgets();
    }
  }

  /**
   * Render a single widget
   */
  private async renderWidget(widget: Widget): Promise<void> {
    if (!this.widgetContainer) {
      logger.warn('[PlayerWidgetRenderer] Widget container not initialized');
      return;
    }

    try {
      // Create container for this widget
      const container = document.createElement('div');
      container.id = `widget-${widget.id}`;
      container.className = 'player-widget';
      container.style.pointerEvents = 'auto'; // Allow interaction for interactive widgets

      this.widgetContainer.appendChild(container);

      // Get template variables from player context
      const variables = await this.getTemplateVariables();

      // Render the widget
      await widgetRenderer.renderWidget(widget, {
        container,
        variables,
        locale: this.getLocale(),
        theme: this.getTheme(),
      });

      // Store widget reference
      this.currentWidgets.set(widget.id, widget);

      logger.debug(`[PlayerWidgetRenderer] Widget rendered: ${widget.id} (${widget.type})`);

    } catch (error) {
      logger.error(`[PlayerWidgetRenderer] Error rendering widget ${widget.id}:`, error);
    }
  }

  /**
   * Update all widgets
   */
  async updateWidgets(): Promise<void> {
    if (!this.isActive || !this.widgetContainer) return;

    const variables = await this.getTemplateVariables();

    for (const [widgetId, widget] of this.currentWidgets) {
      const container = this.widgetContainer.querySelector(`#widget-${widgetId}`);
      if (container) {
        await widgetRenderer.updateWidget(widget, {
          container: container as HTMLElement,
          variables,
          locale: this.getLocale(),
          theme: this.getTheme(),
        });
      }
    }
  }

  /**
   * Clear all widgets
   */
  clearWidgets(): void {
    if (!this.widgetContainer) return;

    // Destroy all widget renderers
    this.currentWidgets.forEach((_widget, widgetId) => {
      widgetRenderer.destroyWidget(widgetId);
    });

    // Clear the container
    this.widgetContainer.innerHTML = '';
    this.currentWidgets.clear();
    this.isActive = false;

    logger.debug('[PlayerWidgetRenderer] All widgets cleared');
  }

  /**
   * Get template variables from various sources
   */
  private async getTemplateVariables(): Promise<Record<string, any>> {
    try {
      // Get all variables from template processor
      return templateProcessor.getAllVariables();
    } catch (error) {
      logger.error('[PlayerWidgetRenderer] Error getting template variables:', error);
      return {};
    }
  }


  /**
   * Get current locale
   */
  private getLocale(): string {
    return 'en-US';
  }

  /**
   * Get current theme
   */
  private getTheme(): 'light' | 'dark' {
    // Check if dark mode is preferred
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  }

  /**
   * Setup event listeners
   */
  private setupEventListeners(): void {
    // Listen for widget update events
    eventBus.on('widgets:update', () => {
      this.updateWidgets();
    });

    // Listen for template variable changes
    eventBus.on('variables:changed', () => {
      this.updateWidgets();
    });

    // Update time-based widgets every second
    setInterval(() => {
      if (this.isActive) {
        // Only update time-sensitive widgets
        this.currentWidgets.forEach(() => {
          // Clock and text widgets are handled by their own intervals
        });
      }
    }, 1000);
  }

  /**
   * Inject widget styles
   */
  private injectWidgetStyles(): void {
    const style = document.createElement('style');
    style.textContent = `
      .player-widget {
        position: absolute;
        overflow: hidden;
      }

      .widget-clock.digital {
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
      }

      .widget-weather {
        backdrop-filter: blur(10px);
      }

      .widget-text {
        text-shadow: 0 1px 3px rgba(0,0,0,0.3);
      }

      .widget-calendar {
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      }

      /* Responsive adjustments */
      @media (max-width: 768px) {
        .player-widget {
          transform: scale(0.8);
          transform-origin: top left;
        }
      }

      /* Animation classes */
      .widget-fade-in {
        animation: widgetFadeIn 0.3s ease-out;
      }

      .widget-fade-out {
        animation: widgetFadeOut 0.3s ease-out;
      }

      @keyframes widgetFadeIn {
        from {
          opacity: 0;
          transform: translateY(10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      @keyframes widgetFadeOut {
        from {
          opacity: 1;
          transform: translateY(0);
        }
        to {
          opacity: 0;
          transform: translateY(-10px);
        }
      }
    `;

    document.head.appendChild(style);
  }

  /**
   * Destroy the widget renderer
   */
  destroy(): void {
    this.clearWidgets();
    
    if (this.widgetContainer) {
      this.widgetContainer.remove();
      this.widgetContainer = undefined;
    }

    logger.info('[PlayerWidgetRenderer] Service destroyed');
  }
}

// Export singleton instance
export const playerWidgetRenderer = new PlayerWidgetRenderer();