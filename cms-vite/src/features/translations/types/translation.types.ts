/**
 * Translation Types
 * Type definitions for translation management system
 */

// Supported languages
export type Language =
  | 'en' // English
  | 'id' // Indonesian
  | 'zh' // Chinese
  | 'ja' // Japanese
  | 'ko' // Korean
  | 'th' // Thai
  | 'vi' // Vietnamese
  | 'ms' // Malay
  | 'es' // Spanish
  | 'fr' // French

// Entity types that can be translated
export type EntityType = 'content' | 'playlist' | 'template' | 'widget'

// Translation status
export type TranslationStatus = 'pending' | 'approved' | 'rejected'

// Base translation interface
export interface Translation {
  id: number
  entity_type: EntityType
  entity_id: number
  language: Language
  field_name: string
  translated_text: string
  status: TranslationStatus
  created_at: string
  updated_at: string
  created_by?: number
  approved_by?: number
  approved_at?: string
}

// Language information
export interface LanguageInfo {
  code: Language
  name: string
  nativeName: string
  flag: string
  direction: 'ltr' | 'rtl'
}

// Language catalog
export const LANGUAGES: Record<Language, LanguageInfo> = {
  en: {
    code: 'en',
    name: 'English',
    nativeName: 'English',
    flag: '🇬🇧',
    direction: 'ltr',
  },
  id: {
    code: 'id',
    name: 'Indonesian',
    nativeName: 'Bahasa Indonesia',
    flag: '🇮🇩',
    direction: 'ltr',
  },
  zh: {
    code: 'zh',
    name: 'Chinese',
    nativeName: '中文',
    flag: '🇨🇳',
    direction: 'ltr',
  },
  ja: {
    code: 'ja',
    name: 'Japanese',
    nativeName: '日本語',
    flag: '🇯🇵',
    direction: 'ltr',
  },
  ko: {
    code: 'ko',
    name: 'Korean',
    nativeName: '한국어',
    flag: '🇰🇷',
    direction: 'ltr',
  },
  th: {
    code: 'th',
    name: 'Thai',
    nativeName: 'ไทย',
    flag: '🇹🇭',
    direction: 'ltr',
  },
  vi: {
    code: 'vi',
    name: 'Vietnamese',
    nativeName: 'Tiếng Việt',
    flag: '🇻🇳',
    direction: 'ltr',
  },
  ms: {
    code: 'ms',
    name: 'Malay',
    nativeName: 'Bahasa Melayu',
    flag: '🇲🇾',
    direction: 'ltr',
  },
  es: {
    code: 'es',
    name: 'Spanish',
    nativeName: 'Español',
    flag: '🇪🇸',
    direction: 'ltr',
  },
  fr: {
    code: 'fr',
    name: 'French',
    nativeName: 'Français',
    flag: '🇫🇷',
    direction: 'ltr',
  },
}

// Entity type information
export interface EntityTypeInfo {
  type: EntityType
  label: string
  icon: string
  description: string
  translatableFields: string[]
}

export const ENTITY_TYPES: Record<EntityType, EntityTypeInfo> = {
  content: {
    type: 'content',
    label: 'Content',
    icon: '📄',
    description: 'Translate content titles and descriptions',
    translatableFields: ['title', 'description'],
  },
  playlist: {
    type: 'playlist',
    label: 'Playlist',
    icon: '📋',
    description: 'Translate playlist names and descriptions',
    translatableFields: ['name', 'description'],
  },
  template: {
    type: 'template',
    label: 'Template',
    icon: '📝',
    description: 'Translate template names and content',
    translatableFields: ['name', 'description', 'content'],
  },
  widget: {
    type: 'widget',
    label: 'Widget',
    icon: '🧩',
    description: 'Translate widget names and configuration',
    translatableFields: ['name', 'config'],
  },
}

// API Request/Response types
export interface TranslationFilters {
  entity_type?: EntityType
  entity_id?: number
  language?: Language
  status?: TranslationStatus
  search?: string
}

export interface TranslationListResponse {
  translations: Translation[]
  total: number
}

export interface CreateTranslationRequest {
  entity_type: EntityType
  entity_id: number
  language: Language
  field_name: string
  translated_text: string
}

export interface UpdateTranslationRequest {
  translated_text?: string
  status?: TranslationStatus
}

export interface BulkTranslationRequest {
  entity_type: EntityType
  entity_id: number
  translations: {
    language: Language
    field_name: string
    translated_text: string
  }[]
}

export interface TranslationStatsResponse {
  total_translations: number
  by_language: Record<Language, number>
  by_entity_type: Record<EntityType, number>
  by_status: Record<TranslationStatus, number>
  completion_rate: number
}

export interface EntityTranslationsResponse {
  entity_type: EntityType
  entity_id: number
  entity_name: string
  translations: Translation[]
  available_fields: string[]
  coverage: Record<Language, number> // percentage of fields translated per language
}

// Bulk import types
export interface BulkImportItem {
  entity_type: EntityType
  entity_id: number
  language: Language
  field_name: string
  translated_text: string
}

export interface BulkImportRequest {
  translations: BulkImportItem[]
  skip_duplicates?: boolean
}

export interface BulkImportResponse {
  imported: number
  skipped: number
  errors: {
    row: number
    error: string
  }[]
}

// CSV export template
export interface CSVExportTemplate {
  entity_type: EntityType
  entity_id: number
  entity_name: string
  field_name: string
  original_text: string
  language: Language
  translated_text: string
}

// Translation coverage for entity
export interface TranslationCoverage {
  language: Language
  total_fields: number
  translated_fields: number
  percentage: number
  missing_fields: string[]
}
