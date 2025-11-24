/**
 * Console WebSocket Control Client
 * Player-side WebSocket client for Hybrid Console Streaming architecture
 *
 * @features
 * - Singleton pattern for centralized WebSocket management
 * - Bidirectional communication with backend control endpoint
 * - Command listening (start_streaming, stop_streaming)
 * - Log batch sending (historical + real-time)
 * - Auto-reconnect with exponential backoff
 * - Heartbeat ping/pong for connection health
 * - Event emitter for console interceptor integration
 * - Buffer management for offline resilience
 *
 * @architecture
 * Player → WS → Backend Control → Redis Pub/Sub → Admin
 *
 * @events_emitted
 * - **start_streaming** - Backend requests log streaming
 * - **stop_streaming** - Backend stops log streaming
 * - **connected** - WebSocket connection established
 * - **disconnected** - WebSocket connection closed
 * - **error** - WebSocket error occurred
 */

import { SharedLogger } from '@shared/logger';
import { SharedDeviceState } from '@shared/device';
import { config } from '@shared/config';

/**
 * Console log entry format (matches backend DTO)
 */
export interface ConsoleLog {
  level: 'log' | 'info' | 'warn' | 'error' | 'debug';
  message: string;
  timestamp: string;
  stack?: string | null;
}

/**
 * Control command from backend
 */
export interface ControlCommand {
  command: 'start_streaming' | 'stop_streaming';
  data?: any;
  timestamp: string;
}

/**
 * Log message sent to backend
 */
export interface LogMessage {
  type: 'console_logs';
  logs: ConsoleLog[];
  logType: 'historical' | 'realtime';
}

/**
 * Event listener callback type
 */
type EventCallback = (data?: any) => void;

/**
 * Console WebSocket Client Class
 * Singleton pattern for centralized WebSocket management
 */
class ConsoleWebSocketClient {
  private ws: WebSocket | null = null;
  private deviceId: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectTimeout: number | null = null;
  private heartbeatInterval: number | null = null;
  private isManualClose = false;
  private eventListeners: Map<string, EventCallback[]> = new Map();
  private logBuffer: LogMessage[] = [];
  private readonly maxBufferSize = 100;

  // Reconnection backoff configuration (1s, 2s, 4s, 8s, 16s, max 30s)
  private readonly initialReconnectDelay = 1000;
  private readonly maxReconnectDelay = 30000;
  private readonly reconnectBackoffMultiplier = 2;

  // Heartbeat configuration (30s ping/pong)
  private readonly heartbeatIntervalMs = 30000;

  /**
   * Initialize WebSocket client
   */
  constructor() {
    SharedLogger.log('[ConsoleWebSocketClient] Initialized');
  }

  /**
   * Connect to backend control WebSocket
   */
  connect(): void {
    // Get device ID from SharedDeviceState
    this.deviceId = SharedDeviceState.getDeviceId();

    if (!this.deviceId) {
      SharedLogger.warn('[ConsoleWebSocketClient] No device ID found, cannot connect');
      return;
    }

    // Prevent duplicate connections
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      SharedLogger.warn('[ConsoleWebSocketClient] Already connected');
      return;
    }

    if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
      SharedLogger.warn('[ConsoleWebSocketClient] Connection already in progress');
      return;
    }

    // Build WebSocket URL
    const wsUrl = `${config.api.wsBaseURL}/api/v1/devices/${this.deviceId}/console/control`;

    SharedLogger.log(`[ConsoleWebSocketClient] Connecting to ${wsUrl}`);

    try {
      this.ws = new WebSocket(wsUrl);
      this.setupWebSocketHandlers();
    } catch (error) {
      SharedLogger.error('[ConsoleWebSocketClient] Failed to create WebSocket:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Setup WebSocket event handlers
   */
  private setupWebSocketHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      SharedLogger.success('[ConsoleWebSocketClient] Connected');
      this.reconnectAttempts = 0;
      this.isManualClose = false;
      this.startHeartbeat();
      this.flushBufferedLogs();
      this.emit('connected');
    };

    this.ws.onmessage = (event) => {
      this.handleMessage(event.data);
    };

    this.ws.onerror = (event) => {
      SharedLogger.error('[ConsoleWebSocketClient] WebSocket error:', event);
      this.emit('error', event);
    };

    this.ws.onclose = (event) => {
      SharedLogger.warn('[ConsoleWebSocketClient] Disconnected:', {
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean,
      });

      this.stopHeartbeat();
      this.emit('disconnected', { code: event.code, reason: event.reason });

      // Auto-reconnect if not manual close
      if (!this.isManualClose) {
        this.scheduleReconnect();
      }
    };
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(data: string): void {
    try {
      const message = JSON.parse(data);

      // Handle ping/pong heartbeat
      if (message.type === 'ping') {
        this.sendPong();
        return;
      }

      // Handle control commands
      if (message.command) {
        this.handleControlCommand(message as ControlCommand);
        return;
      }

      SharedLogger.log('[ConsoleWebSocketClient] Received message:', message);
    } catch (error) {
      SharedLogger.error('[ConsoleWebSocketClient] Failed to parse message:', error);
    }
  }

  /**
   * Handle control commands from backend
   */
  private handleControlCommand(command: ControlCommand): void {
    SharedLogger.log(`[ConsoleWebSocketClient] Received command: ${command.command}`, command);

    switch (command.command) {
      case 'start_streaming':
        this.emit('start_streaming', command.data);
        break;

      case 'stop_streaming':
        this.emit('stop_streaming', command.data);
        break;

      default:
        SharedLogger.warn('[ConsoleWebSocketClient] Unknown command:', command.command);
    }
  }

  /**
   * Send logs to backend
   * @param logs - Array of console logs
   * @param logType - Type of logs (historical or realtime)
   */
  sendLogs(logs: ConsoleLog[], logType: 'historical' | 'realtime'): void {
    const message: LogMessage = {
      type: 'console_logs',
      logs,
      logType,
    };

    // If WebSocket not connected, buffer the message
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.bufferLogMessage(message);
      SharedLogger.log(
        `[ConsoleWebSocketClient] WebSocket not connected, buffered ${logs.length} logs (${logType})`
      );
      return;
    }

    // Send immediately if connected
    try {
      this.ws.send(JSON.stringify(message));
      SharedLogger.log(`[ConsoleWebSocketClient] Sent ${logs.length} logs (${logType})`);
    } catch (error) {
      SharedLogger.error('[ConsoleWebSocketClient] Failed to send logs:', error);
      this.bufferLogMessage(message);
    }
  }

  /**
   * Buffer log message for later sending
   */
  private bufferLogMessage(message: LogMessage): void {
    this.logBuffer.push(message);

    // Keep buffer size manageable (FIFO)
    if (this.logBuffer.length > this.maxBufferSize) {
      const removed = this.logBuffer.shift();
      SharedLogger.warn(
        `[ConsoleWebSocketClient] Buffer full, removed oldest batch (${removed?.logs.length} logs)`
      );
    }
  }

  /**
   * Flush buffered logs on reconnect
   */
  private flushBufferedLogs(): void {
    if (this.logBuffer.length === 0) return;

    SharedLogger.log(`[ConsoleWebSocketClient] Flushing ${this.logBuffer.length} buffered batches`);

    const bufferedMessages = [...this.logBuffer];
    this.logBuffer = [];

    bufferedMessages.forEach((message) => {
      this.sendLogs(message.logs, message.logType);
    });
  }

  /**
   * Send pong response to heartbeat ping
   */
  private sendPong(): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

    try {
      this.ws.send(JSON.stringify({ type: 'pong' }));
      SharedLogger.debug('[ConsoleWebSocketClient] Sent pong');
    } catch (error) {
      SharedLogger.error('[ConsoleWebSocketClient] Failed to send pong:', error);
    }
  }

  /**
   * Start heartbeat ping/pong
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();

    this.heartbeatInterval = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.sendPong();
      }
    }, this.heartbeatIntervalMs);

    SharedLogger.log('[ConsoleWebSocketClient] Heartbeat started');
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval !== null) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
      SharedLogger.log('[ConsoleWebSocketClient] Heartbeat stopped');
    }
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      SharedLogger.error(
        `[ConsoleWebSocketClient] Max reconnect attempts (${this.maxReconnectAttempts}) reached, giving up`
      );
      return;
    }

    // Calculate backoff delay (exponential: 1s, 2s, 4s, 8s, 16s, max 30s)
    const delay = Math.min(
      this.initialReconnectDelay * Math.pow(this.reconnectBackoffMultiplier, this.reconnectAttempts),
      this.maxReconnectDelay
    );

    this.reconnectAttempts++;

    SharedLogger.log(
      `[ConsoleWebSocketClient] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    );

    this.reconnectTimeout = window.setTimeout(() => {
      this.reconnectTimeout = null;
      this.connect();
    }, delay);
  }

  /**
   * Cancel scheduled reconnection
   */
  private cancelReconnect(): void {
    if (this.reconnectTimeout !== null) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
      SharedLogger.log('[ConsoleWebSocketClient] Reconnect cancelled');
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    this.isManualClose = true;
    this.cancelReconnect();
    this.stopHeartbeat();

    if (this.ws) {
      try {
        this.ws.close(1000, 'Manual disconnect');
        SharedLogger.log('[ConsoleWebSocketClient] Manual disconnect');
      } catch (error) {
        SharedLogger.error('[ConsoleWebSocketClient] Error during disconnect:', error);
      }

      this.ws = null;
    }
  }

  /**
   * Register event listener
   */
  on(event: string, callback: EventCallback): void {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }

    this.eventListeners.get(event)!.push(callback);
    SharedLogger.debug(`[ConsoleWebSocketClient] Event listener registered: ${event}`);
  }

  /**
   * Unregister event listener
   */
  off(event: string, callback: EventCallback): void {
    const listeners = this.eventListeners.get(event);
    if (!listeners) return;

    const index = listeners.indexOf(callback);
    if (index !== -1) {
      listeners.splice(index, 1);
      SharedLogger.debug(`[ConsoleWebSocketClient] Event listener removed: ${event}`);
    }
  }

  /**
   * Emit event to all listeners
   */
  private emit(event: string, data?: any): void {
    const listeners = this.eventListeners.get(event);
    if (!listeners || listeners.length === 0) return;

    SharedLogger.debug(`[ConsoleWebSocketClient] Emitting event: ${event}`, data);

    listeners.forEach((callback) => {
      try {
        callback(data);
      } catch (error) {
        SharedLogger.error(`[ConsoleWebSocketClient] Error in event listener (${event}):`, error);
      }
    });
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Get current connection state
   */
  getState(): string {
    if (!this.ws) return 'DISCONNECTED';

    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'CONNECTING';
      case WebSocket.OPEN:
        return 'CONNECTED';
      case WebSocket.CLOSING:
        return 'CLOSING';
      case WebSocket.CLOSED:
        return 'CLOSED';
      default:
        return 'UNKNOWN';
    }
  }

  /**
   * Get buffer statistics
   */
  getBufferStats(): { size: number; maxSize: number; totalLogs: number } {
    const totalLogs = this.logBuffer.reduce((sum, msg) => sum + msg.logs.length, 0);

    return {
      size: this.logBuffer.length,
      maxSize: this.maxBufferSize,
      totalLogs,
    };
  }

  /**
   * Reset reconnection state (for manual reconnect)
   */
  resetReconnection(): void {
    this.reconnectAttempts = 0;
    this.isManualClose = false;
    SharedLogger.log('[ConsoleWebSocketClient] Reconnection state reset');
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    SharedLogger.log('[ConsoleWebSocketClient] Destroying...');

    this.disconnect();
    this.eventListeners.clear();
    this.logBuffer = [];
  }
}

// Export singleton instance
export const consoleWebSocketClient = new ConsoleWebSocketClient();

// Auto-connect when device is activated
if (SharedDeviceState.isActivated()) {
  consoleWebSocketClient.connect();
}
