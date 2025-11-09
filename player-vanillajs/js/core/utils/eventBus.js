/**
 * EventBus - Simple Pub/Sub Pattern for State Management
 *
 * @class EventBus
 * @description
 * Singleton event bus for decoupled communication between modules.
 * Implements the Observer pattern for reactive state management.
 *
 * @features
 * - Type-safe event subscription/emission
 * - Automatic unsubscribe function return
 * - Once-only event handlers
 * - Error isolation (one handler error won't break others)
 * - Memory leak prevention via unsubscribe pattern
 *
 * @event_naming_convention
 * Events follow the pattern: `namespace:action`
 * Examples:
 * - playlist:loaded - Playlist data loaded from API
 * - playlist:changed - Playlist content changed
 * - device:registered - Device registration complete
 * - device:activated - Device activation complete
 * - cache:sync-failed - Cache synchronization failed
 * - content:ended - Content playback ended
 * - websocket:connected - WebSocket connection established
 * - websocket:message - WebSocket message received
 *
 * @usage
 * ```javascript
 * import { eventBus } from './core/utils/eventBus.js';
 *
 * // Subscribe to event
 * const unsubscribe = eventBus.on('playlist:loaded', (playlist) => {
 *   SharedLogger.log('Playlist loaded:', playlist);
 * });
 *
 * // Emit event
 * eventBus.emit('playlist:loaded', { contents: [...] });
 *
 * // Unsubscribe (prevents memory leaks)
 * unsubscribe();
 * // OR
 * eventBus.off('playlist:loaded', callback);
 * ```
 *
 * @memory_leak_prevention
 * Always unsubscribe when component unmounts or is destroyed:
 * ```javascript
 * class MyComponent {
 *   init() {
 *     this.unsubscribers = [
 *       eventBus.on('playlist:loaded', this.handlePlaylist.bind(this)),
 *       eventBus.on('device:activated', this.handleActivation.bind(this))
 *     ];
 *   }
 *
 *   destroy() {
 *     this.unsubscribers.forEach(unsub => unsub());
 *   }
 * }
 * ```
 *
 * @singleton
 * Exposed as both ES6 module export and window.eventBus global
 */
class EventBus {
  /**
   * Create EventBus instance
   * @constructor
   */
  constructor() {
    /**
     * Event registry mapping event names to callback arrays
     * @type {Object.<string, Function[]>}
     * @private
     */
    this.events = {};
  }

  /**
   * Subscribe to event
   * @param {string} event - Event name
   * @param {Function} callback - Callback function
   * @returns {Function} Unsubscribe function
   */
  on(event, callback) {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(callback);

    // Return unsubscribe function
    return () => this.off(event, callback);
  }

  /**
   * Subscribe to event once (auto-unsubscribes after first call)
   * @param {string} event - Event name
   * @param {Function} callback - Callback function (called once then removed)
   * @returns {Function} Unsubscribe function (for manual early cancellation)
   * @example
   * eventBus.once('device:activated', (device) => {
   *   SharedLogger.log('Device activated (will only log once):', device);
   * });
   */
  once(event, callback) {
    const onceWrapper = (...args) => {
      callback(...args);
      this.off(event, onceWrapper);
    };
    return this.on(event, onceWrapper);
  }

  /**
   * Unsubscribe from event
   * @param {string} event - Event name
   * @param {Function} callback - Callback to remove
   */
  off(event, callback) {
    if (!this.events[event]) return;
    this.events[event] = this.events[event].filter(cb => cb !== callback);
  }

  /**
   * Emit event to all registered listeners
   * @param {string} event - Event name
   * @param {*} data - Event data payload (can be any type)
   * @throws {Error} Errors in individual handlers are caught and logged (doesn't break other handlers)
   * @example
   * // Emit with object payload
   * eventBus.emit('playlist:loaded', { contents: [...], updated_at: '2025-01-01' });
   *
   * // Emit with primitive payload
   * eventBus.emit('content:index-changed', 5);
   *
   * // Emit with error context
   * eventBus.emit('cache:sync-failed', { error: 'Network timeout', retry_in: 5000 });
   */
  emit(event, data) {
    if (!this.events[event]) return;
    this.events[event].forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        SharedLogger.error(`Error in event handler for ${event}:`, error);
      }
    });
  }

  /**
   * Remove all listeners for an event
   * @param {string} event - Event name
   */
  removeAllListeners(event) {
    if (event) {
      delete this.events[event];
    } else {
      this.events = {};
    }
  }

  /**
   * Get listener count for an event
   * @param {string} event - Event name
   * @returns {number}
   */
  listenerCount(event) {
    return this.events[event]?.length || 0;
  }
}

// Create singleton instance
const eventBusInstance = new EventBus();

// Expose to window for global access (loaded as classic script, not ES6 module)
if (typeof window !== 'undefined') {
  window.eventBus = eventBusInstance;
  window.EventBus = EventBus;
  SharedLogger.log('[EventBus] Initialized and exposed to window');
}

// For CommonJS environments (Node.js, testing)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { eventBus: eventBusInstance, EventBus };
}

