/**
 * Upload Modal Component
 *
 * File upload modal with progress tracking, validation, and quota checks
 *
 * ✅ REFACTORED: Now uses shared Modal component
 * - Fixed header (title)
 * - Fixed footer (buttons)
 * - Scrollable content (form fields)
 * - Click outside to close
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Upload, Loader2, FileImage, FileVideo, FileAudio, Trash2, AlertTriangle } from 'lucide-react';
import { Modal } from '@/shared/components';
import { useBulkUploadContent } from '../hooks/useContent';
import { useCheckContentQuota } from '@/features/organizations/hooks/useOrganizationQuota';
import { useAuthStore } from '@/lib/stores/authStore';
import { toast } from 'sonner';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// File type validation - Match backend support
const ALLOWED_TYPES = {
  image: ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/bmp'],
  video: ['video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska', 'video/x-m4v', 'video/x-flv'],
  audio: ['audio/mpeg', 'audio/mp3', 'audio/aac', 'audio/mp4', 'audio/ogg', 'audio/wav', 'audio/flac', 'audio/x-ms-wma', 'audio/x-m4a'],
};

const MAX_FILE_SIZE = {
  image: 50 * 1024 * 1024, // 50MB
  video: 500 * 1024 * 1024, // 500MB
  audio: 100 * 1024 * 1024, // 100MB
};

export function UploadModal({ isOpen, onClose }: UploadModalProps) {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [files, setFiles] = useState<File[]>([]);
  const [duration, setDuration] = useState(10);
  const [isActive, setIsActive] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const uploadMutation = useBulkUploadContent();

  // Calculate total file size
  const totalFileSize = files.reduce((sum, file) => sum + file.size, 0);

  // Check quota with current total file size
  const { data: quotaCheck, isLoading: quotaLoading } = useCheckContentQuota(
    user?.organization_id,
    totalFileSize
  );

  // Check if quota is exceeded
  const isQuotaExceeded = quotaCheck && !quotaCheck.allowed;

  // Show quota warning when files change
  useEffect(() => {
    if (files.length > 0 && isQuotaExceeded && quotaCheck) {
      toast.error(t('contents.upload.quota.exceeded'), {
        description: quotaCheck.reason || t('contents.upload.quota.cannotUpload'),
      });
    }
  }, [isQuotaExceeded, files.length, quotaCheck, t]);

  if (!isOpen) return null;

  // Reset form
  const resetForm = () => {
    setFiles([]);
    setDuration(10);
    setIsActive(true);
    setUploadProgress(0);
    setError(null);
  };

  // Handle file selection (multiple files)
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    if (selectedFiles.length === 0) return;

    setError(null);

    const validFiles: File[] = [];
    const errors: string[] = [];

    selectedFiles.forEach((file) => {
      // Detect file type
      const fileType = file.type;
      let contentType: 'image' | 'video' | 'audio' | null = null;

      if (ALLOWED_TYPES.image.includes(fileType)) contentType = 'image';
      else if (ALLOWED_TYPES.video.includes(fileType)) contentType = 'video';
      else if (ALLOWED_TYPES.audio.includes(fileType)) contentType = 'audio';

      if (!contentType) {
        errors.push(t('contents.upload.errors.invalidFileType', { filename: file.name }));
        return;
      }

      // Check file size
      const maxSize = MAX_FILE_SIZE[contentType];
      if (file.size > maxSize) {
        errors.push(
          t('contents.upload.errors.tooLarge', {
            filename: file.name,
            maxSize: Math.round(maxSize / 1024 / 1024)
          })
        );
        return;
      }

      validFiles.push(file);
    });

    if (errors.length > 0) {
      setError(errors.join(', '));
    }

    setFiles((prev) => [...prev, ...validFiles]);
  };

  // Remove file from list
  const handleRemoveFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  // Handle upload
  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();

    if (files.length === 0) {
      setError(t('contents.upload.errors.selectAtLeastOne'));
      return;
    }

    // Final quota check before upload
    if (isQuotaExceeded) {
      toast.error(t('contents.upload.quota.exceeded'), {
        description: quotaCheck?.reason || t('contents.upload.quota.cannotUpload'),
      });
      return;
    }

    try {
      await uploadMutation.mutateAsync({
        files,
        duration,
        is_active: isActive,
        onProgress: setUploadProgress,
      });

      // Success - close modal and reset
      resetForm();
      onClose();
    } catch (err) {
      // Error is handled by the mutation hook with toast
      console.error('Upload error:', err);
    }
  };

  // Handle close
  const handleClose = () => {
    if (uploadMutation.isPending) {
      // Don't allow closing during upload
      return;
    }
    resetForm();
    onClose();
  };

  // Get file icon
  const getFileIcon = (file?: File) => {
    if (!file) return <Upload className="w-6 h-6" />;

    if (file.type.startsWith('image/')) return <FileImage className="w-6 h-6 text-green-600" />;
    if (file.type.startsWith('video/')) return <FileVideo className="w-6 h-6 text-blue-600" />;
    if (file.type.startsWith('audio/')) return <FileAudio className="w-6 h-6 text-purple-600" />;

    return <Upload className="w-6 h-6" />;
  };

  // Footer with action buttons
  const footer = (
    <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-4">
      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={handleClose}
          disabled={uploadMutation.isPending}
          className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50 transition-colors"
        >
          {t('contents.buttons.cancel')}
        </button>
        <button
          type="submit"
          form="upload-content-form"
          disabled={files.length === 0 || uploadMutation.isPending || isQuotaExceeded || quotaLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
        >
          {uploadMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              {t('contents.buttons.uploadingFiles', { count: files.length })}
            </>
          ) : quotaLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              {t('contents.buttons.checkingQuota')}
            </>
          ) : isQuotaExceeded ? (
            <>
              <AlertTriangle className="w-4 h-4" />
              {t('contents.buttons.quotaExceeded')}
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              {files.length > 0 ? t('contents.buttons.uploadWithCount', { count: files.length }) : t('contents.buttons.upload')}
            </>
          )}
        </button>
      </div>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={t('contents.modals.uploadContent')}
      maxWidth="2xl"
      footer={footer}
      closeOnBackdropClick={!uploadMutation.isPending}
      className="h-[90vh]"
    >
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-6">
        <form id="upload-content-form" onSubmit={handleUpload} className="space-y-6">
          {/* Quota Warning Banner */}
          {isQuotaExceeded && quotaCheck && (
            <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-orange-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="text-sm font-semibold text-orange-900 dark:text-orange-300 mb-1">
                    {t('contents.upload.quota.limitReached')}
                  </h3>
                  <p className="text-xs text-orange-800 dark:text-orange-400">
                    {quotaCheck.reason}
                  </p>
                  <p className="text-xs text-orange-700 dark:text-orange-500 mt-1">
                    {t('contents.upload.quota.totalFileSize', { size: (totalFileSize / 1024 / 1024).toFixed(2) })}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Supported File Types Info */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-3">
              {t('contents.upload.fileTypes.title')}
            </h3>
            <div className="grid grid-cols-3 gap-4 text-xs">
              <div>
                <p className="font-medium text-blue-800 dark:text-blue-400 mb-1">
                  {t('contents.upload.fileTypes.images')}
                </p>
                <p className="text-blue-700 dark:text-blue-300 space-x-1">
                  <span>.jpg</span> <span>.jpeg</span> <span>.png</span> <span>.webp</span>{' '}
                  <span>.gif</span> <span>.bmp</span>
                </p>
              </div>
              <div>
                <p className="font-medium text-blue-800 dark:text-blue-400 mb-1">
                  {t('contents.upload.fileTypes.videos')}
                </p>
                <p className="text-blue-700 dark:text-blue-300 space-x-1">
                  <span>.mp4</span> <span>.webm</span> <span>.mkv</span> <span>.avi</span>{' '}
                  <span>.mov</span> <span>.m4v</span> <span>.flv</span>
                </p>
              </div>
              <div>
                <p className="font-medium text-blue-800 dark:text-blue-400 mb-1">
                  {t('contents.upload.fileTypes.audio')}
                </p>
                <p className="text-blue-700 dark:text-blue-300 space-x-1">
                  <span>.mp3</span> <span>.aac</span> <span>.m4a</span> <span>.ogg</span>{' '}
                  <span>.wav</span> <span>.flac</span> <span>.wma</span>
                </p>
              </div>
            </div>
          </div>

          {/* File Upload Area */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('contents.upload.filesLabel')}
            </label>
            <div className="border-2 border-dashed rounded-lg p-6 text-center border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500">
              <input
                type="file"
                accept="image/*,video/*,audio/*"
                onChange={handleFileChange}
                disabled={uploadMutation.isPending}
                className="hidden"
                id="file-upload"
                multiple
              />
              <label
                htmlFor="file-upload"
                className={`cursor-pointer ${
                  uploadMutation.isPending ? 'pointer-events-none opacity-50' : ''
                }`}
              >
                <div className="flex flex-col items-center">
                  <div className="text-gray-400 dark:text-gray-500 mb-3">
                    <Upload className="w-12 h-12" />
                  </div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white mb-1">
                    {t('contents.upload.clickOrDrag')}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {t('contents.upload.selectMultiple')}
                  </p>
                </div>
              </label>
            </div>

            {/* Selected Files List */}
            {files.length > 0 && (
              <div className="mt-4 space-y-2 max-h-60 overflow-y-auto">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('contents.upload.selectedFiles', { count: files.length })}
                </p>
                {files.map((file, index) => (
                  <div
                    key={`${file.name}-${index}`}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      {getFileIcon(file)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {file.name}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemoveFile(index)}
                      disabled={uploadMutation.isPending}
                      className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 disabled:opacity-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Duration */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('contents.form.displayDuration')}
            </label>
            <input
              type="number"
              value={duration}
              onChange={(e) => setDuration(parseInt(e.target.value))}
              disabled={uploadMutation.isPending}
              className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white disabled:opacity-50"
              min={1}
              max={86400}
              required
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {t('contents.form.durationHelp')}
            </p>
          </div>

          {/* Active Status */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is-active"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              disabled={uploadMutation.isPending}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
            />
            <label
              htmlFor="is-active"
              className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              {t('contents.form.activeLabel')}
            </label>
          </div>

          {/* Upload Progress */}
          {uploadMutation.isPending && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('contents.upload.uploading')}
                </span>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {uploadProgress}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

        </form>
      </div>
    </Modal>
  );
}
