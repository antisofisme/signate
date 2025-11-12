/**
 * PMS Configuration Page
 *
 * Main page for configuring PMS integration
 */

import { useState } from 'react'
import { Building2, Save, Trash2, Users, DoorOpen } from 'lucide-react'
import { PageHeader } from '@/shared/components'
import { PMSProviderSelect } from '../components/PMSProviderSelect'
import { PMSConnectionForm } from '../components/PMSConnectionForm'
import { PMSSyncStatus } from '../components/PMSSyncStatus'
import { RoomMappingTable } from '../components/RoomMappingTable'
import {
  usePMSConfig,
  useCreatePMSConfig,
  useUpdatePMSConfig,
  useDeletePMSConfig,
  usePMSStats,
} from '../hooks/usePMS'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api/client'
import type { PMSProvider, PMSConnectionConfig, PMSSyncConfig } from '../types/pms.types'

export default function PMSConfigPage() {
  const { data: config, isLoading } = usePMSConfig()
  const { data: stats } = usePMSStats()
  const createConfig = useCreatePMSConfig()
  const updateConfig = useUpdatePMSConfig()
  const deleteConfig = useDeletePMSConfig()

  // Get available devices for room mapping
  const { data: devicesData } = useQuery({
    queryKey: ['devices'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/devices')
      return response.data
    },
  })

  const [activeTab, setActiveTab] = useState<'config' | 'guests' | 'rooms'>('config')
  const [provider, setProvider] = useState<PMSProvider>(config?.provider || 'opera')
  const [connectionConfig, setConnectionConfig] = useState<PMSConnectionConfig>(
    config?.connection_config || {
      host: '',
      port: 443,
      protocol: 'https',
      timeout: 30,
      retry_attempts: 3,
      ssl_verify: true,
    }
  )
  const [syncConfig, setSyncConfig] = useState<PMSSyncConfig>(
    config?.sync_config || {
      auto_sync_enabled: true,
      sync_interval_minutes: 30,
      sync_guests: true,
      sync_rooms: true,
      sync_reservations: false,
    }
  )

  const handleSave = () => {
    const data = {
      provider,
      connection_config: connectionConfig,
      sync_config: syncConfig,
    }

    if (config) {
      updateConfig.mutate(data)
    } else {
      createConfig.mutate(data)
    }
  }

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete the PMS configuration? This cannot be undone.')) {
      deleteConfig.mutate()
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading PMS configuration...</div>
      </div>
    )
  }

  return (
    <>
      <PageHeader
        title="PMS Integration"
        description="Configure Property Management System integration for hotel signage"
      />

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Users className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.current_guests}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Current Guests</div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <DoorOpen className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.occupied_rooms}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Occupied Rooms</div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <DoorOpen className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.vacant_rooms}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Vacant Rooms</div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Building2 className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.mapped_devices}/{stats.total_rooms}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Mapped Devices</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setActiveTab('config')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'config'
              ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Configuration
        </button>
        <button
          onClick={() => setActiveTab('rooms')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'rooms'
              ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
        >
          Room Mapping
        </button>
      </div>

      {/* Config Tab */}
      {activeTab === 'config' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Provider & Connection */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <PMSProviderSelect
                value={provider}
                onChange={setProvider}
                disabled={createConfig.isPending || updateConfig.isPending}
              />

              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                <PMSConnectionForm
                  provider={provider}
                  config={connectionConfig}
                  onChange={setConnectionConfig}
                  disabled={createConfig.isPending || updateConfig.isPending}
                />
              </div>
            </div>

            {/* Sync Settings */}
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Sync Settings
              </h3>

              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="auto_sync"
                    checked={syncConfig.auto_sync_enabled}
                    onChange={(e) =>
                      setSyncConfig({ ...syncConfig, auto_sync_enabled: e.target.checked })
                    }
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="auto_sync" className="text-sm text-gray-700 dark:text-gray-300">
                    Enable automatic sync
                  </label>
                </div>

                {syncConfig.auto_sync_enabled && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Sync Interval (minutes)
                    </label>
                    <input
                      type="number"
                      value={syncConfig.sync_interval_minutes}
                      onChange={(e) =>
                        setSyncConfig({
                          ...syncConfig,
                          sync_interval_minutes: parseInt(e.target.value) || 30,
                        })
                      }
                      min="5"
                      max="1440"
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    />
                  </div>
                )}

                <div className="space-y-2 pt-2">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="sync_guests"
                      checked={syncConfig.sync_guests}
                      onChange={(e) =>
                        setSyncConfig({ ...syncConfig, sync_guests: e.target.checked })
                      }
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <label htmlFor="sync_guests" className="text-sm text-gray-700 dark:text-gray-300">
                      Sync guest data
                    </label>
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="sync_rooms"
                      checked={syncConfig.sync_rooms}
                      onChange={(e) =>
                        setSyncConfig({ ...syncConfig, sync_rooms: e.target.checked })
                      }
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <label htmlFor="sync_rooms" className="text-sm text-gray-700 dark:text-gray-300">
                      Sync room data
                    </label>
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="sync_reservations"
                      checked={syncConfig.sync_reservations}
                      onChange={(e) =>
                        setSyncConfig({ ...syncConfig, sync_reservations: e.target.checked })
                      }
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <label
                      htmlFor="sync_reservations"
                      className="text-sm text-gray-700 dark:text-gray-300"
                    >
                      Sync reservations
                    </label>
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <button
                onClick={handleSave}
                disabled={createConfig.isPending || updateConfig.isPending}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="w-5 h-5" />
                {config ? 'Update Configuration' : 'Save Configuration'}
              </button>

              {config && (
                <button
                  onClick={handleDelete}
                  disabled={deleteConfig.isPending}
                  className="flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Trash2 className="w-5 h-5" />
                  Delete Configuration
                </button>
              )}
            </div>
          </div>

          {/* Sync Status Sidebar */}
          <div className="lg:col-span-1">
            <PMSSyncStatus />
          </div>
        </div>
      )}

      {/* Rooms Tab */}
      {activeTab === 'rooms' && (
        <RoomMappingTable availableDevices={devicesData?.devices || []} />
      )}
    </>
  )
}
