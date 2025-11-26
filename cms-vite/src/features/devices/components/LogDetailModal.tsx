/**
 * Log Detail Modal Component
 *
 * Displays full details of a single console log entry
 * with syntax highlighting and copy-to-clipboard functionality
 *
 * ✅ REFACTORED: Now uses shared Modal component
 * - Fixed header (title with badge and copy button)
 * - Fixed footer (close button)
 * - Scrollable content (metadata grid, message, stack trace)
 * - Click outside to close
 */

import { Copy, CheckCircle } from 'lucide-react';
import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Modal } from '@/shared/components';
import type { DeviceLog } from '../types/logs';
import { LOG_LEVEL_COLORS } from '../types/logs';

interface LogDetailModalProps {
  log: DeviceLog | null;
  isOpen: boolean;
  onClose: () => void;
}

export function LogDetailModal({ log, isOpen, onClose }: LogDetailModalProps) {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !log) return null;

  const handleCopy = async () => {
    const logText = `
=== Device Log Details ===
ID: ${log.id}
Device ID: ${log.device_id}
Level: ${log.log_level}
Timestamp: ${new Date(log.recorded_at).toLocaleString()}
Source: ${log.source || 'N/A'}
URL: ${log.url || 'N/A'}
User Agent: ${log.user_agent || 'N/A'}

Message:
${log.message}

${log.stack_trace ? `Stack Trace:\n${log.stack_trace}` : ''}
    `.trim();

    try {
      await navigator.clipboard.writeText(logText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy log:', error);
    }
  };

  // Custom header with badge and copy button
  const customHeader = (
    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Console Log Details
        </h2>
        <Badge className={LOG_LEVEL_COLORS[log.log_level]}>{log.log_level}</Badge>
      </div>
      <button
        onClick={handleCopy}
        className="px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
        title="Copy log to clipboard"
      >
        {copied ? (
          <>
            <CheckCircle className="w-4 h-4 text-green-600" />
            Copied!
          </>
        ) : (
          <>
            <Copy className="w-4 h-4" />
            Copy
          </>
        )}
      </button>
    </div>
  );

  // Footer with close button
  const footer = (
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4 bg-gray-50 dark:bg-gray-900">
      <div className="flex items-center justify-end">
        <button
          onClick={onClose}
          className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      maxWidth="4xl"
      customHeader={customHeader}
      footer={footer}
      showCloseButton={false}
      className="h-[90vh]"
    >
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Metadata Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <div>
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                Log ID
              </span>
              <p className="mt-1 text-sm text-gray-900 dark:text-white font-mono">
                #{log.id}
              </p>
            </div>
            <div>
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                Device ID
              </span>
              <p className="mt-1 text-sm text-gray-900 dark:text-white font-mono">
                #{log.device_id}
              </p>
            </div>
            <div>
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                Timestamp
              </span>
              <p className="mt-1 text-sm text-gray-900 dark:text-white">
                {new Date(log.recorded_at).toLocaleString('en-US', {
                  dateStyle: 'medium',
                  timeStyle: 'medium',
                })}
              </p>
            </div>
            <div>
              <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                Level
              </span>
              <p className="mt-1">
                <Badge className={LOG_LEVEL_COLORS[log.log_level]}>{log.log_level}</Badge>
              </p>
            </div>
            {log.source && (
              <div className="md:col-span-2">
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  Source
                </span>
                <p className="mt-1 text-sm text-gray-900 dark:text-white font-mono break-all">
                  {log.source}
                </p>
              </div>
            )}
            {log.url && (
              <div className="md:col-span-2">
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  URL
                </span>
                <p className="mt-1 text-sm text-blue-600 dark:text-blue-400 font-mono break-all">
                  {log.url}
                </p>
              </div>
            )}
            {log.user_agent && (
              <div className="md:col-span-2">
                <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                  User Agent
                </span>
                <p className="mt-1 text-xs text-gray-700 dark:text-gray-300 font-mono break-all">
                  {log.user_agent}
                </p>
              </div>
            )}
          </div>

          {/* Message */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Message
            </h3>
            <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
              <pre className="text-sm text-gray-900 dark:text-white font-mono whitespace-pre-wrap break-words">
                {log.message}
              </pre>
            </div>
          </div>

          {/* Stack Trace */}
          {log.stack_trace && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Stack Trace
              </h3>
              <div className="p-4 bg-red-50 dark:bg-red-900/10 rounded-lg border border-red-200 dark:border-red-900">
                <pre className="text-xs text-red-900 dark:text-red-200 font-mono whitespace-pre-wrap break-words overflow-x-auto">
                  {log.stack_trace}
                </pre>
              </div>
            </div>
          )}
        </div>
    </Modal>
  );
}
