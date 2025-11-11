/**
 * Global Type Declarations
 * Centralizes all Window interface augmentations to prevent conflicts
 */

import type { PlayerHLSClass } from './player/services/player-hls';
import type { PlayerPlaylistSyncClass } from './player/services/player-playlist-sync';
import type { PlayerMediaCacheClass } from './player/services/player-media-cache';
import type { PlayerHeartbeatClass } from './player/services/player-heartbeat';
import type { PlayerCommandExecutorClass } from './player/services/player-command-executor';
import type { PlayerHealthReporterClass } from './player/services/player-health-reporter';
import type { SharedWebSocketClass } from './shared/websocket/shared-websocket';
import type { ShellRegistrationClass } from './shell/services/shell-registration';
import type { ShellActivationPollClass } from './shell/services/shell-activation-poll';
import type { ShellBootstrapClass } from './shell/services/shell-bootstrap';
import type { ShellActivationScreenClass } from './shell/ui/shell-activation-screen';

declare global {
  interface Window {
    // Player services
    PlayerHLS?: PlayerHLSClass;
    PlayerPlaylistSync?: PlayerPlaylistSyncClass;
    PlayerMediaCache?: PlayerMediaCacheClass;
    PlayerHeartbeat?: PlayerHeartbeatClass;
    PlayerCommandExecutor?: PlayerCommandExecutorClass;
    PlayerHealthReporter?: PlayerHealthReporterClass;

    // Shared services
    SharedWebSocket?: SharedWebSocketClass;

    // Shell services
    ShellRegistration?: ShellRegistrationClass;
    ShellActivationPoll?: ShellActivationPollClass;
    ShellBootstrap?: ShellBootstrapClass;
    ShellActivationScreen?: ShellActivationScreenClass;
    ShellHeartbeat?: {
      stop(): void;
    };
  }
}

export {};
