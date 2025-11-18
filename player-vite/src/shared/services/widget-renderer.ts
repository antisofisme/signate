/**
 * Widget Renderer Service
 * Manages rendering of different widget types
 */

import {
  Widget,
  WidgetType,
  WidgetRenderContext,
  IWidgetRenderer,
} from '@shared/models/widget.model';
import { ClockRenderer } from './widget-renderers/clock-renderer';
import { WeatherRenderer } from './widget-renderers/weather-renderer';
import { TextRenderer } from './widget-renderers/text-renderer';
import { CalendarRenderer } from './widget-renderers/calendar-renderer';
import { HtmlRenderer } from './widget-renderers/html-renderer';
import { logger } from '@shared/logger';

export class WidgetRendererService {
  private renderers: Map<string, IWidgetRenderer> = new Map();
  private renderInterval?: number;

  constructor() {
    logger.info('[WidgetRenderer] Service initialized');
  }

  /**
   * Render a widget to the specified container
   */
  async renderWidget(widget: Widget, context: WidgetRenderContext): Promise<void> {
    try {
      logger.debug(`[WidgetRenderer] Rendering widget: ${widget.id} (${widget.type})`);

      // Get or create renderer for this widget
      const renderer = await this.getRenderer(widget);
      
      // Apply common widget properties
      this.applyWidgetStyles(widget, context.container);
      
      // Render the widget
      await renderer.render(widget, context);

      logger.info(`[WidgetRenderer] Widget rendered successfully: ${widget.id}`);
    } catch (error) {
      logger.error(`[WidgetRenderer] Error rendering widget ${widget.id}:`, error);
      throw error;
    }
  }

  /**
   * Update a widget with new data
   */
  async updateWidget(widget: Widget, context: WidgetRenderContext): Promise<void> {
    try {
      const renderer = this.renderers.get(widget.id);
      if (!renderer) {
        // Widget not rendered yet, render it
        await this.renderWidget(widget, context);
        return;
      }

      await renderer.update(widget, context);
    } catch (error) {
      logger.error(`[WidgetRenderer] Error updating widget ${widget.id}:`, error);
      throw error;
    }
  }

  /**
   * Destroy a widget and clean up resources
   */
  destroyWidget(widgetId: string): void {
    try {
      const renderer = this.renderers.get(widgetId);
      if (renderer) {
        renderer.destroy();
        this.renderers.delete(widgetId);
        logger.debug(`[WidgetRenderer] Widget destroyed: ${widgetId}`);
      }
    } catch (error) {
      logger.error(`[WidgetRenderer] Error destroying widget ${widgetId}:`, error);
    }
  }

  /**
   * Destroy all widgets
   */
  destroyAll(): void {
    this.renderers.forEach((renderer) => {
      try {
        renderer.destroy();
      } catch (error) {
        logger.error(`[WidgetRenderer] Error destroying widget:`, error);
      }
    });
    this.renderers.clear();

    if (this.renderInterval) {
      clearInterval(this.renderInterval);
      this.renderInterval = undefined;
    }

    logger.info('[WidgetRenderer] All widgets destroyed');
  }

  /**
   * Get or create appropriate renderer for widget type
   */
  private async getRenderer(widget: Widget): Promise<IWidgetRenderer> {
    let renderer = this.renderers.get(widget.id);
    
    if (!renderer) {
      renderer = this.createRenderer(widget);
      this.renderers.set(widget.id, renderer);
    }

    return renderer;
  }

  /**
   * Create renderer based on widget type
   */
  private createRenderer(widget: Widget): IWidgetRenderer {
    switch (widget.type) {
      case WidgetType.CLOCK:
        return new ClockRenderer();
      
      case WidgetType.WEATHER:
        return new WeatherRenderer();
      
      case WidgetType.TEXT:
        return new TextRenderer();
      
      case WidgetType.CALENDAR:
        return new CalendarRenderer();
      
      case WidgetType.HTML:
        return new HtmlRenderer();
      
      default:
        throw new Error(`Unknown widget type: ${(widget as any).type}`);
    }
  }

  /**
   * Apply common widget styles (position, visibility, etc.)
   */
  private applyWidgetStyles(widget: Widget, container: HTMLElement): void {
    const { position, is_visible } = widget;

    // Set container styles
    container.style.position = 'absolute';
    container.style.left = `${position.x}px`;
    container.style.top = `${position.y}px`;
    container.style.width = `${position.width}px`;
    container.style.height = `${position.height}px`;
    container.style.zIndex = position.z_index?.toString() || '1';
    container.style.display = is_visible ? 'block' : 'none';

    // Apply animation if specified
    if (widget.animation && widget.animation.type !== 'none') {
      container.style.transition = `all ${widget.animation.duration}ms ease-in-out`;
      
      if (widget.animation.type === 'fade') {
        container.style.opacity = is_visible ? '1' : '0';
      }
    }

    // Set widget ID for debugging
    container.setAttribute('data-widget-id', widget.id);
    container.setAttribute('data-widget-type', widget.type);
  }

  /**
   * Start auto-update interval for time-based widgets
   */
  startAutoUpdate(interval: number = 1000): void {
    if (this.renderInterval) {
      clearInterval(this.renderInterval);
    }

    this.renderInterval = window.setInterval(() => {
      // Update time-based widgets (clock, weather, etc.)
      this.renderers.forEach((renderer) => {
        if (renderer.constructor.name === 'ClockRenderer') {
          // Clock renderer has its own interval, skip
          return;
        }
      });
    }, interval);
  }
}

// Export singleton instance
export const widgetRenderer = new WidgetRendererService();