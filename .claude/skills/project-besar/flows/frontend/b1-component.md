---
description: Create UI component for PROJECT_BESAR
---

# Flow B1: Create UI Component

## Pre-requisites
- [ ] Component purpose defined
- [ ] Props identified
- [ ] Design reference available

## Step 1: Create Component
Location: `modules/{module}/frontend/src/components/{ComponentName}/{ComponentName}.tsx`

```typescript
import { FC } from 'react';
import { cn } from '@/utils/cn';

interface {ComponentName}Props {
  className?: string;
  // Add props
}

export const {ComponentName}: FC<{ComponentName}Props> = ({
  className,
  ...props
}) => {
  return (
    <div className={cn('base-styles', className)}>
      {/* Component content */}
    </div>
  );
};
```

## Step 2: Create Types
Location: `modules/{module}/frontend/src/components/{ComponentName}/types.ts`

```typescript
export interface {ComponentName}Props {
  className?: string;
}
```

## Step 3: Create Index
Location: `modules/{module}/frontend/src/components/{ComponentName}/index.ts`

```typescript
export { {ComponentName} } from './{ComponentName}';
export type { {ComponentName}Props } from './types';
```

## Step 4: Create Test
Location: `modules/{module}/frontend/src/components/{ComponentName}/{ComponentName}.test.tsx`

```typescript
import { render, screen } from '@testing-library/react';
import { {ComponentName} } from './{ComponentName}';

describe('{ComponentName}', () => {
  it('renders correctly', () => {
    render(<{ComponentName} />);
    // Add assertions
  });
});
```

## Step 5: Accessibility Check
- [ ] Proper ARIA labels
- [ ] Keyboard navigation
- [ ] Color contrast
- [ ] Screen reader friendly

## Checklist Before Complete
- [ ] TypeScript strict mode passes
- [ ] Props documented
- [ ] Tests written
- [ ] Accessible
- [ ] Responsive
