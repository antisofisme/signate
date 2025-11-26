/**
 * WebSocket Provider
 * React Context provider for global WebSocket connection
 */

import React, { createContext, useContext, useEffect, useState, useRef } from 'react'
import { WebSocketClient } from './WebSocketClient'
import type { WebSocketState } from './types'
import { useAuthStore } from '../stores/authStore'
import { logger } from '@/shared/utils/logger'
import { getSmartWebSocketUrl } from '../config/network-detector'

// ============================================================================
// Context Types
// ============================================================================

interface WebSocketContextValue {
  client: WebSocketClient | null
  state: WebSocketState
  reconnect: () => void
}

const WebSocketContext = createContext<WebSocketContextValue | undefined>(undefined)

// ============================================================================
// Provider Props
// ============================================================================

interface WebSocketProviderProps {
  children: React.ReactNode
  url?: string
  enabled?: boolean
  debug?: boolean
}

// ============================================================================
// Provider Component
// ============================================================================

export function WebSocketProvider({
  children,
  url,
  enabled = true,
  debug = false,
}: WebSocketProviderProps) {
  const [state, setState] = useState<WebSocketState>('disconnected')
  const clientRef = useRef<WebSocketClient | null>(null)
  const { token, isAuthenticated, _hasHydrated } = useAuthStore()

  useEffect(() => {
    if (!enabled) {
      return
    }

    // Wait for Zustand hydration to complete
    if (!_hasHydrated) {
      logger.debug('[WebSocket] Waiting for store hydration...')
      return
    }

    // Get WebSocket URL
    const wsUrl = url || getWebSocketUrl()
    if (!wsUrl) {
      logger.warn('[WebSocket] No URL provided')
      return
    }

    // Get auth token from Zustand store (not localStorage)
    if (!token || !isAuthenticated) {
      logger.warn('[WebSocket] No auth token found or not authenticated')
      return
    }

    // Guard against React StrictMode double-invocation
    // If there's already a client and it's connected/connecting, don't create a new one
    if (clientRef.current && clientRef.current.isConnected()) {
      logger.debug('[WebSocket] Already connected, skipping reconnection')
      return
    }

    logger.debug('[WebSocket] Store hydrated, token present:', token ? 'YES' : 'NO')

    // Create WebSocket client
    const client = new WebSocketClient({
      url: wsUrl,
      reconnect: true,
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      debug,
    })

    // Setup global handlers
    client.setGlobalHandlers({
      onOpen: () => {
        logger.info('[WebSocket] Connected')
        setState('connected')
      },
      onClose: () => {
        logger.info('[WebSocket] Disconnected')
        setState('disconnected')
      },
      onError: (error) => {
        logger.error('[WebSocket] Error', error)
        setState('error')
      },
    })

    // Connect
    client.connect(token)
    clientRef.current = client

    // Cleanup on unmount (but only if this effect created the client)
    return () => {
      // Only cleanup if we're the ones who created this client
      if (clientRef.current === client) {
        logger.debug('[WebSocket] Cleaning up...')
        client.destroy()
        clientRef.current = null
      }
    }
  }, [url, enabled, debug, isAuthenticated, _hasHydrated]) // Removed 'token' to prevent reconnection loops

  // Reconnect function
  const reconnect = () => {
    const currentToken = useAuthStore.getState().token
    if (clientRef.current && currentToken) {
      clientRef.current.connect(currentToken)
    }
  }

  const value: WebSocketContextValue = {
    client: clientRef.current,
    state,
    reconnect,
  }

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  )
}

// ============================================================================
// Hook to use WebSocket context
// ============================================================================

export function useWebSocketContext() {
  const context = useContext(WebSocketContext)
  if (context === undefined) {
    throw new Error('useWebSocketContext must be used within WebSocketProvider')
  }
  return context
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get WebSocket URL based on environment with smart detection
 */
function getWebSocketUrl(): string {
  // Use smart detection to get base WebSocket URL
  const wsBaseUrl = getSmartWebSocketUrl()
  return `${wsBaseUrl}/api/ws/admin`
}
