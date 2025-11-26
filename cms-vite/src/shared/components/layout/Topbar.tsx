/**
 * Topbar Component
 *
 * LAYER 1: PRESENTATION
 * Top navigation bar with organization switcher, notifications, and user info.
 */

import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/lib/stores/authStore';
import { WebSocketStatus } from '@/lib/websocket/WebSocketStatus';
import { OrganizationSwitcher } from './OrganizationSwitcher';

export default function Topbar() {
  const { t } = useTranslation();
  const { user } = useAuthStore();

  return (
    <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3 lg:px-6">
      <div className="flex items-center justify-between gap-4">
        {/* Left: WebSocket Status */}
        <div className="flex items-center gap-4">
          {/* WebSocket Status */}
          <WebSocketStatus />
        </div>

        {/* Right: Organization Switcher + User Badge */}
        <div className="flex items-center gap-4">
          {/* Organization Switcher */}
          <OrganizationSwitcher />

          {/* User Badge */}
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
    </div>
  );
}
