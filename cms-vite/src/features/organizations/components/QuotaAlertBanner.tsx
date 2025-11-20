/**
 * Quota Alert Banner
 *
 * Shows critical quota warnings at the top of dashboard
 * - Critical (>=95%): Red banner
 * - Warning (>=80%): Orange banner
 * - Info (>=60%): Yellow banner
 */

import { AlertTriangle, Info, XCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { OrganizationQuota } from '../types/organization';

interface QuotaAlertBannerProps {
  quota: OrganizationQuota;
  organizationId: number;
}

export function QuotaAlertBanner({ quota, organizationId }: QuotaAlertBannerProps) {
  const navigate = useNavigate();

  // Determine highest severity warning
  const getHighestSeverity = () => {
    const quotas = [
      { name: 'Devices', percentage: quota.devices.percentage_used },
      { name: 'Users', percentage: quota.users.percentage_used },
      { name: 'Content Items', percentage: quota.content.items_percentage_used },
      { name: 'Storage', percentage: quota.content.size_percentage_used },
      { name: 'Playlists', percentage: quota.playlists.percentage_used },
    ];

    const critical = quotas.filter((q) => q.percentage >= 95);
    const warning = quotas.filter((q) => q.percentage >= 80 && q.percentage < 95);
    const info = quotas.filter((q) => q.percentage >= 60 && q.percentage < 80);

    if (critical.length > 0) {
      return { level: 'critical', quotas: critical };
    }
    if (warning.length > 0) {
      return { level: 'warning', quotas: warning };
    }
    if (info.length > 0) {
      return { level: 'info', quotas: info };
    }
    return null;
  };

  const severity = getHighestSeverity();

  if (!severity) return null; // No warnings

  const { level, quotas: affectedQuotas } = severity;

  const config = {
    critical: {
      variant: 'destructive' as const,
      icon: XCircle,
      title: 'Critical: Quota Limit Reached',
      color: 'text-red-600',
      bgColor: 'bg-red-50',
    },
    warning: {
      variant: 'default' as const,
      icon: AlertTriangle,
      title: 'Warning: Approaching Quota Limit',
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
    info: {
      variant: 'default' as const,
      icon: Info,
      title: 'Info: Quota Usage High',
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
    },
  };

  const { variant, icon: Icon, title, color, bgColor } = config[level];

  const bgColorClass =
    level === 'critical'
      ? 'bg-red-50 border-red-200'
      : level === 'warning'
        ? 'bg-orange-50 border-orange-200'
        : 'bg-yellow-50 border-yellow-200';

  const textColorClass =
    level === 'critical'
      ? 'text-red-800'
      : level === 'warning'
        ? 'text-orange-800'
        : 'text-yellow-800';

  return (
    <div className={`mb-6 rounded-lg border ${bgColorClass} p-4`}>
      <div className="flex items-start gap-3">
        <Icon className={`h-5 w-5 mt-0.5 ${color}`} />
        <div className="flex-1">
          <h3 className={`font-semibold ${color} mb-2`}>{title}</h3>
          <p className="text-sm text-gray-700 mb-3">
            {level === 'critical' && (
              <>
                You have reached or exceeded quota limits. Please contact support to increase
                your limits or reduce usage.
              </>
            )}
            {level === 'warning' && (
              <>
                Your organization is approaching quota limits. Consider upgrading or cleaning
                up unused resources.
              </>
            )}
            {level === 'info' && (
              <>
                Your organization quota usage is moderate. Monitor regularly to avoid hitting
                limits.
              </>
            )}
          </p>

          <div className="flex flex-wrap gap-2 mb-3">
            {affectedQuotas.map((q) => (
              <span
                key={q.name}
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  level === 'critical'
                    ? 'bg-red-100 text-red-800'
                    : level === 'warning'
                      ? 'bg-orange-100 text-orange-800'
                      : 'bg-yellow-100 text-yellow-800'
                }`}
              >
                {q.name}: {q.percentage.toFixed(1)}%
              </span>
            ))}
          </div>

          <button
            type="button"
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              level === 'critical'
                ? 'bg-red-600 text-white hover:bg-red-700'
                : level === 'warning'
                  ? 'bg-orange-600 text-white hover:bg-orange-700'
                  : 'bg-yellow-600 text-white hover:bg-yellow-700'
            }`}
            onClick={() => navigate(`/organizations/${organizationId}`)}
          >
            View Quota Details
          </button>

          {quota.warnings.length > 0 && (
            <div className="mt-3 text-xs text-gray-600">
              <strong>Backend Warnings:</strong>
              <ul className="list-disc list-inside mt-1">
                {quota.warnings.map((warning, idx) => (
                  <li key={idx}>{warning}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
