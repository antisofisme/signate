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
import { Modal, Button } from '@/shared/components';
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
    <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
      <Button
        type="button"
        variant="secondary"
        onClick={handleClose}
        disabled={isLoading}
      >
        {t('common.cancel')}
      </Button>
      <Button
        type="submit"
        form="schedule-form"
        disabled={isLoading}
        loading={isLoading}
        className="bg-purple-600 hover:bg-purple-700"
      >
        {t(mode === 'create' ? 'schedules.createSchedule' : 'schedules.updateSchedule')}
      </Button>
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
