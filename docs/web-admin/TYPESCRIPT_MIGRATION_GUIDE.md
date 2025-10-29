# TypeScript Migration Guide

## Why TypeScript Over PropTypes?

### TypeScript Advantages ✅
- **Compile-time checking** - Errors caught before runtime
- **IDE Support** - Autocomplete, intellisense, instant feedback
- **Type inference** - Automatic type detection
- **Refactoring safety** - Rename with confidence
- **Industry standard** - Used by 80%+ of modern React projects
- **Better DX** - Developer experience is significantly improved

### PropTypes Limitations ❌
- **Runtime-only** - Errors only appear when code runs
- **No IDE support** - No autocomplete or type hints
- **Manual work** - Must write type definitions by hand
- **Legacy technology** - Being phased out in favor of TypeScript

## Migration Status

### ✅ Completed
- TypeScript installed and configured
- `tsconfig.json` created with strict mode
- `main.tsx` converted with proper null checks
- **Modal.tsx** converted (reference implementation)

### 🔄 In Progress
- Gradual migration of shared components
- Button, FormInput, and other core components

### ❌ Not Started
- Page components (.jsx → .tsx)
- Hook files (.js → .ts)
- Utility files (.js → .ts)

## Setup Summary

### Installed Packages
```json
{
  "devDependencies": {
    "typescript": "^5.x",
    "@types/react": "^18.x",
    "@types/react-dom": "^18.x",
    "@types/node": "^20.x"
  }
}
```

### TypeScript Configuration
**tsconfig.json:**
- `strict: true` - Maximum type safety
- `noUnusedLocals: true` - Catch unused variables
- `noUnusedParameters: true` - Catch unused params
- `jsx: "react-jsx"` - Modern JSX transform
- Path aliases: `@/*` → `src/*`

## Migration Pattern: Modal Component Example

### Before (Modal.jsx - PropTypes)
```jsx
import { useEffect } from 'react'
import PropTypes from 'prop-types'

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  className = ''
}) {
  const handleBackdropClick = (e) => {  // ❌ No type for event
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  const sizeClasses = {  // ❌ No type safety for keys
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg'
  }

  return <div onClick={handleBackdropClick}>...</div>
}

// PropTypes defined AFTER component
Modal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  title: PropTypes.string,
  children: PropTypes.node.isRequired,
  footer: PropTypes.node,
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  className: PropTypes.string,
}
```

### After (Modal.tsx - TypeScript)
```tsx
import { useEffect, ReactNode, MouseEvent } from 'react'

// ✅ Types defined FIRST - clear contract
type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | 'full'

interface ModalProps {
  /** Controls modal visibility */
  isOpen: boolean
  /** Callback when modal should close */
  onClose: () => void
  /** Optional modal title */
  title?: string
  /** Modal content */
  children: ReactNode
  /** Optional footer content */
  footer?: ReactNode
  /** Modal size */
  size?: ModalSize
  /** Additional CSS classes */
  className?: string
}

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  className = ''
}: ModalProps) {  // ✅ Type annotation on params
  // ✅ Event type is explicit and type-safe
  const handleBackdropClick = (e: MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose()  // ✅ TypeScript knows onClose is () => void
    }
  }

  // ✅ Record type ensures all ModalSize values are covered
  const sizeClasses: Record<ModalSize, string> = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    '3xl': 'max-w-3xl',
    '4xl': 'max-w-4xl',
    full: 'max-w-full mx-4'
  }

  return <div onClick={handleBackdropClick}>...</div>
}
```

## Key TypeScript Patterns

### 1. Props Interface
```tsx
// ✅ Good: Clear, documented interface
interface ButtonProps {
  /** Button label */
  children: ReactNode
  /** Click handler */
  onClick?: () => void
  /** Button variant */
  variant?: 'primary' | 'secondary'
  /** Disabled state */
  disabled?: boolean
}

function Button({ children, onClick, variant = 'primary', disabled }: ButtonProps) {
  // Implementation
}
```

### 2. Union Types for Variants
```tsx
// ✅ Exhaustive type - autocomplete works!
type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost'
type ButtonSize = 'sm' | 'md' | 'lg'

// ❌ Bad: string allows ANY value
variant: string

// ✅ Good: only valid values allowed
variant: ButtonVariant
```

### 3. Event Handlers
```tsx
import { MouseEvent, ChangeEvent, FormEvent } from 'react'

// ✅ Mouse events
const handleClick = (e: MouseEvent<HTMLButtonElement>) => {}

// ✅ Input change events
const handleChange = (e: ChangeEvent<HTMLInputElement>) => {}

// ✅ Form submit events
const handleSubmit = (e: FormEvent<HTMLFormElement>) => {}
```

### 4. Callback Props
```tsx
interface FormProps {
  // ✅ No params, no return
  onClose: () => void

  // ✅ With params, no return
  onSubmit: (data: FormData) => void

  // ✅ With params and return
  onChange: (value: string) => boolean
}
```

### 5. Optional vs Required Props
```tsx
interface ComponentProps {
  // ✅ Required (no ?)
  title: string

  // ✅ Optional (with ?)
  subtitle?: string

  // ✅ Required but can be undefined
  data: Data | undefined
}
```

### 6. Children Prop
```tsx
import { ReactNode, PropsWithChildren } from 'react'

// Option 1: Explicit
interface Props {
  children: ReactNode
}

// Option 2: PropsWithChildren utility
interface Props extends PropsWithChildren {
  title: string
}
```

### 7. Record Type for Mapped Objects
```tsx
// ✅ Ensures all keys are present
const sizeClasses: Record<Size, string> = {
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg'
}

// TypeScript error if missing a size!
```

### 8. Null Checks
```tsx
// ❌ Before: Can be null
const element = document.getElementById('root')
ReactDOM.createRoot(element).render(...)

// ✅ After: Type-safe
const element = document.getElementById('root')
if (!element) throw new Error('Root element not found')
ReactDOM.createRoot(element).render(...)
```

## Step-by-Step Component Migration

### Step 1: Rename .jsx → .tsx
```bash
git mv src/components/Button.jsx src/components/Button.tsx
```

### Step 2: Add Type Imports
```tsx
import { ReactNode, MouseEvent } from 'react'
```

### Step 3: Define Props Interface
```tsx
interface ButtonProps {
  children: ReactNode
  onClick?: () => void
  variant?: 'primary' | 'secondary'
  disabled?: boolean
  className?: string
}
```

### Step 4: Type the Component
```tsx
export default function Button({
  children,
  onClick,
  variant = 'primary',
  disabled = false,
  className = ''
}: ButtonProps) {
  // Implementation stays the same
}
```

### Step 5: Type Event Handlers
```tsx
const handleClick = (e: MouseEvent<HTMLButtonElement>) => {
  e.preventDefault()
  onClick?.()  // Optional chaining
}
```

### Step 6: Remove PropTypes
```tsx
// ❌ Delete this entire block
Button.propTypes = {
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func,
  // ...
}
```

### Step 7: Test TypeScript Compilation
```bash
npx tsc --noEmit
```

## Common Patterns Reference

### useState with Types
```tsx
// Type inference (recommended)
const [count, setCount] = useState(0)  // number
const [name, setName] = useState('')   // string

// Explicit type (for complex types)
const [user, setUser] = useState<User | null>(null)
const [items, setItems] = useState<Item[]>([])
```

### Custom Hooks
```tsx
// hooks/useToggle.ts
export function useToggle(initialValue = false) {
  const [value, setValue] = useState(initialValue)

  const toggle = () => setValue(v => !v)
  const setTrue = () => setValue(true)
  const setFalse = () => setValue(false)

  return { value, toggle, setTrue, setFalse }
}
```

### API Response Types
```tsx
// types/api.ts
export interface Device {
  id: number
  name: string
  status: 'active' | 'pending' | 'inactive'
  last_seen: string
}

export interface ApiResponse<T> {
  success: boolean
  data: T
  meta: {
    request_id: string
    timestamp: string
  }
}

// Usage
const response: ApiResponse<Device[]> = await api.get('/devices')
```

## Migration Priority

### Phase 1: Foundation (Week 1) ✅ DONE
- [x] Install TypeScript
- [x] Configure tsconfig.json
- [x] Convert main.tsx
- [x] Convert Modal.tsx (reference)

### Phase 2: Shared Components (Week 2)
- [ ] Button.tsx
- [ ] FormInput.tsx
- [ ] Badge.tsx, Card.tsx, StatusBadge.tsx
- [ ] Thumbnail.tsx, LoadingSpinner.tsx, EmptyState.tsx
- [ ] PageHeader.tsx, ErrorBoundary.tsx

### Phase 3: Feature Components (Week 3)
- [ ] Device modals (DeviceDetailModal, etc.)
- [ ] Content modals
- [ ] Tag modals
- [ ] Playlist modals

### Phase 4: Pages & Hooks (Week 4)
- [ ] Dashboard.tsx
- [ ] Devices.tsx, Content.tsx, Tags.tsx
- [ ] Custom hooks (useDashboardStats, etc.)
- [ ] Utility files

### Phase 5: Full Strict Mode (Week 5)
- [ ] Enable `strict: true` in tsconfig
- [ ] Fix all type errors
- [ ] Add missing null checks
- [ ] Comprehensive type coverage

## IDE Setup

### VS Code (Recommended)
1. Install "TypeScript" extension (built-in)
2. Enable "TypeScript: Suggest: Completefunctioncalls"
3. Enable "Editor: Inlay Hints"

### WebStorm
1. TypeScript support built-in
2. Enable "TypeScript Language Service"
3. Set "TypeScript version" to project version

## Troubleshooting

### Error: "Cannot find module './Component.jsx'"
**Fix:** Remove `.jsx` extension from imports
```tsx
// ❌ Bad
import App from './App.jsx'

// ✅ Good
import App from './App'
```

### Error: "Type 'null' is not assignable to type..."
**Fix:** Add null check
```tsx
const element = document.getElementById('root')
if (!element) throw new Error('Not found')
// Now element is guaranteed non-null
```

### Error: "Property 'value' does not exist on type 'EventTarget'"
**Fix:** Type the event correctly
```tsx
// ❌ Bad
const handleChange = (e: Event) => {
  console.log(e.target.value)  // Error!
}

// ✅ Good
const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
  console.log(e.target.value)  // Works!
}
```

## Best Practices

1. **Start strict from Day 1** - Don't use `any` or `@ts-ignore`
2. **Interface over Type** - Use `interface` for objects, `type` for unions
3. **Explicit returns** - Add return types to functions
4. **Avoid null** - Use optional chaining `?.` and nullish coalescing `??`
5. **Document with JSDoc** - Add `/** */` comments to interfaces
6. **Use utility types** - `Record`, `Pick`, `Omit`, `Partial`, `Required`

## Resources

- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [TypeScript Deep Dive](https://basarat.gitbook.io/typescript/)

## Next Steps

1. Convert `Button.tsx` using Modal.tsx as reference
2. Convert `FormInput.tsx` with proper event typing
3. Continue with remaining shared components
4. Update this guide with new patterns discovered

---

**Created:** 2025-01-XX
**Status:** ✅ TypeScript setup complete - Modal.tsx is the reference implementation
**Contact:** See project maintainers for questions
