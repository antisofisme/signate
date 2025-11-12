/**
 * Widgets Page
 *
 * LAYER 1: PRESENTATION
 * Main page for widget management - orchestration only
 */

import { Plus } from 'lucide-react';
import WidgetList from '../components/WidgetList';
import WidgetForm from '../components/WidgetForm';
import { DeleteConfirmModal } from '@/shared/components';
import { useWidgetState } from '../hooks/useWidgetState';

export const WidgetsPage = () => {
  const {
    widgets,
    isLoading,
    modalMode,
    selectedWidget,
    showDeleteConfirm,
    setShowDeleteConfirm,
    setSelectedWidget,
    handleCreate,
    handleEdit,
    handleDelete,
    handleAssign,
    handleSubmit,
    confirmDelete,
    closeModal,
    isSaving,
    isDeleting,
  } = useWidgetState();

  return (
    <>
      {/* Action Bar */}
      <div className="mb-6 flex justify-end">
        <button
          onClick={handleCreate}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Create Widget
        </button>
      </div>

      {/* Widget List */}
      <div className="space-y-6">
        <WidgetList
        widgets={widgets}
        isLoading={isLoading}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onAssign={handleAssign}
        />
      </div>

      {/* Form Modal */}
      {(modalMode === 'create' || modalMode === 'edit') && (
        <WidgetForm
          widget={selectedWidget || undefined}
          mode={modalMode}
          onSubmit={handleSubmit}
          onCancel={closeModal}
          isLoading={isSaving}
        />
      )}

      {/* Delete Confirmation */}
      {showDeleteConfirm && selectedWidget && (
        <DeleteConfirmModal
          isOpen={showDeleteConfirm}
          title="Delete Widget"
          message="Are you sure you want to delete this widget?"
          itemName={selectedWidget.name}
          onClose={() => {
            setShowDeleteConfirm(false);
            setSelectedWidget(null);
          }}
          onConfirm={confirmDelete}
          isLoading={isDeleting}
        />
      )}
    </>
  );
};

export default WidgetsPage;
