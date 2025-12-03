/**
 * Templates Page
 *
 * LAYER 1: PRESENTATION
 * Main page for template management - orchestration only
 */

import { Plus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import TemplateList from '../components/TemplateList';
import TemplateForm from '../components/TemplateForm';
import TemplatePreview from '../components/TemplatePreview';
import {
  DeleteConfirmModal,
  Button,
  Modal,
  PageHeader,
  PageStats,
  PageToolbar,
} from '@/shared/components';
import { useTemplateState } from '../hooks/useTemplateState';

export const TemplatesPage = () => {
  const { t } = useTranslation();
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
      {/* Page Header */}
      <PageHeader
        title={t('templates.title', 'Templates')}
        description={t('templates.subtitle', 'Manage display templates')}
      />

      {/* Toolbar: Buttons kanan */}
      <PageToolbar>
        <PageToolbar.Right>
          <Button
            variant="primary"
            onClick={handleCreate}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            {t('templates.create', 'Create Template')}
          </Button>
        </PageToolbar.Right>
      </PageToolbar>

      {/* Stats: langsung di atas list */}
      <PageStats
        total={templates.length}
        totalLabel="templates"
      />

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
          onSubmit={handleSubmit}
          onCancel={closeModal}
          isLoading={isSaving}
        />
      )}

      {/* Preview Modal */}
      {modalMode === 'preview' && selectedTemplate && (
        <Modal
          isOpen={true}
          onClose={closeModal}
          title={`Preview: ${selectedTemplate.name}`}
          maxWidth="4xl"
        >
          <div className="p-6">
            <TemplatePreview
              content={selectedTemplate.content}
              variables={selectedTemplate.variables || {}}
            />
          </div>
        </Modal>
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
