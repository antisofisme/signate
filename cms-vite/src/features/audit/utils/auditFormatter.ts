/**
 * Audit Formatter Utility
 *
 * Converts raw audit log details to human-readable format
 * Supports before/after diff, action-specific formatting, and i18n
 */

import type { AuditLog } from '../types/auditLog';

export interface FormattedAuditDetail {
  summary: string;
  changes?: ChangeItem[];
  metadata?: MetadataItem[];
  rawDetails?: Record<string, any>;
}

export interface ChangeItem {
  field: string;
  fieldLabel: string;
  before: any;
  after: any;
  type: 'added' | 'removed' | 'changed';
}

export interface MetadataItem {
  label: string;
  value: string | number | boolean;
  type?: 'text' | 'link' | 'badge' | 'code';
}

/**
 * Field labels for human-readable display
 */
const FIELD_LABELS: Record<string, string> = {
  // User fields
  username: 'Username',
  email: 'Email',
  full_name: 'Full Name',
  role: 'Role',
  role_id: 'Role',
  is_active: 'Active Status',
  phone: 'Phone',

  // Device fields
  device_name: 'Device Name',
  device_code: 'Device Code',
  unique_code: 'Activation Code',
  status: 'Status',
  location: 'Location',
  device_type: 'Device Type',
  resolution: 'Resolution',
  orientation: 'Orientation',
  volume: 'Volume',
  is_volume_enabled: 'Volume Enabled',
  is_muted: 'Muted',

  // Content fields
  name: 'Name',
  title: 'Title',
  description: 'Description',
  file_name: 'File Name',
  file_size: 'File Size',
  file_type: 'File Type',
  content_type: 'Content Type',
  duration: 'Duration',

  // Playlist fields
  playlist_name: 'Playlist Name',
  is_default: 'Default Playlist',

  // Organization fields
  organization_name: 'Organization',
  organization_id: 'Organization ID',

  // Common fields
  created_at: 'Created At',
  updated_at: 'Updated At',
  id: 'ID',
};

/**
 * Get human-readable field label
 */
export function getFieldLabel(field: string): string {
  return FIELD_LABELS[field] || field.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Format value for display
 */
export function formatValue(value: any): string {
  if (value === null || value === undefined) {
    return '-';
  }
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2);
  }
  if (typeof value === 'number' && String(value).length > 10) {
    // Likely a timestamp
    try {
      const date = new Date(value);
      if (!isNaN(date.getTime())) {
        return date.toLocaleString();
      }
    } catch {
      // Not a date
    }
  }
  return String(value);
}

/**
 * Generate action summary in human-readable format
 */
export function generateActionSummary(log: AuditLog): string {
  const { action, resource_type, details, username } = log;
  const actor = username || 'System';

  // Extract resource name from details if available
  const resourceName = details?.name || details?.username || details?.device_name ||
                       details?.title || details?.email || `#${log.resource_id}`;

  const summaries: Record<string, string> = {
    // Auth actions
    'auth.login': `${actor} logged in`,
    'auth.logout': `${actor} logged out`,
    'auth.register': `New user "${resourceName}" registered`,
    'auth.password_change': `${actor} changed password`,

    // User actions
    'user.create': `${actor} created user "${resourceName}"`,
    'user.update': `${actor} updated user "${resourceName}"`,
    'user.delete': `${actor} deleted user "${resourceName}"`,
    'user.change_password': `${actor} changed password for "${resourceName}"`,

    // Device actions
    'device.create': `${actor} registered device "${resourceName}"`,
    'device.update': `${actor} updated device "${resourceName}"`,
    'device.delete': `${actor} deleted device "${resourceName}"`,
    'device.activate': `Device "${resourceName}" was activated`,
    'device.deactivate': `Device "${resourceName}" was deactivated`,
    'device.assign_playlist': `${actor} assigned playlist to device "${resourceName}"`,
    'device.unassign_playlist': `${actor} removed playlist from device "${resourceName}"`,

    // Content actions
    'content.upload': `${actor} uploaded content "${resourceName}"`,
    'content.create': `${actor} created content "${resourceName}"`,
    'content.update': `${actor} updated content "${resourceName}"`,
    'content.delete': `${actor} deleted content "${resourceName}"`,
    'content.assign': `${actor} assigned content "${resourceName}"`,

    // Playlist actions
    'playlist.create': `${actor} created playlist "${resourceName}"`,
    'playlist.update': `${actor} updated playlist "${resourceName}"`,
    'playlist.delete': `${actor} deleted playlist "${resourceName}"`,
    'playlist.assign': `${actor} assigned playlist "${resourceName}"`,

    // Organization actions
    'organization.create': `${actor} created organization "${resourceName}"`,
    'organization.update': `${actor} updated organization "${resourceName}"`,
    'organization.delete': `${actor} deleted organization "${resourceName}"`,

    // Schedule actions
    'schedule.create': `${actor} created schedule "${resourceName}"`,
    'schedule.update': `${actor} updated schedule "${resourceName}"`,
    'schedule.delete': `${actor} deleted schedule "${resourceName}"`,
  };

  return summaries[action] || `${actor} performed "${action}" on ${resource_type}`;
}

/**
 * Extract changes (before/after) from audit details
 */
export function extractChanges(details: Record<string, any> | null): ChangeItem[] {
  if (!details) return [];

  const changes: ChangeItem[] = [];

  // Check for explicit before/after structure
  if (details.before && details.after) {
    const before = details.before;
    const after = details.after;

    // Get all keys from both objects
    const allKeys = new Set([...Object.keys(before), ...Object.keys(after)]);

    for (const key of allKeys) {
      // Skip internal/meta fields
      if (['id', 'created_at', 'updated_at', 'password_hash'].includes(key)) continue;

      const beforeVal = before[key];
      const afterVal = after[key];

      if (beforeVal !== afterVal) {
        let type: 'added' | 'removed' | 'changed' = 'changed';
        if (beforeVal === undefined || beforeVal === null) type = 'added';
        else if (afterVal === undefined || afterVal === null) type = 'removed';

        changes.push({
          field: key,
          fieldLabel: getFieldLabel(key),
          before: beforeVal,
          after: afterVal,
          type,
        });
      }
    }
  }

  // Check for changes array format
  if (Array.isArray(details.changes)) {
    for (const change of details.changes) {
      changes.push({
        field: change.field || change.key,
        fieldLabel: getFieldLabel(change.field || change.key),
        before: change.old_value ?? change.before,
        after: change.new_value ?? change.after,
        type: change.type || 'changed',
      });
    }
  }

  return changes;
}

/**
 * Extract metadata from audit details
 */
export function extractMetadata(log: AuditLog): MetadataItem[] {
  const metadata: MetadataItem[] = [];
  const { details, ip_address, user_agent } = log;

  // Add IP address
  if (ip_address) {
    metadata.push({
      label: 'IP Address',
      value: ip_address,
      type: 'code',
    });
  }

  // Add user agent (truncated)
  if (user_agent) {
    metadata.push({
      label: 'User Agent',
      value: user_agent.length > 100 ? user_agent.substring(0, 100) + '...' : user_agent,
      type: 'code',
    });
  }

  // Extract common metadata from details
  if (details) {
    // File info for content uploads
    if (details.file_name) {
      metadata.push({ label: 'File Name', value: details.file_name });
    }
    if (details.file_size) {
      metadata.push({ label: 'File Size', value: formatFileSize(details.file_size) });
    }
    if (details.file_type || details.content_type) {
      metadata.push({ label: 'File Type', value: details.file_type || details.content_type });
    }

    // Device info
    if (details.device_type) {
      metadata.push({ label: 'Device Type', value: details.device_type });
    }
    if (details.resolution) {
      metadata.push({ label: 'Resolution', value: details.resolution });
    }

    // Session info for login
    if (details.session_id) {
      metadata.push({ label: 'Session ID', value: details.session_id, type: 'code' });
    }
  }

  return metadata;
}

/**
 * Format file size to human-readable
 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Main formatter function - creates complete formatted audit detail
 */
export function formatAuditDetail(log: AuditLog): FormattedAuditDetail {
  return {
    summary: generateActionSummary(log),
    changes: extractChanges(log.details),
    metadata: extractMetadata(log),
    rawDetails: log.details || undefined,
  };
}

/**
 * Get action category color
 */
export function getActionColor(action: string): string {
  if (action.includes('create') || action.includes('register'))
    return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
  if (action.includes('update') || action.includes('change'))
    return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
  if (action.includes('delete') || action.includes('remove'))
    return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
  if (action.includes('login') || action.includes('logout'))
    return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400';
  if (action.includes('assign') || action.includes('activate'))
    return 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400';
  return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
}

/**
 * Get change type color
 */
export function getChangeTypeColor(type: 'added' | 'removed' | 'changed'): string {
  switch (type) {
    case 'added':
      return 'text-green-600 dark:text-green-400';
    case 'removed':
      return 'text-red-600 dark:text-red-400';
    case 'changed':
    default:
      return 'text-blue-600 dark:text-blue-400';
  }
}
