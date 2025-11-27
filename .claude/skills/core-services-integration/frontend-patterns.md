# Frontend Integration Patterns

Complete templates and patterns for integrating core services in CMS frontend features.

## Directory Structure Template

```
cms-vite/src/features/[feature]/
├── index.ts                    # Public exports
├── api/
│   └── [feature].api.ts       # API calls
├── components/
│   ├── [Feature]List.tsx      # List component
│   ├── [Feature]Form.tsx      # Create/Edit form
│   ├── [Feature]Card.tsx      # Card component
│   └── [Feature]Table.tsx     # Table component
├── hooks/
│   ├── use[Features].ts       # Data fetching hook
│   └── use[Feature]Mutations.ts # Mutation hooks
├── types/
│   └── [feature].types.ts     # TypeScript types
└── pages/
    └── [Features]Page.tsx     # Page component (optional)
```

## Types Template (types/[feature].types.ts)

```typescript
/**
 * [Feature] Types
 * TypeScript interfaces matching backend DTOs
 */

// =============================================================================
// ENTITY TYPES
// =============================================================================

export interface [Feature] {
  id: number;
  organization_id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
  created_by_id: number | null;
  updated_by_id: number | null;
}

// =============================================================================
// REQUEST TYPES
// =============================================================================

export interface Create[Feature]Request {
  name: string;
  description?: string;
  is_active?: boolean;
}

export interface Update[Feature]Request {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface [Feature]QueryParams {
  page?: number;
  limit?: number;
  search?: string;
  is_active?: boolean;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// =============================================================================
// RESPONSE TYPES
// =============================================================================

export interface [Feature]ListResponse {
  items: [Feature][];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface [Feature]BulkResponse {
  success_count: number;
  failed_count: number;
  errors: Array<{ id: number; error: string }>;
}

// =============================================================================
// FORM TYPES
// =============================================================================

export interface [Feature]FormData {
  name: string;
  description: string;
  is_active: boolean;
}

// Default values for forms
export const DEFAULT_[FEATURE]_FORM: [Feature]FormData = {
  name: '',
  description: '',
  is_active: true,
};
```

## API Template (api/[feature].api.ts)

```typescript
/**
 * [Feature] API
 * All API calls for [feature] management
 */
import { apiClient } from '@/shared/api/client';
import type {
  [Feature],
  [Feature]ListResponse,
  Create[Feature]Request,
  Update[Feature]Request,
  [Feature]QueryParams,
  [Feature]BulkResponse,
} from '../types/[feature].types';

const BASE_URL = '/[features]';

export const [feature]Api = {
  /**
   * Get paginated list of [features]
   */
  getList: async (params?: [Feature]QueryParams): Promise<[Feature]ListResponse> => {
    const response = await apiClient.get<[Feature]ListResponse>(BASE_URL, { params });
    return response.data;
  },

  /**
   * Get single [feature] by ID
   */
  getById: async (id: number): Promise<[Feature]> => {
    const response = await apiClient.get<[Feature]>(`${BASE_URL}/${id}`);
    return response.data;
  },

  /**
   * Create new [feature]
   */
  create: async (data: Create[Feature]Request): Promise<[Feature]> => {
    const response = await apiClient.post<[Feature]>(BASE_URL, data);
    return response.data;
  },

  /**
   * Update existing [feature]
   */
  update: async (id: number, data: Update[Feature]Request): Promise<[Feature]> => {
    const response = await apiClient.put<[Feature]>(`${BASE_URL}/${id}`, data);
    return response.data;
  },

  /**
   * Delete [feature]
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/${id}`);
  },

  /**
   * Bulk delete [features]
   */
  bulkDelete: async (ids: number[]): Promise<[Feature]BulkResponse> => {
    const response = await apiClient.post<[Feature]BulkResponse>(
      `${BASE_URL}/bulk/delete`,
      ids
    );
    return response.data;
  },
};
```

## Hooks Template (hooks/use[Features].ts)

```typescript
/**
 * [Feature] Hooks
 * Data fetching and state management for [features]
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/shared/hooks/useAuth';
import { [feature]Api } from '../api/[feature].api';
import type {
  [Feature],
  [Feature]QueryParams,
  Create[Feature]Request,
  Update[Feature]Request,
} from '../types/[feature].types';
import { toast } from 'sonner';

// Query keys factory
export const [feature]Keys = {
  all: ['[features]'] as const,
  lists: () => [...[feature]Keys.all, 'list'] as const,
  list: (params: [Feature]QueryParams) => [...[feature]Keys.lists(), params] as const,
  details: () => [...[feature]Keys.all, 'detail'] as const,
  detail: (id: number) => [...[feature]Keys.details(), id] as const,
};

/**
 * Hook for fetching [features] list
 */
export function use[Features](params?: [Feature]QueryParams) {
  const { user } = useAuth();
  const orgId = user?.organization_id;

  return useQuery({
    queryKey: [feature]Keys.list({ ...params, orgId }),
    queryFn: () => [feature]Api.getList(params),
    enabled: !!orgId,
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Hook for fetching single [feature]
 */
export function use[Feature](id: number | undefined) {
  const { user } = useAuth();
  const orgId = user?.organization_id;

  return useQuery({
    queryKey: [feature]Keys.detail(id!),
    queryFn: () => [feature]Api.getById(id!),
    enabled: !!id && !!orgId,
  });
}

/**
 * Hook for [feature] mutations (create, update, delete)
 */
export function use[Feature]Mutations() {
  const queryClient = useQueryClient();

  // Invalidate all [feature] queries
  const invalidate[Features] = () => {
    queryClient.invalidateQueries({ queryKey: [feature]Keys.all });
  };

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: Create[Feature]Request) => [feature]Api.create(data),
    onSuccess: (created) => {
      invalidate[Features]();
      toast.success(`[Feature] "${created.name}" created successfully`);
    },
    onError: (error: any) => {
      const message = error.response?.data?.message || 'Failed to create [feature]';
      toast.error(message);
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Update[Feature]Request }) =>
      [feature]Api.update(id, data),
    onSuccess: (updated) => {
      invalidate[Features]();
      toast.success(`[Feature] "${updated.name}" updated successfully`);
    },
    onError: (error: any) => {
      const message = error.response?.data?.message || 'Failed to update [feature]';
      toast.error(message);
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => [feature]Api.delete(id),
    onSuccess: () => {
      invalidate[Features]();
      toast.success('[Feature] deleted successfully');
    },
    onError: (error: any) => {
      const message = error.response?.data?.message || 'Failed to delete [feature]';
      toast.error(message);
    },
  });

  // Bulk delete mutation
  const bulkDeleteMutation = useMutation({
    mutationFn: (ids: number[]) => [feature]Api.bulkDelete(ids),
    onSuccess: (result) => {
      invalidate[Features]();
      toast.success(`${result.success_count} [features] deleted`);
      if (result.failed_count > 0) {
        toast.warning(`${result.failed_count} [features] failed to delete`);
      }
    },
    onError: (error: any) => {
      const message = error.response?.data?.message || 'Failed to delete [features]';
      toast.error(message);
    },
  });

  return {
    create: createMutation.mutate,
    update: updateMutation.mutate,
    delete: deleteMutation.mutate,
    bulkDelete: bulkDeleteMutation.mutate,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
```

## Form Component Template (components/[Feature]Form.tsx)

```typescript
/**
 * [Feature] Form Component
 * Create/Edit form with validation
 */
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { Button } from '@/shared/components/ui/button';
import { Input } from '@/shared/components/ui/input';
import { Textarea } from '@/shared/components/ui/textarea';
import { Switch } from '@/shared/components/ui/switch';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/shared/components/ui/form';
import type { [Feature], [Feature]FormData } from '../types/[feature].types';

// Validation schema
const [feature]Schema = z.object({
  name: z
    .string()
    .min(1, 'Name is required')
    .max(200, 'Name must be less than 200 characters'),
  description: z
    .string()
    .max(2000, 'Description must be less than 2000 characters')
    .optional(),
  is_active: z.boolean().default(true),
});

interface [Feature]FormProps {
  /** Existing [feature] for edit mode, null for create mode */
  [feature]?: [Feature] | null;
  /** Callback when form is submitted */
  onSubmit: (data: [Feature]FormData) => void;
  /** Callback when cancel is clicked */
  onCancel: () => void;
  /** Loading state */
  isLoading?: boolean;
}

export function [Feature]Form({
  [feature],
  onSubmit,
  onCancel,
  isLoading = false,
}: [Feature]FormProps) {
  const { t } = useTranslation();
  const isEditing = !![feature];

  const form = useForm<[Feature]FormData>({
    resolver: zodResolver([feature]Schema),
    defaultValues: {
      name: [feature]?.name || '',
      description: [feature]?.description || '',
      is_active: [feature]?.is_active ?? true,
    },
  });

  const handleSubmit = (data: [Feature]FormData) => {
    onSubmit(data);
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
        {/* Name Field */}
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{t('[features].form.name')}</FormLabel>
              <FormControl>
                <Input
                  {...field}
                  placeholder={t('[features].form.namePlaceholder')}
                  disabled={isLoading}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Description Field */}
        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{t('[features].form.description')}</FormLabel>
              <FormControl>
                <Textarea
                  {...field}
                  placeholder={t('[features].form.descriptionPlaceholder')}
                  rows={4}
                  disabled={isLoading}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Active Status Field */}
        <FormField
          control={form.control}
          name="is_active"
          render={({ field }) => (
            <FormItem className="flex items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <FormLabel className="text-base">
                  {t('[features].form.isActive')}
                </FormLabel>
                <FormDescription>
                  {t('[features].form.isActiveDescription')}
                </FormDescription>
              </div>
              <FormControl>
                <Switch
                  checked={field.value}
                  onCheckedChange={field.onChange}
                  disabled={isLoading}
                />
              </FormControl>
            </FormItem>
          )}
        />

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isLoading}
          >
            {t('common.cancel')}
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading
              ? t('common.saving')
              : isEditing
              ? t('common.update')
              : t('common.create')}
          </Button>
        </div>
      </form>
    </Form>
  );
}
```

## List Component Template (components/[Feature]List.tsx)

```typescript
/**
 * [Feature] List Component
 * Displays paginated list with search and actions
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, Search, Trash2, Edit, MoreHorizontal } from 'lucide-react';
import { usePermissions } from '@/features/rbac/hooks/usePermissions';
import { Button } from '@/shared/components/ui/button';
import { Input } from '@/shared/components/ui/input';
import { Badge } from '@/shared/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/components/ui/dropdown-menu';
import { Skeleton } from '@/shared/components/ui/skeleton';
import { Pagination } from '@/shared/components/Pagination';
import { ConfirmDialog } from '@/shared/components/ConfirmDialog';
import { use[Features], use[Feature]Mutations } from '../hooks/use[Features]';
import type { [Feature] } from '../types/[feature].types';

interface [Feature]ListProps {
  onEdit: ([feature]: [Feature]) => void;
  onCreate: () => void;
}

export function [Feature]List({ onEdit, onCreate }: [Feature]ListProps) {
  const { t } = useTranslation();
  const { hasPermission } = usePermissions();

  // State
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<[Feature] | null>(null);

  // Data fetching
  const { data, isLoading, error } = use[Features]({
    page,
    limit: 20,
    search: search || undefined,
  });

  // Mutations
  const { delete: delete[Feature], isDeleting } = use[Feature]Mutations();

  // Handlers
  const handleSearch = (value: string) => {
    setSearch(value);
    setPage(1);
  };

  const handleDelete = () => {
    if (deleteTarget) {
      delete[Feature](deleteTarget.id);
      setDeleteTarget(null);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="rounded-md bg-destructive/10 p-4 text-destructive">
        {t('common.error')}: {error.message}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={t('[features].searchPlaceholder')}
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        {hasPermission('[features].create') && (
          <Button onClick={onCreate}>
            <Plus className="mr-2 h-4 w-4" />
            {t('[features].create')}
          </Button>
        )}
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t('[features].table.name')}</TableHead>
              <TableHead>{t('[features].table.description')}</TableHead>
              <TableHead>{t('[features].table.status')}</TableHead>
              <TableHead>{t('[features].table.created')}</TableHead>
              <TableHead className="w-[70px]" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  {t('[features].noItems')}
                </TableCell>
              </TableRow>
            ) : (
              data?.items.map(([feature]) => (
                <TableRow key={[feature].id}>
                  <TableCell className="font-medium">{[feature].name}</TableCell>
                  <TableCell className="max-w-xs truncate">
                    {[feature].description || '-'}
                  </TableCell>
                  <TableCell>
                    <Badge variant={[feature].is_active ? 'default' : 'secondary'}>
                      {[feature].is_active ? t('common.active') : t('common.inactive')}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {new Date([feature].created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {hasPermission('[features].update') && (
                          <DropdownMenuItem onClick={() => onEdit([feature])}>
                            <Edit className="mr-2 h-4 w-4" />
                            {t('common.edit')}
                          </DropdownMenuItem>
                        )}
                        {hasPermission('[features].delete') && (
                          <DropdownMenuItem
                            onClick={() => setDeleteTarget([feature])}
                            className="text-destructive"
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            {t('common.delete')}
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {data && data.pages > 1 && (
        <Pagination
          currentPage={page}
          totalPages={data.pages}
          onPageChange={setPage}
        />
      )}

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title={t('[features].deleteConfirm.title')}
        description={t('[features].deleteConfirm.description', {
          name: deleteTarget?.name,
        })}
        confirmText={t('common.delete')}
        onConfirm={handleDelete}
        isLoading={isDeleting}
        variant="destructive"
      />
    </div>
  );
}
```

## Page Component Template (pages/[Features]Page.tsx)

```typescript
/**
 * [Features] Page
 * Main page component with list and modal forms
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { usePermissions } from '@/features/rbac/hooks/usePermissions';
import { PageHeader } from '@/shared/components/PageHeader';
import { Modal } from '@/shared/components/Modal';
import { AccessDenied } from '@/shared/components/AccessDenied';
import { [Feature]List } from '../components/[Feature]List';
import { [Feature]Form } from '../components/[Feature]Form';
import { use[Feature]Mutations } from '../hooks/use[Features]';
import type { [Feature], [Feature]FormData } from '../types/[feature].types';

export function [Features]Page() {
  const { t } = useTranslation();
  const { hasPermission } = usePermissions();

  // State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editing[Feature], setEditing[Feature]] = useState<[Feature] | null>(null);

  // Mutations
  const { create, update, isCreating, isUpdating } = use[Feature]Mutations();

  // Permission check
  if (!hasPermission('[features].read')) {
    return <AccessDenied />;
  }

  // Handlers
  const handleCreate = () => {
    setEditing[Feature](null);
    setIsModalOpen(true);
  };

  const handleEdit = ([feature]: [Feature]) => {
    setEditing[Feature]([feature]);
    setIsModalOpen(true);
  };

  const handleSubmit = (data: [Feature]FormData) => {
    if (editing[Feature]) {
      update(
        { id: editing[Feature].id, data },
        { onSuccess: () => setIsModalOpen(false) }
      );
    } else {
      create(data, { onSuccess: () => setIsModalOpen(false) });
    }
  };

  const handleClose = () => {
    setIsModalOpen(false);
    setEditing[Feature](null);
  };

  return (
    <div className="container py-6">
      <PageHeader
        title={t('[features].title')}
        description={t('[features].description')}
      />

      <[Feature]List onEdit={handleEdit} onCreate={handleCreate} />

      <Modal
        open={isModalOpen}
        onOpenChange={handleClose}
        title={
          editing[Feature]
            ? t('[features].modal.editTitle')
            : t('[features].modal.createTitle')
        }
      >
        <[Feature]Form
          [feature]={editing[Feature]}
          onSubmit={handleSubmit}
          onCancel={handleClose}
          isLoading={isCreating || isUpdating}
        />
      </Modal>
    </div>
  );
}
```

## Index Export (index.ts)

```typescript
/**
 * [Feature] Feature Module
 * Public exports for the [feature] feature
 */

// Components
export { [Feature]List } from './components/[Feature]List';
export { [Feature]Form } from './components/[Feature]Form';

// Hooks
export { use[Features], use[Feature], use[Feature]Mutations, [feature]Keys } from './hooks/use[Features]';

// API
export { [feature]Api } from './api/[feature].api';

// Types
export type {
  [Feature],
  [Feature]ListResponse,
  Create[Feature]Request,
  Update[Feature]Request,
  [Feature]QueryParams,
  [Feature]FormData,
} from './types/[feature].types';

// Page (if using pages)
export { [Features]Page } from './pages/[Features]Page';
```

## i18n Translations Template

```json
// Add to cms-vite/src/i18n/locales/en.json
{
  "[features]": {
    "title": "[Features]",
    "description": "Manage your [features]",
    "create": "Create [Feature]",
    "searchPlaceholder": "Search [features]...",
    "noItems": "No [features] found",
    "table": {
      "name": "Name",
      "description": "Description",
      "status": "Status",
      "created": "Created"
    },
    "form": {
      "name": "Name",
      "namePlaceholder": "Enter [feature] name",
      "description": "Description",
      "descriptionPlaceholder": "Enter description (optional)",
      "isActive": "Active",
      "isActiveDescription": "Enable or disable this [feature]"
    },
    "modal": {
      "createTitle": "Create [Feature]",
      "editTitle": "Edit [Feature]"
    },
    "deleteConfirm": {
      "title": "Delete [Feature]?",
      "description": "Are you sure you want to delete \"{{name}}\"? This action cannot be undone."
    }
  }
}
```

## Route Registration

```typescript
// Add to cms-vite/src/routes/index.tsx
import { [Features]Page } from '@/features/[features]';

// In route configuration
{
  path: '[features]',
  element: <ProtectedRoute><[Features]Page /></ProtectedRoute>,
}

// Add to sidebar navigation (shared/components/layout/Sidebar.tsx)
{
  name: t('[features].title'),
  href: '/[features]',
  icon: [FeatureIcon],
  permission: '[features].read',
}
```

## Permission Constants (Frontend)

```typescript
// Add to cms-vite/src/features/rbac/constants/permissions.ts

export const [FEATURE]_PERMISSIONS = {
  '[features].read': '[Features] - View',
  '[features].create': '[Features] - Create',
  '[features].update': '[Features] - Update',
  '[features].delete': '[Features] - Delete',
  '[features].export': '[Features] - Export',
} as const;

// Add to ALL_PERMISSIONS
export const ALL_PERMISSIONS = {
  ...EXISTING_PERMISSIONS,
  ...[FEATURE]_PERMISSIONS,
};
```
