/**
 * Device Model
 *
 * @class Device
 * @description
 * Represents a registered signage display device with validation, computed properties, and localStorage integration.
 * Used for device registration, activation, and online/offline status tracking.
 *
 * @features
 * - 6-digit activation code validation
 * - Online/offline status based on heartbeat (last_seen < 5 minutes)
 * - Device age calculation
 * - localStorage persistence
 * - Status lifecycle: pending → active → inactive
 *
 * @usage
 * ```javascript
 * // Create new device from API response
 * const device = new Device({
 *   id: 123,
 *   code: '123456',
 *   name: 'Lobby Display',
 *   status: 'active',
 *   platform: 'WebOS'
 * });
 *
 * // Validate device data
 * const validation = device.validate();
 * if (!validation.valid) {
 *   console.error('Validation errors:', validation.errors);
 * }
 *
 * // Check online status
 * if (device.isOnline()) {
 *   console.log('Device is online');
 * }
 *
 * // Save to localStorage
 * device.saveToStorage();
 *
 * // Load from localStorage
 * const savedDevice = Device.fromStorage();
 * ```
 *
 * @lifecycle
 * 1. **Registration**: Device generates 6-digit code → status: 'pending'
 * 2. **Activation**: Admin approves in dashboard → status: 'active'
 * 3. **Operation**: Device sends heartbeat every 30s (updates last_seen)
 * 4. **Offline Detection**: Dashboard marks offline if last_seen > 5 minutes
 * 5. **Deactivation**: Admin can set status: 'inactive' to disable device
 */
(function() {
  'use strict';

  class Device {
    /**
     * Create a Device instance
     * @constructor
     * @param {Object} data - Device data from API or storage
     * @param {number} [data.id=null] - Device unique identifier
     * @param {string} [data.code=null] - 6-digit activation code
     * @param {string} [data.name=null] - Device display name
     * @param {('pending'|'active'|'inactive')} [data.status='pending'] - Device status
     * @param {number} [data.organization_id=null] - Organization/tenant ID
     * @param {string} [data.platform='Browser'] - Platform type (Browser, WebOS, Android, etc.)
     * @param {string} [data.device_token=null] - JWT token for authenticated API calls
     * @param {string} [data.last_seen=null] - ISO timestamp of last heartbeat
     * @param {string} [data.created_at=null] - ISO timestamp of device creation
     * @param {string} [data.updated_at=null] - ISO timestamp of last update
     */
    constructor(data = {}) {
      /** @type {number|null} Device unique identifier */
      this.id = data.id || null;

      /** @type {string|null} 6-digit activation code for device pairing */
      this.code = data.code || null;

      /** @type {string|null} Device display name (e.g., "Lobby Display") */
      this.name = data.name || null;

      /** @type {('pending'|'active'|'inactive')} Device status */
      this.status = data.status || 'pending';

      /** @type {number|null} Organization/tenant ID for multi-tenancy */
      this.organization_id = data.organization_id || null;

      /** @type {string} Platform type (Browser, WebOS, Android, etc.) */
      this.platform = data.platform || 'Browser';

      /** @type {string|null} JWT token for authenticated API calls (persisted) */
      this.device_token = data.device_token || null;

      /** @type {string|null} ISO timestamp of last heartbeat */
      this.last_seen = data.last_seen || null;

      /** @type {string|null} ISO timestamp of device creation */
      this.created_at = data.created_at || null;

      /** @type {string|null} ISO timestamp of last update */
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
        platform: this.platform,
        device_token: this.device_token
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
      const device_token = localStorage.getItem('device_token');

      if (!id) return null;

      return new Device({
        id: parseInt(id),
        code: code,
        name: name,
        status: status,
        organization_id: organization_id ? parseInt(organization_id) : null,
        platform: platform,
        device_token: device_token
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
