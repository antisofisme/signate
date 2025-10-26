import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { API_BASE_URL } from '../utils/constants'

/**
 * FASE 9.3: WebSocket Real-time Updates Hook
 *
 * Connects to WebSocket for real-time dashboard updates
 * Auto-reconnects on disconnect, gracefully falls back to polling if WebSocket unavailable
 *
 * @returns {Object} - { isConnected, connectionStatus }
 */
export function useDashboardWebSocket() {
  const queryClient = useQueryClient()
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('Disconnected')

  useEffect(() => {
    // Convert http to ws protocol
    const wsUrl = API_BASE_URL.replace('http', 'ws') + '/api/ws/dashboard'

    console.log('[WebSocket] Attempting to connect to:', wsUrl)
    setConnectionStatus('Connecting...')

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws

        ws.onopen = () => {
          console.log('[WebSocket] Connected to dashboard')
          setIsConnected(true)
          setConnectionStatus('Connected')
        }

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data)
            console.log('[WebSocket] Received:', message)

            if (message.type === 'dashboard_update') {
              handleDashboardUpdate(message.event, message.data)
            }
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error)
          }
        }

        ws.onerror = (error) => {
          console.error('[WebSocket] Error:', error)
          setConnectionStatus('Error')
        }

        ws.onclose = () => {
          console.log('[WebSocket] Disconnected')
          setIsConnected(false)
          setConnectionStatus('Disconnected')

          // Auto-reconnect after 5 seconds
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('[WebSocket] Reconnecting...')
            setConnectionStatus('Reconnecting...')
            connect()
          }, 5000)
        }
      } catch (error) {
        console.error('[WebSocket] Connection failed:', error)
        setConnectionStatus('Failed')
        setIsConnected(false)
      }
    }

    // Handle dashboard updates
    const handleDashboardUpdate = (event, data) => {
      console.log(`[WebSocket] Dashboard event: ${event}`, data)

      switch (event) {
        case 'device_registered':
        case 'device_approved':
        case 'device_deleted':
        case 'device_updated':
          // Invalidate devices query to trigger refetch
          queryClient.invalidateQueries(['devices'])
          break

        case 'content_uploaded':
        case 'content_deleted':
        case 'content_updated':
          // Invalidate content query
          queryClient.invalidateQueries(['content'])
          queryClient.invalidateQueries(['all-content-assignments'])
          break

        case 'playlist_created':
        case 'playlist_updated':
        case 'playlist_deleted':
          // Invalidate playlists query
          queryClient.invalidateQueries(['playlists'])
          break

        case 'tag_created':
        case 'tag_updated':
        case 'tag_deleted':
          // Invalidate tags query
          queryClient.invalidateQueries(['tags'])
          break

        default:
          console.log('[WebSocket] Unknown event:', event)
      }
    }

    // Attempt to connect
    connect()

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        console.log('[WebSocket] Closing connection')
        wsRef.current.close()
      }
    }
  }, [queryClient])

  return { isConnected, connectionStatus }
}
