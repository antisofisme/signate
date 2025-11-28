/**
 * Sessions Page
 *
 * LAYER 1: PRESENTATION
 * Main page for session management - orchestration only
 *
 * Multi-tenancy support:
 * - Super Admin: sees all sessions from all organizations
 * - Admin: sees sessions from their organization only
 * - Others: only see their own sessions
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { LogOut, Shield, Users, User, Monitor, Globe, Clock, Building2, Smartphone } from 'lucide-react';
import {
  PageSkeleton,
  EmptyState,
  ConfirmDialog,
  AccessDenied
} from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { useAuthStore } from '@/lib/stores/authStore';
import { USER_ROLES } from '@/lib/constants/app';
import { SessionCard } from '../components/SessionCard';
import { SessionStats } from '../components/SessionStats';
import { SecurityWarning } from '../components/SecurityWarning';
import { RevokeAllModal } from '../components/RevokeAllModal';
import {
  useSessions,
  useSessionStats,
  useRevokeSession,
  useRevokeAllSessions,
  useCurrentSession,
  useAllActiveSessions,
} from '../hooks/useSessions';
import type { Session, AllSession } from '../types/session.types';
import { parseUserAgent, getBrowserString, getOSString } from '@/shared/utils/userAgentParser';

type ViewTab = 'my-sessions' | 'all-sessions';

export default function SessionsPage() {
  const { t } = useTranslation();
  const [showRevokeAllModal, setShowRevokeAllModal] = useState(false);
  const [sessionToRevoke, setSessionToRevoke] = useState<Session | null>(null);
  const [activeTab, setActiveTab] = useState<ViewTab>('my-sessions');

  // Get current user for role check
  const { user } = useAuthStore();
  // Show All Sessions tab based on sessions:read permission (not hardcoded role)
  // Super Admin always has all permissions, custom roles with sessions:read can also view
  const { hasPermission: canViewAllSessions } = useCanPerformAction('sessions', 'read');
  const showAllSessionsTab = canViewAllSessions;
  const showOrgColumn = user?.role === USER_ROLES.SUPER_ADMIN;

  // Permission checks
  const { hasPermission: canView, isLoading: permissionLoading } = useCanPerformAction('sessions', 'read');
  const { hasPermission: canDeleteOthers } = useCanPerformAction('sessions', 'delete');

  // Users can always revoke their own sessions (My Sessions tab)
  // canDeleteOthers is for admin to revoke other users' sessions (All Sessions tab)

  // Queries - My Sessions
  const { data: sessionsData, isLoading: sessionsLoading } = useSessions();
  const { data: stats } = useSessionStats();
  const { currentSession } = useCurrentSession();

  // Queries - All Sessions (for admin view)
  const { data: allSessionsData, isLoading: allSessionsLoading } = useAllActiveSessions(
    showAllSessionsTab && activeTab === 'all-sessions' ? { skip: 0, limit: 50 } : undefined
  );

  // Mutations
  const revokeSessionMutation = useRevokeSession();
  const revokeAllMutation = useRevokeAllSessions();

  // Handlers
  const handleRevokeSession = (session: Session) => {
    setSessionToRevoke(session);
  };

  const confirmRevokeSession = () => {
    if (sessionToRevoke) {
      revokeSessionMutation.mutate({
        session_id: sessionToRevoke.id,
        reason: 'User revoked session manually',
      });
      setSessionToRevoke(null);
    }
  };

  const handleRevokeAll = () => {
    revokeAllMutation.mutate(
      { except_current: true },
      {
        onSuccess: () => {
          setShowRevokeAllModal(false);
        },
      }
    );
  };

  // Group sessions
  const activeSessions = sessionsData?.sessions.filter((s) => !s.is_current) || [];
  const otherSessionsCount = activeSessions.length;

  // Helper function to format time ago
  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return t('sessions.justNow', 'Just now');
    if (diffMins < 60) return t('sessions.minutesAgo', '{{count}} min ago', { count: diffMins });
    if (diffHours < 24) return t('sessions.hoursAgo', '{{count}} hours ago', { count: diffHours });
    return t('sessions.daysAgo', '{{count}} days ago', { count: diffDays });
  };

  // Loading state
  if (permissionLoading || sessionsLoading) {
    return <PageSkeleton showFilters={false} showTable={false} tableRows={3} />;
  }

  // Permission check
  if (!canView) {
    return <AccessDenied />;
  }

  return (
    <div className="space-y-6">
      {/* Tab Navigation (for admins only) */}
      {showAllSessionsTab && (
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('my-sessions')}
              className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                activeTab === 'my-sessions'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              <User className="w-4 h-4" />
              {t('sessions.mySessions', 'My Sessions')}
            </button>
            <button
              onClick={() => setActiveTab('all-sessions')}
              className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                activeTab === 'all-sessions'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              <Users className="w-4 h-4" />
              {t('sessions.allUsersSessions', 'All Users Sessions')}
              {allSessionsData && (
                <span className="ml-2 px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 rounded-full text-xs">
                  {allSessionsData.total}
                </span>
              )}
            </button>
          </nav>
        </div>
      )}

      {/* My Sessions Tab Content */}
      {activeTab === 'my-sessions' && (
        <>
          {/* Stats Cards */}
          <SessionStats
            total={sessionsData?.total || 0}
            desktop={stats?.sessions_by_device?.desktop || 0}
            mobile={stats?.sessions_by_device?.mobile || 0}
            tablet={stats?.sessions_by_device?.tablet || 0}
          />

          {/* Security Warning */}
          <SecurityWarning
            sessionCount={otherSessionsCount}
            onRevokeAll={() => setShowRevokeAllModal(true)}
          />

          {/* Logout All Button - users can always revoke their own sessions */}
          {otherSessionsCount > 0 && (
            <div className="flex justify-end">
              <button
                onClick={() => setShowRevokeAllModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
              >
                <LogOut className="w-5 h-5" />
                {t('sessions.logoutAllDevices')}
              </button>
            </div>
          )}

          {/* Current Session */}
          {currentSession && (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                {t('sessions.currentSession')}
              </h2>
              <SessionCard session={currentSession} />
            </div>
          )}

          {/* Other Sessions */}
          {activeSessions.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                {t('sessions.otherSessions', { count: activeSessions.length })}
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {activeSessions.map((session) => (
                  <SessionCard
                    key={session.id}
                    session={session}
                    onRevoke={handleRevokeSession}
                    isRevoking={revokeSessionMutation.isPending}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {!currentSession && activeSessions.length === 0 && (
            <EmptyState
              icon={Shield}
              title={t('sessions.noActiveSessions')}
              description={t('sessions.noActiveSessionsDescription')}
            />
          )}
        </>
      )}

      {/* All Sessions Tab Content (Admin View) */}
      {activeTab === 'all-sessions' && showAllSessionsTab && (
        <div className="space-y-4">
          {/* Info Banner */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <Users className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
              <div>
                <h3 className="text-sm font-medium text-blue-800 dark:text-blue-300">
                  {showOrgColumn
                    ? t('sessions.superAdminView', 'Super Admin View')
                    : t('sessions.adminView', 'Organization Admin View')}
                </h3>
                <p className="text-sm text-blue-600 dark:text-blue-400 mt-1">
                  {showOrgColumn
                    ? t('sessions.superAdminViewDesc', 'Viewing all active sessions across all organizations')
                    : t('sessions.adminViewDesc', 'Viewing all active sessions in your organization')}
                </p>
              </div>
            </div>
          </div>

          {/* All Sessions Table */}
          {allSessionsLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : allSessionsData && allSessionsData.items.length > 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-900">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        {t('sessions.user', 'User')}
                      </th>
                      {showOrgColumn && (
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          {t('sessions.organization', 'Organization')}
                        </th>
                      )}
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        {t('sessions.browser', 'Browser')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        {t('sessions.ipAddress', 'IP Address')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        {t('sessions.lastActivity', 'Last Activity')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        {t('sessions.expiresAt', 'Expires')}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {allSessionsData.items.map((session: AllSession) => (
                      <tr key={session.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-10 w-10 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                              <User className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900 dark:text-white">
                                {session.full_name || session.username}
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                {session.email}
                              </div>
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300">
                                {session.role}
                              </span>
                            </div>
                          </div>
                        </td>
                        {showOrgColumn && (
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center gap-2">
                              <Building2 className="w-4 h-4 text-gray-400" />
                              <span className="text-sm text-gray-900 dark:text-white">
                                {session.organization_name || '-'}
                              </span>
                            </div>
                          </td>
                        )}
                        <td className="px-6 py-4 whitespace-nowrap">
                          {(() => {
                            const parsed = parseUserAgent(session.user_agent);
                            return (
                              <div className="flex items-center gap-2">
                                {parsed.device === 'mobile' ? (
                                  <Smartphone className="w-4 h-4 text-gray-400" />
                                ) : (
                                  <Monitor className="w-4 h-4 text-gray-400" />
                                )}
                                <div>
                                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                                    {getBrowserString(parsed)}
                                  </div>
                                  <div className="text-xs text-gray-500 dark:text-gray-400">
                                    {getOSString(parsed)}
                                  </div>
                                </div>
                              </div>
                            );
                          })()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-2 text-sm text-gray-900 dark:text-white">
                            <Globe className="w-4 h-4 text-gray-400" />
                            <span className="font-mono text-xs">{session.ip_address}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                            <Clock className="w-4 h-4" />
                            {formatTimeAgo(session.last_activity_at)}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {new Date(session.expires_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination Info */}
              <div className="px-6 py-3 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {t('sessions.showingResults', 'Showing {{count}} of {{total}} active sessions', {
                    count: allSessionsData.items.length,
                    total: allSessionsData.total,
                  })}
                </p>
              </div>
            </div>
          ) : (
            <EmptyState
              icon={Users}
              title={t('sessions.noAllActiveSessions', 'No active sessions')}
              description={t('sessions.noAllActiveSessionsDesc', 'There are no active sessions at the moment')}
            />
          )}
        </div>
      )}

      {/* Revoke Session Confirmation Dialog */}
      <ConfirmDialog
        open={!!sessionToRevoke}
        onOpenChange={(open) => !open && setSessionToRevoke(null)}
        title={t('sessions.revokeSessionTitle', 'Revoke Session')}
        description={t('sessions.confirmRevokeSession', {
          device: sessionToRevoke?.device_info?.browser || t('sessions.unknownDevice'),
          ip: sessionToRevoke?.ip_address,
        })}
        variant="warning"
        confirmLabel={t('sessions.revoke', 'Revoke')}
        onConfirm={confirmRevokeSession}
        isLoading={revokeSessionMutation.isPending}
      />

      {/* Revoke All Confirmation Modal */}
      <RevokeAllModal
        isOpen={showRevokeAllModal}
        otherSessionsCount={otherSessionsCount}
        isRevoking={revokeAllMutation.isPending}
        onClose={() => setShowRevokeAllModal(false)}
        onConfirm={handleRevokeAll}
      />
    </div>
  );
}
