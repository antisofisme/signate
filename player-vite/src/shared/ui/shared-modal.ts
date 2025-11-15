/**
 * Shared Modal Component
 * Reusable modal dialog system
 */

import { SharedLogger } from '@shared/logger';
import { SharedEventBus, EventNames } from '@shared/events/shared-event-bus';
import { ServiceRegistry } from '@shared/services/service-registry';

export interface ModalOptions {
  title: string;
  message: string;
  type?: 'info' | 'warning' | 'error' | 'success';
  confirmText?: string;
  cancelText?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
}

export interface CustomModalOptions {
  title?: string;
  content: string | HTMLElement; // Support both HTML string and elements
  width?: string; // e.g., '800px', '90%'
  maxWidth?: string;
  showCloseButton?: boolean;
  onClose?: () => void;
  className?: string; // Additional CSS classes
}

class SharedModalClass {
  private modalElement: HTMLElement | null = null;
  private isProcessing: boolean = false; // Prevent rapid consecutive calls

  show(options: ModalOptions): void {
    // Silently remove existing modal without triggering close() checks
    if (this.modalElement) {
      this.modalElement.remove();
      this.modalElement = null;
    }

    const {
      title,
      message,
      type = 'info',
      confirmText = 'OK',
      cancelText,
      onConfirm,
      onCancel,
    } = options;

    // Get icon based on type
    const getIcon = (modalType: string) => {
      switch (modalType) {
        case 'success':
          return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';
        case 'warning':
          return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>';
        case 'error':
          return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>';
        case 'info':
        default:
          return '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>';
      }
    };

    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="modal-container modal-${type}">
        <div class="modal-header">
          <h3>
            ${getIcon(type)}
            ${title}
          </h3>
          <button class="modal-close">&times;</button>
        </div>
        <div class="modal-body">
          <p>${message}</p>
        </div>
        <div class="modal-footer">
          ${cancelText ? `<button class="modal-btn modal-cancel">${cancelText}</button>` : ''}
          <button class="modal-btn modal-confirm">${confirmText}</button>
        </div>
      </div>
    `;

    this.injectStyles();

    const closeBtn = modal.querySelector('.modal-close');
    const confirmBtn = modal.querySelector('.modal-confirm');
    const cancelBtn = modal.querySelector('.modal-cancel');

    const handleClose = () => {
      this.close();
      onCancel?.();
    };

    const handleConfirm = () => {
      this.close();
      onConfirm?.();
    };

    closeBtn?.addEventListener('click', handleClose);
    confirmBtn?.addEventListener('click', handleConfirm);
    cancelBtn?.addEventListener('click', handleClose);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) handleClose();
    });

    document.body.appendChild(modal);
    this.modalElement = modal;

    // Trigger fade-in animation
    requestAnimationFrame(() => {
      modal.classList.add('show');
    });

    SharedEventBus.emit(EventNames.UI_MODAL_OPEN, options);
    SharedLogger.log('[Modal] Opened:', title);
  }

  close(): void {
    // Don't close if currently processing (prevent race condition)
    if (this.isProcessing) {
      SharedLogger.warn('[Modal] Cannot close - modal is processing');
      return;
    }

    if (this.modalElement) {
      const modal = this.modalElement;

      // Fade-out animation before removal
      modal.classList.remove('show');

      // Wait for animation to complete (200ms) before removing
      setTimeout(() => {
        modal.remove();
        SharedEventBus.emit(EventNames.UI_MODAL_CLOSE);
        SharedLogger.log('[Modal] Closed');
      }, 200);

      this.modalElement = null;
    }
  }

  /**
   * Show confirm modal with Yes/No buttons
   * Returns Promise that resolves with true (confirmed) or false (cancelled)
   */
  async confirm(
    title: string,
    message: string,
    confirmText: string = 'Yes',
    cancelText: string = 'No'
  ): Promise<boolean> {
    SharedLogger.log('[Modal] 🔵 confirm() called, isProcessing:', this.isProcessing, 'modalElement exists:', !!this.modalElement);

    // CRITICAL FIX: Wait for existing modal instead of returning false
    if (this.isProcessing) {
      SharedLogger.warn('[Modal] ⚠️ Already showing modal, waiting for completion...');

      // Wait for current modal to finish (max 30 seconds)
      return new Promise((resolve) => {
        const startTime = Date.now();
        const checkInterval = setInterval(() => {
          if (!this.isProcessing || Date.now() - startTime > 30000) {
            clearInterval(checkInterval);
            SharedLogger.log('[Modal] ⏳ Wait completed, returning false');
            resolve(false); // Timeout or completed
          }
        }, 100);
      });
    }

    SharedLogger.log('[Modal] 🟢 Setting isProcessing = true');
    this.isProcessing = true;

    // CRITICAL FIX: Don't close existing modal - just replace it
    // Calling close() causes flicker (remove old → create new)
    // Instead, remove old modal silently if exists
    if (this.modalElement) {
      SharedLogger.log('[Modal] 🗑️ Removing existing modal element...');
      this.modalElement.remove();
      this.modalElement = null;
      SharedLogger.log('[Modal] ✅ Existing modal removed');
    }

    return new Promise((resolve) => {
      const modal = document.createElement('div');
      modal.className = 'modal-overlay';
      modal.innerHTML = `
        <div class="modal-container modal-warning">
          <div class="modal-header">
            <h3>
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
              ${title}
            </h3>
            <button class="modal-close">&times;</button>
          </div>
          <div class="modal-body">
            <p>${message}</p>
          </div>
          <div class="modal-footer">
            <button class="modal-btn modal-cancel">${cancelText}</button>
            <button class="modal-btn modal-confirm">${confirmText}</button>
          </div>
        </div>
      `;

      this.injectStyles();

      const confirmBtn = modal.querySelector('.modal-confirm') as HTMLButtonElement;
      const cancelBtn = modal.querySelector('.modal-cancel') as HTMLButtonElement;
      const closeBtn = modal.querySelector('.modal-close') as HTMLButtonElement;

      const handleCancel = () => {
        SharedLogger.log('[Modal] 🔴 Cancel clicked');
        this.isProcessing = false; // Reset FIRST
        this.close();
        resolve(false); // User cancelled
      };

      const handleConfirm = () => {
        SharedLogger.log('[Modal] 🟢 Confirm clicked');
        this.isProcessing = false; // Reset FIRST
        this.close();
        resolve(true); // User confirmed
      };

      confirmBtn?.addEventListener('click', handleConfirm);
      cancelBtn?.addEventListener('click', handleCancel);
      closeBtn?.addEventListener('click', handleCancel);
      SharedLogger.log('[Modal] 📌 Event listeners attached');
      // Disable click outside to close for confirm modal (force user to make a choice)
      // modal.addEventListener('click', (e) => {
      //   if (e.target === modal) handleClose();
      // });

      SharedLogger.log('[Modal] 🏗️ Appending modal to DOM...');

      // Append to DOM immediately (no requestAnimationFrame nesting)
      document.body.appendChild(modal);
      this.modalElement = modal;
      SharedLogger.log('[Modal] ✅ Modal appended to DOM');

      // Trigger fade-in animation
      requestAnimationFrame(() => {
        modal.classList.add('show');
      });

      SharedEventBus.emit(EventNames.UI_MODAL_OPEN, { title, message });
      SharedLogger.log('[Modal] 📢 Confirm opened:', title);
    });
  }

  /**
   * Show prompt modal with password input
   * Returns Promise that resolves with password or rejects if cancelled
   */
  async prompt(title: string, message: string, inputType: 'text' | 'password' = 'password'): Promise<string> {
    // Silently remove existing modal without triggering close() checks
    if (this.modalElement) {
      this.modalElement.remove();
      this.modalElement = null;
    }

    return new Promise((resolve, reject) => {
      const modal = document.createElement('div');
      modal.className = 'modal-overlay';
      modal.innerHTML = `
        <div class="modal-container modal-warning">
          <div class="modal-header">
            <h3>
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
              ${title}
            </h3>
            <button class="modal-close">&times;</button>
          </div>
          <div class="modal-body">
            <p style="margin-bottom: 1rem;">${message}</p>
            <input
              type="${inputType}"
              class="modal-input"
              placeholder="${inputType === 'password' ? 'Enter password' : 'Enter value'}"
              autofocus
            />
          </div>
          <div class="modal-footer">
            <button class="modal-btn modal-cancel">Cancel</button>
            <button class="modal-btn modal-confirm">Confirm</button>
          </div>
        </div>
      `;

      this.injectStyles();

      const closeBtn = modal.querySelector('.modal-close') as HTMLButtonElement;
      const confirmBtn = modal.querySelector('.modal-confirm') as HTMLButtonElement;
      const cancelBtn = modal.querySelector('.modal-cancel') as HTMLButtonElement;
      const input = modal.querySelector('.modal-input') as HTMLInputElement;

      const handleClose = () => {
        this.close();
        reject(new Error('Modal cancelled'));
      };

      const handleConfirm = () => {
        const value = input.value.trim();
        this.close();
        if (value) {
          resolve(value);
        } else {
          reject(new Error('No input provided'));
        }
      };

      // Enter key to submit
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          handleConfirm();
        } else if (e.key === 'Escape') {
          handleClose();
        }
      });

      closeBtn?.addEventListener('click', handleClose);
      confirmBtn?.addEventListener('click', handleConfirm);
      cancelBtn?.addEventListener('click', handleClose);
      modal.addEventListener('click', (e) => {
        if (e.target === modal) handleClose();
      });

      document.body.appendChild(modal);
      this.modalElement = modal;

      // Trigger fade-in animation
      requestAnimationFrame(() => {
        modal.classList.add('show');
      });

      // Focus input after a short delay
      setTimeout(() => input.focus(), 100);

      SharedEventBus.emit(EventNames.UI_MODAL_OPEN, { title, message });
      SharedLogger.log('[Modal] Prompt opened:', title);
    });
  }

  /**
   * Show custom modal with complex HTML content
   * Perfect for popups with tabs, tables, forms, etc.
   */
  showCustom(options: CustomModalOptions): HTMLElement {
    // Silently remove existing modal
    if (this.modalElement) {
      this.modalElement.remove();
      this.modalElement = null;
    }

    const {
      title,
      content,
      width = '90%',
      maxWidth = '1200px',
      showCloseButton = true,
      onClose,
      className = '',
    } = options;

    const overlay = document.createElement('div');
    overlay.className = `modal-overlay modal-custom ${className}`;

    const container = document.createElement('div');
    container.className = 'modal-container modal-custom-container';
    container.style.width = width;
    container.style.maxWidth = maxWidth;

    // Build header if title provided
    if (title || showCloseButton) {
      const header = document.createElement('div');
      header.className = 'modal-header';

      if (title) {
        const titleElement = document.createElement('h3');
        titleElement.textContent = title;
        header.appendChild(titleElement);
      }

      if (showCloseButton) {
        const closeBtn = document.createElement('button');
        closeBtn.className = 'modal-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.addEventListener('click', () => {
          this.close();
          onClose?.();
        });
        header.appendChild(closeBtn);
      }

      container.appendChild(header);
    }

    // Build body
    const body = document.createElement('div');
    body.className = 'modal-body modal-custom-body';

    if (typeof content === 'string') {
      body.innerHTML = content;
    } else {
      body.appendChild(content);
    }

    container.appendChild(body);
    overlay.appendChild(container);

    // Close on overlay click
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        this.close();
        onClose?.();
      }
    });

    // Close on Escape key
    const escapeHandler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        this.close();
        onClose?.();
        document.removeEventListener('keydown', escapeHandler);
      }
    };
    document.addEventListener('keydown', escapeHandler);

    this.injectStyles();

    document.body.appendChild(overlay);
    this.modalElement = overlay;

    // Trigger fade-in animation
    requestAnimationFrame(() => {
      overlay.classList.add('show');
    });

    SharedEventBus.emit(EventNames.UI_MODAL_OPEN, { title, custom: true });
    SharedLogger.log('[Modal] Custom modal opened:', title || 'Untitled');

    return body; // Return body element so caller can manipulate content
  }

  private injectStyles(): void {
    if (document.getElementById('shared-modal-styles')) {
      SharedLogger.log('[Modal] Styles already injected, skipping');
      return;
    }

    SharedLogger.log('[Modal] Injecting styles...');
    const style = document.createElement('style');
    style.id = 'shared-modal-styles';
    style.textContent = `
      .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 200000;
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.2s ease, visibility 0.2s ease;
      }
      .modal-overlay.show {
        opacity: 1;
        visibility: visible;
      }
      .modal-container {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
        max-width: 500px;
        width: 90%;
        color: white;
        transform: scale(0.95);
        transition: transform 0.2s ease;
      }
      .modal-overlay.show .modal-container {
        transform: scale(1);
      }
      .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      }
      .modal-header h3 {
        margin: 0;
        font-size: 1.5rem;
        color: white;
        display: flex;
        align-items: center;
        gap: 0.75rem;
      }
      .modal-header h3 svg {
        flex-shrink: 0;
      }
      .modal-close {
        background: none;
        border: none;
        font-size: 2rem;
        cursor: pointer;
        color: rgba(255, 255, 255, 0.7);
      }
      .modal-close:hover {
        color: white;
      }
      .modal-body {
        padding: 1.5rem;
        font-size: 1.1rem;
        line-height: 1.6;
        color: rgba(255, 255, 255, 0.9);
      }
      .modal-footer {
        padding: 1rem 1.5rem;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        justify-content: flex-end;
        gap: 1rem;
      }
      .modal-btn {
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        cursor: pointer;
        font-weight: 500;
      }
      .modal-confirm {
        background: #ef4444;
        color: white;
      }
      .modal-confirm:hover {
        background: #dc2626;
      }
      .modal-cancel {
        background: rgba(255, 255, 255, 0.1);
        color: white;
      }
      .modal-cancel:hover {
        background: rgba(255, 255, 255, 0.15);
      }
      .modal-input {
        width: 100%;
        padding: 0.75rem;
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        font-size: 1rem;
        color: white;
      }
      .modal-input::placeholder {
        color: rgba(255, 255, 255, 0.5);
      }
      .modal-input:focus {
        outline: none;
        border-color: #3b82f6;
      }

      /* Custom Modal Styles */
      .modal-custom-container {
        max-height: 90vh;
        overflow-y: auto;
      }
      .modal-custom-body {
        padding: 0; /* Let content control its own padding */
        max-height: 80vh;
        overflow-y: auto;
      }

      /* Scrollbar styling for custom modals */
      .modal-custom-body::-webkit-scrollbar {
        width: 8px;
      }
      .modal-custom-body::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
      }
      .modal-custom-body::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
      }
      .modal-custom-body::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
      }
    `;
    document.head.appendChild(style);
    SharedLogger.log('[Modal] ✅ Styles injected successfully');
  }
}

export const SharedModal = new SharedModalClass();

declare global {
  interface Window {
    SharedModal: typeof SharedModal;
  }
}

if (typeof window !== 'undefined') {
  // Register to ServiceRegistry
  ServiceRegistry.register('SharedModal', SharedModal);
}
