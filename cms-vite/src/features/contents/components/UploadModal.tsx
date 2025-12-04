/**
 * Upload Modal Component
 *
 * File upload modal with validation and quota checks
 * Uses RHF for form fields, useState for file handling
 *
 * ✅ REFACTORED: Uses Upload Queue + RHF + Shared Components
 * - Files added to queue instead of blocking upload
 * - Modal closes immediately after adding to queue
 * - Progress tracked in UploadQueuePanel (bottom-right)
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Upload, FileImage, FileVideo, FileAudio, Trash2, AlertTriangle } from 'lucide-react';
import { Modal, Button, FormInput, FormSwitch } from '@/shared/components';
import { useCheckContentQuota } from '@/features/organizations/hooks/useOrganizationQuota';
import { useAuthStore } from '@/lib/stores/authStore';
import { useUploadQueueStore } from '@/lib/stores/uploadQueueStore';
import { toast } from '@/shared/utils/toast';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Validation schema for form fields
const uploadFormSchema = z.object({
  duration: z.coerce.number().min(1, 'Duration must be at least 1 second').max(86400, 'Duration must be less than 24 hours'),
  is_active: z.boolean(),
});

type UploadFormData = z.infer<typeof uploadFormSchema>;

// File type validation - Match backend support (Updated 2025-11-29)
const ALLOWED_TYPES = {
  image: [
    'image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/bmp',
    'image/tiff', 'image/heic', 'image/heif', 'image/avif',
  ],
  video: [
    'video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo', 'video/x-matroska',
    'video/x-m4v', 'video/x-flv', 'video/x-ms-wmv',
    'video/mpeg', 'video/3gpp', 'video/3gpp2', 'video/mp2t', 'video/ogg',
  ],
  audio: [
    'audio/mpeg', 'audio/mp3', 'audio/aac', 'audio/mp4', 'audio/ogg', 'audio/wav',
    'audio/flac', 'audio/x-ms-wma', 'audio/x-m4a',
    'audio/opus', 'audio/amr', 'audio/aiff', 'audio/x-aiff', 'audio/webm',
  ],
};

const MAX_FILE_SIZE = {
  image: 50 * 1024 * 1024, // 50MB
  video: 500 * 1024 * 1024, // 500MB
  audio: 100 * 1024 * 1024, // 100MB
};

export function UploadModal({ isOpen, onClose }: UploadModalProps) {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const { addToQueue } = useUploadQueueStore();

  // File state (kept separate from RHF as RHF doesn't handle file lists well)
  const [files, setFiles] = useState<File[]>([]);
  const [fileError, setFileError] = useState<string | null>(null);

  // RHF for form fields
  const methods = useForm<UploadFormData>({
    resolver: zodResolver(uploadFormSchema),
    defaultValues: {
      duration: 10,
      is_active: true,
    },
  });

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
    setFileError(null);
    methods.reset();
  };

  // Handle file selection (multiple files)
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    if (selectedFiles.length === 0) return;

    setFileError(null);

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
      setFileError(errors.join(', '));
    }

    setFiles((prev) => [...prev, ...validFiles]);
  };

  // Remove file from list
  const handleRemoveFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  // Handle upload - Add files to queue
  const handleSubmit = (data: UploadFormData) => {
    if (files.length === 0) {
      setFileError(t('contents.upload.errors.selectAtLeastOne'));
      return;
    }

    // Final quota check before upload
    if (isQuotaExceeded) {
      toast.error(t('contents.upload.quota.exceeded'), {
        description: quotaCheck?.reason || t('contents.upload.quota.cannotUpload'),
      });
      return;
    }

    // Add files to upload queue (content type)
    addToQueue(files, { uploadType: 'content', duration: data.duration, isActive: data.is_active });

    // Show toast notification
    toast.success(
      t('uploads.addedToQueue', {
        count: files.length,
        defaultValue: `${files.length} file(s) added to queue`,
      })
    );

    // Close modal immediately and reset form
    resetForm();
    onClose();
  };

  // Handle close
  const handleClose = () => {
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
    <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
      <Button
        type="button"
        variant="secondary"
        onClick={handleClose}
      >
        {t('contents.buttons.cancel')}
      </Button>
      <Button
        type="submit"
        form="upload-content-form"
        disabled={files.length === 0 || isQuotaExceeded || quotaLoading}
        loading={quotaLoading}
        leftIcon={isQuotaExceeded ? <AlertTriangle className="w-4 h-4" /> : <Upload className="w-4 h-4" />}
      >
        {isQuotaExceeded
          ? t('contents.buttons.quotaExceeded')
          : files.length > 0
          ? t('contents.buttons.addToQueue', { count: files.length, defaultValue: `Add ${files.length} to Queue` })
          : t('contents.buttons.upload')
        }
      </Button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={t('contents.modals.uploadContent')}
      maxWidth="2xl"
      footer={footer}
      closeOnBackdropClick={true}
      className="h-[90vh]"
    >
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-6">
        <FormProvider {...methods}>
          <form id="upload-content-form" onSubmit={methods.handleSubmit(handleSubmit)} className="space-y-6">
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
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div>
                  <p className="font-medium text-blue-800 dark:text-blue-400 mb-1">
                    {t('contents.upload.fileTypes.images')} (11)
                  </p>
                  <p className="text-blue-700 dark:text-blue-300 space-x-1">
                    <span>.jpg</span> <span>.png</span> <span>.webp</span> <span>.gif</span>{' '}
                    <span>.bmp</span> <span>.tiff</span> <span>.heic</span> <span>.avif</span>
                  </p>
                </div>
                <div>
                  <p className="font-medium text-blue-800 dark:text-blue-400 mb-1">
                    {t('contents.upload.fileTypes.videos')} (16)
                  </p>
                  <p className="text-blue-700 dark:text-blue-300 space-x-1">
                    <span>.mp4</span> <span>.webm</span> <span>.mkv</span> <span>.avi</span>{' '}
                    <span>.mov</span> <span>.m4v</span> <span>.wmv</span> <span>.mpg</span>{' '}
                    <span>.3gp</span> <span>.mts</span> <span>.ts</span> <span>.ogv</span>
                  </p>
                </div>
                <div>
                  <p className="font-medium text-blue-800 dark:text-blue-400 mb-1">
                    {t('contents.upload.fileTypes.audio')} (14)
                  </p>
                  <p className="text-blue-700 dark:text-blue-300 space-x-1">
                    <span>.mp3</span> <span>.aac</span> <span>.m4a</span> <span>.ogg</span>{' '}
                    <span>.wav</span> <span>.flac</span> <span>.wma</span> <span>.opus</span>{' '}
                    <span>.amr</span> <span>.aiff</span> <span>.oga</span> <span>.weba</span>
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
                  className="hidden"
                  id="file-upload"
                  multiple
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer"
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
                        className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* File Error Message */}
            {fileError && (
              <div className="bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg text-sm">
                {fileError}
              </div>
            )}

            {/* Duration - Using RHF FormInput */}
            <FormInput
              name="duration"
              type="number"
              label={t('contents.form.displayDuration')}
              description={t('contents.form.durationHelp')}
              min={1}
              max={86400}
            />

            {/* Active Status - Using RHF FormSwitch */}
            <FormSwitch
              name="is_active"
              label={t('contents.form.activeLabel')}
              description={t('contents.form.activeHelp') || 'Content will be available for playlists'}
            />
          </form>
        </FormProvider>
      </div>
    </Modal>
  );
}
