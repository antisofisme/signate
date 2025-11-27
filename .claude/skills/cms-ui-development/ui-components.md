# UI Components Standards

Complete reference for shared UI components in the CMS.

## Component Location

```
cms-vite/src/shared/components/
├── ui/                    # shadcn/ui base components
│   ├── button.tsx
│   ├── input.tsx
│   ├── select.tsx
│   └── ...
├── form/                  # Form wrapper components
│   ├── FormInput.tsx
│   ├── FormSelect.tsx
│   ├── FormTextarea.tsx
│   ├── FormCheckbox.tsx
│   └── FormDatePicker.tsx
├── table/                 # Table components
│   ├── DataTable.tsx
│   ├── TablePagination.tsx
│   ├── TableFilters.tsx
│   └── TableActions.tsx
├── feedback/              # Feedback components
│   ├── PageSkeleton.tsx
│   ├── TableSkeleton.tsx
│   ├── CardSkeleton.tsx
│   └── EmptyState.tsx
├── layout/                # Layout components
│   ├── DashboardLayout.tsx
│   ├── Sidebar.tsx
│   ├── Topbar.tsx
│   └── PageHeader.tsx
├── Modal.tsx              # Shared modal
├── ConfirmDialog.tsx      # Confirmation dialog
├── Pagination.tsx         # Pagination controls
├── AccessDenied.tsx       # Permission denied page
└── ErrorBoundary.tsx      # Error boundary
```

---

## Form Components

### FormInput

```typescript
/**
 * FormInput - Controlled input with label, error, and helper text
 */
import { useFormContext } from 'react-hook-form';
import { Input } from '@/shared/components/ui/input';
import { Label } from '@/shared/components/ui/label';
import { cn } from '@/shared/utils/cn';

interface FormInputProps {
  name: string;
  label: string;
  placeholder?: string;
  type?: 'text' | 'email' | 'password' | 'number';
  disabled?: boolean;
  required?: boolean;
  helperText?: string;
  className?: string;
}

export function FormInput({
  name,
  label,
  placeholder,
  type = 'text',
  disabled = false,
  required = false,
  helperText,
  className,
}: FormInputProps) {
  const {
    register,
    formState: { errors },
  } = useFormContext();

  const error = errors[name];

  return (
    <div className={cn('space-y-2', className)}>
      <Label htmlFor={name} className="flex items-center gap-1">
        {label}
        {required && <span className="text-destructive">*</span>}
      </Label>
      <Input
        id={name}
        type={type}
        placeholder={placeholder}
        disabled={disabled}
        {...register(name)}
        className={cn(error && 'border-destructive')}
      />
      {helperText && !error && (
        <p className="text-sm text-muted-foreground">{helperText}</p>
      )}
      {error && (
        <p className="text-sm text-destructive">{error.message as string}</p>
      )}
    </div>
  );
}
```

### FormSelect

```typescript
/**
 * FormSelect - Controlled select with label and error
 */
import { useFormContext, Controller } from 'react-hook-form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/components/ui/select';
import { Label } from '@/shared/components/ui/label';
import { cn } from '@/shared/utils/cn';

interface Option {
  value: string;
  label: string;
}

interface FormSelectProps {
  name: string;
  label: string;
  options: Option[];
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
}

export function FormSelect({
  name,
  label,
  options,
  placeholder = 'Select...',
  disabled = false,
  required = false,
  className,
}: FormSelectProps) {
  const {
    control,
    formState: { errors },
  } = useFormContext();

  const error = errors[name];

  return (
    <div className={cn('space-y-2', className)}>
      <Label htmlFor={name} className="flex items-center gap-1">
        {label}
        {required && <span className="text-destructive">*</span>}
      </Label>
      <Controller
        name={name}
        control={control}
        render={({ field }) => (
          <Select
            value={field.value}
            onValueChange={field.onChange}
            disabled={disabled}
          >
            <SelectTrigger className={cn(error && 'border-destructive')}>
              <SelectValue placeholder={placeholder} />
            </SelectTrigger>
            <SelectContent>
              {options.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      />
      {error && (
        <p className="text-sm text-destructive">{error.message as string}</p>
      )}
    </div>
  );
}
```

### FormTextarea

```typescript
/**
 * FormTextarea - Controlled textarea with label and error
 */
import { useFormContext } from 'react-hook-form';
import { Textarea } from '@/shared/components/ui/textarea';
import { Label } from '@/shared/components/ui/label';
import { cn } from '@/shared/utils/cn';

interface FormTextareaProps {
  name: string;
  label: string;
  placeholder?: string;
  rows?: number;
  disabled?: boolean;
  required?: boolean;
  maxLength?: number;
  className?: string;
}

export function FormTextarea({
  name,
  label,
  placeholder,
  rows = 4,
  disabled = false,
  required = false,
  maxLength,
  className,
}: FormTextareaProps) {
  const {
    register,
    watch,
    formState: { errors },
  } = useFormContext();

  const error = errors[name];
  const value = watch(name) || '';

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center justify-between">
        <Label htmlFor={name} className="flex items-center gap-1">
          {label}
          {required && <span className="text-destructive">*</span>}
        </Label>
        {maxLength && (
          <span className="text-sm text-muted-foreground">
            {value.length}/{maxLength}
          </span>
        )}
      </div>
      <Textarea
        id={name}
        placeholder={placeholder}
        rows={rows}
        disabled={disabled}
        maxLength={maxLength}
        {...register(name)}
        className={cn(error && 'border-destructive')}
      />
      {error && (
        <p className="text-sm text-destructive">{error.message as string}</p>
      )}
    </div>
  );
}
```

### FormCheckbox

```typescript
/**
 * FormCheckbox - Controlled checkbox with label
 */
import { useFormContext, Controller } from 'react-hook-form';
import { Checkbox } from '@/shared/components/ui/checkbox';
import { Label } from '@/shared/components/ui/label';
import { cn } from '@/shared/utils/cn';

interface FormCheckboxProps {
  name: string;
  label: string;
  description?: string;
  disabled?: boolean;
  className?: string;
}

export function FormCheckbox({
  name,
  label,
  description,
  disabled = false,
  className,
}: FormCheckboxProps) {
  const { control } = useFormContext();

  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => (
        <div className={cn('flex items-start space-x-3', className)}>
          <Checkbox
            id={name}
            checked={field.value}
            onCheckedChange={field.onChange}
            disabled={disabled}
          />
          <div className="space-y-1 leading-none">
            <Label htmlFor={name} className="cursor-pointer">
              {label}
            </Label>
            {description && (
              <p className="text-sm text-muted-foreground">{description}</p>
            )}
          </div>
        </div>
      )}
    />
  );
}
```

### FormSwitch (for is_active toggles)

```typescript
/**
 * FormSwitch - Controlled switch for boolean fields
 */
import { useFormContext, Controller } from 'react-hook-form';
import { Switch } from '@/shared/components/ui/switch';
import { Label } from '@/shared/components/ui/label';
import { cn } from '@/shared/utils/cn';

interface FormSwitchProps {
  name: string;
  label: string;
  description?: string;
  disabled?: boolean;
  className?: string;
}

export function FormSwitch({
  name,
  label,
  description,
  disabled = false,
  className,
}: FormSwitchProps) {
  const { control } = useFormContext();

  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => (
        <div
          className={cn(
            'flex items-center justify-between rounded-lg border p-4',
            className
          )}
        >
          <div className="space-y-0.5">
            <Label htmlFor={name}>{label}</Label>
            {description && (
              <p className="text-sm text-muted-foreground">{description}</p>
            )}
          </div>
          <Switch
            id={name}
            checked={field.value}
            onCheckedChange={field.onChange}
            disabled={disabled}
          />
        </div>
      )}
    />
  );
}
```

---

## Table Components

### DataTable

```typescript
/**
 * DataTable - Reusable data table with TanStack Table
 */
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  ColumnDef,
} from '@tanstack/react-table';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/components/ui/table';

interface DataTableProps<TData> {
  columns: ColumnDef<TData>[];
  data: TData[];
  onRowClick?: (row: TData) => void;
}

export function DataTable<TData>({
  columns,
  data,
  onRowClick,
}: DataTableProps<TData>) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <TableHead key={header.id}>
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows?.length ? (
            table.getRowModel().rows.map((row) => (
              <TableRow
                key={row.id}
                onClick={() => onRowClick?.(row.original)}
                className={onRowClick ? 'cursor-pointer hover:bg-muted/50' : ''}
              >
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center">
                No results.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
```

### TableFilters

```typescript
/**
 * TableFilters - Search and filter bar for tables
 */
import { useState, useEffect } from 'react';
import { Search, X } from 'lucide-react';
import { Input } from '@/shared/components/ui/input';
import { Button } from '@/shared/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/components/ui/select';
import { useDebounce } from '@/shared/hooks/useDebounce';

interface FilterOption {
  value: string;
  label: string;
}

interface TableFiltersProps {
  searchPlaceholder?: string;
  onSearchChange: (value: string) => void;
  filters?: {
    name: string;
    placeholder: string;
    options: FilterOption[];
    value: string;
    onChange: (value: string) => void;
  }[];
  onReset?: () => void;
}

export function TableFilters({
  searchPlaceholder = 'Search...',
  onSearchChange,
  filters = [],
  onReset,
}: TableFiltersProps) {
  const [searchValue, setSearchValue] = useState('');
  const debouncedSearch = useDebounce(searchValue, 300);

  useEffect(() => {
    onSearchChange(debouncedSearch);
  }, [debouncedSearch, onSearchChange]);

  const handleReset = () => {
    setSearchValue('');
    onReset?.();
  };

  return (
    <div className="flex flex-wrap items-center gap-4">
      {/* Search */}
      <div className="relative w-64">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder={searchPlaceholder}
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Filters */}
      {filters.map((filter) => (
        <Select
          key={filter.name}
          value={filter.value}
          onValueChange={filter.onChange}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder={filter.placeholder} />
          </SelectTrigger>
          <SelectContent>
            {filter.options.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      ))}

      {/* Reset */}
      {(searchValue || filters.some((f) => f.value)) && onReset && (
        <Button variant="ghost" size="sm" onClick={handleReset}>
          <X className="mr-2 h-4 w-4" />
          Reset
        </Button>
      )}
    </div>
  );
}
```

### TableActions

```typescript
/**
 * TableActions - Dropdown menu for row actions
 */
import { MoreHorizontal, Edit, Trash2, Eye, Copy } from 'lucide-react';
import { Button } from '@/shared/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/components/ui/dropdown-menu';
import { usePermissions } from '@/features/rbac/hooks/usePermissions';

interface Action {
  label: string;
  icon?: React.ReactNode;
  onClick: () => void;
  permission?: string;
  variant?: 'default' | 'destructive';
  separator?: boolean;
}

interface TableActionsProps {
  actions: Action[];
}

export function TableActions({ actions }: TableActionsProps) {
  const { hasPermission } = usePermissions();

  const visibleActions = actions.filter(
    (action) => !action.permission || hasPermission(action.permission)
  );

  if (visibleActions.length === 0) {
    return null;
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <MoreHorizontal className="h-4 w-4" />
          <span className="sr-only">Actions</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {visibleActions.map((action, index) => (
          <div key={index}>
            {action.separator && index > 0 && <DropdownMenuSeparator />}
            <DropdownMenuItem
              onClick={action.onClick}
              className={action.variant === 'destructive' ? 'text-destructive' : ''}
            >
              {action.icon}
              <span className="ml-2">{action.label}</span>
            </DropdownMenuItem>
          </div>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

// Usage example
const actions = [
  { label: 'View', icon: <Eye className="h-4 w-4" />, onClick: handleView },
  { label: 'Edit', icon: <Edit className="h-4 w-4" />, onClick: handleEdit, permission: 'items.update' },
  { label: 'Duplicate', icon: <Copy className="h-4 w-4" />, onClick: handleDuplicate, permission: 'items.create' },
  { label: 'Delete', icon: <Trash2 className="h-4 w-4" />, onClick: handleDelete, permission: 'items.delete', variant: 'destructive', separator: true },
];
```

---

## Loading States (Skeletons)

### TableSkeleton

```typescript
/**
 * TableSkeleton - Loading state for tables
 */
import { Skeleton } from '@/shared/components/ui/skeleton';

interface TableSkeletonProps {
  rows?: number;
  columns?: number;
}

export function TableSkeleton({ rows = 5, columns = 4 }: TableSkeletonProps) {
  return (
    <div className="rounded-md border">
      {/* Header */}
      <div className="flex gap-4 border-b p-4">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>

      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex gap-4 border-b p-4 last:border-0">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={colIndex} className="h-4 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}
```

### CardSkeleton

```typescript
/**
 * CardSkeleton - Loading state for cards
 */
import { Skeleton } from '@/shared/components/ui/skeleton';

interface CardSkeletonProps {
  count?: number;
  showImage?: boolean;
}

export function CardSkeleton({ count = 3, showImage = false }: CardSkeletonProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-lg border p-4 space-y-4">
          {showImage && <Skeleton className="h-40 w-full rounded-md" />}
          <Skeleton className="h-6 w-3/4" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-1/2" />
          <div className="flex gap-2">
            <Skeleton className="h-8 w-20" />
            <Skeleton className="h-8 w-20" />
          </div>
        </div>
      ))}
    </div>
  );
}
```

### PageSkeleton

```typescript
/**
 * PageSkeleton - Full page loading state
 */
import { Skeleton } from '@/shared/components/ui/skeleton';

export function PageSkeleton() {
  return (
    <div className="container py-6 space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-96" />
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-10 w-32" />
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <div className="flex gap-4 border-b p-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-4 flex-1" />
          ))}
        </div>
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex gap-4 border-b p-4">
            {[1, 2, 3, 4].map((j) => (
              <Skeleton key={j} className="h-4 flex-1" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Empty State

```typescript
/**
 * EmptyState - Display when no data available
 */
import { LucideIcon } from 'lucide-react';
import { cn } from '@/shared/utils/cn';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-lg border border-dashed p-12 text-center',
        className
      )}
    >
      <div className="rounded-full bg-muted p-4">
        <Icon className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="mt-4 text-lg font-semibold">{title}</h3>
      {description && (
        <p className="mt-2 text-sm text-muted-foreground max-w-md">
          {description}
        </p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
```

---

## Modal & Dialogs

### Modal (already exists)

```typescript
// Located at: cms-vite/src/shared/components/Modal.tsx
// Uses createPortal to render in #modal-root

import { Modal } from '@/shared/components/Modal';

<Modal
  open={isOpen}
  onOpenChange={setIsOpen}
  title="Modal Title"
  description="Optional description text"
  size="md" // sm | md | lg | xl | full
>
  <ModalContent />
</Modal>
```

### ConfirmDialog

```typescript
/**
 * ConfirmDialog - Confirmation dialog for dangerous actions
 */
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/components/ui/alert-dialog';
import { Button } from '@/shared/components/ui/button';
import { Loader2 } from 'lucide-react';

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  isLoading?: boolean;
  variant?: 'default' | 'destructive';
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  isLoading = false,
  variant = 'default',
}: ConfirmDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isLoading}>
            {cancelText}
          </AlertDialogCancel>
          <Button
            variant={variant}
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {confirmText}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

---

## Error Boundary

```typescript
/**
 * ErrorBoundary - Catch and display errors gracefully
 */
import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/shared/components/ui/button';

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    // TODO: Log to error tracking service (e.g., Sentry)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
          <div className="rounded-full bg-destructive/10 p-4">
            <AlertTriangle className="h-8 w-8 text-destructive" />
          </div>
          <h2 className="mt-4 text-xl font-semibold">Something went wrong</h2>
          <p className="mt-2 text-sm text-muted-foreground max-w-md">
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <Button onClick={this.handleReset} className="mt-6">
            <RefreshCw className="mr-2 h-4 w-4" />
            Try again
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Usage: Wrap feature components
<ErrorBoundary>
  <FeaturePage />
</ErrorBoundary>
```

---

## Access Denied

```typescript
/**
 * AccessDenied - Display when user lacks permission
 */
import { ShieldX } from 'lucide-react';
import { Button } from '@/shared/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export function AccessDenied() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
      <div className="rounded-full bg-destructive/10 p-4">
        <ShieldX className="h-8 w-8 text-destructive" />
      </div>
      <h2 className="mt-4 text-xl font-semibold">
        {t('common.accessDenied')}
      </h2>
      <p className="mt-2 text-sm text-muted-foreground max-w-md">
        {t('common.accessDeniedDescription')}
      </p>
      <Button onClick={() => navigate(-1)} className="mt-6">
        {t('common.goBack')}
      </Button>
    </div>
  );
}
```

---

## Dark Mode Support

All components should use Tailwind CSS classes that support dark mode:

```typescript
// Good - Uses CSS variables that adapt to theme
<div className="bg-background text-foreground border-border" />

// Good - Uses Tailwind dark: prefix
<div className="bg-white dark:bg-gray-900" />

// Avoid - Hardcoded colors
<div className="bg-white text-black" />
```

### CSS Variables (in tailwind.config.js)
```javascript
theme: {
  extend: {
    colors: {
      background: 'hsl(var(--background))',
      foreground: 'hsl(var(--foreground))',
      primary: {
        DEFAULT: 'hsl(var(--primary))',
        foreground: 'hsl(var(--primary-foreground))',
      },
      // ... more semantic colors
    },
  },
},
```
