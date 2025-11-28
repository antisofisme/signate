/**
 * Device Preview Page
 *
 * Full-screen preview of content that will play on a device
 * Shows content rotation based on 3-tier priority system
 */

import { useParams, useNavigate } from 'react-router-dom';
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
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';

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

export default function DevicePreviewPage() {
  const { id: deviceId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);

  // Fetch resolved content for device
  const { data, isLoading, error } = useQuery({
    queryKey: ['device-content-resolved', deviceId],
    queryFn: async () => {
      const response = await apiClient.get(`/api/v1/devices/${deviceId}/content/resolved`);
      // Response interceptor unwraps {success, data} to just data
      // But if 'total' exists at any level, it may not unwrap
      const result = response.data?.data ?? response.data;
      return result as ResolvedContent;
    },
    enabled: !!deviceId,
  });

  const content = data?.items || [];
  const currentContent = content[currentIndex];

  // Auto-play simulation
  useEffect(() => {
    if (!isPlaying || !currentContent) return;

    const duration = currentContent.duration * 1000; // Convert to ms
    const interval = 100; // Update every 100ms
    const increment = (interval / duration) * 100;

    const timer = setInterval(() => {
      setProgress((prev) => {
        const next = prev + increment;
        if (next >= 100) {
          // Move to next content
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

  const handleClose = () => {
    navigate(-1);
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
        return 'Direct Assignment (P1)';
      case 'tag':
        return 'Tag-Based (P2)';
      case 'playlist':
        return 'Playlist (P3)';
      default:
        return 'Unknown';
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-white text-lg">Loading device content...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-white text-xl font-semibold mb-2">Failed to Load Content</h2>
          <p className="text-gray-400 mb-6">
            {(error as any)?.message || 'Unable to fetch device content'}
          </p>
          <button
            onClick={handleClose}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!content || content.length === 0) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center max-w-md">
          <Monitor className="w-16 h-16 text-gray-500 mx-auto mb-4" />
          <h2 className="text-white text-xl font-semibold mb-2">No Content Assigned</h2>
          <p className="text-gray-400 mb-6">
            This device has no content assigned yet. Assign content via direct assignment, tags, or playlists.
          </p>
          <button
            onClick={handleClose}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header Controls */}
      <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black/80 to-transparent p-6 z-10">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Monitor className="w-6 h-6" />
              Device Preview
            </h1>
            <p className="text-sm text-gray-400 mt-1">
              Simulating content playback • Device #{deviceId}
            </p>
          </div>
          <button
            onClick={handleClose}
            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Main Content Display */}
      <div className="flex items-center justify-center min-h-screen p-20">
        <div className="w-full max-w-5xl">
          {/* Content Preview */}
          <div className="bg-gray-800 rounded-lg overflow-hidden shadow-2xl">
            {currentContent.type === 'image' ? (
              <img
                src={currentContent.uri}
                alt={currentContent.name}
                className="w-full h-[600px] object-contain bg-black"
              />
            ) : currentContent.type === 'video' ? (
              <div className="relative">
                <video
                  key={currentContent.uri}
                  src={currentContent.uri}
                  className="w-full h-[600px] object-contain bg-black"
                  autoPlay={isPlaying}
                  muted
                  loop={false}
                />
                {!isPlaying && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                    <Play className="w-20 h-20 text-white opacity-80" />
                  </div>
                )}
              </div>
            ) : currentContent.type === 'url' || currentContent.type === 'webpage' ? (
              <iframe
                src={currentContent.uri}
                className="w-full h-[600px] border-0"
                title={currentContent.name}
              />
            ) : (
              <div className="w-full h-[600px] flex items-center justify-center bg-gray-700">
                <div className="text-center">
                  <p className="text-xl text-gray-400 mb-2">{currentContent.type.toUpperCase()}</p>
                  <p className="text-sm text-gray-500">{currentContent.name}</p>
                </div>
              </div>
            )}

            {/* Progress Bar */}
            <div className="h-2 bg-gray-700">
              <div
                className="h-full bg-blue-500 transition-all duration-100"
                style={{ width: `${progress}%` }}
              />
            </div>

            {/* Content Info */}
            <div className="p-4 bg-gray-800">
              <div className="flex items-center justify-between mb-2">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{currentContent.name}</h3>
                  <div className="flex items-center gap-3 mt-1">
                    <span className={`px-2 py-1 rounded text-xs font-medium text-white ${getSourceColor(currentContent.source)}`}>
                      {getSourceLabel(currentContent.source)}
                    </span>
                    <span className="text-sm text-gray-400">
                      Duration: {currentContent.duration}s
                    </span>
                    <span className="text-sm text-gray-400">
                      Priority: {currentContent.priority}
                    </span>
                  </div>
                </div>
                <div className="text-sm text-gray-400">
                  {currentIndex + 1} / {content.length}
                </div>
              </div>
            </div>
          </div>

          {/* Playback Controls */}
          <div className="mt-6 flex items-center justify-center gap-4">
            <button
              onClick={handlePrevious}
              disabled={content.length <= 1}
              className="p-3 rounded-lg bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <SkipBack className="w-6 h-6" />
            </button>

            <button
              onClick={handlePlayPause}
              className="p-4 rounded-lg bg-blue-600 hover:bg-blue-700 transition-colors"
            >
              {isPlaying ? (
                <Pause className="w-8 h-8" />
              ) : (
                <Play className="w-8 h-8" />
              )}
            </button>

            <button
              onClick={handleNext}
              disabled={content.length <= 1}
              className="p-3 rounded-lg bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <SkipForward className="w-6 h-6" />
            </button>
          </div>

          {/* Content Breakdown Info */}
          {data?.breakdown && (
            <div className="mt-6 bg-gray-800 rounded-lg p-4">
              <h4 className="font-semibold mb-3">Content Sources Breakdown:</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-400">{data.breakdown.direct}</div>
                  <div className="text-sm text-gray-400">Direct (P1)</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400">{data.breakdown.tag}</div>
                  <div className="text-sm text-gray-400">Tag-Based (P2)</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400">{data.breakdown.playlist}</div>
                  <div className="text-sm text-gray-400">Playlist (P3)</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
