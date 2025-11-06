/**
 * Bulk Tag Modal Component
 * Assign/unassign tags to multiple content items
 *
 * TODO: Requires backend endpoint for content-tag assignments
 */

import { X } from 'lucide-react';
import type { Content } from '../types/content';

interface BulkTagModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedContent: Content[];
}

export function BulkTagModal({ isOpen, onClose, selectedContent }: BulkTagModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Bulk Tag Assignment
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Assigning tags to {selectedContent.length} content items
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Coming Soon Message */}
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6 text-center">
          <p className="text-yellow-900 dark:text-yellow-300 font-medium mb-2">
            🚧 Coming Soon
          </p>
          <p className="text-sm text-yellow-700 dark:text-yellow-400">
            Bulk tag assignment feature is currently under development.
            <br />
            Backend endpoint for content-tag assignments is required.
          </p>
        </div>

        {/* Close Button */}
        <div className="flex justify-end mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
