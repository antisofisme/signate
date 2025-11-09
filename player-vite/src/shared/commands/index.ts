/**
 * Command Module Barrel Export
 *
 * @description
 * Centralized export for all command classes and types.
 * Implements Command Pattern for remote device control.
 *
 * @usage
 * ```typescript
 * import { BrightnessCommand, VolumeCommand, InfoCommand } from '@/shared/commands';
 *
 * const brightness = new BrightnessCommand();
 * await brightness.executeWithTimeout({ level: 75 });
 * ```
 */

// Base command and types
export { BaseCommand } from './base-command';
export type { CommandResult, WebOSService, WebOSWindow } from './base-command';

// Brightness command
export { BrightnessCommand } from './brightness-command';
export type { BrightnessParameters, BrightnessResult } from './brightness-command';

// Volume command
export { VolumeCommand } from './volume-command';
export type { VolumeParameters, VolumeResult } from './volume-command';

// Reboot command
export { RebootCommand } from './reboot-command';
export type { RebootParameters, RebootResult } from './reboot-command';

// Info command
export { InfoCommand } from './info-command';
export type { DeviceInfo, InfoResult } from './info-command';

// Screenshot command
export { ScreenshotCommand } from './screenshot-command';
export type {
  ScreenshotQuality,
  ScreenshotParameters,
  ScreenshotResult
} from './screenshot-command';

// Shell command
export { ShellCommand } from './shell-command';
export type { ShellParameters, ShellResult } from './shell-command';
