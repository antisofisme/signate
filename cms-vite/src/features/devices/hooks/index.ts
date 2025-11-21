/**
 * Device Hooks Barrel Export
 */

export * from './useDevices';
// Export only non-conflicting items from useDeviceLogs
export { logKeys, useLatestDeviceLogs, useCreateDeviceLog, useClearDeviceLogs } from './useDeviceLogs';
export * from './useDeviceWebSocket';
// Note: useDeviceAssignments has overlapping exports with useDevices
// Use specific imports if needed: import { assignmentKeys } from './useDeviceAssignments';
