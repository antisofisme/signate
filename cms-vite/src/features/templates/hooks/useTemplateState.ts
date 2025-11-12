/**
 * Template State Management Hook
 * Manages state and handlers for templates page
 */

import { useState } from 'react';
import { useTemplates, useCreateTemplate, useUpdateTemplate, useDeleteTemplate } from './useTemplates';
import type { Template, CreateTemplateRequest, UpdateTemplateRequest } from '../types/template.types';

type ModalMode = 'create' | 'edit' | 'preview' | null;

export function useTemplateState() {
  const [modalMode, setModalMode] = useState<ModalMode>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Queries
  const { data, isLoading } = useTemplates();

  // Mutations
  const createMutation = useCreateTemplate();
  const updateMutation = useUpdateTemplate();
  const deleteMutation = useDeleteTemplate();

  // Handlers
  const handleCreate = () => {
    setModalMode('create');
    setSelectedTemplate(null);
  };

  const handleEdit = (template: Template) => {
    setModalMode('edit');
    setSelectedTemplate(template);
  };

  const handleDelete = (template: Template) => {
    setSelectedTemplate(template);
    setShowDeleteConfirm(true);
  };

  const handlePreview = (template: Template) => {
    setModalMode('preview');
    setSelectedTemplate(template);
  };

  const handleSubmit = async (formData: CreateTemplateRequest | UpdateTemplateRequest) => {
    if (modalMode === 'create') {
      await createMutation.mutateAsync(formData as CreateTemplateRequest);
    } else if (modalMode === 'edit' && selectedTemplate) {
      await updateMutation.mutateAsync({
        id: selectedTemplate.id,
        data: formData as UpdateTemplateRequest,
      });
    }
    setModalMode(null);
    setSelectedTemplate(null);
  };

  const confirmDelete = async () => {
    if (!selectedTemplate) return;
    await deleteMutation.mutateAsync(selectedTemplate.id);
    setShowDeleteConfirm(false);
    setSelectedTemplate(null);
  };

  const closeModal = () => {
    setModalMode(null);
    setSelectedTemplate(null);
  };

  return {
    // Data
    templates: data?.templates || [],
    isLoading,

    // State
    modalMode,
    selectedTemplate,
    showDeleteConfirm,

    // Setters
    setShowDeleteConfirm,
    setSelectedTemplate,

    // Handlers
    handleCreate,
    handleEdit,
    handleDelete,
    handlePreview,
    handleSubmit,
    confirmDelete,
    closeModal,

    // Mutation states
    isSaving: createMutation.isPending || updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
