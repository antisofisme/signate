/**
 * Device Hooks Barrel Export
 */

export * from './useDevices';
// Export only non-conflicting items from useDeviceLogs
export { logKeys, useLatestLogs, useDeviceLogs, useClearLogs, useConnectionLogs } from './useDeviceLogs';
export * from './useDeviceWebSocket';
export * from './useConsoleLiveStream';
// Note: useDeviceAssignments has overlapping exports with useDevices
// Use specific imports if needed: import { assignmentKeys } from './useDeviceAssignments';
