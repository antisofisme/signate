/**
 * WebSocket Client
 * Robust WebSocket client with auto-reconnect and event handling
 */

import type {
  WebSocketConfig,
  WebSocketState,
  WebSocketMessage,
  WebSocketMessageType,
  WebSocketEventHandler,
  WebSocketEventHandlers,
} from './types'

export class WebSocketClient {
  private ws: WebSocket | null = null
  private config: Required<WebSocketConfig>
  private state: WebSocketState = 'disconnected'
  private reconnectAttempts = 0
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private eventHandlers: Map<WebSocketMessageType, Set<WebSocketEventHandler>> = new Map()
  private globalHandlers: WebSocketEventHandlers = {}

  constructor(config: WebSocketConfig) {
    this.config = {
      url: config.url,
      reconnect: config.reconnect ?? true,
      reconnectInterval: config.reconnectInterval ?? 5000,
      maxReconnectAttempts: config.maxReconnectAttempts ?? 10,
      heartbeatInterval: config.heartbeatInterval ?? 30000,
      debug: config.debug ?? false,
    }

    this.log('WebSocket client initialized', this.config)
  }

  // ============================================================================
  // Connection Management
  // ============================================================================

  /**
   * Connect to WebSocket server
   */
  connect(token?: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.log('Already connected')
      return
    }

    if (this.ws?.readyState === WebSocket.CONNECTING) {
      this.log('Connection in progress')
      return
    }

    try {
      this.state = 'connecting'

      // Build URL with token if provided
      let url = this.config.url
      if (token) {
        const separator = url.includes('?') ? '&' : '?'
        url = `${url}${separator}token=${token}`
      }

      this.log('Connecting to:', url.replace(/token=[^&]+/, 'token=***'))

      this.ws = new WebSocket(url)
      this.setupEventListeners()

    } catch (error) {
      this.log('Connection error:', error)
      this.state = 'error'
      this.globalHandlers.onError?.(error as Event)
      this.scheduleReconnect()
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.log('Disconnecting...')

    this.clearTimers()
    this.config.reconnect = false // Prevent auto-reconnect

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect')
      this.ws = null
    }

    this.state = 'disconnected'
    this.reconnectAttempts = 0
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.state === 'connected' && this.ws?.readyState === WebSocket.OPEN
  }

  /**
   * Get current state
   */
  getState(): WebSocketState {
    return this.state
  }

  // ============================================================================
  // Event Listeners Setup
  // ============================================================================

  private setupEventListeners(): void {
    if (!this.ws) return

    this.ws.onopen = this.handleOpen.bind(this)
    this.ws.onclose = this.handleClose.bind(this)
    this.ws.onerror = this.handleError.bind(this)
    this.ws.onmessage = this.handleMessage.bind(this)
  }

  private handleOpen(): void {
    this.log('Connected')
    this.state = 'connected'
    this.reconnectAttempts = 0

    this.globalHandlers.onOpen?.()
    this.startHeartbeat()
  }

  private handleClose(event: CloseEvent): void {
    this.log('Disconnected', event.code, event.reason)
    this.state = 'disconnected'

    this.clearTimers()
    this.globalHandlers.onClose?.(event)

    // Auto-reconnect if enabled and not a normal closure
    if (this.config.reconnect && event.code !== 1000) {
      this.scheduleReconnect()
    }
  }

  private handleError(error: Event): void {
    this.log('WebSocket error:', error)
    this.state = 'error'
    this.globalHandlers.onError?.(error)
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)
      this.log('Message received:', message.type)

      // Call global message handler
      this.globalHandlers.onMessage?.(message)

      // Call specific event handlers
      const handlers = this.eventHandlers.get(message.type)
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(message.data)
          } catch (error) {
            this.log('Error in event handler:', error)
          }
        })
      }

    } catch (error) {
      this.log('Error parsing message:', error)
    }
  }

  // ============================================================================
  // Send Messages
  // ============================================================================

  /**
   * Send message to server
   */
  send<T = any>(type: WebSocketMessageType, data?: T): boolean {
    if (!this.isConnected()) {
      this.log('Cannot send message: not connected')
      return false
    }

    try {
      const message: WebSocketMessage<T> = {
        type,
        data: data as T,
        timestamp: new Date().toISOString(),
      }

      this.ws!.send(JSON.stringify(message))
      this.log('Message sent:', type)
      return true

    } catch (error) {
      this.log('Error sending message:', error)
      return false
    }
  }

  // ============================================================================
  // Event Handlers
  // ============================================================================

  /**
   * Register event handler for specific message type
   */
  on<T = any>(type: WebSocketMessageType, handler: WebSocketEventHandler<T>): () => void {
    if (!this.eventHandlers.has(type)) {
      this.eventHandlers.set(type, new Set())
    }

    this.eventHandlers.get(type)!.add(handler as WebSocketEventHandler)

    // Return unsubscribe function
    return () => {
      this.off(type, handler)
    }
  }

  /**
   * Unregister event handler
   */
  off<T = any>(type: WebSocketMessageType, handler: WebSocketEventHandler<T>): void {
    const handlers = this.eventHandlers.get(type)
    if (handlers) {
      handlers.delete(handler as WebSocketEventHandler)
      if (handlers.size === 0) {
        this.eventHandlers.delete(type)
      }
    }
  }

  /**
   * Register global event handlers
   */
  setGlobalHandlers(handlers: WebSocketEventHandlers): void {
    this.globalHandlers = { ...this.globalHandlers, ...handlers }
  }

  // ============================================================================
  // Reconnection Logic
  // ============================================================================

  private scheduleReconnect(): void {
    if (!this.config.reconnect) return

    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.log('Max reconnect attempts reached')
      this.state = 'error'
      return
    }

    this.reconnectAttempts++
    const delay = this.config.reconnectInterval * Math.min(this.reconnectAttempts, 5)

    this.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`)

    this.reconnectTimer = setTimeout(() => {
      this.connect()
    }, delay)
  }

  // ============================================================================
  // Heartbeat
  // ============================================================================

  private startHeartbeat(): void {
    this.clearHeartbeat()

    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        this.send('ping')
      }
    }, this.config.heartbeatInterval)
  }

  private clearHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  // ============================================================================
  // Utility
  // ============================================================================

  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.clearHeartbeat()
  }

  private log(...args: any[]): void {
    if (this.config.debug) {
      console.log('[WebSocket]', ...args)
    }
  }

  // ============================================================================
  // Cleanup
  // ============================================================================

  /**
   * Cleanup all resources
   */
  destroy(): void {
    this.disconnect()
    this.eventHandlers.clear()
    this.globalHandlers = {}
  }
}
