/**
 * Translations Page
 *
 * LAYER 1: PRESENTATION
 * Main page for translation management - orchestration only
 */

import { Plus, Upload, BarChart } from 'lucide-react';
import TranslationList from '../components/TranslationList';
import TranslationForm from '../components/TranslationForm';
import TranslationStats from '../components/TranslationStats';
import BulkImportModal from '../components/BulkImportModal';
import { DeleteConfirmModal } from '@/shared/components';
import { useTranslationState } from '../hooks/useTranslationState';

export const TranslationsPage = () => {
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
      {/* Action Bar */}
      <div className="mb-6 flex justify-between items-center">
        <div className="flex gap-3">
            <button
              onClick={() => setShowStats(!showStats)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2"
            >
              <BarChart className="w-4 h-4" />
              {showStats ? 'Hide' : 'Show'} Stats
            </button>
            <button
              onClick={() => setShowBulkImport(true)}
              className="px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              Bulk Import
            </button>
            <button
              onClick={handleCreate}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Create Translation
            </button>
        </div>
      </div>

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
