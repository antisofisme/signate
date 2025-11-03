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
 * ```javascript
 * const cmd = new ShellCommand();
 * const result = await cmd.executeWithTimeout({ command: 'uptime' });
 * ```
 */

class ShellCommand extends BaseCommand {
  /**
   * Shell command whitelist (SECURITY)
   * @type {Array<string>}
   */
  static WHITELIST = [
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
   * @param {Object} parameters - Command parameters
   * @param {string} parameters.command - Shell command to execute
   * @throws {Error} If command not whitelisted
   */
  validate(parameters) {
    if (!parameters.command || typeof parameters.command !== 'string') {
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
   * @param {Object} parameters - Command parameters
   * @param {string} parameters.command - Shell command to execute
   * @returns {Promise<Object>} - Command output
   */
  async execute(parameters) {
    const { command } = parameters;

    this.log(`Shell command requested: ${command}`);
    this.validate(parameters);

    // WebOS only
    if (!this.isWebOS()) {
      throw new Error('Shell commands only available on WebOS TV platform');
    }

    this.log('✅ Command whitelisted, executing...');

    return await this._executeViaWebOS(command);
  }

  /**
   * Execute command via WebOS SDK agent
   *
   * @param {string} command - Shell command
   * @returns {Promise<Object>} - Execution result
   * @private
   */
  async _executeViaWebOS(command) {
    return new Promise((resolve, reject) => {
      window.webOS.service.request('luna://com.webos.service.sdkagent', {
        method: 'exec',
        parameters: {
          command: command,
          subscribe: false
        },
        onSuccess: (res) => {
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
        onFailure: (err) => {
          this.logError('❌ Shell command failed:', err);
          reject(new Error(`Shell execution failed: ${err.errorText || 'Unknown error'}`));
        }
      });
    });
  }

  /**
   * Get current whitelist (for inspection)
   *
   * @returns {Array<string>} - Whitelisted commands
   */
  static getWhitelist() {
    return [...ShellCommand.WHITELIST];
  }

  /**
   * Check if command is whitelisted
   *
   * @param {string} command - Command to check
   * @returns {boolean} - True if whitelisted
   */
  static isWhitelisted(command) {
    return ShellCommand.WHITELIST.some(whitelisted => {
      return command.trim() === whitelisted;
    });
  }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ShellCommand;
}

// Export to window for vanilla JS
window.ShellCommand = ShellCommand;
