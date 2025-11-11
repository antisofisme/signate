/**
 * Text Widget Renderer
 */

import { TextWidget, WidgetRenderContext, IWidgetRenderer } from '../../models/widget.model';
import { logger } from '../../logger';
import { templateProcessor } from '../template-processor';

export class TextRenderer implements IWidgetRenderer {
  private container?: HTMLElement;
  private scrollAnimation?: Animation;

  async render(widget: TextWidget, context: WidgetRenderContext): Promise<void> {
    this.container = context.container;
    
    // Clear existing content
    this.container.innerHTML = '';

    const { config } = widget;

    // Create text element
    const textEl = document.createElement('div');
    textEl.className = 'widget-text';
    
    // Apply styles
    textEl.style.cssText = `
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: ${this.getJustifyContent(config.text_align)};
      padding: 10px;
      box-sizing: border-box;
      overflow: ${config.scroll?.enabled ? 'hidden' : 'auto'};
      font-family: ${config.font_family || 'Arial, sans-serif'};
      font-size: ${config.font_size || 24}px;
      color: ${config.color || '#ffffff'};
      background-color: ${config.background_color || 'transparent'};
      text-align: ${config.text_align || 'left'};
      white-space: ${config.scroll?.enabled ? 'nowrap' : 'normal'};
      user-select: none;
    `;

    // Process template variables if enabled
    let content = config.content;
    if (config.template_variables && context.variables) {
      content = this.processTemplates(content, context.variables);
    }

    // Create text content
    const contentEl = document.createElement('div');
    contentEl.className = 'text-content';
    contentEl.innerHTML = this.sanitizeHtml(content);

    textEl.appendChild(contentEl);
    this.container.appendChild(textEl);

    // Apply scrolling if enabled
    if (config.scroll?.enabled) {
      this.applyScrolling(contentEl, config.scroll);
    }

    logger.debug(`[TextRenderer] Rendered text widget: ${widget.id}`);
  }

  async update(widget: TextWidget, context: WidgetRenderContext): Promise<void> {
    if (this.scrollAnimation) {
      this.scrollAnimation.cancel();
    }
    await this.render(widget, context);
  }

  destroy(): void {
    if (this.scrollAnimation) {
      this.scrollAnimation.cancel();
      this.scrollAnimation = undefined;
    }
    if (this.container) {
      this.container.innerHTML = '';
    }
    logger.debug('[TextRenderer] Destroyed');
  }

  private getJustifyContent(align?: string): string {
    switch (align) {
      case 'center':
        return 'center';
      case 'right':
        return 'flex-end';
      case 'left':
      default:
        return 'flex-start';
    }
  }

  private processTemplates(text: string, variables: Record<string, any>): string {
    // Use the template processor for consistent variable handling
    return templateProcessor.processTemplate(text, variables);
  }

  private sanitizeHtml(html: string): string {
    // Basic HTML sanitization - in production, use a proper sanitizer like DOMPurify
    const div = document.createElement('div');
    div.textContent = html;
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;
    
    // Remove scripts and unsafe elements
    const scripts = tempDiv.querySelectorAll('script, iframe, object, embed, link, style');
    scripts.forEach(el => el.remove());
    
    // Remove event handlers
    const allElements = tempDiv.querySelectorAll('*');
    allElements.forEach(el => {
      for (let i = el.attributes.length - 1; i >= 0; i--) {
        const attr = el.attributes[i];
        if (attr.name.startsWith('on')) {
          el.removeAttribute(attr.name);
        }
      }
    });

    return tempDiv.innerHTML;
  }

  private applyScrolling(element: HTMLElement, scroll: NonNullable<TextWidget['config']['scroll']>): void {
    const { direction, speed } = scroll;
    
    // Calculate animation distance
    const parentWidth = this.container!.offsetWidth;
    const parentHeight = this.container!.offsetHeight;
    const contentWidth = element.scrollWidth;
    const contentHeight = element.scrollHeight;

    let keyframes: Keyframe[] = [];
    let duration = 10000; // Default 10 seconds

    switch (direction) {
      case 'left':
        keyframes = [
          { transform: `translateX(${parentWidth}px)` },
          { transform: `translateX(-${contentWidth}px)` }
        ];
        duration = ((parentWidth + contentWidth) / speed) * 1000;
        break;
      
      case 'right':
        keyframes = [
          { transform: `translateX(-${contentWidth}px)` },
          { transform: `translateX(${parentWidth}px)` }
        ];
        duration = ((parentWidth + contentWidth) / speed) * 1000;
        break;
      
      case 'up':
        keyframes = [
          { transform: `translateY(${parentHeight}px)` },
          { transform: `translateY(-${contentHeight}px)` }
        ];
        duration = ((parentHeight + contentHeight) / speed) * 1000;
        element.style.whiteSpace = 'normal';
        break;
      
      case 'down':
        keyframes = [
          { transform: `translateY(-${contentHeight}px)` },
          { transform: `translateY(${parentHeight}px)` }
        ];
        duration = ((parentHeight + contentHeight) / speed) * 1000;
        element.style.whiteSpace = 'normal';
        break;
    }

    // Apply animation
    this.scrollAnimation = element.animate(keyframes, {
      duration,
      iterations: Infinity,
      easing: 'linear'
    });

    logger.debug(`[TextRenderer] Applied ${direction} scroll animation (${duration}ms)`);
  }
}