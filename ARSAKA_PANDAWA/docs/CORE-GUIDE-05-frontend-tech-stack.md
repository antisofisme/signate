# Frontend Technology Stack

> **Date**: 2025-12-23
> **Status**: Official Reference
> **Purpose**: Technology choices, usage patterns, and best practices for ARSAKA_PANDAWA frontend
> **Audience**: Frontend developers, full-stack developers, onboarding engineers

---

## Philosophy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      FRONTEND TECH PHILOSOPHY                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Core Principle:                                                        │
│  > Right tool for the right job, not everything is a nail              │
│                                                                         │
│  Goals:                                                                 │
│  ✓ High performance for large datasets                                  │
│  ✓ Multi-tenant safe & secure                                          │
│  ✓ Stable & consistent UX                                              │
│  ✓ Maintainable by small team                                          │
│  ✓ Not over-engineered                                                 │
│                                                                         │
│  Core Concepts:                                                         │
│  1. Server data ≠ UI state (separate concerns)                          │
│  2. Cache is more important than fast fetch                             │
│  3. Large tables must be virtualized                                    │
│  4. Frontend is NOT a security layer                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FRONTEND TECHNOLOGY STACK                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ FOUNDATION (UI Framework & Build)                               │   │
│  │ ┌─────────────────────────────────────────────────────────────┐ │   │
│  │ │ React 18+          (Component library & virtual DOM)         │ │   │
│  │ │ Vite               (Build tool, fast dev, small bundle)      │ │   │
│  │ │ TypeScript         (Type safety)                             │ │   │
│  │ │ Tailwind CSS       (Utility CSS)                             │ │   │
│  │ │ shadcn/ui          (Component library)                       │ │   │
│  │ └─────────────────────────────────────────────────────────────┘ │   │
│  │                                                                   │   │
│  │ ┌─────────────────────────────────────────────────────────────┐ │   │
│  │ │ STATE MANAGEMENT                                            │ │   │
│  │ │ ┌───────────────────────┐     ┌────────────────────────┐   │ │   │
│  │ │ │ TanStack Query        │     │ Zustand              │   │ │   │
│  │ │ │ (Server state cache)  │     │ (Client/UI state)    │   │ │   │
│  │ │ └───────────────────────┘     └────────────────────────┘   │ │   │
│  │ └─────────────────────────────────────────────────────────────┘ │   │
│  │                                                                   │   │
│  │ ┌─────────────────────────────────────────────────────────────┐ │   │
│  │ │ DATA HANDLING                                               │ │   │
│  │ │ ┌────────────────────┐  ┌────────────────────────────────┐ │ │   │
│  │ │ │ TanStack Table     │  │ TanStack Virtual              │ │ │   │
│  │ │ │ (Complex tables)   │  │ (Big data rendering)          │ │ │   │
│  │ │ │ - Sorting          │  │ - Virtualization              │ │ │   │
│  │ │ │ - Filtering        │  │ - 1000s of rows              │ │ │   │
│  │ │ │ - Pagination       │  │ - Minimal DOM nodes           │ │ │   │
│  │ │ └────────────────────┘  └────────────────────────────────┘ │ │   │
│  │ └─────────────────────────────────────────────────────────────┘ │   │
│  │                                                                   │   │
│  │ ┌─────────────────────────────────────────────────────────────┐ │   │
│  │ │ FORMS & VALIDATION                                          │ │   │
│  │ │ ┌────────────────────┐  ┌────────────────────────────────┐ │ │   │
│  │ │ │ React Hook Form    │  │ Zod                           │ │ │   │
│  │ │ │ (Form state)       │  │ (Schema validation)           │ │ │   │
│  │ │ │ - Minimal re-render│  │ - Type-safe                   │ │ │   │
│  │ │ │ - Built-in errors  │  │ - Shareable with backend      │ │ │   │
│  │ │ └────────────────────┘  └────────────────────────────────┘ │ │   │
│  │ └─────────────────────────────────────────────────────────────┘ │   │
│  │                                                                   │   │
│  │ ┌─────────────────────────────────────────────────────────────┐ │   │
│  │ │ ROUTING                                                     │ │   │
│  │ │ React Router 6+  (SPA routing with guards & loaders)        │ │   │
│  │ └─────────────────────────────────────────────────────────────┘ │   │
│  │                                                                   │   │
│  │ ┌─────────────────────────────────────────────────────────────┐ │   │
│  │ │ REALTIME                                                    │ │   │
│  │ │ Centrifuge JS  (WebSocket events for live updates)          │ │   │
│  │ └─────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Foundation Stack

### React 18+

**Problem Solved:**
- Managing UI state changes
- Virtual DOM diffing
- Component reusability

**Why Chosen:**
- Mature ecosystem (most libraries support React)
- Great TypeScript support
- Concurrent rendering (18+)
- Community & hiring pool

**Usage:**
```typescript
// Functional components with hooks
export function ReservationCard({ reservation }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div onClick={() => setExpanded(!expanded)}>
      <h3>{reservation.guestName}</h3>
      {expanded && (
        <Details reservation={reservation} />
      )}
    </div>
  )
}

// Custom hooks for logic
function useReservation(id: number) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['reservation', id],
    queryFn: () => api.getReservation(id)
  })

  return { data, isLoading, error }
}
```

**Best Practices:**
- Keep components small & focused
- Extract logic into custom hooks
- Use lazy loading for large components
- Memoize expensive computations

**Trade-offs:**
✗ Large bundle size (mitigated by tree-shaking & lazy loading)
✗ Learning curve for new developers

---

### Vite

**Problem Solved:**
- Fast development server
- Optimized production build
- Modern ES modules support

**Why Chosen:**
- 10-100x faster than Webpack in dev
- Smaller bundle size
- Native ES modules in browser
- Vue/React support

**Setup:**
```bash
npm create vite@latest my-app -- --template react-ts
npm install
npm run dev      # Dev server (instant HMR)
npm run build    # Production build
```

**Configuration:**
```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  build: {
    target: 'ES2020',
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom'],
          'vendor-table': ['@tanstack/react-table'],
          'vendor-query': ['@tanstack/react-query']
        }
      }
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

**Best Practices:**
- Use path aliases (@/components, @/utils)
- Code splitting for lazy routes
- Monitor bundle size with `npm run build`

---

### TypeScript

**Problem Solved:**
- Type safety
- Better IDE support
- Self-documenting code

**Why Chosen:**
- Prevents entire class of bugs
- Great for refactoring
- All modern libraries support it

**Usage:**
```typescript
// Type-safe API calls
interface Reservation {
  id: number
  guestName: string
  checkIn: Date
  checkOut: Date
  total: number
}

async function getReservation(id: number): Promise<Reservation> {
  const response = await fetch(`/api/reservations/${id}`)
  if (!response.ok) throw new Error('Failed to fetch')
  return response.json()
}

// Component props
interface ReservationCardProps {
  reservation: Reservation
  onEdit?: (id: number) => void
  isLoading?: boolean
}

export function ReservationCard({
  reservation,
  onEdit,
  isLoading = false
}: ReservationCardProps) {
  // Type-safe!
  return (
    <div>
      <h3>{reservation.guestName}</h3>
      <p>Check-in: {reservation.checkIn.toLocaleDateString()}</p>
    </div>
  )
}
```

**Configuration:**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  }
}
```

---

### Tailwind CSS + shadcn/ui

**Problem Solved:**
- Consistent styling across app
- Rapid UI development
- Pre-built accessible components

**Why Chosen:**
- Utility-first approach (no naming hassles)
- Extremely fast development
- shadcn/ui provides accessible components
- Easy theming & customization

**Usage:**
```typescript
// Using shadcn Button
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function ReservationForm() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Create Reservation</CardTitle>
      </CardHeader>
      <CardContent>
        <form>
          <input
            className="w-full px-3 py-2 border rounded-md"
            type="text"
            placeholder="Guest name"
          />
          <Button type="submit" className="mt-4">
            Create
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
```

**Configuration:**
```bash
# Install shadcn/ui component
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add form
npx shadcn-ui@latest add table
```

**Tailwind Config:**
```javascript
// tailwind.config.js
module.exports = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        'brand': '#0066cc'
      }
    }
  }
}
```

---

## Part 2: State Management

### TanStack Query (React Query)

**Problem Solved:**
- Fetching server data
- Caching
- Synchronization with server
- Automatic refetching
- Deduplication

**Why Chosen:**
- Industry standard for server state
- Reduces boilerplate 80%
- Excellent TypeScript support
- Built-in devtools

**Usage Pattern:**
```typescript
// 1. SIMPLE QUERY
import { useQuery } from '@tanstack/react-query'

function ReservationList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['reservations', { tenantId, month }],
    queryFn: () => api.getReservations({ tenantId, month }),
    staleTime: 5 * 60 * 1000,  // Data fresh for 5 min
    gcTime: 10 * 60 * 1000      // Keep in cache 10 min
  })

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorAlert error={error} />

  return (
    <ul>
      {data?.map(res => (
        <li key={res.id}>{res.guestName}</li>
      ))}
    </ul>
  )
}

// 2. MUTATION (Create/Update/Delete)
function CreateReservationForm() {
  const queryClient = useQueryClient()

  const { mutate, isPending } = useMutation({
    mutationFn: (data) => api.createReservation(data),
    onSuccess: (newRes) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({
        queryKey: ['reservations']
      })

      // Or optimistic update
      queryClient.setQueryData(
        ['reservations'],
        (old) => [...old, newRes]
      )
    },
    onError: (error) => {
      showErrorToast(error.message)
    }
  })

  return (
    <form onSubmit={(e) => {
      e.preventDefault()
      mutate(formData)
    }}>
      {/* form fields */}
      <button disabled={isPending}>Create</button>
    </form>
  )
}

// 3. DEPENDENT QUERIES
function GuestDetails({ guestId }) {
  // First query: get guest
  const { data: guest } = useQuery({
    queryKey: ['guest', guestId],
    queryFn: () => api.getGuest(guestId)
  })

  // Second query: only runs when guest is loaded
  const { data: reservations } = useQuery({
    queryKey: ['reservations', guest?.id],
    queryFn: () => api.getReservations(guest.id),
    enabled: !!guest  // ← Only run if guest exists
  })

  return (
    <div>
      <h3>{guest?.name}</h3>
      <ReservationList reservations={reservations} />
    </div>
  )
}
```

**Best Practices:**
```typescript
// ✅ DO: Include all dependencies in queryKey
useQuery({
  queryKey: ['reservations', { tenantId, status, month }],
  queryFn: ({ queryKey }) => {
    const [, filters] = queryKey
    return api.getReservations(filters)
  }
})

// ❌ DON'T: Fetch without query key
const [reservations, setReservations] = useState([])
useEffect(() => {
  api.getReservations().then(setReservations)
}, [])  // ← Missing dependencies!

// ✅ DO: Set appropriate staleTime
useQuery({
  queryKey: ['user'],
  queryFn: () => api.getUser(),
  staleTime: Infinity  // User data rarely changes
})

// ❌ DON'T: Treat it like Redux
// (Don't try to store UI state in query)
```

**Multi-Tenant Considerations:**
```typescript
// ✅ DO: Include tenantId in queryKey
useQuery({
  queryKey: ['reservations', tenantId, filters],
  queryFn: () => api.getReservations(tenantId, filters)
})

// ✅ DO: Clear cache on tenant change
const { tenantId } = useAppContext()
const queryClient = useQueryClient()

useEffect(() => {
  // Clear all queries when tenant changes
  queryClient.clear()
}, [tenantId, queryClient])

// ❌ DON'T: Share cache between tenants
// (Always include tenantId in queryKey)
```

---

### Zustand

**Problem Solved:**
- UI state (modals, sidebars, theme)
- Global client state
- Lightweight alternative to Redux

**Why Chosen:**
- Minimal boilerplate
- No providers needed (can be used without)
- Perfect for UI state
- Very small bundle size

**Usage:**
```typescript
// 1. DEFINE STORE
import { create } from 'zustand'

interface AppState {
  // State
  theme: 'light' | 'dark'
  sidebarOpen: boolean
  activeTab: string

  // Actions
  setTheme: (theme: 'light' | 'dark') => void
  toggleSidebar: () => void
  setActiveTab: (tab: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  theme: 'light',
  sidebarOpen: true,
  activeTab: 'dashboard',

  // Actions
  setTheme: (theme) => set({ theme }),
  toggleSidebar: () => set((state) => ({
    sidebarOpen: !state.sidebarOpen
  })),
  setActiveTab: (tab) => set({ activeTab: tab })
}))

// 2. USE IN COMPONENT
function Navbar() {
  const { theme, setTheme } = useAppStore()

  return (
    <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
      Toggle Theme: {theme}
    </button>
  )
}

// 3. PERSIST TO LOCALSTORAGE
import { persist } from 'zustand/middleware'

export const useAppStore = create<AppState>(
  persist(
    (set) => ({
      // ... store definition
    }),
    {
      name: 'app-store',  // ← localStorage key
      partialize: (state) => ({
        theme: state.theme,
        sidebarOpen: state.sidebarOpen
      })  // ← Only persist these
    }
  )
)
```

**What to Store in Zustand:**
✅ Theme, language, sidebar state
✅ Modal visibility
✅ UI preferences
✅ Temporary UI state

**What NOT to Store in Zustand:**
❌ API data (use TanStack Query)
❌ User info (derive from auth)
❌ Business logic data

---

## Part 3: Data Handling

### TanStack Table (React Table)

**Problem Solved:**
- Complex data tables
- Sorting, filtering, pagination
- Large datasets

**Why Chosen:**
- Headless (you control rendering)
- Works with shadcn/ui
- Flexible & extensible
- Works with virtualization

**Usage:**
```typescript
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  ColumnDef
} from '@tanstack/react-table'

// 1. DEFINE COLUMNS
const columns: ColumnDef<Reservation>[] = [
  {
    accessorKey: 'guestName',
    header: 'Guest',
    cell: (info) => info.getValue()
  },
  {
    accessorKey: 'checkIn',
    header: 'Check-in',
    cell: (info) => (info.getValue() as Date).toLocaleDateString()
  },
  {
    accessorKey: 'total',
    header: 'Total',
    cell: (info) => `$${(info.getValue() as number).toFixed(2)}`
  }
]

// 2. CREATE TABLE
function ReservationTable({ data }: { data: Reservation[] }) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: 10
  })

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    state: {
      sorting,
      columnFilters,
      pagination
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onPaginationChange: setPagination
  })

  // 3. RENDER TABLE
  return (
    <div>
      {/* Filter input */}
      <input
        placeholder="Filter by guest..."
        onChange={(e) =>
          table.getColumn('guestName')?.setFilterValue(e.target.value)
        }
      />

      {/* Table */}
      <table>
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  onClick={header.column.getToggleSortingHandler()}
                >
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                  {/* Sort indicator */}
                  {header.column.getIsSorted() === 'asc' ? '▲' : '▼'}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id}>
                  {flexRender(
                    cell.column.columnDef.cell,
                    cell.getContext()
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Pagination */}
      <div>
        <button
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          Previous
        </button>
        <span>
          Page {table.getState().pagination.pageIndex + 1} of{' '}
          {table.getPageCount()}
        </span>
        <button
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          Next
        </button>
      </div>
    </div>
  )
}
```

**Best Practices:**
- Use for >10 rows
- Combine with virtualization for >500 rows
- Implement server-side filtering for large datasets

---

### TanStack Virtual

**Problem Solved:**
- Rendering thousands of rows
- Memory & performance optimization
- Smooth scrolling

**Why Chosen:**
- Renders only visible items
- Huge performance boost
- Works with React Table

**Usage:**
```typescript
import { useVirtualizer } from '@tanstack/react-virtual'

function VirtualizedLedger({ entries }: { entries: LedgerEntry[] }) {
  const parentRef = useRef<HTMLDivElement>(null)

  const virtualizer = useVirtualizer({
    count: entries.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,  // Row height
    overscan: 10  // Render 10 rows outside viewport
  })

  const virtualItems = virtualizer.getVirtualItems()

  return (
    <div
      ref={parentRef}
      style={{ height: '600px', overflow: 'auto' }}
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative'
        }}
      >
        {virtualItems.map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`
            }}
          >
            <LedgerRow entry={entries[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  )
}
```

**When to Use:**
✅ Lists > 500 items
✅ Tables with scroll
✅ Chat message history
✅ Activity streams

**When NOT to Use:**
❌ Small lists < 100 items
❌ Fixed-height containers
❌ Requires precise measurements

---

## Part 4: Forms & Validation

### React Hook Form

**Problem Solved:**
- Complex form state management
- Minimal re-renders
- Form validation
- Built-in error handling

**Why Chosen:**
- Very small bundle size
- Minimal re-renders (only invalid fields)
- Great TypeScript support
- Works with Zod perfectly

**Usage:**
```typescript
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

// Schema (also used for backend)
const reservationSchema = z.object({
  guestName: z.string().min(2, 'Name required'),
  email: z.string().email('Invalid email'),
  checkIn: z.date(),
  checkOut: z.date(),
  roomId: z.number()
})

type ReservationForm = z.infer<typeof reservationSchema>

function CreateReservationForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    watch
  } = useForm<ReservationForm>({
    resolver: zodResolver(reservationSchema)
  })

  const checkIn = watch('checkIn')

  const onSubmit = async (data: ReservationForm) => {
    await api.createReservation(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Text input */}
      <input
        {...register('guestName')}
        placeholder="Guest name"
      />
      {errors.guestName && (
        <span className="text-red-500">{errors.guestName.message}</span>
      )}

      {/* Email input */}
      <input
        {...register('email')}
        type="email"
        placeholder="Email"
      />
      {errors.email && (
        <span className="text-red-500">{errors.email.message}</span>
      )}

      {/* Date input */}
      <input
        {...register('checkIn', { valueAsDate: true })}
        type="date"
      />

      {/* Conditional validation: checkout after checkin */}
      <input
        {...register('checkOut', { valueAsDate: true })}
        type="date"
      />
      {checkIn && (
        <p className="text-sm">
          Checkout must be after {checkIn.toLocaleDateString()}
        </p>
      )}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Creating...' : 'Create'}
      </button>
    </form>
  )
}
```

**Best Practices:**
```typescript
// ✅ DO: Use useForm options for validation
const { register } = useForm({
  resolver: zodResolver(schema),
  mode: 'onBlur'  // ← Validate on blur, not every keystroke
})

// ❌ DON'T: Manual validation logic
const [errors, setErrors] = useState({})
const [guestName, setGuestName] = useState('')
// ... manual validation ...

// ✅ DO: Watch for dependent fields
const { watch } = useForm()
const checkIn = watch('checkIn')

// ❌ DON'T: Calculate in render
const daysStay = days.includes(checkIn) ? ... // Bad!
```

---

### Zod

**Problem Solved:**
- Runtime validation
- Type-safe schemas
- API contract validation

**Why Chosen:**
- Can share schema with backend (JSON serializable)
- Works perfectly with React Hook Form
- Excellent error messages
- TypeScript-first

**Usage:**
```typescript
import { z } from 'zod'

// 1. DEFINE SCHEMA
const userSchema = z.object({
  id: z.number(),
  email: z.string().email(),
  role: z.enum(['user', 'admin']),
  createdAt: z.date()
})

// 2. EXTRACT TYPE
type User = z.infer<typeof userSchema>

// 3. VALIDATE API RESPONSE
async function getUser(id: number): Promise<User> {
  const response = await fetch(`/api/users/${id}`)
  const data = await response.json()

  // Runtime validation!
  return userSchema.parse(data)
}

// 4. HANDLE VALIDATION ERRORS
try {
  const user = await getUser(123)
} catch (error) {
  if (error instanceof z.ZodError) {
    console.log(error.errors)
    // [{ path: ['email'], message: 'Invalid email', code: 'invalid_string' }]
  }
}

// 5. CUSTOM VALIDATION
const passwordSchema = z.string()
  .min(8, 'Must be 8+ characters')
  .regex(/[A-Z]/, 'Must contain uppercase')
  .regex(/[0-9]/, 'Must contain number')

// 6. CONDITIONAL VALIDATION
const checkoutSchema = z.object({
  checkIn: z.date(),
  checkOut: z.date()
}).refine(
  (data) => data.checkOut > data.checkIn,
  { message: 'Checkout must be after check-in' }
)
```

**Sharing with Backend:**
```typescript
// frontend/schemas/user.ts
export const userSchema = z.object({
  id: z.number(),
  email: z.string().email(),
  name: z.string()
})

// backend/schemas.py (convert to Pydantic)
from pydantic import BaseModel, EmailStr

class UserSchema(BaseModel):
    id: int
    email: EmailStr
    name: str
```

---

## Part 5: Routing & Realtime

### Module Loading & Subscription Synchronization

**Frontend Module Loading Strategy**:

Modules are loaded dynamically based on tenant subscription:

```typescript
// 1. ON LOGIN: Get user's subscriptions from backend
const loginResponse = await api.login(credentials)
// Response includes:
// {
//   user: {...},
//   tenantMemberships: [
//     {
//       tenant_id: "hotel-001",
//       role: "owner",
//       tenant_subscriptions: [
//         { app_code: "PMS", subscription_status: "active", is_enabled: true },
//         { app_code: "ACC", subscription_status: "active", is_enabled: true },
//         { app_code: "INV", subscription_status: "inactive", is_enabled: false }
//       ]
//     }
//   ]
// }

// 2. BUILD AVAILABLE MODULES (client-side)
const activeTenant = loginResponse.tenantMemberships[0]
const availableModules = []
for (const sub of activeTenant.tenant_subscriptions) {
  if (sub.subscription_status === 'active' && sub.is_enabled) {
    availableModules.push(sub.app_code)  // PMS, ACC, INV, etc.
  }
}

// 3. LAZY LOAD ONLY AVAILABLE MODULES
const moduleRoutes = {
  PMS: () => import('./modules/pms').then(m => ({ Component: m.PMSModule })),
  ACC: () => import('./modules/accounting').then(m => ({ Component: m.AccountingModule })),
  INV: () => import('./modules/inventory').then(m => ({ Component: m.InventoryModule })),
  // ... other modules
}

// 4. BUILD ROUTER DYNAMICALLY
const routes = availableModules.map(code => ({
  path: code.toLowerCase(),
  lazy: moduleRoutes[code]
}))

// 5. HANDLE "NOT SUBSCRIBED"
// If user tries to access /pms but PMS not subscribed:
// Route guard checks subscriptions → shows "Not Subscribed" page
```

**Important**:
- Module code is available in frontend (just hidden via routing)
- Authorization enforced on backend API (not frontend)
- Frontend shows "Not Subscribed" if user manually navigates to disabled route
- Real access control check happens on API calls (backend always enforces)

---

### React Router 6+

**Problem Solved:**
- SPA routing
- Navigation guards
- Lazy loading routes
- State management across navigation

**Why Chosen:**
- Most popular React router
- Great TypeScript support
- Loaders & actions for data fetching
- Excellent DX

**Usage:**
```typescript
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useNavigate
} from 'react-router-dom'

// 1. DEFINE ROUTES
const router = createBrowserRouter([
  {
    path: '/',
    element: <Landing />
  },
  {
    path: '/auth',
    element: <AuthLayout />,
    children: [
      { path: 'login', element: <Login /> },
      { path: 'register', element: <Register /> }
    ]
  },
  {
    path: '/app',
    element: <ProtectedRoute><AppShell /></ProtectedRoute>,
    children: [
      { path: 'dashboard', element: <Dashboard /> },
      {
        path: 'pms',
        lazy: () => import('./modules/pms').then(m => ({
          Component: m.PMSModule
        }))
      },
      {
        path: 'accounting',
        lazy: () => import('./modules/accounting').then(m => ({
          Component: m.AccountingModule
        }))
      }
    ]
  },
  {
    path: '*',
    element: <NotFound />
  }
])

// 2. PROTECTED ROUTE
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, activeTenantId } = useAppContext()
  const navigate = useNavigate()

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" replace />
  }

  if (!activeTenantId) {
    return <Navigate to="/auth/select-tenant" replace />
  }

  return <>{children}</>
}

// 3. USE IN APP
export function App() {
  return <RouterProvider router={router} />
}

// 4. PROGRAMMATIC NAVIGATION
function NavItem({ to, label }: { to: string; label: string }) {
  const navigate = useNavigate()

  return (
    <button onClick={() => navigate(to)}>
      {label}
    </button>
  )
}

// 5. ROUTE PARAMETERS
function ReservationDetail() {
  const { id } = useParams<{ id: string }>()
  const { data } = useQuery({
    queryKey: ['reservation', id],
    queryFn: () => api.getReservation(parseInt(id!))
  })

  return <div>{data?.guestName}</div>
}
```

**Best Practices:**
- Lazy load heavy modules
- Protect routes before rendering
- Use loaders for data fetching before render
- Handle not found routes

---

### Centrifuge JS

**Problem Solved:**
- Real-time updates via WebSocket
- Publish/subscribe messaging
- Live notifications

**Why Chosen:**
- Language-agnostic protocol
- Automatic reconnection
- Works with any backend
- Small bundle size

**Usage:**
```typescript
import { Centrifuge } from 'centrifuge'

// 1. CREATE CLIENT
const centrifuge = new Centrifuge(
  `ws://${location.host}/connection/websocket`,
  {
    token: getAuthToken()
  }
)

// 2. LISTEN TO EVENTS
centrifuge.on('connect', () => {
  console.log('Connected')
})

centrifuge.on('disconnect', (ctx) => {
  console.log('Disconnected:', ctx.reason)
})

// 3. SUBSCRIBE TO CHANNEL
function RoomStatusMonitor({ roomId }: { roomId: number }) {
  const [status, setStatus] = useState('available')

  useEffect(() => {
    const sub = centrifuge.newSubscription(`room:${roomId}`)

    sub.on('subscribe', () => {
      console.log('Subscribed to room updates')
    })

    sub.on('publication', (ctx) => {
      const { data } = ctx
      // Receive update: { status: 'occupied', updatedBy: 'user123' }
      setStatus(data.status)
    })

    sub.on('error', (ctx) => {
      console.error('Subscription error:', ctx.error)
    })

    sub.subscribe()

    return () => sub.unsubscribe()
  }, [roomId])

  return <div>Room Status: {status}</div>
}

// 4. PUBLISH EVENT
async function updateRoomStatus(roomId: number, status: string) {
  await centrifuge.publish(`room:${roomId}`, {
    status,
    updatedAt: new Date().toISOString()
  })
}

// 5. MULTI-TENANT CHANNELS
useEffect(() => {
  const { tenantId } = useAppContext()

  // Subscribe to tenant-specific channel
  const sub = centrifuge.newSubscription(`tenant:${tenantId}:notifications`)
  sub.subscribe()

  return () => sub.unsubscribe()
}, [tenantId])
```

**Best Practices:**
```typescript
// ✅ DO: Send only deltas, not full data
publish('room:123', {
  status: 'occupied',  // ← Changed field
  updatedAt: '2024-01-01T12:00:00Z'
})

// ❌ DON'T: Send entire object
publish('room:123', {
  id: 123,
  number: 'A101',
  type: 'double',
  status: 'occupied',
  maxGuests: 2,
  // ... more fields ...
})

// ✅ DO: Use TanStack Query to fetch initial data
const { data: room } = useQuery(...)

// ✅ DO: Update query cache on realtime update
centrifuge.on('publication', (ctx) => {
  queryClient.setQueryData(['room', roomId], (old) => ({
    ...old,
    status: ctx.data.status
  }))
})
```

---

## Anti-Patterns (DO NOT DO)

```typescript
// ❌ ANTI-PATTERN #1: Manual fetching with useEffect
const [reservations, setReservations] = useState([])

useEffect(() => {
  api.getReservations().then(setReservations)
}, [])  // ← Missing dependencies!

// ✅ USE: TanStack Query
const { data: reservations } = useQuery({
  queryKey: ['reservations', tenantId],
  queryFn: () => api.getReservations(tenantId)
})

---

// ❌ ANTI-PATTERN #2: Storing business data in Zustand
const useStore = create((set) => ({
  reservations: [],  // ← Should be in React Query
  setReservations: (data) => set({ reservations: data })
}))

// ✅ USE: React Query for server data
const { data: reservations } = useQuery({
  queryKey: ['reservations'],
  queryFn: () => api.getReservations()
})

---

// ❌ ANTI-PATTERN #3: Rendering large tables without virtualization
{reservations.map(res => (
  <div key={res.id}>{res.guestName}</div>
))}
// ← If > 500 items, will be slow

// ✅ USE: TanStack Virtual
const virtualizer = useVirtualizer({
  count: reservations.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 50
})

---

// ❌ ANTI-PATTERN #4: SQL logic in frontend
const ledgerTotal = ledger
  .filter(entry => entry.status === 'posted')
  .reduce((sum, entry) => sum + entry.amount, 0)

// ✅ USE: Semantic layer (backend API)
const { data: total } = useQuery({
  queryKey: ['ledger', 'total', filters],
  queryFn: () => api.getLedgerTotal(filters)
})

---

// ❌ ANTI-PATTERN #5: Using fetch directly
useEffect(() => {
  fetch('/api/data')
    .then(r => r.json())
    .then(setData)
    .catch(setError)
}, [])

// ✅ USE: Consistent HTTP client
const client = createClient({
  baseURL: '/api',
  timeout: 30000,
  interceptors: {
    request: (config) => ({
      ...config,
      headers: {
        ...config.headers,
        'X-Tenant-ID': tenantId
      }
    })
  }
})
```

---

## Performance Checklist

- [ ] Code splitting: Lazy load routes & components
- [ ] Bundle size: `npm run build` < 500KB (gzipped)
- [ ] Images: Use WebP with fallback
- [ ] Tables: Use virtualization for > 500 rows
- [ ] Forms: Use React Hook Form for large forms
- [ ] Queries: Set appropriate `staleTime` & `gcTime`
- [ ] Re-renders: Monitor with React DevTools Profiler
- [ ] Metrics: Track Core Web Vitals

---

## Testing Strategy

```typescript
// Unit: Component tests with Vitest
describe('ReservationCard', () => {
  it('renders guest name', () => {
    const { getByText } = render(
      <ReservationCard reservation={mockReservation} />
    )
    expect(getByText('John Doe')).toBeInTheDocument()
  })
})

// Integration: Query + component
describe('ReservationList', () => {
  it('fetches and displays reservations', async () => {
    const { getByText } = render(<ReservationList />)

    await waitFor(() => {
      expect(getByText('John Doe')).toBeInTheDocument()
    })
  })
})

// E2E: Full user flow
cy.visit('/app/reservations')
cy.contains('Create').click()
cy.get('[name="guestName"]').type('John Doe')
cy.get('[type="submit"]').click()
cy.contains('John Doe').should('exist')
```

---

## Summary

| Library | Purpose | When to Use |
|---------|---------|------------|
| **React** | UI rendering | Always |
| **Vite** | Build tool | Always |
| **TypeScript** | Type safety | Always |
| **Tailwind** | Styling | Always |
| **TanStack Query** | Server state | API data |
| **Zustand** | Client state | UI state only |
| **TanStack Table** | Data tables | Complex tables |
| **TanStack Virtual** | Big data | > 500 rows |
| **React Hook Form** | Forms | Forms with validation |
| **Zod** | Validation | Schemas & API responses |
| **React Router** | Routing | SPA routing |
| **Centrifuge** | Realtime | Live updates |

---

**Related Documents:**
- ARCH-05: Frontend Architecture (architecture patterns)
- ARCH-07: Design Patterns (UI patterns & concepts)
- STD-02: Frontend-Backend Validation (validation standards)
