/**
 * Upload Modal Component
 *
 * File upload modal with progress tracking and validation
 */

import { useState } from 'react';
import { X, Upload, Loader2, FileImage, FileVideo, FileAudio } from 'lucide-react';
import { useUploadContent } from '../hooks/useContent';
import type { ContentUploadData } from '../types/content';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// File type validation
const ALLOWED_TYPES = {
  image: ['image/jpeg', 'image/png', 'image/webp', 'image/gif'],
  video: ['video/mp4', 'video/webm', 'video/quicktime'],
  audio: ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/aac'],
};

const MAX_FILE_SIZE = {
  image: 50 * 1024 * 1024, // 50MB
  video: 500 * 1024 * 1024, // 500MB
  audio: 100 * 1024 * 1024, // 100MB
};

export function UploadModal({ isOpen, onClose }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [duration, setDuration] = useState(10);
  const [isActive, setIsActive] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const uploadMutation = useUploadContent();

  if (!isOpen) return null;

  // Reset form
  const resetForm = () => {
    setFile(null);
    setTitle('');
    setDescription('');
    setDuration(10);
    setIsActive(true);
    setUploadProgress(0);
    setError(null);
  };

  // Handle file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setError(null);

    // Detect file type
    const fileType = selectedFile.type;
    let contentType: 'image' | 'video' | 'audio' | null = null;

    if (ALLOWED_TYPES.image.includes(fileType)) contentType = 'image';
    else if (ALLOWED_TYPES.video.includes(fileType)) contentType = 'video';
    else if (ALLOWED_TYPES.audio.includes(fileType)) contentType = 'audio';

    if (!contentType) {
      setError('Invalid file type. Please upload an image, video, or audio file.');
      return;
    }

    // Check file size
    const maxSize = MAX_FILE_SIZE[contentType];
    if (selectedFile.size > maxSize) {
      setError(
        `File too large. Max size for ${contentType} is ${Math.round(
          maxSize / 1024 / 1024
        )}MB`
      );
      return;
    }

    setFile(selectedFile);
    // Auto-fill title from filename
    if (!title) {
      setTitle(selectedFile.name.replace(/\.[^/.]+$/, ''));
    }
  };

  // Handle upload
  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    if (!title.trim()) {
      setError('Please enter a title');
      return;
    }

    const uploadData: ContentUploadData = {
      file,
      title: title.trim(),
      description: description.trim() || undefined,
      duration,
      is_active: isActive,
    };

    try {
      await uploadMutation.mutateAsync({
        data: uploadData,
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
  const getFileIcon = () => {
    if (!file) return <Upload className="w-12 h-12" />;

    if (file.type.startsWith('image/')) return <FileImage className="w-12 h-12" />;
    if (file.type.startsWith('video/')) return <FileVideo className="w-12 h-12" />;
    if (file.type.startsWith('audio/')) return <FileAudio className="w-12 h-12" />;

    return <Upload className="w-12 h-12" />;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Upload Content
          </h2>
          <button
            onClick={handleClose}
            disabled={uploadMutation.isPending}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleUpload} className="space-y-6">
          {/* Supported File Types Info */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-3">
              📎 Supported File Types & Limits
            </h3>
            <div className="grid grid-cols-3 gap-4 text-xs">
              <div>
                <p className="font-medium text-blue-800 dark:text-blue-400 mb-1">
                  Images (Max 50MB)
                </p>
                <p className="text-blue-700 dark:text-blue-300 space-x-1">
                  <span>.jpg</span> <span>.jpeg</span> <span>.png</span> <span>.webp</span>{' '}
                  <span>.gif</span> <span>.bmp</span>
                </p>
              </div>
              <div>
                <p className="font-medium text-blue-800 dark:text-blue-400 mb-1">
                  Videos (Max 500MB)
                </p>
                <p className="text-blue-700 dark:text-blue-300 space-x-1">
                  <span>.mp4</span> <span>.webm</span> <span>.mkv</span> <span>.avi</span>{' '}
                  <span>.mov</span> <span>.m4v</span> <span>.flv</span>
                </p>
              </div>
              <div>
                <p className="font-medium text-blue-800 dark:text-blue-400 mb-1">
                  Audio (Max 100MB)
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
              File *
            </label>
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center ${
                file
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
              }`}
            >
              <input
                type="file"
                accept="image/*,video/*,audio/*"
                onChange={handleFileChange}
                disabled={uploadMutation.isPending}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className={`cursor-pointer ${
                  uploadMutation.isPending ? 'pointer-events-none opacity-50' : ''
                }`}
              >
                <div className="flex flex-col items-center">
                  <div className="text-gray-400 dark:text-gray-500 mb-4">
                    {getFileIcon()}
                  </div>
                  {file ? (
                    <>
                      <p className="text-sm font-medium text-gray-900 dark:text-white mb-1">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </>
                  ) : (
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      Click to upload or drag and drop
                    </p>
                  )}
                </div>
              </label>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={uploadMutation.isPending}
              className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white disabled:opacity-50"
              placeholder="Enter content title"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={uploadMutation.isPending}
              className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white disabled:opacity-50"
              placeholder="Enter content description (optional)"
              rows={3}
            />
          </div>

          {/* Duration */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Display Duration (seconds)
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
              How long this content should display in playlists (1-86400 seconds)
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
              Active (available for playlists)
            </label>
          </div>

          {/* Upload Progress */}
          {uploadMutation.isPending && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Uploading...
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

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-700">
            <button
              type="button"
              onClick={handleClose}
              disabled={uploadMutation.isPending}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!file || !title.trim() || uploadMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {uploadMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Upload
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
