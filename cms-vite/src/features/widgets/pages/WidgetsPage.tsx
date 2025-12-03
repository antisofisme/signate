/**
 * Widgets Page
 *
 * LAYER 1: PRESENTATION
 * Main page for widget management - orchestration only
 */

import { Plus } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import WidgetList from '../components/WidgetList';
import WidgetForm from '../components/WidgetForm';
import {
  DeleteConfirmModal,
  Button,
  PageHeader,
  PageStats,
  PageToolbar,
} from '@/shared/components';
import { useWidgetState } from '../hooks/useWidgetState';

export const WidgetsPage = () => {
  const { t } = useTranslation();
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
      {/* Page Header */}
      <PageHeader
        title={t('widgets.title', 'Widgets')}
        description={t('widgets.subtitle', 'Manage display widgets')}
      />

      {/* Toolbar: Buttons kanan */}
      <PageToolbar>
        <PageToolbar.Right>
          <Button
            variant="primary"
            onClick={handleCreate}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            {t('widgets.create', 'Create Widget')}
          </Button>
        </PageToolbar.Right>
      </PageToolbar>

      {/* Stats: langsung di atas list */}
      <PageStats
        total={widgets.length}
        totalLabel="widgets"
      />

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
