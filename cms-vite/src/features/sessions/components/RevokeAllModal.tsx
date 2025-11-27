/**
 * Revoke All Sessions Modal
 * Confirmation modal for revoking all other sessions
 * ✅ REFACTORED to use shared ConfirmDialog component
 */

import { useTranslation } from 'react-i18next';
import { ConfirmDialog } from '@/shared/components';

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

  return (
    <ConfirmDialog
      open={isOpen}
      onOpenChange={(open) => !open && onClose()}
      title={t('sessions.modal.title', 'Revoke All Sessions')}
      description={`${t('sessions.modal.description', 'This will log you out from all other devices. You will remain logged in on this device.')}

${t('sessions.modal.sessionsToRevoke', { count: otherSessionsCount })}`}
      variant="danger"
      confirmLabel={t('sessions.modal.confirmButton', 'Revoke All')}
      cancelLabel={t('sessions.modal.cancel', 'Cancel')}
      onConfirm={onConfirm}
      onCancel={onClose}
      isLoading={isRevoking}
    />
  );
}

export default RevokeAllModal;
