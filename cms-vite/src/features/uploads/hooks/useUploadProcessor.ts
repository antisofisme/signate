/**
 * useUploadProcessor Hook
 *
 * Processes the upload queue - handles actual file uploads
 * with progress tracking, cancellation, and retry logic
 *
 * FIXED 2025-11-29: Race condition that caused duplicate uploads
 */

import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from '@/shared/utils/toast';
import { useUploadQueueStore } from '@/lib/stores/uploadQueueStore';
import { uploadSingleContent, isAbortError, isPermanentError, getErrorMessage } from '../api/uploadApi';
import { contentKeys } from '@/features/contents/hooks/useContent';
import { useSelectedOrgId } from '@/shared/hooks';

/**
 * Delay in milliseconds before retrying a failed upload
 */
const RETRY_DELAY = 2000;

/**
 * Hook to process upload queue
 *
 * Should be mounted once in the app (e.g., in UploadQueuePanel)
 */
export function useUploadProcessor() {
  const queryClient = useQueryClient();
  const orgId = useSelectedOrgId(); // Get current organization for proper cache scoping
  const processingRef = useRef(false);
  const retryTimeoutsRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  // Track items currently being uploaded to prevent duplicate processing
  const uploadingItemsRef = useRef<Set<string>>(new Set());

  const {
    items,
    settings,
    getNextPending,
    getActiveCount,
    setStatus,
    setContentId,
    setAbortController,
    updateProgress,
    incrementRetryCount,
    _hasHydrated,
  } = useUploadQueueStore();

  /**
   * Process a single upload item
   * FIXED: Added uploadingItemsRef check to prevent duplicate processing
   */
  const processItem = useCallback(
    async (itemId: string): Promise<void> => {
      // CRITICAL: Check if already being processed (prevents duplicate uploads)
      if (uploadingItemsRef.current.has(itemId)) {
        console.log(`[UploadProcessor] Item ${itemId} already being processed, skipping`);
        return;
      }

      // Mark as being processed IMMEDIATELY (before any async operation)
      uploadingItemsRef.current.add(itemId);

      const store = useUploadQueueStore.getState();
      const item = store.items.find((i) => i.id === itemId);

      if (!item || !item.file) {
        // No file object - mark as failed (e.g., after page reload)
        uploadingItemsRef.current.delete(itemId);
        setStatus(itemId, 'failed', 'File not available');
        return;
      }

      // Create abort controller
      const controller = new AbortController();
      setAbortController(itemId, controller);

      // Set status to uploading
      setStatus(itemId, 'uploading');

      try {
        // Upload the file
        const result = await uploadSingleContent(
          item.file,
          { duration: item.duration, is_active: item.isActive },
          (progress, uploadedBytes) => {
            updateProgress(itemId, progress, uploadedBytes);
          },
          controller.signal
        );

        // Success! Remove from tracking set
        uploadingItemsRef.current.delete(itemId);
        setStatus(itemId, 'completed');
        // Note: result is already unwrapped by apiClient interceptor
        // So result is { id, title, ... } not { data: { id, ... } }
        setContentId(itemId, result.id);

        // IMMEDIATE CACHE UPDATE: Force refresh content list after upload
        console.log('[UploadProcessor] Upload success! Content ID:', result.id, 'OrgId:', orgId);

        // Find and update all content list queries for this org
        const allQueries = queryClient.getQueryCache().getAll();
        const contentQueries = allQueries.filter(q =>
          q.queryKey[0] === 'content' &&
          q.queryKey[1] === 'list' &&
          q.queryKey[2] === orgId
        );

        console.log('[UploadProcessor] Found content list queries:', contentQueries.length);

        // Step 1: Update each matching query with setQueryData (triggers re-render)
        contentQueries.forEach((query, i) => {
          const queryKey = query.queryKey;
          console.log(`[UploadProcessor] Updating query ${i}:`, JSON.stringify(queryKey));

          queryClient.setQueryData(queryKey, (oldData: any) => {
            if (!oldData) {
              console.log('[UploadProcessor] No oldData for query', i);
              return oldData;
            }

            // Handle { data: [...], pagination: {...} } format
            if (oldData.data && Array.isArray(oldData.data)) {
              console.log('[UploadProcessor] Adding to', oldData.data.length, 'items in query', i);
              const newData = {
                ...oldData,
                data: [result, ...oldData.data],
                pagination: oldData.pagination ? {
                  ...oldData.pagination,
                  total: (oldData.pagination.total || 0) + 1,
                } : undefined,
              };
              console.log('[UploadProcessor] New data length:', newData.data.length);
              return newData;
            }

            return oldData;
          });
        });

        // Step 2: Invalidate duplicates (mark stale, refetch when viewed)
        queryClient.invalidateQueries({
          queryKey: contentKeys.duplicates(orgId),
        });

        // Step 3: Mark content list as stale (will refetch on next focus/interaction)
        // Do NOT immediately refetch - it might return cached HTTP response and overwrite optimistic update
        queryClient.invalidateQueries({
          queryKey: contentKeys.lists(orgId),
          refetchType: 'none',  // Just mark stale, don't refetch
        });

        console.log('[UploadProcessor] Cache updated for org:', orgId, '- New item should be visible now');

        toast.success(`${item.fileName} uploaded successfully`);
      } catch (error) {
        // Remove from tracking set
        uploadingItemsRef.current.delete(itemId);

        // Check if cancelled
        if (isAbortError(error)) {
          setStatus(itemId, 'cancelled');
          return;
        }

        // Get error message
        const errorMessage = getErrorMessage(error);

        // Check if this is a permanent error (4xx) - don't retry these
        if (isPermanentError(error)) {
          // Permanent failure - mark as failed immediately
          setStatus(itemId, 'failed', errorMessage);
          toast.error(`${item.fileName} failed: ${errorMessage}`);
          return;
        }

        // Check if should retry (only for transient errors like network issues, 5xx)
        const currentItem = useUploadQueueStore.getState().items.find((i) => i.id === itemId);
        const currentRetryCount = currentItem?.retryCount || 0;

        if (currentRetryCount < settings.maxRetries) {
          // Increment retry count
          incrementRetryCount(itemId);

          // Set status back to pending for retry
          setStatus(itemId, 'pending', `Retrying... (${currentRetryCount + 1}/${settings.maxRetries})`);

          // Schedule retry
          const timeout = setTimeout(() => {
            retryTimeoutsRef.current.delete(itemId);
          }, RETRY_DELAY);
          retryTimeoutsRef.current.set(itemId, timeout);
        } else {
          // Max retries reached - mark as failed
          setStatus(itemId, 'failed', errorMessage);
          toast.error(`${item.fileName} failed: ${errorMessage}`);
        }
      }
    },
    [queryClient, orgId, settings.maxRetries, setStatus, setContentId, setAbortController, updateProgress, incrementRetryCount]
  );

  /**
   * Process queue - find next pending item and upload
   * FIXED: Skip items already being processed
   */
  const processQueue = useCallback(async () => {
    // Prevent concurrent processing calls
    if (processingRef.current) return;
    processingRef.current = true;

    try {
      // Keep processing while there are pending items and slots available
      while (true) {
        const store = useUploadQueueStore.getState();

        // Check if we have room for more uploads
        // Count items in our local tracking set (more accurate than store status)
        const activeCount = uploadingItemsRef.current.size;
        if (activeCount >= store.settings.maxConcurrent) {
          break;
        }

        // Get next pending item that is NOT already being processed
        const nextItem = store.items.find(
          (i) => i.status === 'pending' && !uploadingItemsRef.current.has(i.id)
        );
        if (!nextItem) {
          break;
        }

        // Process this item (don't await - let it run in background)
        // The processItem function will add to uploadingItemsRef immediately
        processItem(nextItem.id);

        // Small delay to prevent rapid-fire requests
        await new Promise((resolve) => setTimeout(resolve, 100));
      }
    } finally {
      processingRef.current = false;
    }
  }, [processItem]);

  /**
   * Watch for changes in items and trigger processing
   * FIXED: Consolidated into single effect with better checks
   */
  useEffect(() => {
    // Don't process until hydrated
    if (!_hasHydrated) return;

    // Check if there are pending items that are NOT already being processed
    const hasPendingNotProcessing = items.some(
      (i) => i.status === 'pending' && !uploadingItemsRef.current.has(i.id)
    );

    // Only trigger if we have items to process
    if (hasPendingNotProcessing) {
      processQueue();
    }
  }, [items, _hasHydrated, processQueue]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      // Clear retry timeouts
      retryTimeoutsRef.current.forEach((timeout) => clearTimeout(timeout));
      retryTimeoutsRef.current.clear();

      // Clear uploading items tracking
      uploadingItemsRef.current.clear();
    };
  }, []);
}
