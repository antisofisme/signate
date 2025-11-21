/**
 * Template Domain Types
 * Generated from backend-python/services/template/dtos.py
 */

// ============================================================================
// Template Types
// ============================================================================

export interface CreateTemplateRequest {
  name: string;
  description?: string;
  template_type: string;
  content: string;
  variables?: Record<string, any>;
  preview_data?: Record<string, any>;
  is_active?: boolean;
}

export interface UpdateTemplateRequest {
  name?: string;
  description?: string;
  template_type?: string;
  content?: string;
  variables?: Record<string, any>;
  preview_data?: Record<string, any>;
  is_active?: boolean;
}

export interface Template {
  id: number;
  organization_id: number;
  name: string;
  description?: string;
  template_type: string;
  content: string;
  variables?: Record<string, any>;
  preview_data?: Record<string, any>;
  is_active: boolean;
  created_by?: number;
  created_at: string;
  updated_at: string;
}

export interface TemplateListResponse {
  templates: Template[];
  total: number;
}

// ============================================================================
// Template Rendering Types
// ============================================================================

export interface RenderTemplateRequest {
  data: Record<string, any>;
}

export interface RenderTemplateResponse {
  rendered_content: string;
  template_id: number;
  template_name: string;
}

export interface ValidateTemplateRequest {
  content: string;
  variables?: Record<string, any>;
}

export interface ValidateTemplateResponse {
  valid: boolean;
  message: string;
  extracted_variables?: string[];
  rendered_preview?: string;
}

// ============================================================================
// Template Variable Extraction
// ============================================================================

export interface ExtractVariablesRequest {
  content: string;
}

export interface ExtractVariablesResponse {
  variables: string[];
  variable_count: number;
}
