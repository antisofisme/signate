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
} from '@/shared/components';
import { useTranslationState } from '../hooks/useTranslationState';

export const TranslationsPage = () => {
  const { t } = useTranslation();
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
        title={t('translations.title', 'Translations')}
        description={t('translations.subtitle', 'Manage multi-language translations')}
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
            {showStats ? t('translations.hideStats', 'Hide Stats') : t('translations.showStats', 'Show Stats')}
          </Button>
        </PageToolbar.Left>
        <PageToolbar.Right>
          <Button
            variant="secondary"
            onClick={() => setShowBulkImport(true)}
            leftIcon={<Upload className="w-4 h-4" />}
          >
            {t('translations.bulkImport', 'Bulk Import')}
          </Button>
          <Button
            variant="primary"
            onClick={handleCreate}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            {t('translations.create', 'Create Translation')}
          </Button>
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
        onEdit={handleEdit}
        onDelete={handleDelete}
        onApprove={handleApprove}
        onReject={handleReject}
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
          title="Delete Translation"
          message="Are you sure you want to delete this translation?"
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
