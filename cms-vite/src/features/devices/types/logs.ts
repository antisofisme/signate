/**
 * Device Logs Domain Types
 *
 * Types for Console Logs and Connection Logs
 */

// ========================================
// Console Logs (device_logs table)
// ========================================

export type LogLevel = 'log' | 'info' | 'warn' | 'error' | 'debug';

export interface DeviceLog {
  id: number;
  device_id: number;
  log_level: LogLevel;
  message: string;
  source?: string;
  stack_trace?: string;
  user_agent?: string;
  url?: string;
  recorded_at: string; // ISO datetime
}

export interface LogListResponse {
  logs: DeviceLog[];
  total: number;
}

export interface LogFilters {
  log_level?: LogLevel | 'all';
  limit?: number; // 1-500, default 100
  skip?: number;  // default 0
}

// ========================================
// Connection Logs (for future use)
// ========================================

export type EventType = 'network' | 'server' | 'speed_test';

export interface ConnectionLogEntry {
  logged_at: string;
  event_type: EventType;
  status: string;
  latency_ms?: number;
  error_message?: string;
  download_speed_mbps?: number;
  upload_speed_mbps?: number;
  connection_type?: string;
  effective_type?: string;
  rtt_ms?: number;
  endpoint?: string;
  http_status?: number;
  metadata?: Record<string, any>;
}

// ========================================
// UI State Types
// ========================================

export interface LogViewerState {
  selectedLog: DeviceLog | null;
  autoRefreshEnabled: boolean;
  currentPage: number;
  pageSize: number;
}

// ========================================
// Helper Types
// ========================================

export interface LogLevelOption {
  value: LogLevel | 'all';
  label: string;
  color: string;
}

export const LOG_LEVEL_OPTIONS: LogLevelOption[] = [
  { value: 'all', label: 'All Logs', color: 'gray' },
  { value: 'log', label: 'Log', color: 'blue' },
  { value: 'info', label: 'Info', color: 'cyan' },
  { value: 'warn', label: 'Warning', color: 'yellow' },
  { value: 'error', label: 'Error', color: 'red' },
  { value: 'debug', label: 'Debug', color: 'gray' },
];

export const LOG_LEVEL_COLORS: Record<LogLevel, string> = {
  log: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  info: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200',
  warn: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  error: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  debug: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
};
