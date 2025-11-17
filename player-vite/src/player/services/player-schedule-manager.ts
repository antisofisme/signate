/**
 * Player Schedule Manager
 * Manages advanced scheduling for playlist playback
 */

import { SharedAPIClient } from '@shared/api';
import { SharedLogger } from '@shared/logger';
import { SharedEventBus } from '@shared/events/shared-event-bus';
import { SharedDeviceState } from '@shared/device';

export interface Schedule {
  id: number;
  name: string;
  playlist_id: number;
  organization_id: number;
  start_date: string;
  end_date: string | null;
  start_time: string;
  end_time: string;
  recurrence_type: 'once' | 'daily' | 'weekly' | 'monthly' | 'yearly';
  recurrence_pattern?: {
    interval?: number;
    days?: number[]; // For weekly: 1=Mon, 7=Sun
    day_of_month?: number;
    month?: number;
  };
  exceptions?: string[]; // ISO date strings
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ActiveSchedule {
  schedule: Schedule | null;
  playlist_id: number | null;
  schedule_name: string | null;
  priority: number | null;
  is_found: boolean;
}

export class PlayerScheduleManager {
  private schedules: Schedule[] = [];
  private currentSchedule: Schedule | null = null;
  private checkInterval: number | null = null;
  private lastCheck: Date | null = null;
  private organizationId: number | null = null;

  constructor() {
    SharedLogger.info('[PlayerScheduleManager] Initializing...');
  }

  /**
   * Initialize schedule manager
   */
  async initialize(): Promise<void> {
    // Get organization_id from localStorage (more reliable)
    const orgIdStr = SharedDeviceState.getOrganizationId();
    if (!orgIdStr) {
      SharedLogger.debug('[PlayerScheduleManager] No organization ID yet, skipping initialization (will retry on activation)');
      return;
    }

    this.organizationId = parseInt(orgIdStr, 10);
    
    // Initial sync
    await this.syncSchedules();
    
    // Start schedule checking
    this.startScheduleCheck();
    
    // Listen for events
    this.setupEventListeners();
    
    SharedLogger.info('[PlayerScheduleManager] Initialized');
  }

  /**
   * Sync schedules from backend
   */
  async syncSchedules(): Promise<void> {
    try {
      if (!this.organizationId) return;

      // TODO: Schedule API not implemented yet in backend
      // Temporarily skip sync to avoid console errors
      SharedLogger.debug('[PlayerScheduleManager] Schedule sync skipped (API not ready)');
      return;

      /* Uncomment when backend /api/v1/schedules is ready
      const response = await SharedAPIClient.get<{ schedules: Schedule[] }>(
        `/api/v1/schedules?organization_id=${this.organizationId}&is_active=true`
      );

      if (response) {
        this.schedules = response.schedules || [];
        SharedLogger.info(`[PlayerScheduleManager] Synced ${this.schedules.length} schedules`);

        // Check for active schedule immediately after sync
        this.checkActiveSchedule();
      }
      */
    } catch (error) {
      SharedLogger.error('[PlayerScheduleManager] Failed to sync schedules:', error);
    }
  }

  /**
   * Start periodic schedule checking
   */
  private startScheduleCheck(): void {
    // Stop existing interval
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
    }
    
    // Check every minute
    this.checkInterval = window.setInterval(() => {
      this.checkActiveSchedule();
    }, 60000); // 1 minute
    
    SharedLogger.debug('[PlayerScheduleManager] Schedule check interval started');
  }

  /**
   * Check for active schedule
   */
  private checkActiveSchedule(): void {
    const now = new Date();
    const currentTime = this.formatTime(now);
    const currentDate = this.formatDate(now);
    
    // Don't check too frequently
    if (this.lastCheck) {
      const timeSinceLastCheck = now.getTime() - this.lastCheck.getTime();
      if (timeSinceLastCheck < 10000) { // 10 seconds
        return;
      }
    }
    
    this.lastCheck = now;
    
    // Find active schedule with highest priority
    let activeSchedule: Schedule | null = null;
    let highestPriority = -1;
    
    for (const schedule of this.schedules) {
      if (!schedule.is_active) continue;
      
      // Check date range
      if (currentDate < schedule.start_date) continue;
      if (schedule.end_date && currentDate > schedule.end_date) continue;
      
      // Check time range
      if (currentTime < schedule.start_time || currentTime > schedule.end_time) continue;
      
      // Check if date is in exceptions
      if (schedule.exceptions?.includes(currentDate)) continue;
      
      // Check recurrence pattern
      if (!this.isScheduleActiveOnDate(schedule, now)) continue;
      
      // Check priority
      if (schedule.priority > highestPriority) {
        activeSchedule = schedule;
        highestPriority = schedule.priority;
      }
    }
    
    // If active schedule changed, emit event
    if (activeSchedule?.id !== this.currentSchedule?.id) {
      this.currentSchedule = activeSchedule;
      
      if (activeSchedule) {
        SharedLogger.info(`[PlayerScheduleManager] Active schedule: ${activeSchedule.name} (playlist: ${activeSchedule.playlist_id})`);
        SharedEventBus.emit('schedule:changed', {
          schedule: activeSchedule,
          playlist_id: activeSchedule.playlist_id,
        });
      } else {
        SharedLogger.info('[PlayerScheduleManager] No active schedule');
        SharedEventBus.emit('schedule:changed', {
          schedule: null,
          playlist_id: null,
        });
      }
    }
  }

  /**
   * Check if schedule is active on given date
   */
  private isScheduleActiveOnDate(schedule: Schedule, date: Date): boolean {
    const dayOfWeek = date.getDay() || 7; // Convert Sunday from 0 to 7
    const dayOfMonth = date.getDate();
    const month = date.getMonth() + 1;
    
    switch (schedule.recurrence_type) {
      case 'once':
        return this.formatDate(date) === schedule.start_date;
        
      case 'daily':
        const interval = schedule.recurrence_pattern?.interval || 1;
        const startDate = new Date(schedule.start_date);
        const daysDiff = Math.floor((date.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
        return daysDiff >= 0 && daysDiff % interval === 0;
        
      case 'weekly':
        const days = schedule.recurrence_pattern?.days || [];
        return days.includes(dayOfWeek);
        
      case 'monthly':
        const monthDays = schedule.recurrence_pattern?.days || [];
        return monthDays.includes(dayOfMonth);
        
      case 'yearly':
        const yearMonth = schedule.recurrence_pattern?.month;
        const yearDay = schedule.recurrence_pattern?.day_of_month;
        return month === yearMonth && dayOfMonth === yearDay;
        
      default:
        return false;
    }
  }

  /**
   * Get current active schedule
   */
  getCurrentSchedule(): Schedule | null {
    return this.currentSchedule;
  }

  /**
   * Get active schedule info
   */
  async getActiveSchedule(): Promise<ActiveSchedule> {
    if (!this.organizationId) {
      return {
        schedule: null,
        playlist_id: null,
        schedule_name: null,
        priority: null,
        is_found: false,
      };
    }
    
    try {
      const now = new Date();
      const response = await SharedAPIClient.get<ActiveSchedule>(
        `/api/v1/schedules/active?organization_id=${this.organizationId}&date=${this.formatDate(now)}&time=${this.formatTime(now)}`
      );
      
      if (response) {
        return response;
      }
    } catch (error) {
      SharedLogger.error('[PlayerScheduleManager] Failed to get active schedule:', error);
    }
    
    return {
      schedule: null,
      playlist_id: null,
      schedule_name: null,
      priority: null,
      is_found: false,
    };
  }

  /**
   * Setup event listeners
   */
  private setupEventListeners(): void {
    // Re-sync schedules when device comes online
    SharedEventBus.on('device:online', () => {
      this.syncSchedules();
    });
    
    // Re-sync schedules periodically
    setInterval(() => {
      this.syncSchedules();
    }, 300000); // 5 minutes
  }

  /**
   * Format date as YYYY-MM-DD
   */
  private formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
  }

  /**
   * Format time as HH:MM:SS
   */
  private formatTime(date: Date): string {
    return date.toTimeString().split(' ')[0];
  }

  /**
   * Stop schedule manager
   */
  stop(): void {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
    
    SharedLogger.info('[PlayerScheduleManager] Stopped');
  }
}

// Export singleton instance
export const playerScheduleManager = new PlayerScheduleManager();