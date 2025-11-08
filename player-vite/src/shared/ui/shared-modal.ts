/**
 * Shared Modal Component
 * Reusable modal dialog system
 */

import { SharedLogger } from '@shared/logger';
import { SharedEventBus, EventNames } from '@shared/events/shared-event-bus';

export interface ModalOptions {
  title: string;
  message: string;
  type?: 'info' | 'warning' | 'error' | 'success';
  confirmText?: string;
  cancelText?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
}

class SharedModalClass {
  private modalElement: HTMLElement | null = null;

  show(options: ModalOptions): void {
    this.close(); // Close any existing modal

    const {
      title,
      message,
      type = 'info',
      confirmText = 'OK',
      cancelText,
      onConfirm,
      onCancel,
    } = options;

    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="modal-container modal-${type}">
        <div class="modal-header">
          <h3>${title}</h3>
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

    SharedEventBus.emit(EventNames.UI_MODAL_OPEN, options);
    SharedLogger.log('[Modal] Opened:', title);
  }

  close(): void {
    if (this.modalElement) {
      this.modalElement.remove();
      this.modalElement = null;
      SharedEventBus.emit(EventNames.UI_MODAL_CLOSE);
      SharedLogger.log('[Modal] Closed');
    }
  }

  /**
   * Show prompt modal with password input
   * Returns Promise that resolves with password or rejects if cancelled
   */
  async prompt(title: string, message: string, inputType: 'text' | 'password' = 'password'): Promise<string> {
    this.close(); // Close any existing modal

    return new Promise((resolve, reject) => {
      const modal = document.createElement('div');
      modal.className = 'modal-overlay';
      modal.innerHTML = `
        <div class="modal-container modal-warning">
          <div class="modal-header">
            <h3>${title}</h3>
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

      // Focus input after a short delay
      setTimeout(() => input.focus(), 100);

      SharedEventBus.emit(EventNames.UI_MODAL_OPEN, { title, message });
      SharedLogger.log('[Modal] Prompt opened:', title);
    });
  }

  private injectStyles(): void {
    if (document.getElementById('shared-modal-styles')) return;

    const style = document.createElement('style');
    style.id = 'shared-modal-styles';
    style.textContent = `
      .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
      }
      .modal-container {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
        max-width: 500px;
        width: 90%;
        color: white;
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
      }
      .modal-close {
        background: none;
        border: none;
        font-size: 2rem;
        cursor: pointer;
        color: rgba(255, 255, 255, 0.7);
        transition: color 0.2s;
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
        transition: all 0.2s;
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
      .modal-btn:hover {
        transform: translateY(-1px);
      }
      .modal-input {
        width: 100%;
        padding: 0.75rem;
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        font-size: 1rem;
        color: white;
        transition: border-color 0.2s;
      }
      .modal-input::placeholder {
        color: rgba(255, 255, 255, 0.5);
      }
      .modal-input:focus {
        outline: none;
        border-color: #3b82f6;
      }
    `;
    document.head.appendChild(style);
  }
}

export const SharedModal = new SharedModalClass();

declare global {
  interface Window {
    SharedModal: typeof SharedModal;
  }
}

if (typeof window !== 'undefined') {
  window.SharedModal = SharedModal;
}
