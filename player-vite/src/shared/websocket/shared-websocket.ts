/**
 * Shared WebSocket Client
 * Real-time bidirectional communication with backend
 *
 * @features
 * - Auto-reconnection with exponential backoff
 * - Heartbeat/ping-pong mechanism
 * - Message queue for offline messages
 * - Event-based message handling via EventBus
 * - Type-safe message protocol
 */

import { config } from '@shared/config';
import { SharedLogger } from '@shared/logger';
import { SharedDeviceState } from '@shared/device';
import { SharedEventBus, EventNames } from '@shared/events/shared-event-bus';
import { ServiceRegistry } from '@shared/services/service-registry';

/**
 * WebSocket message types
 */
export enum WSMessageType {
  // Control messages
  PING = 'ping',
  PONG = 'pong',
  AUTH = 'auth',

  // Command messages
  COMMAND = 'command',
  COMMAND_RESPONSE = 'command_response',

  // Playlist messages (legacy format)
  PLAYLIST_UPDATE = 'playlist_update',
  CONTENT_UPDATE = 'content_update',

  // Playlist messages (backend colon format)
  PLAYLIST_ASSIGNED = 'playlist:assigned',
  PLAYLIST_UNASSIGNED = 'playlist:unassigned',
  CONTENT_UPDATED = 'content:updated',

  // Device messages
  DEVICE_STATUS = 'device_status',
  DEVICE_CONFIG = 'device_config',
  DEVICE_COMMAND = 'device:command',

  // Player messages
  PLAYER_STATE = 'player_state',
  PLAYER_CONTROL = 'player_control',
}

/**
 * WebSocket message interface
 */
export interface WSMessage<T = any> {
  type: WSMessageType;
  data: T;
  timestamp?: string;
  id?: string;
}

/**
 * WebSocket connection state
 */
export enum WSState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error',
}

/**
 * Shared WebSocket Class
 * Singleton pattern for WebSocket management
 */
class SharedWebSocketClass {
  private ws: WebSocket | null = null;
  private state: WSState = WSState.DISCONNECTED;
  private reconnectAttempts = 0;
  private readonly maxReconnectAttempts = 10;
  private reconnectTimeout: number | null = null;
  private pingInterval: number | null = null;
  private readonly pingIntervalMs = 30000; // 30 seconds
  private messageQueue: WSMessage[] = [];
  private readonly maxQueueSize = 100;

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    const deviceId = SharedDeviceState.getDeviceId();
    const deviceToken = SharedDeviceState.getDeviceToken();

    if (!deviceId) {
      SharedLogger.error('[WebSocket] Cannot connect - no device_id');
      return;
    }

    // Skip WebSocket if no device token (optional feature)
    if (!deviceToken) {
      SharedLogger.log('[WebSocket] No device token - skipping WebSocket connection (optional feature)');
      return;
    }

    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      SharedLogger.warn('[WebSocket] Already connected or connecting');
      return;
    }

    try {
      this.state = WSState.CONNECTING;
      SharedLogger.log('[WebSocket] Connecting to:', config.api.wsBaseURL);

      // Build WebSocket URL with auth params (backend router mounted at /api)
      // Note: device_id is extracted from JWT token, not from URL path
      const wsUrl = `${config.api.wsBaseURL}/api/ws/device?token=${deviceToken}`;

      this.ws = new WebSocket(wsUrl);

      // Event handlers
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
    } catch (error) {
      SharedLogger.error('[WebSocket] Connection error:', error);
      this.state = WSState.ERROR;
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    SharedLogger.log('[WebSocket] Disconnecting...');

    // Stop ping interval
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }

    // Stop reconnect timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Close WebSocket
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.state = WSState.DISCONNECTED;
    this.reconnectAttempts = 0;

    // Emit disconnected event
    SharedEventBus.emit(EventNames.WS_DISCONNECTED);
  }

  /**
   * Send message to server
   */
  send<T = any>(type: WSMessageType, data: T): void {
    const message: WSMessage<T> = {
      type,
      data,
      timestamp: new Date().toISOString(),
      id: this.generateMessageId(),
    };

    if (this.state === WSState.CONNECTED && this.ws) {
      try {
        this.ws.send(JSON.stringify(message));
        SharedLogger.log(`[WebSocket] Sent '${type}':`, data);
      } catch (error) {
        SharedLogger.error(`[WebSocket] Failed to send '${type}':`, error);
        this.queueMessage(message);
      }
    } else {
      SharedLogger.warn(`[WebSocket] Not connected, queuing message '${type}'`);
      this.queueMessage(message);
    }
  }

  /**
   * Handle WebSocket open event
   */
  private handleOpen(): void {
    SharedLogger.log('[WebSocket] ✅ Connected');
    this.state = WSState.CONNECTED;
    this.reconnectAttempts = 0;

    // Send auth message
    this.sendAuth();

    // Start ping interval
    this.startPing();

    // Process queued messages
    this.processQueue();

    // Emit connected event
    SharedEventBus.emit(EventNames.WS_CONNECTED);
  }

  /**
   * Handle WebSocket message event
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WSMessage = JSON.parse(event.data);
      SharedLogger.log(`[WebSocket] Received '${message.type}':`, message.data);

      // Handle pong
      if (message.type === WSMessageType.PONG) {
        SharedLogger.log('[WebSocket] Pong received');
        return;
      }

      // Emit message event to EventBus
      SharedEventBus.emit(EventNames.WS_MESSAGE, message);

      // Handle specific message types
      this.handleMessageType(message);
    } catch (error) {
      SharedLogger.error('[WebSocket] Failed to parse message:', error);
    }
  }

  /**
   * Handle WebSocket error event
   */
  private handleError(event: Event): void {
    SharedLogger.error('[WebSocket] Error:', event);
    this.state = WSState.ERROR;
    SharedEventBus.emit(EventNames.WS_ERROR, event);
  }

  /**
   * Handle WebSocket close event
   */
  private handleClose(event: CloseEvent): void {
    SharedLogger.warn('[WebSocket] Disconnected:', {
      code: event.code,
      reason: event.reason,
      wasClean: event.wasClean,
    });

    this.state = WSState.DISCONNECTED;

    // Stop ping interval
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }

    // Emit disconnected event
    SharedEventBus.emit(EventNames.WS_DISCONNECTED, { code: event.code, reason: event.reason });

    // Attempt reconnection if not a clean close
    if (!event.wasClean) {
      this.scheduleReconnect();
    }
  }

  /**
   * Handle specific message types
   */
  private handleMessageType(message: WSMessage): void {
    // Handle both enum values and raw string types from backend
    const msgType = message.type as string;

    switch (msgType) {
      case WSMessageType.COMMAND:
      case 'device:command':
        SharedEventBus.emit(EventNames.COMMAND_RECEIVED, message.data);
        break;

      // Legacy format
      case WSMessageType.PLAYLIST_UPDATE:
      case WSMessageType.CONTENT_UPDATE:
        SharedEventBus.emit(EventNames.PLAYLIST_CHANGED, message.data);
        break;

      // Backend colon format - playlist/content assignment triggers playlist reload
      case WSMessageType.PLAYLIST_ASSIGNED:
      case 'playlist:assigned':
      case WSMessageType.PLAYLIST_UNASSIGNED:
      case 'playlist:unassigned':
      case WSMessageType.CONTENT_UPDATED:
      case 'content:updated':
        SharedLogger.log('[WebSocket] 🔄 Playlist/Content changed - triggering reload');
        SharedEventBus.emit(EventNames.PLAYLIST_CHANGED, message.data);
        break;

      // Schedule events - real-time schedule activation/deactivation
      case 'SCHEDULE_ACTIVATED':
      case 'schedule:activated':
        SharedLogger.log('[WebSocket] 📅 Schedule activated - triggering sync');
        SharedEventBus.emit('ws:SCHEDULE_ACTIVATED', message.data);
        break;

      case 'SCHEDULE_DEACTIVATED':
      case 'schedule:deactivated':
        SharedLogger.log('[WebSocket] 📅 Schedule deactivated - triggering sync');
        SharedEventBus.emit('ws:SCHEDULE_DEACTIVATED', message.data);
        break;

      case WSMessageType.PLAYER_CONTROL:
        this.handlePlayerControl(message.data);
        break;

      // Device status messages (info only, emitted for other services to react)
      case 'device:online':
      case 'device:offline':
        SharedLogger.log(`[WebSocket] 📡 Device status: ${msgType}`);
        SharedEventBus.emit('device:status', { type: msgType, data: message.data });
        break;

      // System notifications (ping, keepalive, etc.) - acknowledge silently
      case 'system:notification':
        // Handle ping/pong from backend keepalive
        if (message.data?.type === 'ping') {
          SharedLogger.log('[WebSocket] 🏓 System ping received');
        }
        break;

      default:
        SharedLogger.log(`[WebSocket] Unhandled message type: ${msgType}`);
    }
  }

  /**
   * Handle player control messages
   */
  private handlePlayerControl(data: any): void {
    const { action } = data;

    switch (action) {
      case 'play':
        SharedEventBus.emit(EventNames.PLAYER_PLAY);
        break;
      case 'pause':
        SharedEventBus.emit(EventNames.PLAYER_PAUSE);
        break;
      case 'stop':
        SharedEventBus.emit(EventNames.PLAYER_STOP);
        break;
      case 'next':
        SharedEventBus.emit(EventNames.PLAYER_NEXT);
        break;
      case 'previous':
        SharedEventBus.emit(EventNames.PLAYER_PREVIOUS);
        break;
      default:
        SharedLogger.warn(`[WebSocket] Unknown player control: ${action}`);
    }
  }

  /**
   * Send auth message
   */
  private sendAuth(): void {
    const deviceId = SharedDeviceState.getDeviceId();
    const deviceToken = SharedDeviceState.getDeviceToken();

    this.send(WSMessageType.AUTH, {
      device_id: deviceId,
      token: deviceToken,
    });
  }

  /**
   * Start ping interval
   */
  private startPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }

    this.pingInterval = window.setInterval(() => {
      if (this.state === WSState.CONNECTED) {
        this.send(WSMessageType.PING, {});
      }
    }, this.pingIntervalMs);
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      SharedLogger.error(`[WebSocket] Max reconnect attempts (${this.maxReconnectAttempts}) reached`);
      return;
    }

    this.reconnectAttempts++;
    this.state = WSState.RECONNECTING;

    // Exponential backoff: 1s, 2s, 4s, 8s, 16s, 32s, ...
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 32000);

    SharedLogger.log(`[WebSocket] Reconnecting in ${delay / 1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    this.reconnectTimeout = window.setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Queue message for later sending
   */
  private queueMessage(message: WSMessage): void {
    if (this.messageQueue.length >= this.maxQueueSize) {
      SharedLogger.warn('[WebSocket] Message queue full, dropping oldest message');
      this.messageQueue.shift();
    }

    this.messageQueue.push(message);
    SharedLogger.log(`[WebSocket] Queued message (queue size: ${this.messageQueue.length})`);
  }

  /**
   * Process queued messages
   */
  private processQueue(): void {
    if (this.messageQueue.length === 0) return;

    SharedLogger.log(`[WebSocket] Processing ${this.messageQueue.length} queued message(s)`);

    while (this.messageQueue.length > 0 && this.state === WSState.CONNECTED) {
      const message = this.messageQueue.shift();
      if (message && this.ws) {
        try {
          this.ws.send(JSON.stringify(message));
        } catch (error) {
          SharedLogger.error('[WebSocket] Failed to send queued message:', error);
        }
      }
    }
  }

  /**
   * Generate unique message ID
   */
  private generateMessageId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get current state
   */
  getState(): WSState {
    return this.state;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.state === WSState.CONNECTED && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get queue size
   */
  getQueueSize(): number {
    return this.messageQueue.length;
  }
}

// Export singleton instance
export const SharedWebSocket = new SharedWebSocketClass();

// Make available globally for compatibility
if (typeof window !== 'undefined') {
  // Register to ServiceRegistry
  ServiceRegistry.register('SharedWebSocket', SharedWebSocket);
}
