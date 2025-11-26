/**
 * useWebSocket Hook
 * React hook for WebSocket functionality
 */

import { useEffect, useCallback, useRef } from 'react'
import { useWebSocketContext } from './WebSocketProvider'
import type { WebSocketMessageType, WebSocketEventHandler } from './types'
import { logger } from '@/shared/utils/logger'

/**
 * Hook to subscribe to WebSocket events
 *
 * @example
 * ```tsx
 * const { send, isConnected } = useWebSocket('device:status', (data) => {
 *   console.log('Device status:', data)
 * })
 * ```
 */
export function useWebSocket<T = any>(
  messageType: WebSocketMessageType,
  handler?: WebSocketEventHandler<T>
) {
  const { client, state } = useWebSocketContext()
  const handlerRef = useRef(handler)

  // Update handler ref when it changes
  useEffect(() => {
    handlerRef.current = handler
  }, [handler])

  // Subscribe to message type
  useEffect(() => {
    if (!client || !handlerRef.current) return

    const unsubscribe = client.on(messageType, handlerRef.current)
    return unsubscribe
  }, [client, messageType])

  // Send message function
  const send = useCallback(
    (data?: any) => {
      if (!client) {
        logger.warn('[useWebSocket] Client not available')
        return false
      }
      return client.send(messageType, data)
    },
    [client, messageType]
  )

  return {
    send,
    isConnected: state === 'connected',
    state,
  }
}

/**
 * Hook to subscribe to multiple WebSocket events
 *
 * @example
 * ```tsx
 * useWebSocketEvents({
 *   'device:status': (data) => console.log('Status:', data),
 *   'device:heartbeat': (data) => console.log('Heartbeat:', data),
 * })
 * ```
 */
export function useWebSocketEvents(
  handlers: Partial<Record<WebSocketMessageType, WebSocketEventHandler>>
) {
  const { client } = useWebSocketContext()

  useEffect(() => {
    if (!client) return

    const unsubscribers: Array<() => void> = []

    // Subscribe to all handlers
    Object.entries(handlers).forEach(([type, handler]) => {
      if (handler) {
        const unsubscribe = client.on(type as WebSocketMessageType, handler)
        unsubscribers.push(unsubscribe)
      }
    })

    // Cleanup all subscriptions
    return () => {
      unsubscribers.forEach(unsubscribe => unsubscribe())
    }
  }, [client, handlers])
}

/**
 * Hook to send WebSocket messages
 *
 * @example
 * ```tsx
 * const sendMessage = useWebSocketSend()
 * sendMessage('device:status', { device_id: 1 })
 * ```
 */
export function useWebSocketSend() {
  const { client } = useWebSocketContext()

  return useCallback(
    <T = any>(type: WebSocketMessageType, data?: T) => {
      if (!client) {
        logger.warn('[useWebSocketSend] Client not available')
        return false
      }
      return client.send(type, data)
    },
    [client]
  )
}

/**
 * Hook to check WebSocket connection status
 *
 * @example
 * ```tsx
 * const { isConnected, state } = useWebSocketStatus()
 * ```
 */
export function useWebSocketStatus() {
  const { state } = useWebSocketContext()

  return {
    isConnected: state === 'connected',
    isConnecting: state === 'connecting',
    isDisconnected: state === 'disconnected',
    isError: state === 'error',
    state,
  }
}
