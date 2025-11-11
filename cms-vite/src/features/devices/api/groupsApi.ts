/**
 * Device Groups API
 */

import { apiClient } from '@/lib/api/client'
import { API_ENDPOINTS } from '@/lib/api/endpoints'
import type {
  DeviceGroup,
  CreateDeviceGroupRequest,
  UpdateDeviceGroupRequest,
  DeviceGroupStats,
} from '../types/groups'

export const groupsApi = {
  /**
   * Get all device groups
   */
  async getGroups(): Promise<{ items: DeviceGroup[]; total: number }> {
    const response = await apiClient.get(API_ENDPOINTS.DEVICES.GROUPS.LIST)
    return response.data
  },

  /**
   * Get root groups (no parent)
   */
  async getRootGroups(): Promise<{ items: DeviceGroup[]; total: number }> {
    const response = await apiClient.get(API_ENDPOINTS.DEVICES.GROUPS.ROOTS)
    return response.data
  },

  /**
   * Get single group
   */
  async getGroup(groupId: number): Promise<DeviceGroup> {
    const response = await apiClient.get(API_ENDPOINTS.DEVICES.GROUPS.GET(groupId))
    return response.data
  },

  /**
   * Get child groups
   */
  async getChildren(groupId: number): Promise<{ items: DeviceGroup[]; total: number }> {
    const response = await apiClient.get(API_ENDPOINTS.DEVICES.GROUPS.CHILDREN(groupId))
    return response.data
  },

  /**
   * Get group statistics
   */
  async getGroupStats(groupId: number): Promise<DeviceGroupStats> {
    const response = await apiClient.get(API_ENDPOINTS.DEVICES.GROUPS.STATS(groupId))
    return response.data
  },

  /**
   * Get devices in group
   */
  async getGroupDevices(groupId: number, recursive = false): Promise<{ devices: number[]; count: number }> {
    const response = await apiClient.get(API_ENDPOINTS.DEVICES.GROUPS.DEVICES(groupId), {
      params: { recursive },
    })
    return response.data
  },

  /**
   * Create device group
   */
  async createGroup(data: CreateDeviceGroupRequest): Promise<DeviceGroup> {
    const response = await apiClient.post(API_ENDPOINTS.DEVICES.GROUPS.CREATE, data)
    return response.data
  },

  /**
   * Update device group
   */
  async updateGroup(groupId: number, data: UpdateDeviceGroupRequest): Promise<DeviceGroup> {
    const response = await apiClient.put(API_ENDPOINTS.DEVICES.GROUPS.UPDATE(groupId), data)
    return response.data
  },

  /**
   * Delete device group
   */
  async deleteGroup(groupId: number): Promise<void> {
    await apiClient.delete(API_ENDPOINTS.DEVICES.GROUPS.DELETE(groupId))
  },

  /**
   * Add device to group
   */
  async addDeviceToGroup(groupId: number, deviceId: number): Promise<void> {
    await apiClient.post(API_ENDPOINTS.DEVICES.GROUPS.ADD_DEVICE(groupId), {
      device_id: deviceId,
    })
  },

  /**
   * Remove device from group
   */
  async removeDeviceFromGroup(groupId: number, deviceId: number): Promise<void> {
    await apiClient.delete(API_ENDPOINTS.DEVICES.GROUPS.REMOVE_DEVICE(groupId, deviceId))
  },
}
