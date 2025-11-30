/**
 * Menu Media Tab Component
 * Upload and manage images specifically for menu items
 */

import { useState, useRef, ChangeEvent } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Upload,
  Trash2,
  Loader2,
  Image as ImageIcon,
  Copy,
  Check,
  Search,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/shared/components';
import { ConfirmDialog } from '@/shared/components/feedback/ConfirmDialog';
import { useMenuMedia, useUploadMenuMedia, useDeleteMenuMedia } from '../hooks/useMenuMedia';
import type { MenuMedia } from '../types/menu';

export const MenuMediaTab = () => {
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<MenuMedia | null>(null);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Queries and mutations
  const { data, isLoading, error } = useMenuMedia();
  const uploadMutation = useUploadMenuMedia();
  const deleteMutation = useDeleteMenuMedia();

  // File upload handler
  const handleFileUpload = async (files: FileList | null) => {
    if (!files) return;

    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    const maxSize = 10 * 1024 * 1024; // 10MB

    for (const file of Array.from(files)) {
      if (!allowedTypes.includes(file.type)) {
        toast.error(t('menus.media.invalidType', 'Invalid file type. Only JPG, PNG, GIF, WebP allowed.'));
        continue;
      }
      if (file.size > maxSize) {
        toast.error(t('menus.media.fileTooLarge', 'File is too large. Maximum size is 10MB.'));
        continue;
      }
      try {
        await uploadMutation.mutateAsync(file);
      } catch {
        // Error handled in hook
      }
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    handleFileUpload(e.target.files);
    // Reset input so same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileUpload(e.dataTransfer.files);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  // Copy URL to clipboard
  const handleCopyUrl = async (media: MenuMedia) => {
    try {
      await navigator.clipboard.writeText(media.url || '');
      setCopiedId(media.id);
      toast.success(t('menus.media.urlCopied', 'URL copied to clipboard'));
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      toast.error(t('menus.media.copyFailed', 'Failed to copy URL'));
    }
  };

  // Delete handler
  const handleDelete = async () => {
    if (!deleteTarget) return;
    await deleteMutation.mutateAsync(deleteTarget.id);
    setDeleteTarget(null);
  };

  // Filter media by search
  const filteredMedia = data?.items.filter((media) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      media.original_filename.toLowerCase().includes(query) ||
      media.title?.toLowerCase().includes(query)
    );
  });

  // Format file size
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <div
        onClick={() => fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragging
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/gif,image/webp"
          multiple
          onChange={handleInputChange}
          className="hidden"
        />
        <div className="flex flex-col items-center">
          {uploadMutation.isPending ? (
            <>
              <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
              <p className="text-gray-600 dark:text-gray-400">
                {t('menus.media.uploading', 'Uploading...')}
              </p>
            </>
          ) : (
            <>
              <Upload className="w-12 h-12 text-gray-400 dark:text-gray-500 mb-4" />
              <p className="text-gray-600 dark:text-gray-400 mb-2">
                {isDragging
                  ? t('menus.media.dropHere', 'Drop images here...')
                  : t('menus.media.dragDrop', 'Drag & drop images here, or click to select')}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500">
                {t('menus.media.allowedTypes', 'JPG, PNG, GIF, WebP - Max 10MB')}
              </p>
            </>
          )}
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          placeholder={t('menus.media.searchPlaceholder', 'Search images...')}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Media Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : error ? (
        <div className="text-center py-12 text-red-500">
          {t('menus.media.loadError', 'Failed to load images')}
        </div>
      ) : filteredMedia && filteredMedia.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {filteredMedia.map((media) => (
            <div
              key={media.id}
              className="group relative bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 overflow-hidden"
            >
              {/* Image */}
              <div className="aspect-square bg-gray-100 dark:bg-gray-900">
                <img
                  src={media.url}
                  alt={media.alt_text || media.original_filename}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              </div>

              {/* Overlay actions */}
              <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-opacity flex items-center justify-center opacity-0 group-hover:opacity-100">
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleCopyUrl(media)}
                    className="p-2 bg-white rounded-full text-gray-700 hover:bg-gray-100 transition-colors"
                    title={t('menus.media.copyUrl', 'Copy URL')}
                  >
                    {copiedId === media.id ? (
                      <Check className="w-4 h-4 text-green-500" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </button>
                  <button
                    onClick={() => setDeleteTarget(media)}
                    className="p-2 bg-white rounded-full text-red-600 hover:bg-red-50 transition-colors"
                    title={t('menus.media.delete', 'Delete')}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* File info */}
              <div className="p-2">
                <p className="text-xs text-gray-600 dark:text-gray-400 truncate" title={media.original_filename}>
                  {media.original_filename}
                </p>
                <p className="text-xs text-gray-400 dark:text-gray-500">
                  {media.width}x{media.height} - {formatFileSize(media.file_size)}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <ImageIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">
            {searchQuery
              ? t('menus.media.noSearchResults', 'No images found matching your search')
              : t('menus.media.noImages', 'No images uploaded yet')}
          </p>
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
            {t('menus.media.uploadHint', 'Upload images to use them in your menu items')}
          </p>
        </div>
      )}

      {/* Total count */}
      {data && data.total > 0 && (
        <div className="text-sm text-gray-500 dark:text-gray-400 text-center">
          {t('menus.media.totalCount', '{{count}} images total', { count: data.total })}
        </div>
      )}

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        onConfirm={handleDelete}
        title={t('menus.media.deleteTitle', 'Delete Image')}
        description={t('menus.media.deleteMessage', 'Are you sure you want to delete this image? Menu items using this image will no longer display it.')}
        confirmLabel={t('common.delete', 'Delete')}
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
};
