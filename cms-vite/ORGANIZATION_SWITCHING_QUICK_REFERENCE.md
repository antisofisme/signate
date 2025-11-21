# Organization Switching - Quick Reference Guide

## For Developers

### Import Components

```tsx
// Organization switcher dropdown
import { OrganizationSwitcher } from '@/shared/components/layout';

// Context indicator badges
import {
  OrgContextIndicator,
  OrgContextBreadcrumb,
  OrgContextSidebarWidget,
} from '@/shared/components/layout';
```

### Import Hooks

```tsx
// Cache invalidation
import { useOrgSwitch } from '@/shared/hooks/useOrgSwitch';

// Enhanced auth hooks
import {
  useSwitchOrganization,
  useOrganizations,
  useUserPreferences,
} from '@/features/auth/hooks/useAuth';

// Keyboard shortcuts
import { useKeyboardShortcut } from '@/shared/hooks/useKeyboardShortcuts';
```

---

## Common Patterns

### 1. Add Organization Switcher to a Page

```tsx
import { OrganizationSwitcher } from '@/shared/components/layout';

export function MyPage() {
  return (
    <div>
      <OrganizationSwitcher />
      {/* Page content */}
    </div>
  );
}
```

### 2. Show Current Organization Badge

```tsx
import { OrgContextIndicator } from '@/shared/components/layout';

export function PageHeader() {
  return (
    <div className="flex items-center gap-4">
      <h1>Dashboard</h1>
      <OrgContextIndicator variant="chip" />
    </div>
  );
}
```

### 3. Invalidate Feature-Specific Caches

```tsx
import { useInvalidateOnOrgSwitch } from '@/shared/hooks/useOrgSwitch';

export function MyFeature() {
  // Invalidate custom query keys when org switches
  useInvalidateOnOrgSwitch(['my-feature-data', 'my-feature-stats']);

  return <div>{/* Feature content */}</div>;
}
```

### 4. Track Organization Switches

```tsx
import { useOrgSwitchCallback } from '@/shared/hooks/useOrgSwitch';

export function App() {
  useOrgSwitchCallback((event) => {
    console.log('Switched to:', event.organizationName);
    analytics.track('org_switch', { orgId: event.newOrgId });
  }, []);

  return <div>{/* App */}</div>;
}
```

### 5. Programmatic Organization Switch

```tsx
import { useSwitchOrganization } from '@/features/auth/hooks/useAuth';

export function QuickSwitcher() {
  const switchOrg = useSwitchOrganization();

  return (
    <button onClick={() => switchOrg(123)}>
      Switch to Org 123
    </button>
  );
}
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Open organization switcher |
| `Ctrl/Cmd + 1-9` | Quick switch to organization 1-9 |
| `Arrow Up/Down` | Navigate dropdown |
| `Enter` | Select organization |
| `Escape` | Close dropdown |

---

## Component Variants

### OrganizationSwitcher

```tsx
// Default
<OrganizationSwitcher />

// Show PIN
<OrganizationSwitcher showPin={true} />

// Compact (mobile)
<OrganizationSwitcherCompact />
```

### OrgContextIndicator

```tsx
// Badge (default)
<OrgContextIndicator />

// Chip
<OrgContextIndicator variant="chip" />

// Inline
<OrgContextIndicator variant="inline" />

// Compact (icon only)
<OrgContextIndicator variant="compact" />

// Interactive
<OrgContextIndicator
  interactive
  onClick={() => openSwitcher()}
/>
```

### Specialized Components

```tsx
// Breadcrumb format
<OrgContextBreadcrumb />

// Sidebar widget
<OrgContextSidebarWidget
  onSwitch={() => openSwitcher()}
/>
```

---

## Hook Configurations

### useOrgSwitch

```tsx
// Default (already in DashboardLayout)
useOrgSwitch();

// Custom config
useOrgSwitch({
  showToast: true,
  invalidateCaches: true,
  customQueryKeys: ['my-data'],
  debounceMs: 500,
  onBeforeSwitch: (event) => {
    console.log('Before switch');
  },
  onAfterSwitch: (event) => {
    console.log('After switch');
  },
});
```

### useKeyboardShortcut

```tsx
// Single shortcut
useKeyboardShortcut('k', () => setOpen(true), {
  ctrlOrCmd: true,
});

// Multiple modifiers
useKeyboardShortcut('s', saveDraft, {
  ctrlOrCmd: true,
  shift: true,
});
```

---

## State Management

### Access Auth Store

```tsx
import { useAuthStore } from '@/lib/stores/authStore';

const {
  organizations,
  selectedOrgId,
  preferences,
  switchOrganization,
  updatePreferences,
  getOrganizationById,
} = useAuthStore();
```

### User Preferences

```tsx
import { useUserPreferences } from '@/features/auth/hooks/useAuth';

const { preferences, updatePreferences } = useUserPreferences();

// Update preference
updatePreferences({
  rememberOrganization: true,
});
```

---

## Testing Checklist

- [ ] Organization switcher visible in topbar (multi-org users only)
- [ ] Dropdown shows all active organizations
- [ ] Current organization highlighted
- [ ] Switch updates data without navigation
- [ ] Toast notification appears on switch
- [ ] Keyboard shortcuts work (Ctrl/Cmd+K, 1-9)
- [ ] Remember checkbox persists preference
- [ ] Auto-select on login works
- [ ] Mobile responsive
- [ ] No data leaks between organizations

---

## Troubleshooting

### Org switcher not showing
- Check if user has > 1 organization
- Verify `organizations` array in AuthStore

### Cache not invalidating
- Ensure `useOrgSwitch()` is called in parent layout
- Check browser console for event logs
- Verify query keys match in both places

### Keyboard shortcuts not working
- Check if input field has focus
- Verify browser doesn't override shortcut
- Test with different key combinations

### Remember preference not persisting
- Check localStorage for 'auth-storage'
- Verify `preferences` in AuthStore
- Clear localStorage and test again

---

## Quick Links

- [Full Documentation](./ORGANIZATION_SWITCHING_UX.md)
- [AuthStore](/src/lib/stores/authStore.ts)
- [OrganizationSwitcher](/src/shared/components/layout/OrganizationSwitcher.tsx)
- [useOrgSwitch](/src/shared/hooks/useOrgSwitch.ts)

---

**Version**: 1.0.0
**Last Updated**: 2025-01-21
