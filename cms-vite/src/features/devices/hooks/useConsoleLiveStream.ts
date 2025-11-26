/**
 * Console Live Stream Hook
 *
 * WebSocket-based live console log streaming from device to CMS
 * - Subscribes when modal opens
 * - Unsubscribes when modal closes
 * - Receives historical logs (all logs since page load) on first connect
 * - Receives real-time logs continuously after history loaded
 * - Real-time updates (<100ms latency)
 * - Auto-reconnect on disconnect with exponential backoff
 *
 * Event Types:
 * - console.subscribed: Subscription confirmation
 * - console.historical: Historical logs (sent once, REPLACES existing)
 * - device.console_log: Real-time logs (continuous, APPENDS to existing)
 *   - Can include logType metadata: 'historical' | 'realtime'
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { useAuthStore } from '@/lib/stores/authStore';
import { logger } from '@/shared/utils/logger';
import { getSmartWebSocketUrl } from '@/lib/config/network-detector';

interface ConsoleLog {
  level: 'log' | 'info' | 'warn' | 'error' | 'debug';
  message: string;
  timestamp: string;
  stack?: string;
}

interface ConsoleLogEvent {
  event: 'console.subscribed' | 'console.historical' | 'device.console_log';
  data: {
    device_id: number;
    logs?: ConsoleLog[];
    logType?: 'historical' | 'realtime';
    message?: string;
  };
  timestamp: string;
}

interface UseConsoleLiveStreamOptions {
  deviceId: number;
  enabled?: boolean;
  maxLogs?: number;
  onError?: (error: Error) => void;
}

interface UseConsoleLiveStreamReturn {
  logs: ConsoleLog[];
  isConnected: boolean;
  isConnecting: boolean;
  isLoadingHistory: boolean;
  error: Error | null;
  clearLogs: () => void;
  reconnect: () => void;
}

/**
 * Hook to stream console logs live from device via WebSocket
 */
export function useConsoleLiveStream({
  deviceId,
  enabled = true,
  maxLogs = 1000,
  onError,
}: UseConsoleLiveStreamOptions): UseConsoleLiveStreamReturn {
  const { user } = useAuthStore();
  const [logs, setLogs] = useState<ConsoleLog[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef(0);

  /**
   * Clear all logs
   */
  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    if (!enabled || !user?.id || !deviceId) return;

    // Already connected or connecting
    if (wsRef.current?.readyState === WebSocket.OPEN || isConnecting) {
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      // WebSocket URL using smart network detection
      const wsBaseUrl = getSmartWebSocketUrl();
      const wsUrl = `${wsBaseUrl}/api/v1/devices/${deviceId}/console/stream?user_id=${user.id}`;

      logger.debug('[ConsoleStream] Connecting to:', wsUrl);

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        logger.debug('[ConsoleStream] Connected to device', deviceId);
        setIsConnected(true);
        setIsConnecting(false);
        setIsLoadingHistory(true); // Start loading history
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const message: ConsoleLogEvent = JSON.parse(event.data);

          // DEBUG: Log ALL messages received
          logger.debug('[ConsoleStream] Message received:', message);

          if (message.event === 'console.subscribed') {
            logger.debug('[ConsoleStream] Subscription confirmed:', message.data.message);
          }
          // Historical logs (sent once on subscribe) - REPLACE existing logs
          else if (message.event === 'console.historical') {
            const historicalLogs = message.data.logs || [];
            logger.debug('[ConsoleStream] Historical logs received:', historicalLogs.length);
            setLogs(historicalLogs.slice(-maxLogs)); // REPLACE, not append
            setIsLoadingHistory(false);
          }
          // Real-time logs (continuous stream) - APPEND to existing logs
          else if (message.event === 'device.console_log' && message.data.logs) {
            const logType = message.data.logType || 'realtime';

            if (logType === 'historical') {
              // Alternative handling if backend uses same event with metadata
              logger.debug('[ConsoleStream] Historical logs (via logType):', message.data.logs.length);
              setLogs(message.data.logs.slice(-maxLogs)); // REPLACE
              setIsLoadingHistory(false);
            } else {
              // Real-time logs
              logger.debug('[ConsoleStream] Real-time log received:', message.data.logs.length);
              setLogs((prev) => {
                const newLogs = [...prev, ...message.data.logs!];
                return newLogs.slice(-maxLogs); // Keep last maxLogs
              });
            }
          }
          else {
            logger.warn(`[ConsoleStream] Unhandled message event: ${message.event}`, message);
          }
        } catch (err) {
          logger.error('[ConsoleStream] Failed to parse message:', err);
        }
      };

      ws.onerror = (event) => {
        logger.error('[ConsoleStream] WebSocket error:', event);
        const err = new Error('WebSocket connection error');
        setError(err);
        if (onError) onError(err);
      };

      ws.onclose = (event) => {
        logger.debug(`[ConsoleStream] Disconnected: ${event.code} ${event.reason}`);
        setIsConnected(false);
        setIsConnecting(false);
        setIsLoadingHistory(false); // Reset loading state on disconnect

        // Auto-reconnect with exponential backoff
        if (enabled && reconnectAttemptsRef.current < 5) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          logger.debug(`[ConsoleStream] Reconnecting in ${delay}ms...`);

          reconnectTimeoutRef.current = window.setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      logger.error('[ConsoleStream] Failed to create WebSocket:', err);
      const error = err instanceof Error ? err : new Error('Failed to connect');
      setError(error);
      setIsConnecting(false);
      if (onError) onError(error);
    }
  }, [deviceId, enabled, user?.id, maxLogs, isConnecting, onError]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
    setIsLoadingHistory(false);
  }, []);

  /**
   * Manual reconnect
   */
  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttemptsRef.current = 0;
    connect();
  }, [disconnect, connect]);

  /**
   * Effect: Connect when enabled, disconnect when disabled
   */
  useEffect(() => {
    // Guard against React StrictMode double-invocation
    if (enabled && deviceId && user?.id) {
      // Only connect if not already connected or connecting
      if (wsRef.current?.readyState === WebSocket.OPEN || isConnecting) {
        logger.debug('[ConsoleStream] Already connected/connecting, skipping');
        return;
      }
      connect();
    } else {
      disconnect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [enabled, deviceId, user?.id]); // Don't include connect/disconnect to avoid loops

  return {
    logs,
    isConnected,
    isConnecting,
    isLoadingHistory,
    error,
    clearLogs,
    reconnect,
  };
}
