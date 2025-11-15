/**
 * Shared Event Bus
 * Global event system for inter-component communication
 *
 * @features
 * - Type-safe event emission and subscription
 * - Wildcard event listeners
 * - Once listeners (auto-unsubscribe after first event)
 * - Event history for debugging
 * - Namespace support for scoped events
 */

import { SharedLogger } from '@shared/logger';
import { ServiceRegistry } from '@shared/services/service-registry';

/**
 * Event handler function type
 */
type EventHandler<T = any> = (data: T) => void;

/**
 * Event subscription type
 */
interface EventSubscription {
  event: string;
  handler: EventHandler;
  once: boolean;
  namespace?: string;
}

/**
 * Event history entry
 */
interface EventHistoryEntry {
  event: string;
  data: any;
  timestamp: string;
}

/**
 * Shared Event Bus Class
 * Singleton pattern for global event management
 */
class SharedEventBusClass {
  private listeners: Map<string, EventSubscription[]> = new Map();
  private history: EventHistoryEntry[] = [];
  private readonly maxHistorySize = 100;

  /**
   * Subscribe to an event
   */
  on<T = any>(event: string, handler: EventHandler<T>, namespace?: string): () => void {
    const subscription: EventSubscription = {
      event,
      handler,
      once: false,
      namespace,
    };

    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }

    this.listeners.get(event)!.push(subscription);

    SharedLogger.log(`[EventBus] Subscribed to '${event}'${namespace ? ` (namespace: ${namespace})` : ''}`);

    // Return unsubscribe function
    return () => this.off(event, handler);
  }

  /**
   * Subscribe to an event (fires once then auto-unsubscribes)
   */
  once<T = any>(event: string, handler: EventHandler<T>, namespace?: string): () => void {
    const subscription: EventSubscription = {
      event,
      handler,
      once: true,
      namespace,
    };

    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }

    this.listeners.get(event)!.push(subscription);

    SharedLogger.log(`[EventBus] Subscribed to '${event}' (once)${namespace ? ` (namespace: ${namespace})` : ''}`);

    // Return unsubscribe function
    return () => this.off(event, handler);
  }

  /**
   * Unsubscribe from an event
   */
  off(event: string, handler: EventHandler): void {
    const subscriptions = this.listeners.get(event);
    if (!subscriptions) return;

    const index = subscriptions.findIndex((sub) => sub.handler === handler);
    if (index !== -1) {
      subscriptions.splice(index, 1);
      SharedLogger.log(`[EventBus] Unsubscribed from '${event}'`);

      // Clean up empty listener arrays
      if (subscriptions.length === 0) {
        this.listeners.delete(event);
      }
    }
  }

  /**
   * Emit an event
   */
  emit<T = any>(event: string, data?: T): void {
    // Add to history
    this.addToHistory(event, data);

    // Get direct listeners
    const subscriptions = this.listeners.get(event) || [];

    // Get wildcard listeners (e.g., 'player:*' matches 'player:play', 'player:pause', etc.)
    const wildcardListeners = this.getWildcardListeners(event);

    // Combine all listeners
    const allListeners = [...subscriptions, ...wildcardListeners];

    if (allListeners.length === 0) {
      SharedLogger.log(`[EventBus] Emitted '${event}' (no listeners)`, data);
      return;
    }

    SharedLogger.log(`[EventBus] Emitting '${event}' to ${allListeners.length} listener(s)`, data);

    // Call all handlers
    const listenersToRemove: EventSubscription[] = [];

    allListeners.forEach((subscription) => {
      try {
        subscription.handler(data);

        // Mark once listeners for removal
        if (subscription.once) {
          listenersToRemove.push(subscription);
        }
      } catch (error) {
        SharedLogger.error(`[EventBus] Error in '${event}' handler:`, error);
      }
    });

    // Remove once listeners
    listenersToRemove.forEach((subscription) => {
      this.off(subscription.event, subscription.handler);
    });
  }

  /**
   * Remove all listeners for an event
   */
  removeAllListeners(event?: string): void {
    if (event) {
      this.listeners.delete(event);
      SharedLogger.log(`[EventBus] Removed all listeners for '${event}'`);
    } else {
      this.listeners.clear();
      SharedLogger.log('[EventBus] Removed all listeners');
    }
  }

  /**
   * Remove all listeners in a namespace
   */
  removeNamespace(namespace: string): void {
    let removedCount = 0;

    this.listeners.forEach((subscriptions, event) => {
      const filtered = subscriptions.filter((sub) => sub.namespace !== namespace);
      removedCount += subscriptions.length - filtered.length;

      if (filtered.length === 0) {
        this.listeners.delete(event);
      } else {
        this.listeners.set(event, filtered);
      }
    });

    SharedLogger.log(`[EventBus] Removed ${removedCount} listener(s) from namespace '${namespace}'`);
  }

  /**
   * Get all listeners for an event
   */
  getListeners(event: string): EventSubscription[] {
    return this.listeners.get(event) || [];
  }

  /**
   * Get wildcard listeners for an event
   * Example: 'player:*' matches 'player:play', 'player:pause', etc.
   */
  private getWildcardListeners(event: string): EventSubscription[] {
    const wildcardListeners: EventSubscription[] = [];

    this.listeners.forEach((subscriptions, pattern) => {
      if (pattern.includes('*')) {
        const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
        if (regex.test(event)) {
          wildcardListeners.push(...subscriptions);
        }
      }
    });

    return wildcardListeners;
  }

  /**
   * Add event to history
   */
  private addToHistory(event: string, data: any): void {
    this.history.push({
      event,
      data,
      timestamp: new Date().toISOString(),
    });

    // Limit history size
    if (this.history.length > this.maxHistorySize) {
      this.history.shift();
    }
  }

  /**
   * Get event history
   */
  getHistory(event?: string): EventHistoryEntry[] {
    if (event) {
      return this.history.filter((entry) => entry.event === event);
    }
    return [...this.history];
  }

  /**
   * Clear event history
   */
  clearHistory(): void {
    this.history = [];
    SharedLogger.log('[EventBus] History cleared');
  }

  /**
   * Get all registered events
   */
  getAllEvents(): string[] {
    return Array.from(this.listeners.keys());
  }

  /**
   * Get listener count for an event
   */
  getListenerCount(event: string): number {
    return this.getListeners(event).length;
  }

  /**
   * Debug info
   */
  debug(): void {
    console.group('[EventBus] Debug Info');
    console.log('Registered Events:', this.getAllEvents());
    console.log('Total Listeners:', Array.from(this.listeners.values()).reduce((sum, subs) => sum + subs.length, 0));
    console.log('History Size:', this.history.length);
    console.table(
      Array.from(this.listeners.entries()).map(([event, subs]) => ({
        event,
        listeners: subs.length,
        namespaces: [...new Set(subs.map((s) => s.namespace || 'default'))].join(', '),
      }))
    );
    console.groupEnd();
  }
}

// Export singleton instance
export const SharedEventBus = new SharedEventBusClass();

// Make available globally for compatibility
declare global {
  interface Window {
    SharedEventBus: typeof SharedEventBus;
  }
}

if (typeof window !== 'undefined') {
  // Register to ServiceRegistry
  ServiceRegistry.register('SharedEventBus', SharedEventBus);
}

/**
 * Predefined Event Names (for type safety)
 */
export const EventNames = {
  // Device events
  DEVICE_REGISTERED: 'device:registered',
  DEVICE_ACTIVATED: 'device:activated',
  DEVICE_VERIFIED: 'device:verified',

  // Playlist events
  PLAYLIST_LOADED: 'playlist:loaded',
  PLAYLIST_CHANGED: 'playlist:changed',
  PLAYLIST_SYNC_START: 'playlist:sync:start',
  PLAYLIST_SYNC_SUCCESS: 'playlist:sync:success',
  PLAYLIST_SYNC_ERROR: 'playlist:sync:error',

  // Player events
  PLAYER_PLAY: 'player:play',
  PLAYER_PAUSE: 'player:pause',
  PLAYER_STOP: 'player:stop',
  PLAYER_NEXT: 'player:next',
  PLAYER_PREVIOUS: 'player:previous',
  PLAYER_ERROR: 'player:error',

  // Content events
  CONTENT_START: 'content:start',
  CONTENT_END: 'content:end',
  CONTENT_ERROR: 'content:error',

  // Connection events
  CONNECTION_ONLINE: 'connection:online',
  CONNECTION_OFFLINE: 'connection:offline',
  CONNECTION_LOST: 'connection:lost',
  CONNECTION_RESTORED: 'connection:restored',

  // WebSocket events
  WS_CONNECTED: 'ws:connected',
  WS_DISCONNECTED: 'ws:disconnected',
  WS_ERROR: 'ws:error',
  WS_MESSAGE: 'ws:message',

  // Command events
  COMMAND_RECEIVED: 'command:received',
  COMMAND_EXECUTED: 'command:executed',
  COMMAND_ERROR: 'command:error',

  // UI events
  UI_MODAL_OPEN: 'ui:modal:open',
  UI_MODAL_CLOSE: 'ui:modal:close',
  UI_TOAST_SHOW: 'ui:toast:show',
  UI_FULLSCREEN_ENTER: 'ui:fullscreen:enter',
  UI_FULLSCREEN_EXIT: 'ui:fullscreen:exit',
} as const;

export type EventName = typeof EventNames[keyof typeof EventNames];
