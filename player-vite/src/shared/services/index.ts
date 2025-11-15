/**
 * Shared Services Barrel Export
 * Centralized exports for all shared services
 */

export { ConnectionLogger } from './connection-logger';
export { NetworkSpeedTest } from './network-speed-test';
export { i18n } from './i18n';
export {
  ServiceRegistry,
  getPlayerHLS,
  getPlayerMediaCache,
  getPlayerHeartbeat,
  getPlayerPlaylistSync,
  getPlayerCommandExecutor,
  getPlayerHealthReporter,
  getShellBootstrap,
  getShellRegistration,
  getShellActivationPoll,
  getShellActivationScreen,
  getSharedWebSocket,
  getDeviceInfoPopup
} from './service-registry';
