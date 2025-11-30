/**
 * Shell Keyboard Handler
 * Handles TV remote control and keyboard input
 *
 * @features
 * - Handle arrow keys (up, down, left, right)
 * - Handle Enter/OK button
 * - Handle Back button
 * - Handle number keys (0-9) for shortcuts
 * - Emit events via EventBus
 * - Support webOS TV remote codes
 * - Support Tizen TV remote codes
 * - Auto-initialize on import
 */

import { SharedLogger } from '@shared/logger';
import { SharedEventBus } from '@shared/events/shared-event-bus';
import { ServiceRegistry } from '@shared/services/service-registry';

/**
 * Keyboard event types
 */
export type KeyboardEventType =
  | 'arrow_up'
  | 'arrow_down'
  | 'arrow_left'
  | 'arrow_right'
  | 'enter'
  | 'back'
  | 'number'
  | 'exit'
  | 'menu'
  | 'volume_up'
  | 'volume_down'
  | 'mute'
  | 'play_pause'
  | 'stop';

/**
 * Keyboard event data
 */
export interface KeyboardEventData {
  type: KeyboardEventType;
  key: string;
  code: string;
  number?: number; // For number keys
  originalEvent: KeyboardEvent;
}

/**
 * TV Remote key codes (for reference)
 */
// const TV_REMOTE_KEYS = {
//   // webOS TV
//   webOS: {
//     RED: 403,
//     GREEN: 404,
//     YELLOW: 405,
//     BLUE: 406,
//     BACK: 461,
//     EXIT: 1001,
//     MENU: 18,
//     UP: 38,
//     DOWN: 40,
//     LEFT: 37,
//     RIGHT: 39,
//     ENTER: 13,
//     PLAY: 415,
//     PAUSE: 19,
//     STOP: 413,
//     REWIND: 412,
//     FORWARD: 417,
//   },
//   // Tizen TV
//   tizen: {
//     UP: 38,
//     DOWN: 40,
//     LEFT: 37,
//     RIGHT: 39,
//     ENTER: 13,
//     BACK: 10009,
//     EXIT: 10182,
//     MENU: 18,
//     PLAY: 415,
//     PAUSE: 19,
//     STOP: 413,
//   },
// };

/**
 * Shell Keyboard Handler Class
 * Singleton pattern for keyboard input management
 */
class ShellKeyboardHandlerClass {
  private initialized = false;
  private inputBuffer: string[] = [];
  private inputTimeout: number | null = null;
  private readonly inputTimeoutDuration = 2000; // 2 seconds to complete number input

  /**
   * Initialize keyboard handler
   */
  init(): void {
    if (this.initialized) {
      SharedLogger.warn('[KeyboardHandler] Already initialized');
      return;
    }

    this.initialized = true;

    // Listen to keyboard events
    document.addEventListener('keydown', this.handleKeyDown);
    document.addEventListener('keyup', this.handleKeyUp);

    // Register webOS TV keys if available
    this.registerWebOSKeys();

    // Register Tizen TV keys if available
    this.registerTizenKeys();

    SharedLogger.log('[KeyboardHandler] Initialized');
  }

  /**
   * Check if keyboard input should be ignored (when typing in input fields)
   */
  private isTypingInInput(): boolean {
    const activeElement = document.activeElement;
    if (!activeElement) return false;

    const tagName = activeElement.tagName.toLowerCase();
    const isInput = tagName === 'input' || tagName === 'textarea';
    const isContentEditable = activeElement.getAttribute('contenteditable') === 'true';

    return isInput || isContentEditable;
  }

  /**
   * Handle keydown event
   */
  private handleKeyDown = (event: KeyboardEvent): void => {
    // Skip keyboard handling when user is typing in input fields
    // Allow Escape to still work for closing modals etc.
    if (this.isTypingInInput() && event.key !== 'Escape') {
      return;
    }

    const eventData = this.mapKeyEvent(event);

    if (eventData) {
      // Prevent default for navigation keys (but not when typing)
      if (['arrow_up', 'arrow_down', 'arrow_left', 'arrow_right', 'enter', 'back'].includes(eventData.type)) {
        event.preventDefault();
      }

      // Emit event
      SharedEventBus.emit(`keyboard:${eventData.type}`, eventData);
      SharedEventBus.emit('keyboard:any', eventData);

      SharedLogger.log(`[KeyboardHandler] Key pressed: ${eventData.type}`, eventData);
    }
  };

  /**
   * Handle keyup event
   */
  private handleKeyUp = (_event: KeyboardEvent): void => {
    // Can be used for long-press detection in future
  };

  /**
   * Map keyboard event to our event type
   */
  private mapKeyEvent(event: KeyboardEvent): KeyboardEventData | null {
    const { key, code, keyCode } = event;

    let type: KeyboardEventType | null = null;
    let number: number | undefined;

    // Arrow keys
    if (key === 'ArrowUp' || keyCode === 38) {
      type = 'arrow_up';
    } else if (key === 'ArrowDown' || keyCode === 40) {
      type = 'arrow_down';
    } else if (key === 'ArrowLeft' || keyCode === 37) {
      type = 'arrow_left';
    } else if (key === 'ArrowRight' || keyCode === 39) {
      type = 'arrow_right';
    }
    // Enter/OK
    else if (key === 'Enter' || keyCode === 13) {
      type = 'enter';
    }
    // Back button (Escape, Backspace, or TV remote back)
    else if (key === 'Escape' || key === 'Backspace' || keyCode === 461 || keyCode === 10009) {
      type = 'back';
    }
    // Exit button (TV remote)
    else if (keyCode === 1001 || keyCode === 10182) {
      type = 'exit';
    }
    // Menu button
    else if (keyCode === 18) {
      type = 'menu';
    }
    // Number keys (0-9)
    else if (/^[0-9]$/.test(key)) {
      type = 'number';
      number = parseInt(key, 10);
      this.handleNumberInput(number);
    }
    // Volume controls
    else if (keyCode === 447) {
      type = 'volume_up';
    } else if (keyCode === 448) {
      type = 'volume_down';
    } else if (keyCode === 449) {
      type = 'mute';
    }
    // Media controls
    else if (keyCode === 415 || keyCode === 19) {
      type = 'play_pause';
    } else if (keyCode === 413) {
      type = 'stop';
    }

    if (!type) return null;

    return {
      type,
      key,
      code,
      number,
      originalEvent: event,
    };
  }

  /**
   * Handle number input (for activation code, etc.)
   */
  private handleNumberInput(num: number): void {
    // Clear previous timeout
    if (this.inputTimeout) {
      clearTimeout(this.inputTimeout);
    }

    // Add to buffer
    this.inputBuffer.push(num.toString());

    // Set timeout to clear buffer
    this.inputTimeout = window.setTimeout(() => {
      this.clearInputBuffer();
    }, this.inputTimeoutDuration);

    // Check for 6-digit activation code
    if (this.inputBuffer.length === 6) {
      const code = this.inputBuffer.join('');
      SharedEventBus.emit('keyboard:activation_code', { code });
      SharedLogger.log('[KeyboardHandler] Activation code entered:', code);
      this.clearInputBuffer();
    }

    SharedLogger.log('[KeyboardHandler] Number buffer:', this.inputBuffer.join(''));
  }

  /**
   * Clear input buffer
   */
  private clearInputBuffer(): void {
    this.inputBuffer = [];
    if (this.inputTimeout) {
      clearTimeout(this.inputTimeout);
      this.inputTimeout = null;
    }
  }

  /**
   * Get current input buffer (for debugging)
   */
  getInputBuffer(): string {
    return this.inputBuffer.join('');
  }

  /**
   * Register webOS TV specific keys
   */
  private registerWebOSKeys(): void {
    // @ts-ignore - webOS API
    if (typeof window.webOS !== 'undefined') {
      SharedLogger.log('[KeyboardHandler] webOS TV detected - registering keys');

      // @ts-ignore
      window.webOS.platformBack = () => {
        SharedEventBus.emit('keyboard:back', {
          type: 'back',
          key: 'webOS_Back',
          code: '',
          originalEvent: new KeyboardEvent('keydown'),
        });
      };
    }
  }

  /**
   * Register Tizen TV specific keys
   */
  private registerTizenKeys(): void {
    // @ts-ignore - Tizen API
    if (typeof window.tizen !== 'undefined') {
      SharedLogger.log('[KeyboardHandler] Tizen TV detected - registering keys');

      try {
        // @ts-ignore
        tizen.tvinputdevice.registerKeyBatch([
          'MediaPlay',
          'MediaPause',
          'MediaStop',
          'MediaRewind',
          'MediaFastForward',
        ]);
      } catch (error) {
        SharedLogger.error('[KeyboardHandler] Failed to register Tizen keys:', error);
      }
    }
  }

  /**
   * Simulate key press (for testing)
   */
  simulateKeyPress(type: KeyboardEventType): void {
    const event = new KeyboardEvent('keydown', {
      key: type,
      code: type,
    });

    const eventData: KeyboardEventData = {
      type,
      key: type,
      code: type,
      originalEvent: event,
    };

    SharedEventBus.emit(`keyboard:${type}`, eventData);
    SharedEventBus.emit('keyboard:any', eventData);

    SharedLogger.log('[KeyboardHandler] Simulated key press:', type);
  }

  /**
   * Cleanup event listeners
   */
  destroy(): void {
    document.removeEventListener('keydown', this.handleKeyDown);
    document.removeEventListener('keyup', this.handleKeyUp);
    this.clearInputBuffer();
    this.initialized = false;
    SharedLogger.log('[KeyboardHandler] Destroyed');
  }
}

// Export singleton instance
export const ShellKeyboardHandler = new ShellKeyboardHandlerClass();

// Make available globally for compatibility
declare global {
  interface Window {
    ShellKeyboardHandler: typeof ShellKeyboardHandler;
  }
}

if (typeof window !== 'undefined') {
  // Register to ServiceRegistry
  ServiceRegistry.register('ShellKeyboardHandler', ShellKeyboardHandler);
}

// Auto-initialize when module is imported
ShellKeyboardHandler.init();
