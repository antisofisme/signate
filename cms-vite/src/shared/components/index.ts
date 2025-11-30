/**
 * Shared Components Export
 */

// Layout & Navigation
export { ThemeSwitcher } from './ThemeSwitcher';
export { LanguageSwitcher } from './LanguageSwitcher';
export { default as PageHeader } from './layout/PageHeader';
export { StatsCard } from './StatsCard';

// Pagination & Navigation
export { Pagination, PaginationCompact } from './Pagination';
export type { PaginationProps } from './Pagination';
export { Tabs, TabPanel } from './Tabs';
export type { Tab } from './Tabs';

// Modal & Dialog
export { Modal, ModalOverlay } from './Modal';
export type { ModalProps, ModalOverlayProps, MaxWidthKey } from './Modal';
export { DeleteConfirmModal } from './DeleteConfirmModal';

// Common UI
export { default as Button } from './common/Button';
export { default as RefreshButton } from './common/RefreshButton';
export { OptimizedImage, Thumbnail, Avatar } from './OptimizedImage';
export type { OptimizedImageProps, ThumbnailProps, AvatarProps } from './OptimizedImage';

// Error Handling
export { ErrorBoundary, PageErrorBoundary, ComponentErrorBoundary } from './ErrorBoundary';

// Form Components (React Hook Form integrated)
export {
  FormInput,
  FormSelect,
  FormTextarea,
  FormSwitch,
  FormCheckbox,
} from './form';
export type { SelectOption } from './form';

// Feedback Components (Loading, Empty, Error states)
export {
  ConfirmDialog,
  EmptyState,
  TableSkeleton,
  PageSkeleton,
  CardSkeleton,
  CardGridSkeleton,
  ErrorDisplay,
  InlineError,
  AccessDenied,
} from './feedback';

// Toast Provider (Sonner with theme sync & dynamic positioning)
export { ToastProvider } from './ToastProvider';
