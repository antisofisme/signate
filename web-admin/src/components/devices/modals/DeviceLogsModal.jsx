import { useState, useEffect, useRef } from 'react'
import { X, Trash2, Download } from 'lucide-react'
import { devicesAPI } from '../../../services/api'

/**
 * DeviceLogsModal Component
 * Real-time log viewer using WebSocket streaming
 */
export default function DeviceLogsModal({ device, onClose }) {
  const [logs, setLogs] = useState([])
  const [filteredLogs, setFilteredLogs] = useState([])
  const [selectedLevel, setSelectedLevel] = useState('all')
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('Connecting...')

  const logsEndRef = useRef(null)
  const wsRef = useRef(null)

  // Format timestamp to local time (WIB/WITA/WIT)
  const formatLocalTime = (timestamp) => {
    const date = new Date(timestamp)
    // Add 'Z' if not present to ensure UTC parsing
    const utcDate = timestamp.endsWith('Z') ? date : new Date(timestamp + 'Z')

    return utcDate.toLocaleTimeString('id-ID', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  }

  const formatLocalDateTime = (timestamp) => {
    const date = new Date(timestamp)
    const utcDate = timestamp.endsWith('Z') ? date : new Date(timestamp + 'Z')

    return utcDate.toLocaleString('id-ID', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  }

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [filteredLogs])

  // Filter logs by level
  useEffect(() => {
    if (selectedLevel === 'all') {
      setFilteredLogs(logs)
    } else {
      setFilteredLogs(logs.filter(log => log.log_level === selectedLevel))
    }
  }, [logs, selectedLevel])

  // Count logs by level
  const getLogCount = (level) => {
    if (level === 'all') {
      return logs.length
    }
    return logs.filter(log => log.log_level === level).length
  }

  // Load initial logs from REST API
  useEffect(() => {
    const loadInitialLogs = async () => {
      try {
        setConnectionStatus('Loading logs...')
        const response = await devicesAPI.getLogs(device.id)

        // Response.data is array of logs, reverse to show oldest first
        const reversedLogs = [...response.data].reverse()
        setLogs(reversedLogs)
        setConnectionStatus('Loaded')
        console.log(`Loaded ${response.data.length} initial logs for device ${device.id}`)
      } catch (error) {
        console.error('Failed to load initial logs:', error)
        setConnectionStatus('Failed to load logs')
      }
    }

    loadInitialLogs()
  }, [device.id])

  // WebSocket connection for real-time updates (optional)
  useEffect(() => {
    const wsUrl = `ws://192.168.5.12:8001/api/ws/logs/${device.id}`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected for real-time logs')
        setIsConnected(true)
        setConnectionStatus('Connected (real-time)')
      }

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)

        if (data.type === 'connected') {
          console.log('Received connection confirmation:', data.message)
        } else if (data.type === 'subscribed') {
          console.log('Subscribed to channel:', data.channel)
        } else if (data.type === 'log') {
          // Add new log to the end
          setLogs(prev => [...prev, data])
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        // Don't change status if we already have logs loaded
        if (logs.length === 0) {
          setConnectionStatus('WebSocket error (viewing cached logs)')
        }
        setIsConnected(false)
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
        // Keep status as "Loaded" if we have logs
        if (logs.length > 0) {
          setConnectionStatus('Loaded (no real-time updates)')
        } else {
          setConnectionStatus('Disconnected')
        }
      }

    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      setConnectionStatus('WebSocket unavailable (viewing cached logs)')
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [device.id])

  const handleRunSpeedTest = async () => {
    try {
      // Queue command to run speed test
      await devicesAPI.queueCommand(device.id, {
        command_type: 'run_speed_test',
        reason: 'Manual speed test triggered from web admin'
      })

      alert('Speed test command queued successfully. Check logs in a few seconds for results.')
    } catch (error) {
      console.error('Failed to queue speed test command:', error)
      alert(`Failed to run speed test: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleClearLogs = async () => {
    if (confirm('Clear all logs for this device?')) {
      try {
        await devicesAPI.deleteLogs(device.id)
        setLogs([])
        alert('Logs cleared successfully')
      } catch (error) {
        console.error('Failed to clear logs:', error)

        // Show specific error message
        if (error.response?.status === 401) {
          alert('Session expired. Please login again.')
        } else if (error.response?.status === 403) {
          alert('You do not have permission to clear logs')
        } else {
          alert(`Failed to clear logs: ${error.response?.data?.detail || error.message}`)
        }
      }
    }
  }

  const handleExportLogs = () => {
    const logsText = filteredLogs.map(log =>
      `[${formatLocalDateTime(log.timestamp)}] [${log.log_level.toUpperCase()}] ${log.message}`
    ).join('\n')

    const blob = new Blob([logsText], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `device-${device.id}-logs-${Date.now()}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const getLogLevelColor = (level) => {
    switch (level) {
      case 'error': return 'text-red-600 bg-red-50'
      case 'warn': return 'text-yellow-600 bg-yellow-50'
      case 'info': return 'text-blue-600 bg-blue-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="flex justify-between items-center p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold">Device Logs</h2>
            <p className="text-gray-600 mt-1">{device.device_name} (ID: {device.id})</p>
            <div className="flex items-center gap-2 mt-2">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm text-gray-600">{connectionStatus}</span>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="flex items-center justify-between p-4 border-b bg-gray-50">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-700">Filter:</span>
            {['all', 'log', 'info', 'warn', 'error'].map(level => {
              const count = getLogCount(level)
              return (
                <button
                  key={level}
                  onClick={() => setSelectedLevel(level)}
                  className={`inline-flex items-baseline gap-1 px-3 py-1 rounded text-sm font-medium transition-colors ${
                    selectedLevel === level ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <span>{level.toUpperCase()}</span>
                  <span className={`px-1.5 rounded-full text-xs font-bold leading-tight -translate-y-2 ${
                    selectedLevel === level
                      ? 'bg-red-500 text-white'
                      : 'bg-gray-500 text-white'
                  }`}>
                    {count}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 bg-gray-900 text-gray-100 font-mono text-sm">
          {filteredLogs.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              {logs.length === 0 ? 'Waiting for logs...' : 'No logs matching filter'}
            </div>
          ) : (
            filteredLogs.map((log, index) => (
              <div key={log.id || index} className="mb-2 flex items-start gap-3 hover:bg-gray-800 p-2 rounded">
                <span className="text-gray-500 text-xs whitespace-nowrap">
                  {formatLocalTime(log.timestamp)}
                </span>
                <span className={`px-2 py-0.5 rounded text-xs font-bold ${getLogLevelColor(log.log_level)}`}>
                  {log.log_level.toUpperCase()}
                </span>
                {log.source && (
                  <span className="text-purple-400 text-xs">[{log.source}]</span>
                )}
                <span className="flex-1 break-words">{log.message}</span>
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>

        <div className="p-4 border-t bg-gray-50">
          <div className="flex justify-between items-center mb-3">
            <span className="text-sm text-gray-600">Total logs: {logs.length} | Filtered: {filteredLogs.length}</span>
            <span className="text-xs text-gray-600">Real-time streaming via WebSocket</span>
          </div>
          <div className="flex items-center justify-end gap-2">
            <button
              onClick={handleRunSpeedTest}
              className="flex items-center gap-2 px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
              disabled={device.status !== 'active'}
              title={device.status !== 'active' ? 'Device must be active to run speed test' : 'Run network speed test'}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Speed Test
            </button>
            <button
              onClick={handleExportLogs}
              className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
              disabled={filteredLogs.length === 0}
            >
              <Download className="w-4 h-4" />
              Export
            </button>
            <button
              onClick={handleClearLogs}
              className="flex items-center gap-2 px-3 py-1.5 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
            >
              <Trash2 className="w-4 h-4" />
              Clear
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
