# Smart TV Signage - Modular Refactoring Skill

**Type:** Reusable Project Maintenance Skill
**Project:** Smart TV Digital Signage System
**Purpose:** Guide for modular refactoring, code organization, and maintenance

---

## 🎯 SKILL OBJECTIVES

This skill provides consistent guidelines for:
1. Refactoring monolithic components into modular architecture
2. Maintaining code quality and consistency
3. Implementing new features following project standards
4. Debugging and fixing issues systematically

---

## 📐 PROJECT ARCHITECTURE STANDARDS

### Directory Structure (Web Admin)

```
web-admin/src/
├── pages/                          # Main page containers (150-250 lines max)
│   ├── Content.jsx                 # Content management page
│   ├── Devices.jsx                 # Device management page
│   ├── Tags.jsx                    # Tag management page
│   └── Dashboard.jsx               # Dashboard overview
│
├── components/
│   ├── common/                     # Reusable UI components
│   │   ├── Button.jsx              # Custom button variants
│   │   ├── Modal.jsx               # Base modal component
│   │   ├── Card.jsx                # Card layout
│   │   ├── Badge.jsx               # Status badges
│   │   ├── Table.jsx               # Data table
│   │   ├── Checkbox.jsx            # Checkbox with label
│   │   ├── EmptyState.jsx          # Empty state placeholder
│   │   └── LoadingSpinner.jsx      # Loading indicators
│   │
│   ├── content/                    # Content-specific components
│   │   ├── ContentCard.jsx         # Single content item
│   │   ├── VideoThumbnail.jsx      # Video thumbnail
│   │   ├── AssignmentBadge.jsx     # Assignment info badge
│   │   ├── ContentGrid.jsx         # Content grid layout
│   │   ├── ContentFilters.jsx      # Filter controls
│   │   ├── SelectionBar.jsx        # Bulk selection bar
│   │   ├── modals/
│   │   │   ├── UploadModal.jsx
│   │   │   ├── EditModal.jsx
│   │   │   ├── AssignModal.jsx
│   │   │   ├── PreviewModal.jsx
│   │   │   ├── BulkEditModal.jsx
│   │   │   └── BulkTagModal.jsx
│   │   └── forms/
│   │       ├── ContentForm.jsx
│   │       ├── AssignmentForm.jsx
│   │       └── BulkActionForm.jsx
│   │
│   ├── devices/                    # Device-specific components
│   │   ├── DeviceCard.jsx
│   │   ├── DeviceGrid.jsx
│   │   ├── DeviceStatusBadge.jsx
│   │   ├── DeviceFilters.jsx
│   │   └── modals/
│   │       ├── TVRegisterModal.jsx
│   │       ├── AssignContentModal.jsx
│   │       └── DeviceInfoModal.jsx
│   │
│   └── Layout.jsx                  # Main layout wrapper
│
├── hooks/                          # Custom React hooks
│   ├── useContent.js               # Content CRUD operations
│   ├── useDevices.js               # Device operations
│   ├── useTags.js                  # Tag operations
│   ├── useModal.js                 # Modal state management
│   ├── useSelection.js             # Bulk selection logic
│   └── useDebounce.js              # Debounced inputs
│
├── services/
│   ├── api/                        # API layer (separated by resource)
│   │   ├── content.api.js
│   │   ├── devices.api.js
│   │   ├── tags.api.js
│   │   └── index.js
│   └── api.js                      # Base axios configuration
│
└── utils/                          # Utility functions
    ├── formatters.js               # Date, size, duration formatting
    ├── validators.js               # Form validation
    ├── constants.js                # App constants
    └── helpers.js                  # Helper functions
```

---

## 🔧 COMPONENT DESIGN PRINCIPLES

### 1. Single Responsibility Principle
- **One component = One purpose**
- Max 150-250 lines per component
- If larger, break into sub-components

### 2. Component Composition
```jsx
// ❌ BAD: Monolithic component
function Content() {
  return (
    <div>
      {/* 2000+ lines of mixed logic and UI */}
    </div>
  )
}

// ✅ GOOD: Composed components
function Content() {
  return (
    <>
      <ContentFilters />
      <ContentGrid />
      <Modals />
    </>
  )
}
```

### 3. Separation of Concerns

**Pages (Container Components):**
- Coordinate data flow
- Handle routing
- Manage global state
- Minimal UI logic

**UI Components:**
- Pure presentational
- Receive props, render UI
- No API calls
- No business logic

**Hooks:**
- Data fetching
- State management
- Side effects
- Business logic

---

## 📝 NAMING CONVENTIONS

### Files & Folders
```
✅ CORRECT:
- components/content/ContentCard.jsx        # PascalCase for components
- hooks/useContent.js                       # camelCase with 'use' prefix
- services/api/content.api.js               # camelCase with .api suffix
- utils/formatters.js                       # camelCase for utilities

❌ WRONG:
- components/content/contentCard.jsx
- hooks/ContentHook.js
- services/api/ContentAPI.js
```

### Components
```jsx
// ✅ Descriptive, specific names
<ContentCard />
<DeviceStatusBadge />
<UploadModal />

// ❌ Generic, unclear names
<Card />
<Badge />
<Modal />
```

### Functions & Variables
```jsx
// ✅ Clear, descriptive
const handleUploadContent = () => {}
const selectedContentIds = []
const isUploadModalOpen = false

// ❌ Unclear, abbreviated
const handleUpload = () => {}
const selected = []
const isOpen = false
```

---

## 🔄 REFACTORING WORKFLOW

### Step 1: Analyze Component
```bash
# Check file size
wc -l src/pages/Content.jsx

# Identify sub-components
grep "^function\|^const.*= (" src/pages/Content.jsx
```

### Step 2: Plan Extraction
```markdown
Current: Content.jsx (2142 lines)
├── VideoThumbnail (96 lines)       → components/content/VideoThumbnail.jsx
├── AssignmentBadge (18 lines)      → components/content/AssignmentBadge.jsx
├── UploadForm (197 lines)          → components/content/modals/UploadModal.jsx
├── AssignForm (364 lines)          → components/content/modals/AssignModal.jsx
├── ModalVideoPlayer (89 lines)     → components/content/modals/VideoPlayer.jsx
├── PreviewModal (242 lines)        → components/content/modals/PreviewModal.jsx
├── BulkEditForm (265 lines)        → components/content/modals/BulkEditModal.jsx
└── BulkTagForm (285 lines)         → components/content/modals/BulkTagModal.jsx
```

### Step 3: Extract One Component at a Time

**Template:**
```jsx
// 1. Create new file
// components/content/VideoThumbnail.jsx

import { useState } from 'react'

export default function VideoThumbnail({ content }) {
  // Move component logic here
  return (
    // Move JSX here
  )
}

// 2. Update original file
// pages/Content.jsx

import VideoThumbnail from '../components/content/VideoThumbnail'

export default function Content() {
  return (
    <div>
      <VideoThumbnail content={item} />
    </div>
  )
}

// 3. Test immediately after extraction
// - Does it render correctly?
// - Are props passed correctly?
// - Does it work as before?
```

### Step 4: Extract Hooks
```jsx
// hooks/useContent.js

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { contentAPI } from '../services/api'

export function useContent() {
  const queryClient = useQueryClient()

  // Fetch content list
  const { data: content, isLoading } = useQuery({
    queryKey: ['content'],
    queryFn: contentAPI.getAll
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: contentAPI.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['content'])
    }
  })

  return {
    content: content?.items || [],
    isLoading,
    create: createMutation.mutate,
    // ... other operations
  }
}
```

### Step 5: Clean Up
- Remove unused imports
- Remove dead code
- Update prop-types/TypeScript types
- Add comments where needed

---

## ✅ CODE QUALITY CHECKLIST

### Before Committing
- [ ] File is under 250 lines
- [ ] Component has single responsibility
- [ ] No business logic in UI components
- [ ] Props are validated (PropTypes or TypeScript)
- [ ] No console.log in production code
- [ ] Error handling is implemented
- [ ] Loading states are handled
- [ ] Component is tested manually

### Component Quality
- [ ] Descriptive name
- [ ] Clear props interface
- [ ] Proper error boundaries
- [ ] Accessibility attributes (aria-*)
- [ ] Responsive design
- [ ] Performance optimized (useMemo, useCallback if needed)

### Hook Quality
- [ ] Starts with 'use' prefix
- [ ] Returns consistent interface
- [ ] Handles loading/error states
- [ ] Cleans up side effects
- [ ] Dependencies are correct

---

## 🐛 DEBUGGING GUIDELINES

### When Content/Tags Disappear
1. Check API endpoint first
   ```bash
   curl -s http://192.168.5.12:8001/api/content/ | python3 -m json.tool
   curl -s http://192.168.5.12:8001/api/tags | python3 -m json.tool
   ```

2. Check backend logs
   ```bash
   docker logs signage-backend --tail 50
   ```

3. Check for schema/model mismatches
   - Database columns vs Model fields
   - Pydantic schema vs Database fields
   - Optional fields need default values

### When Components Break After Refactoring
1. Check import paths
   ```jsx
   // ❌ Wrong relative path
   import Button from '../../common/Button'

   // ✅ Use absolute imports
   import Button from '@/components/common/Button'
   ```

2. Check props passing
   ```jsx
   // Parent must pass all required props
   <ContentCard
     content={item}        // ✅
     onSelect={handleSelect} // ✅
     // missing: onDelete  ❌
   />
   ```

3. Check state management
   - Is state lifted to correct parent?
   - Are callbacks properly bound?
   - Is React Query cache invalidated?

---

## 🚀 IMPLEMENTATION PHASES

### Phase 1: Infrastructure (2 hours)
1. Create folder structure
2. Setup barrel exports (index.js)
3. Create base common components:
   - Button, Modal, Card, Badge, Table
4. Create utility functions
5. Test base components

### Phase 2: Extract Common Logic (2 hours)
1. Create custom hooks:
   - useContent, useDevices, useTags
   - useModal, useSelection
2. Move API calls to services/api/
3. Test hooks independently

### Phase 3: Refactor Content.jsx (6 hours)
Priority order:
1. Extract VideoThumbnail (simple, no dependencies)
2. Extract AssignmentBadge (simple)
3. Extract modals (medium complexity):
   - PreviewModal
   - UploadModal
   - AssignModal
   - BulkEditModal
   - BulkTagModal
4. Create ContentGrid component
5. Create ContentFilters component
6. Simplify Content.jsx to container
7. **Test after each extraction**

### Phase 4: Refactor Devices.jsx (4 hours)
1. Extract DeviceCard
2. Extract modals
3. Create DeviceGrid
4. Create DeviceFilters
5. Simplify Devices.jsx

### Phase 5: Testing & Polish (2 hours)
1. Full integration test
2. Fix any bugs
3. Update documentation
4. Performance check

---

## 📦 COMPONENT TEMPLATES

### Page Container Template
```jsx
import { useState } from 'react'
import ItemGrid from '../components/[resource]/ItemGrid'
import ItemFilters from '../components/[resource]/ItemFilters'
import CreateModal from '../components/[resource]/modals/CreateModal'
import { use[Resource] } from '../hooks/use[Resource]'

export default function [ResourcePage]() {
  const { items, isLoading, create, update, delete } = use[Resource]()
  const [showCreateModal, setShowCreateModal] = useState(false)

  if (isLoading) return <LoadingSpinner />

  return (
    <div>
      <ItemFilters />
      <ItemGrid items={items} />

      {showCreateModal && (
        <CreateModal
          onClose={() => setShowCreateModal(false)}
          onSubmit={create}
        />
      )}
    </div>
  )
}
```

### UI Component Template
```jsx
export default function ComponentName({
  prop1,
  prop2,
  onAction
}) {
  return (
    <div>
      {/* Pure presentational UI */}
    </div>
  )
}
```

### Modal Template
```jsx
import Modal from '../../common/Modal'

export default function [Feature]Modal({
  data,
  onClose,
  onSubmit
}) {
  const [formData, setFormData] = useState(data || {})

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await onSubmit(formData)
      onClose()
    } catch (error) {
      // Handle error
    }
  }

  return (
    <Modal onClose={onClose}>
      <form onSubmit={handleSubmit}>
        {/* Form fields */}
      </form>
    </Modal>
  )
}
```

### Custom Hook Template
```jsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { [resource]API } from '../services/api'

export function use[Resource]() {
  const queryClient = useQueryClient()

  // Queries
  const { data, isLoading } = useQuery({
    queryKey: ['[resource]'],
    queryFn: [resource]API.getAll
  })

  // Mutations
  const createMutation = useMutation({
    mutationFn: [resource]API.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['[resource]'])
    }
  })

  return {
    items: data?.items || [],
    isLoading,
    create: createMutation.mutate,
    // ...
  }
}
```

---

## 🎓 BEST PRACTICES

### 1. Always Test After Changes
```bash
# Start dev server
cd web-admin && npm run dev

# Manual testing checklist:
# - Navigate to affected page
# - Test all interactive elements
# - Check console for errors
# - Test edge cases (empty data, errors)
```

### 2. Keep Components Focused
```jsx
// ❌ Component doing too much
function ContentCard() {
  const [content] = useState()
  const [devices] = useState()
  const [tags] = useState()
  // API calls, business logic, UI all mixed
}

// ✅ Focused component
function ContentCard({ content, onSelect, onDelete }) {
  // Only UI and user interaction
  return <div>...</div>
}
```

### 3. Use Composition
```jsx
// ❌ Props drilling
<Parent>
  <Child prop1={x} prop2={y} prop3={z} prop4={a} prop5={b} />
</Parent>

// ✅ Composition
<Parent>
  <Child>
    <Section1 />
    <Section2 />
  </Child>
</Parent>
```

### 4. Extract Repeated Logic
```jsx
// ❌ Repeated code
function Content() {
  const formatDate = (date) => new Date(date).toLocaleDateString()
  const formatSize = (bytes) => `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

function Devices() {
  const formatDate = (date) => new Date(date).toLocaleDateString()
}

// ✅ Shared utility
// utils/formatters.js
export const formatDate = (date) => new Date(date).toLocaleDateString()
export const formatSize = (bytes) => `${(bytes / 1024 / 1024).toFixed(2)} MB`
```

---

## ⚠️ COMMON PITFALLS TO AVOID

### 1. Circular Dependencies
```jsx
// ❌ BAD
// A.jsx imports B.jsx
// B.jsx imports A.jsx

// ✅ GOOD
// Extract shared logic to separate file
// shared.js exports common functions
// A.jsx and B.jsx import from shared.js
```

### 2. Prop Drilling Hell
```jsx
// ❌ Passing props through 5+ levels
<Level1 data={data}>
  <Level2 data={data}>
    <Level3 data={data}>
      <Level4 data={data}>
        <Level5 data={data} />
      </Level4>
    </Level3>
  </Level2>
</Level1>

// ✅ Use Context or state management
const DataContext = createContext()
<DataProvider value={data}>
  <Level5 /> {/* Uses useContext(DataContext) */}
</DataProvider>
```

### 3. Premature Optimization
```jsx
// ❌ Over-optimizing before measuring
const MemoizedEverything = React.memo(
  useMemo(() =>
    useCallback(() => { ... }, [])
  , [])
)

// ✅ Optimize when needed
// 1. Measure performance first
// 2. Identify bottlenecks
// 3. Then optimize
```

---

## 📚 REFERENCES

### File Size Limits
- Page containers: 150-250 lines
- UI components: 100-200 lines
- Modals: 150-300 lines
- Hooks: 100-250 lines
- Utilities: 50-150 lines

### Import Order
```jsx
// 1. React imports
import { useState, useEffect } from 'react'

// 2. Third-party libraries
import { useQuery } from '@tanstack/react-query'

// 3. Internal imports (absolute paths)
import Button from '@/components/common/Button'
import { useContent } from '@/hooks/useContent'
import { contentAPI } from '@/services/api'

// 4. Relative imports (same directory)
import styles from './styles.module.css'
```

---

## 🎯 SKILL ACTIVATION

### When to Use This Skill

1. **Refactoring large files** (>500 lines)
   - Invoke: "Use signage-refactor skill to refactor Content.jsx"

2. **Adding new features**
   - Invoke: "Use signage-refactor skill to add [feature] following modular standards"

3. **Fixing bugs systematically**
   - Invoke: "Use signage-refactor skill debugging guidelines for [issue]"

4. **Code review**
   - Invoke: "Use signage-refactor skill to review [component] quality"

### Skill Invocation Examples

```
"Refactor Content.jsx following signage-refactor skill guidelines"
"Add device tagging feature using signage-refactor skill patterns"
"Debug missing content issue using signage-refactor skill checklist"
"Review Devices.jsx component quality with signage-refactor skill"
```

---

## 🔄 SKILL MAINTENANCE

This skill document should be updated when:
- Project structure changes significantly
- New patterns emerge
- Best practices evolve
- Common issues are discovered

**Last Updated:** 2025-10-23
**Version:** 1.0.0
**Maintainer:** Claude AI for Smart TV Signage Project
