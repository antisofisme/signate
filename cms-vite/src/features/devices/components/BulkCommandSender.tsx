/**
 * Bulk Command Sender Component
 * Send commands to multiple devices at once
 */

import { useState } from 'react'
import { Send, Loader2, CheckCircle, XCircle, Users, AlertTriangle } from 'lucide-react'
import { deviceCommandApi } from '../api/commands'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import type { CommandType } from '../types/commands'
import { COMMAND_TYPE_INFO } from '../types/commandTemplates'

interface Device {
  id: number
  name: string
  status: string
}

interface BulkCommandSenderProps {
  devices: Device[]
  onComplete?: () => void
}

export function BulkCommandSender({ devices, onComplete }: BulkCommandSenderProps) {
  const [selectedDeviceIds, setSelectedDeviceIds] = useState<number[]>([])
  const [commandType, setCommandType] = useState<CommandType>('refresh_content')
  const [parameters, setParameters] = useState<Record<string, any>>({})
  const [priority, setPriority] = useState(5)
  const [expiresIn, setExpiresIn] = useState(30)
  const [showResults, setShowResults] = useState(false)
  const [results, setResults] = useState<any>(null)

  const queryClient = useQueryClient()

  const sendBulkCommand = useMutation({
    mutationFn: (data: any) => deviceCommandApi.sendBulkCommand(data),
    onSuccess: (data) => {
      setResults(data)
      setShowResults(true)
      queryClient.invalidateQueries({ queryKey: ['devices'] })
      toast.success(`Command sent to ${data.success_count || 0} devices`)

      // Auto-close after 3 seconds if all successful
      if (data.failure_count === 0) {
        setTimeout(() => {
          onComplete?.()
        }, 3000)
      }
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to send bulk command')
    },
  })

  const handleDeviceToggle = (deviceId: number) => {
    setSelectedDeviceIds((prev) =>
      prev.includes(deviceId) ? prev.filter((id) => id !== deviceId) : [...prev, deviceId]
    )
  }

  const handleSelectAll = () => {
    const onlineDevices = devices.filter((d) => d.status === 'online')
    setSelectedDeviceIds(onlineDevices.map((d) => d.id))
  }

  const handleDeselectAll = () => {
    setSelectedDeviceIds([])
  }

  const handleSend = () => {
    if (selectedDeviceIds.length === 0) {
      toast.error('Please select at least one device')
      return
    }

    const commandInfo = COMMAND_TYPE_INFO[commandType]
    if (commandInfo.requiresParameters && Object.keys(parameters).length === 0) {
      toast.error('This command requires parameters')
      return
    }

    sendBulkCommand.mutate({
      device_ids: selectedDeviceIds,
      command_type: commandType,
      command_data: parameters,
      priority,
      expires_in_minutes: expiresIn,
    })
  }

  const commandInfo = COMMAND_TYPE_INFO[commandType]
  const onlineDevices = devices.filter((d) => d.status === 'online')
  const offlineCount = devices.length - onlineDevices.length

  if (showResults && results) {
    return (
      <div className="space-y-4">
        {/* Results Summary */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Bulk Command Results
            </h3>
            <button
              onClick={() => {
                setShowResults(false)
                setResults(null)
                onComplete?.()
              }}
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
            >
              Close
            </button>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {results.total_devices}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Devices</div>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {results.success_count}
              </div>
              <div className="text-sm text-green-700 dark:text-green-400">Successful</div>
            </div>
            <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                {results.failure_count}
              </div>
              <div className="text-sm text-red-700 dark:text-red-400">Failed</div>
            </div>
          </div>

          {/* Detailed Results */}
          {results.commands && results.commands.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                Detailed Results
              </h4>
              <div className="max-h-60 overflow-y-auto space-y-2">
                {results.commands.map((cmd: any, idx: number) => (
                  <div
                    key={idx}
                    className={`flex items-center justify-between p-3 rounded-lg border ${
                      cmd.status === 'success'
                        ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                        : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {cmd.status === 'success' ? (
                        <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                      )}
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {cmd.device_name}
                        </div>
                        {cmd.error && (
                          <div className="text-xs text-red-600 dark:text-red-400 mt-0.5">
                            {cmd.error}
                          </div>
                        )}
                      </div>
                    </div>
                    {cmd.command_id && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        ID: {cmd.command_id}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Users className="w-6 h-6 text-blue-600 dark:text-blue-400" />
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Bulk Command Sender
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Send commands to multiple devices at once
          </p>
        </div>
      </div>

      {/* Warning for offline devices */}
      {offlineCount > 0 && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-yellow-800 dark:text-yellow-300">
              <strong>{offlineCount}</strong> device{offlineCount > 1 ? 's are' : ' is'} offline and will not receive commands.
              Only online devices are shown below.
            </div>
          </div>
        </div>
      )}

      {/* Command Configuration */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Command Configuration
        </h3>

        {/* Command Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Command Type
          </label>
          <select
            value={commandType}
            onChange={(e) => {
              setCommandType(e.target.value as CommandType)
              setParameters({})
            }}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            {Object.values(COMMAND_TYPE_INFO).map((cmd) => (
              <option key={cmd.type} value={cmd.type}>
                {cmd.icon} {cmd.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {commandInfo.description}
          </p>
        </div>

        {/* Parameters (if required) */}
        {commandInfo.requiresParameters && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Parameters (JSON)
            </label>
            <textarea
              value={JSON.stringify(parameters, null, 2)}
              onChange={(e) => {
                try {
                  setParameters(JSON.parse(e.target.value))
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              placeholder={JSON.stringify(commandInfo.commonParameters || {}, null, 2)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-mono text-sm"
            />
          </div>
        )}

        {/* Priority & Expiration */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Priority (1-10)
            </label>
            <input
              type="number"
              min="1"
              max="10"
              value={priority}
              onChange={(e) => setPriority(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Expires In (minutes)
            </label>
            <input
              type="number"
              min="5"
              max="1440"
              value={expiresIn}
              onChange={(e) => setExpiresIn(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>
        </div>
      </div>

      {/* Device Selection */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Select Devices ({selectedDeviceIds.length} selected)
            </h3>
            <div className="flex gap-2">
              <button
                onClick={handleSelectAll}
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                Select All
              </button>
              <span className="text-gray-400">|</span>
              <button
                onClick={handleDeselectAll}
                className="text-sm text-gray-600 dark:text-gray-400 hover:underline"
              >
                Deselect All
              </button>
            </div>
          </div>
        </div>

        <div className="max-h-80 overflow-y-auto p-4">
          {onlineDevices.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No online devices available
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {onlineDevices.map((device) => (
                <label
                  key={device.id}
                  className={`flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-colors ${
                    selectedDeviceIds.includes(device.id)
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedDeviceIds.includes(device.id)}
                    onChange={() => handleDeviceToggle(device.id)}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {device.name}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      ID: {device.id}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Send Button */}
      <div className="flex justify-end gap-3">
        <button
          onClick={onComplete}
          className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSend}
          disabled={selectedDeviceIds.length === 0 || sendBulkCommand.isPending}
          className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {sendBulkCommand.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Sending...
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              Send to {selectedDeviceIds.length} Device{selectedDeviceIds.length !== 1 ? 's' : ''}
            </>
          )}
        </button>
      </div>
    </div>
  )
}

export default BulkCommandSender
