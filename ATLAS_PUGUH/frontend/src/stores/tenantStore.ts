/**
 * Tenant Store
 *
 * Zustand store for managing current tenant context.
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Tenant, TenantWithMembership, MemberRole } from '@/features/tenant'

interface CurrentTenant {
  tenant_id: string
  name: string
  slug: string
  plan: string
  role: MemberRole
}

interface TenantState {
  // Current tenant context
  currentTenant: CurrentTenant | null
  availableTenants: TenantWithMembership[]

  // Actions
  setCurrentTenant: (tenant: CurrentTenant | null) => void
  setAvailableTenants: (tenants: TenantWithMembership[]) => void
  selectTenant: (tenantId: string) => void
  clearTenant: () => void
}

export const useTenantStore = create<TenantState>()(
  persist(
    (set, get) => ({
      currentTenant: null,
      availableTenants: [],

      setCurrentTenant: (tenant) => set({ currentTenant: tenant }),

      setAvailableTenants: (tenants) => {
        set({ availableTenants: tenants })

        // Auto-select if only one tenant and none selected
        const state = get()
        if (tenants.length === 1 && !state.currentTenant) {
          const t = tenants[0]
          set({
            currentTenant: {
              tenant_id: t.tenant.tenant_id,
              name: t.tenant.name,
              slug: t.tenant.slug,
              plan: t.tenant.plan,
              role: t.role,
            },
          })
        }
      },

      selectTenant: (tenantId) => {
        const { availableTenants } = get()
        const found = availableTenants.find((t) => t.tenant.tenant_id === tenantId)
        if (found) {
          set({
            currentTenant: {
              tenant_id: found.tenant.tenant_id,
              name: found.tenant.name,
              slug: found.tenant.slug,
              plan: found.tenant.plan,
              role: found.role,
            },
          })
        }
      },

      clearTenant: () => set({ currentTenant: null, availableTenants: [] }),
    }),
    {
      name: 'tenant-storage',
      partialize: (state) => ({ currentTenant: state.currentTenant }),
    }
  )
)

// Selector hooks
export const useCurrentTenant = () => useTenantStore((state) => state.currentTenant)
export const useAvailableTenants = () => useTenantStore((state) => state.availableTenants)
export const useIsOwner = () =>
  useTenantStore((state) => state.currentTenant?.role === 'owner')
export const useIsAdmin = () =>
  useTenantStore((state) => ['owner', 'admin'].includes(state.currentTenant?.role || ''))
