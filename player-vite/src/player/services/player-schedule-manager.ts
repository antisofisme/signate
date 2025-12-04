/**
 * Player Schedule Manager
 * Manages advanced scheduling for playlist playback
 */

import { SharedAPIClient } from '@shared/api';
import { SharedLogger } from '@shared/logger';
import { SharedEventBus } from '@shared/events/shared-event-bus';
import { SharedDeviceState } from '@shared/device';
import { config } from '@shared/config';

// Target device info from junction table
export interface TargetDeviceInfo {
  id: number;
  device_name: string;
}

// Target tag info from junction table
export interface TargetTagInfo {
  id: number;
  name: string;
}

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
  is_active: boolean;
  mode: 'override' | 'rotate';  // Playback mode: override (only playlist), rotate (merge all)
  created_at: string;
  updated_at: string;

  // Targeting fields (Migration 078)
  device_ids?: number[];              // DEPRECATED: Legacy JSONB array
  tag_ids?: number[];                 // DEPRECATED: Legacy JSONB array
  target_devices?: TargetDeviceInfo[];  // New: From junction table
  target_tags?: TargetTagInfo[];        // New: From junction table
  applies_to_all?: boolean;           // Apply to all devices in organization
}

export interface ActiveSchedule {
  schedule: Schedule | null;
  playlist_id: number | null;
  schedule_name: string | null;
  is_found: boolean;
}

export class PlayerScheduleManager {
  private schedules: Schedule[] = [];
  private currentSchedule: Schedule | null = null;
  private checkInterval: number | null = null;
  private syncInterval: number | null = null; // Track sync interval
  private lastCheck: Date | null = null;
  private organizationId: number | null = null;
  private eventCleanup: (() => void) | null = null; // Track event listener cleanup

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
   * FIX #2: Added retry logic for failed syncs
   * @param retryCount - Current retry attempt (0-3)
   */
  async syncSchedules(retryCount = 0): Promise<void> {
    try {
      // FIX #2: Try to get organizationId if not available
      if (!this.organizationId) {
        const orgId = SharedDeviceState.getOrganizationId();
        if (orgId) {
          this.organizationId = parseInt(orgId, 10);
          SharedLogger.info(`[PlayerScheduleManager] Got organization ID from device state: ${this.organizationId}`);
        } else if (retryCount < 3) {
          SharedLogger.warn(`[PlayerScheduleManager] No organization ID, retry ${retryCount + 1}/3 in 1s...`);
          await new Promise(resolve => setTimeout(resolve, 1000));
          return this.syncSchedules(retryCount + 1);
        } else {
          SharedLogger.error('[PlayerScheduleManager] ❌ No organization ID after 3 retries');
          // Still emit event with no schedule to ensure PlaylistSync gets notified
          this.checkActiveSchedule();
          return;
        }
      }

      const deviceId = SharedDeviceState.getDeviceId();
      if (!deviceId) {
        SharedLogger.warn('[PlayerScheduleManager] No device ID, skipping schedule sync');
        this.checkActiveSchedule();
        return;
      }

      // FIX: Use full URL with base URL (was missing before, causing fetch to fail)
      const url = `${config.api.baseURL}/api/v1/client/schedules?organization_id=${this.organizationId}&device_id=${deviceId}&is_active=true`;

      SharedLogger.info(`[PlayerScheduleManager] 📡 Fetching schedules: ${url}`);

      const response = await SharedAPIClient.get<{ schedules: Schedule[] }>(url);

      if (response) {
        this.schedules = response.schedules || [];
        SharedLogger.info(`[PlayerScheduleManager] ✅ Synced ${this.schedules.length} schedules`);

        // Debug: Log schedule details including mode
        this.schedules.forEach((s) => {
          SharedLogger.info(`[PlayerScheduleManager] 📅 Schedule: ${s.name} (id=${s.id}, playlist=${s.playlist_id}, mode=${s.mode})`);
        });

        // Check for active schedule immediately after sync
        this.checkActiveSchedule();
      } else {
        SharedLogger.warn('[PlayerScheduleManager] ⚠️ Empty response from schedule API');
        this.checkActiveSchedule();
      }
    } catch (error: any) {
      SharedLogger.error('[PlayerScheduleManager] ❌ Failed to sync schedules:', {
        error: error?.message || error,
        organizationId: this.organizationId,
        retryCount,
        stack: error?.stack,
      });

      // FIX #2: Retry on failure
      if (retryCount < 3) {
        SharedLogger.warn(`[PlayerScheduleManager] Retrying schedule sync ${retryCount + 1}/3 in 2s...`);
        await new Promise(resolve => setTimeout(resolve, 2000));
        return this.syncSchedules(retryCount + 1);
      }

      // After all retries failed, still emit event to ensure PlaylistSync is notified
      SharedLogger.error('[PlayerScheduleManager] ❌ Schedule sync failed after 3 retries');
      this.checkActiveSchedule();
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
    
    // Find active schedule
    // NOTE: Priority feature removed - now using playback mode (override/rotate)
    // If multiple schedules are active, override mode takes precedence, then newest schedule
    let activeSchedule: Schedule | null = null;

    SharedLogger.info(`[PlayerScheduleManager] 🕐 Current: date=${currentDate}, time=${currentTime}, schedules=${this.schedules.length}`);

    for (const schedule of this.schedules) {
      SharedLogger.debug(`[PlayerScheduleManager] 📋 Checking: "${schedule.name}" (${schedule.start_time}-${schedule.end_time}, mode=${schedule.mode})`);

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

      // Schedule is active! Determine if it should be the activeSchedule
      SharedLogger.info(`[PlayerScheduleManager] ✅ Schedule "${schedule.name}" matches current time (mode=${schedule.mode})`);

      // Selection logic (priority removed, now based on mode):
      // 1. Override mode takes precedence over rotate
      // 2. If same mode, prefer newer schedule (higher id)
      if (!activeSchedule) {
        activeSchedule = schedule;
      } else if (schedule.mode === 'override' && activeSchedule.mode !== 'override') {
        // Override mode wins
        activeSchedule = schedule;
      } else if (schedule.mode === activeSchedule.mode && schedule.id > activeSchedule.id) {
        // Same mode, prefer newer schedule
        activeSchedule = schedule;
      }
    }
    
    // Check if schedule changed (for logging purposes)
    const scheduleChanged = activeSchedule?.id !== this.currentSchedule?.id;
    const modeChanged = activeSchedule?.mode !== this.currentSchedule?.mode;

    // Debug logging for schedule detection
    SharedLogger.info(`[PlayerScheduleManager] Check result: activeSchedule=${activeSchedule?.id || 'none'}, currentSchedule=${this.currentSchedule?.id || 'none'}, scheduleChanged=${scheduleChanged}, modeChanged=${modeChanged}`);

    // FIX #1: ALWAYS update currentSchedule and emit event
    // This ensures PlaylistSync receives schedule info even on first initialization
    // Previously, event was only emitted on CHANGE, causing race condition on boot
    this.currentSchedule = activeSchedule;

    if (activeSchedule) {
      SharedLogger.info(`[PlayerScheduleManager] 🎯 Active schedule: ${activeSchedule.name} (id=${activeSchedule.id}, playlist=${activeSchedule.playlist_id}, mode=${activeSchedule.mode})`);
      SharedEventBus.emit('schedule:changed', {
        schedule: activeSchedule,
        playlist_id: activeSchedule.playlist_id,
        mode: activeSchedule.mode || 'rotate',  // Include playback mode
      });
    } else {
      SharedLogger.info('[PlayerScheduleManager] No active schedule');
      SharedEventBus.emit('schedule:changed', {
        schedule: null,
        playlist_id: null,
        mode: 'rotate',  // Default to rotate when no schedule
      });
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
      is_found: false,
    };
  }

  /**
   * Setup event listeners
   */
  private setupEventListeners(): void {
    // Re-sync schedules when device comes online - store cleanup function
    this.eventCleanup = SharedEventBus.on('device:online', () => {
      this.syncSchedules();
    });

    // Listen for WebSocket schedule events (real-time updates)
    SharedEventBus.on('ws:SCHEDULE_ACTIVATED', (event: any) => {
      SharedLogger.info('[PlayerScheduleManager] WebSocket: Schedule activated', event);
      // Immediate sync instead of waiting for interval
      this.syncSchedules();
    });

    SharedEventBus.on('ws:SCHEDULE_DEACTIVATED', (event: any) => {
      SharedLogger.info('[PlayerScheduleManager] WebSocket: Schedule deactivated', event);
      // Clear current schedule and notify
      this.currentSchedule = null;
      SharedEventBus.emit('schedule:changed', {
        schedule: null,
        playlist_id: null,
      });
      // Sync to get the next active schedule (if any)
      this.syncSchedules();
    });

    // Re-sync schedules periodically (fallback) - track interval
    this.syncInterval = window.setInterval(() => {
      this.syncSchedules();
    }, 300000); // 5 minutes
  }

  /**
   * Format date as YYYY-MM-DD (local time, consistent with backend)
   */
  private formatDate(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
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
    // Clear check interval
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }

    // Clear sync interval
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }

    // Clean up event listener
    if (this.eventCleanup) {
      this.eventCleanup();
      this.eventCleanup = null;
    }

    SharedLogger.info('[PlayerScheduleManager] Stopped');
  }
}

// Export singleton instance
export const playerScheduleManager = new PlayerScheduleManager();