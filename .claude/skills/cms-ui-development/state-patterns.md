# State Management & Performance Patterns

Complete guide for state management, dark mode, and performance optimization.

## State Management Overview

| Type | Technology | Use Case |
|------|------------|----------|
| Global UI State | Zustand | Auth, theme, sidebar, toasts |
| Server State | TanStack Query | API data, caching, sync |
| Form State | React Hook Form | Form inputs, validation |
| Local State | useState | Component-specific state |

---

## Zustand - Global State

### Store Structure

```
cms-vite/src/lib/stores/
├── authStore.ts      # Authentication state
├── uiStore.ts        # UI preferences (theme, sidebar)
└── index.ts          # Re-export all stores
```

### Auth Store (existing)

```typescript
// cms-vite/src/lib/stores/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  organization_id: number;
  permissions: string[];
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      setAuth: (user, token) => {
        set({ user, token, isAuthenticated: true });
      },

      clearAuth: () => {
        set({ user: null, token: null, isAuthenticated: false });
      },

      hasPermission: (permission) => {
        const { user } = get();
        if (!user) return false;
        // Super admin has all permissions
        if (user.role === 'SUPER_ADMIN') return true;
        return user.permissions.includes(permission);
      },

      hasRole: (role) => {
        const { user } = get();
        return user?.role === role;
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Convenience hook
export function useAuth() {
  const store = useAuthStore();
  return {
    user: store.user,
    token: store.token,
    isAuthenticated: store.isAuthenticated,
    login: store.setAuth,
    logout: store.clearAuth,
    hasPermission: store.hasPermission,
    hasRole: store.hasRole,
  };
}
```

### UI Store (with Dark Mode)

```typescript
// cms-vite/src/lib/stores/uiStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'light' | 'dark' | 'system';

interface UIState {
  // Theme
  theme: Theme;
  setTheme: (theme: Theme) => void;

  // Sidebar
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;

  // Mobile menu
  mobileMenuOpen: boolean;
  setMobileMenuOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      // Theme
      theme: 'system',
      setTheme: (theme) => {
        set({ theme });
        applyTheme(theme);
      },

      // Sidebar
      sidebarCollapsed: false,
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

      // Mobile menu
      mobileMenuOpen: false,
      setMobileMenuOpen: (open) => set({ mobileMenuOpen: open }),
    }),
    {
      name: 'ui-storage',
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
);

// Apply theme to document
function applyTheme(theme: Theme) {
  const root = document.documentElement;
  root.classList.remove('light', 'dark');

  if (theme === 'system') {
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
    root.classList.add(systemTheme);
  } else {
    root.classList.add(theme);
  }
}

// Initialize theme on app start
export function initializeTheme() {
  const stored = localStorage.getItem('ui-storage');
  if (stored) {
    const { state } = JSON.parse(stored);
    applyTheme(state.theme || 'system');
  }
}
```

---

## TanStack Query - Server State

### Query Client Setup

```typescript
// cms-vite/src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000, // 30 seconds
      gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});
```

### Query Keys Factory Pattern

```typescript
// cms-vite/src/features/[feature]/hooks/use[Features].ts

// ALWAYS use factory pattern for query keys
export const featureKeys = {
  all: ['features'] as const,
  lists: () => [...featureKeys.all, 'list'] as const,
  list: (params: QueryParams) => [...featureKeys.lists(), params] as const,
  details: () => [...featureKeys.all, 'detail'] as const,
  detail: (id: number) => [...featureKeys.details(), id] as const,
};

// Usage
const { data } = useQuery({
  queryKey: featureKeys.list({ page: 1, search: 'test' }),
  queryFn: () => featureApi.getList({ page: 1, search: 'test' }),
});

// Invalidation
queryClient.invalidateQueries({ queryKey: featureKeys.all });
queryClient.invalidateQueries({ queryKey: featureKeys.lists() });
queryClient.invalidateQueries({ queryKey: featureKeys.detail(123) });
```

### Data Fetching Hook

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/lib/stores/authStore';
import { featureApi } from '../api/feature.api';
import { toast } from 'sonner';

export function useFeatures(params?: QueryParams) {
  const { user } = useAuth();
  const orgId = user?.organization_id;

  return useQuery({
    // IMPORTANT: Include orgId in query key for proper caching per organization
    queryKey: [...featureKeys.list(params || {}), orgId],
    queryFn: () => featureApi.getList(params),
    enabled: !!orgId, // Only fetch when authenticated
    staleTime: 30 * 1000,
    placeholderData: (previousData) => previousData, // Keep previous data while loading
  });
}

export function useFeature(id: number | undefined) {
  return useQuery({
    queryKey: featureKeys.detail(id!),
    queryFn: () => featureApi.getById(id!),
    enabled: !!id,
  });
}

export function useFeatureMutations() {
  const queryClient = useQueryClient();

  const invalidateFeatures = () => {
    queryClient.invalidateQueries({ queryKey: featureKeys.all });
  };

  const createMutation = useMutation({
    mutationFn: featureApi.create,
    onSuccess: () => {
      invalidateFeatures();
      toast.success('Feature created successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to create');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateData }) =>
      featureApi.update(id, data),
    onSuccess: () => {
      invalidateFeatures();
      toast.success('Feature updated successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to update');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: featureApi.delete,
    onSuccess: () => {
      invalidateFeatures();
      toast.success('Feature deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to delete');
    },
  });

  return {
    create: createMutation.mutate,
    update: updateMutation.mutate,
    delete: deleteMutation.mutate,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
```

---

## Dark Mode Implementation

### 1. Tailwind Config

```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        // Use CSS variables for theme colors
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
      },
    },
  },
};
```

### 2. CSS Variables

```css
/* cms-vite/src/index.css */
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}
```

### 3. Theme Toggle Component

```typescript
// cms-vite/src/shared/components/ThemeToggle.tsx
import { Moon, Sun, Monitor } from 'lucide-react';
import { Button } from '@/shared/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/components/ui/dropdown-menu';
import { useUIStore } from '@/lib/stores/uiStore';

export function ThemeToggle() {
  const { theme, setTheme } = useUIStore();

  const Icon = theme === 'dark' ? Moon : theme === 'light' ? Sun : Monitor;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <Icon className="h-5 w-5" />
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => setTheme('light')}>
          <Sun className="mr-2 h-4 w-4" />
          Light
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('dark')}>
          <Moon className="mr-2 h-4 w-4" />
          Dark
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('system')}>
          <Monitor className="mr-2 h-4 w-4" />
          System
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

### 4. Initialize Theme in App

```typescript
// cms-vite/src/main.tsx
import { initializeTheme } from '@/lib/stores/uiStore';

// Initialize theme before React renders
initializeTheme();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

---

## Performance Patterns

### 1. Debounced Search

```typescript
// cms-vite/src/shared/hooks/useDebounce.ts
import { useState, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// Usage in component
function SearchComponent() {
  const [searchInput, setSearchInput] = useState('');
  const debouncedSearch = useDebounce(searchInput, 300);

  // Fetch only triggers when debouncedSearch changes
  const { data } = useFeatures({ search: debouncedSearch });

  return (
    <Input
      value={searchInput}
      onChange={(e) => setSearchInput(e.target.value)}
      placeholder="Search..."
    />
  );
}
```

### 2. Lazy Loading Routes

```typescript
// cms-vite/src/routes/index.tsx
import { lazy, Suspense } from 'react';
import { PageSkeleton } from '@/shared/components/feedback/PageSkeleton';

// Lazy load pages
const DevicesPage = lazy(() => import('@/features/devices/pages/DevicesPage'));
const ContentsPage = lazy(() => import('@/features/contents/pages/ContentsPage'));
const PlaylistsPage = lazy(() => import('@/features/playlists/pages/PlaylistsPage'));

// Wrap with Suspense
export const routes = [
  {
    path: '/devices',
    element: (
      <Suspense fallback={<PageSkeleton />}>
        <DevicesPage />
      </Suspense>
    ),
  },
  {
    path: '/contents',
    element: (
      <Suspense fallback={<PageSkeleton />}>
        <ContentsPage />
      </Suspense>
    ),
  },
  // ...
];
```

### 3. Virtual Scrolling for Long Lists

```typescript
// Using @tanstack/react-virtual
import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef } from 'react';

interface VirtualListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  itemHeight: number;
}

export function VirtualList<T>({
  items,
  renderItem,
  itemHeight,
}: VirtualListProps<T>) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => itemHeight,
    overscan: 5,
  });

  return (
    <div
      ref={parentRef}
      className="h-[500px] overflow-auto"
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            {renderItem(items[virtualItem.index], virtualItem.index)}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 4. Memoization

```typescript
import { useMemo, useCallback, memo } from 'react';

// Memoize expensive calculations
const expensiveData = useMemo(() => {
  return items.filter(/* complex filter */).map(/* complex transform */);
}, [items]);

// Memoize callbacks passed to children
const handleClick = useCallback((id: number) => {
  // handle click
}, [/* dependencies */]);

// Memoize components that receive same props
const MemoizedRow = memo(function Row({ item }: { item: Item }) {
  return <div>{item.name}</div>;
});
```

---

## UX Patterns

### 1. Optimistic Updates

```typescript
function useFeatureMutations() {
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: featureApi.delete,

    // Optimistic update
    onMutate: async (id: number) => {
      // Cancel outgoing queries
      await queryClient.cancelQueries({ queryKey: featureKeys.lists() });

      // Snapshot previous data
      const previousFeatures = queryClient.getQueryData(featureKeys.lists());

      // Optimistically remove from cache
      queryClient.setQueryData(featureKeys.lists(), (old: any) => ({
        ...old,
        items: old.items.filter((item: Feature) => item.id !== id),
      }));

      // Return snapshot for rollback
      return { previousFeatures };
    },

    // Rollback on error
    onError: (err, id, context) => {
      if (context?.previousFeatures) {
        queryClient.setQueryData(featureKeys.lists(), context.previousFeatures);
      }
      toast.error('Failed to delete');
    },

    // Refetch on success
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: featureKeys.all });
    },
  });

  return { delete: deleteMutation.mutate };
}
```

### 2. Bulk Actions

```typescript
function FeatureTable() {
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const { bulkDelete, isDeleting } = useFeatureMutations();

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(data.items.map((item) => item.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectOne = (id: number, checked: boolean) => {
    if (checked) {
      setSelectedIds((prev) => [...prev, id]);
    } else {
      setSelectedIds((prev) => prev.filter((i) => i !== id));
    }
  };

  const handleBulkDelete = () => {
    bulkDelete(selectedIds, {
      onSuccess: () => setSelectedIds([]),
    });
  };

  return (
    <div>
      {/* Bulk Actions Bar */}
      {selectedIds.length > 0 && (
        <div className="flex items-center gap-4 p-4 bg-muted rounded-lg mb-4">
          <span>{selectedIds.length} items selected</span>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleBulkDelete}
            disabled={isDeleting}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete Selected
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSelectedIds([])}
          >
            Clear Selection
          </Button>
        </div>
      )}

      {/* Table with checkboxes */}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[50px]">
              <Checkbox
                checked={selectedIds.length === data.items.length}
                onCheckedChange={handleSelectAll}
              />
            </TableHead>
            {/* ... other headers */}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.items.map((item) => (
            <TableRow key={item.id}>
              <TableCell>
                <Checkbox
                  checked={selectedIds.includes(item.id)}
                  onCheckedChange={(checked) =>
                    handleSelectOne(item.id, !!checked)
                  }
                />
              </TableCell>
              {/* ... other cells */}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
```

### 3. Drag & Drop (Playlist Items)

```typescript
// Using @hello-pangea/dnd (fork of react-beautiful-dnd)
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';

interface PlaylistItem {
  id: number;
  content_id: number;
  order: number;
}

function PlaylistEditor() {
  const [items, setItems] = useState<PlaylistItem[]>([]);

  const handleDragEnd = (result: any) => {
    if (!result.destination) return;

    const reordered = Array.from(items);
    const [removed] = reordered.splice(result.source.index, 1);
    reordered.splice(result.destination.index, 0, removed);

    // Update order values
    const updated = reordered.map((item, index) => ({
      ...item,
      order: index + 1,
    }));

    setItems(updated);
  };

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <Droppable droppableId="playlist-items">
        {(provided) => (
          <div
            {...provided.droppableProps}
            ref={provided.innerRef}
            className="space-y-2"
          >
            {items.map((item, index) => (
              <Draggable
                key={item.id}
                draggableId={item.id.toString()}
                index={index}
              >
                {(provided, snapshot) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.draggableProps}
                    {...provided.dragHandleProps}
                    className={cn(
                      'flex items-center gap-4 p-4 rounded-lg border',
                      snapshot.isDragging && 'shadow-lg bg-accent'
                    )}
                  >
                    <GripVertical className="h-5 w-5 text-muted-foreground" />
                    <span>{item.order}.</span>
                    <span>Content #{item.content_id}</span>
                  </div>
                )}
              </Draggable>
            ))}
            {provided.placeholder}
          </div>
        )}
      </Droppable>
    </DragDropContext>
  );
}
```

### 4. Infinite Scroll / Load More

```typescript
import { useInfiniteQuery } from '@tanstack/react-query';
import { useInView } from 'react-intersection-observer';
import { useEffect } from 'react';

function InfiniteFeatureList() {
  const { ref, inView } = useInView();

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteQuery({
    queryKey: ['features', 'infinite'],
    queryFn: ({ pageParam = 1 }) =>
      featureApi.getList({ page: pageParam, limit: 20 }),
    getNextPageParam: (lastPage, allPages) => {
      const nextPage = allPages.length + 1;
      return nextPage <= lastPage.pages ? nextPage : undefined;
    },
    initialPageParam: 1,
  });

  // Auto-fetch when scroll to bottom
  useEffect(() => {
    if (inView && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, isFetchingNextPage, fetchNextPage]);

  if (isLoading) return <TableSkeleton />;

  const allItems = data?.pages.flatMap((page) => page.items) || [];

  return (
    <div>
      {allItems.map((item) => (
        <FeatureCard key={item.id} item={item} />
      ))}

      {/* Load more trigger */}
      <div ref={ref} className="h-10 flex items-center justify-center">
        {isFetchingNextPage && <Loader2 className="h-6 w-6 animate-spin" />}
        {!hasNextPage && allItems.length > 0 && (
          <p className="text-muted-foreground">No more items</p>
        )}
      </div>
    </div>
  );
}
```

---

## Common Patterns Summary

| Pattern | When to Use | Technology |
|---------|-------------|------------|
| Global State | Auth, theme, sidebar | Zustand |
| Server State | API data | TanStack Query |
| Debounce | Search, resize | useDebounce hook |
| Lazy Loading | Routes, heavy components | React.lazy + Suspense |
| Virtual Scroll | Lists > 100 items | @tanstack/react-virtual |
| Memoization | Expensive renders | useMemo, useCallback, memo |
| Optimistic Update | Delete, toggle actions | TanStack Query onMutate |
| Bulk Actions | Multi-select tables | useState + useMutation |
| Drag & Drop | Reorderable lists | @hello-pangea/dnd |
| Infinite Scroll | Long lists | useInfiniteQuery + IntersectionObserver |
