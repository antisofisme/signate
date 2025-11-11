/**
 * Clock Widget Renderer
 */

import { ClockWidget, WidgetRenderContext, IWidgetRenderer } from '../../models/widget.model';
import { logger } from '../../logger';
import { i18n } from '../i18n';

export class ClockRenderer implements IWidgetRenderer {
  private container?: HTMLElement;
  private updateInterval?: number;
  private currentWidget?: ClockWidget;

  async render(widget: ClockWidget, context: WidgetRenderContext): Promise<void> {
    this.container = context.container;
    this.currentWidget = widget;

    // Clear existing content
    this.container.innerHTML = '';

    const { config } = widget;

    if (config.style === 'digital') {
      await this.renderDigitalClock(widget, context);
    } else {
      await this.renderAnalogClock(widget, context);
    }

    // Start update interval
    this.startUpdateInterval();
  }

  async update(widget: ClockWidget, context: WidgetRenderContext): Promise<void> {
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
    logger.debug('[ClockRenderer] Destroyed');
  }

  private async renderDigitalClock(widget: ClockWidget, _context: WidgetRenderContext): Promise<void> {
    const { config } = widget;

    // Create clock element
    const clockEl = document.createElement('div');
    clockEl.className = 'widget-clock digital';
    clockEl.style.cssText = `
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Segoe UI', system-ui, sans-serif;
      font-size: ${config.font_size || 48}px;
      color: ${config.color || '#ffffff'};
      font-weight: 300;
      font-variant-numeric: tabular-nums;
      user-select: none;
    `;

    // Initial time display
    this.updateDigitalClock(clockEl, config);

    this.container!.appendChild(clockEl);
  }

  private async renderAnalogClock(widget: ClockWidget, _context: WidgetRenderContext): Promise<void> {
    const { config } = widget;
    const size = Math.min(widget.position.width, widget.position.height);

    // Create SVG for analog clock
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 200 200');
    svg.setAttribute('width', size.toString());
    svg.setAttribute('height', size.toString());
    svg.style.cssText = `
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
    `;

    // Clock face
    const face = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    face.setAttribute('cx', '100');
    face.setAttribute('cy', '100');
    face.setAttribute('r', '95');
    face.setAttribute('fill', 'none');
    face.setAttribute('stroke', config.color || '#ffffff');
    face.setAttribute('stroke-width', '2');
    svg.appendChild(face);

    // Hour marks
    for (let i = 0; i < 12; i++) {
      const angle = (i * 30 - 90) * (Math.PI / 180);
      const x1 = 100 + 85 * Math.cos(angle);
      const y1 = 100 + 85 * Math.sin(angle);
      const x2 = 100 + 75 * Math.cos(angle);
      const y2 = 100 + 75 * Math.sin(angle);

      const mark = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      mark.setAttribute('x1', x1.toString());
      mark.setAttribute('y1', y1.toString());
      mark.setAttribute('x2', x2.toString());
      mark.setAttribute('y2', y2.toString());
      mark.setAttribute('stroke', config.color || '#ffffff');
      mark.setAttribute('stroke-width', i % 3 === 0 ? '3' : '1');
      svg.appendChild(mark);
    }

    // Clock hands
    const hourHand = this.createClockHand(50, 6, config.color || '#ffffff');
    hourHand.setAttribute('id', 'hour-hand');
    svg.appendChild(hourHand);

    const minuteHand = this.createClockHand(70, 4, config.color || '#ffffff');
    minuteHand.setAttribute('id', 'minute-hand');
    svg.appendChild(minuteHand);

    if (config.show_seconds) {
      const secondHand = this.createClockHand(80, 2, '#ff0000');
      secondHand.setAttribute('id', 'second-hand');
      svg.appendChild(secondHand);
    }

    // Center dot
    const center = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    center.setAttribute('cx', '100');
    center.setAttribute('cy', '100');
    center.setAttribute('r', '5');
    center.setAttribute('fill', config.color || '#ffffff');
    svg.appendChild(center);

    this.container!.appendChild(svg);

    // Initial position
    this.updateAnalogClock(svg, config);
  }

  private createClockHand(length: number, width: number, color: string): SVGLineElement {
    const hand = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    hand.setAttribute('x1', '100');
    hand.setAttribute('y1', '100');
    hand.setAttribute('x2', '100');
    hand.setAttribute('y2', (100 - length).toString());
    hand.setAttribute('stroke', color);
    hand.setAttribute('stroke-width', width.toString());
    hand.setAttribute('stroke-linecap', 'round');
    hand.style.transformOrigin = '100px 100px';
    hand.style.transition = 'transform 0.5s cubic-bezier(0.4, 0.0, 0.2, 1)';
    return hand;
  }

  private updateDigitalClock(element: HTMLElement, config: ClockWidget['config']): void {
    const now = this.getTime(config.timezone);
    
    // Use i18n for time formatting based on locale
    const locale = i18n.getLocale();
    const options: Intl.DateTimeFormatOptions = {
      hour: '2-digit',
      minute: '2-digit',
      hour12: config.format === '12h'
    };
    
    if (config.show_seconds) {
      options.second = '2-digit';
    }
    
    // Add timezone if specified
    if (config.timezone) {
      options.timeZone = config.timezone;
    }
    
    const timeString = now.toLocaleTimeString(locale, options);
    element.textContent = timeString;
  }

  private updateAnalogClock(svg: SVGElement, config: ClockWidget['config']): void {
    const now = this.getTime(config.timezone);
    
    const hours = now.getHours() % 12;
    const minutes = now.getMinutes();
    const seconds = now.getSeconds();

    const hourAngle = (hours + minutes / 60) * 30 - 90;
    const minuteAngle = (minutes + seconds / 60) * 6 - 90;
    const secondAngle = seconds * 6 - 90;

    const hourHand = svg.querySelector('#hour-hand');
    const minuteHand = svg.querySelector('#minute-hand');
    const secondHand = svg.querySelector('#second-hand');

    if (hourHand) {
      (hourHand as any).style.transform = `rotate(${hourAngle}deg)`;
    }
    if (minuteHand) {
      (minuteHand as any).style.transform = `rotate(${minuteAngle}deg)`;
    }
    if (secondHand && config.show_seconds) {
      (secondHand as any).style.transform = `rotate(${secondAngle}deg)`;
    }
  }

  private getTime(timezone?: string): Date {
    if (!timezone) {
      return new Date();
    }

    try {
      const formatter = new Intl.DateTimeFormat('en-US', {
        timeZone: timezone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
      });

      const parts = formatter.formatToParts(new Date());
      const dateParts: Record<string, string> = {};
      
      parts.forEach(part => {
        dateParts[part.type] = part.value;
      });

      return new Date(
        `${dateParts.year}-${dateParts.month}-${dateParts.day}T${dateParts.hour}:${dateParts.minute}:${dateParts.second}`
      );
    } catch (error) {
      logger.warn(`[ClockRenderer] Invalid timezone: ${timezone}`, error);
      return new Date();
    }
  }

  private startUpdateInterval(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }

    const updateFrequency = this.currentWidget?.config.show_seconds ? 1000 : 60000;

    this.updateInterval = window.setInterval(() => {
      if (!this.container || !this.currentWidget) return;

      if (this.currentWidget.config.style === 'digital') {
        const clockEl = this.container.querySelector('.widget-clock');
        if (clockEl) {
          this.updateDigitalClock(clockEl as HTMLElement, this.currentWidget.config);
        }
      } else {
        const svg = this.container.querySelector('svg');
        if (svg) {
          this.updateAnalogClock(svg, this.currentWidget.config);
        }
      }
    }, updateFrequency);

    logger.debug(`[ClockRenderer] Update interval started (${updateFrequency}ms)`);
  }
}