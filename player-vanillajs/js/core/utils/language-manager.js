/**
 * Language Manager Module
 * Handles multi-language support for the digital signage viewer
 *
 * Features:
 * - Language selection and persistence
 * - Auto-detection from device/browser
 * - Language rotation mode (airport/hotel mode)
 * - Fallback chain (requested → primary → default → en)
 * - RTL support
 * - Event-driven updates
 */

class LanguageManager extends EventTarget {
    constructor() {
        super();

        // Configuration
        this.currentLanguage = null;
        this.availableLanguages = [];
        this.primaryLanguage = 'en'; // Default fallback
        this.rotationMode = false;
        this.rotationInterval = 30; // seconds
        this.rotationTimer = null;
        this.rotationIndex = 0;

        // API configuration
        this.apiBaseUrl = window.ENV?.API_BASE_URL ||
                          window.PlayerState?.API_BASE_URL ||
                          'http://localhost:8001';

        // Load saved language preference
        this.currentLanguage = this.loadLanguageFromStorage();

        console.log('[LanguageManager] Initialized with language:', this.currentLanguage);
    }

    /**
     * Initialize language manager
     * Loads available languages from backend and sets up language
     */
    async initialize() {
        console.log('[LanguageManager] Starting initialization...');

        try {
            // Load available languages from backend
            await this.loadAvailableLanguages();

            // Auto-detect language if not already set
            if (!this.currentLanguage || !this.isLanguageAvailable(this.currentLanguage)) {
                await this.autoDetectLanguage();
            } else {
                // Validate and apply saved language
                this.applyLanguage(this.currentLanguage);
            }

            // Check if rotation mode is enabled from device settings
            const rotationEnabled = localStorage.getItem('language_rotation_enabled');
            const rotationInterval = localStorage.getItem('language_rotation_interval');

            if (rotationEnabled === 'true') {
                this.rotationInterval = parseInt(rotationInterval) || 30;
                this.startRotation();
            }

            console.log('[LanguageManager] ✅ Initialization complete');
            console.log('[LanguageManager] Current language:', this.currentLanguage);
            console.log('[LanguageManager] Available languages:', this.availableLanguages.length);
            console.log('[LanguageManager] Rotation mode:', this.rotationMode);

            return this.currentLanguage;

        } catch (error) {
            console.error('[LanguageManager] ❌ Initialization failed:', error);
            // Fallback to English
            this.currentLanguage = 'en';
            this.applyLanguage('en');
            return 'en';
        }
    }

    /**
     * Load available languages from backend
     */
    async loadAvailableLanguages() {
        console.log('[LanguageManager] Loading available languages from backend...');

        try {
            // Use APIClient if available
            let data;
            if (window.APIClient) {
                data = await window.APIClient.get(`${this.apiBaseUrl}/api/languages`);
            } else {
                const response = await fetch(`${this.apiBaseUrl}/api/languages`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                data = await response.json();
            }

            this.availableLanguages = data.languages || data || [];

            console.log('[LanguageManager] ✅ Loaded languages:', this.availableLanguages);

            // Set primary language from backend if available
            if (data.primary_language) {
                this.primaryLanguage = data.primary_language;
                console.log('[LanguageManager] Primary language set to:', this.primaryLanguage);
            }

        } catch (error) {
            console.warn('[LanguageManager] ⚠️ Failed to load languages from backend:', error);

            // Fallback to default language set
            this.availableLanguages = [
                { code: 'en', name: 'English', native_name: 'English', is_rtl: false },
                { code: 'id', name: 'Indonesian', native_name: 'Bahasa Indonesia', is_rtl: false },
                { code: 'zh', name: 'Chinese', native_name: '中文', is_rtl: false },
                { code: 'ja', name: 'Japanese', native_name: '日本語', is_rtl: false },
                { code: 'ko', name: 'Korean', native_name: '한국어', is_rtl: false },
                { code: 'ar', name: 'Arabic', native_name: 'العربية', is_rtl: true },
                { code: 'es', name: 'Spanish', native_name: 'Español', is_rtl: false },
                { code: 'fr', name: 'French', native_name: 'Français', is_rtl: false },
                { code: 'de', name: 'German', native_name: 'Deutsch', is_rtl: false },
                { code: 'ru', name: 'Russian', native_name: 'Русский', is_rtl: false }
            ];

            console.log('[LanguageManager] Using fallback language set');
        }
    }

    /**
     * Auto-detect language from device/browser
     */
    async autoDetectLanguage() {
        console.log('[LanguageManager] Auto-detecting language...');

        // 1. Try device language setting (for WebOS TV)
        const deviceLang = await this.getDeviceLanguage();
        if (deviceLang && this.isLanguageAvailable(deviceLang)) {
            console.log('[LanguageManager] ✅ Detected from device:', deviceLang);
            this.setLanguage(deviceLang, 'device-detected');
            return;
        }

        // 2. Try browser language
        const browserLang = this.getBrowserLanguage();
        if (browserLang && this.isLanguageAvailable(browserLang)) {
            console.log('[LanguageManager] ✅ Detected from browser:', browserLang);
            this.setLanguage(browserLang, 'browser-detected');
            return;
        }

        // 3. Try primary language from backend
        if (this.primaryLanguage && this.isLanguageAvailable(this.primaryLanguage)) {
            console.log('[LanguageManager] ✅ Using primary language:', this.primaryLanguage);
            this.setLanguage(this.primaryLanguage, 'primary-default');
            return;
        }

        // 4. Default to English
        console.log('[LanguageManager] ℹ️ Using default language: en');
        this.setLanguage('en', 'default');
    }

    /**
     * Get device language (WebOS TV specific)
     */
    async getDeviceLanguage() {
        try {
            // Check if WebOS API is available
            if (window.webOS && window.webOS.deviceInfo) {
                const deviceInfo = await window.webOS.deviceInfo();
                if (deviceInfo.language) {
                    // Extract language code (e.g., "en-US" → "en")
                    return deviceInfo.language.split('-')[0].toLowerCase();
                }
            }

            // Check localStorage for device setting
            const savedDeviceLang = localStorage.getItem('device_language');
            if (savedDeviceLang) {
                return savedDeviceLang.split('-')[0].toLowerCase();
            }

        } catch (error) {
            console.debug('[LanguageManager] Device language not available:', error.message);
        }

        return null;
    }

    /**
     * Get browser language
     */
    getBrowserLanguage() {
        try {
            // Try navigator.language first
            if (navigator.language) {
                return navigator.language.split('-')[0].toLowerCase();
            }

            // Fallback to navigator.languages array
            if (navigator.languages && navigator.languages.length > 0) {
                return navigator.languages[0].split('-')[0].toLowerCase();
            }

        } catch (error) {
            console.debug('[LanguageManager] Browser language not available:', error.message);
        }

        return null;
    }

    /**
     * Set current language
     */
    setLanguage(langCode, source = 'manual') {
        // Validate language code
        if (!langCode) {
            console.warn('[LanguageManager] ⚠️ Empty language code provided');
            return false;
        }

        langCode = langCode.toLowerCase();

        if (!this.isLanguageAvailable(langCode)) {
            console.warn(`[LanguageManager] ⚠️ Language ${langCode} not available`);

            // Try fallback to primary language
            if (this.primaryLanguage && this.isLanguageAvailable(this.primaryLanguage)) {
                console.log(`[LanguageManager] Falling back to primary language: ${this.primaryLanguage}`);
                langCode = this.primaryLanguage;
            } else {
                // Fallback to English
                console.log('[LanguageManager] Falling back to English');
                langCode = 'en';
            }
        }

        const oldLang = this.currentLanguage;
        this.currentLanguage = langCode;

        // Save to localStorage
        this.saveLanguageToStorage(langCode, source);

        // Apply language to DOM
        this.applyLanguage(langCode);

        // Dispatch event
        this.dispatchEvent(new CustomEvent('language-changed', {
            detail: {
                oldLang,
                newLang: langCode,
                source,
                languageInfo: this.getLanguageInfo(langCode)
            }
        }));

        console.log(`[LanguageManager] ✅ Language changed: ${oldLang} → ${langCode} (${source})`);

        return true;
    }

    /**
     * Apply language to DOM
     */
    applyLanguage(langCode) {
        // Update HTML lang attribute
        document.documentElement.lang = langCode;

        // Update RTL if needed
        const langData = this.getLanguageInfo(langCode);
        if (langData && langData.is_rtl) {
            document.documentElement.dir = 'rtl';
            document.body.classList.add('rtl');
            console.log(`[LanguageManager] Applied RTL direction for ${langCode}`);
        } else {
            document.documentElement.dir = 'ltr';
            document.body.classList.remove('rtl');
        }

        // Update page title if needed
        const langName = langData ? langData.native_name : langCode.toUpperCase();
        console.log(`[LanguageManager] Applied language: ${langName}`);
    }

    /**
     * Start language rotation mode (airport/hotel mode)
     */
    startRotation() {
        if (this.rotationMode) {
            console.log('[LanguageManager] ⚠️ Rotation already active');
            return;
        }

        console.log(`[LanguageManager] 🔄 Starting rotation mode (interval: ${this.rotationInterval}s)`);
        this.rotationMode = true;

        // Save rotation settings
        localStorage.setItem('language_rotation_enabled', 'true');
        localStorage.setItem('language_rotation_interval', this.rotationInterval.toString());

        // Find starting index
        this.rotationIndex = this.availableLanguages.findIndex(
            lang => lang.code === this.currentLanguage
        );

        if (this.rotationIndex === -1) {
            this.rotationIndex = 0;
        }

        // Start rotation timer
        this.rotationTimer = setInterval(() => {
            this.rotateToNextLanguage();
        }, this.rotationInterval * 1000);

        // Dispatch event
        this.dispatchEvent(new CustomEvent('rotation-started', {
            detail: { interval: this.rotationInterval }
        }));
    }

    /**
     * Stop language rotation mode
     */
    stopRotation() {
        if (!this.rotationMode) {
            console.log('[LanguageManager] ⚠️ Rotation not active');
            return;
        }

        console.log('[LanguageManager] ⏹️ Stopping rotation mode');
        this.rotationMode = false;

        // Clear timer
        if (this.rotationTimer) {
            clearInterval(this.rotationTimer);
            this.rotationTimer = null;
        }

        // Clear rotation settings
        localStorage.removeItem('language_rotation_enabled');

        // Dispatch event
        this.dispatchEvent(new CustomEvent('rotation-stopped'));
    }

    /**
     * Rotate to next language
     */
    rotateToNextLanguage() {
        if (this.availableLanguages.length === 0) {
            console.warn('[LanguageManager] ⚠️ No languages available for rotation');
            return;
        }

        // Move to next language
        this.rotationIndex = (this.rotationIndex + 1) % this.availableLanguages.length;
        const nextLang = this.availableLanguages[this.rotationIndex].code;

        console.log(`[LanguageManager] 🔄 Rotating to language ${this.rotationIndex + 1}/${this.availableLanguages.length}: ${nextLang}`);

        this.setLanguage(nextLang, 'rotation');
    }

    /**
     * Set rotation interval
     */
    setRotationInterval(seconds) {
        if (seconds < 5) {
            console.warn('[LanguageManager] ⚠️ Rotation interval too short, minimum is 5 seconds');
            seconds = 5;
        }

        this.rotationInterval = seconds;
        localStorage.setItem('language_rotation_interval', seconds.toString());

        console.log(`[LanguageManager] Rotation interval set to ${seconds}s`);

        // Restart rotation if active
        if (this.rotationMode) {
            this.stopRotation();
            this.startRotation();
        }
    }

    /**
     * Check if language is available
     */
    isLanguageAvailable(langCode) {
        if (!langCode) return false;
        langCode = langCode.toLowerCase();
        return this.availableLanguages.some(lang => lang.code.toLowerCase() === langCode);
    }

    /**
     * Get language information
     */
    getLanguageInfo(langCode) {
        if (!langCode) return null;
        langCode = langCode.toLowerCase();
        return this.availableLanguages.find(lang => lang.code.toLowerCase() === langCode);
    }

    /**
     * Get all available languages
     */
    getAvailableLanguages() {
        return [...this.availableLanguages];
    }

    /**
     * Get current language code
     */
    getCurrentLanguage() {
        return this.currentLanguage;
    }

    /**
     * Get current language info
     */
    getCurrentLanguageInfo() {
        return this.getLanguageInfo(this.currentLanguage);
    }

    /**
     * Check if rotation is active
     */
    isRotationActive() {
        return this.rotationMode;
    }

    /**
     * Load language from storage
     */
    loadLanguageFromStorage() {
        const savedLang = localStorage.getItem('language');
        if (savedLang) {
            console.log('[LanguageManager] Loaded language from storage:', savedLang);
            return savedLang;
        }
        return null;
    }

    /**
     * Save language to storage
     */
    saveLanguageToStorage(langCode, source) {
        localStorage.setItem('language', langCode);
        localStorage.setItem('language_source', source);
        localStorage.setItem('language_updated_at', new Date().toISOString());
        console.log(`[LanguageManager] Saved language to storage: ${langCode} (${source})`);
    }

    /**
     * Clear language from storage
     */
    clearLanguageFromStorage() {
        localStorage.removeItem('language');
        localStorage.removeItem('language_source');
        localStorage.removeItem('language_updated_at');
        console.log('[LanguageManager] Cleared language from storage');
    }

    /**
     * Get language statistics
     */
    getStatistics() {
        return {
            currentLanguage: this.currentLanguage,
            availableLanguages: this.availableLanguages.length,
            rotationMode: this.rotationMode,
            rotationInterval: this.rotationInterval,
            source: localStorage.getItem('language_source'),
            updatedAt: localStorage.getItem('language_updated_at')
        };
    }
}

// Create global instance
window.LanguageManager = new LanguageManager();

console.log('[LanguageManager] Module loaded');
