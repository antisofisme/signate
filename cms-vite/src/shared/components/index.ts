/**
 * Shared Components Export
 */

// Layout & Navigation
export { ThemeSwitcher } from './ThemeSwitcher';
export { LanguageSwitcher } from './LanguageSwitcher';
export { default as PageHeader } from './layout/PageHeader';
export { StatsCard } from './StatsCard';

// Page Layout Components (Standardized Toolbar)
export { PageToolbar } from './layout/PageToolbar';
export { PageStats } from './layout/PageStats';
export { ViewTabs } from './layout/ViewTabs';
export { FilterButtonGroup } from './layout/FilterButtonGroup';

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
export { ColorPicker } from './ColorPicker';

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

// Data Display
export { DataTable, TABLE_STYLES, ACTION_BUTTON } from './DataTable';
export type { Column, DataTableProps, SortConfig, SortDirection } from './DataTable';

// Sortable Table Header (for tables using TABLE_STYLES with server-side sorting)
export { SortableTableHeader } from './SortableTableHeader';
export type { SortableTableHeaderProps } from './SortableTableHeader';

// Status Badge (for processing/upload status indicators)
export { default as StatusBadge, StatusBadgeSolid } from './StatusBadge';
export type { StatusBadgeProps, BadgeStatus, BadgeSize } from './StatusBadge';

// Toast Provider (Sonner with theme sync & dynamic positioning)
export { ToastProvider } from './ToastProvider';

// Date Display Components (relative time with tooltips)
export { DateCell, OnlineStatusCell } from './DateCell';
export type { default as DateCellDefault } from './DateCell';
