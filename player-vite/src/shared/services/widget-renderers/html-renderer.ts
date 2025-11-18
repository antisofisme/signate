/**
 * HTML/iFrame Widget Renderer
 */

import { HtmlWidget, WidgetRenderContext, IWidgetRenderer } from '@shared/models/widget.model';
import { logger } from '@shared/logger';
import { templateProcessor } from '@shared/services/template-processor';

export class HtmlRenderer implements IWidgetRenderer {
  private container?: HTMLElement;
  private iframe?: HTMLIFrameElement;
  private refreshInterval?: number;
  private currentWidget?: HtmlWidget;

  async render(widget: HtmlWidget, context: WidgetRenderContext): Promise<void> {
    this.container = context.container;
    this.currentWidget = widget;

    // Clear existing content
    this.container.innerHTML = '';

    const { config } = widget;

    if (config.url) {
      // Render as iframe for external URL
      this.renderIframe(widget, context);
    } else if (config.content) {
      // Render as HTML content
      this.renderHtmlContent(widget, context);
    } else {
      // Empty widget
      this.renderEmpty();
    }

    // Start refresh interval if specified
    if (config.refresh_interval && config.refresh_interval > 0) {
      this.startRefreshInterval(config.refresh_interval);
    }
  }

  async update(widget: HtmlWidget, context: WidgetRenderContext): Promise<void> {
    this.currentWidget = widget;
    await this.render(widget, context);
  }

  destroy(): void {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = undefined;
    }
    if (this.iframe) {
      this.iframe.src = 'about:blank';
      this.iframe = undefined;
    }
    if (this.container) {
      this.container.innerHTML = '';
    }
    logger.debug('[HtmlRenderer] Destroyed');
  }

  private renderIframe(widget: HtmlWidget, _context: WidgetRenderContext): void {
    const { config } = widget;

    this.iframe = document.createElement('iframe');
    this.iframe.src = config.url!;
    this.iframe.style.cssText = `
      width: 100%;
      height: 100%;
      border: none;
      overflow: auto;
    `;

    // Apply sandbox restrictions
    if (config.sandbox_options && config.sandbox_options.length > 0) {
      this.iframe.sandbox.value = config.sandbox_options.join(' ');
    } else {
      // Default sandbox restrictions for security
      this.iframe.sandbox.value = 'allow-scripts allow-same-origin';
    }

    // Allow interaction if specified
    if (!config.allow_interaction) {
      this.iframe.style.pointerEvents = 'none';
    }

    // Handle iframe load events
    this.iframe.addEventListener('load', () => {
      logger.debug(`[HtmlRenderer] iFrame loaded: ${config.url}`);
    });

    this.iframe.addEventListener('error', (error) => {
      logger.error(`[HtmlRenderer] iFrame error: ${config.url}`, error);
      this.renderError('Failed to load content');
    });

    this.container!.appendChild(this.iframe);
  }

  private renderHtmlContent(widget: HtmlWidget, context: WidgetRenderContext): void {
    const { config } = widget;

    // Create container for HTML content
    const contentEl = document.createElement('div');
    contentEl.className = 'widget-html-content';
    contentEl.style.cssText = `
      width: 100%;
      height: 100%;
      overflow: auto;
      padding: 10px;
      box-sizing: border-box;
    `;

    // Process template variables if context provides them
    let htmlContent = config.content || '';
    if (context.variables) {
      htmlContent = this.processTemplateVariables(htmlContent, context.variables);
    }

    // Sanitize and set HTML content
    contentEl.innerHTML = this.sanitizeHtml(htmlContent);

    // Disable interaction if specified
    if (!config.allow_interaction) {
      contentEl.style.pointerEvents = 'none';
      contentEl.style.userSelect = 'none';
    }

    // Apply theme if specified
    if (context.theme) {
      contentEl.classList.add(`theme-${context.theme}`);
    }

    this.container!.appendChild(contentEl);
    
    // Execute any inline scripts if allowed
    if (config.sandbox_options?.includes('allow-scripts')) {
      this.executeInlineScripts(contentEl);
    }
  }

  private renderEmpty(): void {
    const emptyEl = document.createElement('div');
    emptyEl.style.cssText = `
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #999;
      font-family: Arial, sans-serif;
      font-size: 14px;
    `;
    emptyEl.textContent = 'No content to display';
    this.container!.appendChild(emptyEl);
  }

  private renderError(message: string): void {
    if (!this.container) return;

    this.container.innerHTML = '';
    const errorEl = document.createElement('div');
    errorEl.style.cssText = `
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #fee;
      color: #c00;
      font-family: Arial, sans-serif;
      font-size: 14px;
      text-align: center;
      padding: 20px;
      box-sizing: border-box;
    `;
    errorEl.innerHTML = `
      <div>
        <div style="font-size: 24px; margin-bottom: 10px;">⚠️</div>
        <div>${message}</div>
      </div>
    `;
    this.container.appendChild(errorEl);
  }

  private processTemplateVariables(html: string, variables: Record<string, any>): string {
    // Use the template processor for consistent variable handling
    const processed = templateProcessor.processTemplate(html, variables);
    
    // HTML escape for security (template processor returns plain text)
    const div = document.createElement('div');
    div.textContent = processed;
    return div.innerHTML;
  }

  private sanitizeHtml(html: string): string {
    // Create a temporary container
    const temp = document.createElement('div');
    temp.innerHTML = html;

    // Remove dangerous elements
    const dangerousElements = temp.querySelectorAll(
      'script, iframe, object, embed, link[rel="import"], meta, base'
    );
    dangerousElements.forEach(el => el.remove());

    // Remove dangerous attributes
    const allElements = temp.querySelectorAll('*');
    allElements.forEach(el => {
      // Remove event handlers
      Array.from(el.attributes).forEach(attr => {
        if (attr.name.startsWith('on') || 
            attr.name === 'srcdoc' ||
            attr.value.includes('javascript:')) {
          el.removeAttribute(attr.name);
        }
      });

      // Remove dangerous style properties
      if (el.hasAttribute('style')) {
        const style = el.getAttribute('style') || '';
        if (style.includes('expression') || 
            style.includes('javascript:') ||
            style.includes('behavior:')) {
          el.removeAttribute('style');
        }
      }
    });

    // Remove form elements if interaction is not allowed
    if (!this.currentWidget?.config.allow_interaction) {
      const formElements = temp.querySelectorAll(
        'form, input, textarea, select, button'
      );
      formElements.forEach(el => el.remove());
    }

    return temp.innerHTML;
  }

  private executeInlineScripts(container: HTMLElement): void {
    // Find all script elements
    const scripts = container.querySelectorAll('script');
    
    scripts.forEach(script => {
      try {
        // Create new script element to execute
        const newScript = document.createElement('script');
        
        if (script.src) {
          // External script
          newScript.src = script.src;
        } else {
          // Inline script - wrap in function to isolate scope
          newScript.textContent = `
            (function() {
              'use strict';
              try {
                ${script.textContent}
              } catch (error) {
                console.error('[HtmlWidget] Script error:', error);
              }
            })();
          `;
        }

        // Replace old script with new one
        script.parentNode?.replaceChild(newScript, script);
      } catch (error) {
        logger.error('[HtmlRenderer] Error executing script:', error);
      }
    });
  }

  private startRefreshInterval(seconds: number): void {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }

    const interval = seconds * 1000;

    this.refreshInterval = window.setInterval(() => {
      if (!this.currentWidget || !this.container) return;

      logger.debug('[HtmlRenderer] Refreshing content...');

      if (this.iframe && this.currentWidget.config.url) {
        // Reload iframe
        this.iframe.src = this.currentWidget.config.url;
      } else if (this.currentWidget.config.content) {
        // Re-render HTML content
        this.renderHtmlContent(this.currentWidget, { 
          container: this.container,
          variables: {}, // TODO: Get fresh variables
          theme: 'light'
        });
      }
    }, interval);

    logger.debug(`[HtmlRenderer] Refresh interval started (${interval}ms)`);
  }
}