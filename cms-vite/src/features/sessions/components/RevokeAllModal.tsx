// ✅ REFACTORED to use shared Modal component
/**
 * Revoke All Sessions Modal
 * Confirmation modal for revoking all other sessions
 */

import { useTranslation } from 'react-i18next';
import { AlertTriangle } from 'lucide-react';
import { Modal } from '@/shared/components';

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
  const { t } = useTranslation();

  // Custom header with alert icon
  const customHeader = (
    <div className="flex items-center gap-3 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
        <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
      </div>
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
        {t('sessions.modal.title')}
      </h2>
    </div>
  );

  // Footer with action buttons
  const footer = (
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex items-center gap-3">
        <button
          onClick={onClose}
          disabled={isRevoking}
          className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
        >
          {t('sessions.modal.cancel')}
        </button>
        <button
          onClick={onConfirm}
          disabled={isRevoking}
          className="flex-1 px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isRevoking ? t('sessions.modal.revoking') : t('sessions.modal.confirmButton')}
        </button>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      customHeader={customHeader}
      footer={footer}
      maxWidth="md"
      closeOnBackdropClick={!isRevoking}
      showCloseButton={false}
    >
      <div className="p-6">
        <p className="text-gray-600 dark:text-gray-400">
          {t('sessions.modal.description')}
          <br />
          <br />
          <strong>{t('sessions.modal.sessionsToRevoke', { count: otherSessionsCount })}</strong>
        </p>
      </div>
    </Modal>
  );
}

export default RevokeAllModal;
