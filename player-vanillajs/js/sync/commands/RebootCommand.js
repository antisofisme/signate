/**
 * Reboot Command
 *
 * @class RebootCommand
 * @extends BaseCommand
 * @description
 * Command to reboot device.
 * Supports WebOS TV API for hardware reboot and page reload fallback for browsers.
 *
 * @features
 * - WebOS TV API integration for hardware reboot
 * - Configurable reboot delay
 * - Page reload fallback for browsers
 * - Status reporting before reboot
 *
 * @usage
 * ```javascript
 * const cmd = new RebootCommand();
 * const result = await cmd.executeWithTimeout({ delay: 5 });
 * ```
 */

class RebootCommand extends BaseCommand {
  /**
   * Create reboot command instance
   */
  constructor() {
    super('Reboot');
  }

  /**
   * Validate reboot parameters
   *
   * @param {Object} parameters - Command parameters
   * @throws {Error} If validation fails
   */
  validate(parameters) {
    if (parameters.delay !== undefined && typeof parameters.delay !== 'number') {
      throw new Error('Delay must be a number (seconds)');
    }

    if (parameters.delay !== undefined && parameters.delay < 0) {
      throw new Error('Delay cannot be negative');
    }
  }

  /**
   * Execute reboot command
   *
   * @param {Object} parameters - Command parameters
   * @param {number} [parameters.delay=1] - Delay before reboot in seconds
   * @returns {Promise<Object>} - Reboot result
   */
  async execute(parameters = {}) {
    const delay = parameters.delay || 1;

    this.validate(parameters);
    this.log(`REBOOT requested (delay: ${delay}s)`);

    // WebOS TV API
    if (this.isWebOS()) {
      return await this._executeWebOS(delay);
    }

    // Browser fallback
    return this._executeBrowser(delay);
  }

  /**
   * Execute reboot via WebOS API
   *
   * @param {number} delay - Delay in seconds
   * @returns {Promise<Object>} - Result object
   * @private
   */
  async _executeWebOS(delay) {
    return new Promise((resolve) => {
      this.log('Executing WebOS reboot...');

      setTimeout(async () => {
        try {
          const response = await this.webOSRequest(
            'luna://com.webos.service.tvpower',
            'power/setState',
            { state: 'reboot' }
          );

          this.log('✅ Reboot initiated');
          resolve({
            rebooting: true,
            method: 'webos_api',
            delay_seconds: delay,
            response: response
          });

        } catch (error) {
          this.logError('❌ WebOS reboot failed:', error);
          // Still report success (may need manual reboot)
          resolve({
            rebooting: false,
            method: 'webos_api',
            error: error.message,
            note: 'Reboot command sent but may have failed'
          });
        }
      }, delay * 1000);
    });
  }

  /**
   * Execute reboot via browser fallback (page reload)
   *
   * @param {number} delay - Delay in seconds
   * @returns {Object} - Result object
   * @private
   */
  _executeBrowser(delay) {
    this.log('Browser detected - reloading page instead');

    setTimeout(() => {
      this.log('Reloading page...');
      window.location.reload();
    }, delay * 1000);

    return {
      rebooting: true,
      method: 'page_reload',
      delay_seconds: delay,
      note: 'Browser reload only (not full device reboot)'
    };
  }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = RebootCommand;
}

// Export to window for vanilla JS
window.RebootCommand = RebootCommand;
