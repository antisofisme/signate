/**
 * Templates Page
 *
 * LAYER 1: PRESENTATION
 * Main page for template management - orchestration only
 */

import { Plus, Eye } from 'lucide-react';
import TemplateList from '../components/TemplateList';
import TemplateForm from '../components/TemplateForm';
import TemplatePreview from '../components/TemplatePreview';
import { DeleteConfirmModal } from '@/shared/components';
import { useTemplateState } from '../hooks/useTemplateState';

export const TemplatesPage = () => {
  const {
    templates,
    isLoading,
    modalMode,
    selectedTemplate,
    showDeleteConfirm,
    setShowDeleteConfirm,
    setSelectedTemplate,
    handleCreate,
    handleEdit,
    handleDelete,
    handlePreview,
    handleSubmit,
    confirmDelete,
    closeModal,
    isSaving,
    isDeleting,
  } = useTemplateState();

  return (
    <>
      {/* Action Bar */}
      <div className="mb-6 flex justify-end">
        <button
          onClick={handleCreate}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Create Template
        </button>
      </div>

      {/* Template List */}
      <div className="space-y-6">
        <TemplateList
        templates={templates}
        isLoading={isLoading}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onPreview={handlePreview}
        />
      </div>

      {/* Form Modal */}
      {(modalMode === 'create' || modalMode === 'edit') && (
        <TemplateForm
          template={selectedTemplate || undefined}
          mode={modalMode}
          onSubmit={handleSubmit}
          onCancel={closeModal}
          isLoading={isSaving}
        />
      )}

      {/* Preview Modal */}
      {modalMode === 'preview' && selectedTemplate && (
        <TemplatePreview template={selectedTemplate} onClose={closeModal} />
      )}

      {/* Delete Confirmation */}
      {showDeleteConfirm && selectedTemplate && (
        <DeleteConfirmModal
          isOpen={showDeleteConfirm}
          title="Delete Template"
          message="Are you sure you want to delete this template?"
          itemName={selectedTemplate.name}
          onClose={() => {
            setShowDeleteConfirm(false);
            setSelectedTemplate(null);
          }}
          onConfirm={confirmDelete}
          isLoading={isDeleting}
        />
      )}
    </>
  );
};

export default TemplatesPage;
