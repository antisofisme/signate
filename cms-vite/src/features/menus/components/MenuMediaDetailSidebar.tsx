/**
 * Menu Media Detail Sidebar Component
 * Right sidebar panel showing media details with inline editing
 * Shows empty state hint when no media is selected
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  X,
  Copy,
  Check,
  Download,
  Trash2,
  FileImage,
  Calendar,
  HardDrive,
  Maximize,
  User,
  Save,
  Pencil,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button, ConfirmDialog } from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { useUpdateMenuMedia, useDeleteMenuMedia } from '../hooks/useMenuMedia';
import type { MenuMedia } from '../types/menu';

// Format file size
const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// Format date
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('id-ID', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

interface MenuMediaDetailSidebarProps {
  media: MenuMedia | null;
  isOpen: boolean;
  onUpdate?: (media: MenuMedia) => void;
  onDelete?: () => void;
  onClose?: () => void;
}

export function MenuMediaDetailSidebar({ media, isOpen, onUpdate, onDelete, onClose }: MenuMediaDetailSidebarProps) {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canUpdate } = useCanPerformAction('menus', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('menus', 'delete');

  // State for inline editing
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [isEditingAlt, setIsEditingAlt] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editAlt, setEditAlt] = useState('');
  const [copied, setCopied] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Mutations
  const updateMutation = useUpdateMenuMedia();
  const deleteMutation = useDeleteMenuMedia();

  // Reset edit state when media changes
  useEffect(() => {
    if (media) {
      setEditTitle(media.title || '');
      setEditAlt(media.alt_text || '');
      setIsEditingTitle(false);
      setIsEditingAlt(false);
    }
  }, [media?.id]);

  // Handlers
  const handleCopyUrl = async () => {
    if (!media?.url) return;
    try {
      await navigator.clipboard.writeText(media.url);
      setCopied(true);
      toast.success(t('menus.media.messages.urlCopied', 'URL copied'));
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error(t('menus.media.messages.urlCopyFailed', 'Failed to copy URL'));
    }
  };

  const handleDownload = () => {
    if (!media?.url) return;
    const link = document.createElement('a');
    link.href = media.url;
    link.download = media.original_filename;
    link.click();
    toast.success(t('menus.media.messages.downloadStarted', 'Download started'));
  };

  const handleSaveTitle = async () => {
    if (!media) return;
    try {
      const result = await updateMutation.mutateAsync({
        id: media.id,
        data: { title: editTitle || undefined },
      });
      setIsEditingTitle(false);
      onUpdate?.({ ...media, title: editTitle || undefined });
    } catch {
      // Error handled by mutation
    }
  };

  const handleSaveAlt = async () => {
    if (!media) return;
    try {
      await updateMutation.mutateAsync({
        id: media.id,
        data: { alt_text: editAlt || undefined },
      });
      setIsEditingAlt(false);
      onUpdate?.({ ...media, alt_text: editAlt || undefined });
    } catch {
      // Error handled by mutation
    }
  };

  const handleDelete = async () => {
    if (!media) return;
    await deleteMutation.mutateAsync(media.id);
    setShowDeleteConfirm(false);
    onDelete?.();
  };

  // Don't render if not open
  if (!isOpen) {
    return null;
  }

  // Empty state (shouldn't happen since we only open when media is selected)
  if (!media) {
    return null;
  }

  return (
    <div className="w-[360px] flex-shrink-0 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden animate-slide-in-right">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <h3 className="font-medium text-gray-900 dark:text-white">
          {t('menus.media.sidebar.title', 'Detail Media')}
        </h3>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Content - Scrollable */}
      <div className="flex-1 overflow-y-auto">
        {/* Editable Fields */}
        <div className="p-4 space-y-4 border-b border-gray-200 dark:border-gray-700">
          {/* Title - Editable */}
          <div>
            <label className="flex items-center justify-between text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-1.5">
              <span>{t('menus.media.sidebar.title_field', 'Title')}</span>
              {canUpdate && !isEditingTitle && (
                <button
                  onClick={() => setIsEditingTitle(true)}
                  className="text-blue-500 hover:text-blue-600"
                >
                  <Pencil className="w-3.5 h-3.5" />
                </button>
              )}
            </label>
            {isEditingTitle ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  placeholder={t('menus.media.sidebar.titlePlaceholder', 'Enter title...')}
                  className="flex-1 px-3 py-1.5 text-sm bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  autoFocus
                />
                <button
                  onClick={handleSaveTitle}
                  disabled={updateMutation.isPending}
                  className="p-1.5 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded"
                >
                  <Save className="w-4 h-4" />
                </button>
                <button
                  onClick={() => {
                    setIsEditingTitle(false);
                    setEditTitle(media.title || '');
                  }}
                  className="p-1.5 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <p className="text-sm text-gray-900 dark:text-white">
                {media.title || (
                  <span className="text-gray-400 italic">
                    {t('menus.media.sidebar.noTitle', 'No title')}
                  </span>
                )}
              </p>
            )}
          </div>

          {/* Alt Text - Editable */}
          <div>
            <label className="flex items-center justify-between text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-1.5">
              <span>{t('menus.media.sidebar.alt_text', 'Alt Text')}</span>
              {canUpdate && !isEditingAlt && (
                <button
                  onClick={() => setIsEditingAlt(true)}
                  className="text-blue-500 hover:text-blue-600"
                >
                  <Pencil className="w-3.5 h-3.5" />
                </button>
              )}
            </label>
            {isEditingAlt ? (
              <div className="flex items-start gap-2">
                <textarea
                  value={editAlt}
                  onChange={(e) => setEditAlt(e.target.value)}
                  placeholder={t('menus.media.sidebar.altPlaceholder', 'Enter alt text...')}
                  rows={2}
                  className="flex-1 px-3 py-1.5 text-sm bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                  autoFocus
                />
                <div className="flex flex-col gap-1">
                  <button
                    onClick={handleSaveAlt}
                    disabled={updateMutation.isPending}
                    className="p-1.5 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded"
                  >
                    <Save className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {
                      setIsEditingAlt(false);
                      setEditAlt(media.alt_text || '');
                    }}
                    className="p-1.5 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-900 dark:text-white">
                {media.alt_text || (
                  <span className="text-gray-400 italic">
                    {t('menus.media.sidebar.noAltText', 'No alt text')}
                  </span>
                )}
              </p>
            )}
          </div>
        </div>

        {/* Metadata - Read Only */}
        <div className="p-4 space-y-3 border-b border-gray-200 dark:border-gray-700">
          <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
            {t('menus.media.sidebar.metadata', 'Metadata')}
          </h4>

          {/* Filename */}
          <div className="flex items-start gap-3">
            <FileImage className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <div className="min-w-0">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {t('menus.media.sidebar.filename', 'Filename')}
              </p>
              <p className="text-sm text-gray-900 dark:text-white truncate" title={media.original_filename}>
                {media.original_filename}
              </p>
            </div>
          </div>

          {/* Dimensions */}
          {media.width && media.height && (
            <div className="flex items-start gap-3">
              <Maximize className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {t('menus.media.sidebar.dimensions', 'Dimensions')}
                </p>
                <p className="text-sm text-gray-900 dark:text-white">
                  {media.width} x {media.height} px
                </p>
              </div>
            </div>
          )}

          {/* File Size */}
          <div className="flex items-start gap-3">
            <HardDrive className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {t('menus.media.sidebar.size', 'Size')}
              </p>
              <p className="text-sm text-gray-900 dark:text-white">
                {formatFileSize(media.file_size)} ({media.mime_type})
              </p>
            </div>
          </div>

          {/* Uploaded Date */}
          <div className="flex items-start gap-3">
            <Calendar className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {t('menus.media.sidebar.uploaded', 'Uploaded')}
              </p>
              <p className="text-sm text-gray-900 dark:text-white">
                {formatDate(media.created_at)}
              </p>
            </div>
          </div>

          {/* Uploaded By */}
          {media.uploaded_by_id && (
            <div className="flex items-start gap-3">
              <User className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {t('menus.media.sidebar.uploadedBy', 'Uploaded by')}
                </p>
                <p className="text-sm text-gray-900 dark:text-white">
                  User #{media.uploaded_by_id}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Usage Info - Placeholder for Phase 2 backend */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-3">
            {t('menus.media.sidebar.usedIn', 'Dipakai di')}
          </h4>
          <div className="text-sm text-gray-500 dark:text-gray-400 italic">
            {t('menus.media.sidebar.usageComingSoon', 'Info penggunaan akan ditampilkan di sini')}
          </div>
        </div>
      </div>

      {/* Actions - Fixed at bottom */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
        <div className="flex flex-wrap gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleCopyUrl}
            leftIcon={copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
            className="flex-1"
          >
            {copied ? t('common.copied', 'Copied') : t('menus.media.actions.copyUrl', 'Copy URL')}
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleDownload}
            leftIcon={<Download className="w-4 h-4" />}
            className="flex-1"
          >
            {t('menus.media.actions.download', 'Download')}
          </Button>
          {canDelete && (
            <Button
              variant="danger"
              size="sm"
              onClick={() => setShowDeleteConfirm(true)}
              leftIcon={<Trash2 className="w-4 h-4" />}
              className="w-full mt-2"
            >
              {t('menus.media.actions.delete', 'Delete')}
            </Button>
          )}
        </div>
      </div>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={showDeleteConfirm}
        onOpenChange={setShowDeleteConfirm}
        title={t('menus.media.dialogs.deleteTitle', 'Delete Image')}
        description={
          t('menus.media.dialogs.deleteMessage', { name: media.original_filename }) ||
          `Are you sure you want to delete "${media.original_filename}"?`
        }
        variant="danger"
        confirmLabel={t('menus.media.actions.delete', 'Delete')}
        onConfirm={handleDelete}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
