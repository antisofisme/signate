/**
 * useTranscodingProgress Hook
 *
 * Listens for WebSocket transcoding progress events and shows toast notifications.
 * Also triggers cache invalidation when transcoding completes.
 */

import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useWebSocketEvents } from '@/lib/websocket';
import { contentKeys } from './useContent';
import { useSelectedOrgId } from '@/shared/hooks';
import type {
  ContentTranscodingProgressData,
  ContentTranscodedData,
  ContentTranscodingFailedData,
  ContentThumbnailReadyData,
} from '@/lib/websocket/types';

/**
 * Hook to listen for transcoding progress events via WebSocket
 *
 * Shows toast notifications for:
 * - Transcoding started
 * - Transcoding progress (major milestones)
 * - Transcoding completed
 * - Transcoding failed
 */
export function useTranscodingProgress() {
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId();

  useWebSocketEvents({
    // Transcoding progress updates
    'content:transcoding_progress': (data: ContentTranscodingProgressData) => {
      // Only show toast for significant progress (avoid spam)
      // Show at start (0%) and every 25%
      if (data.progress === 0) {
        toast.info(`Starting transcoding: ${data.title}`, {
          duration: 3000,
        });
      } else if (data.progress === 50) {
        toast.info(`Transcoding ${data.title}: 50% complete`, {
          duration: 2000,
        });
      }
    },

    // Transcoding completed
    'content:transcoded': (data: ContentTranscodedData) => {
      toast.success(`Transcoding completed: ${data.title}`, {
        description: `${data.variants.length} quality variants ready`,
        duration: 5000,
      });

      // Invalidate content queries to refresh the list
      queryClient.invalidateQueries({
        queryKey: contentKeys.lists(orgId),
        refetchType: 'active',
      });

      // Invalidate specific content detail if cached
      queryClient.invalidateQueries({
        queryKey: contentKeys.detail(data.content_id),
        refetchType: 'active',
      });
    },

    // Transcoding failed
    'content:transcoding_failed': (data: ContentTranscodingFailedData) => {
      toast.error(`Transcoding failed: ${data.title}`, {
        description: data.error,
        duration: 10000,
      });

      // Invalidate to refresh status
      queryClient.invalidateQueries({
        queryKey: contentKeys.lists(orgId),
        refetchType: 'active',
      });
    },

    // Content uploaded (from another admin)
    // NOTE: This event is broadcast to ALL users in the org, including the uploader
    // We don't need to refetch here because:
    // - Our own uploads are handled by useUploadProcessor (optimistic update)
    // - Other users' uploads will be visible on next manual refresh or navigation
    // Using refetchType: 'none' to just mark stale without immediate refetch
    // This prevents overwriting optimistic updates with potentially stale HTTP-cached data
    'content:uploaded': (data: { content_id: number; title: string; uploaded_by?: string }) => {
      // Show notification (could be from another user)
      toast.info(`New content uploaded: ${data.title}`, {
        duration: 3000,
      });

      // Just mark as stale, don't immediately refetch
      // This preserves optimistic updates from useUploadProcessor
      queryClient.invalidateQueries({
        queryKey: contentKeys.lists(orgId),
        refetchType: 'none',  // Don't refetch immediately, just mark stale
      });
    },

    // Thumbnail generated (for videos - async task)
    'content:thumbnail_ready': (data: ContentThumbnailReadyData) => {
      console.log('[Thumbnail] Received thumbnail_ready event:', data);

      // Update the specific content in cache with new thumbnail_url
      queryClient.setQueriesData(
        { queryKey: contentKeys.lists(orgId) },
        (oldData: any) => {
          if (!oldData?.data) return oldData;

          return {
            ...oldData,
            data: oldData.data.map((item: any) =>
              item.id === data.content_id
                ? { ...item, thumbnail_url: data.thumbnail_url }
                : item
            ),
          };
        }
      );

      // Also update detail cache if exists
      queryClient.setQueryData(
        contentKeys.detail(data.content_id),
        (oldData: any) => {
          if (!oldData?.data) return oldData;
          return {
            ...oldData,
            data: { ...oldData.data, thumbnail_url: data.thumbnail_url },
          };
        }
      );
    },
  });
}
