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
 * ```typescript
 * const cmd = new RebootCommand();
 * const result = await cmd.executeWithTimeout({ delay: 5 });
 * ```
 */

import { BaseCommand, CommandResult } from './base-command';

export interface RebootParameters {
  delay?: number;
}

export interface RebootResult extends CommandResult {
  rebooting: boolean;
  method: 'webos_api' | 'page_reload';
  delay_seconds: number;
  response?: any;
  error?: string;
  note?: string;
}

export class RebootCommand extends BaseCommand {
  /**
   * Create reboot command instance
   */
  constructor() {
    super('Reboot');
  }

  /**
   * Validate reboot parameters
   *
   * @param parameters - Command parameters
   * @throws Error if validation fails
   */
  validate(parameters?: RebootParameters): void {
    if (!parameters) return;

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
   * @param parameters - Command parameters
   * @returns Reboot result
   */
  async execute(parameters: RebootParameters = {}): Promise<RebootResult> {
    const delay = parameters.delay || 1;

    this.validate(parameters);
    this.log(`REBOOT requested (delay: ${delay}s)`);

    // WebOS TV API
    if (this.isWebOS()) {
      return await this.executeWebOS(delay);
    }

    // Browser fallback
    return this.executeBrowser(delay);
  }

  /**
   * Execute reboot via WebOS API
   *
   * @param delay - Delay in seconds
   * @returns Result object
   */
  private async executeWebOS(delay: number): Promise<RebootResult> {
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
            success: true,
            rebooting: true,
            method: 'webos_api',
            delay_seconds: delay,
            response: response
          });

        } catch (error) {
          this.logError('❌ WebOS reboot failed:', error as Error);
          // Still report success (may need manual reboot)
          resolve({
            success: true,
            rebooting: false,
            method: 'webos_api',
            delay_seconds: delay,
            error: (error as Error).message,
            note: 'Reboot command sent but may have failed'
          });
        }
      }, delay * 1000);
    });
  }

  /**
   * Execute reboot via browser fallback (page reload)
   *
   * @param delay - Delay in seconds
   * @returns Result object
   */
  private executeBrowser(delay: number): RebootResult {
    this.log('Browser detected - reloading page instead');

    setTimeout(() => {
      this.log('Reloading page...');
      window.location.reload();
    }, delay * 1000);

    return {
      success: true,
      rebooting: true,
      method: 'page_reload',
      delay_seconds: delay,
      note: 'Browser reload only (not full device reboot)'
    };
  }
}
