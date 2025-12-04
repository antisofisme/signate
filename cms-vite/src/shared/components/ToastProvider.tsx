/**
 * Toast Provider Component
 *
 * Wrapper for Sonner Toaster with:
 * - Dark/Light theme support (synced with app theme)
 * - Dynamic positioning above Upload Queue panel (uses actual measured height)
 * - Uses unified uploadQueueStore for all upload types
 * - Consistent z-index hierarchy
 */

import { Toaster } from 'sonner';
import { useUIStore } from '@/lib/stores/uiStore';
import { useUploadQueueStore } from '@/lib/stores/uploadQueueStore';
import { Z_INDEX } from '@/shared/constants/zIndex';

const BASE_OFFSET = 16; // default offset from edge (bottom-4 = 16px)
const RIGHT_OFFSET = 16; // right offset to align with upload queue (right-4 = 16px)
const PANEL_GAP = 12; // extra gap above upload queue panel to prevent overlap

export function ToastProvider() {
  const theme = useUIStore((state) => state.theme);
  // Use actual measured panel height from unified upload queue store
  const panelHeight = useUploadQueueStore((state) => state.panelHeight);

  // Calculate bottom offset based on upload queue panel height
  // Add extra gap when panel is visible to prevent overlap with header
  const bottomOffset = panelHeight > 0 ? panelHeight + PANEL_GAP : BASE_OFFSET;

  return (
    <Toaster
      position="bottom-right"
      theme={theme}
      richColors
      expand={true}
      visibleToasts={4}
      gap={8}
      toastOptions={{
        style: { zIndex: Z_INDEX.TOAST },
        className: 'sonner-toast',
        duration: 4000,
      }}
      closeButton
      style={{
        // Override default positioning to keep right alignment fixed
        // while only adjusting bottom offset dynamically
        '--offset': `${RIGHT_OFFSET}px`,
        bottom: `${bottomOffset}px`,
        right: `${RIGHT_OFFSET}px`,
      } as React.CSSProperties}
    />
  );
}
