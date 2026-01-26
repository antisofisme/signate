/**
 * Configuration Master Data Types
 * Customer-defined master data for governance and UI grouping
 * NOT for decision evaluation logic
 */

// Functional Area (Customer-defined)
export interface FunctionalArea {
  functional_area_id: string
  tenant_id: string
  code: string
  name: string
  description?: string
  is_active: boolean
  display_order: number
  created_at: string
  updated_at?: string
}

export interface FunctionalAreaCreate {
  code: string
  name: string
  description?: string
  is_active?: boolean
  display_order?: number
}

export interface FunctionalAreaUpdate {
  name?: string
  description?: string
  is_active?: boolean
  display_order?: number
}

export interface FunctionalAreasResponse {
  functional_areas: FunctionalArea[]
  total: number
}

// Decision Type (System-defined contracts)
export interface DecisionType {
  decision_type_id: string
  tenant_id: string
  type_code: string
  type_name: string
  description?: string
  context_schema: Record<string, any>
  is_system_defined: boolean
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface DecisionTypeCreate {
  type_code: string
  type_name: string
  description?: string
  context_schema?: Record<string, any>
  is_active?: boolean
}

export interface DecisionTypeUpdate {
  type_name?: string
  description?: string
  context_schema?: Record<string, any>
  is_active?: boolean
}

export interface DecisionTypesResponse {
  decision_types: DecisionType[]
  total: number
}

// Approver Role (Customer-defined)
export interface ApproverRole {
  approver_role_id: string
  tenant_id: string
  role_code: string
  role_name: string
  description?: string
  is_active: boolean
  display_order: number
  created_at: string
  updated_at?: string
}

export interface ApproverRoleCreate {
  role_code: string
  role_name: string
  description?: string
  is_active?: boolean
  display_order?: number
}

export interface ApproverRoleUpdate {
  role_name?: string
  description?: string
  is_active?: boolean
  display_order?: number
}

export interface ApproverRolesResponse {
  approver_roles: ApproverRole[]
  total: number
}
