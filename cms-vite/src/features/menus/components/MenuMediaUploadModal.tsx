/**
 * Menu Media Upload Modal Component
 * Uses global queue store for persistent upload tracking
 */

import { useState, useRef, ChangeEvent } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Upload,
  Loader2,
  X,
  FileImage,
  Check,
  AlertCircle,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/shared/components';
import { useUploadMenuMedia } from '../hooks/useMenuMedia';
import { useMenuMediaUploadStore } from '@/lib/stores/menuMediaUploadStore';

interface MenuMediaUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function MenuMediaUploadModal({ isOpen, onClose }: MenuMediaUploadModalProps) {
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [localFiles, setLocalFiles] = useState<File[]>([]);
  const [validationErrors, setValidationErrors] = useState<Map<string, string>>(new Map());

  const uploadMutation = useUploadMenuMedia();

  // Global queue store
  const addToQueue = useMenuMediaUploadStore((state) => state.addToQueue);
  const items = useMenuMediaUploadStore((state) => state.items);
  const updateStatus = useMenuMediaUploadStore((state) => state.updateStatus);
  const setProcessing = useMenuMediaUploadStore((state) => state.setProcessing);
  const getSummary = useMenuMediaUploadStore((state) => state.getSummary);

  // File validation
  const validateFile = (file: File): string | null => {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!allowedTypes.includes(file.type)) {
      return 'Invalid file type. Only JPG, PNG, GIF, WebP allowed.';
    }
    if (file.size > maxSize) {
      return 'File is too large. Maximum size is 10MB.';
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
      toast.error(`${newErrors.size} file(s) rejected due to validation errors`);
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
  const handleUpload = async () => {
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
    toast.success(`${newItems.length} image(s) uploaded`);
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
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Upload Images
          </h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {/* Drop Zone */}
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
            <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-600 dark:text-gray-400 mb-1">
              {isDragging ? 'Drop images here...' : 'Drag & drop images here, or click to select'}
            </p>
            <p className="text-sm text-gray-500">JPG, PNG, GIF, WebP - Max 10MB</p>
          </div>

          {/* Selected Files */}
          {localFiles.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
                <span>{localFiles.length} file(s) ready to upload</span>
                <button
                  onClick={clearLocalFiles}
                  className="text-blue-600 hover:text-blue-700"
                >
                  Clear All
                </button>
              </div>

              <div className="max-h-60 overflow-y-auto space-y-2">
                {localFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800"
                  >
                    <FileImage className="w-4 h-4 text-gray-400" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {formatFileSize(file.size)}
                      </p>
                    </div>
                    <button
                      onClick={() => removeLocalFile(index)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Validation Errors */}
          {validationErrors.size > 0 && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <p className="text-sm font-medium text-red-800 dark:text-red-300 mb-2">
                {validationErrors.size} file(s) rejected:
              </p>
              <ul className="text-xs text-red-700 dark:text-red-400 space-y-1">
                {Array.from(validationErrors.entries()).map(([name, error]) => (
                  <li key={name}>
                    <span className="font-medium">{name}:</span> {error}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700">
          <Button variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          {localFiles.length > 0 && (
            <Button
              variant="primary"
              onClick={handleUpload}
              leftIcon={<Upload className="w-4 h-4" />}
            >
              Upload {localFiles.length} file(s)
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
