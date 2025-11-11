/**
 * Device Command Types
 * Based on backend DTOs from services/device/dtos.py
 */

export type CommandType =
  | 'reboot'
  | 'refresh_content'
  | 'update_settings'
  | 'clear_cache'
  | 'screenshot'
  | 'update_playlist'
  | 'reset'
  | 'refresh'
  | 'reload'
  | 'volume'
  | 'brightness'
  | 'speed_test'
  | 'update_content';

export type CommandStatus = 'pending' | 'sent' | 'executed' | 'failed' | 'expired';

export interface DeviceCommand {
  id: number;
  device_id: number;
  organization_id: number;
  command_type: CommandType;
  command_data?: Record<string, any>;
  parameters?: Record<string, any>;
  reason?: string;
  status: CommandStatus;
  priority?: number;
  sent_at?: string;
  executed_at?: string;
  failed_at?: string;
  result?: Record<string, any>;
  error_message?: string;
  retry_count?: number;
  max_retries?: number;
  created_by?: number;
  created_at: string;
  updated_at?: string;
  expires_at?: string;
}

export interface SendCommandRequest {
  command_type: CommandType;
  command_data?: Record<string, any>;
  parameters?: Record<string, any>;
  reason?: string;
  priority?: number;
  expires_in_minutes?: number;
}

export interface BulkSendCommandRequest {
  device_ids: number[];
  command_type: CommandType;
  command_data?: Record<string, any>;
  priority?: number;
  expires_in_minutes?: number;
}

export interface CommandListResponse {
  total: number;
  items: DeviceCommand[];
}

export interface PendingCommandsResponse {
  commands: DeviceCommand[];
  count: number;
}

export interface CommandExecutionRequest {
  result?: Record<string, any>;
}

export interface CommandFailureRequest {
  error_message: string;
}
