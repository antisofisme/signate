/**
 * Translations Page
 *
 * LAYER 1: PRESENTATION
 * Main page for translation management - orchestration only
 */

import { Plus, Upload, BarChart } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import TranslationList from '../components/TranslationList';
import TranslationForm from '../components/TranslationForm';
import TranslationStats from '../components/TranslationStats';
import BulkImportModal from '../components/BulkImportModal';
import {
  DeleteConfirmModal,
  Button,
  PageHeader,
  PageStats,
  PageToolbar,
  AccessDenied,
  PageSkeleton,
} from '@/shared/components';
import { useTranslationState } from '../hooks/useTranslationState';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';

export const TranslationsPage = () => {
  const { t } = useTranslation();

  // Permission checks - using 'settings' resource for translations
  const { hasPermission: canRead, isLoading: loadingReadPerm } = useCanPerformAction('settings', 'read');
  const { hasPermission: canCreate } = useCanPerformAction('settings', 'create');
  const { hasPermission: canUpdate } = useCanPerformAction('settings', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('settings', 'delete');

  // Show loading state while checking permissions
  if (loadingReadPerm) {
    return <PageSkeleton />;
  }

  // Show access denied if no read permission
  if (!canRead) {
    return <AccessDenied />;
  }

  const {
    translations,
    isLoading,
    modalMode,
    selectedTranslation,
    showDeleteConfirm,
    showBulkImport,
    showStats,
    setShowBulkImport,
    setShowStats,
    setShowDeleteConfirm,
    setSelectedTranslation,
    handleCreate,
    handleEdit,
    handleDelete,
    handleApprove,
    handleReject,
    handleSubmit,
    confirmDelete,
    closeModal,
    isSaving,
    isDeleting,
    isApproving,
    isRejecting,
  } = useTranslationState();

  return (
    <>
      {/* Page Header */}
      <PageHeader
        title={t('translationsPage.title', 'Translations')}
        description={t('translationsPage.subtitle', 'Manage multi-language translations')}
      />

      {/* Toolbar: Buttons kanan */}
      <PageToolbar>
        <PageToolbar.Left>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowStats(!showStats)}
            leftIcon={<BarChart className="w-4 h-4" />}
          >
            {showStats ? t('translationsPage.hideStats', 'Hide Stats') : t('translationsPage.showStats', 'Show Stats')}
          </Button>
        </PageToolbar.Left>
        <PageToolbar.Right>
          {canCreate && (
            <Button
              variant="secondary"
              onClick={() => setShowBulkImport(true)}
              leftIcon={<Upload className="w-4 h-4" />}
            >
              {t('translationsPage.bulkImport', 'Bulk Import')}
            </Button>
          )}
          {canCreate && (
            <Button
              variant="primary"
              onClick={handleCreate}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              {t('translationsPage.create', 'Create Translation')}
            </Button>
          )}
        </PageToolbar.Right>
      </PageToolbar>

      {/* Stats: langsung di atas list */}
      <PageStats
        total={translations.length}
        totalLabel="translations"
      />

      {/* Content */}
      <div className="space-y-6">
        {/* Stats */}
        {showStats && <TranslationStats />}

        {/* Translation List */}
        <TranslationList
          translations={translations}
          isLoading={isLoading}
          onEdit={canUpdate ? handleEdit : undefined}
          onDelete={canDelete ? handleDelete : undefined}
          onApprove={canUpdate ? handleApprove : undefined}
          onReject={canUpdate ? handleReject : undefined}
          isApproving={isApproving}
          isRejecting={isRejecting}
        />
      </div>

      {/* Form Modal */}
      {modalMode && (
        <TranslationForm
          translation={selectedTranslation || undefined}
          onSubmit={handleSubmit}
          onCancel={closeModal}
          isLoading={isSaving}
        />
      )}

      {/* Delete Confirmation */}
      {showDeleteConfirm && selectedTranslation && (
        <DeleteConfirmModal
          isOpen={showDeleteConfirm}
          title={t('translationsPage.delete.title', 'Delete Translation')}
          message={t('translationsPage.delete.message', 'Are you sure you want to delete this translation?')}
          itemName={selectedTranslation.field_name}
          onClose={() => {
            setShowDeleteConfirm(false);
            setSelectedTranslation(null);
          }}
          onConfirm={confirmDelete}
          isLoading={isDeleting}
        />
      )}

      {/* Bulk Import Modal */}
      {showBulkImport && <BulkImportModal isOpen={showBulkImport} onClose={() => setShowBulkImport(false)} />}
    </>
  );
};

export default TranslationsPage;
