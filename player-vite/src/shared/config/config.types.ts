/**
 * Configuration type definitions
 * Central types for all config values
 */

export interface ApiConfig {
  baseURL: string;
  wsBaseURL: string;
  timeout: number;
}

export interface DeviceConfig {
  heartbeatInterval: number;
  logSendInterval: number;
  logBufferSize: number;
}

export interface RetryConfig {
  maxRetryCount: number;
  initialRetryDelay: number;
  maxRetryDelay: number;
  backoffMultiplier: number;
}

export interface LogConfig {
  level: 'debug' | 'log' | 'info' | 'warn' | 'error' | 'silent';
  enableConsole: boolean;
}

export interface DebugConfig {
  debugMode: boolean;
  apiDebug: boolean;
  wsDebug: boolean;
}

export interface PlayerConfig {
  version: string;
}

export interface AppConfig {
  api: ApiConfig;
  device: DeviceConfig;
  retry: RetryConfig;
  log: LogConfig;
  debug: DebugConfig;
  player: PlayerConfig;
}
