/**
 * EventBus - Simple Pub/Sub Pattern for State Management
 *
 * Usage:
 *   import { eventBus } from './core/utils/eventBus.js';
 *   
 *   // Subscribe
 *   eventBus.on('playlist:loaded', (playlist) => {
 *     console.log('Playlist loaded:', playlist);
 *   });
 *   
 *   // Emit
 *   eventBus.emit('playlist:loaded', playlist);
 *   
 *   // Unsubscribe
 *   eventBus.off('playlist:loaded', callback);
 */

class EventBus {
  constructor() {
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
   * Subscribe to event once
   * @param {string} event - Event name
   * @param {Function} callback - Callback function
   */
  once(event, callback) {
    const onceWrapper = (...args) => {
      callback(...args);
      this.off(event, onceWrapper);
    };
    this.on(event, onceWrapper);
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
   * Emit event
   * @param {string} event - Event name
   * @param {*} data - Event data
   */
  emit(event, data) {
    if (!this.events[event]) return;
    this.events[event].forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in event handler for ${event}:`, error);
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

// Export for ES6 modules
export const eventBus = eventBusInstance;
export { EventBus };

// Also expose to window for backward compatibility (IIFE pattern)
if (typeof window !== 'undefined') {
  window.eventBus = eventBusInstance;
  window.EventBus = EventBus;
  console.log('[EventBus] Initialized and exposed to window');
}

