---
name: cms-ui-development
description: Ensure consistent CMS UI development with standardized components, forms, state management, and patterns. Use when creating new pages, components, or features in the CMS frontend. This skill works together with core-services-integration for complete full-stack consistency.
---

# CMS UI Development Guide

## Overview

This skill ensures consistent UI development across all CMS frontend features. It standardizes components, forms, state management, and UX patterns for the Smart TV Digital Signage CMS.

**IMPORTANT**: This skill works together with `core-services-integration`. Always check both skills when developing new features.

## When to Use This Skill

- Creating new CMS pages or features
- Building form components
- Implementing data tables
- Adding modals or dialogs
- Creating loading/error states
- Implementing dark mode
- Optimizing performance

## Related Skills

- **core-services-integration**: Backend & frontend integration patterns for Auth, RBAC, Organization, User, Audit
- See: `.claude/skills/core-services-integration/`

## Quick Reference

### Tech Stack
| Area | Technology |
|------|------------|
| Framework | React 18 + TypeScript |
| Build Tool | Vite |
| Styling | Tailwind CSS + shadcn/ui |
| Icons | Lucide React |
| Forms | React Hook Form + Zod |
| State (Global) | Zustand |
| State (Server) | TanStack Query |
| i18n | react-i18next |

### Feature Folder Structure
```
cms-vite/src/features/[feature]/
├── index.ts                    # Public exports
├── api/
│   └── [feature].api.ts        # API calls
├── components/
│   ├── [Feature]List.tsx       # List component
│   ├── [Feature]Form.tsx       # Create/Edit form
│   └── [Feature]Table.tsx      # Table component
├── hooks/
│   ├── use[Features].ts        # Data fetching hook
│   └── use[Feature]Mutations.ts # Mutation hooks
├── types/
│   └── [feature].types.ts      # TypeScript types
└── pages/
    └── [Features]Page.tsx      # Page component
```

## Development Checklist

### UI Requirements (this skill)
- [ ] Feature folder structure correct (api/components/hooks/types)
- [ ] Forms use React Hook Form + Zod
- [ ] Validation uses Zod schemas
- [ ] Modals use shared Modal.tsx
- [ ] Loading states with Skeleton components
- [ ] Error states with proper display
- [ ] Empty states for no data
- [ ] Dark mode compatible (CSS variables)
- [ ] i18n translations complete (en + id)
- [ ] Debounce on search inputs (300ms)

### Core Services Requirements (from core-services-integration)
- [ ] `useAuth()` for authentication check
- [ ] `hasPermission()` to gate UI elements
- [ ] Organization ID in all query keys
- [ ] Route registered with ProtectedRoute
- [ ] Sidebar navigation added

### Backend Integration (if creating new endpoints)
- [ ] `require_permission()` for authorization
- [ ] Filter by `organization_id`
- [ ] `sanitize_input()` for all user input
- [ ] Standardized errors
- [ ] Audit logging for mutations

## Supporting Documentation

- [ui-components.md](ui-components.md) - Component standards (Form, Table, Loading, Modal)
- [forms-validation.md](forms-validation.md) - Form handling with RHF + Zod
- [state-patterns.md](state-patterns.md) - State management and performance patterns

## Code Standards

### Import Order
```typescript
// 1. React & external libraries
import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

// 2. Shared components & hooks
import { useAuth } from '@/shared/hooks/useAuth';
import { Button } from '@/shared/components/ui/button';
import { Modal } from '@/shared/components/Modal';

// 3. Feature-specific imports
import { useFeatures, useFeatureMutations } from '../hooks/useFeatures';
import { FeatureForm } from './FeatureForm';

// 4. Types (last)
import type { Feature, FeatureFormData } from '../types/feature.types';
```

### Component Template
```typescript
/**
 * FeatureName Component
 * Brief description of what this component does
 */
import { useTranslation } from 'react-i18next';
import { usePermissions } from '@/features/rbac/hooks/usePermissions';

interface FeatureNameProps {
  // Props interface
}

export function FeatureName({ ...props }: FeatureNameProps) {
  const { t } = useTranslation();
  const { hasPermission } = usePermissions();

  // Permission check
  if (!hasPermission('feature.read')) {
    return <AccessDenied />;
  }

  return (
    // Component JSX
  );
}
```

### Hook Template
```typescript
/**
 * useFeatures Hook
 * Data fetching and state management for features
 */
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/shared/hooks/useAuth';
import { featureApi } from '../api/feature.api';

// Query keys factory - ALWAYS include orgId
export const featureKeys = {
  all: ['features'] as const,
  lists: () => [...featureKeys.all, 'list'] as const,
  list: (params: QueryParams, orgId: number) => [...featureKeys.lists(), params, orgId] as const,
  details: () => [...featureKeys.all, 'detail'] as const,
  detail: (id: number) => [...featureKeys.details(), id] as const,
};

export function useFeatures(params?: QueryParams) {
  const { user } = useAuth();
  const orgId = user?.organization_id;

  return useQuery({
    queryKey: featureKeys.list(params || {}, orgId!),
    queryFn: () => featureApi.getList(params),
    enabled: !!orgId, // Only fetch when org is available
    staleTime: 30 * 1000, // 30 seconds
  });
}
```

## Common Patterns

### 1. Page with List + Modal Form
```typescript
function FeaturesPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<Feature | null>(null);
  const { hasPermission } = usePermissions();

  if (!hasPermission('features.read')) {
    return <AccessDenied />;
  }

  return (
    <div className="container py-6">
      <PageHeader
        title={t('features.title')}
        actions={
          hasPermission('features.create') && (
            <Button onClick={() => setIsModalOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              {t('features.create')}
            </Button>
          )
        }
      />

      <FeatureList
        onEdit={(item) => {
          setEditingItem(item);
          setIsModalOpen(true);
        }}
      />

      <Modal
        open={isModalOpen}
        onOpenChange={(open) => {
          if (!open) setEditingItem(null);
          setIsModalOpen(open);
        }}
        title={editingItem ? t('features.edit') : t('features.create')}
      >
        <FeatureForm
          feature={editingItem}
          onSuccess={() => setIsModalOpen(false)}
        />
      </Modal>
    </div>
  );
}
```

### 2. Permission-Gated Actions
```typescript
// Always wrap actions with permission checks
<DropdownMenu>
  <DropdownMenuContent>
    {hasPermission('features.update') && (
      <DropdownMenuItem onClick={() => onEdit(item)}>
        <Edit className="mr-2 h-4 w-4" />
        {t('common.edit')}
      </DropdownMenuItem>
    )}
    {hasPermission('features.delete') && (
      <DropdownMenuItem
        onClick={() => setDeleteTarget(item)}
        className="text-destructive"
      >
        <Trash2 className="mr-2 h-4 w-4" />
        {t('common.delete')}
      </DropdownMenuItem>
    )}
  </DropdownMenuContent>
</DropdownMenu>
```

### 3. Loading/Error/Empty States
```typescript
function FeatureList() {
  const { data, isLoading, error } = useFeatures();

  // Loading state
  if (isLoading) {
    return <TableSkeleton rows={5} columns={4} />;
  }

  // Error state
  if (error) {
    return (
      <div className="rounded-md bg-destructive/10 p-4 text-destructive">
        {t('common.error')}: {error.message}
      </div>
    );
  }

  // Empty state
  if (!data?.items.length) {
    return (
      <EmptyState
        icon={Package}
        title={t('features.noItems')}
        description={t('features.noItemsDescription')}
        action={
          hasPermission('features.create') && (
            <Button onClick={onCreate}>
              <Plus className="mr-2 h-4 w-4" />
              {t('features.create')}
            </Button>
          )
        }
      />
    );
  }

  return <FeatureTable items={data.items} />;
}
```

## Quick Commands

```bash
# Create new feature folder structure
mkdir -p cms-vite/src/features/[name]/{api,components,hooks,types,pages}
touch cms-vite/src/features/[name]/index.ts

# Add translations
# Edit: cms-vite/src/i18n/locales/en.json
# Edit: cms-vite/src/i18n/locales/id.json

# Add route
# Edit: cms-vite/src/routes/index.tsx

# Add to sidebar
# Edit: cms-vite/src/shared/components/layout/Sidebar.tsx
```
