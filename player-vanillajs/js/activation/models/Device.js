/**
 * Device Model
 * Represents a registered device with validation and computed properties
 */

(function() {
  'use strict';

  class Device {
    constructor(data = {}) {
      this.id = data.id || null;
      this.code = data.code || null;
      this.name = data.name || null;
      this.status = data.status || 'pending'; // pending, active, inactive
      this.organization_id = data.organization_id || null;
      this.platform = data.platform || 'Browser';
      this.last_seen = data.last_seen || null;
      this.created_at = data.created_at || null;
      this.updated_at = data.updated_at || null;
    }

    /**
     * Validate device data
     * @returns {Object} { valid: boolean, errors: string[] }
     */
    validate() {
      const errors = [];

      if (!this.code || this.code.length !== 6) {
        errors.push('Activation code must be 6 digits');
      }

      if (!this.name || this.name.trim().length === 0) {
        errors.push('Device name is required');
      }

      if (!['pending', 'active', 'inactive'].includes(this.status)) {
        errors.push('Invalid device status');
      }

      return {
        valid: errors.length === 0,
        errors: errors
      };
    }

    /**
     * Check if device is active
     * @returns {boolean}
     */
    isActive() {
      return this.status === 'active';
    }

    /**
     * Check if device is online (last_seen within 5 minutes)
     * @returns {boolean}
     */
    isOnline() {
      if (!this.last_seen) return false;

      const lastSeenDate = new Date(this.last_seen);
      const now = new Date();
      const diffMinutes = (now - lastSeenDate) / 1000 / 60;

      return diffMinutes < 5;
    }

    /**
     * Get device age in days
     * @returns {number}
     */
    getAgeInDays() {
      if (!this.created_at) return 0;

      const createdDate = new Date(this.created_at);
      const now = new Date();
      const diffDays = Math.floor((now - createdDate) / 1000 / 60 / 60 / 24);

      return diffDays;
    }

    /**
     * Convert to plain object for API calls
     * @returns {Object}
     */
    toJSON() {
      return {
        id: this.id,
        code: this.code,
        name: this.name,
        status: this.status,
        organization_id: this.organization_id,
        platform: this.platform,
        last_seen: this.last_seen,
        created_at: this.created_at,
        updated_at: this.updated_at
      };
    }

    /**
     * Convert to localStorage format
     * @returns {Object}
     */
    toStorage() {
      return {
        device_id: this.id,
        device_code: this.code,
        device_name: this.name,
        device_status: this.status,
        organization_id: this.organization_id,
        platform: this.platform
      };
    }

    /**
     * Load from localStorage
     * @returns {Device|null}
     */
    static fromStorage() {
      const id = localStorage.getItem('device_id');
      const code = localStorage.getItem('device_code');
      const name = localStorage.getItem('device_name');
      const status = localStorage.getItem('device_status');
      const organization_id = localStorage.getItem('organization_id');
      const platform = localStorage.getItem('platform');

      if (!id) return null;

      return new Device({
        id: parseInt(id),
        code: code,
        name: name,
        status: status,
        organization_id: organization_id ? parseInt(organization_id) : null,
        platform: platform
      });
    }

    /**
     * Save to localStorage
     */
    saveToStorage() {
      const storage = this.toStorage();
      Object.keys(storage).forEach(key => {
        localStorage.setItem(key, storage[key]);
      });
    }
  }

  // Export to window (Vanilla JS pattern)
  window.Device = Device;

  console.log('[Models/Device] Device model loaded');

})();
