/**
 * UploadItem Component
 *
 * Displays a single upload item with progress and controls
 * Supports multiple upload types: content, menu_media
 */

import { useTranslation } from 'react-i18next';
import {
  FileImage,
  FileVideo,
  FileAudio,
  Image,
  X,
  RotateCcw,
  Trash2,
  Check,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import Button from '@/shared/components/common/Button';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import type { UploadItem as UploadItemType, UploadType } from '../types/upload';
import { formatFileSize } from '../types/upload';
import { useUploadQueueStore } from '@/lib/stores/uploadQueueStore';

interface UploadItemProps {
  item: UploadItemType;
}

/**
 * Get icon for file type based on uploadType and fileType
 */
function getFileIcon(uploadType: UploadType, fileType?: string) {
  // Menu media is always an image
  if (uploadType === 'menu_media') {
    return Image;
  }
  // Content uploads use file type
  switch (fileType) {
    case 'image':
      return FileImage;
    case 'video':
      return FileVideo;
    case 'audio':
      return FileAudio;
    default:
      return FileImage;
  }
}

/**
 * Get upload type badge config
 */
function getUploadTypeBadge(uploadType: UploadType) {
  switch (uploadType) {
    case 'menu_media':
      return {
        label: 'Menu',
        bgColor: 'bg-purple-100 dark:bg-purple-900/30',
        textColor: 'text-purple-700 dark:text-purple-300',
      };
    case 'content':
    default:
      return {
        label: 'Content',
        bgColor: 'bg-blue-100 dark:bg-blue-900/30',
        textColor: 'text-blue-700 dark:text-blue-300',
      };
  }
}

/**
 * Get status color
 */
function getStatusColor(status: string) {
  switch (status) {
    case 'uploading':
      return 'text-blue-500';
    case 'completed':
      return 'text-green-500';
    case 'failed':
      return 'text-red-500';
    case 'cancelled':
      return 'text-gray-400';
    default:
      return 'text-gray-500';
  }
}

export function UploadItem({ item }: UploadItemProps) {
  const { t } = useTranslation();
  const { cancelUpload, retryUpload, removeFromQueue } = useUploadQueueStore();

  const FileIcon = getFileIcon(item.uploadType, item.fileType);
  const statusColor = getStatusColor(item.status);
  const typeBadge = getUploadTypeBadge(item.uploadType);

  const handleCancel = () => {
    cancelUpload(item.id);
  };

  const handleRetry = () => {
    retryUpload(item.id);
  };

  const handleRemove = () => {
    removeFromQueue(item.id);
  };

  return (
    <div className="flex items-center gap-3 p-3 border-b border-gray-200 dark:border-gray-700 last:border-b-0 hover:bg-gray-50 dark:hover:bg-gray-700/50">
      {/* File Icon */}
      <div className={cn('flex-shrink-0', statusColor)}>
        <FileIcon className="w-5 h-5" />
      </div>

      {/* File Info */}
      <div className="flex-1 min-w-0">
        {/* Filename with type badge */}
        <div className="flex items-center gap-2">
          <p
            className="text-sm font-medium text-gray-900 dark:text-white truncate"
            title={item.fileName}
          >
            {item.fileName}
          </p>
          {/* Upload type badge */}
          <span
            className={cn(
              'flex-shrink-0 px-1.5 py-0.5 text-[10px] font-medium rounded',
              typeBadge.bgColor,
              typeBadge.textColor
            )}
          >
            {typeBadge.label}
          </span>
        </div>

        {/* File size and status */}
        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
          <span>{formatFileSize(item.fileSize)}</span>

          {/* Status indicator */}
          {item.status === 'pending' && (
            <span className="text-gray-400">{t('uploads.status.pending')}</span>
          )}
          {item.status === 'uploading' && (
            <span className="text-blue-500">{item.progress}%</span>
          )}
          {item.status === 'completed' && (
            <span className="text-green-500">{t('uploads.status.completed')}</span>
          )}
          {item.status === 'failed' && (
            <span className="text-red-500" title={item.error}>
              {t('uploads.status.failed')}
            </span>
          )}
          {item.status === 'cancelled' && (
            <span className="text-gray-400">{t('uploads.status.cancelled')}</span>
          )}
        </div>

        {/* Progress bar (only when uploading) */}
        {item.status === 'uploading' && (
          <div className="mt-1">
            <Progress value={item.progress} className="h-1" />
          </div>
        )}

        {/* Error message */}
        {item.status === 'failed' && item.error && (
          <p className="mt-1 text-xs text-red-500 truncate" title={item.error}>
            {item.error}
          </p>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex-shrink-0 flex items-center gap-1">
        {/* Pending: Show loader */}
        {item.status === 'pending' && (
          <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
        )}

        {/* Uploading: Cancel button */}
        {item.status === 'uploading' && (
          <Button
            variant="icon"
            size="sm"
            className="h-7 w-7"
            onClick={handleCancel}
            title={t('uploads.actions.cancel')}
          >
            <X className="w-4 h-4" />
          </Button>
        )}

        {/* Completed: Checkmark */}
        {item.status === 'completed' && (
          <div className="flex items-center gap-1">
            <Check className="w-4 h-4 text-green-500" />
            <Button
              variant="icon"
              size="sm"
              className="h-7 w-7 text-gray-400 hover:text-gray-600"
              onClick={handleRemove}
              title={t('uploads.actions.remove')}
            >
              <Trash2 className="w-3 h-3" />
            </Button>
          </div>
        )}

        {/* Failed: Retry + Remove buttons */}
        {item.status === 'failed' && (
          <div className="flex items-center gap-1">
            <AlertCircle className="w-4 h-4 text-red-500" />
            {item.file && (
              <Button
                variant="icon"
                size="sm"
                className="h-7 w-7 text-blue-500 hover:text-blue-600"
                onClick={handleRetry}
                title={t('uploads.actions.retry')}
              >
                <RotateCcw className="w-4 h-4" />
              </Button>
            )}
            <Button
              variant="icon"
              size="sm"
              className="h-7 w-7 text-gray-400 hover:text-gray-600"
              onClick={handleRemove}
              title={t('uploads.actions.remove')}
            >
              <Trash2 className="w-3 h-3" />
            </Button>
          </div>
        )}

        {/* Cancelled: Remove button */}
        {item.status === 'cancelled' && (
          <Button
            variant="icon"
            size="sm"
            className="h-7 w-7 text-gray-400 hover:text-gray-600"
            onClick={handleRemove}
            title={t('uploads.actions.remove')}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        )}
      </div>
    </div>
  );
}
