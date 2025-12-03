/**
 * UploadItem Component
 *
 * Displays a single upload item with progress and controls
 */

import { useTranslation } from 'react-i18next';
import {
  FileImage,
  FileVideo,
  FileAudio,
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
import type { UploadItem as UploadItemType } from '../types/upload';
import { formatFileSize } from '../types/upload';
import { useUploadQueueStore } from '@/lib/stores/uploadQueueStore';

interface UploadItemProps {
  item: UploadItemType;
}

/**
 * Get icon for file type
 */
function getFileIcon(fileType: string) {
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

  const FileIcon = getFileIcon(item.fileType);
  const statusColor = getStatusColor(item.status);

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
        {/* Filename */}
        <p
          className="text-sm font-medium text-gray-900 dark:text-white truncate"
          title={item.fileName}
        >
          {item.fileName}
        </p>

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
