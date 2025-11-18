/**
 * Schedule Info Component
 * Displays current active schedule information
 */

import { playerScheduleManager } from '@player/services/player-schedule-manager';
import { i18n } from '@shared/services/i18n';
import { SharedLogger } from '@shared/logger';
import { SharedEventBus } from '@shared/events/shared-event-bus';

export class ScheduleInfo {
  private container?: HTMLElement;
  private isVisible = false;

  /**
   * Initialize schedule info component
   */
  initialize(playerContainer: HTMLElement): void {
    // Create container
    this.container = document.createElement('div');
    this.container.id = 'schedule-info';
    this.container.className = 'schedule-info';
    this.container.style.cssText = `
      position: absolute;
      top: 10px;
      left: 10px;
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 10px 15px;
      border-radius: 8px;
      font-family: 'Segoe UI', system-ui, sans-serif;
      font-size: 14px;
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      display: none;
      z-index: 100;
      max-width: 300px;
    `;

    playerContainer.appendChild(this.container);

    // Listen for schedule changes
    SharedEventBus.on('schedule:changed', () => {
      this.update();
    });

    // Update periodically
    setInterval(() => {
      if (this.isVisible) {
        this.update();
      }
    }, 60000); // Update every minute

    SharedLogger.debug('[ScheduleInfo] Initialized');
  }

  /**
   * Update schedule info display
   */
  update(): void {
    if (!this.container) return;

    const schedule = playerScheduleManager.getCurrentSchedule();
    
    if (!schedule) {
      this.container.innerHTML = `
        <div class="schedule-status">
          <strong>${i18n.t('schedule.no_active', 'No Active Schedule')}</strong>
        </div>
      `;
      return;
    }

    const now = new Date();
    const currentTime = now.toLocaleTimeString(i18n.getLocale(), { 
      hour: '2-digit', 
      minute: '2-digit' 
    });

    this.container.innerHTML = `
      <div class="schedule-status">
        <div style="margin-bottom: 8px;">
          <strong>${i18n.t('schedule.active', 'Active Schedule')}</strong>
        </div>
        <div style="opacity: 0.9; font-size: 13px;">
          <div>${schedule.name}</div>
          <div style="margin-top: 4px; opacity: 0.7;">
            ${schedule.start_time} - ${schedule.end_time}
          </div>
          <div style="margin-top: 4px; opacity: 0.7;">
            ${this.getRecurrenceText(schedule.recurrence_type)}
          </div>
          <div style="margin-top: 6px; font-size: 12px; opacity: 0.6;">
            ${i18n.t('schedule.current_time', 'Current time')}: ${currentTime}
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Get recurrence text
   */
  private getRecurrenceText(type: string): string {
    const translations: Record<string, string> = {
      'once': i18n.t('schedule.once', 'One time'),
      'daily': i18n.t('schedule.daily', 'Daily'),
      'weekly': i18n.t('schedule.weekly', 'Weekly'),
      'monthly': i18n.t('schedule.monthly', 'Monthly'),
      'yearly': i18n.t('schedule.yearly', 'Yearly'),
    };

    return translations[type] || type;
  }

  /**
   * Show schedule info
   */
  show(): void {
    if (this.container) {
      this.container.style.display = 'block';
      this.isVisible = true;
      this.update();
    }
  }

  /**
   * Hide schedule info
   */
  hide(): void {
    if (this.container) {
      this.container.style.display = 'none';
      this.isVisible = false;
    }
  }

  /**
   * Toggle visibility
   */
  toggle(): void {
    if (this.isVisible) {
      this.hide();
    } else {
      this.show();
    }
  }

  /**
   * Destroy component
   */
  destroy(): void {
    if (this.container) {
      this.container.remove();
      this.container = undefined;
    }
  }
}

// Export singleton instance
export const scheduleInfo = new ScheduleInfo();