/**
 * Menu Media Upload Modal Component
 * Uses global queue store for persistent upload tracking
 *
 * Refactored to match Content UploadModal structure
 */

import { useState, useRef, ChangeEvent } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Upload,
  FileImage,
  Trash2,
} from 'lucide-react';
import { toast } from 'sonner';
import { Modal, Button } from '@/shared/components';
import { useUploadMenuMedia } from '../hooks/useMenuMedia';
import { useMenuMediaUploadStore } from '@/lib/stores/menuMediaUploadStore';

interface MenuMediaUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// File type validation
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export function MenuMediaUploadModal({ isOpen, onClose }: MenuMediaUploadModalProps) {
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [localFiles, setLocalFiles] = useState<File[]>([]);
  const [validationErrors, setValidationErrors] = useState<Map<string, string>>(new Map());

  const uploadMutation = useUploadMenuMedia();

  // Global queue store
  const addToQueue = useMenuMediaUploadStore((state) => state.addToQueue);
  const updateStatus = useMenuMediaUploadStore((state) => state.updateStatus);
  const setProcessing = useMenuMediaUploadStore((state) => state.setProcessing);

  // File validation
  const validateFile = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return t('menuMedia.upload.errors.invalidType', { defaultValue: 'Invalid file type. Only JPG, PNG, GIF, WebP allowed.' });
    }
    if (file.size > MAX_FILE_SIZE) {
      return t('menuMedia.upload.errors.tooLarge', { defaultValue: 'File is too large. Maximum size is 10MB.' });
    }
    return null;
  };

  // Add files to local state for validation
  const handleFilesSelected = (files: FileList | null) => {
    if (!files) return;

    const newErrors = new Map<string, string>();
    const validFiles: File[] = [];

    for (const file of Array.from(files)) {
      const error = validateFile(file);
      if (error) {
        newErrors.set(file.name, error);
      } else {
        validFiles.push(file);
      }
    }

    setValidationErrors(newErrors);
    setLocalFiles((prev) => [...prev, ...validFiles]);

    // Show error toast for invalid files
    if (newErrors.size > 0) {
      toast.error(t('menuMedia.upload.errors.rejected', { count: newErrors.size, defaultValue: `${newErrors.size} file(s) rejected due to validation errors` }));
    }
  };

  // Remove file from local list
  const removeLocalFile = (index: number) => {
    setLocalFiles((prev) => prev.filter((_, i) => i !== index));
  };

  // Clear local files
  const clearLocalFiles = () => {
    setLocalFiles([]);
    setValidationErrors(new Map());
  };

  // Process upload - Add to queue and start uploading
  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (localFiles.length === 0) return;

    // Add to global queue
    addToQueue(localFiles);
    setProcessing(true);

    // Get the items we just added (by matching file names)
    const queueItems = useMenuMediaUploadStore.getState().items;
    const newItems = queueItems.filter((item) =>
      localFiles.some((f) => f.name === item.file.name && item.status === 'pending')
    );

    // Clear local files and close modal
    clearLocalFiles();
    onClose();

    // Show toast notification
    toast.success(
      t('menuMedia.upload.addedToQueue', {
        count: newItems.length,
        defaultValue: `${newItems.length} file(s) added to queue`,
      })
    );

    // Process uploads
    for (const item of newItems) {
      updateStatus(item.id, 'uploading');

      try {
        await uploadMutation.mutateAsync({ file: item.file });
        updateStatus(item.id, 'success');
      } catch (error: any) {
        updateStatus(item.id, 'error', error.message || 'Upload failed');
      }
    }

    setProcessing(false);
  };

  // Handle file input change
  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    handleFilesSelected(e.target.files);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Drag handlers
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFilesSelected(e.dataTransfer.files);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  // Close modal
  const handleClose = () => {
    clearLocalFiles();
    onClose();
  };

  // Format file size
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  // Footer with action buttons
  const footer = (
    <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
      <Button
        type="button"
        variant="secondary"
        onClick={handleClose}
      >
        {t('common.cancel', { defaultValue: 'Cancel' })}
      </Button>
      <Button
        type="submit"
        form="upload-menu-media-form"
        disabled={localFiles.length === 0}
        leftIcon={<Upload className="w-4 h-4" />}
      >
        {localFiles.length > 0
          ? t('menuMedia.upload.addToQueue', { count: localFiles.length, defaultValue: `Add ${localFiles.length} to Queue` })
          : t('menuMedia.upload.upload', { defaultValue: 'Upload' })}
      </Button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={t('menuMedia.upload.title', { defaultValue: 'Upload Images' })}
      maxWidth="2xl"
      footer={footer}
      closeOnBackdropClick={true}
      className="h-[90vh]"
    >
      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-6">
        <form id="upload-menu-media-form" onSubmit={handleUpload} className="space-y-6">
          {/* Supported File Types Info */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-2">
              {t('menuMedia.upload.fileTypes.title', { defaultValue: 'Supported File Types' })}
            </h3>
            <div className="text-xs">
              <p className="font-medium text-blue-800 dark:text-blue-400 mb-1">
                {t('menuMedia.upload.fileTypes.images', { defaultValue: 'Images' })} (4)
              </p>
              <p className="text-blue-700 dark:text-blue-300 space-x-1">
                <span>.jpg</span> <span>.png</span> <span>.gif</span> <span>.webp</span>
              </p>
              <p className="text-blue-600 dark:text-blue-400 mt-2 text-xs">
                {t('menuMedia.upload.fileTypes.maxSize', { defaultValue: 'Maximum file size: 10MB per image' })}
              </p>
            </div>
          </div>

          {/* File Upload Area */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('menuMedia.upload.filesLabel', { defaultValue: 'Select Images' })}
            </label>
            <div
              onClick={() => fileInputRef.current?.click()}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={`
                border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors
                ${isDragging
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
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
                <div className="text-gray-400 dark:text-gray-500 mb-3">
                  <Upload className="w-12 h-12" />
                </div>
                <p className="text-sm font-medium text-gray-900 dark:text-white mb-1">
                  {isDragging
                    ? t('menuMedia.upload.dropHere', { defaultValue: 'Drop images here...' })
                    : t('menuMedia.upload.clickOrDrag', { defaultValue: 'Click to select or drag images here' })}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {t('menuMedia.upload.selectMultiple', { defaultValue: 'You can select multiple images at once' })}
                </p>
              </div>
            </div>

            {/* Selected Files List */}
            {localFiles.length > 0 && (
              <div className="mt-4 space-y-2 max-h-60 overflow-y-auto">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {t('menuMedia.upload.selectedFiles', { count: localFiles.length, defaultValue: `${localFiles.length} file(s) selected` })}
                </p>
                {localFiles.map((file, index) => (
                  <div
                    key={`${file.name}-${index}`}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <FileImage className="w-6 h-6 text-green-600" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {file.name}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeLocalFile(index)}
                      className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Validation Errors */}
          {validationErrors.size > 0 && (
            <div className="bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg text-sm">
              <p className="font-medium mb-2">
                {t('menuMedia.upload.errors.title', { count: validationErrors.size, defaultValue: `${validationErrors.size} file(s) rejected:` })}
              </p>
              <ul className="text-xs space-y-1">
                {Array.from(validationErrors.entries()).map(([name, error]) => (
                  <li key={name}>
                    <span className="font-medium">{name}:</span> {error}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </form>
      </div>
    </Modal>
  );
}
