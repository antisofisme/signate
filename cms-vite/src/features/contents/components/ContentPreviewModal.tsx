/**
 * Content Preview Modal
 *
 * Full-screen modal for previewing content (image, video, audio) before publishing
 * - Image: Full resolution preview with zoom
 * - Video: Embedded player with HLS support
 * - Audio: Audio player with waveform
 */

import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X, ZoomIn, ZoomOut, Download, Play, Pause, Volume2, VolumeX } from 'lucide-react';
import type { Content } from '../types/content';

interface ContentPreviewModalProps {
  content: Content;
  isOpen: boolean;
  onClose: () => void;
}

export function ContentPreviewModal({ content, isOpen, onClose }: ContentPreviewModalProps) {
  const { t } = useTranslation();
  const [zoom, setZoom] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
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

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setZoom(1);
      setIsPlaying(false);
      setIsMuted(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleDownload = () => {
    window.open(content.file_url, '_blank');
  };

  const togglePlay = () => {
    const media = content.content_type === 'video' ? videoRef.current : audioRef.current;
    if (!media) return;

    if (isPlaying) {
      media.pause();
    } else {
      media.play();
    }
    setIsPlaying(!isPlaying);
  };

  const toggleMute = () => {
    const media = content.content_type === 'video' ? videoRef.current : audioRef.current;
    if (!media) return;
    media.muted = !media.muted;
    setIsMuted(!isMuted);
  };

  const renderPreview = () => {
    switch (content.content_type) {
      case 'image':
        return (
          <div className="flex flex-col items-center justify-center h-full gap-4">
            <div className="relative flex items-center justify-center">
              <img
                src={content.file_url}
                alt={content.title}
                className="max-w-[85vw] max-h-[calc(100vh-250px)] w-auto h-auto object-contain rounded-lg shadow-2xl"
                style={{ transform: `scale(${zoom})`, transition: 'transform 0.2s' }}
                loading="lazy"
              />
            </div>

            {/* Zoom Controls */}
            <div className="flex items-center gap-2 bg-gray-900/80 px-4 py-2 rounded-lg">
              <button
                type="button"
                onClick={() => setZoom(Math.max(0.5, zoom - 0.25))}
                disabled={zoom <= 0.5}
                className="p-2 text-white hover:bg-gray-700 rounded disabled:opacity-50"
                title={t('contents.preview.zoomOut')}
              >
                <ZoomOut className="w-5 h-5" />
              </button>
              <span className="text-white text-sm min-w-[60px] text-center">
                {Math.round(zoom * 100)}%
              </span>
              <button
                type="button"
                onClick={() => setZoom(Math.min(3, zoom + 0.25))}
                disabled={zoom >= 3}
                className="p-2 text-white hover:bg-gray-700 rounded disabled:opacity-50"
                title={t('contents.preview.zoomIn')}
              >
                <ZoomIn className="w-5 h-5" />
              </button>
            </div>
          </div>
        );

      case 'video':
        return (
          <div className="flex flex-col items-center justify-center h-full gap-4">
            <div className="relative flex items-center justify-center">
              <video
                ref={videoRef}
                src={content.hls_master_playlist_url || content.file_url}
                className="max-w-[85vw] max-h-[calc(100vh-250px)] w-auto h-auto rounded-lg shadow-2xl"
                controls
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
                onVolumeChange={(e) => setIsMuted(e.currentTarget.muted)}
              >
                {t('contents.messages.videoNotSupported')}
              </video>
            </div>

            {/* Video Info */}
            <div className="text-white text-sm bg-gray-900/80 px-4 py-2 rounded-lg">
              {content.resolution && <span>{t('contents.preview.resolution', { resolution: content.resolution })}</span>}
              <span className="ml-4">{t('contents.preview.duration', { duration: formatDuration(content.duration) })}</span>
              {content.hls_master_playlist_url && (
                <span className="ml-4 text-green-400">{t('contents.preview.hlsStreaming')}</span>
              )}
            </div>
          </div>
        );

      case 'audio':
        return (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg p-12 shadow-2xl max-w-2xl w-full">
              <div className="text-center text-white mb-8">
                <h2 className="text-3xl font-bold mb-2">{content.title}</h2>
                {content.description && (
                  <p className="text-gray-100 opacity-90">{content.description}</p>
                )}
              </div>

              <audio
                ref={audioRef}
                src={content.file_url}
                className="w-full"
                controls
                controlsList="nodownload"
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
                onVolumeChange={(e) => setIsMuted(e.currentTarget.muted)}
              >
                {t('contents.messages.audioNotSupported')}
              </audio>

              <div className="mt-6 text-center text-white text-sm">
                <p>{t('contents.preview.duration', { duration: formatDuration(content.duration) })}</p>
                <p className="text-gray-100 opacity-75 mt-1">{content.mime_type}</p>
              </div>
            </div>
          </div>
        );

      default:
        return (
          <div className="flex items-center justify-center h-full text-white">
            <p>{t('contents.messages.previewNotAvailable')}</p>
          </div>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/95 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-gray-900/80 backdrop-blur-sm">
        <div className="flex-1">
          <h2 className="text-xl font-semibold text-white">{content.title}</h2>
          <p className="text-sm text-gray-300 mt-1">
            {content.content_type.toUpperCase()} • {formatFileSize(content.file_size)}
            {content.resolution && ` • ${content.resolution}`}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleDownload}
            className="p-2 text-white hover:bg-gray-700 rounded-lg transition-colors"
            title={t('contents.preview.download')}
          >
            <Download className="w-5 h-5" />
          </button>

          <button
            type="button"
            onClick={onClose}
            className="p-2 text-white hover:bg-gray-700 rounded-lg transition-colors"
            title={t('contents.preview.closeEsc')}
          >
            <X className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Preview Content */}
      <div className="flex-1 overflow-hidden p-4">{renderPreview()}</div>

      {/* Footer Info */}
      <div className="p-4 bg-gray-900/80 backdrop-blur-sm text-sm text-gray-300">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-6">
            <span>{t('contents.preview.original', { filename: content.original_filename })}</span>
            <span>{t('contents.preview.uploaded', { date: new Date(content.created_at).toLocaleDateString() })}</span>
            {content.transcoding_status !== 'completed' && (
              <span
                className={`px-2 py-1 rounded text-xs ${
                  content.transcoding_status === 'processing'
                    ? 'bg-yellow-500/20 text-yellow-300'
                    : content.transcoding_status === 'failed'
                      ? 'bg-red-500/20 text-red-300'
                      : 'bg-gray-500/20 text-gray-300'
                }`}
              >
                {t('contents.preview.transcoding', {
                  status: `${content.transcoding_status}${content.transcoding_progress > 0 ? ` (${content.transcoding_progress}%)` : ''}`
                })}
              </span>
            )}
          </div>

          <div className="text-gray-400">
            {t('contents.preview.pressEscToClose')}
          </div>
        </div>
      </div>
    </div>
  );
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
