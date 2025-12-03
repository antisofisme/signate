/**
 * Schedule Delete Modal Component
 * Confirmation modal for schedule deletion
 *
 * ✅ REFACTORED: Now uses shared Modal component
 * - Fixed header (title)
 * - Fixed footer (action buttons)
 * - Scrollable content (message + schedule details)
 * - Click outside to close (disabled during deletion)
 */

import { useTranslation } from 'react-i18next';
import { Modal, Button } from '@/shared/components';
import type { Schedule } from '../types/schedule.types';

interface ScheduleDeleteModalProps {
  isOpen: boolean;
  schedule: Schedule;
  isDeleting: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export function ScheduleDeleteModal({
  isOpen,
  schedule,
  isDeleting,
  onClose,
  onConfirm,
}: ScheduleDeleteModalProps) {
  const { t } = useTranslation();

  const handleClose = () => {
    if (!isDeleting) {
      onClose();
    }
  };

  const footer = (
    <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
      <Button
        variant="secondary"
        onClick={handleClose}
        disabled={isDeleting}
      >
        {t('schedules.deleteModal.cancel')}
      </Button>
      <Button
        variant="danger"
        onClick={onConfirm}
        disabled={isDeleting}
        loading={isDeleting}
      >
        {t('schedules.deleteModal.deleteButton')}
      </Button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={t('schedules.deleteModal.title')}
      maxWidth="md"
      footer={footer}
      closeOnBackdropClick={!isDeleting}
    >
      <div className="p-6 space-y-6">
        <p className="text-gray-600 dark:text-gray-400">
          {t('schedules.deleteModal.confirmMessage')}
        </p>
        <div className="bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded p-3">
          <p className="text-sm font-medium text-gray-900 dark:text-white">{schedule.name}</p>
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
            {schedule.recurrence_type} • {schedule.playlist_name}
          </p>
        </div>
      </div>
    </Modal>
  );
}

export default ScheduleDeleteModal;
