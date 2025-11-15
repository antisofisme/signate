/**
 * Shell Connection Status Monitor
 * Monitors network connection and backend availability
 *
 * @features
 * - Monitor navigator.onLine status
 * - Periodic ping to backend API
 * - Emit CONNECTION_ONLINE/OFFLINE events
 * - Show connection status indicator
 * - Auto-reconnect when connection restored
 * - Exponential backoff for ping retries
 */

import { SharedLogger } from '@shared/logger';
import { SharedEventBus, EventNames } from '@shared/events/shared-event-bus';
import { config } from '@shared/config';
import { ConnectionLogger } from '@shared/services/connection-logger';
import { ServiceRegistry } from '@shared/services/service-registry';

/**
 * Connection status
 */
export type ConnectionStatus = 'online' | 'offline' | 'checking';

/**
 * Connection check result
 */
export interface ConnectionCheckResult {
  isOnline: boolean;
  latency?: number; // milliseconds
  timestamp: string;
}

/**
 * Shell Connection Status Class
 * Singleton pattern for connection monitoring
 */
class ShellConnectionStatusClass {
  private initialized = false;
  private status: ConnectionStatus = 'checking';
  private wasOnline = true;
  private pingInterval: number | null = null;
  private pingTimeout: number | null = null;
  private retryCount = 0;
  private readonly maxRetries = 5;
  private readonly basePingInterval = 30000; // 30 seconds
  private readonly pingTimeoutDuration = 10000; // 10 seconds

  /**
   * Initialize connection status monitor
   */
  init(): void {
    if (this.initialized) {
      SharedLogger.warn('[ConnectionStatus] Already initialized');
      return;
    }

    this.initialized = true;

    // Check initial status
    this.status = navigator.onLine ? 'online' : 'offline';
    this.wasOnline = navigator.onLine;

    // Listen to browser events
    window.addEventListener('online', this.handleBrowserOnline);
    window.addEventListener('offline', this.handleBrowserOffline);

    // Start periodic ping
    this.startPing();

    // Do immediate check
    void this.checkConnection();

    SharedLogger.log('[ConnectionStatus] Initialized - Initial status:', this.status);
  }

  /**
   * Handle browser online event
   */
  private handleBrowserOnline = (): void => {
    SharedLogger.log('[ConnectionStatus] Browser reports online');
    this.status = 'checking';

    // Get network information
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;

    // Log network online event with detailed info
    ConnectionLogger.log({
      eventType: 'network',
      status: 'online',
      metadata: {
        event: 'browser_online',
        connectionType: connection?.type || 'unknown',
        effectiveType: connection?.effectiveType || 'unknown',
        downlink: connection?.downlink || 0,
        rtt: connection?.rtt || 0,
        saveData: connection?.saveData || false
      }
    }).catch(err => SharedLogger.error('[ConnectionStatus] Failed to log:', err));

    void this.checkConnection();
  };

  /**
   * Handle browser offline event
   */
  private handleBrowserOffline = (): void => {
    SharedLogger.warn('[ConnectionStatus] Browser reports offline');

    // Get network information
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;

    // Log network offline event with detailed info
    ConnectionLogger.log({
      eventType: 'network',
      status: 'offline',
      errorMessage: 'Browser network disconnected',
      metadata: {
        event: 'browser_offline',
        connectionType: connection?.type || 'unknown',
        effectiveType: connection?.effectiveType || 'unknown',
        downlink: connection?.downlink || 0,
        rtt: connection?.rtt || 0,
        saveData: connection?.saveData || false
      }
    }).catch(err => SharedLogger.error('[ConnectionStatus] Failed to log:', err));

    this.setOffline();
  };

  /**
   * Start periodic ping
   */
  private startPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }

    const interval = this.getPingInterval();

    this.pingInterval = window.setInterval(() => {
      void this.checkConnection();
    }, interval);

    SharedLogger.log(`[ConnectionStatus] Ping interval started: ${interval}ms`);
  }

  /**
   * Get ping interval with exponential backoff
   */
  private getPingInterval(): number {
    if (this.status === 'offline') {
      // Exponential backoff when offline: 30s, 60s, 120s, 240s, 480s
      const backoff = Math.min(Math.pow(2, this.retryCount), 16);
      return this.basePingInterval * backoff;
    }
    return this.basePingInterval;
  }

  /**
   * Check connection to backend
   */
  async checkConnection(): Promise<ConnectionCheckResult> {
    // Skip if browser is offline
    if (!navigator.onLine) {
      this.setOffline();
      return { isOnline: false, timestamp: new Date().toISOString() };
    }

    const startTime = Date.now();

    try {
      // Ping health endpoint with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.pingTimeoutDuration);

      const response = await fetch(`${config.api.baseURL}/health`, {
        method: 'GET',
        signal: controller.signal,
        cache: 'no-cache',
      });

      clearTimeout(timeoutId);

      const latency = Date.now() - startTime;

      if (response.ok) {
        // Log successful ping check
        ConnectionLogger.log({
          eventType: 'server',
          status: 'connected',
          latencyMs: latency,
          metadata: {
            event: 'health_check',
            timestamp: new Date().toISOString(),
            endpoint: '/health',
            httpStatus: response.status,
            responseTime: `${latency}ms`
          }
        }).catch(err => SharedLogger.error('[ConnectionStatus] Failed to log:', err));

        this.setOnline(latency);
        return { isOnline: true, latency, timestamp: new Date().toISOString() };
      } else {
        SharedLogger.warn('[ConnectionStatus] Backend returned error:', response.status);

        // Log server error
        ConnectionLogger.log({
          eventType: 'server',
          status: 'disconnected',
          errorMessage: `Server returned status ${response.status}`,
          metadata: {
            event: 'health_check_failed',
            endpoint: '/health',
            statusCode: response.status,
            httpStatus: response.status,
            errorCode: `HTTP_${response.status}`
          }
        }).catch(err => SharedLogger.error('[ConnectionStatus] Failed to log:', err));

        this.setOffline();
        return { isOnline: false, timestamp: new Date().toISOString() };
      }
    } catch (error) {
      // Only log first failure to avoid console spam
      if (this.retryCount === 0) {
        SharedLogger.warn('[ConnectionStatus] Backend unreachable (will retry silently)');
      }
      this.setOffline();
      return { isOnline: false, timestamp: new Date().toISOString() };
    }
  }

  /**
   * Set status to online
   */
  private setOnline(latency?: number): void {
    const wasOffline = this.status === 'offline';

    this.status = 'online';
    this.retryCount = 0;

    if (wasOffline) {
      // Connection restored
      SharedEventBus.emit(EventNames.CONNECTION_RESTORED, { latency });
      SharedLogger.log('[ConnectionStatus] Connection restored - Latency:', latency);

      // Log connection restored event
      ConnectionLogger.log({
        eventType: 'server',
        status: 'connected',
        latencyMs: latency,
        metadata: {
          event: 'connection_restored',
          endpoint: '/health',
          httpStatus: 200,
          responseTime: `${latency}ms`
        }
      }).catch(err => SharedLogger.error('[ConnectionStatus] Failed to log:', err));
    } else if (!this.wasOnline) {
      // First time online
      SharedEventBus.emit(EventNames.CONNECTION_ONLINE, { latency });
      SharedLogger.log('[ConnectionStatus] Connection online - Latency:', latency);

      // Log connection online event
      ConnectionLogger.log({
        eventType: 'server',
        status: 'connected',
        latencyMs: latency,
        metadata: {
          event: 'connection_online',
          endpoint: '/health',
          httpStatus: 200,
          responseTime: `${latency}ms`
        }
      }).catch(err => SharedLogger.error('[ConnectionStatus] Failed to log:', err));
    }

    this.wasOnline = true;

    // Reset ping interval
    this.startPing();
  }

  /**
   * Set status to offline
   */
  private setOffline(): void {
    const wasOnline = this.status === 'online';

    this.status = 'offline';
    this.retryCount = Math.min(this.retryCount + 1, this.maxRetries);

    if (wasOnline) {
      // Connection lost
      SharedEventBus.emit(EventNames.CONNECTION_LOST);
      SharedLogger.warn('[ConnectionStatus] Connection lost');

      // Log connection lost event
      ConnectionLogger.log({
        eventType: 'server',
        status: 'disconnected',
        errorMessage: 'Connection lost to backend server',
        metadata: { event: 'connection_lost', retryCount: this.retryCount }
      }).catch(err => SharedLogger.error('[ConnectionStatus] Failed to log:', err));
    } else if (this.wasOnline) {
      // First time offline
      SharedEventBus.emit(EventNames.CONNECTION_OFFLINE);
      SharedLogger.warn('[ConnectionStatus] Connection offline');

      // Log connection offline event
      ConnectionLogger.log({
        eventType: 'server',
        status: 'disconnected',
        errorMessage: 'Server connection unavailable',
        metadata: { event: 'connection_offline', retryCount: this.retryCount }
      }).catch(err => SharedLogger.error('[ConnectionStatus] Failed to log:', err));
    }

    this.wasOnline = false;

    // Restart ping with backoff
    this.startPing();
  }

  /**
   * Get current status
   */
  getStatus(): ConnectionStatus {
    return this.status;
  }

  /**
   * Check if online
   */
  isOnline(): boolean {
    return this.status === 'online';
  }

  /**
   * Check if offline
   */
  isOffline(): boolean {
    return this.status === 'offline';
  }

  /**
   * Get retry count
   */
  getRetryCount(): number {
    return this.retryCount;
  }

  /**
   * Force connection check
   */
  async forceCheck(): Promise<ConnectionCheckResult> {
    SharedLogger.log('[ConnectionStatus] Force checking connection...');
    return this.checkConnection();
  }

  /**
   * Reset retry count (useful after manual intervention)
   */
  resetRetries(): void {
    this.retryCount = 0;
    this.startPing();
    SharedLogger.log('[ConnectionStatus] Retry count reset');
  }

  /**
   * Get connection info (for debugging)
   */
  getInfo(): {
    status: ConnectionStatus;
    retryCount: number;
    browserOnline: boolean;
    wasOnline: boolean;
  } {
    return {
      status: this.status,
      retryCount: this.retryCount,
      browserOnline: navigator.onLine,
      wasOnline: this.wasOnline,
    };
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    window.removeEventListener('online', this.handleBrowserOnline);
    window.removeEventListener('offline', this.handleBrowserOffline);

    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }

    if (this.pingTimeout) {
      clearTimeout(this.pingTimeout);
      this.pingTimeout = null;
    }

    this.initialized = false;
    SharedLogger.log('[ConnectionStatus] Destroyed');
  }
}

// Export singleton instance
export const ShellConnectionStatus = new ShellConnectionStatusClass();

// Make available globally for compatibility
declare global {
  interface Window {
    ShellConnectionStatus: typeof ShellConnectionStatus;
  }
}

if (typeof window !== 'undefined') {
  // Register to ServiceRegistry
  ServiceRegistry.register('ShellConnectionStatus', ShellConnectionStatus);
}

// Auto-initialize when module is imported
ShellConnectionStatus.init();
