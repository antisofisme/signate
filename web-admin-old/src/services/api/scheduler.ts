/**
 * Scheduler API Module
 * Scheduler service monitoring, device schedule tracking, and manual refresh endpoints
 */

import api from './index'
import type { AxiosResponse } from 'axios'
import type {
  SchedulerStatus,
  DeviceSchedule,
  DeviceRefreshResult,
  BulkRefreshResult,
} from '../../types/scheduler'

/**
 * Response wrapper for device schedule
 */
interface DeviceScheduleResponse {
  schedule: DeviceSchedule
}

const schedulerAPI = {
  /**
   * Get scheduler service status
   * GET /api/scheduler/status
   */
  getStatus: (): Promise<AxiosResponse<SchedulerStatus>> => {
    return api.get('/api/scheduler/status')
  },

  /**
   * Get all device schedules
   * GET /api/scheduler/devices/schedules
   */
  getAllDeviceSchedules: (): Promise<AxiosResponse<DeviceSchedule[]>> => {
    return api.get('/api/scheduler/devices/schedules')
  },

  /**
   * Get schedule for a specific device
   * GET /api/scheduler/devices/{id}/schedule
   */
  getDeviceSchedule: (deviceId: number): Promise<AxiosResponse<DeviceScheduleResponse>> => {
    return api.get(`/api/scheduler/devices/${deviceId}/schedule`)
  },

  /**
   * Manually refresh content for a specific device
   * POST /api/scheduler/devices/{id}/refresh
   */
  refreshDevice: (deviceId: number): Promise<AxiosResponse<DeviceRefreshResult>> => {
    return api.post(`/api/scheduler/devices/${deviceId}/refresh`)
  },

  /**
   * Manually refresh content for all active devices
   * POST /api/scheduler/refresh-all
   */
  refreshAll: (): Promise<AxiosResponse<BulkRefreshResult>> => {
    return api.post('/api/scheduler/refresh-all')
  },
}

export default schedulerAPI
