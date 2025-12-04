/**
 * Content Gallery Card Component
 * Card for masonry grid with content type support (image, video, audio)
 * Supports checkbox selection, transcoding status, and hover actions
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Eye,
  Trash2,
  Download,
  Play,
  Tag,
  ListMusic,
  FileImage,
  FileVideo,
  FileAudio,
  Clock,
  Loader2,
  AlertCircle,
  Check,
} from 'lucide-react';
import { toast } from '@/shared/utils/toast';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { useDeleteContent } from '../hooks/useContent';
import { ConfirmDialog } from '@/shared/components';
import { formatFileSize, downloadContent } from '../api/contentApi';
import type { Content, ContentType, TranscodingStatus } from '../types/content';
import { ContentPreviewModal } from './ContentPreviewModal';

// Get content type icon
function getContentTypeIcon(type: ContentType, className = 'w-4 h-4') {
  switch (type) {
    case 'image':
      return <FileImage className={className} />;
    case 'video':
      return <FileVideo className={className} />;
    case 'audio':
      return <FileAudio className={className} />;
  }
}

// Get transcoding status badge
function getTranscodingBadge(status: TranscodingStatus, progress: number, t: (key: string) => string) {
  switch (status) {
    case 'pending':
      return (
        <div className="flex items-center gap-1 px-2 py-0.5 bg-gray-500/80 text-white text-xs rounded">
          <Clock className="w-3 h-3" />
          <span>{t('contents.transcoding.pending')}</span>
        </div>
      );
    case 'processing':
      return (
        <div className="flex items-center gap-1 px-2 py-0.5 bg-blue-500/80 text-white text-xs rounded">
          <Loader2 className="w-3 h-3 animate-spin" />
          <span>{progress}%</span>
        </div>
      );
    case 'failed':
      return (
        <div className="flex items-center gap-1 px-2 py-0.5 bg-red-500/80 text-white text-xs rounded">
          <AlertCircle className="w-3 h-3" />
          <span>{t('contents.transcoding.failed')}</span>
        </div>
      );
    case 'completed':
    default:
      return null;
  }
}

// Format duration as mm:ss
function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

interface ContentGalleryCardProps {
  content: Content;
  isSelected: boolean;
  showCheckbox: boolean; // Force show checkbox (selection mode active)
  onSelect: () => void; // Click card -> open sidebar
  onCheckboxChange: (checked: boolean) => void;
  onTagAssign?: (content: Content) => void; // Optional: assign tag
  onPlaylistAssign?: (content: Content) => void; // Optional: assign to playlist
}

export function ContentGalleryCard({
  content,
  isSelected,
  showCheckbox,
  onSelect,
  onCheckboxChange,
  onTagAssign,
  onPlaylistAssign,
}: ContentGalleryCardProps) {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canEdit } = useCanPerformAction('contents', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('contents', 'delete');

  // State
  const [isHovered, setIsHovered] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Mutations
  const deleteMutation = useDeleteContent();

  // Handlers
  const handleDownload = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await downloadContent(content.id, content.original_filename);
      toast.success(t('contents.messages.downloadStarted'));
    } catch {
      toast.error(t('contents.messages.downloadFailed'));
    }
  };

  const handlePreview = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowPreview(true);
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowDeleteConfirm(true);
  };

  const handleTagAssign = (e: React.MouseEvent) => {
    e.stopPropagation();
    onTagAssign?.(content);
  };

  const handlePlaylistAssign = (e: React.MouseEvent) => {
    e.stopPropagation();
    onPlaylistAssign?.(content);
  };

  const handleDelete = async () => {
    await deleteMutation.mutateAsync(content.id);
    setShowDeleteConfirm(false);
  };

  const handleCheckboxClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onCheckboxChange(e.target.checked);
  };

  // Determine if has thumbnail or needs fallback
  const hasThumbnail = content.thumbnail_url || content.content_type === 'image';
  const thumbnailUrl = content.thumbnail_url || (content.content_type === 'image' ? content.file_url : null);

  // Get gradient for non-image content without thumbnail
  const getGradientClass = () => {
    switch (content.content_type) {
      case 'video':
        return 'bg-gradient-to-br from-slate-700 to-slate-900';
      case 'audio':
        return 'bg-gradient-to-br from-purple-600 to-purple-900';
      default:
        return 'bg-gradient-to-br from-gray-600 to-gray-800';
    }
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
        {/* Content Display */}
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt={content.title || content.original_filename}
            className="w-full h-auto object-cover"
            loading="lazy"
          />
        ) : (
          <div className={`w-full aspect-video flex items-center justify-center ${getGradientClass()}`}>
            {getContentTypeIcon(content.content_type, 'w-12 h-12 text-white/50')}
          </div>
        )}

        {/* Content Type Badge - Top Left */}
        <div className="absolute top-2 left-2 flex flex-col gap-1">
          <div className="p-1.5 bg-black/50 rounded-md">
            {getContentTypeIcon(content.content_type, 'w-4 h-4 text-white')}
          </div>
        </div>

        {/* Checkbox - Top Left, below type badge */}
        {(showCheckbox || isHovered || isSelected) && (
          <div className="absolute top-12 left-2" onClick={handleCheckboxClick}>
            <input
              type="checkbox"
              checked={isSelected}
              onChange={handleCheckboxChange}
              className="w-5 h-5 text-blue-600 bg-white/90 border-2 border-white rounded focus:ring-blue-500 cursor-pointer"
            />
          </div>
        )}

        {/* Transcoding Status Badge - Top Right */}
        {content.content_type === 'video' && content.transcoding_status !== 'completed' && (
          <div className="absolute top-2 right-2">
            {getTranscodingBadge(content.transcoding_status, content.transcoding_progress, t)}
          </div>
        )}

        {/* Play Icon Overlay - Center for video/audio */}
        {(content.content_type === 'video' || content.content_type === 'audio') && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-12 h-12 bg-black/50 rounded-full flex items-center justify-center">
              <Play className="w-6 h-6 text-white ml-1" fill="white" />
            </div>
          </div>
        )}

        {/* Duration Badge - Bottom Right for video/audio */}
        {(content.content_type === 'video' || content.content_type === 'audio') && content.duration > 0 && (
          <div className="absolute bottom-2 right-2 px-2 py-0.5 bg-black/70 text-white text-xs rounded">
            {formatDuration(content.duration)}
          </div>
        )}

        {/* Hover Overlay with Actions */}
        <div
          className={`absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent transition-opacity duration-200 ${
            isHovered || isSelected ? 'opacity-100' : 'opacity-0'
          }`}
        >
          {/* Quick Actions - Top Right (below transcoding badge if present) */}
          <div className={`absolute ${content.transcoding_status !== 'completed' ? 'top-10' : 'top-2'} right-2 flex gap-1`}>
            <button
              onClick={handlePreview}
              className="p-1.5 bg-white/90 dark:bg-gray-800/90 rounded-md hover:bg-white dark:hover:bg-gray-700 transition-colors"
              title={t('contents.actions.preview')}
            >
              <Eye className="w-4 h-4 text-blue-600" />
            </button>
            <button
              onClick={handleDownload}
              className="p-1.5 bg-white/90 dark:bg-gray-800/90 rounded-md hover:bg-white dark:hover:bg-gray-700 transition-colors"
              title={t('contents.actions.download')}
            >
              <Download className="w-4 h-4 text-gray-600" />
            </button>
            {canEdit && onTagAssign && (
              <button
                onClick={handleTagAssign}
                className="p-1.5 bg-white/90 dark:bg-gray-800/90 rounded-md hover:bg-purple-50 dark:hover:bg-purple-900/50 transition-colors"
                title={t('contents.actions.assignTag', 'Assign Tag')}
              >
                <Tag className="w-4 h-4 text-purple-600" />
              </button>
            )}
            {canEdit && onPlaylistAssign && (
              <button
                onClick={handlePlaylistAssign}
                className="p-1.5 bg-white/90 dark:bg-gray-800/90 rounded-md hover:bg-blue-50 dark:hover:bg-blue-900/50 transition-colors"
                title={t('contents.actions.assignPlaylist', 'Assign Playlist')}
              >
                <ListMusic className="w-4 h-4 text-blue-600" />
              </button>
            )}
            {canDelete && (
              <button
                onClick={handleDeleteClick}
                className="p-1.5 bg-white/90 dark:bg-gray-800/90 rounded-md hover:bg-red-50 dark:hover:bg-red-900/50 transition-colors"
                title={t('contents.actions.delete')}
              >
                <Trash2 className="w-4 h-4 text-red-600" />
              </button>
            )}
          </div>

          {/* File Info - Bottom */}
          <div className="absolute bottom-0 left-0 right-0 p-3">
            <p className="text-white text-sm font-medium truncate" title={content.title}>
              {content.title}
            </p>
            <div className="flex items-center gap-2 text-white/70 text-xs mt-1">
              {content.resolution && <span>{content.resolution}</span>}
              <span>{formatFileSize(content.file_size)}</span>
            </div>
          </div>
        </div>

        {/* Selected Check Indicator */}
        {isSelected && (
          <div className="absolute top-2 left-2 pointer-events-none">
            <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center mt-10 ml-0">
              <Check className="w-4 h-4 text-white" />
            </div>
          </div>
        )}

        {/* Inactive Overlay */}
        {!content.is_active && (
          <div className="absolute inset-0 bg-gray-900/40 flex items-center justify-center pointer-events-none">
            <span className="px-2 py-1 bg-gray-800/80 text-gray-300 text-xs rounded">
              {t('contents.status.inactive')}
            </span>
          </div>
        )}
      </div>

      {/* Preview Modal */}
      <ContentPreviewModal
        isOpen={showPreview}
        content={content}
        onClose={() => setShowPreview(false)}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={showDeleteConfirm}
        onOpenChange={setShowDeleteConfirm}
        title={t('contents.dialogs.deleteTitle')}
        description={t('contents.dialogs.deleteMessage', { name: content.title })}
        variant="danger"
        confirmLabel={t('contents.actions.delete')}
        onConfirm={handleDelete}
        isLoading={deleteMutation.isPending}
      />
    </>
  );
}
