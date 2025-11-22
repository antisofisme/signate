/**
 * Device Preview Modal
 *
 * Full-screen modal preview of content that will play on a device
 * Shows content rotation based on 3-tier priority system
 * Uses centralized ModalOverlay for custom styling
 */

import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import {
  X,
  Play,
  Pause,
  SkipForward,
  SkipBack,
  Monitor,
  Loader2,
  AlertCircle,
  Maximize2,
  Minimize2,
} from 'lucide-react';
import { ModalOverlay } from '@/shared/components';
import { apiClient } from '@/lib/api/client';
import type { Device } from '../../types/device';

interface ContentItem {
  id: number;
  name: string;
  type: string;
  uri: string;
  duration: number;
  priority: number;
  source: 'direct' | 'tag' | 'playlist';
}

interface ResolvedContent {
  device_id: number;
  total: number;
  items: ContentItem[];
  breakdown: {
    direct: number;
    tag: number;
    playlist: number;
  };
}

interface DevicePreviewModalProps {
  isOpen: boolean;
  device: Device | null;
  onClose: () => void;
}

export function DevicePreviewModal({ isOpen, device, onClose }: DevicePreviewModalProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Fetch resolved content for device
  const { data, isLoading, error } = useQuery({
    queryKey: ['device-content-resolved', device?.id],
    queryFn: async () => {
      const response = await apiClient.get(`/api/v1/devices/${device?.id}/content/resolved`);
      const result = response.data?.data ?? response.data;
      return result as ResolvedContent;
    },
    enabled: isOpen && !!device?.id,
  });

  const content = data?.items || [];
  const currentContent = content[currentIndex];

  // Reset state when modal opens/closes or device changes
  useEffect(() => {
    if (isOpen) {
      setCurrentIndex(0);
      setProgress(0);
      setIsPlaying(false);
      setIsFullscreen(false);
    }
  }, [isOpen, device?.id]);

  // Auto-play simulation
  useEffect(() => {
    if (!isPlaying || !currentContent) return;

    const duration = currentContent.duration * 1000;
    const interval = 100;
    const increment = (interval / duration) * 100;

    const timer = setInterval(() => {
      setProgress((prev) => {
        const next = prev + increment;
        if (next >= 100) {
          handleNext();
          return 0;
        }
        return next;
      });
    }, interval);

    return () => clearInterval(timer);
  }, [isPlaying, currentIndex, currentContent]);

  const handleNext = () => {
    setProgress(0);
    setCurrentIndex((prev) => (prev + 1) % content.length);
  };

  const handlePrevious = () => {
    setProgress(0);
    setCurrentIndex((prev) => (prev - 1 + content.length) % content.length);
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'direct':
        return 'bg-purple-500';
      case 'tag':
        return 'bg-blue-500';
      case 'playlist':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getSourceLabel = (source: string) => {
    switch (source) {
      case 'direct':
        return 'Direct (P1)';
      case 'tag':
        return 'Tag (P2)';
      case 'playlist':
        return 'Playlist (P3)';
      default:
        return 'Unknown';
    }
  };

  if (!device) return null;

  return (
    <ModalOverlay isOpen={isOpen} onClose={onClose} backdropOpacity={50}>
      <div
        className={`bg-gray-900 rounded-lg overflow-hidden flex flex-col transition-all duration-300 ${
          isFullscreen
            ? 'w-full h-full max-w-none max-h-none rounded-none'
            : 'w-full max-w-5xl max-h-[90vh]'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`flex items-center justify-between border-b border-gray-700 ${isFullscreen ? 'p-2' : 'p-4'}`}>
          <div>
            <h2 className={`font-semibold text-white flex items-center gap-2 ${isFullscreen ? 'text-sm' : 'text-lg'}`}>
              <Monitor className={isFullscreen ? 'w-4 h-4' : 'w-5 h-5'} />
              Preview: {device.device_name}
            </h2>
            {!isFullscreen && <p className="text-sm text-gray-400">Device #{device.id}</p>}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleFullscreen}
              className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition-colors"
              title={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
            >
              {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto p-4">
          {isLoading ? (
            <div className="flex items-center justify-center h-80">
              <div className="text-center">
                <Loader2 className="w-10 h-10 text-blue-500 animate-spin mx-auto mb-3" />
                <p className="text-white">Loading content...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-80">
              <div className="text-center">
                <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
                <h3 className="text-white text-lg font-semibold mb-2">Failed to Load</h3>
                <p className="text-gray-400">{(error as Error)?.message || 'Unknown error'}</p>
              </div>
            </div>
          ) : !content.length ? (
            <div className="flex items-center justify-center h-80">
              <div className="text-center">
                <Monitor className="w-12 h-12 text-gray-500 mx-auto mb-3" />
                <h3 className="text-white text-lg font-semibold mb-2">No Content Assigned</h3>
                <p className="text-gray-400">Assign content via direct assignment, tags, or playlists.</p>
              </div>
            </div>
          ) : (
            <>
              {/* Content Preview */}
              <div className={`bg-black overflow-hidden ${isFullscreen ? '' : 'rounded-lg'}`}>
                {currentContent.type === 'image' ? (
                  <img
                    src={currentContent.uri}
                    alt={currentContent.name}
                    className={`w-full object-contain ${isFullscreen ? 'h-[calc(100vh-180px)]' : 'h-80'}`}
                  />
                ) : currentContent.type === 'video' ? (
                  <div className="relative">
                    <video
                      key={currentContent.uri}
                      src={currentContent.uri}
                      className={`w-full object-contain ${isFullscreen ? 'h-[calc(100vh-180px)]' : 'h-80'}`}
                      autoPlay={isPlaying}
                      muted
                      loop={false}
                    />
                    {!isPlaying && (
                      <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                        <Play className="w-16 h-16 text-white opacity-80" />
                      </div>
                    )}
                  </div>
                ) : currentContent.type === 'url' || currentContent.type === 'webpage' ? (
                  <iframe
                    src={currentContent.uri}
                    className={`w-full border-0 ${isFullscreen ? 'h-[calc(100vh-180px)]' : 'h-80'}`}
                    title={currentContent.name}
                  />
                ) : (
                  <div className={`w-full flex items-center justify-center bg-gray-800 ${isFullscreen ? 'h-[calc(100vh-180px)]' : 'h-80'}`}>
                    <div className="text-center">
                      <p className="text-xl text-gray-400 mb-2">{currentContent.type.toUpperCase()}</p>
                      <p className="text-sm text-gray-500">{currentContent.name}</p>
                    </div>
                  </div>
                )}

                {/* Progress Bar */}
                <div className="h-1 bg-gray-700">
                  <div
                    className="h-full bg-blue-500 transition-all duration-100"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              {/* Content Info */}
              <div className="mt-4 p-3 bg-gray-800 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h4 className="font-semibold text-white">{currentContent.name}</h4>
                    <div className="flex items-center gap-3 mt-1">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium text-white ${getSourceColor(currentContent.source)}`}>
                        {getSourceLabel(currentContent.source)}
                      </span>
                      <span className="text-sm text-gray-400">{currentContent.duration}s</span>
                    </div>
                  </div>
                  <span className="text-sm text-gray-400">
                    {currentIndex + 1} / {content.length}
                  </span>
                </div>
              </div>

              {/* Playback Controls */}
              <div className="mt-4 flex items-center justify-center gap-3">
                <button
                  onClick={handlePrevious}
                  disabled={content.length <= 1}
                  className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white transition-colors"
                >
                  <SkipBack className="w-5 h-5" />
                </button>
                <button
                  onClick={handlePlayPause}
                  className="p-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors"
                >
                  {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6" />}
                </button>
                <button
                  onClick={handleNext}
                  disabled={content.length <= 1}
                  className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white transition-colors"
                >
                  <SkipForward className="w-5 h-5" />
                </button>
              </div>

              {/* Content Breakdown - hide in fullscreen */}
              {data?.breakdown && !isFullscreen && (
                <div className="mt-4 grid grid-cols-3 gap-3">
                  <div className="text-center p-2 bg-gray-800 rounded-lg">
                    <div className="text-xl font-bold text-purple-400">{data.breakdown.direct}</div>
                    <div className="text-xs text-gray-400">Direct (P1)</div>
                  </div>
                  <div className="text-center p-2 bg-gray-800 rounded-lg">
                    <div className="text-xl font-bold text-blue-400">{data.breakdown.tag}</div>
                    <div className="text-xs text-gray-400">Tag (P2)</div>
                  </div>
                  <div className="text-center p-2 bg-gray-800 rounded-lg">
                    <div className="text-xl font-bold text-green-400">{data.breakdown.playlist}</div>
                    <div className="text-xs text-gray-400">Playlist (P3)</div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </ModalOverlay>
  );
}
