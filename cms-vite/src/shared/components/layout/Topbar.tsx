/**
 * Topbar Component
 *
 * LAYER 1: PRESENTATION
 * Top navigation bar (optional breadcrumbs, notifications, etc.)
 */

import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/lib/stores/authStore';
import { useCurrentOrganization } from '@/features/auth/hooks/useAuth';
import { Building2 } from 'lucide-react';
import { WebSocketStatus } from '@/lib/websocket/WebSocketStatus';

export default function Topbar() {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const currentOrg = useCurrentOrganization();

  return (
    <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3 lg:px-6">
      <div className="flex items-center justify-between">
        {/* Left: Organization Info */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <Building2 className="w-4 h-4" />
            <span>{currentOrg?.name || t('dashboard.noOrganization')}</span>
          </div>

          {/* WebSocket Status */}
          <WebSocketStatus />
        </div>

        {/* Right: User Badge (optional) */}
        <div className="hidden sm:flex items-center gap-2">
          <div className="text-right">
            <p className="text-sm font-medium text-gray-900 dark:text-white">
              {user?.full_name || user?.username}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {user?.email || user?.role}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
