/**
 * Volume Command
 *
 * @class VolumeCommand
 * @extends BaseCommand
 * @description
 * Command to set device audio volume.
 * Supports WebOS TV API and HTML5 video element fallback for browsers.
 *
 * @features
 * - WebOS TV API integration for hardware volume control
 * - HTML5 video element volume control fallback
 * - Browser preference storage
 * - Volume range validation (0-100)
 *
 * @usage
 * ```javascript
 * const cmd = new VolumeCommand();
 * const result = await cmd.executeWithTimeout({ level: 50 });
 * ```
 */

class VolumeCommand extends BaseCommand {
  /**
   * Create volume command instance
   */
  constructor() {
    super('Volume');
  }

  /**
   * Validate volume level parameter
   *
   * @param {Object} parameters - Command parameters
   * @param {number} parameters.level - Volume level (0-100)
   * @throws {Error} If validation fails
   */
  validate(parameters) {
    if (typeof parameters.level !== 'number') {
      throw new Error('Volume level must be a number');
    }

    if (parameters.level < 0 || parameters.level > 100) {
      throw new Error('Volume level must be between 0 and 100');
    }
  }

  /**
   * Execute volume command
   *
   * @param {Object} parameters - Command parameters
   * @param {number} parameters.level - Volume level (0-100)
   * @returns {Promise<Object>} - Execution result
   */
  async execute(parameters) {
    const { level } = parameters;

    this.validate(parameters);
    this.log(`Setting volume to ${level}%`);

    // WebOS TV API
    if (this.isWebOS()) {
      return await this._executeWebOS(level);
    }

    // Browser fallback
    return this._executeBrowser(level);
  }

  /**
   * Execute volume command via WebOS API
   *
   * @param {number} level - Volume level
   * @returns {Promise<Object>} - Result object
   * @private
   */
  async _executeWebOS(level) {
    try {
      const response = await this.webOSRequest(
        'luna://com.webos.audio',
        'setVolume',
        { volume: level }
      );

      this.log('✅ Volume set via WebOS API');

      return {
        volume: level,
        success: true,
        method: 'webos_api',
        response: response
      };

    } catch (error) {
      this.logError('❌ WebOS volume API failed:', error);
      throw error;
    }
  }

  /**
   * Execute volume command via browser fallback
   *
   * @param {number} level - Volume level
   * @returns {Object} - Result object
   * @private
   */
  _executeBrowser(level) {
    this.log('Browser detected - storing volume preference');
    localStorage.setItem('volume_preference', level);

    // Try to control video element volume
    const videoElements = document.querySelectorAll('video');
    if (videoElements.length > 0) {
      videoElements.forEach(video => {
        video.volume = level / 100;
      });

      return {
        volume: level,
        success: true,
        method: 'html5_video',
        note: 'Applied to video elements only (browser limitation)'
      };
    }

    return {
      volume: level,
      success: true,
      method: 'preference_only',
      note: 'Volume preference stored (browser has limited control)'
    };
  }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = VolumeCommand;
}

// Export to window for vanilla JS
window.VolumeCommand = VolumeCommand;
