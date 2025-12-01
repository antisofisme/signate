/**
 * Upload Queue Store - Zustand
 *
 * Manages upload queue state:
 * - Queue items with progress tracking
 * - Cancel/retry functionality
 * - Panel minimize state
 * - Settings persistence
 *
 * Persisted to localStorage (settings + completed/failed items only)
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  UploadItem,
  UploadStatus,
  QueueSettings,
  QueueSummary,
  UploadQueueState,
  AddToQueueOptions,
} from '@/features/uploads/types/upload';
import {
  DEFAULT_QUEUE_SETTINGS,
  getContentTypeFromMime,
  generateId,
} from '@/features/uploads/types/upload';

interface UploadQueueStore extends UploadQueueState {
  // Hydration status
  _hasHydrated: boolean;
  setHasHydrated: (state: boolean) => void;

  // Panel height for toast positioning
  panelHeight: number;
  setPanelHeight: (height: number) => void;

  // Queue actions
  addToQueue: (files: File[], options: AddToQueueOptions) => void;
  removeFromQueue: (id: string) => void;
  clearCompleted: () => void;
  clearAll: () => void;

  // Upload control actions
  cancelUpload: (id: string) => void;
  retryUpload: (id: string) => void;
  retryAllFailed: () => void;

  // Progress actions
  updateProgress: (id: string, progress: number, uploadedBytes: number) => void;
  setStatus: (id: string, status: UploadStatus, error?: string) => void;
  setContentId: (id: string, contentId: number) => void;
  setAbortController: (id: string, controller: AbortController) => void;
  incrementRetryCount: (id: string) => void;

  // UI actions
  toggleMinimize: () => void;
  setProcessing: (isProcessing: boolean) => void;

  // Computed getters
  getSummary: () => QueueSummary;
  getNextPending: () => UploadItem | undefined;
  getActiveCount: () => number;
  hasActiveItems: () => boolean;
}

export const useUploadQueueStore = create<UploadQueueStore>()(
  persist(
    (set, get) => ({
      // Initial state
      items: [],
      settings: DEFAULT_QUEUE_SETTINGS,
      isMinimized: false,
      isProcessing: false,
      _hasHydrated: false,
      panelHeight: 0,

      // Set hydration status
      setHasHydrated: (state) => {
        set({ _hasHydrated: state });
      },

      // Set panel height for toast positioning
      setPanelHeight: (height) => {
        set({ panelHeight: height });
      },

      // Add files to queue
      addToQueue: (files, options) => {
        console.log('[UploadQueueStore] addToQueue called with', files.length, 'files');

        const newItems: UploadItem[] = files.map((file) => ({
          id: generateId(),
          file,
          fileName: file.name,
          fileSize: file.size,
          fileType: getContentTypeFromMime(file.type),
          mimeType: file.type,
          duration: options.duration,
          isActive: options.isActive,
          status: 'pending' as UploadStatus,
          progress: 0,
          uploadedBytes: 0,
          createdAt: Date.now(),
          retryCount: 0,
        }));

        console.log('[UploadQueueStore] Created newItems:', newItems.length);

        set((state) => {
          const updatedItems = [...state.items, ...newItems];
          console.log('[UploadQueueStore] Updated items count:', updatedItems.length);
          return {
            items: updatedItems,
            isMinimized: false, // Expand panel when adding items
          };
        });
      },

      // Remove item from queue
      removeFromQueue: (id) => {
        const state = get();
        const item = state.items.find((i) => i.id === id);

        // Cancel if uploading
        if (item?.abortController && item.status === 'uploading') {
          item.abortController.abort();
        }

        set((state) => ({
          items: state.items.filter((i) => i.id !== id),
        }));
      },

      // Clear completed items
      clearCompleted: () => {
        set((state) => ({
          items: state.items.filter(
            (i) => i.status !== 'completed' && i.status !== 'cancelled'
          ),
        }));
      },

      // Clear all items
      clearAll: () => {
        const state = get();

        // Cancel all uploading items
        state.items.forEach((item) => {
          if (item.abortController && item.status === 'uploading') {
            item.abortController.abort();
          }
        });

        set({ items: [], isProcessing: false });
      },

      // Cancel specific upload
      cancelUpload: (id) => {
        const state = get();
        const item = state.items.find((i) => i.id === id);

        if (item?.abortController) {
          item.abortController.abort();
        }

        set((state) => ({
          items: state.items.map((i) =>
            i.id === id ? { ...i, status: 'cancelled' as UploadStatus } : i
          ),
        }));
      },

      // Retry failed upload
      retryUpload: (id) => {
        set((state) => ({
          items: state.items.map((i) =>
            i.id === id
              ? {
                  ...i,
                  status: 'pending' as UploadStatus,
                  progress: 0,
                  uploadedBytes: 0,
                  error: undefined,
                  abortController: undefined,
                }
              : i
          ),
        }));
      },

      // Retry all failed uploads
      retryAllFailed: () => {
        set((state) => ({
          items: state.items.map((i) =>
            i.status === 'failed'
              ? {
                  ...i,
                  status: 'pending' as UploadStatus,
                  progress: 0,
                  uploadedBytes: 0,
                  error: undefined,
                  abortController: undefined,
                }
              : i
          ),
        }));
      },

      // Update progress
      updateProgress: (id, progress, uploadedBytes) => {
        set((state) => ({
          items: state.items.map((i) =>
            i.id === id ? { ...i, progress, uploadedBytes } : i
          ),
        }));
      },

      // Set status
      setStatus: (id, status, error) => {
        set((state) => ({
          items: state.items.map((i) =>
            i.id === id
              ? {
                  ...i,
                  status,
                  error,
                  startedAt: status === 'uploading' ? Date.now() : i.startedAt,
                  completedAt:
                    status === 'completed' || status === 'failed'
                      ? Date.now()
                      : i.completedAt,
                }
              : i
          ),
        }));
      },

      // Set content ID after successful upload
      setContentId: (id, contentId) => {
        set((state) => ({
          items: state.items.map((i) =>
            i.id === id ? { ...i, contentId } : i
          ),
        }));
      },

      // Set abort controller
      setAbortController: (id, controller) => {
        set((state) => ({
          items: state.items.map((i) =>
            i.id === id ? { ...i, abortController: controller } : i
          ),
        }));
      },

      // Increment retry count
      incrementRetryCount: (id) => {
        set((state) => ({
          items: state.items.map((i) =>
            i.id === id ? { ...i, retryCount: i.retryCount + 1 } : i
          ),
        }));
      },

      // Toggle minimize
      toggleMinimize: () => {
        set((state) => ({ isMinimized: !state.isMinimized }));
      },

      // Set processing state
      setProcessing: (isProcessing) => {
        set({ isProcessing });
      },

      // Get queue summary
      getSummary: () => {
        const items = get().items;

        const pending = items.filter((i) => i.status === 'pending').length;
        const uploading = items.filter((i) => i.status === 'uploading').length;
        const completed = items.filter((i) => i.status === 'completed').length;
        const failed = items.filter((i) => i.status === 'failed').length;
        const cancelled = items.filter((i) => i.status === 'cancelled').length;

        const totalBytes = items.reduce((sum, i) => sum + i.fileSize, 0);
        const uploadedBytes = items.reduce((sum, i) => sum + i.uploadedBytes, 0);

        const overallProgress =
          totalBytes > 0 ? Math.round((uploadedBytes / totalBytes) * 100) : 0;

        return {
          total: items.length,
          pending,
          uploading,
          completed,
          failed,
          cancelled,
          overallProgress,
          totalBytes,
          uploadedBytes,
        };
      },

      // Get next pending item
      getNextPending: () => {
        return get().items.find((i) => i.status === 'pending');
      },

      // Get count of active (uploading) items
      getActiveCount: () => {
        return get().items.filter((i) => i.status === 'uploading').length;
      },

      // Check if there are any active items
      hasActiveItems: () => {
        const items = get().items;
        return items.some(
          (i) => i.status === 'pending' || i.status === 'uploading'
        );
      },
    }),
    {
      name: 'upload-queue-storage',
      partialize: (state) => ({
        // Persist settings
        settings: state.settings,
        isMinimized: state.isMinimized,
        // Only persist completed/failed items (without File objects)
        items: state.items
          .filter(
            (i) =>
              i.status === 'completed' ||
              i.status === 'failed' ||
              i.status === 'cancelled'
          )
          .map((item) => ({
            ...item,
            file: undefined, // Cannot serialize File
            abortController: undefined, // Cannot serialize AbortController
          })),
      }),
      onRehydrateStorage: () => (state) => {
        // Mark items that were uploading/pending as failed on reload
        if (state) {
          state.items = state.items.map((item) => {
            if (item.status === 'uploading' || item.status === 'pending') {
              return {
                ...item,
                status: 'failed' as UploadStatus,
                error: 'Upload interrupted by page reload',
              };
            }
            return item;
          });
          state.setHasHydrated(true);
        }
      },
    }
  )
);
