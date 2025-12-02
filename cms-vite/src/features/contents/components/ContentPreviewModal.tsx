/**
 * Content Preview Modal
 *
 * Modal for previewing content (image, video, audio) with details panel
 * Uses centralized ModalOverlay for consistent behavior
 */

import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X, Download, Copy, Check } from 'lucide-react';
import { toast } from 'sonner';
import { Button, ModalOverlay } from '@/shared/components';
import type { Content } from '../types/content';

interface ContentPreviewModalProps {
  content: Content;
  isOpen: boolean;
  onClose: () => void;
}

// Helper functions
function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

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

// Get file type label from mime type
const getFileTypeLabel = (mimeType: string) => {
  if (mimeType.includes('jpeg') || mimeType.includes('jpg')) return 'JPEG';
  if (mimeType.includes('png')) return 'PNG';
  if (mimeType.includes('gif')) return 'GIF';
  if (mimeType.includes('webp')) return 'WebP';
  if (mimeType.includes('mp4')) return 'MP4';
  if (mimeType.includes('webm')) return 'WebM';
  if (mimeType.includes('avi')) return 'AVI';
  if (mimeType.includes('mov') || mimeType.includes('quicktime')) return 'MOV';
  if (mimeType.includes('mkv')) return 'MKV';
  if (mimeType.includes('mp3') || mimeType.includes('mpeg')) return 'MP3';
  if (mimeType.includes('wav')) return 'WAV';
  if (mimeType.includes('ogg')) return 'OGG';
  if (mimeType.includes('flac')) return 'FLAC';
  return mimeType.split('/')[1]?.toUpperCase() || 'File';
};

export function ContentPreviewModal({ content, isOpen, onClose }: ContentPreviewModalProps) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Close on ESC key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleEsc);
      return () => window.removeEventListener('keydown', handleEsc);
    }
  }, [isOpen, onClose]);

  const handleCopyUrl = async () => {
    try {
      await navigator.clipboard.writeText(content.file_url || '');
      setCopied(true);
      toast.success('URL copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Failed to copy URL');
    }
  };

  const handleDownload = () => {
    if (!content.file_url) return;
    const link = document.createElement('a');
    link.href = content.file_url;
    link.download = content.original_filename;
    link.click();
    toast.success('Download started');
  };

  const renderPreview = () => {
    switch (content.content_type) {
      case 'image':
        return (
          <div className="bg-gray-100 dark:bg-gray-900 rounded-lg overflow-hidden flex items-center justify-center" style={{ minHeight: '300px' }}>
            <img
              src={content.file_url}
              alt={content.title}
              className="max-w-full max-h-[60vh] object-contain"
            />
          </div>
        );

      case 'video':
        return (
          <div className="bg-gray-100 dark:bg-gray-900 rounded-lg overflow-hidden flex items-center justify-center" style={{ minHeight: '300px' }}>
            <video
              ref={videoRef}
              src={content.hls_master_playlist_url || content.file_url}
              className="max-w-full max-h-[60vh]"
              controls
            >
              {t('contents.messages.videoNotSupported')}
            </video>
          </div>
        );

      case 'audio':
        return (
          <div className="bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg p-8 flex flex-col items-center justify-center" style={{ minHeight: '300px' }}>
            <div className="text-center text-white mb-6">
              <h2 className="text-2xl font-bold mb-2">{content.title}</h2>
              {content.description && (
                <p className="text-gray-100 opacity-90">{content.description}</p>
              )}
            </div>
            <audio
              ref={audioRef}
              src={content.file_url}
              className="w-full max-w-md"
              controls
            >
              {t('contents.messages.audioNotSupported')}
            </audio>
          </div>
        );

      default:
        return (
          <div className="bg-gray-100 dark:bg-gray-900 rounded-lg flex items-center justify-center" style={{ minHeight: '300px' }}>
            <p className="text-gray-500">{t('contents.messages.previewNotAvailable')}</p>
          </div>
        );
    }
  };

  return (
    <ModalOverlay isOpen={isOpen} onClose={onClose} backdropOpacity={75}>
      {/* Modal */}
      <div
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white truncate pr-4">
            {content.title || content.original_filename}
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
            {/* Preview */}
            <div className="md:col-span-2">
              {renderPreview()}
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
                      {content.original_filename}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Type</p>
                    <p className="text-sm text-gray-900 dark:text-white">
                      {getFileTypeLabel(content.mime_type)} ({content.mime_type})
                    </p>
                  </div>
                  {content.resolution && (
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Resolution</p>
                      <p className="text-sm text-gray-900 dark:text-white">
                        {content.resolution}
                      </p>
                    </div>
                  )}
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">File Size</p>
                    <p className="text-sm text-gray-900 dark:text-white">
                      {formatFileSize(content.file_size)}
                    </p>
                  </div>
                  {content.duration > 0 && (
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Duration</p>
                      <p className="text-sm text-gray-900 dark:text-white">
                        {formatDuration(content.duration)}
                      </p>
                    </div>
                  )}
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Uploaded</p>
                    <p className="text-sm text-gray-900 dark:text-white">
                      {formatDate(content.created_at)}
                    </p>
                  </div>
                </div>
              </div>

              {(content.title || content.description) && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Metadata
                  </h3>
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 space-y-3">
                    {content.title && (
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Title</p>
                        <p className="text-sm text-gray-900 dark:text-white">
                          {content.title}
                        </p>
                      </div>
                    )}
                    {content.description && (
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Description</p>
                        <p className="text-sm text-gray-900 dark:text-white">
                          {content.description}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Transcoding Status */}
              {content.transcoding_status && content.transcoding_status !== 'completed' && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                    Processing Status
                  </h3>
                  <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        content.transcoding_status === 'processing'
                          ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                          : content.transcoding_status === 'failed'
                            ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {content.transcoding_status}
                      {content.transcoding_progress > 0 && ` (${content.transcoding_progress}%)`}
                    </span>
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
                    {content.file_url}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ModalOverlay>
  );
}
