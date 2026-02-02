/**
 * Tenant Selector Component
 *
 * Dropdown to switch between user's tenants.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, ChevronsUpDown, Plus, Building2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Badge } from '@/components/ui/badge'
import { useTenantStore, useCurrentTenant } from '@/stores/tenantStore'
import { useTenants } from '@/features/tenant'
import { useEffect } from 'react'

interface TenantSelectorProps {
  className?: string
}

export function TenantSelector({ className }: TenantSelectorProps) {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  const currentTenant = useCurrentTenant()
  const { selectTenant, setAvailableTenants, availableTenants } = useTenantStore()

  // Fetch tenants
  const { data: tenantsData, isLoading } = useTenants()

  // Sync tenants to store
  useEffect(() => {
    if (tenantsData?.data) {
      setAvailableTenants(tenantsData.data)
    }
  }, [tenantsData, setAvailableTenants])

  const handleSelectTenant = (tenantId: string) => {
    selectTenant(tenantId)
    setOpen(false)
  }

  const handleCreateTenant = () => {
    setOpen(false)
    navigate('/app/tenant/new')
  }

  if (isLoading) {
    return (
      <Button variant="outline" className={cn('w-[200px] justify-between', className)} disabled>
        <Building2 className="mr-2 h-4 w-4" />
        Loading...
      </Button>
    )
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          aria-label="Select tenant"
          className={cn('w-[200px] justify-between', className)}
        >
          <Building2 className="mr-2 h-4 w-4" />
          {currentTenant ? (
            <span className="truncate">{currentTenant.name}</span>
          ) : (
            <span className="text-muted-foreground">Select tenant...</span>
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[250px] p-0">
        <Command>
          <CommandInput placeholder="Search tenant..." />
          <CommandList>
            <CommandEmpty>No tenant found.</CommandEmpty>
            <CommandGroup heading="Your Tenants">
              {availableTenants.map((item) => (
                <CommandItem
                  key={item.tenant.tenant_id}
                  onSelect={() => handleSelectTenant(item.tenant.tenant_id)}
                  className="flex items-center justify-between"
                >
                  <div className="flex items-center">
                    <Check
                      className={cn(
                        'mr-2 h-4 w-4',
                        currentTenant?.tenant_id === item.tenant.tenant_id
                          ? 'opacity-100'
                          : 'opacity-0'
                      )}
                    />
                    <span className="truncate">{item.tenant.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      {item.role}
                    </Badge>
                    {item.tenant.plan !== 'free' && (
                      <Badge variant="secondary" className="text-xs">
                        {item.tenant.plan}
                      </Badge>
                    )}
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandSeparator />
            <CommandGroup>
              <CommandItem onSelect={handleCreateTenant} className="cursor-pointer">
                <Plus className="mr-2 h-4 w-4" />
                Create new tenant
              </CommandItem>
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}

export default TenantSelector
