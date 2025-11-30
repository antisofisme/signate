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
import { Loader2 } from 'lucide-react';
import { Modal } from '@/shared/components';
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
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex justify-end gap-3">
        <button
          onClick={handleClose}
          disabled={isDeleting}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
        >
          {t('schedules.deleteModal.cancel')}
        </button>
        <button
          onClick={onConfirm}
          disabled={isDeleting}
          className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
        >
          {isDeleting && <Loader2 className="w-4 h-4 animate-spin" />}
          {t('schedules.deleteModal.deleteButton')}
        </button>
      </div>
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
