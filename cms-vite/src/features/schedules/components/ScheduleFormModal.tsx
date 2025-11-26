/**
 * Schedule Form Modal Wrapper Component
 * Modal wrapper for create/edit schedule form
 *
 * ✅ REFACTORED: Now uses shared Modal component
 * - Fixed header (title)
 * - Fixed footer (action buttons)
 * - Scrollable content (form fields)
 * - Click outside to close
 */

import { useTranslation } from 'react-i18next';
import { Loader2 } from 'lucide-react';
import { Modal } from '@/shared/components';
import ScheduleForm from './ScheduleForm';
import type { Schedule, CreateScheduleRequest, UpdateScheduleRequest } from '../types/schedule.types';

interface ScheduleFormModalProps {
  mode: 'create' | 'edit';
  schedule?: Schedule;
  isLoading: boolean;
  onSubmit: (data: CreateScheduleRequest | UpdateScheduleRequest) => void;
  onCancel: () => void;
}

export function ScheduleFormModal({
  mode,
  schedule,
  isLoading,
  onSubmit,
  onCancel,
}: ScheduleFormModalProps) {
  const { t } = useTranslation();

  const handleClose = () => {
    if (!isLoading) {
      onCancel();
    }
  };

  // Footer with action buttons
  const footer = (
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={handleClose}
          disabled={isLoading}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
        >
          {t('common.cancel')}
        </button>
        <button
          type="submit"
          form="schedule-form"
          disabled={isLoading}
          className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
        >
          {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
          {t(mode === 'create' ? 'schedules.createSchedule' : 'schedules.updateSchedule')}
        </button>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={true}
      onClose={handleClose}
      title={t(mode === 'create' ? 'schedules.createSchedule' : 'schedules.editSchedule')}
      maxWidth="5xl"
      footer={footer}
      closeOnBackdropClick={!isLoading}
      className="h-[90vh]"
    >
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-6">
        <ScheduleForm
          schedule={schedule}
          onSubmit={onSubmit}
          onCancel={onCancel}
          isLoading={isLoading}
          showButtons={false}
        />
      </div>
    </Modal>
  );
}

export default ScheduleFormModal;
