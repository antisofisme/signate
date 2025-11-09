/**
 * Toast Notification System
 * Provides non-intrusive notifications with automatic dismiss
 *
 * Usage:
 *   window.SharedToast.success('Title', 'Message')
 *   window.SharedToast.error('Title', 'Message')
 *   window.SharedToast.warning('Title', 'Message')
 *   window.SharedToast.info('Title', 'Message')
 */

(function() {
    'use strict';

    /**
     * Toast notification system with support for success, error, warning, and info types
     * @type {Object}
     */
    window.SharedToast = {
        /**
         * SVG icons for different toast types
         * @type {Object}
         */
        icons: {
            success: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>',
            error: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>',
            warning: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>',
            info: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>',
            close: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>'
        },

        /**
         * Show a toast notification with the specified type
         *
         * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'
         * @param {string} title - Toast title text
         * @param {string} [message] - Optional toast message text
         * @param {number} [duration=5000] - Duration in ms before auto-dismiss (0 = no auto-dismiss)
         * @returns {HTMLElement} The created toast element
         */
        show: function(type, title, message, duration = 5000) {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;

            // SECURITY FIX: Build DOM safely to prevent XSS
            // Create icon element
            const iconDiv = document.createElement('div');
            iconDiv.className = 'toast-icon';
            iconDiv.innerHTML = this.icons[type]; // Safe - icons are controlled by us

            // Create content container
            const contentDiv = document.createElement('div');
            contentDiv.className = 'toast-content';

            // Create title element - SAFE from XSS
            const titleDiv = document.createElement('div');
            titleDiv.className = 'toast-title';
            titleDiv.textContent = title; // textContent auto-escapes HTML

            contentDiv.appendChild(titleDiv);

            // Create message element if provided - SAFE from XSS
            if (message) {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'toast-message';
                messageDiv.textContent = message; // textContent auto-escapes HTML
                contentDiv.appendChild(messageDiv);
            }

            // Create close button
            const closeDiv = document.createElement('div');
            closeDiv.className = 'toast-close';
            closeDiv.innerHTML = this.icons.close; // Safe - icons are controlled by us

            // Assemble toast
            toast.appendChild(iconDiv);
            toast.appendChild(contentDiv);
            toast.appendChild(closeDiv);

            // Close button event
            closeDiv.addEventListener('click', () => {
                this.remove(toast);
            });

            container.appendChild(toast);

            // Auto remove after duration
            if (duration > 0) {
                setTimeout(() => {
                    this.remove(toast);
                }, duration);
            }

            return toast;
        },

        /**
         * Remove a toast notification with fade animation
         *
         * @param {HTMLElement} toast - The toast element to remove
         */
        remove: function(toast) {
            toast.classList.add('removing');
            setTimeout(() => {
                toast.remove();
            }, 300);
        },

        /**
         * Show a success toast
         *
         * @param {string} title - Toast title
         * @param {string} [message] - Optional message
         * @param {number} [duration=5000] - Auto-dismiss duration
         * @returns {HTMLElement} The created toast element
         */
        success: function(title, message, duration) {
            return this.show('success', title, message, duration);
        },

        /**
         * Show an error toast
         *
         * @param {string} title - Toast title
         * @param {string} [message] - Optional message
         * @param {number} [duration=5000] - Auto-dismiss duration
         * @returns {HTMLElement} The created toast element
         */
        error: function(title, message, duration) {
            return this.show('error', title, message, duration);
        },

        /**
         * Show a warning toast
         *
         * @param {string} title - Toast title
         * @param {string} [message] - Optional message
         * @param {number} [duration=5000] - Auto-dismiss duration
         * @returns {HTMLElement} The created toast element
         */
        warning: function(title, message, duration) {
            return this.show('warning', title, message, duration);
        },

        /**
         * Show an info toast
         *
         * @param {string} title - Toast title
         * @param {string} [message] - Optional message
         * @param {number} [duration=5000] - Auto-dismiss duration
         * @returns {HTMLElement} The created toast element
         */
        info: function(title, message, duration) {
            return this.show('info', title, message, duration);
        }
    };

    // Export for ES6 modules if needed
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.SharedToast;
    }
})();
