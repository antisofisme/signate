/**
 * Content Detail Sidebar Component
 * Right sidebar panel showing content metadata (NO thumbnail preview)
 * Supports inline editing and actions
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  X,
  Download,
  Trash2,
  FileImage,
  FileVideo,
  FileAudio,
  Calendar,
  HardDrive,
  Maximize,
  User,
  Save,
  Pencil,
  Clock,
  Loader2,
  AlertCircle,
  CheckCircle,
  Play,
  List,
  Tag,
  Monitor,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button, ConfirmDialog } from '@/shared/components';
import { useCanPerformAction } from '@/features/rbac/hooks/usePermissions';
import { useUpdateContent, useDeleteContent } from '../hooks/useContent';
import { useContentTags, useUnassignTagFromContents } from '@/features/tags/hooks/useTags';
import { formatFileSize, downloadContent } from '../api/contentApi';
import { AddToPlaylistModal } from './AddToPlaylistModal';
import { AssignToDeviceModal } from './AssignToDeviceModal';
import type { Content, ContentType, TranscodingStatus, ContentUsage } from '../types/content';

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

// Get transcoding status display
function getTranscodingStatusDisplay(status: TranscodingStatus, progress: number, t: (key: string) => string) {
  switch (status) {
    case 'pending':
      return {
        icon: <Clock className="w-4 h-4 text-gray-500" />,
        label: t('contents.transcoding.pending'),
        color: 'text-gray-600 dark:text-gray-400',
      };
    case 'processing':
      return {
        icon: <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />,
        label: `${t('contents.transcoding.processing')} (${progress}%)`,
        color: 'text-blue-600 dark:text-blue-400',
      };
    case 'failed':
      return {
        icon: <AlertCircle className="w-4 h-4 text-red-500" />,
        label: t('contents.transcoding.failed'),
        color: 'text-red-600 dark:text-red-400',
      };
    case 'completed':
      return {
        icon: <CheckCircle className="w-4 h-4 text-green-500" />,
        label: t('contents.transcoding.completed'),
        color: 'text-green-600 dark:text-green-400',
      };
  }
}

interface ContentDetailSidebarProps {
  content: Content | null;
  usage?: ContentUsage;
  isOpen: boolean;
  onUpdate?: (content: Content) => void;
  onDelete?: () => void;
  onClose?: () => void;
}

export function ContentDetailSidebar({
  content,
  usage,
  isOpen,
  onUpdate,
  onDelete,
  onClose,
}: ContentDetailSidebarProps) {
  const { t } = useTranslation();

  // Permission checks
  const { hasPermission: canUpdate } = useCanPerformAction('contents', 'edit');
  const { hasPermission: canDelete } = useCanPerformAction('contents', 'delete');

  // State for inline editing
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [isEditingDuration, setIsEditingDuration] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editDuration, setEditDuration] = useState(0);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showAddToPlaylist, setShowAddToPlaylist] = useState(false);
  const [showAssignToDevice, setShowAssignToDevice] = useState(false);

  // Mutations
  const updateMutation = useUpdateContent();
  const deleteMutation = useDeleteContent();
  const unassignTagMutation = useUnassignTagFromContents();

  // Fetch actual tags for this content
  const { data: contentTags = [], refetch: refetchTags } = useContentTags(content?.id || 0);

  // Reset edit state when content changes
  useEffect(() => {
    if (content) {
      setEditTitle(content.title || '');
      setEditDuration(content.duration);
      setIsEditingTitle(false);
      setIsEditingDuration(false);
    }
  }, [content?.id]);

  // Handlers
  const handleDownload = async () => {
    if (!content) return;
    try {
      await downloadContent(content.id, content.original_filename);
      toast.success(t('contents.messages.downloadStarted'));
    } catch {
      toast.error(t('contents.messages.downloadFailed'));
    }
  };

  const handleSaveTitle = async () => {
    if (!content) return;
    try {
      await updateMutation.mutateAsync({
        id: content.id,
        data: { title: editTitle || content.original_filename },
      });
      setIsEditingTitle(false);
      onUpdate?.({ ...content, title: editTitle || content.original_filename });
    } catch {
      // Error handled by mutation
    }
  };

  const handleSaveDuration = async () => {
    if (!content) return;
    try {
      await updateMutation.mutateAsync({
        id: content.id,
        data: { duration: editDuration },
      });
      setIsEditingDuration(false);
      onUpdate?.({ ...content, duration: editDuration });
    } catch {
      // Error handled by mutation
    }
  };

  const handleToggleActive = async () => {
    if (!content) return;
    try {
      await updateMutation.mutateAsync({
        id: content.id,
        data: { is_active: !content.is_active },
      });
      onUpdate?.({ ...content, is_active: !content.is_active });
    } catch {
      // Error handled by mutation
    }
  };

  const handleDelete = async () => {
    if (!content) return;
    await deleteMutation.mutateAsync(content.id);
    setShowDeleteConfirm(false);
    onDelete?.();
  };

  const handleRemoveTag = async (tagId: number) => {
    if (!content) return;
    try {
      await unassignTagMutation.mutateAsync({
        tagId,
        contentIds: [content.id],
      });
      // Refetch tags after successful removal
      refetchTags();
    } catch {
      // Error handled by mutation
    }
  };

  // Check if usage exists (tags are now shown separately with remove buttons)
  const hasUsage = usage && (usage.playlists.length > 0 || usage.devices.length > 0);

  // Don't render if not open
  if (!isOpen) {
    return null;
  }

  // Empty state (shouldn't happen since we only open when content is selected)
  if (!content) {
    return null;
  }

  const transcodingDisplay = content.content_type === 'video'
    ? getTranscodingStatusDisplay(content.transcoding_status, content.transcoding_progress, t)
    : null;

  return (
    <div className="w-[360px] flex-shrink-0 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden animate-slide-in-right">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-gray-100 dark:bg-gray-700 rounded">
            {getContentTypeIcon(content.content_type)}
          </div>
          <h3 className="font-medium text-gray-900 dark:text-white">
            {t('contents.sidebar.title', 'Content Details')}
          </h3>
        </div>
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
        {/* Editable Title */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <label className="flex items-center justify-between text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-1.5">
            <span>{t('contents.sidebar.titleField', 'Title')}</span>
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
                placeholder={t('contents.sidebar.titlePlaceholder', 'Enter title...')}
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
                  setEditTitle(content.title || '');
                }}
                className="p-1.5 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <p className="text-sm text-gray-900 dark:text-white font-medium truncate" title={content.title}>
              {content.title}
            </p>
          )}
        </div>

        {/* Status Toggle */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                {t('contents.sidebar.status', 'Status')}
              </p>
              <p className={`text-sm font-medium ${content.is_active ? 'text-green-600' : 'text-gray-500'}`}>
                {content.is_active ? t('contents.status.active') : t('contents.status.inactive')}
              </p>
            </div>
            {canUpdate && (
              <button
                onClick={handleToggleActive}
                disabled={updateMutation.isPending}
                className="p-1"
              >
                {content.is_active ? (
                  <ToggleRight className="w-8 h-8 text-green-500" />
                ) : (
                  <ToggleLeft className="w-8 h-8 text-gray-400" />
                )}
              </button>
            )}
          </div>
        </div>

        {/* Metadata - Read Only */}
        <div className="p-4 space-y-3 border-b border-gray-200 dark:border-gray-700">
          <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
            {t('contents.sidebar.metadata', 'File Information')}
          </h4>

          {/* Filename */}
          <div className="flex items-start gap-3">
            {getContentTypeIcon(content.content_type, 'w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0')}
            <div className="min-w-0">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {t('contents.sidebar.filename', 'Filename')}
              </p>
              <p className="text-sm text-gray-900 dark:text-white truncate" title={content.original_filename}>
                {content.original_filename}
              </p>
            </div>
          </div>

          {/* Resolution */}
          {content.resolution && (
            <div className="flex items-start gap-3">
              <Maximize className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {t('contents.sidebar.resolution', 'Resolution')}
                </p>
                <p className="text-sm text-gray-900 dark:text-white">
                  {content.resolution}
                </p>
              </div>
            </div>
          )}

          {/* File Size */}
          <div className="flex items-start gap-3">
            <HardDrive className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {t('contents.sidebar.size', 'Size')}
              </p>
              <p className="text-sm text-gray-900 dark:text-white">
                {formatFileSize(content.file_size)} ({content.mime_type})
              </p>
            </div>
          </div>

          {/* Duration - Editable for images */}
          <div className="flex items-start gap-3">
            <Play className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {t('contents.sidebar.duration', 'Display Duration')}
                </p>
                {canUpdate && content.content_type === 'image' && !isEditingDuration && (
                  <button
                    onClick={() => setIsEditingDuration(true)}
                    className="text-blue-500 hover:text-blue-600"
                  >
                    <Pencil className="w-3 h-3" />
                  </button>
                )}
              </div>
              {isEditingDuration ? (
                <div className="flex items-center gap-2 mt-1">
                  <input
                    type="number"
                    value={editDuration}
                    onChange={(e) => setEditDuration(Number(e.target.value))}
                    min={1}
                    className="w-20 px-2 py-1 text-sm bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500"
                    autoFocus
                  />
                  <span className="text-sm text-gray-500">s</span>
                  <button
                    onClick={handleSaveDuration}
                    disabled={updateMutation.isPending}
                    className="p-1 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded"
                  >
                    <Save className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => {
                      setIsEditingDuration(false);
                      setEditDuration(content.duration);
                    }}
                    className="p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <p className="text-sm text-gray-900 dark:text-white">
                  {content.duration}s
                </p>
              )}
            </div>
          </div>

          {/* Uploaded Date */}
          <div className="flex items-start gap-3">
            <Calendar className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {t('contents.sidebar.uploaded', 'Uploaded')}
              </p>
              <p className="text-sm text-gray-900 dark:text-white">
                {formatDate(content.created_at)}
              </p>
            </div>
          </div>

          {/* Uploaded By */}
          {content.uploaded_by && (
            <div className="flex items-start gap-3">
              <User className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {t('contents.sidebar.uploadedBy', 'Uploaded by')}
                </p>
                <p className="text-sm text-gray-900 dark:text-white">
                  User #{content.uploaded_by}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Transcoding Status - Video only */}
        {content.content_type === 'video' && transcodingDisplay && (
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-3">
              {t('contents.sidebar.transcoding', 'Transcoding Status')}
            </h4>
            <div className="flex items-center gap-2">
              {transcodingDisplay.icon}
              <span className={`text-sm ${transcodingDisplay.color}`}>
                {transcodingDisplay.label}
              </span>
            </div>
            {/* HLS Availability */}
            {content.hls_master_playlist_url && (
              <div className="mt-3 flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                <CheckCircle className="w-4 h-4" />
                <span>{t('contents.sidebar.hlsAvailable', 'HLS Streaming Available')}</span>
              </div>
            )}
          </div>
        )}

        {/* Tags Section - Individual tags with remove button */}
        {contentTags.length > 0 && (
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-3">
              {t('contents.sidebar.tags', 'Tags')}
            </h4>
            <div className="flex flex-wrap gap-2">
              {contentTags.map((tag) => (
                <div
                  key={tag.id}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium"
                  style={{
                    backgroundColor: tag.color ? `${tag.color}20` : '#e5e7eb',
                    color: tag.color || '#374151',
                    border: `1px solid ${tag.color || '#d1d5db'}`,
                  }}
                >
                  <span>{tag.tag_name}</span>
                  {canUpdate && (
                    <button
                      onClick={() => handleRemoveTag(tag.id)}
                      disabled={unassignTagMutation.isPending}
                      className="ml-0.5 p-0.5 rounded-full hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
                      title={t('contents.actions.removeTag', 'Remove tag')}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Usage Info - Playlists and Devices */}
        {usage && (usage.playlists.length > 0 || usage.devices.length > 0) && (
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-3">
              {t('contents.sidebar.usedIn', 'Used In')}
            </h4>
            <div className="space-y-2">
              {usage.playlists.length > 0 && (
                <div className="flex items-center gap-2 text-sm">
                  <List className="w-4 h-4 text-blue-500" />
                  <span className="text-gray-900 dark:text-white">
                    {usage.playlists.length} {t('contents.usage.playlists', 'playlist(s)')}
                  </span>
                </div>
              )}
              {usage.devices.length > 0 && (
                <div className="flex items-center gap-2 text-sm">
                  <Monitor className="w-4 h-4 text-green-500" />
                  <span className="text-gray-900 dark:text-white">
                    {usage.devices.length} {t('contents.usage.devices', 'device(s)')}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Actions - Fixed at bottom */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
        <div className="flex flex-wrap gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleDownload}
            leftIcon={<Download className="w-4 h-4" />}
            className="flex-1"
          >
            {t('contents.actions.download', 'Download')}
          </Button>
          {canUpdate && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowAddToPlaylist(true)}
              leftIcon={<List className="w-4 h-4" />}
              className="flex-1"
            >
              {t('contents.actions.addToPlaylist', 'Add to Playlist')}
            </Button>
          )}
          {canUpdate && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowAssignToDevice(true)}
              leftIcon={<Monitor className="w-4 h-4" />}
              className="flex-1"
            >
              {t('contents.actions.assignToDevice', 'Assign to Device')}
            </Button>
          )}
          {canDelete && (
            <Button
              variant="danger"
              size="sm"
              onClick={() => setShowDeleteConfirm(true)}
              leftIcon={<Trash2 className="w-4 h-4" />}
              className="flex-1"
            >
              {t('contents.actions.delete', 'Delete')}
            </Button>
          )}
        </div>
      </div>

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

      {/* Add to Playlist Modal */}
      <AddToPlaylistModal
        open={showAddToPlaylist}
        onOpenChange={setShowAddToPlaylist}
        content={content}
      />

      {/* Assign to Device Modal */}
      <AssignToDeviceModal
        open={showAssignToDevice}
        onOpenChange={setShowAssignToDevice}
        content={content}
      />
    </div>
  );
}
