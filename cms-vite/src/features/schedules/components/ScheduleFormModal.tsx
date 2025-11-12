/**
 * Schedule Form Modal Wrapper Component
 * Modal wrapper for create/edit schedule form
 */

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
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-5xl w-full my-8">
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 rounded-t-lg">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {mode === 'create' ? 'Create Schedule' : 'Edit Schedule'}
          </h2>
        </div>
        <div className="p-6 max-h-[calc(100vh-200px)] overflow-y-auto">
          <ScheduleForm
            schedule={schedule}
            onSubmit={onSubmit}
            onCancel={onCancel}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
}

export default ScheduleFormModal;
