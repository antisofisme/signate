/**
 * Schedule Delete Modal Component
 * Confirmation modal for schedule deletion
 */

import { Loader2 } from 'lucide-react';
import type { Schedule } from '../types/schedule.types';

interface ScheduleDeleteModalProps {
  schedule: Schedule;
  isDeleting: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export function ScheduleDeleteModal({
  schedule,
  isDeleting,
  onClose,
  onConfirm,
}: ScheduleDeleteModalProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full p-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Delete Schedule</h2>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Are you sure you want to delete this schedule? This action cannot be undone.
        </p>
        <div className="bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded p-3 mb-6">
          <p className="text-sm font-medium text-gray-900 dark:text-white">{schedule.name}</p>
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
            {schedule.recurrence_type} • {schedule.device_ids.length} device(s)
          </p>
        </div>
        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={isDeleting}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isDeleting}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
          >
            {isDeleting && <Loader2 className="w-4 h-4 animate-spin" />}
            Delete Schedule
          </button>
        </div>
      </div>
    </div>
  );
}

export default ScheduleDeleteModal;
