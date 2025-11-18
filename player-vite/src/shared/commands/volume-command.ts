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
 * ```typescript
 * const cmd = new VolumeCommand();
 * const result = await cmd.executeWithTimeout({ level: 50 });
 * ```
 */

import { BaseCommand, CommandResult } from './base-command';
import { SharedDeviceState } from '@shared/device';

export interface VolumeParameters {
  level: number;
}

export interface VolumeResult extends CommandResult {
  volume: number;
  method: 'webos_api' | 'html5_video' | 'preference_only';
  response?: any;
  note?: string;
}

export class VolumeCommand extends BaseCommand {
  /**
   * Create volume command instance
   */
  constructor() {
    super('Volume');
  }

  /**
   * Validate volume level parameter
   *
   * @param parameters - Command parameters
   * @throws Error if validation fails
   */
  validate(parameters?: VolumeParameters): void {
    if (!parameters) {
      throw new Error('Volume parameters are required');
    }

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
   * @param parameters - Command parameters
   * @returns Execution result
   */
  async execute(parameters?: VolumeParameters): Promise<VolumeResult> {
    if (!parameters) {
      throw new Error('Volume parameters are required');
    }

    const { level } = parameters;

    this.validate(parameters);
    this.log(`Setting volume to ${level}%`);

    // WebOS TV API
    if (this.isWebOS()) {
      return await this.executeWebOS(level);
    }

    // Browser fallback
    return this.executeBrowser(level);
  }

  /**
   * Execute volume command via WebOS API
   *
   * @param level - Volume level
   * @returns Result object
   */
  private async executeWebOS(level: number): Promise<VolumeResult> {
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
      this.logError('❌ WebOS volume API failed:', error as Error);
      throw error;
    }
  }

  /**
   * Execute volume command via browser fallback
   *
   * @param level - Volume level
   * @returns Result object
   */
  private executeBrowser(level: number): VolumeResult {
    this.log('Browser detected - storing volume preference');
    SharedDeviceState.setVolumePreference(level);

    // Try to control video element volume
    const videoElements = document.querySelectorAll('video');
    if (videoElements.length > 0) {
      videoElements.forEach(video => {
        (video as HTMLVideoElement).volume = level / 100;
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
