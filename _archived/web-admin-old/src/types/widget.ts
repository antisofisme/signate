/**
 * Widget Type Definitions
 *
 * TypeScript interfaces for widget components and configurations
 */

// ============================================================================
// Widget Common Types
// ============================================================================

/** Widget type enumeration */
export type WidgetType = 'calendar' | 'text' | 'iframe' | 'weather' | 'countdown' | 'clock' | 'system_pms'

/** Base widget structure */
export interface Widget {
  id: number
  name: string
  type: WidgetType
  description?: string
  config?: Record<string, unknown>
  is_active: boolean
  created_at: string
  updated_at: string
}

/** Widgets list response */
export interface WidgetsResponse {
  items: Widget[]
  total: number
}

/** Widget create/update payload */
export interface WidgetPayload {
  name: string
  type: WidgetType
  description?: string
  config?: Record<string, unknown>
  is_active?: boolean
}

// ============================================================================
// Firebird/SystemPMS Types
// ============================================================================

/** Firebird connection mode */
export type FirebirdConnectionMode = 'server' | 'embedded'

/** Firebird connection status */
export type FirebirdConnectionStatus = 'connected' | 'disconnected' | 'error' | 'checking'

/** Firebird configuration */
export interface FirebirdConfig {
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

/** Firebird configurations list response */
export interface FirebirdConfigsResponse {
  configs: FirebirdConfig[]
  total: number
}

/** Firebird configuration create/update payload */
export interface FirebirdConfigPayload {
  config_key: string
  connection_mode: FirebirdConnectionMode
  database_host?: string
  database_port?: number
  database_path: string
  database_user: string
  database_password: string
  refresh_interval: number
  is_active: boolean
  notes?: string
  test_only?: boolean
}

/** Firebird health status */
export interface FirebirdHealthStatus {
  status: FirebirdConnectionStatus
  message?: string
  last_sync?: string
  error?: string
}

/** Firebird test connection response */
export interface FirebirdTestConnectionResponse {
  success: boolean
  message: string
  connection_time?: number
}

// ============================================================================
// Widget Tab Props
// ============================================================================

/** Calendar tab component props */
export interface CalendarTabProps {
  // Calendar tabs typically have minimal props or none
}

/** Text tab component props */
export interface TextTabProps {
  // Text tabs typically have minimal props or none
}

/** IFrame tab component props */
export interface IFrameTabProps {
  // IFrame tabs typically have minimal props or none
}

/** Weather tab component props */
export interface WeatherTabProps {
  // Weather tabs typically have minimal props or none
}

/** Countdown tab component props */
export interface CountdownTabProps {
  // Countdown tabs typically have minimal props or none
}

/** Clock tab component props */
export interface ClockTabProps {
  // Clock tabs typically have minimal props or none
}

/** SystemPMS tab component props */
export interface SystemPMSTabProps {
  // SystemPMS tabs typically have minimal props or none
}

/** Firebird connection status component props */
export interface FirebirdConnectionStatusProps {
  configId: number
  config?: FirebirdConfig | null
  autoRefresh?: boolean
}

/** Firebird connection badge component props */
export interface FirebirdConnectionBadgeProps {
  status: FirebirdConnectionStatus
  showLabel?: boolean
}

/** Firebird config modal component props */
export interface FirebirdConfigModalProps {
  config?: FirebirdConfig | null
  onClose: () => void
  onSuccess?: () => void
}

// ============================================================================
// Form Types for Firebird Modal
// ============================================================================

/** Firebird form data */
export interface FirebirdFormData {
  config_key: string
  connection_mode: FirebirdConnectionMode
  database_host: string
  database_port: number
  database_path: string
  database_user: string
  database_password: string
  refresh_interval: number
  is_active: boolean
  notes: string
}

/** Firebird form errors */
export interface FirebirdFormErrors {
  config_key?: string
  database_host?: string
  database_port?: string
  database_path?: string
  database_user?: string
  database_password?: string
  refresh_interval?: string
}

/** Firebird test status */
export type FirebirdTestStatus = 'testing' | 'success' | 'error' | null
