/**
 * Modal Dialog Systems
 * Provides password modal and organization PIN modal
 *
 * Usage:
 *   window.PasswordModal.show('Title', 'Message')
 *   window.OrganizationPINModal.show()
 */

(function() {
    'use strict';

    /**
     * Password modal for confirming sensitive actions
     * @type {Object}
     */
    window.PasswordModal = {
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

    /**
     * Organization PIN modal for linking devices to organizations
     * @type {Object}
     */
    window.OrganizationPINModal = {
        /**
         * Show organization PIN input modal and return a Promise
         *
         * Validates PIN against server before resolving
         *
         * @returns {Promise<string>} Promise resolving to PIN string, rejecting on cancel
         */
        show: function() {
            return new Promise((resolve, reject) => {
                const modal = document.getElementById('org-pin-modal');
                const input = document.getElementById('org-pin-input');
                const cancelBtn = document.getElementById('org-pin-cancel');
                const saveBtn = document.getElementById('org-pin-save');
                const currentPinDisplay = document.getElementById('current-pin-display');
                const currentPinValue = document.getElementById('current-pin-value');

                // Check if PIN already exists
                const existingPIN = localStorage.getItem('organization_pin');
                if (existingPIN) {
                    currentPinDisplay.style.display = 'block';
                    currentPinValue.textContent = existingPIN;
                    input.placeholder = 'Enter new PIN to change';
                } else {
                    currentPinDisplay.style.display = 'none';
                    input.placeholder = 'Enter 8-digit PIN';
                }

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
                 * Save button click handler
                 * Validates PIN with server before saving
                 * @private
                 */
                const handleSave = async () => {
                    const pin = input.value.trim();

                    // Validate PIN length
                    if (pin && pin.length < 8) {
                        window.Toast.error('Invalid PIN', 'Organization PIN must be at least 8 characters');
                        return;
                    }

                    // If user entered a new PIN, validate with server
                    if (pin) {
                        // Disable button while validating
                        saveBtn.disabled = true;
                        saveBtn.textContent = 'Validating...';

                        try {
                            const state = window.ShellState;
                            const response = await fetch(
                                `${state.API_BASE_URL}/api/organizations/validate-pin?pin=${encodeURIComponent(pin)}`
                            );

                            if (!response.ok) {
                                // PIN validation failed
                                if (response.status === 404) {
                                    window.Toast.error('Invalid PIN', 'Organization PIN not found. Please check and try again.');
                                } else {
                                    window.Toast.error('Validation Failed', 'Could not validate PIN. Please try again.');
                                }
                                saveBtn.disabled = false;
                                saveBtn.textContent = 'Save';
                                return;
                            }

                            // PIN is valid, get organization name
                            const data = await response.json();
                            console.log('[Shell/OrganizationPIN] PIN validated successfully:', data);

                            // Save new PIN
                            localStorage.setItem('organization_pin', pin);
                            window.Toast.success('PIN Saved', `Organization: ${data.details?.organization_name || 'Unknown'}`);
                            console.log('[Shell/OrganizationPIN] PIN saved:', pin);

                        } catch (error) {
                            console.error('[Shell/OrganizationPIN] Validation error:', error);
                            window.Toast.error('Network Error', 'Could not connect to server. Please check your connection.');
                            saveBtn.disabled = false;
                            saveBtn.textContent = 'Save';
                            return;
                        }
                    }

                    // Close modal and resolve
                    modal.classList.remove('show');
                    resolve(pin || existingPIN);
                    cleanup();
                };

                /**
                 * Keyboard event handler for Enter and Escape keys
                 * @private
                 */
                const handleKeyPress = (e) => {
                    if (e.key === 'Enter') {
                        handleSave();
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
                    saveBtn.removeEventListener('click', handleSave);
                    input.removeEventListener('keypress', handleKeyPress);
                };

                // Attach listeners
                cancelBtn.addEventListener('click', handleCancel);
                saveBtn.addEventListener('click', handleSave);
                input.addEventListener('keypress', handleKeyPress);
            });
        }
    };

    /**
     * Initialize organization PIN button click handler
     * @private
     */
    document.addEventListener('DOMContentLoaded', function() {
        const orgPinBtn = document.getElementById('org-pin-btn');

        if (orgPinBtn) {
            orgPinBtn.addEventListener('click', function() {
                console.log('[Shell/OrganizationPIN] Opening PIN modal');
                window.OrganizationPINModal.show().catch(err => {
                    console.log('[Shell/OrganizationPIN] Modal cancelled');
                });
            });
        }
    });

    // Export for ES6 modules if needed
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            PasswordModal: window.PasswordModal,
            OrganizationPINModal: window.OrganizationPINModal
        };
    }
})();
