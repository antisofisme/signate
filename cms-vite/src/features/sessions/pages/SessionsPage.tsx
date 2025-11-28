/**
 * Sessions Page
 *
 * LAYER 1: PRESENTATION
 * Main page for session management - orchestration only
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { LogOut, Shield } from 'lucide-react';
import {
  PageSkeleton,
  EmptyState,
  ConfirmDialog,
  AccessDenied
} from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
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
} from '../hooks/useSessions';
import type { Session } from '../types/session.types';

export default function SessionsPage() {
  const { t } = useTranslation();
  const [showRevokeAllModal, setShowRevokeAllModal] = useState(false);
  const [sessionToRevoke, setSessionToRevoke] = useState<Session | null>(null);

  // Permission checks
  const { hasPermission: canView, isLoading: permissionLoading } = useCanPerformAction('sessions', 'read');
  const { hasPermission: canDelete } = useCanPerformAction('sessions', 'delete');

  // Queries
  const { data: sessionsData, isLoading: sessionsLoading } = useSessions();
  const { data: stats } = useSessionStats();
  const { currentSession } = useCurrentSession();

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
        {/* Stats Cards */}
        <SessionStats
          total={sessionsData?.total || 0}
          desktop={stats?.sessions_by_device?.desktop || 0}
          mobile={stats?.sessions_by_device?.mobile || 0}
          tablet={stats?.sessions_by_device?.tablet || 0}
        />

        {/* Security Warning */}
        {canDelete && (
          <SecurityWarning
            sessionCount={otherSessionsCount}
            onRevokeAll={() => setShowRevokeAllModal(true)}
          />
        )}

        {/* Logout All Button */}
        {canDelete && otherSessionsCount > 0 && (
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
                  onRevoke={canDelete ? handleRevokeSession : undefined}
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
