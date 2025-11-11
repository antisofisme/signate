/**
 * Internationalization (i18n) Service
 * Manages multi-language support in the player
 */

import { logger } from '../logger';
import { SharedAPIClient } from '../api';
import { SharedEventBus } from '../events/shared-event-bus';
import { defaultTranslations } from '../data/translations';

export interface Translation {
  key: string;
  value: string;
  language: string;
  category?: string;
}

export interface LanguageConfig {
  code: string;
  name: string;
  direction: 'ltr' | 'rtl';
  isDefault?: boolean;
}

export class I18nService {
  private translations: Map<string, Map<string, string>> = new Map();
  private currentLanguage: string = 'en';
  private availableLanguages: LanguageConfig[] = [
    { code: 'en', name: 'English', direction: 'ltr', isDefault: true },
    { code: 'id', name: 'Bahasa Indonesia', direction: 'ltr' },
    { code: 'zh', name: '中文', direction: 'ltr' },
    { code: 'ja', name: '日本語', direction: 'ltr' },
    { code: 'ko', name: '한국어', direction: 'ltr' },
    { code: 'ar', name: 'العربية', direction: 'rtl' },
  ];
  private fallbackLanguage: string = 'en';
  private organizationId?: number;

  constructor() {
    logger.info('[I18nService] Service initialized');
    this.loadDefaultTranslations();
    this.loadSavedLanguage();
  }

  /**
   * Load default translations
   */
  private loadDefaultTranslations(): void {
    // Load default translations for each language
    Object.entries(defaultTranslations).forEach(([language, translations]) => {
      this.addTranslations(language, translations);
    });
    
    logger.info('[I18nService] Default translations loaded');
  }

  /**
   * Initialize i18n service with organization context
   */
  async initialize(organizationId: number): Promise<void> {
    this.organizationId = organizationId;
    
    // Load translations from backend
    await this.loadTranslations();
    
    // Check for guest language preference
    await this.checkGuestLanguage();
    
    logger.info(`[I18nService] Initialized with language: ${this.currentLanguage}`);
  }

  /**
   * Get translation for a key
   */
  translate(key: string, options?: Record<string, any> | string): string {
    let params: Record<string, any> | undefined;
    let defaultValue: string | undefined;
    
    // Handle options - can be params object or defaultValue string
    if (typeof options === 'string') {
      defaultValue = options;
    } else if (options) {
      params = options;
      defaultValue = options.defaultValue;
    }
    
    // Try current language
    let translation = this.getTranslation(key, this.currentLanguage);
    
    // Fallback to default language
    if (!translation && this.currentLanguage !== this.fallbackLanguage) {
      translation = this.getTranslation(key, this.fallbackLanguage);
    }
    
    // If still no translation, return defaultValue or key
    if (!translation) {
      if (defaultValue) {
        return defaultValue;
      }
      logger.warn(`[I18nService] Missing translation for key: ${key}`);
      return key;
    }
    
    // Replace parameters if provided
    if (params) {
      translation = this.replaceParams(translation, params);
    }
    
    return translation;
  }

  /**
   * Shorthand for translate
   */
  t(key: string, options?: Record<string, any> | string): string {
    return this.translate(key, options);
  }

  /**
   * Set current language
   */
  setLanguage(languageCode: string): void {
    const language = this.availableLanguages.find(lang => lang.code === languageCode);
    
    if (!language) {
      logger.error(`[I18nService] Invalid language code: ${languageCode}`);
      return;
    }
    
    this.currentLanguage = languageCode;
    localStorage.setItem('player_language', languageCode);
    
    // Update document direction for RTL languages
    document.documentElement.dir = language.direction;
    document.documentElement.lang = languageCode;
    
    // Emit language change event
    SharedEventBus.emit('language:changed', {
      code: languageCode,
      language: language,
    });
    
    logger.info(`[I18nService] Language changed to: ${languageCode}`);
  }

  /**
   * Get current language
   */
  getLanguage(): string {
    return this.currentLanguage;
  }

  /**
   * Get current language config
   */
  getCurrentLanguageConfig(): LanguageConfig | undefined {
    return this.availableLanguages.find(lang => lang.code === this.currentLanguage);
  }

  /**
   * Get available languages
   */
  getAvailableLanguages(): LanguageConfig[] {
    return this.availableLanguages;
  }

  /**
   * Format date according to current locale
   */
  formatDate(date: Date | string, options?: Intl.DateTimeFormatOptions): string {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    const locale = this.getLocale();
    
    return dateObj.toLocaleDateString(locale, options);
  }

  /**
   * Format time according to current locale
   */
  formatTime(date: Date | string, options?: Intl.DateTimeFormatOptions): string {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    const locale = this.getLocale();
    
    return dateObj.toLocaleTimeString(locale, options);
  }

  /**
   * Format number according to current locale
   */
  formatNumber(num: number, options?: Intl.NumberFormatOptions): string {
    const locale = this.getLocale();
    return num.toLocaleString(locale, options);
  }

  /**
   * Format currency according to current locale
   */
  formatCurrency(amount: number, currency: string = 'USD'): string {
    const locale = this.getLocale();
    
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currency,
    }).format(amount);
  }

  /**
   * Get locale string for current language
   */
  getLocale(): string {
    // Map language codes to locales
    const localeMap: Record<string, string> = {
      'en': 'en-US',
      'id': 'id-ID',
      'zh': 'zh-CN',
      'ja': 'ja-JP',
      'ko': 'ko-KR',
      'ar': 'ar-SA',
    };
    
    return localeMap[this.currentLanguage] || 'en-US';
  }

  /**
   * Load saved language from localStorage
   */
  private loadSavedLanguage(): void {
    const savedLanguage = localStorage.getItem('player_language');
    
    if (savedLanguage && this.availableLanguages.some(lang => lang.code === savedLanguage)) {
      this.setLanguage(savedLanguage);
    }
  }

  /**
   * Load translations from backend
   */
  private async loadTranslations(): Promise<void> {
    try {
      if (!this.organizationId) return;
      
      const response = await SharedAPIClient.get<any>(`/api/v1/translations?organization_id=${this.organizationId}`);
      
      if (response.success && response.data) {
        // Process translations
        const translations = response.data.items || [];
        
        translations.forEach((translation: any) => {
          const langMap = this.translations.get(translation.language) || new Map();
          langMap.set(translation.key, translation.value);
          this.translations.set(translation.language, langMap);
        });
        
        logger.info(`[I18nService] Loaded ${translations.length} translations`);
      }
    } catch (error) {
      logger.error('[I18nService] Error loading translations:', error);
    }
  }

  /**
   * Check for guest language preference from PMS
   */
  private async checkGuestLanguage(): Promise<void> {
    try {
      // Get device ID
      const deviceId = localStorage.getItem('device_id');
      if (!deviceId) return;
      
      // Get guest data
      const response = await SharedAPIClient.get<any>(`/api/v1/pms/device/${deviceId}/current-guest`);
      
      if (response.success && response.data && response.data.language) {
        const guestLanguage = response.data.language;
        
        // Set language if it's available
        if (this.availableLanguages.some(lang => lang.code === guestLanguage)) {
          this.setLanguage(guestLanguage);
          logger.info(`[I18nService] Set guest language preference: ${guestLanguage}`);
        }
      }
    } catch (error) {
      logger.error('[I18nService] Error checking guest language:', error);
    }
  }

  /**
   * Get translation from map
   */
  private getTranslation(key: string, language: string): string | undefined {
    const langMap = this.translations.get(language);
    
    if (!langMap) return undefined;
    
    return langMap.get(key);
  }

  /**
   * Replace parameters in translation string
   */
  private replaceParams(text: string, params: Record<string, any>): string {
    let result = text;
    
    // Replace {param} style placeholders
    Object.entries(params).forEach(([key, value]) => {
      const regex = new RegExp(`\\{${key}\\}`, 'g');
      result = result.replace(regex, String(value));
    });
    
    return result;
  }

  /**
   * Add runtime translation
   */
  addTranslation(language: string, key: string, value: string): void {
    const langMap = this.translations.get(language) || new Map();
    langMap.set(key, value);
    this.translations.set(language, langMap);
  }

  /**
   * Bulk add translations
   */
  addTranslations(language: string, translations: Record<string, string>): void {
    const langMap = this.translations.get(language) || new Map();
    
    Object.entries(translations).forEach(([key, value]) => {
      langMap.set(key, value);
    });
    
    this.translations.set(language, langMap);
  }

  /**
   * Clear all translations
   */
  clearTranslations(): void {
    this.translations.clear();
  }

  /**
   * Get direction for current language
   */
  getDirection(): 'ltr' | 'rtl' {
    const config = this.getCurrentLanguageConfig();
    return config?.direction || 'ltr';
  }
}

// Export singleton instance
export const i18n = new I18nService();

// Export convenience functions
export const t = (key: string, params?: Record<string, any>) => i18n.t(key, params);
export const setLanguage = (code: string) => i18n.setLanguage(code);
export const getLanguage = () => i18n.getLanguage();