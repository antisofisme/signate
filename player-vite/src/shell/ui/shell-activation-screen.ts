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
import { SharedModal } from '@shared/ui';

/**
 * Shell Activation Screen Class
 * Manages the activation UI
 */
class ShellActivationScreenClass {
  private container: HTMLElement | null = null;
  private codeElement: HTMLElement | null = null;
  private statusElement: HTMLElement | null = null;
  private countdownElement: HTMLElement | null = null;
  private countdownInterval: number | null = null;
  private expiredModalTimeout: number | null = null;
  private expiresAt: Date | null = null;
  private isShowingExpiredModal: boolean = false; // SINGLE FLAG to prevent multiple modals

  /**
   * Render activation screen
   */
  render(containerId = 'shell-container'): void {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      SharedLogger.error('[ShellActivationScreen] Container not found:', containerId);
      return;
    }

    // Get activation code - try pending code first (during registration), fallback to device_code
    const pendingCode = localStorage.getItem('pending_activation_code');
    const activationCode = pendingCode || SharedDeviceState.getDeviceCode();
    const deviceId = SharedDeviceState.getDeviceId();
    const platform = SharedDeviceState.getPlatform();

    SharedLogger.log('[ShellActivationScreen] Rendering activation screen...', {
      pendingCode,
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

          <p id="code-countdown" style="margin-top: 1rem; font-size: 1rem; opacity: 0.9; color: #f59e0b;">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: inline-block; vertical-align: middle; margin-right: 6px;">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            Code expires in: <span id="countdown-timer">--:--</span>
          </p>

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
    this.countdownElement = document.getElementById('countdown-timer');

    // Restore countdown timer from localStorage if available
    const savedExpiresAt = SharedDeviceState.getCodeExpiresAt();
    if (savedExpiresAt) {
      SharedLogger.log('[ShellActivationScreen] Restoring countdown from localStorage:', savedExpiresAt);
      this.startCountdown(savedExpiresAt);
    }

    SharedLogger.log('[ShellActivationScreen] ✅ Activation screen rendered');
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
   * Start countdown timer
   * @param expiresAt - ISO timestamp when code expires
   */
  startCountdown(expiresAt: string): void {
    try {
      SharedLogger.log('[ShellActivationScreen] 🕐 startCountdown called with:', expiresAt);

      // Parse and validate date FIRST
      const newExpiresAt = new Date(expiresAt);
      if (isNaN(newExpiresAt.getTime())) {
        SharedLogger.error('[ShellActivationScreen] ❌ Invalid date:', expiresAt);
        return;
      }

      // Check if already expired BEFORE starting countdown
      const now = new Date();
      if (newExpiresAt.getTime() <= now.getTime()) {
        SharedLogger.warn('[ShellActivationScreen] ⚠️ Code already expired, not starting countdown');
        return;
      }

      // CRITICAL FIX: Stop ANY existing countdown FIRST (prevents multiple intervals)
      this.stopCountdown();

      // Clear any pending modal timeouts
      if (this.expiredModalTimeout !== null) {
        clearTimeout(this.expiredModalTimeout);
        this.expiredModalTimeout = null;
      }

      // Reset flag AFTER stopping (not before) - only if not currently showing
      if (!this.isShowingExpiredModal) {
        this.isShowingExpiredModal = false;
      }

      this.expiresAt = newExpiresAt;
      SharedLogger.log('[ShellActivationScreen] 🕐 Parsed expiresAt:', this.expiresAt);

      // Update immediately
      SharedLogger.log('[ShellActivationScreen] 🕐 Calling updateCountdown() immediately...');
      this.updateCountdown();

      // Start new interval
      this.countdownInterval = window.setInterval(() => {
        this.updateCountdown();
      }, 1000);

      SharedLogger.log('[ShellActivationScreen] ✅ Countdown started (single interval), ID:', this.countdownInterval);
    } catch (error) {
      SharedLogger.error('[ShellActivationScreen] ❌ Failed to start countdown:', error);
    }
  }

  /**
   * Stop countdown timer
   */
  stopCountdown(): void {
    if (this.countdownInterval !== null) {
      clearInterval(this.countdownInterval);
      this.countdownInterval = null;
      SharedLogger.log('[ShellActivationScreen] Countdown stopped');
    }
  }

  /**
   * Check if countdown is running
   */
  isCountdownRunning(): boolean {
    return this.countdownInterval !== null;
  }

  /**
   * Update countdown display
   */
  private updateCountdown(): void {
    // Guard: Don't update if modal is already showing
    if (this.isShowingExpiredModal) {
      SharedLogger.warn('[ShellActivationScreen] ⏸️ BLOCKED - Modal already showing, skipping updateCountdown');
      // Stop countdown to prevent further calls when modal is active
      this.stopCountdown();
      return;
    }

    // Guard: No expiration date set
    if (!this.expiresAt) {
      return;
    }

    // Re-query element if not cached (similar to updateCode)
    if (!this.countdownElement) {
      this.countdownElement = document.getElementById('countdown-timer');
    }

    if (!this.countdownElement) {
      return;
    }

    const now = new Date();
    const diffMs = this.expiresAt.getTime() - now.getTime();

    // If expired
    if (diffMs <= 0) {
      // Check if already handled
      if (this.isShowingExpiredModal) {
        SharedLogger.warn('[ShellActivationScreen] ⏸️ BLOCKED - Flag already set, not showing modal again');
        return; // Already handled, don't proceed
      }

      SharedLogger.error('[ShellActivationScreen] ⏰ CODE EXPIRED! diffMs:', diffMs, 'flag:', this.isShowingExpiredModal);

      // CRITICAL FIX: Set flag FIRST to prevent re-entry
      this.isShowingExpiredModal = true;
      SharedLogger.error('[ShellActivationScreen] 🚩 Flag set to TRUE');

      // CRITICAL FIX: Stop countdown IMMEDIATELY BEFORE async call
      // This prevents interval from triggering updateCountdown() again
      // while showExpiredModal() is still awaiting user response
      this.stopCountdown();
      SharedLogger.error('[ShellActivationScreen] ⏹️ Countdown stopped');

      // Clear expiresAt to prevent any further checks
      this.expiresAt = null;
      SharedLogger.error('[ShellActivationScreen] 🗑️ expiresAt cleared');

      // Update UI
      this.countdownElement.textContent = 'EXPIRED';
      this.countdownElement.style.color = '#ef4444';

      // CRITICAL FIX: Use setTimeout to break out of interval context
      // This ensures interval is fully stopped before showing modal
      setTimeout(() => {
        SharedLogger.error('[ShellActivationScreen] 🚨 setTimeout fired - Calling showExpiredModal()...');
        this.showExpiredModal()
          .catch((error) => {
            SharedLogger.error('[ShellActivationScreen] ❌ Failed to show modal:', error);
            setTimeout(() => location.reload(), 2000);
          });
      }, 50); // Small delay to ensure interval is fully cleared

      return;
    }

    // Calculate minutes and seconds
    const totalSeconds = Math.floor(diffMs / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    // Format as MM:SS
    const formatted = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    this.countdownElement.textContent = formatted;

    // Change color based on time remaining
    if (totalSeconds < 60) {
      // Last minute - red
      this.countdownElement.style.color = '#ef4444';
    } else if (totalSeconds < 180) {
      // Last 3 minutes - yellow
      this.countdownElement.style.color = '#f59e0b';
    } else {
      // Normal - orange
      this.countdownElement.style.color = '#f59e0b';
    }
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

      /* Countdown Timer */
      #code-countdown {
        margin-top: 1rem;
        font-size: 1rem;
        opacity: 0.9;
        color: #f59e0b;
        font-weight: 500;
      }

      #countdown-timer {
        font-family: 'Courier New', monospace;
        font-weight: bold;
        font-size: 1.1rem;
        padding: 0.25rem 0.5rem;
        background: rgba(245, 158, 11, 0.1);
        border-radius: 6px;
        transition: color 0.3s ease;
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
    // Stop countdown when hiding screen
    this.stopCountdown();
  }

  /**
   * Show activation screen
   */
  show(): void {
    if (this.container) {
      this.container.style.display = 'block';
    }
  }

  /**
   * Show expired code modal with regenerate option
   * NOTE: Called from setTimeout, so interval is already stopped
   */
  private async showExpiredModal(): Promise<void> {
    SharedLogger.log('[ShellActivationScreen] 📢 Showing expired modal...');

    try {
      // Show confirmation modal
      const regenerate = await SharedModal.confirm(
        'Activation Code Expired',
        'Kode aktivasi telah kadaluarsa (10 menit). Apakah Anda ingin generate kode baru?',
        'Generate Kode Baru',
        'Tidak'
      );

      if (regenerate) {
        SharedLogger.log('[ShellActivationScreen] User chose to regenerate code');

        // Clear old device data and pending code
        SharedDeviceState.clearDeviceData({ preserveAuth: false });
        localStorage.removeItem('pending_activation_code');
        localStorage.removeItem('code_expires_at');

        // Reset expired modal flag
        this.isShowingExpiredModal = false;

        // Reload page to trigger new registration
        SharedLogger.log('[ShellActivationScreen] Reloading page to generate new code...');
        setTimeout(() => location.reload(), 500);
      } else {
        SharedLogger.log('[ShellActivationScreen] User chose NOT to regenerate code');
        // Don't show status message - user already knows from modal choice
      }
    } finally {
      this.isShowingExpiredModal = false;
    }
  }
}

// Export singleton instance
export const ShellActivationScreen = new ShellActivationScreenClass();

// Export type for global window declaration
export type { ShellActivationScreenClass };

// Make available globally for compatibility
declare global {
  interface Window {
    ShellActivationScreen: typeof ShellActivationScreen;
  }
}

if (typeof window !== 'undefined') {
  window.ShellActivationScreen = ShellActivationScreen;
}
