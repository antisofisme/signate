/**
 * Sessions Management Page
 * View and manage active user sessions
 */

import React, { useState } from 'react'
import { Shield, LogOut, AlertTriangle, Monitor, Smartphone, Tablet } from 'lucide-react'
import { PageHeader } from '@/shared/components'
import { SessionCard } from '@/features/sessions/components/SessionCard'
import {
  useSessions,
  useSessionStats,
  useRevokeSession,
  useRevokeAllSessions,
  useCurrentSession,
} from '@/features/sessions/hooks/useSessions'
import type { Session } from '@/features/sessions/types/session.types'

export default function SessionsPage() {
  const [showRevokeAllModal, setShowRevokeAllModal] = useState(false)

  // Queries
  const { data: sessionsData, isLoading: sessionsLoading } = useSessions()
  const { data: stats } = useSessionStats()
  const { currentSession } = useCurrentSession()

  // Mutations
  const revokeSessionMutation = useRevokeSession()
  const revokeAllMutation = useRevokeAllSessions()

  // Handlers
  const handleRevokeSession = (session: Session) => {
    if (
      confirm(
        `Are you sure you want to revoke this session?\n\nDevice: ${session.device_info?.browser || 'Unknown'}\nIP: ${session.ip_address}\n\nYou will be logged out from that device.`
      )
    ) {
      revokeSessionMutation.mutate({
        session_id: session.id,
        reason: 'User revoked session manually',
      })
    }
  }

  const handleRevokeAll = () => {
    revokeAllMutation.mutate(
      { except_current: true },
      {
        onSuccess: () => {
          setShowRevokeAllModal(false)
        },
      }
    )
  }

  // Group sessions
  const activeSessions = sessionsData?.sessions.filter((s) => !s.is_current) || []
  const otherSessionsCount = activeSessions.length

  // Loading state
  if (sessionsLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500 dark:text-gray-400">Loading sessions...</div>
      </div>
    )
  }

  return (
    <>
      <PageHeader
        title="Active Sessions"
        description="Manage your active login sessions across devices"
        icon={Shield}
      />

      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {sessionsData?.total || 0}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Total Sessions</div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <Monitor className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats?.sessions_by_device.desktop || 0}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Desktop</div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Smartphone className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats?.sessions_by_device.mobile || 0}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Mobile</div>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                <Tablet className="w-5 h-5 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats?.sessions_by_device.tablet || 0}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Tablet</div>
              </div>
            </div>
          </div>
        </div>

        {/* Security Warning */}
        {otherSessionsCount > 3 && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-yellow-900 dark:text-yellow-200 mb-1">
                  Multiple Active Sessions Detected
                </h3>
                <p className="text-sm text-yellow-800 dark:text-yellow-300 mb-3">
                  You have {otherSessionsCount} other active session(s). If you don't recognize
                  these devices, revoke them immediately to secure your account.
                </p>
                <button
                  onClick={() => setShowRevokeAllModal(true)}
                  className="text-sm font-medium text-yellow-900 dark:text-yellow-200 hover:text-yellow-700 dark:hover:text-yellow-100 underline"
                >
                  Revoke all other sessions
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Logout All Button */}
        {otherSessionsCount > 0 && (
          <div className="flex justify-end">
            <button
              onClick={() => setShowRevokeAllModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
            >
              <LogOut className="w-5 h-5" />
              Logout from All Other Devices
            </button>
          </div>
        )}

        {/* Current Session */}
        {currentSession && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Current Session
            </h2>
            <SessionCard session={currentSession} />
          </div>
        )}

        {/* Other Sessions */}
        {activeSessions.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Other Sessions ({activeSessions.length})
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
              No Active Sessions
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              You don't have any active sessions at the moment
            </p>
          </div>
        )}
      </div>

      {/* Revoke All Confirmation Modal */}
      {showRevokeAllModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Logout from All Devices?
              </h2>
            </div>

            <p className="text-gray-600 dark:text-gray-400 mb-6">
              This will logout all your active sessions except this one. You'll need to login again
              on those devices.
              <br />
              <br />
              <strong>Sessions to revoke: {otherSessionsCount}</strong>
            </p>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowRevokeAllModal(false)}
                disabled={revokeAllMutation.isPending}
                className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleRevokeAll}
                disabled={revokeAllMutation.isPending}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {revokeAllMutation.isPending ? 'Revoking...' : 'Logout All'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
