/**
 * Shared Layer Type Definitions
 * Types for WebSocket, common utilities, and cross-cutting concerns
 */

// ========================================
// WebSocket Types
// ========================================

export enum WSMessageType {
  // Control messages
  PING = 'ping',
  PONG = 'pong',
  AUTH = 'auth',

  // Command messages
  COMMAND = 'command',
  COMMAND_RESPONSE = 'command_response',

  // Playlist messages
  PLAYLIST_UPDATE = 'playlist_update',
  CONTENT_UPDATE = 'content_update',

  // Device messages
  DEVICE_STATUS = 'device_status',
  DEVICE_CONFIG = 'device_config',

  // Player messages
  PLAYER_STATE = 'player_state',
  PLAYER_CONTROL = 'player_control',
}

export interface WSMessage<T = any> {
  type: WSMessageType;
  data: T;
  timestamp?: string;
  id?: string;
}

export enum WSState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error',
}

export interface SharedWebSocket {
  connect(): void;
  disconnect(): void;
  send<T = any>(type: WSMessageType, data: T): void;
  onMessage<T = any>(type: WSMessageType, handler: (data: T) => void): void;
  offMessage(type: WSMessageType, handler: Function): void;
  isConnected(): boolean;
  getState(): WSState;
}

// ========================================
// Device Info Popup Types
// ========================================

export interface DeviceInfoPopup {
  init(): void;
  open(): Promise<void>;
}
