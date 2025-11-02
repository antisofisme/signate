/**
 * Language Selector UI Component
 * Provides an elegant UI for language selection
 *
 * Features:
 * - Dropdown or modal UI
 * - Flag icons for each language
 * - Search/filter for many languages
 * - Current language indicator
 * - Smooth animations
 * - Touch-friendly for WebOS TV
 */

class LanguageSelector {
    constructor(languageManager) {
        this.languageManager = languageManager;
        this.isOpen = false;
        this.searchQuery = '';
        this.filteredLanguages = [];

        // UI elements (will be populated after render)
        this.container = null;
        this.button = null;
        this.dropdown = null;
        this.searchInput = null;
        this.languageList = null;

        console.log('[LanguageSelector] Initializing...');
    }

    /**
     * Initialize and render the language selector
     */
    async initialize() {
        // Wait for languageManager to be ready
        if (this.languageManager.availableLanguages.length === 0) {
            console.log('[LanguageSelector] Waiting for languages to load...');
            await new Promise(resolve => {
                this.languageManager.addEventListener('language-changed', resolve, { once: true });
            });
        }

        this.render();
        this.attachEventListeners();

        console.log('[LanguageSelector] ✅ Initialized');
    }

    /**
     * Render the language selector UI
     */
    render() {
        // Remove existing selector if any
        const existing = document.getElementById('language-selector');
        if (existing) {
            existing.remove();
        }

        // Create container
        this.container = document.createElement('div');
        this.container.id = 'language-selector';
        this.container.className = 'language-selector';

        // Get current language info
        const currentLang = this.languageManager.getCurrentLanguageInfo();
        const currentCode = this.languageManager.getCurrentLanguage() || 'en';

        // Build HTML
        this.container.innerHTML = `
            <button class="language-btn" id="language-btn" title="Change Language">
                <span class="flag-icon" data-lang="${currentCode}">${this.getFlagEmoji(currentCode)}</span>
                <span class="language-code">${currentCode.toUpperCase()}</span>
                <span class="dropdown-arrow">▼</span>
            </button>

            <div class="language-dropdown" id="language-dropdown">
                <div class="language-header">
                    <h3>Select Language</h3>
                    <button class="language-close" id="language-close" title="Close">×</button>
                </div>

                <div class="language-search">
                    <input type="text"
                           id="language-search"
                           placeholder="Search language..."
                           autocomplete="off">
                </div>

                <div class="language-list" id="language-list">
                    ${this.renderLanguageList()}
                </div>

                ${this.renderRotationControls()}
            </div>
        `;

        // Append to body
        document.body.appendChild(this.container);

        // Store references
        this.button = document.getElementById('language-btn');
        this.dropdown = document.getElementById('language-dropdown');
        this.searchInput = document.getElementById('language-search');
        this.languageList = document.getElementById('language-list');

        console.log('[LanguageSelector] UI rendered');
    }

    /**
     * Render language list
     */
    renderLanguageList() {
        const languages = this.searchQuery
            ? this.filteredLanguages
            : this.languageManager.getAvailableLanguages();

        if (languages.length === 0) {
            return `
                <div class="language-empty">
                    <p>No languages found</p>
                </div>
            `;
        }

        const currentCode = this.languageManager.getCurrentLanguage();

        return languages.map(lang => {
            const isActive = lang.code === currentCode;
            const flagEmoji = this.getFlagEmoji(lang.code);

            return `
                <button class="language-item ${isActive ? 'active' : ''}"
                        data-lang="${lang.code}"
                        title="${lang.name}">
                    <span class="flag-icon">${flagEmoji}</span>
                    <div class="language-info">
                        <span class="language-name">${lang.name}</span>
                        <span class="language-native">${lang.native_name}</span>
                    </div>
                    ${isActive ? '<span class="check-icon">✓</span>' : ''}
                </button>
            `;
        }).join('');
    }

    /**
     * Render rotation controls
     */
    renderRotationControls() {
        const isRotating = this.languageManager.isRotationActive();
        const interval = this.languageManager.rotationInterval;

        return `
            <div class="language-rotation">
                <div class="rotation-header">
                    <span>Language Rotation</span>
                    <label class="rotation-toggle">
                        <input type="checkbox"
                               id="rotation-toggle"
                               ${isRotating ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </label>
                </div>

                <div class="rotation-settings" ${isRotating ? '' : 'style="display: none;"'}>
                    <label for="rotation-interval">
                        Interval: <strong id="rotation-interval-value">${interval}</strong>s
                    </label>
                    <input type="range"
                           id="rotation-interval"
                           min="5"
                           max="120"
                           step="5"
                           value="${interval}">
                </div>
            </div>
        `;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Toggle dropdown on button click
        this.button.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggle();
        });

        // Close button
        const closeBtn = document.getElementById('language-close');
        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.close();
        });

        // Language selection
        this.languageList.addEventListener('click', (e) => {
            const item = e.target.closest('.language-item');
            if (item) {
                const langCode = item.dataset.lang;
                this.selectLanguage(langCode);
            }
        });

        // Search input
        this.searchInput.addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });

        // Rotation toggle
        const rotationToggle = document.getElementById('rotation-toggle');
        rotationToggle.addEventListener('change', (e) => {
            this.handleRotationToggle(e.target.checked);
        });

        // Rotation interval slider
        const intervalSlider = document.getElementById('rotation-interval');
        intervalSlider.addEventListener('input', (e) => {
            this.handleRotationIntervalChange(parseInt(e.target.value));
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (this.isOpen && !this.container.contains(e.target)) {
                this.close();
            }
        });

        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });

        // Listen to language manager events
        this.languageManager.addEventListener('language-changed', (e) => {
            this.handleLanguageChange(e.detail);
        });

        this.languageManager.addEventListener('rotation-started', () => {
            this.updateRotationUI(true);
        });

        this.languageManager.addEventListener('rotation-stopped', () => {
            this.updateRotationUI(false);
        });

        console.log('[LanguageSelector] Event listeners attached');
    }

    /**
     * Toggle dropdown
     */
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    /**
     * Open dropdown
     */
    open() {
        this.isOpen = true;
        this.dropdown.classList.add('visible');
        this.button.classList.add('active');

        // Focus search input
        setTimeout(() => {
            this.searchInput.focus();
        }, 100);

        console.log('[LanguageSelector] Opened');
    }

    /**
     * Close dropdown
     */
    close() {
        this.isOpen = false;
        this.dropdown.classList.remove('visible');
        this.button.classList.add('active');

        // Clear search
        this.searchInput.value = '';
        this.searchQuery = '';
        this.updateLanguageList();

        console.log('[LanguageSelector] Closed');
    }

    /**
     * Select language
     */
    selectLanguage(langCode) {
        console.log('[LanguageSelector] Language selected:', langCode);

        // Stop rotation if active (user manual selection)
        if (this.languageManager.isRotationActive()) {
            this.languageManager.stopRotation();
            this.showNotification('Language rotation stopped');
        }

        // Set language
        this.languageManager.setLanguage(langCode, 'manual');

        // Close dropdown
        this.close();

        // Show notification
        const langInfo = this.languageManager.getLanguageInfo(langCode);
        this.showNotification(`Language changed to ${langInfo.native_name}`);
    }

    /**
     * Handle search
     */
    handleSearch(query) {
        this.searchQuery = query.toLowerCase().trim();

        if (this.searchQuery === '') {
            this.filteredLanguages = [];
        } else {
            // Filter languages by name or native name
            this.filteredLanguages = this.languageManager.getAvailableLanguages().filter(lang => {
                return lang.name.toLowerCase().includes(this.searchQuery) ||
                       lang.native_name.toLowerCase().includes(this.searchQuery) ||
                       lang.code.toLowerCase().includes(this.searchQuery);
            });
        }

        this.updateLanguageList();
    }

    /**
     * Handle rotation toggle
     */
    handleRotationToggle(enabled) {
        console.log('[LanguageSelector] Rotation toggle:', enabled);

        if (enabled) {
            this.languageManager.startRotation();
            this.showNotification('Language rotation started');

            // Show rotation settings
            document.querySelector('.rotation-settings').style.display = 'block';
        } else {
            this.languageManager.stopRotation();
            this.showNotification('Language rotation stopped');

            // Hide rotation settings
            document.querySelector('.rotation-settings').style.display = 'none';
        }
    }

    /**
     * Handle rotation interval change
     */
    handleRotationIntervalChange(seconds) {
        // Update value display
        document.getElementById('rotation-interval-value').textContent = seconds;

        // Update language manager
        this.languageManager.setRotationInterval(seconds);

        console.log('[LanguageSelector] Rotation interval changed to:', seconds);
    }

    /**
     * Handle language change event
     */
    handleLanguageChange(detail) {
        console.log('[LanguageSelector] Language changed:', detail);

        // Update button
        this.updateButton(detail.newLang);

        // Update language list
        this.updateLanguageList();
    }

    /**
     * Update button UI
     */
    updateButton(langCode) {
        const flagIcon = this.button.querySelector('.flag-icon');
        const codeSpan = this.button.querySelector('.language-code');

        flagIcon.textContent = this.getFlagEmoji(langCode);
        flagIcon.dataset.lang = langCode;
        codeSpan.textContent = langCode.toUpperCase();
    }

    /**
     * Update language list
     */
    updateLanguageList() {
        this.languageList.innerHTML = this.renderLanguageList();
    }

    /**
     * Update rotation UI
     */
    updateRotationUI(isActive) {
        const toggle = document.getElementById('rotation-toggle');
        const settings = document.querySelector('.rotation-settings');

        toggle.checked = isActive;
        settings.style.display = isActive ? 'block' : 'none';
    }

    /**
     * Show notification
     */
    showNotification(message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'language-notification';
        notification.textContent = message;

        document.body.appendChild(notification);

        // Trigger animation
        setTimeout(() => {
            notification.classList.add('visible');
        }, 10);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('visible');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    /**
     * Get flag emoji for language code
     */
    getFlagEmoji(langCode) {
        // Map language codes to flag emojis
        const flagMap = {
            'en': '🇬🇧',
            'id': '🇮🇩',
            'zh': '🇨🇳',
            'ja': '🇯🇵',
            'ko': '🇰🇷',
            'ar': '🇸🇦',
            'es': '🇪🇸',
            'fr': '🇫🇷',
            'de': '🇩🇪',
            'ru': '🇷🇺',
            'pt': '🇵🇹',
            'it': '🇮🇹',
            'nl': '🇳🇱',
            'tr': '🇹🇷',
            'pl': '🇵🇱',
            'vi': '🇻🇳',
            'th': '🇹🇭',
            'hi': '🇮🇳',
            'bn': '🇧🇩',
            'ms': '🇲🇾'
        };

        return flagMap[langCode] || '🌐';
    }

    /**
     * Destroy selector
     */
    destroy() {
        if (this.container) {
            this.container.remove();
        }
        console.log('[LanguageSelector] Destroyed');
    }
}

// Export for global use
window.LanguageSelector = LanguageSelector;

console.log('[LanguageSelector] Module loaded');
