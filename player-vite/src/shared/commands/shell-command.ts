/**
 * Shell Command
 *
 * @class ShellCommand
 * @extends BaseCommand
 * @description
 * Command to execute whitelisted shell commands on WebOS TV devices.
 * Heavily restricted for security - only whitelisted commands are allowed.
 *
 * @features
 * - Whitelist-based security enforcement
 * - WebOS SDK agent integration
 * - Command output capture (stdout, stderr)
 * - Return code tracking
 * - Browser fallback (throws error)
 *
 * @security
 * Only the following commands are allowed:
 * - uptime, date, hostname, whoami
 * - df -h, free -m, ps aux | head -20
 * - uname -a, cat /proc/meminfo | head -10, cat /proc/cpuinfo | head -20
 * - ip addr, netstat -tuln | head -20
 *
 * @usage
 * ```typescript
 * const cmd = new ShellCommand();
 * const result = await cmd.executeWithTimeout({ command: 'uptime' });
 * ```
 */

import { BaseCommand, CommandResult } from './base-command';

export interface ShellParameters {
  command: string;
}

export interface ShellResult extends CommandResult {
  command: string;
  stdout: string;
  stderr: string;
  returnValue: any;
  method: 'webos_sdkagent';
}

export class ShellCommand extends BaseCommand {
  /**
   * Shell command whitelist (SECURITY)
   */
  private static readonly WHITELIST: readonly string[] = [
    'uptime',
    'date',
    'hostname',
    'whoami',
    'df -h',
    'free -m',
    'ps aux | head -20',
    'uname -a',
    'cat /proc/meminfo | head -10',
    'cat /proc/cpuinfo | head -20',
    'ip addr',
    'netstat -tuln | head -20'
  ];

  /**
   * Create shell command instance
   */
  constructor() {
    super('Shell');
  }

  /**
   * Validate shell command parameter
   *
   * @param parameters - Command parameters
   * @throws Error if command not whitelisted
   */
  validate(parameters?: ShellParameters): void {
    if (!parameters || !parameters.command || typeof parameters.command !== 'string') {
      throw new Error('Command must be a non-empty string');
    }

    const isWhitelisted = ShellCommand.WHITELIST.some(whitelisted => {
      return parameters.command.trim() === whitelisted;
    });

    if (!isWhitelisted) {
      const allowedCommands = ShellCommand.WHITELIST.join(', ');
      throw new Error(
        `Command rejected: Not in whitelist. Allowed commands: ${allowedCommands}`
      );
    }
  }

  /**
   * Execute shell command
   *
   * @param parameters - Command parameters
   * @returns Command output
   */
  async execute(parameters?: ShellParameters): Promise<ShellResult> {
    if (!parameters) {
      throw new Error('Shell parameters are required');
    }

    const { command } = parameters;

    this.log(`Shell command requested: ${command}`);
    this.validate(parameters);

    // WebOS only
    if (!this.isWebOS()) {
      throw new Error('Shell commands only available on WebOS TV platform');
    }

    this.log('✅ Command whitelisted, executing...');

    return await this.executeViaWebOS(command);
  }

  /**
   * Execute command via WebOS SDK agent
   */
  private async executeViaWebOS(command: string): Promise<ShellResult> {
    return new Promise((resolve, reject) => {
      (window as any).webOS.service.request('luna://com.webos.service.sdkagent', {
        method: 'exec',
        parameters: {
          command: command,
          subscribe: false
        },
        onSuccess: (res: any) => {
          this.log('✅ Shell command executed');
          resolve({
            success: true,
            command: command,
            stdout: res.stdOut || '',
            stderr: res.stdErr || '',
            returnValue: res.returnValue,
            method: 'webos_sdkagent'
          });
        },
        onFailure: (err: any) => {
          this.logError('❌ Shell command failed:', err);
          reject(new Error(`Shell execution failed: ${err.errorText || 'Unknown error'}`));
        }
      });
    });
  }

  /**
   * Get current whitelist (for inspection)
   */
  static getWhitelist(): readonly string[] {
    return ShellCommand.WHITELIST;
  }

  /**
   * Check if command is whitelisted
   */
  static isWhitelisted(command: string): boolean {
    return ShellCommand.WHITELIST.some(whitelisted => {
      return command.trim() === whitelisted;
    });
  }
}
