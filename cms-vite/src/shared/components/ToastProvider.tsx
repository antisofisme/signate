/**
 * Toast Provider Component
 *
 * Wrapper for Sonner Toaster with:
 * - Dark/Light theme support (synced with app theme)
 * - Dynamic positioning above Upload Queue panel
 * - Consistent z-index hierarchy
 */

import { Toaster } from 'sonner';
import { useUIStore } from '@/lib/stores/uiStore';
import { useUploadQueueStore } from '@/lib/stores/uploadQueueStore';
import { Z_INDEX } from '@/shared/constants/zIndex';

// Upload queue panel dimensions
const UPLOAD_QUEUE_MINIMIZED_HEIGHT = 56 + 24; // w-14 h-14 button + bottom-6 padding
const UPLOAD_QUEUE_EXPANDED_HEIGHT = 350 + 24; // approximate expanded height + padding
const BASE_OFFSET = 24; // default offset from edge

export function ToastProvider() {
  const theme = useUIStore((state) => state.theme);
  const uploadItems = useUploadQueueStore((state) => state.items);
  const isMinimized = useUploadQueueStore((state) => state.isMinimized);

  // Calculate bottom offset based on upload queue visibility
  const hasUploadItems = uploadItems.length > 0;
  let bottomOffset = BASE_OFFSET;

  if (hasUploadItems) {
    if (isMinimized) {
      bottomOffset = UPLOAD_QUEUE_MINIMIZED_HEIGHT;
    } else {
      bottomOffset = UPLOAD_QUEUE_EXPANDED_HEIGHT;
    }
  }

  return (
    <Toaster
      position="bottom-right"
      theme={theme}
      richColors
      expand={false}
      visibleToasts={4}
      offset={bottomOffset}
      gap={8}
      toastOptions={{
        style: { zIndex: Z_INDEX.TOAST },
        className: 'sonner-toast',
        duration: 4000,
      }}
      closeButton
    />
  );
}
