/**
 * Command Executor - Refactored with Command Pattern
 *
 * @module command-executor-new
 * @description
 * Orchestrator for remote command execution using the Command Pattern.
 * Delegates to specific command classes while managing queue, state, and reporting.
 *
 * Features:
 * - Command routing to appropriate handler classes
 * - Timeout protection (30s max)
 * - Status reporting to backend
 * - Backward compatible with window.ShellCommandExecutor API
 * - Modular command architecture
 *
 * Supported Commands:
 * - volume: Set audio volume (0-100%)
 * - brightness: Set screen brightness (0-100%)
 * - screenshot: Capture current display
 * - reboot: Restart device
 * - shell: Execute whitelisted shell commands (WebOS only)
 * - info: Get detailed device information
 *
 * @usage
 * ```javascript
 * await window.ShellCommandExecutor.executeCommand({
 *   id: 123,
 *   command_type: 'volume',
 *   parameters: { level: 50 },
 *   reason: 'User adjusted volume'
 * });
 * ```
 *
 * @version 2.0.0 (refactored)
 */

window.ShellCommandExecutor = {
  /**
   * Execution queue and state
   */
  executionQueue: [],
  isExecuting: false,
  currentCommand: null,

  /**
   * Command timeout (30 seconds max)
   */
  COMMAND_TIMEOUT: 30000,

  /**
   * Shell command whitelist (for reference, actual enforcement in ShellCommand)
   */
  SHELL_WHITELIST: [
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
  ],

  /**
   * Command class instances
   */
  commands: {
    volume: null,
    brightness: null,
    screenshot: null,
    reboot: null,
    shell: null,
    info: null
  },

  /**
   * Initialize command executor
   *
   * @returns {void}
   */
  init: function() {
    // Lazy initialize command classes when needed
    SharedLogger.log('[CommandExecutor] Initialized with Command Pattern architecture');
  },

  /**
   * Execute a command received from backend
   *
   * @param {Object} commandData - Command data from backend
   * @param {number} commandData.id - Command ID
   * @param {string} commandData.command_type - Command type
   * @param {Object} commandData.parameters - Command parameters
   * @param {string} commandData.reason - Command reason/description
   * @returns {Promise<void>}
   */
  executeCommand: async function(commandData) {
    const { id, command_type, parameters = {}, reason } = commandData;

    SharedLogger.log(`[CommandExecutor] Executing: ${command_type} (ID: ${id})`);
    if (reason) {
      SharedLogger.log(`[CommandExecutor] Reason: ${reason}`);
    }
    SharedLogger.log(`[CommandExecutor] Parameters:`, parameters);

    // Update current command
    this.currentCommand = {
      id,
      type: command_type,
      startTime: Date.now()
    };

    // Report status as running
    await CommandReporter.reportStatus(id, 'running');

    try {
      let result;

      // Execute command with timeout protection
      const executePromise = this._executeCommandInternal(command_type, parameters);
      const timeoutPromise = this._createTimeoutPromise(this.COMMAND_TIMEOUT);

      result = await Promise.race([executePromise, timeoutPromise]);

      SharedLogger.log(`[CommandExecutor] Command ${command_type} completed`);
      SharedLogger.log(`[CommandExecutor] Result:`, result);

      // Report success
      await CommandReporter.reportStatus(id, 'completed', result);

    } catch (error) {
      SharedLogger.error(`[CommandExecutor] Command ${command_type} failed:`, error);

      // Report failure
      await CommandReporter.reportStatus(id, 'failed', null, error.message);

    } finally {
      // Clear current command
      this.currentCommand = null;
    }
  },

  /**
   * Internal command execution (without timeout wrapper)
   *
   * @param {string} commandType - Command type
   * @param {Object} parameters - Command parameters
   * @returns {Promise<Object>} - Execution result
   * @private
   */
  _executeCommandInternal: async function(commandType, parameters) {
    switch (commandType) {
      case 'volume':
        return await this._executeVolume(parameters);

      case 'brightness':
        return await this._executeBrightness(parameters);

      case 'screenshot':
        return await this._executeScreenshot(parameters);

      case 'reboot':
        return await this._executeReboot(parameters);

      case 'shell':
        return await this._executeShell(parameters);

      case 'info':
        return await this._executeInfo(parameters);

      default:
        throw new Error(`Unknown command type: ${commandType}`);
    }
  },

  /**
   * Create timeout promise
   *
   * @param {number} timeout - Timeout in milliseconds
   * @returns {Promise<never>} - Promise that rejects after timeout
   * @private
   */
  _createTimeoutPromise: function(timeout) {
    return new Promise((_, reject) => {
      setTimeout(() => {
        reject(new Error(`Command execution timeout after ${timeout}ms`));
      }, timeout);
    });
  },

  /**
   * Execute volume command
   *
   * @param {Object} parameters - Command parameters
   * @returns {Promise<Object>} - Execution result
   * @private
   */
  _executeVolume: async function(parameters) {
    if (!this.commands.volume) {
      this.commands.volume = new window.VolumeCommand();
    }
    return await this.commands.volume.executeWithTimeout(parameters);
  },

  /**
   * Execute brightness command
   *
   * @param {Object} parameters - Command parameters
   * @returns {Promise<Object>} - Execution result
   * @private
   */
  _executeBrightness: async function(parameters) {
    if (!this.commands.brightness) {
      this.commands.brightness = new window.BrightnessCommand();
    }
    return await this.commands.brightness.executeWithTimeout(parameters);
  },

  /**
   * Execute screenshot command
   *
   * @param {Object} parameters - Command parameters
   * @returns {Promise<Object>} - Execution result
   * @private
   */
  _executeScreenshot: async function(parameters) {
    if (!this.commands.screenshot) {
      this.commands.screenshot = new window.ScreenshotCommand();
    }
    return await this.commands.screenshot.executeWithTimeout(parameters);
  },

  /**
   * Execute reboot command
   *
   * @param {Object} parameters - Command parameters
   * @returns {Promise<Object>} - Execution result
   * @private
   */
  _executeReboot: async function(parameters) {
    if (!this.commands.reboot) {
      this.commands.reboot = new window.RebootCommand();
    }
    return await this.commands.reboot.executeWithTimeout(parameters);
  },

  /**
   * Execute shell command
   *
   * @param {Object} parameters - Command parameters
   * @returns {Promise<Object>} - Execution result
   * @private
   */
  _executeShell: async function(parameters) {
    if (!this.commands.shell) {
      this.commands.shell = new window.ShellCommand();
    }
    return await this.commands.shell.executeWithTimeout(parameters);
  },

  /**
   * Execute info command
   *
   * @param {Object} parameters - Command parameters
   * @returns {Promise<Object>} - Execution result
   * @private
   */
  _executeInfo: async function(parameters) {
    if (!this.commands.info) {
      this.commands.info = new window.InfoCommand();
    }
    return await this.commands.info.executeWithTimeout(parameters);
  },

  /**
   * Get current execution status (for debugging)
   *
   * @returns {Object} - Current execution status
   */
  getStatus: function() {
    return {
      is_executing: this.isExecuting,
      current_command: this.currentCommand,
      queue_length: this.executionQueue.length,
      shell_whitelist_count: this.SHELL_WHITELIST.length
    };
  }
};

SharedLogger.log('[CommandExecutor] Loaded - Command Pattern architecture active');
SharedLogger.log(`[CommandExecutor] Shell whitelist: ${window.ShellCommandExecutor.SHELL_WHITELIST.length} commands`);
