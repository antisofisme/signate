/**
 * Device Module Entry Point
 * Exports SharedDeviceState singleton and types
 */

export { SharedDeviceState } from './shared-device-state';
export type { DeviceState, ClearDeviceOptions } from './device-state.types';

// DeviceStatus and DeviceData are exported from @shared/models to avoid duplication
