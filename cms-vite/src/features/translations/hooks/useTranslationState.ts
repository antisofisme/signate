/**
 * Translation State Management Hook
 * Manages state and handlers for translations page
 */

import { useState } from 'react';
import {
  useTranslations,
  useCreateTranslation,
  useUpdateTranslation,
  useDeleteTranslation,
  useApproveTranslation,
  useRejectTranslation,
} from './useTranslations';
import type {
  Translation,
  CreateTranslationRequest,
  UpdateTranslationRequest,
} from '../types/translation.types';

type ModalMode = 'create' | 'edit' | null;

export function useTranslationState() {
  const [modalMode, setModalMode] = useState<ModalMode>(null);
  const [selectedTranslation, setSelectedTranslation] = useState<Translation | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showBulkImport, setShowBulkImport] = useState(false);
  const [showStats, setShowStats] = useState(false);

  // Queries
  const { data, isLoading } = useTranslations();

  // Mutations
  const createMutation = useCreateTranslation();
  const updateMutation = useUpdateTranslation();
  const deleteMutation = useDeleteTranslation();
  const approveMutation = useApproveTranslation();
  const rejectMutation = useRejectTranslation();

  // Handlers
  const handleCreate = () => {
    setModalMode('create');
    setSelectedTranslation(null);
  };

  const handleEdit = (translation: Translation) => {
    setModalMode('edit');
    setSelectedTranslation(translation);
  };

  const handleDelete = (translation: Translation) => {
    setSelectedTranslation(translation);
    setShowDeleteConfirm(true);
  };

  const handleApprove = async (translation: Translation) => {
    await approveMutation.mutateAsync(translation.id);
  };

  const handleReject = async (translation: Translation) => {
    await rejectMutation.mutateAsync(translation.id);
  };

  const handleSubmit = async (formData: CreateTranslationRequest | UpdateTranslationRequest) => {
    if (modalMode === 'create') {
      await createMutation.mutateAsync(formData as CreateTranslationRequest);
    } else if (modalMode === 'edit' && selectedTranslation) {
      await updateMutation.mutateAsync({
        id: selectedTranslation.id,
        data: formData as UpdateTranslationRequest,
      });
    }
    setModalMode(null);
    setSelectedTranslation(null);
  };

  const confirmDelete = async () => {
    if (!selectedTranslation) return;
    await deleteMutation.mutateAsync(selectedTranslation.id);
    setShowDeleteConfirm(false);
    setSelectedTranslation(null);
  };

  const closeModal = () => {
    setModalMode(null);
    setSelectedTranslation(null);
  };

  return {
    // Data
    translations: data?.translations || [],
    isLoading,

    // State
    modalMode,
    selectedTranslation,
    showDeleteConfirm,
    showBulkImport,
    showStats,

    // Setters
    setShowBulkImport,
    setShowStats,
    setShowDeleteConfirm,
    setSelectedTranslation,

    // Handlers
    handleCreate,
    handleEdit,
    handleDelete,
    handleApprove,
    handleReject,
    handleSubmit,
    confirmDelete,
    closeModal,

    // Mutation states
    isSaving: createMutation.isPending || updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isApproving: approveMutation.isPending,
    isRejecting: rejectMutation.isPending,
  };
}
