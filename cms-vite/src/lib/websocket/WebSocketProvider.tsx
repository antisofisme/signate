/**
 * WebSocket Provider
 * React Context provider for global WebSocket connection
 */

import React, { createContext, useContext, useEffect, useState, useRef } from 'react'
import { WebSocketClient } from './WebSocketClient'
import type { WebSocketState } from './types'

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

  useEffect(() => {
    if (!enabled) {
      return
    }

    // Get WebSocket URL
    const wsUrl = url || getWebSocketUrl()
    if (!wsUrl) {
      console.warn('[WebSocket] No URL provided')
      return
    }

    // Get auth token
    const token = localStorage.getItem('auth-token')
    if (!token) {
      console.warn('[WebSocket] No auth token found')
      return
    }

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
        console.log('[WebSocket] ✅ Connected')
        setState('connected')
      },
      onClose: () => {
        console.log('[WebSocket] ❌ Disconnected')
        setState('disconnected')
      },
      onError: (error) => {
        console.error('[WebSocket] 🔴 Error:', error)
        setState('error')
      },
    })

    // Connect
    client.connect(token)
    clientRef.current = client

    // Cleanup on unmount
    return () => {
      console.log('[WebSocket] Cleaning up...')
      client.destroy()
      clientRef.current = null
    }
  }, [url, enabled, debug])

  // Reconnect function
  const reconnect = () => {
    if (clientRef.current) {
      const token = localStorage.getItem('auth-token')
      if (token) {
        clientRef.current.connect(token)
      }
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
 * Get WebSocket URL based on environment
 */
function getWebSocketUrl(): string {
  // Get base URL from environment or window location
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = import.meta.env.VITE_API_URL
    ? new URL(import.meta.env.VITE_API_URL).host
    : window.location.host

  // For development, use server IP
  if (import.meta.env.DEV) {
    return `ws://192.168.5.12:8001/api/ws/admin`
  }

  // For production, use same host as API
  return `${protocol}//${host}/api/ws/admin`
}
