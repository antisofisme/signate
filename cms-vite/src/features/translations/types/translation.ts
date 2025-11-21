/**
 * Translation Domain Types
 * Generated from backend-python/services/translation/dtos.py
 */

// ============================================================================
// Translation Types
// ============================================================================

export interface AddTranslationRequest {
  entity_type: string;
  entity_id: number;
  language_code: string;
  field_name: string;
  translated_value: string;
}

export interface UpdateTranslationRequest {
  translated_value: string;
}

export interface Translation {
  id: number;
  organization_id: number;
  entity_type: string;
  entity_id: number;
  language_code: string;
  field_name: string;
  translated_value: string;
  created_at: string;
  updated_at: string;
}

export interface TranslationListResponse {
  translations: Translation[];
  total: number;
}

// ============================================================================
// Entity Translation Types
// ============================================================================

export interface EntityTranslations {
  entity_type: string;
  entity_id: number;
  language_code: string;
  translations: Record<string, string>;
}

// ============================================================================
// Bulk Import Types
// ============================================================================

export interface BulkTranslationItem {
  entity_type: string;
  entity_id: number;
  language_code: string;
  field_name: string;
  translated_value: string;
}

export interface BulkImportRequest {
  translations: BulkTranslationItem[];
}

export interface BulkImportResponse {
  imported: number;
  updated: number;
  failed: number;
  errors?: string[];
}

// ============================================================================
// Language Support Types
// ============================================================================

export interface SupportedLanguage {
  code: string;
  name: string;
  native_name: string;
}

export interface SupportedLanguagesResponse {
  languages: SupportedLanguage[];
}

export interface OrganizationLanguagesResponse {
  language_codes: string[];
  total: number;
}

// ============================================================================
// Translation Statistics Types
// ============================================================================

export interface TranslationStats {
  total_translations: number;
  languages_count: number;
  entity_types: Record<string, number>;
  completion_rate: Record<string, number>;
}
