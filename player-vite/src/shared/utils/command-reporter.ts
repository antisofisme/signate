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
 * ```typescript
 * await reportCommandStatus(commandId, 'completed', result);
 * await reportCommandStatus(commandId, 'failed', null, errorMsg);
 * ```
 */

import { SharedAPIClient } from '@shared/api';

/**
 * Command status types
 */
export type CommandStatus = 'running' | 'completed' | 'failed';

/**
 * Command report payload
 */
interface CommandReport {
  command_id: number;
  status: CommandStatus;
  executed_at: string;
  result?: any;
  error?: string | null;
}

/**
 * Report command execution status to backend
 *
 * @param commandId - Command ID
 * @param status - Status ('running', 'completed', 'failed')
 * @param result - Execution result (if completed)
 * @param error - Error message (if failed)
 * @returns Promise that resolves when status is reported
 *
 * @example
 * await reportCommandStatus(123, 'completed', { volume: 50 });
 * await reportCommandStatus(124, 'failed', null, 'API error');
 */
export async function reportCommandStatus(
  commandId: number,
  status: CommandStatus,
  result: any = null,
  error: string | null = null
): Promise<void> {
  // Get deviceId from localStorage or sessionStorage
  const deviceId = localStorage.getItem('deviceId') || sessionStorage.getItem('deviceId');

  if (!deviceId) {
    console.warn('[CommandReporter] No device ID, cannot report status');
    return;
  }

  const report: CommandReport = {
    command_id: commandId,
    status: status,
    executed_at: new Date().toISOString(),
    result: result,
    error: error,
  };

  console.log(`[CommandReporter] Reporting status: ${status}`, report);

  try {
    // Use API client for standardized response handling
    await SharedAPIClient.post(
      `/devices/${deviceId}/commands/${commandId}/report`,
      report
    );

    console.log(`[CommandReporter] ✅ Status reported: ${status}`);
  } catch (reportError) {
    console.error(`[CommandReporter] ❌ Failed to report status:`, reportError);
    // Don't throw - reporting failure shouldn't break command execution
  }
}

/**
 * Report command as running
 * @param commandId - Command ID
 */
export async function reportCommandRunning(commandId: number): Promise<void> {
  return reportCommandStatus(commandId, 'running');
}

/**
 * Report command as completed
 * @param commandId - Command ID
 * @param result - Execution result
 */
export async function reportCommandCompleted(
  commandId: number,
  result?: any
): Promise<void> {
  return reportCommandStatus(commandId, 'completed', result);
}

/**
 * Report command as failed
 * @param commandId - Command ID
 * @param error - Error message
 */
export async function reportCommandFailed(
  commandId: number,
  error: string
): Promise<void> {
  return reportCommandStatus(commandId, 'failed', null, error);
}
