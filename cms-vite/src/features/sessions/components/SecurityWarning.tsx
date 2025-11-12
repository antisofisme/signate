/**
 * Security Warning Component
 * Warning banner for multiple active sessions
 */

import { AlertTriangle } from 'lucide-react';

interface SecurityWarningProps {
  sessionCount: number;
  onRevokeAll: () => void;
}

export function SecurityWarning({ sessionCount, onRevokeAll }: SecurityWarningProps) {
  if (sessionCount <= 3) return null;

  return (
    <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="font-semibold text-yellow-900 dark:text-yellow-200 mb-1">
            Multiple Active Sessions Detected
          </h3>
          <p className="text-sm text-yellow-800 dark:text-yellow-300 mb-3">
            You have {sessionCount} other active session(s). If you don't recognize
            these devices, revoke them immediately to secure your account.
          </p>
          <button
            onClick={onRevokeAll}
            className="text-sm font-medium text-yellow-900 dark:text-yellow-200 hover:text-yellow-700 dark:hover:text-yellow-100 underline"
          >
            Revoke all other sessions
          </button>
        </div>
      </div>
    </div>
  );
}

export default SecurityWarning;
