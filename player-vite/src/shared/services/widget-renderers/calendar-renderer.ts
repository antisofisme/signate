/**
 * Calendar Widget Renderer
 */

import { CalendarWidget, WidgetRenderContext, IWidgetRenderer } from '../../models/widget.model';
import { logger } from '../../logger';

interface CalendarEvent {
  title: string;
  start: Date;
  end: Date;
  allDay?: boolean;
  location?: string;
}

export class CalendarRenderer implements IWidgetRenderer {
  private container?: HTMLElement;
  private updateInterval?: number;
  private currentWidget?: CalendarWidget;
  private events: CalendarEvent[] = [];

  async render(widget: CalendarWidget, context: WidgetRenderContext): Promise<void> {
    this.container = context.container;
    this.currentWidget = widget;

    // Clear existing content
    this.container.innerHTML = '';

    const { config } = widget;

    // Create calendar container
    const calendarEl = document.createElement('div');
    calendarEl.className = `widget-calendar ${config.theme}`;
    calendarEl.style.cssText = `
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      background: ${config.theme === 'dark' ? '#1a1a1a' : '#ffffff'};
      color: ${config.theme === 'dark' ? '#ffffff' : '#000000'};
      font-family: 'Segoe UI', Arial, sans-serif;
      border-radius: 8px;
      overflow: hidden;
    `;

    // Render based on view type
    switch (config.view) {
      case 'month':
        this.renderMonthView(calendarEl, config);
        break;
      case 'week':
        this.renderWeekView(calendarEl, config);
        break;
      case 'day':
        this.renderDayView(calendarEl, config);
        break;
    }

    this.container.appendChild(calendarEl);

    // Load events if URL provided
    if (config.calendar_url && config.show_events) {
      await this.loadEvents(config.calendar_url);
    }

    // Start update interval
    this.startUpdateInterval();
  }

  async update(widget: CalendarWidget, context: WidgetRenderContext): Promise<void> {
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
    logger.debug('[CalendarRenderer] Destroyed');
  }

  private renderMonthView(container: HTMLElement, config: CalendarWidget['config']): void {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = now.getDate();

    // Header
    const header = document.createElement('div');
    header.style.cssText = `
      padding: 15px;
      text-align: center;
      font-size: 20px;
      font-weight: 500;
      border-bottom: 1px solid ${config.theme === 'dark' ? '#333' : '#e0e0e0'};
    `;
    header.textContent = new Date(year, month).toLocaleDateString('en-US', { 
      month: 'long', 
      year: 'numeric' 
    });
    container.appendChild(header);

    // Calendar grid
    const grid = document.createElement('div');
    grid.style.cssText = `
      flex: 1;
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      gap: 1px;
      background: ${config.theme === 'dark' ? '#333' : '#e0e0e0'};
      padding: 1px;
    `;

    // Day headers
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    dayNames.forEach(day => {
      const dayHeader = document.createElement('div');
      dayHeader.style.cssText = `
        padding: 10px 5px;
        text-align: center;
        font-size: 12px;
        font-weight: 500;
        background: ${config.theme === 'dark' ? '#1a1a1a' : '#f5f5f5'};
      `;
      dayHeader.textContent = day;
      grid.appendChild(dayHeader);
    });

    // Empty cells before first day
    for (let i = 0; i < firstDay; i++) {
      const emptyCell = document.createElement('div');
      emptyCell.style.background = config.theme === 'dark' ? '#1a1a1a' : '#ffffff';
      grid.appendChild(emptyCell);
    }

    // Calendar days
    for (let day = 1; day <= daysInMonth; day++) {
      const dayCell = document.createElement('div');
      const isToday = day === today;
      
      dayCell.style.cssText = `
        padding: 10px;
        text-align: center;
        background: ${config.theme === 'dark' ? '#1a1a1a' : '#ffffff'};
        cursor: pointer;
        position: relative;
        min-height: 40px;
        ${isToday && config.highlight_today ? `
          background: ${config.theme === 'dark' ? '#0066cc' : '#e3f2fd'};
          color: ${config.theme === 'dark' ? '#ffffff' : '#0066cc'};
          font-weight: bold;
        ` : ''}
      `;

      // Day number
      const dayNumber = document.createElement('div');
      dayNumber.style.fontSize = '14px';
      dayNumber.textContent = day.toString();
      dayCell.appendChild(dayNumber);

      // Add events if any
      const dayEvents = this.getEventsForDay(new Date(year, month, day));
      if (dayEvents.length > 0 && config.show_events) {
        const eventDot = document.createElement('div');
        eventDot.style.cssText = `
          width: 6px;
          height: 6px;
          background: #ff4444;
          border-radius: 50%;
          margin: 4px auto 0;
        `;
        dayCell.appendChild(eventDot);
      }

      grid.appendChild(dayCell);
    }

    container.appendChild(grid);

    // Week numbers
    if (config.show_week_numbers) {
      this.addWeekNumbers(grid, year, month);
    }
  }

  private renderWeekView(container: HTMLElement, config: CalendarWidget['config']): void {
    const now = new Date();
    const weekStart = new Date(now);
    weekStart.setDate(now.getDate() - now.getDay());

    // Header
    const header = document.createElement('div');
    header.style.cssText = `
      padding: 15px;
      text-align: center;
      font-size: 18px;
      border-bottom: 1px solid ${config.theme === 'dark' ? '#333' : '#e0e0e0'};
    `;
    header.textContent = `Week of ${weekStart.toLocaleDateString()}`;
    container.appendChild(header);

    // Days container
    const daysContainer = document.createElement('div');
    daysContainer.style.cssText = `
      flex: 1;
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      gap: 10px;
      padding: 10px;
    `;

    for (let i = 0; i < 7; i++) {
      const date = new Date(weekStart);
      date.setDate(weekStart.getDate() + i);
      
      const dayCol = document.createElement('div');
      dayCol.style.cssText = `
        border-right: 1px solid ${config.theme === 'dark' ? '#333' : '#e0e0e0'};
        padding: 10px;
      `;

      const dayHeader = document.createElement('div');
      dayHeader.style.cssText = `
        text-align: center;
        font-weight: 500;
        margin-bottom: 10px;
        ${date.toDateString() === now.toDateString() && config.highlight_today ? 
          `color: ${config.theme === 'dark' ? '#4da6ff' : '#0066cc'};` : ''}
      `;
      dayHeader.innerHTML = `
        <div style="font-size: 12px;">${date.toLocaleDateString('en-US', { weekday: 'short' })}</div>
        <div style="font-size: 16px;">${date.getDate()}</div>
      `;
      dayCol.appendChild(dayHeader);

      // Events for this day
      if (config.show_events) {
        const events = this.getEventsForDay(date);
        const eventsList = document.createElement('div');
        eventsList.style.cssText = 'font-size: 12px;';
        
        events.forEach(event => {
          const eventEl = document.createElement('div');
          eventEl.style.cssText = `
            padding: 4px;
            margin: 2px 0;
            background: ${config.theme === 'dark' ? '#333' : '#f0f0f0'};
            border-radius: 4px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          `;
          eventEl.textContent = `${this.formatEventTime(event)} ${event.title}`;
          eventsList.appendChild(eventEl);
        });
        
        dayCol.appendChild(eventsList);
      }

      daysContainer.appendChild(dayCol);
    }

    container.appendChild(daysContainer);
  }

  private renderDayView(container: HTMLElement, config: CalendarWidget['config']): void {
    const now = new Date();

    // Header
    const header = document.createElement('div');
    header.style.cssText = `
      padding: 15px;
      text-align: center;
      font-size: 20px;
      font-weight: 500;
      border-bottom: 1px solid ${config.theme === 'dark' ? '#333' : '#e0e0e0'};
    `;
    header.textContent = now.toLocaleDateString('en-US', { 
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
    container.appendChild(header);

    // Time slots
    const timeSlots = document.createElement('div');
    timeSlots.style.cssText = `
      flex: 1;
      overflow-y: auto;
      padding: 10px;
    `;

    // Generate hourly slots
    for (let hour = 0; hour < 24; hour++) {
      const slot = document.createElement('div');
      slot.style.cssText = `
        display: grid;
        grid-template-columns: 60px 1fr;
        gap: 10px;
        padding: 10px 0;
        border-bottom: 1px solid ${config.theme === 'dark' ? '#333' : '#f0f0f0'};
      `;

      const timeLabel = document.createElement('div');
      timeLabel.style.cssText = `
        font-size: 12px;
        color: ${config.theme === 'dark' ? '#999' : '#666'};
        text-align: right;
      `;
      timeLabel.textContent = `${hour.toString().padStart(2, '0')}:00`;
      slot.appendChild(timeLabel);

      const events = document.createElement('div');
      
      if (config.show_events) {
        const hourEvents = this.getEventsForHour(now, hour);
        hourEvents.forEach(event => {
          const eventEl = document.createElement('div');
          eventEl.style.cssText = `
            padding: 8px;
            margin: 2px 0;
            background: ${config.theme === 'dark' ? '#0066cc' : '#e3f2fd'};
            border-radius: 4px;
            font-size: 13px;
          `;
          eventEl.innerHTML = `
            <div style="font-weight: 500;">${event.title}</div>
            ${event.location ? `<div style="font-size: 11px; opacity: 0.7;">${event.location}</div>` : ''}
          `;
          events.appendChild(eventEl);
        });
      }

      slot.appendChild(events);
      timeSlots.appendChild(slot);
    }

    container.appendChild(timeSlots);
  }

  private async loadEvents(calendarUrl: string): Promise<void> {
    try {
      // In production, this would fetch and parse iCal data
      logger.debug(`[CalendarRenderer] Loading calendar events from: ${calendarUrl}`);
      
      // Mock events for demo
      this.events = [
        {
          title: 'Team Meeting',
          start: new Date(),
          end: new Date(Date.now() + 3600000),
          location: 'Conference Room A'
        },
        {
          title: 'Project Deadline',
          start: new Date(Date.now() + 86400000),
          end: new Date(Date.now() + 90000000),
          allDay: true
        }
      ];
    } catch (error) {
      logger.error('[CalendarRenderer] Error loading calendar events:', error);
    }
  }

  private getEventsForDay(date: Date): CalendarEvent[] {
    return this.events.filter(event => {
      const eventDate = new Date(event.start);
      return eventDate.toDateString() === date.toDateString();
    });
  }

  private getEventsForHour(date: Date, hour: number): CalendarEvent[] {
    return this.events.filter(event => {
      const eventDate = new Date(event.start);
      return eventDate.toDateString() === date.toDateString() && 
             eventDate.getHours() === hour;
    });
  }

  private formatEventTime(event: CalendarEvent): string {
    if (event.allDay) return 'All day';
    return event.start.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
  }

  private addWeekNumbers(_grid: HTMLElement, _year: number, _month: number): void {
    // Implementation for week numbers
    // This would require more complex calculation
    logger.debug('[CalendarRenderer] Week numbers not implemented yet');
  }

  private startUpdateInterval(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
    }

    // Update every minute to keep current time accurate
    this.updateInterval = window.setInterval(() => {
      if (this.container && this.currentWidget) {
        // Re-render to update current day highlight
        const calendarEl = this.container.querySelector('.widget-calendar');
        if (calendarEl) {
          const newCalendarEl = document.createElement('div');
          newCalendarEl.className = calendarEl.className;
          newCalendarEl.style.cssText = (calendarEl as HTMLElement).style.cssText;
          
          switch (this.currentWidget.config.view) {
            case 'month':
              this.renderMonthView(newCalendarEl, this.currentWidget.config);
              break;
            case 'week':
              this.renderWeekView(newCalendarEl, this.currentWidget.config);
              break;
            case 'day':
              this.renderDayView(newCalendarEl, this.currentWidget.config);
              break;
          }
          
          calendarEl.replaceWith(newCalendarEl);
        }
      }
    }, 60000); // Update every minute

    logger.debug('[CalendarRenderer] Update interval started (60s)');
  }
}