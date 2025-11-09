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
   */
  render(containerId = 'shell-container'): void {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      SharedLogger.error('[ShellActivationScreen] Container not found:', containerId);
      return;
    }

    const activationCode = SharedDeviceState.getDeviceCode();
    const deviceId = SharedDeviceState.getDeviceId();
    const platform = SharedDeviceState.getPlatform();

    SharedLogger.log('[ShellActivationScreen] Rendering activation screen...', {
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
            Digital Signage
          </h1>

          <div id="activation-code">
            ${activationCode || '------'}
          </div>

          <div class="spinner"></div>

          <p id="status-message">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline-block; vertical-align: middle; margin-right: 6px;">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            Initializing...
          </p>

          <p id="activation-instruction" style="margin-top: 1.5rem; font-size: 1rem; opacity: 0.8;">
            Daftarkan kode ini di CMS untuk menambahkan device ke organisasi Anda
          </p>
        </div>
      </div>
    `;

    // Add styles
    this.injectStyles();

    // Store references
    this.codeElement = document.getElementById('activation-code');
    this.statusElement = document.getElementById('status-message');

    SharedLogger.log('[ShellActivationScreen] ✅ Activation screen rendered');
  }

  /**
   * Update activation code display
   */
  updateCode(newCode: string): void {
    if (this.codeElement) {
      this.codeElement.textContent = newCode;
      SharedLogger.log('[ShellActivationScreen] Code updated:', newCode);
    }
  }

  /**
   * Update status message
   */
  updateStatus(message: string, type: 'waiting' | 'success' | 'error' = 'waiting'): void {
    if (this.statusElement) {
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

// Make available globally for compatibility
declare global {
  interface Window {
    ShellActivationScreen: typeof ShellActivationScreen;
  }
}

if (typeof window !== 'undefined') {
  window.ShellActivationScreen = ShellActivationScreen;
}
