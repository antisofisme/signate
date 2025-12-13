---
description: Create page/view for PROJECT_BESAR
---

# Flow B2: Create Page/View

## Pre-requisites
- [ ] Page purpose defined
- [ ] Route path defined
- [ ] Required permissions identified

## Step 1: Create Page Component
Location: `modules/{module}/frontend/src/pages/{PageName}/{PageName}Page.tsx`

```typescript
import { FC } from 'react';
import { PageHeader } from '@/components/PageHeader';
import { use{Entity}Query } from '@/hooks/use{Entity}';

export const {PageName}Page: FC = () => {
  const { data, isLoading, error } = use{Entity}Query();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <div className="page-container">
      <PageHeader title="{Page Title}" />
      <div className="page-content">
        {/* Page content */}
      </div>
    </div>
  );
};
```

## Step 2: Create Index
Location: `modules/{module}/frontend/src/pages/{PageName}/index.ts`

```typescript
export { {PageName}Page } from './{PageName}Page';
```

## Step 3: Add Route
Location: `modules/{module}/frontend/src/routes.tsx`

```typescript
import { {PageName}Page } from '@/pages/{PageName}';

{
  path: '{page-path}',
  element: (
    <ProtectedRoute permission="{module}.{resource}.view">
      <{PageName}Page />
    </ProtectedRoute>
  ),
}
```

## Step 4: Add Navigation
Location: `modules/{module}/frontend/src/config/navigation.ts`

```typescript
{
  name: '{Page Name}',
  href: '/{page-path}',
  icon: Icon{PageName},
  permission: '{module}.{resource}.view',
}
```

## Checklist Before Complete
- [ ] Route configured
- [ ] Permission check added
- [ ] Loading state handled
- [ ] Error state handled
- [ ] Navigation added
