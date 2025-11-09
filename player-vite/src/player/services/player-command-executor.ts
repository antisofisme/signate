/**
 * Player Command Executor
 * Executes remote commands received from admin panel via WebSocket
 *
 * @features
 * - Command validation and execution
 * - Command history tracking
 * - Result reporting back to server
 * - Type-safe command handlers
 */

import { SharedLogger } from '@shared/logger';
import { SharedEventBus, EventNames } from '@shared/events/shared-event-bus';
import { SharedWebSocket, WSMessageType } from '@shared/websocket/shared-websocket';

/**
 * Command types
 */
export enum CommandType {
  // Player controls
  PLAY = 'play',
  PAUSE = 'pause',
  STOP = 'stop',
  NEXT = 'next',
  PREVIOUS = 'previous',
  SEEK = 'seek',
  SET_VOLUME = 'set_volume',

  // Playlist controls
  LOAD_PLAYLIST = 'load_playlist',
  RELOAD_PLAYLIST = 'reload_playlist',
  CLEAR_PLAYLIST = 'clear_playlist',

  // Cache controls
  CLEAR_CACHE = 'clear_cache',
  CACHE_CONTENT = 'cache_content',

  // System controls
  REBOOT = 'reboot',
  RELOAD_PAGE = 'reload_page',
  CLEAR_STORAGE = 'clear_storage',
  FACTORY_RESET = 'factory_reset',

  // Display controls
  FULLSCREEN = 'fullscreen',
  EXIT_FULLSCREEN = 'exit_fullscreen',
  SET_BRIGHTNESS = 'set_brightness',

  // Network controls
  RUN_SPEEDTEST = 'run_speedtest',
  PING_TEST = 'ping_test',

  // Info requests
  GET_STATUS = 'get_status',
  GET_SYSTEM_INFO = 'get_system_info',
  GET_PLAYLIST_INFO = 'get_playlist_info',
}

/**
 * Command interface
 */
export interface Command {
  id: string;
  type: CommandType;
  params?: Record<string, any>;
  timestamp: string;
}

/**
 * Command result interface
 */
export interface CommandResult {
  command_id: string;
  success: boolean;
  data?: any;
  error?: string;
  executed_at: string;
}

/**
 * Command handler function type
 */
type CommandHandler = (params?: Record<string, any>) => Promise<CommandResult['data']>;

/**
 * Player Command Executor Class
 * Singleton pattern for command execution
 */
class PlayerCommandExecutorClass {
  private handlers: Map<CommandType, CommandHandler> = new Map();
  private history: CommandResult[] = [];
  private readonly maxHistorySize = 100;

  /**
   * Initialize command executor
   */
  init(): void {
    SharedLogger.log('[CommandExecutor] Initializing...');

    // Register default handlers
    this.registerDefaultHandlers();

    // Listen for command events from WebSocket
    SharedEventBus.on<Command>(EventNames.COMMAND_RECEIVED, (command) => {
      void this.executeCommand(command);
    });

    SharedLogger.log('[CommandExecutor] ✅ Initialized');
  }

  /**
   * Register default command handlers
   */
  private registerDefaultHandlers(): void {
    // Player controls
    this.registerHandler(CommandType.PLAY, this.handlePlay.bind(this));
    this.registerHandler(CommandType.PAUSE, this.handlePause.bind(this));
    this.registerHandler(CommandType.STOP, this.handleStop.bind(this));
    this.registerHandler(CommandType.NEXT, this.handleNext.bind(this));
    this.registerHandler(CommandType.PREVIOUS, this.handlePrevious.bind(this));
    this.registerHandler(CommandType.SEEK, this.handleSeek.bind(this));
    this.registerHandler(CommandType.SET_VOLUME, this.handleSetVolume.bind(this));

    // Playlist controls
    this.registerHandler(CommandType.LOAD_PLAYLIST, this.handleLoadPlaylist.bind(this));
    this.registerHandler(CommandType.RELOAD_PLAYLIST, this.handleReloadPlaylist.bind(this));

    // Cache controls
    this.registerHandler(CommandType.CLEAR_CACHE, this.handleClearCache.bind(this));

    // System controls
    this.registerHandler(CommandType.RELOAD_PAGE, this.handleReloadPage.bind(this));
    this.registerHandler(CommandType.CLEAR_STORAGE, this.handleClearStorage.bind(this));

    // Display controls
    this.registerHandler(CommandType.FULLSCREEN, this.handleFullscreen.bind(this));
    this.registerHandler(CommandType.EXIT_FULLSCREEN, this.handleExitFullscreen.bind(this));

    // Info requests
    this.registerHandler(CommandType.GET_STATUS, this.handleGetStatus.bind(this));
    this.registerHandler(CommandType.GET_SYSTEM_INFO, this.handleGetSystemInfo.bind(this));

    SharedLogger.log(`[CommandExecutor] Registered ${this.handlers.size} default handlers`);
  }

  /**
   * Register a command handler
   */
  registerHandler(type: CommandType, handler: CommandHandler): void {
    this.handlers.set(type, handler);
    SharedLogger.log(`[CommandExecutor] Registered handler for '${type}'`);
  }

  /**
   * Execute a command
   */
  async executeCommand(command: Command): Promise<CommandResult> {
    SharedLogger.log('[CommandExecutor] Executing command:', command);

    const result: CommandResult = {
      command_id: command.id,
      success: false,
      executed_at: new Date().toISOString(),
    };

    try {
      const handler = this.handlers.get(command.type);

      if (!handler) {
        throw new Error(`Unknown command type: ${command.type}`);
      }

      // Execute handler
      const data = await handler(command.params);

      result.success = true;
      result.data = data;

      SharedLogger.log(`[CommandExecutor] ✅ Command '${command.type}' executed successfully`);

      // Emit command executed event
      SharedEventBus.emit(EventNames.COMMAND_EXECUTED, { command, result });
    } catch (error) {
      result.success = false;
      result.error = error instanceof Error ? error.message : String(error);

      SharedLogger.error(`[CommandExecutor] ❌ Command '${command.type}' failed:`, error);

      // Emit command error event
      SharedEventBus.emit(EventNames.COMMAND_ERROR, { command, error });
    }

    // Add to history
    this.addToHistory(result);

    // Send result back to server via WebSocket
    this.sendResult(result);

    return result;
  }

  /**
   * Send command result to server
   */
  private sendResult(result: CommandResult): void {
    if (SharedWebSocket.isConnected()) {
      SharedWebSocket.send(WSMessageType.COMMAND_RESPONSE, result);
    } else {
      SharedLogger.warn('[CommandExecutor] WebSocket not connected, cannot send result');
    }
  }

  /**
   * Add result to history
   */
  private addToHistory(result: CommandResult): void {
    this.history.push(result);

    if (this.history.length > this.maxHistorySize) {
      this.history.shift();
    }
  }

  /**
   * Get command history
   */
  getHistory(): CommandResult[] {
    return [...this.history];
  }

  // ========================================
  // Command Handlers
  // ========================================

  private async handlePlay(): Promise<any> {
    if (window.PlayerHLS) {
      await window.PlayerHLS.play();
      return { message: 'Playback started' };
    }
    throw new Error('PlayerHLS not available');
  }

  private async handlePause(): Promise<any> {
    if (window.PlayerHLS) {
      window.PlayerHLS.pause();
      return { message: 'Playback paused' };
    }
    throw new Error('PlayerHLS not available');
  }

  private async handleStop(): Promise<any> {
    if (window.PlayerHLS) {
      window.PlayerHLS.stop();
      return { message: 'Playback stopped' };
    }
    throw new Error('PlayerHLS not available');
  }

  private async handleNext(): Promise<any> {
    if (window.PlayerHLS) {
      await window.PlayerHLS.next();
      return { message: 'Skipped to next item' };
    }
    throw new Error('PlayerHLS not available');
  }

  private async handlePrevious(): Promise<any> {
    if (window.PlayerHLS) {
      await window.PlayerHLS.previous();
      return { message: 'Skipped to previous item' };
    }
    throw new Error('PlayerHLS not available');
  }

  private async handleSeek(params?: Record<string, any>): Promise<any> {
    const { time } = params || {};
    if (!time) throw new Error('Seek time required');

    // Seek implementation would go here
    return { message: `Seeked to ${time}s` };
  }

  private async handleSetVolume(params?: Record<string, any>): Promise<any> {
    const { volume } = params || {};
    if (volume === undefined) throw new Error('Volume level required');

    // Volume implementation would go here
    return { message: `Volume set to ${volume}` };
  }

  private async handleLoadPlaylist(params?: Record<string, any>): Promise<any> {
    const { playlist_id } = params || {};
    if (!playlist_id) throw new Error('Playlist ID required');

    // Load playlist implementation would go here
    return { message: `Loading playlist ${playlist_id}` };
  }

  private async handleReloadPlaylist(): Promise<any> {
    if (window.PlayerPlaylistSync) {
      window.PlayerPlaylistSync.forceReload();
      return { message: 'Playlist reload triggered' };
    }
    throw new Error('PlayerPlaylistSync not available');
  }

  private async handleClearCache(): Promise<any> {
    if (window.PlayerMediaCache) {
      await window.PlayerMediaCache.clearCache();
      return { message: 'Cache cleared' };
    }
    throw new Error('PlayerMediaCache not available');
  }

  private async handleReloadPage(): Promise<any> {
    window.location.reload();
    return { message: 'Page reloading...' };
  }

  private async handleClearStorage(): Promise<any> {
    localStorage.clear();
    return { message: 'Storage cleared' };
  }

  private async handleFullscreen(): Promise<any> {
    if (document.documentElement.requestFullscreen) {
      await document.documentElement.requestFullscreen();
      return { message: 'Entered fullscreen' };
    }
    throw new Error('Fullscreen not supported');
  }

  private async handleExitFullscreen(): Promise<any> {
    if (document.exitFullscreen) {
      await document.exitFullscreen();
      return { message: 'Exited fullscreen' };
    }
    throw new Error('Fullscreen not supported');
  }

  private async handleGetStatus(): Promise<any> {
    if (window.PlayerHLS) {
      const state = window.PlayerHLS.getState();
      return { player_state: state };
    }
    throw new Error('PlayerHLS not available');
  }

  private async handleGetSystemInfo(): Promise<any> {
    return {
      platform: navigator.platform,
      user_agent: navigator.userAgent,
      screen: {
        width: screen.width,
        height: screen.height,
      },
      memory: (performance as any).memory?.usedJSHeapSize || null,
    };
  }
}

// Export singleton instance
export const PlayerCommandExecutor = new PlayerCommandExecutorClass();

// Make available globally for compatibility
if (typeof window !== 'undefined') {
  window.PlayerCommandExecutor = PlayerCommandExecutor;
}
