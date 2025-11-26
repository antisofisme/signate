/**
 * Delete Confirmation Modal Component
 *
 * LAYER 1: PRESENTATION
 * Reusable confirmation modal for delete operations
 *
 * ✅ REFACTORED: Now uses shared Modal component
 * - Fixed header (title)
 * - Fixed footer (buttons)
 * - Scrollable content (message + item name)
 * - Click outside to close
 */

import { Loader2 } from 'lucide-react';
import { Modal } from './Modal';

interface DeleteConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  itemName: string;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}

export function DeleteConfirmModal({
  isOpen,
  title,
  message,
  itemName,
  onClose,
  onConfirm,
  isLoading,
}: DeleteConfirmModalProps) {
  // Prevent closing during loading
  const handleClose = () => {
    if (!isLoading) {
      onClose();
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
          className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50 transition-colors"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={isLoading}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2 transition-colors"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Deleting...
            </>
          ) : (
            'Delete'
          )}
        </button>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={title}
      maxWidth="md"
      footer={footer}
      closeOnBackdropClick={!isLoading}
    >
      {/* Scrollable content */}
      <div className="p-6 space-y-3">
        <p className="text-gray-700 dark:text-gray-300">{message}</p>
        <p className="text-gray-900 dark:text-white font-semibold">
          {itemName}
        </p>
      </div>
    </Modal>
  );
}

export default DeleteConfirmModal;
