/**
 * Logger Type Definitions
 */

export type LogLevel = 'debug' | 'log' | 'info' | 'warn' | 'error' | 'silent';

export interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  source: string;
}

export interface LoggerConfig {
  level: LogLevel;
  enabled: boolean;
  maxBufferSize: number;
  flushInterval: number;
}

export interface Logger {
  debug(...args: unknown[]): void;
  log(...args: unknown[]): void;
  info(...args: unknown[]): void;
  warn(...args: unknown[]): void;
  error(...args: unknown[]): void;
  setLevel(level: LogLevel): void;
  getLevel(): LogLevel;
  enable(): void;
  disable(): void;
  isEnabled(): boolean;
  getBuffer(): LogEntry[];
  clearBuffer(): void;
  flush(): Promise<void>;
}
