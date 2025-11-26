/**
 * Sessions Page
 *
 * LAYER 1: PRESENTATION
 * Main page for session management - orchestration only
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { LogOut, Shield } from 'lucide-react';
import { PageHeader } from '@/shared/components';
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

  // Queries
  const { data: sessionsData, isLoading: sessionsLoading } = useSessions();
  const { data: stats } = useSessionStats();
  const { currentSession } = useCurrentSession();

  // Mutations
  const revokeSessionMutation = useRevokeSession();
  const revokeAllMutation = useRevokeAllSessions();

  // Handlers
  const handleRevokeSession = (session: Session) => {
    if (
      confirm(
        t('sessions.confirmRevokeSession', {
          device: session.device_info?.browser || t('sessions.unknownDevice'),
          ip: session.ip_address,
        })
      )
    ) {
      revokeSessionMutation.mutate({
        session_id: session.id,
        reason: 'User revoked session manually',
      });
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
  if (sessionsLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500 dark:text-gray-400">{t('sessions.loadingSessions')}</div>
      </div>
    );
  }

  return (
    <>
      <PageHeader
        title={t('sessions.title')}
        description={t('sessions.description')}
      />

      <div className="space-y-6">
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

        {/* Logout All Button */}
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
          <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {t('sessions.noActiveSessions')}
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              {t('sessions.noActiveSessionsDescription')}
            </p>
          </div>
        )}
      </div>

      {/* Revoke All Confirmation Modal */}
      <RevokeAllModal
        isOpen={showRevokeAllModal}
        otherSessionsCount={otherSessionsCount}
        isRevoking={revokeAllMutation.isPending}
        onClose={() => setShowRevokeAllModal(false)}
        onConfirm={handleRevokeAll}
      />
    </>
  );
}
