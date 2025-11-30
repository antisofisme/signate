/**
 * Menu Media Preview Modal Component
 */

import { X, Download, Copy, Check } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';
import { Button } from '@/shared/components';
import type { MenuMedia } from '../types/menu';

interface MenuMediaPreviewModalProps {
  isOpen: boolean;
  media: MenuMedia;
  onClose: () => void;
}

// Format file size
const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// Format date
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('id-ID', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export function MenuMediaPreviewModal({ isOpen, media, onClose }: MenuMediaPreviewModalProps) {
  const [copied, setCopied] = useState(false);

  const handleCopyUrl = async () => {
    try {
      await navigator.clipboard.writeText(media.url || '');
      setCopied(true);
      toast.success('URL copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Failed to copy URL');
    }
  };

  const handleDownload = () => {
    if (!media.url) return;
    const link = document.createElement('a');
    link.href = media.url;
    link.download = media.original_filename;
    link.click();
    toast.success('Download started');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-75"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white truncate pr-4">
            {media.title || media.original_filename}
          </h2>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={handleCopyUrl}
              leftIcon={copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
            >
              {copied ? 'Copied!' : 'Copy URL'}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleDownload}
              leftIcon={<Download className="w-4 h-4" />}
            >
              Download
            </Button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500 ml-2"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Image Preview */}
            <div className="md:col-span-2">
              <div className="bg-gray-100 dark:bg-gray-900 rounded-lg overflow-hidden flex items-center justify-center" style={{ minHeight: '300px' }}>
                <img
                  src={media.url}
                  alt={media.alt_text || media.original_filename}
                  className="max-w-full max-h-[60vh] object-contain"
                />
              </div>
            </div>

            {/* Details */}
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  File Information
                </h3>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 space-y-3">
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Filename</p>
                    <p className="text-sm text-gray-900 dark:text-white break-all">
                      {media.original_filename}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Type</p>
                    <p className="text-sm text-gray-900 dark:text-white">
                      {media.mime_type}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Dimensions</p>
                    <p className="text-sm text-gray-900 dark:text-white">
                      {media.width} x {media.height} px
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">File Size</p>
                    <p className="text-sm text-gray-900 dark:text-white">
                      {formatFileSize(media.file_size)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Uploaded</p>
                    <p className="text-sm text-gray-900 dark:text-white">
                      {formatDate(media.created_at)}
                    </p>
                  </div>
                </div>
              </div>

              {(media.title || media.alt_text) && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Metadata
                  </h3>
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 space-y-3">
                    {media.title && (
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Title</p>
                        <p className="text-sm text-gray-900 dark:text-white">
                          {media.title}
                        </p>
                      </div>
                    )}
                    {media.alt_text && (
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Alt Text</p>
                        <p className="text-sm text-gray-900 dark:text-white">
                          {media.alt_text}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* URL */}
              <div>
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  Direct URL
                </h3>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                  <p className="text-xs text-gray-600 dark:text-gray-400 break-all font-mono">
                    {media.url}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
