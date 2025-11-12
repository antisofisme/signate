/**
 * Widget State Management Hook
 * Manages state and handlers for widgets page
 */

import { useState } from 'react';
import { useWidgets, useCreateWidget, useUpdateWidget, useDeleteWidget } from './useWidgets';
import type { Widget, CreateWidgetRequest, UpdateWidgetRequest } from '../types/widget.types';

type ModalMode = 'create' | 'edit' | 'assign' | null;

export function useWidgetState() {
  const [modalMode, setModalMode] = useState<ModalMode>(null);
  const [selectedWidget, setSelectedWidget] = useState<Widget | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Queries
  const { data, isLoading } = useWidgets();

  // Mutations
  const createMutation = useCreateWidget();
  const updateMutation = useUpdateWidget();
  const deleteMutation = useDeleteWidget();

  // Handlers
  const handleCreate = () => {
    setModalMode('create');
    setSelectedWidget(null);
  };

  const handleEdit = (widget: Widget) => {
    setModalMode('edit');
    setSelectedWidget(widget);
  };

  const handleDelete = (widget: Widget) => {
    setSelectedWidget(widget);
    setShowDeleteConfirm(true);
  };

  const handleAssign = (widget: Widget) => {
    setModalMode('assign');
    setSelectedWidget(widget);
  };

  const handleSubmit = async (formData: CreateWidgetRequest | UpdateWidgetRequest) => {
    if (modalMode === 'create') {
      await createMutation.mutateAsync(formData as CreateWidgetRequest);
    } else if (modalMode === 'edit' && selectedWidget) {
      await updateMutation.mutateAsync({
        id: selectedWidget.id,
        data: formData as UpdateWidgetRequest,
      });
    }
    setModalMode(null);
    setSelectedWidget(null);
  };

  const confirmDelete = async () => {
    if (!selectedWidget) return;
    await deleteMutation.mutateAsync(selectedWidget.id);
    setShowDeleteConfirm(false);
    setSelectedWidget(null);
  };

  const closeModal = () => {
    setModalMode(null);
    setSelectedWidget(null);
  };

  return {
    // Data
    widgets: data?.widgets || [],
    isLoading,

    // State
    modalMode,
    selectedWidget,
    showDeleteConfirm,

    // Setters
    setShowDeleteConfirm,
    setSelectedWidget,

    // Handlers
    handleCreate,
    handleEdit,
    handleDelete,
    handleAssign,
    handleSubmit,
    confirmDelete,
    closeModal,

    // Mutation states
    isSaving: createMutation.isPending || updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
