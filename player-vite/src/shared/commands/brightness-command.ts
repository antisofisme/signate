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
 * ```typescript
 * const cmd = new BrightnessCommand();
 * const result = await cmd.executeWithTimeout({ level: 75 });
 * ```
 */

import { BaseCommand, CommandResult } from './base-command';
import { SharedDeviceState } from '@shared/device';

export interface BrightnessParameters {
  level: number;
}

export interface BrightnessResult extends CommandResult {
  brightness: number;
  method: 'webos_api' | 'css_filter';
  response?: any;
  note?: string;
}

export class BrightnessCommand extends BaseCommand {
  /**
   * Create brightness command instance
   */
  constructor() {
    super('Brightness');
  }

  /**
   * Validate brightness level parameter
   *
   * @param parameters - Command parameters
   * @throws Error if validation fails
   */
  validate(parameters?: BrightnessParameters): void {
    if (!parameters) {
      throw new Error('Brightness parameters are required');
    }

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
   * @param parameters - Command parameters
   * @returns Execution result
   */
  async execute(parameters?: BrightnessParameters): Promise<BrightnessResult> {
    if (!parameters) {
      throw new Error('Brightness parameters are required');
    }

    const { level } = parameters;

    this.validate(parameters);
    this.log(`Setting brightness to ${level}%`);

    // WebOS TV API
    if (this.isWebOS()) {
      return await this.executeWebOS(level);
    }

    // Browser fallback
    return this.executeBrowser(level);
  }

  /**
   * Execute brightness command via WebOS API
   *
   * @param level - Brightness level
   * @returns Result object
   */
  private async executeWebOS(level: number): Promise<BrightnessResult> {
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
      this.logError('❌ WebOS brightness API failed:', error as Error);
      throw error;
    }
  }

  /**
   * Execute brightness command via browser fallback
   *
   * @param level - Brightness level
   * @returns Result object
   */
  private executeBrowser(level: number): BrightnessResult {
    this.log('Browser detected - using CSS filter');

    const brightness = level / 100; // 0-1 range
    document.body.style.filter = `brightness(${brightness})`;

    // Store preference via SharedDeviceState
    SharedDeviceState.setBrightnessPreference(level);

    return {
      brightness: level,
      success: true,
      method: 'css_filter',
      note: 'CSS filter applied (not hardware brightness control)'
    };
  }
}
