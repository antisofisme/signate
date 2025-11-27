# Widget Types Quick Reference

Quick reference for TypeScript widget type definitions and usage patterns.

## Import Statements

```typescript
// Widget types
import type {
  Widget,
  WidgetType,
  WidgetsResponse,
  WidgetPayload
} from '../../types/widget'

// Firebird types
import type {
  FirebirdConfig,
  FirebirdConfigsResponse,
  FirebirdConfigPayload,
  FirebirdHealthStatus,
  FirebirdConnectionMode,
  FirebirdConnectionStatus
} from '../../types/widget'

// Component props
import type {
  CalendarTabProps,
  SystemPMSTabProps,
  FirebirdConnectionStatusProps,
  FirebirdConnectionBadgeProps,
  FirebirdConfigModalProps
} from '../../types/widget'

// Form types
import type {
  FirebirdFormData,
  FirebirdFormErrors,
  FirebirdTestStatus
} from '../../types/widget'
```

## Common Patterns

### 1. Widget List Component
```typescript
export default function WidgetTab({}: WidgetTabProps) {
  const { data: widgetsData, isLoading } = useQuery<WidgetsResponse>({
    queryKey: ['widgets', 'type'],
    queryFn: () => widgetsAPI.list('type').then(res => res.data),
  })

  const deleteMutation = useMutation<void, AxiosError<ApiError>, number>({
    mutationFn: widgetsAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['widgets', 'type'])
    }
  })
}
```

### 2. Firebird Configuration Management
```typescript
export default function SystemPMSTab({}: SystemPMSTabProps) {
  const [selectedConfig, setSelectedConfig] = useState<FirebirdConfig | null>(null)
  const [expandedConfigId, setExpandedConfigId] = useState<number | null>(null)

  const { data: configsData } = useQuery<FirebirdConfigsResponse>({
    queryKey: ['firebird-configs'],
    queryFn: () => firebirdAPI.listConfigs().then(res => res.data),
  })

  const handleEdit = (config: FirebirdConfig): void => {
    setSelectedConfig(config)
  }
}
```

### 3. Firebird Form with Validation
```typescript
export default function FirebirdConfigModal({ config, onClose }: FirebirdConfigModalProps) {
  const [formData, setFormData] = useState<FirebirdFormData>({
    config_key: config?.config_key || '',
    connection_mode: config?.connection_mode || 'server',
    // ... other fields
  })

  const [errors, setErrors] = useState<FirebirdFormErrors>({})
  const [testStatus, setTestStatus] = useState<FirebirdTestStatus>(null)

  const handleChange = <K extends keyof FirebirdFormData>(
    field: K,
    value: FirebirdFormData[K]
  ): void => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const validateForm = (): boolean => {
    const newErrors: FirebirdFormErrors = {}
    // validation logic
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }
}
```

### 4. Connection Status Component
```typescript
export default function FirebirdConnectionStatus({
  configId,
  config,
  autoRefresh = true
}: FirebirdConnectionStatusProps) {
  const { data: healthData } = useQuery<FirebirdHealthStatus>({
    queryKey: ['firebird-health', configId],
    queryFn: () => firebirdAPI.getHealth(configId).then(res => res.data),
    refetchInterval: autoRefresh ? 30000 : false,
  })

  const getStatus = (): FirebirdConnectionStatus => {
    if (error || healthData?.status === 'error') return 'error'
    if (healthData?.status === 'connected') return 'connected'
    return 'disconnected'
  }
}
```

## Type Values

### WidgetType Union
```typescript
type WidgetType =
  | 'calendar'
  | 'text'
  | 'iframe'
  | 'weather'
  | 'countdown'
  | 'clock'
  | 'system_pms'
```

### FirebirdConnectionMode
```typescript
type FirebirdConnectionMode = 'server' | 'embedded'
```

### FirebirdConnectionStatus
```typescript
type FirebirdConnectionStatus =
  | 'connected'
  | 'disconnected'
  | 'error'
  | 'checking'
```

### FirebirdTestStatus
```typescript
type FirebirdTestStatus = 'testing' | 'success' | 'error' | null
```

## Interface Structures

### Widget Interface
```typescript
interface Widget {
  id: number
  name: string
  type: WidgetType
  description?: string
  config?: Record<string, unknown>
  is_active: boolean
  created_at: string
  updated_at: string
}
```

### FirebirdConfig Interface
```typescript
interface FirebirdConfig {
  id: number
  config_key: string
  connection_mode: FirebirdConnectionMode
  database_host: string
  database_port: number
  database_path: string
  database_user: string
  database_password: string
  refresh_interval: number
  is_active: boolean
  notes?: string
  created_at: string
  updated_at: string
}
```

### FirebirdHealthStatus Interface
```typescript
interface FirebirdHealthStatus {
  status: FirebirdConnectionStatus
  message?: string
  last_sync?: string
  error?: string
}
```

## React Query Typing

### Query
```typescript
const { data, isLoading } = useQuery<ResponseType>({
  queryKey: ['key'],
  queryFn: () => apiCall().then(res => res.data),
})
```

### Mutation
```typescript
const mutation = useMutation<
  ReturnType,           // Success return type
  AxiosError<ApiError>, // Error type
  ParameterType         // Variables type
>({
  mutationFn: apiCall,
  onSuccess: (data) => { /* ... */ },
  onError: (error) => { /* ... */ },
})
```

## Common Type Guards

### Check Widget Type
```typescript
const isCalendarWidget = (widget: Widget): boolean => {
  return widget.type === 'calendar'
}
```

### Check Connection Mode
```typescript
const isServerMode = (config: FirebirdConfig): boolean => {
  return config.connection_mode === 'server'
}
```

### Check Connection Status
```typescript
const isConnected = (status: FirebirdConnectionStatus): boolean => {
  return status === 'connected'
}
```

## Validation Patterns

### Required Field
```typescript
if (!formData.config_key.trim()) {
  errors.config_key = 'Configuration name is required'
}
```

### Conditional Field
```typescript
if (formData.connection_mode === 'server') {
  if (!formData.database_host.trim()) {
    errors.database_host = 'Database host is required for server mode'
  }
}
```

### Numeric Range
```typescript
if (!formData.database_port || formData.database_port < 1 || formData.database_port > 65535) {
  errors.database_port = 'Valid port number is required (1-65535)'
}
```

## Status Configuration Pattern

```typescript
interface StatusConfig {
  icon: LucideIcon
  color: string
  bgColor: string
  borderColor: string
  label: string
}

const statusConfig: Record<FirebirdConnectionStatus, StatusConfig> = {
  connected: {
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    label: 'Connected',
  },
  // ... other statuses
}

const currentConfig = statusConfig[status]
const StatusIcon = currentConfig.icon
```

## API Call Patterns

### List Widgets
```typescript
const response = await widgetsAPI.list('calendar')
const widgets: WidgetsResponse = response.data
```

### Create Firebird Config
```typescript
const payload: FirebirdConfigPayload = { /* ... */ }
const response = await firebirdAPI.createConfig(payload)
```

### Test Connection
```typescript
const response = await firebirdAPI.testConnection(configId)
const result: FirebirdTestConnectionResponse = response.data
```

### Get Health Status
```typescript
const response = await firebirdAPI.getHealth(configId)
const health: FirebirdHealthStatus = response.data
```

---

**File Location:** `/mnt/g/khoirul/signate/web-admin/src/types/widget.ts`

**Usage:** Import the required types at the top of your widget component files.
