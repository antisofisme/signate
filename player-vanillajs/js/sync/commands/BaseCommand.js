/**
 * Base Command Class
 *
 * @class BaseCommand
 * @description
 * Abstract base class for all remote commands.
 * Implements Command Pattern for modular command execution.
 *
 * @features
 * - Timeout protection (30s max)
 * - Validation framework
 * - Error handling
 * - WebOS detection
 * - Browser fallbacks
 *
 * @usage
 * ```javascript
 * class MyCommand extends BaseCommand {
 *   async execute(parameters) {
 *     // Your implementation
 *   }
 * }
 * ```
 */

class BaseCommand {
  /**
   * Command timeout (30 seconds max)
   * @type {number}
   */
  static TIMEOUT = 30000;

  /**
   * Create command instance
   * @param {string} name - Command name
   */
  constructor(name) {
    this.name = name;
    this.startTime = null;
  }

  /**
   * Execute command with timeout protection
   *
   * @param {Object} parameters - Command parameters
   * @returns {Promise<Object>} - Execution result
   */
  async executeWithTimeout(parameters) {
    this.startTime = Date.now();

    // Create timeout promise
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error(`Command execution timeout after ${BaseCommand.TIMEOUT}ms`));
      }, BaseCommand.TIMEOUT);
    });

    // Race between execution and timeout
    return Promise.race([
      this.execute(parameters),
      timeoutPromise
    ]);
  }

  /**
   * Execute command (to be overridden by subclasses)
   *
   * @param {Object} parameters - Command parameters
   * @returns {Promise<Object>} - Execution result
   * @abstract
   */
  async execute(parameters) {
    throw new Error(`execute() must be implemented by ${this.constructor.name}`);
  }

  /**
   * Validate command parameters (to be overridden by subclasses)
   *
   * @param {Object} parameters - Command parameters
   * @throws {Error} If validation fails
   */
  validate(parameters) {
    // Default: no validation
    // Subclasses should override this
  }

  /**
   * Check if running on WebOS TV
   * @returns {boolean}
   */
  isWebOS() {
    return typeof window.webOS !== 'undefined' && window.webOS.service;
  }

  /**
   * Check if running in browser (non-WebOS)
   * @returns {boolean}
   */
  isBrowser() {
    return !this.isWebOS();
  }

  /**
   * Get execution duration in milliseconds
   * @returns {number}
   */
  getDuration() {
    if (!this.startTime) return 0;
    return Date.now() - this.startTime;
  }

  /**
   * Create WebOS service request
   *
   * @param {string} service - Luna service URI
   * @param {string} method - Service method
   * @param {Object} parameters - Method parameters
   * @returns {Promise<Object>} - Service response
   */
  webOSRequest(service, method, parameters = {}) {
    if (!this.isWebOS()) {
      throw new Error('WebOS API not available');
    }

    return new Promise((resolve, reject) => {
      window.webOS.service.request(service, {
        method,
        parameters,
        onSuccess: (res) => resolve(res),
        onFailure: (err) => reject(new Error(err.errorText || 'Unknown WebOS error'))
      });
    });
  }

  /**
   * Log command execution
   *
   * @param {string} message - Log message
   * @param {Object} [data] - Optional data to log
   */
  log(message, data) {
    const prefix = `[Command:${this.name}]`;
    if (data) {
      console.log(prefix, message, data);
    } else {
      console.log(prefix, message);
    }
  }

  /**
   * Log command error
   *
   * @param {string} message - Error message
   * @param {Error} [error] - Optional error object
   */
  logError(message, error) {
    const prefix = `[Command:${this.name}]`;
    if (error) {
      console.error(prefix, message, error);
    } else {
      console.error(prefix, message);
    }
  }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = BaseCommand;
}

// Export to window for vanilla JS
window.BaseCommand = BaseCommand;
