/**
 * Menu Media Gallery Card Component
 * Single card for masonry grid with natural aspect ratio
 * Hover shows quick actions, click selects for sidebar detail
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Eye, Trash2, Copy, Check, Download } from 'lucide-react';
import { toast } from 'sonner';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { useDeleteMenuMedia } from '../hooks/useMenuMedia';
import { ConfirmDialog } from '@/shared/components';
import type { MenuMedia } from '../types/menu';
import { MenuMediaPreviewModal } from './MenuMediaPreviewModal';

// Format file size
const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

interface MenuMediaGalleryCardProps {
  media: MenuMedia;
  isSelected: boolean;
  onSelect: () => void;
}

export function MenuMediaGalleryCard({ media, isSelected, onSelect }: MenuMediaGalleryCardProps) {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canDelete } = useCanPerformAction('menus', 'delete');

  // State
  const [isHovered, setIsHovered] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Mutations
  const deleteMutation = useDeleteMenuMedia();

  // Handlers
  const handleCopyUrl = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(media.url || '');
      setCopied(true);
      toast.success(t('menus.media.messages.urlCopied', 'URL copied'));
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error(t('menus.media.messages.urlCopyFailed', 'Failed to copy URL'));
    }
  };

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!media.url) return;
    const link = document.createElement('a');
    link.href = media.url;
    link.download = media.original_filename;
    link.click();
    toast.success(t('menus.media.messages.downloadStarted', 'Download started'));
  };

  const handlePreview = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowPreview(true);
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowDeleteConfirm(true);
  };

  const handleDelete = async () => {
    await deleteMutation.mutateAsync(media.id);
    setShowDeleteConfirm(false);
  };

  return (
    <>
      <div
        className={`masonry-item relative group cursor-pointer rounded-lg overflow-hidden transition-all duration-200 ${
          isSelected
            ? 'ring-2 ring-blue-500 ring-offset-2 dark:ring-offset-gray-900'
            : 'hover:ring-2 hover:ring-gray-300 dark:hover:ring-gray-600'
        }`}
        onClick={onSelect}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Image */}
        <img
          src={media.url}
          alt={media.alt_text || media.original_filename}
          className="w-full h-auto object-cover"
          loading="lazy"
        />

        {/* Hover Overlay with Actions */}
        <div
          className={`absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent transition-opacity duration-200 ${
            isHovered || isSelected ? 'opacity-100' : 'opacity-0'
          }`}
        >
          {/* Quick Actions - Top Right */}
          <div className="absolute top-2 right-2 flex gap-1">
            <button
              onClick={handlePreview}
              className="p-1.5 bg-white/90 dark:bg-gray-800/90 rounded-md hover:bg-white dark:hover:bg-gray-700 transition-colors"
              title={t('menus.media.actions.preview', 'Preview')}
            >
              <Eye className="w-4 h-4 text-blue-600" />
            </button>
            <button
              onClick={handleCopyUrl}
              className="p-1.5 bg-white/90 dark:bg-gray-800/90 rounded-md hover:bg-white dark:hover:bg-gray-700 transition-colors"
              title={t('menus.media.actions.copyUrl', 'Copy URL')}
            >
              {copied ? (
                <Check className="w-4 h-4 text-green-500" />
              ) : (
                <Copy className="w-4 h-4 text-purple-600" />
              )}
            </button>
            <button
              onClick={handleDownload}
              className="p-1.5 bg-white/90 dark:bg-gray-800/90 rounded-md hover:bg-white dark:hover:bg-gray-700 transition-colors"
              title={t('menus.media.actions.download', 'Download')}
            >
              <Download className="w-4 h-4 text-gray-600" />
            </button>
            {canDelete && (
              <button
                onClick={handleDeleteClick}
                className="p-1.5 bg-white/90 dark:bg-gray-800/90 rounded-md hover:bg-red-50 dark:hover:bg-red-900/50 transition-colors"
                title={t('menus.media.actions.delete', 'Delete')}
              >
                <Trash2 className="w-4 h-4 text-red-600" />
              </button>
            )}
          </div>

          {/* File Info - Bottom */}
          <div className="absolute bottom-0 left-0 right-0 p-3">
            <p className="text-white text-sm font-medium truncate" title={media.title || media.original_filename}>
              {media.title || media.original_filename}
            </p>
            <div className="flex items-center gap-2 text-white/70 text-xs mt-1">
              {media.width && media.height && (
                <span>{media.width}x{media.height}</span>
              )}
              <span>{formatFileSize(media.file_size)}</span>
            </div>
          </div>
        </div>

        {/* Selected Indicator */}
        {isSelected && (
          <div className="absolute top-2 left-2">
            <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
              <Check className="w-4 h-4 text-white" />
            </div>
          </div>
        )}
      </div>

      {/* Preview Modal */}
      <MenuMediaPreviewModal
        isOpen={showPreview}
        media={media}
        onClose={() => setShowPreview(false)}
      />

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
    </>
  );
}
