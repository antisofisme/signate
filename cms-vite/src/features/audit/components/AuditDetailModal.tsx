/**
 * Audit Detail Modal Component
 *
 * Displays audit log details in human-readable format
 * with before/after diff view and formatted metadata
 *
 * Features:
 * - Human-readable action summary
 * - Before/After change comparison
 * - Formatted metadata display
 * - Raw JSON view toggle
 * - Copy to clipboard
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { format } from 'date-fns';
import {
  Copy,
  CheckCircle,
  ArrowRight,
  Plus,
  Minus,
  RefreshCw,
  Code,
  Eye,
  User,
  Clock,
  Globe,
  Server,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Modal, Button } from '@/shared/components';
import type { AuditLog } from '../types/auditLog';
import {
  formatAuditDetail,
  formatValue,
  getActionColor,
  getChangeTypeColor,
  type ChangeItem,
  type MetadataItem,
} from '../utils/auditFormatter';

interface AuditDetailModalProps {
  log: AuditLog | null;
  isOpen: boolean;
  onClose: () => void;
}

export function AuditDetailModal({ log, isOpen, onClose }: AuditDetailModalProps) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const [showRawJson, setShowRawJson] = useState(false);

  if (!isOpen || !log) return null;

  const formatted = formatAuditDetail(log);

  const handleCopy = async () => {
    const copyText = `
=== Audit Log Details ===
ID: ${log.id}
Action: ${log.action}
Resource: ${log.resource_type} (ID: ${log.resource_id})
User: ${log.username || 'System'}
Organization: ${log.organization_name || '-'}
Timestamp: ${format(new Date(log.created_at), 'PPpp')}
IP Address: ${log.ip_address || '-'}

Summary: ${formatted.summary}

${formatted.changes && formatted.changes.length > 0 ? `Changes:
${formatted.changes.map(c => `- ${c.fieldLabel}: "${formatValue(c.before)}" -> "${formatValue(c.after)}"`).join('\n')}` : ''}

${log.details ? `\nRaw Details:\n${JSON.stringify(log.details, null, 2)}` : ''}
    `.trim();

    try {
      await navigator.clipboard.writeText(copyText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  // Custom header
  const customHeader = (
    <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          {t('audit.detail.title', 'Audit Log Details')}
        </h2>
        <Badge className={getActionColor(log.action)}>{log.action}</Badge>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={() => setShowRawJson(!showRawJson)}
          className={`px-3 py-1.5 text-sm rounded-lg transition-colors flex items-center gap-2 ${
            showRawJson
              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
          }`}
          title={showRawJson ? 'Show formatted' : 'Show raw JSON'}
        >
          {showRawJson ? <Eye className="w-4 h-4" /> : <Code className="w-4 h-4" />}
          {showRawJson ? 'Formatted' : 'Raw JSON'}
        </button>
        <button
          onClick={handleCopy}
          className="px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
          title="Copy to clipboard"
        >
          {copied ? (
            <>
              <CheckCircle className="w-4 h-4 text-green-600" />
              {t('common.copied', 'Copied!')}
            </>
          ) : (
            <>
              <Copy className="w-4 h-4" />
              {t('common.copy', 'Copy')}
            </>
          )}
        </button>
      </div>
    </div>
  );

  // Footer
  const footer = (
    <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
      <Button variant="secondary" onClick={onClose}>
        {t('common.close', 'Close')}
      </Button>
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
      className="max-h-[85vh]"
    >
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Summary Section */}
        <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-lg text-gray-900 dark:text-white font-medium">
            {formatted.summary}
          </p>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* User */}
          <MetadataCard
            icon={<User className="w-4 h-4" />}
            label={t('audit.table.user', 'User')}
            value={log.username || t('audit.system', 'System')}
            subValue={log.organization_name}
          />

          {/* Timestamp */}
          <MetadataCard
            icon={<Clock className="w-4 h-4" />}
            label={t('audit.table.timestamp', 'Timestamp')}
            value={format(new Date(log.created_at), 'MMM dd, yyyy')}
            subValue={format(new Date(log.created_at), 'HH:mm:ss')}
          />

          {/* Resource */}
          <MetadataCard
            icon={<Server className="w-4 h-4" />}
            label={t('audit.table.resource', 'Resource')}
            value={log.resource_type}
            subValue={log.resource_id ? `ID: ${log.resource_id}` : undefined}
          />

          {/* IP Address */}
          <MetadataCard
            icon={<Globe className="w-4 h-4" />}
            label={t('audit.table.ipAddress', 'IP Address')}
            value={log.ip_address || '-'}
            mono
          />
        </div>

        {/* Changes Section - Before/After Diff */}
        {formatted.changes && formatted.changes.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <RefreshCw className="w-4 h-4" />
              {t('audit.detail.changes', 'Changes')}
            </h3>
            <div className="space-y-2">
              {formatted.changes.map((change, index) => (
                <ChangeRow key={index} change={change} />
              ))}
            </div>
          </div>
        )}

        {/* Additional Metadata */}
        {formatted.metadata && formatted.metadata.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              {t('audit.detail.additionalInfo', 'Additional Information')}
            </h3>
            <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg space-y-2">
              {formatted.metadata.map((item, index) => (
                <MetadataRow key={index} item={item} />
              ))}
            </div>
          </div>
        )}

        {/* Raw JSON View */}
        {showRawJson && log.details && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
              <Code className="w-4 h-4" />
              {t('audit.detail.rawJson', 'Raw JSON')}
            </h3>
            <div className="p-4 bg-gray-900 dark:bg-gray-950 rounded-lg border border-gray-700 overflow-x-auto">
              <pre className="text-sm text-green-400 font-mono whitespace-pre-wrap">
                {JSON.stringify(log.details, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* Empty State for No Details */}
        {!formatted.changes?.length && !formatted.metadata?.length && !log.details && (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <Code className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>{t('audit.detail.noDetails', 'No additional details available')}</p>
          </div>
        )}
      </div>
    </Modal>
  );
}

// Metadata Card Component
interface MetadataCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  subValue?: string;
  mono?: boolean;
}

function MetadataCard({ icon, label, value, subValue, mono }: MetadataCardProps) {
  return (
    <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
      <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 mb-1">
        {icon}
        {label}
      </div>
      <p className={`text-sm text-gray-900 dark:text-white ${mono ? 'font-mono' : 'font-medium'}`}>
        {value}
      </p>
      {subValue && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{subValue}</p>
      )}
    </div>
  );
}

// Change Row Component - Before/After Diff
interface ChangeRowProps {
  change: ChangeItem;
}

function ChangeRow({ change }: ChangeRowProps) {
  const getIcon = () => {
    switch (change.type) {
      case 'added':
        return <Plus className="w-4 h-4 text-green-500" />;
      case 'removed':
        return <Minus className="w-4 h-4 text-red-500" />;
      default:
        return <ArrowRight className="w-4 h-4 text-blue-500" />;
    }
  };

  return (
    <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
      <div className="flex items-center gap-2 mb-2">
        {getIcon()}
        <span className={`text-sm font-medium ${getChangeTypeColor(change.type)}`}>
          {change.fieldLabel}
        </span>
      </div>
      <div className="flex items-center gap-3 text-sm">
        {change.type !== 'added' && (
          <div className="flex-1 p-2 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
            <span className="text-red-700 dark:text-red-300 font-mono text-xs break-all">
              {formatValue(change.before)}
            </span>
          </div>
        )}
        {change.type === 'changed' && (
          <ArrowRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
        )}
        {change.type !== 'removed' && (
          <div className="flex-1 p-2 bg-green-50 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-800">
            <span className="text-green-700 dark:text-green-300 font-mono text-xs break-all">
              {formatValue(change.after)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

// Metadata Row Component
interface MetadataRowProps {
  item: MetadataItem;
}

function MetadataRow({ item }: MetadataRowProps) {
  return (
    <div className="flex items-start justify-between py-1">
      <span className="text-xs text-gray-500 dark:text-gray-400">{item.label}</span>
      <span
        className={`text-sm text-gray-900 dark:text-white text-right max-w-[60%] break-all ${
          item.type === 'code' ? 'font-mono text-xs' : ''
        }`}
      >
        {String(item.value)}
      </span>
    </div>
  );
}

export default AuditDetailModal;
