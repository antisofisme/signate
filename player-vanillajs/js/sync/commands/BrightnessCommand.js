/**
 * Brightness Command
 *
 * @class BrightnessCommand
 * @extends BaseCommand
 * @description
 * Command to set device screen brightness.
 * Supports WebOS TV API and CSS filter fallback for browsers.
 *
 * @features
 * - WebOS TV API integration for hardware brightness control
 * - CSS filter brightness fallback for browsers
 * - Brightness preference storage
 * - Brightness range validation (0-100)
 *
 * @usage
 * ```javascript
 * const cmd = new BrightnessCommand();
 * const result = await cmd.executeWithTimeout({ level: 75 });
 * ```
 */

class BrightnessCommand extends BaseCommand {
  /**
   * Create brightness command instance
   */
  constructor() {
    super('Brightness');
  }

  /**
   * Validate brightness level parameter
   *
   * @param {Object} parameters - Command parameters
   * @param {number} parameters.level - Brightness level (0-100)
   * @throws {Error} If validation fails
   */
  validate(parameters) {
    if (typeof parameters.level !== 'number') {
      throw new Error('Brightness level must be a number');
    }

    if (parameters.level < 0 || parameters.level > 100) {
      throw new Error('Brightness level must be between 0 and 100');
    }
  }

  /**
   * Execute brightness command
   *
   * @param {Object} parameters - Command parameters
   * @param {number} parameters.level - Brightness level (0-100)
   * @returns {Promise<Object>} - Execution result
   */
  async execute(parameters) {
    const { level } = parameters;

    this.validate(parameters);
    this.log(`Setting brightness to ${level}%`);

    // WebOS TV API
    if (this.isWebOS()) {
      return await this._executeWebOS(level);
    }

    // Browser fallback
    return this._executeBrowser(level);
  }

  /**
   * Execute brightness command via WebOS API
   *
   * @param {number} level - Brightness level
   * @returns {Promise<Object>} - Result object
   * @private
   */
  async _executeWebOS(level) {
    try {
      const response = await this.webOSRequest(
        'luna://com.webos.settingsservice',
        'setSystemSettings',
        {
          category: 'picture',
          settings: { backlight: level }
        }
      );

      this.log('✅ Brightness set via WebOS API');

      return {
        brightness: level,
        success: true,
        method: 'webos_api',
        response: response
      };

    } catch (error) {
      this.logError('❌ WebOS brightness API failed:', error);
      throw error;
    }
  }

  /**
   * Execute brightness command via browser fallback
   *
   * @param {number} level - Brightness level
   * @returns {Object} - Result object
   * @private
   */
  _executeBrowser(level) {
    this.log('Browser detected - using CSS filter');

    const brightness = level / 100; // 0-1 range
    document.body.style.filter = `brightness(${brightness})`;

    // Store preference
    SharedDeviceState.setPreference('brightness_preference', level);

    return {
      brightness: level,
      success: true,
      method: 'css_filter',
      note: 'CSS filter applied (not hardware brightness control)'
    };
  }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = BrightnessCommand;
}

// Export to window for vanilla JS
window.BrightnessCommand = BrightnessCommand;
