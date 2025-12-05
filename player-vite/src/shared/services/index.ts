/**
 * Shared Services Barrel Export
 * Centralized exports for all shared services
 */

export { ConnectionLogger } from './connection-logger';
export { NetworkSpeedTest } from './network-speed-test';
export {
  ServiceRegistry,
  getPlayerVideoJS,
  getPlayerMediaCache,
  getPlayerHeartbeat,
  getPlayerPlaylistSync,
  getPlayerCommandExecutor,
  getPlayerHealthReporter,
  getPlayerCapabilitiesReporter,
  getPlayerHLSCache,
  getPlayerBackgroundAudio,
  getShellBootstrap,
  getShellRegistration,
  getShellActivationPoll,
  getShellActivationScreen,
  getSharedWebSocket,
  getDeviceInfoPopup
} from './service-registry';
