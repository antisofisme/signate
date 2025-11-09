/**
 * Command Status Reporter Utility
 *
 * @module command-reporter
 * @description
 * Handles reporting of command execution status back to the backend API.
 * Supports different status states and error reporting.
 *
 * @features
 * - Status reporting (running, completed, failed)
 * - Error message inclusion
 * - Result payload handling
 * - API integration with fallbacks
 * - Graceful error handling
 *
 * @usage
 * ```javascript
 * await CommandReporter.reportStatus(commandId, 'completed', result);
 * await CommandReporter.reportStatus(commandId, 'failed', null, errorMsg);
 * ```
 */

const CommandReporter = {
  /**
   * Report command execution status to backend
   *
   * @param {number} commandId - Command ID
   * @param {string} status - Status ('running', 'completed', 'failed')
   * @param {Object} [result] - Execution result (if completed)
   * @param {string} [error] - Error message (if failed)
   * @returns {Promise<void>}
   *
   * @example
   * await CommandReporter.reportStatus(123, 'completed', { volume: 50 });
   * await CommandReporter.reportStatus(124, 'failed', null, 'API error');
   */
  reportStatus: async function(commandId, status, result = null, error = null) {
    // Get deviceId from deviceState, fallback to ShellState
    const device = window.SharedDeviceState ? window.SharedDeviceState.getDevice() : null;
    const deviceId = device ? device.id : window.ShellState?.deviceId;

    if (!deviceId) {
      SharedLogger.warn('[CommandReporter] No device ID, cannot report status');
      return;
    }

    // Get API_BASE_URL from Config/ENV
    const apiBaseUrl = window.Config?.API_BASE_URL || window.SharedENV?.API_BASE_URL;
    if (!apiBaseUrl) {
      SharedLogger.error('[CommandReporter] No API_BASE_URL configured');
      return;
    }

    const report = {
      command_id: commandId,
      status: status,
      executed_at: new Date().toISOString(),
      result: result,
      error: error
    };

    SharedLogger.log(`[CommandReporter] Reporting status: ${status}`);

    try {
      // Use APIClient for standardized response handling
      await window.SharedAPIClient.post(
        `${apiBaseUrl}/api/devices/${deviceId}/commands/${commandId}/report`,
        report
      );

      SharedLogger.log(`[CommandReporter] ✅ Status reported: ${status}`);

    } catch (reportError) {
      SharedLogger.error(`[CommandReporter] ❌ Failed to report status:`, reportError);
      // Don't throw - reporting failure shouldn't break command execution
    }
  }
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CommandReporter;
}

// Export to window for vanilla JS
window.CommandReporter = CommandReporter;
