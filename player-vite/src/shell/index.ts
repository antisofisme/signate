/**
 * Shell Module Entry Point
 * Exports all shell services and types
 *
 * @module Shell
 * @description
 * Shell context handles device registration and activation flow.
 * This is the first context users see when device is not yet activated.
 */

// Services
export { ShellBootstrap } from './services/shell-bootstrap';
export { ShellRegistration } from './services/shell-registration';
export { ShellActivationPoll } from './services/shell-activation-poll';
export { ShellKeyboardHandler } from './services/shell-keyboard-handler';
export { ShellFullscreenHandler } from './services/shell-fullscreen-handler';
export { ShellConnectionStatus } from './services/shell-connection-status';
export { ShellNetworkDiagnostics } from './services/shell-network-diagnostics';
export { ShellDisplaySettings } from './services/shell-display-settings';
export { ShellDeviceControls } from './services/shell-device-controls';

// UI Components
export { ShellActivationScreen } from './ui/shell-activation-screen';

// Types
export type {
  RegistrationResponse,
  ActivationCheckResponse,
  VerifyDeviceResponse,
  PlatformInfo,
  RetryConfig,
  ShellRegistration as IShellRegistration,
  ShellActivationPoll as IShellActivationPoll,
  ShellBootstrap as IShellBootstrap,
} from './types/shell.types';

export type {
  KeyboardEventType,
  KeyboardEventData,
} from './services/shell-keyboard-handler';

export type {
  FullscreenOptions,
} from './services/shell-fullscreen-handler';

export type {
  ConnectionStatus,
  ConnectionCheckResult,
} from './services/shell-connection-status';

export type {
  SpeedTestResult,
  PingTestResult,
  NetworkQuality,
  DiagnosticsOptions,
} from './services/shell-network-diagnostics';

export type {
  DisplayInfo,
  TVCapabilities,
} from './services/shell-display-settings';

export type {
  VolumeLevel,
  BrightnessLevel,
  DeviceCapabilities,
} from './services/shell-device-controls';
