/**
 * Revoke All Sessions Modal
 * Confirmation modal for revoking all other sessions
 */

import { AlertTriangle } from 'lucide-react';

interface RevokeAllModalProps {
  isOpen: boolean;
  otherSessionsCount: number;
  isRevoking: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export function RevokeAllModal({
  isOpen,
  otherSessionsCount,
  isRevoking,
  onClose,
  onConfirm,
}: RevokeAllModalProps) {
  if (!isOpen) return null;

  return (
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
            onClick={onClose}
            disabled={isRevoking}
            className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isRevoking}
            className="flex-1 px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRevoking ? 'Revoking...' : 'Logout All'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default RevokeAllModal;
