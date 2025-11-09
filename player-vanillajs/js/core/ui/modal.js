/**
 * Modal Dialog Systems
 * Provides password modal for confirming sensitive actions
 *
 * Usage:
 *   window.SharedModal.show('Title', 'Message')
 */

(function() {
    'use strict';

    /**
     * Password modal for confirming sensitive actions
     * @type {Object}
     */
    window.SharedModal = {
        /**
         * Show password input modal and return a Promise
         *
         * @param {string} title - Modal title
         * @param {string} message - Modal message
         * @returns {Promise<string>} Promise resolving to password string, rejecting on cancel
         */
        show: function(title, message) {
            return new Promise((resolve, reject) => {
                const modal = document.getElementById('password-modal');
                const input = document.getElementById('password-input');
                const cancelBtn = document.getElementById('modal-cancel');
                const confirmBtn = document.getElementById('modal-confirm');

                // Reset input
                input.value = '';

                // Show modal
                modal.classList.add('show');
                input.focus();

                /**
                 * Cancel button click handler
                 * @private
                 */
                const handleCancel = () => {
                    modal.classList.remove('show');
                    reject('cancelled');
                    cleanup();
                };

                /**
                 * Confirm button click handler
                 * @private
                 */
                const handleConfirm = () => {
                    const password = input.value;
                    modal.classList.remove('show');
                    resolve(password);
                    cleanup();
                };

                /**
                 * Keyboard event handler for Enter and Escape keys
                 * @private
                 */
                const handleKeyPress = (e) => {
                    if (e.key === 'Enter') {
                        handleConfirm();
                    } else if (e.key === 'Escape') {
                        handleCancel();
                    }
                };

                /**
                 * Remove all event listeners
                 * @private
                 */
                const cleanup = () => {
                    cancelBtn.removeEventListener('click', handleCancel);
                    confirmBtn.removeEventListener('click', handleConfirm);
                    input.removeEventListener('keypress', handleKeyPress);
                };

                // Attach listeners
                cancelBtn.addEventListener('click', handleCancel);
                confirmBtn.addEventListener('click', handleConfirm);
                input.addEventListener('keypress', handleKeyPress);
            });
        }
    };

    // Export for ES6 modules if needed
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            SharedModal: window.SharedModal
        };
    }
})();
