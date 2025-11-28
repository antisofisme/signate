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

import { Modal } from './Modal';
import Button from './common/Button';

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
        <Button
          variant="ghost"
          onClick={handleClose}
          disabled={isLoading}
        >
          Cancel
        </Button>
        <Button
          variant="danger"
          onClick={onConfirm}
          disabled={isLoading}
          loading={isLoading}
        >
          {isLoading ? 'Deleting...' : 'Delete'}
        </Button>
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
