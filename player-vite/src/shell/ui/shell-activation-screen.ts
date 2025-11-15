/**
 * Shell Activation Screen
 * UI component for displaying device activation code
 *
 * @features
 * - Displays 6-digit activation code
 * - Shows device information
 * - Auto-updates on state changes
 * - Responsive design with Tailwind-style classes
 */

import { SharedLogger } from '@shared/logger';
import { SharedDeviceState } from '@shared/device';
import { deviceConfigStorage } from '@shared/storage';
import { i18n } from '@shared/services/i18n';

/**
 * Shell Activation Screen Class
 * Manages the activation UI
 */
class ShellActivationScreenClass {
  private container: HTMLElement | null = null;
  private codeElement: HTMLElement | null = null;
  private statusElement: HTMLElement | null = null;

  /**
   * Render activation screen
   * Now async to load activation code from IndexedDB
   */
  async render(containerId = 'shell-container'): Promise<void> {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      SharedLogger.error('[ShellActivationScreen] Container not found:', containerId);
      return;
    }

    // Get activation code from IndexedDB (persistent across cache clears)
    const pendingCode = await deviceConfigStorage.getActivationCode();
    const activationCode = pendingCode || SharedDeviceState.getDeviceCode();
    const deviceId = SharedDeviceState.getDeviceId();
    const platform = SharedDeviceState.getPlatform();

    SharedLogger.log('[ShellActivationScreen] Rendering activation screen...', {
      pendingCode_from_indexeddb: pendingCode,
      activationCode,
      deviceId,
      platform,
    });

    this.container.innerHTML = `
      <div id="activation-screen">
        <div class="activation-card">
          <h1>
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline-block; vertical-align: middle; margin-right: 8px;">
              <rect width="20" height="14" x="2" y="3" rx="2"/>
              <line x1="8" x2="16" y1="21" y2="21"/>
              <line x1="12" x2="12" y1="17" y2="21"/>
            </svg>
            ${i18n.t('activation.title')}
          </h1>

          <div id="activation-code">
            ${activationCode || '______'}
          </div>

          <div class="spinner"></div>

          <p id="status-message">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline-block; vertical-align: middle; margin-right: 6px;">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            ${activationCode ? i18n.t('activation.waiting') : 'Generating activation code...'}
          </p>

          <p id="activation-instruction" style="margin-top: 1.5rem; font-size: 1rem; opacity: 0.8;">
            ${i18n.t('activation.instruction')}
          </p>
          
          <!-- Language Selector -->
          <div class="language-selector" style="margin-top: 2rem;">
            <label style="display: block; margin-bottom: 0.5rem; opacity: 0.7;">
              ${i18n.t('common.language')}:
            </label>
            <select id="language-select" class="language-dropdown">
              ${this.renderLanguageOptions()}
            </select>
          </div>
        </div>
      </div>
    `;

    // Add styles
    this.injectStyles();

    // Store references
    this.codeElement = document.getElementById('activation-code');
    this.statusElement = document.getElementById('status-message');

    SharedLogger.log('[ShellActivationScreen] ✅ Activation screen rendered');
    
    // Add language change handler
    const languageSelect = document.getElementById('language-select') as HTMLSelectElement;
    if (languageSelect) {
      languageSelect.addEventListener('change', (e) => {
        const target = e.target as HTMLSelectElement;
        i18n.setLanguage(target.value);
        // Re-render to update translations
        this.render(containerId);
      });
    }
  }

  /**
   * Update activation code display
   */
  updateCode(newCode: string): void {
    // Try to use cached element first
    if (!this.codeElement) {
      // Re-query element if not cached (in case render was called before)
      this.codeElement = document.getElementById('activation-code');
    }

    if (this.codeElement) {
      this.codeElement.textContent = newCode;
      SharedLogger.log('[ShellActivationScreen] Code updated:', newCode);
    } else {
      SharedLogger.warn('[ShellActivationScreen] Cannot update code - element not found');
    }
  }

  /**
   * Update status message
   */
  updateStatus(messageKey: string | { key: string, params?: Record<string, any> }, type: 'waiting' | 'success' | 'error' = 'waiting'): void {
    if (this.statusElement) {
      // Get translated message
      let message: string;
      if (typeof messageKey === 'string') {
        // Try to translate the key first, fallback to the original message
        message = i18n.t(messageKey);
        // If no translation found (returns the key), use the original message
        if (message === messageKey && !messageKey.includes('.')) {
          message = messageKey; // It's probably a raw message, not a key
        }
      } else {
        message = i18n.t(messageKey.key, messageKey.params);
      }
      
      // Update text content (keep the icon SVG)
      const icon = this.statusElement.querySelector('svg');
      if (icon) {
        this.statusElement.innerHTML = icon.outerHTML + ' ' + message;
      } else {
        this.statusElement.textContent = message;
      }

      SharedLogger.log('[ShellActivationScreen] Status updated:', { message, type });
    }
  }

  /**
   * Show error message
   */
  showError(errorMessage: string): void {
    this.updateStatus(errorMessage, 'error');
  }

  /**
   * Show success message
   */
  showSuccess(successMessage: string): void {
    this.updateStatus(successMessage, 'success');
  }

  /**
   * Inject CSS styles
   */
  private injectStyles(): void {
    const existingStyle = document.getElementById('shell-activation-styles');
    if (existingStyle) return;

    const style = document.createElement('style');
    style.id = 'shell-activation-styles';
    style.textContent = `
      /* Activation Screen - Exact copy from player-vanillajs/styles/shell.css */
      #activation-screen {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        text-align: center;
        padding: 2rem;
        position: relative;
        z-index: 1000;
      }

      .activation-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 3rem;
        backdrop-filter: blur(16px);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        max-width: 600px;
        color: white;
      }

      .activation-card h1,
      #activation-screen h1 {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        color: white;
        font-weight: 600;
      }

      #activation-code {
        font-size: 5rem;
        font-weight: bold;
        font-family: 'Courier New', monospace;
        padding: 1.5rem 3rem;
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        margin: 2rem 0;
        letter-spacing: 0.3rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        color: white;
      }

      .loader-icon {
        display: inline-block;
        opacity: 0.5;
        animation: spin 1s linear infinite;
      }

      .spinner {
        width: 60px;
        height: 60px;
        border: 5px solid rgba(255, 255, 255, 0.3);
        border-top-color: white;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 2rem auto;
      }

      @keyframes spin {
        to { transform: rotate(360deg); }
      }

      #status-message {
        font-size: 1.5rem;
        margin: 1.5rem 0;
        color: white;
      }

      #activation-instruction {
        margin-top: 1.5rem;
        font-size: 1rem;
        opacity: 0.8;
        color: white;
      }

      /* Language Selector Styles */
      .language-selector {
        margin-top: 2rem;
        text-align: center;
      }
      
      .language-dropdown {
        background-color: rgba(255, 255, 255, 0.1);
        color: #fff;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        min-width: 150px;
      }
      
      .language-dropdown:hover {
        background-color: rgba(255, 255, 255, 0.2);
        border-color: rgba(255, 255, 255, 0.3);
      }
      
      .language-dropdown:focus {
        outline: none;
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
      }
      
      .language-dropdown option {
        background-color: #1f2937;
        color: #fff;
      }

      /* Responsive */
      @media (max-width: 640px) {
        .activation-card h1,
        #activation-screen h1 {
          font-size: 2rem;
        }
        #activation-code {
          font-size: 3rem;
          letter-spacing: 0.2rem;
          padding: 1rem 2rem;
        }
        #status-message {
          font-size: 1.25rem;
        }
      }
    `;

    document.head.appendChild(style);
  }

  /**
   * Render language options
   */
  private renderLanguageOptions(): string {
    const languages = i18n.getAvailableLanguages();
    const currentLang = i18n.getLanguage();
    
    return languages.map(lang => `
      <option value="${lang.code}" ${lang.code === currentLang ? 'selected' : ''}>
        ${lang.name}
      </option>
    `).join('');
  }

  /**
   * Hide activation screen
   */
  hide(): void {
    if (this.container) {
      this.container.style.display = 'none';
    }
  }

  /**
   * Show activation screen
   */
  show(): void {
    if (this.container) {
      this.container.style.display = 'block';
    }
  }
}

// Export singleton instance
export const ShellActivationScreen = new ShellActivationScreenClass();

// Export type for global window declaration
export type { ShellActivationScreenClass };

// Make available globally for compatibility
if (typeof window !== 'undefined') {
  (window as any).ShellActivationScreen = ShellActivationScreen;
}
