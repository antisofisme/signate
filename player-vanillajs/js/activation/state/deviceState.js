/**
 * Device State Management
 *
 * @module deviceState
 * @description
 * Reactive state management for device registration and activation using EventBus pattern.
 * Manages device lifecycle: registration → activation → heartbeat monitoring.
 *
 * @features
 * - Centralized device state management
 * - Automatic localStorage persistence
 * - Reactive event-driven updates via EventBus
 * - Device validation and error handling
 * - Online/offline status tracking
 * - Memory leak prevention via private state
 *
 * @events_emitted
 * - **device:loaded** - Device set/updated (payload: Device)
 * - **device:restored** - Device loaded from localStorage (payload: Device)
 * - **device:status-changed** - Status updated (payload: {device, status})
 * - **device:heartbeat-sent** - Heartbeat timestamp updated (payload: Device)
 * - **device:cleared** - Device state cleared/logged out (no payload)
 *
 * @usage
 * ```javascript
 * // Subscribe to device events
 * eventBus.on('device:loaded', (device) => {
 *   SharedLogger.log('Device registered:', device);
 *   document.querySelector('#device-name').textContent = device.name;
 * });
 *
 * // Set device after registration
 * SharedDeviceState.setDevice({
 *   id: 123,
 *   code: '123456',
 *   name: 'Lobby Display',
 *   status: 'pending'
 * });
 *
 * // Update status after activation
 * SharedDeviceState.setStatus('active');
 *
 * // Check device state
 * if (SharedDeviceState.isActive()) {
 *   SharedLogger.log('Device is active');
 * }
 *
 * // Send heartbeat
 * SharedDeviceState.updateLastSeen();
 * ```
 *
 * @persistence
 * Device data is automatically saved to localStorage on every update:
 * - device_id
 * - device_code
 * - device_name
 * - device_status
 * - organization_id
 * - platform
 *
 * Use `loadFromStorage()` on page load to restore device state.
 *
 * @architecture
 * Uses private state (_currentDevice) encapsulated in IIFE to prevent external mutation.
 * All updates must go through public methods, ensuring validation and event emission.
 */
(function() {
  'use strict';

  // Private state
  /** @type {Device|null} Current device instance (private, access via getDevice()) */
  let _currentDevice = null;

  /**
   * Device State Manager
   * @namespace SharedDeviceState
   * @global
   */
  const SharedDeviceState = {
    /**
     * Get current device
     * @returns {Device|null}
     */
    getDevice() {
      return _currentDevice;
    },

    /**
     * Set device (triggers device:loaded event)
     * @param {Device|Object} deviceData - Device instance or plain object
     */
    setDevice(deviceData) {
      // Convert to Device model if plain object
      if (!(deviceData instanceof window.Device)) {
        _currentDevice = new window.Device(deviceData);
      } else {
        _currentDevice = deviceData;
      }

      // Validate device
      const validation = _currentDevice.validate();
      if (!validation.valid) {
        SharedLogger.error('[DeviceState] Invalid device data:', validation.errors);
      }

      // Save to localStorage
      _currentDevice.saveToStorage();

      // Emit event for reactive UI updates
      if (window.eventBus) {
        window.eventBus.emit('device:loaded', _currentDevice);
      }

      SharedLogger.log('[DeviceState] Device set:', _currentDevice.toJSON());
    },

    /**
     * Update device status (triggers device:status-changed event)
     * @param {string} status - pending, active, inactive
     */
    setStatus(status) {
      if (!_currentDevice) {
        SharedLogger.warn('[DeviceState] No device loaded');
        return;
      }

      _currentDevice.status = status;
      _currentDevice.saveToStorage();

      // Emit event
      if (window.eventBus) {
        window.eventBus.emit('device:status-changed', {
          device: _currentDevice,
          status: status
        });
      }

      SharedLogger.log('[DeviceState] Status changed:', status);
    },

    /**
     * Update device last_seen timestamp
     */
    updateLastSeen() {
      if (!_currentDevice) return;

      _currentDevice.last_seen = new Date().toISOString();

      // Emit event
      if (window.eventBus) {
        window.eventBus.emit('device:heartbeat-sent', _currentDevice);
      }
    },

    /**
     * Clear device (logout)
     */
    clearDevice() {
      _currentDevice = null;

      // Clear localStorage (including device_token)
      [
        'device_id',
        'device_code',
        'device_name',
        'device_status',
        'organization_id',
        'platform',
        'device_token'
      ].forEach(key => localStorage.removeItem(key));

      // Emit event
      if (window.eventBus) {
        window.eventBus.emit('device:cleared');
      }

      SharedLogger.log('[DeviceState] Device cleared');
    },

    /**
     * Load device from localStorage
     * @returns {Device|null}
     */
    loadFromStorage() {
      const device = window.Device.fromStorage();

      if (device) {
        _currentDevice = device;

        // Emit event (without re-saving)
        if (window.eventBus) {
          window.eventBus.emit('device:restored', device);
        }

        SharedLogger.log('[DeviceState] Device restored from storage');
      }

      return device;
    },

    /**
     * Check if device is registered
     * @returns {boolean}
     */
    isRegistered() {
      return _currentDevice !== null && _currentDevice.id !== null;
    },

    /**
     * Check if device is active
     * @returns {boolean}
     */
    isActive() {
      return _currentDevice !== null && _currentDevice.isActive();
    },

    /**
     * Check if device is online
     * @returns {boolean}
     */
    isOnline() {
      return _currentDevice !== null && _currentDevice.isOnline();
    },

    // ==========================================================================
    // PREFERENCES & SETTINGS (Player-specific, but accessed via device state)
    // ==========================================================================

    /**
     * Get player preference from localStorage
     * @param {string} key - Preference key (volume_preference, brightness_preference, preferredQuality)
     * @param {any} defaultValue - Default value if not set
     * @returns {any}
     */
    getPreference(key, defaultValue = null) {
      const value = localStorage.getItem(key);
      return value !== null ? value : defaultValue;
    },

    /**
     * Set player preference to localStorage
     * @param {string} key - Preference key
     * @param {any} value - Preference value
     */
    setPreference(key, value) {
      localStorage.setItem(key, value);
      SharedLogger.log(`[SharedDeviceState] Preference set: ${key} = ${value}`);
    },

    /**
     * Remove player preference from localStorage
     * @param {string} key - Preference key
     */
    removePreference(key) {
      localStorage.removeItem(key);
      SharedLogger.log(`[SharedDeviceState] Preference removed: ${key}`);
    },

    // ==========================================================================
    // DEVICE CORE DATA ACCESSORS (Phase 2: Bootstrap/Activation)
    // ==========================================================================

    /**
     * Get device ID from localStorage
     * @returns {string|null}
     */
    getDeviceId() {
      return localStorage.getItem('device_id');
    },

    /**
     * Get device status from localStorage
     * @returns {string|null} - 'pending', 'active', or 'inactive'
     */
    getDeviceStatus() {
      return localStorage.getItem('device_status');
    },

    /**
     * Get device activation code from localStorage
     * @returns {string|null}
     */
    getDeviceCode() {
      return localStorage.getItem('device_code');
    },

    /**
     * Get organization ID from localStorage
     * @returns {string|null}
     */
    getOrganizationId() {
      return localStorage.getItem('organization_id');
    },

    /**
     * Get device JWT token from localStorage
     * @returns {string|null}
     */
    getDeviceToken() {
      return localStorage.getItem('device_token');
    },

    /**
     * Get device name from localStorage
     * @returns {string|null}
     */
    getDeviceName() {
      return localStorage.getItem('device_name');
    },

    /**
     * Set device ID to localStorage (with logging)
     * @param {string|number} id - Device ID
     */
    setDeviceId(id) {
      localStorage.setItem('device_id', String(id));
      SharedLogger.log(`[SharedDeviceState] Device ID set: ${id}`);
    },

    /**
     * Set device status to localStorage (with validation and logging)
     * @param {string} status - 'pending', 'active', or 'inactive'
     */
    setDeviceStatus(status) {
      const validStatuses = ['pending', 'active', 'inactive'];
      if (!validStatuses.includes(status)) {
        SharedLogger.error(`[SharedDeviceState] Invalid status: ${status}. Valid: ${validStatuses.join(', ')}`);
        return;
      }
      localStorage.setItem('device_status', status);
      SharedLogger.log(`[SharedDeviceState] Device status set: ${status}`);
    },

    /**
     * Set device activation code to localStorage (with logging)
     * @param {string} code - 6-digit activation code
     */
    setDeviceCode(code) {
      localStorage.setItem('device_code', code);
      SharedLogger.log(`[SharedDeviceState] Device code set: ${code}`);
    },

    /**
     * Set organization ID to localStorage (with logging)
     * @param {string|number} orgId - Organization ID
     */
    setOrganizationId(orgId) {
      localStorage.setItem('organization_id', String(orgId));
      SharedLogger.log(`[SharedDeviceState] Organization ID set: ${orgId}`);
    },

    /**
     * Set device JWT token to localStorage (with logging)
     * @param {string} token - JWT token
     */
    setDeviceToken(token) {
      localStorage.setItem('device_token', token);
      SharedLogger.log('[SharedDeviceState] Device token set');
    },

    /**
     * Set device name to localStorage (with logging)
     * @param {string} name - Device name
     */
    setDeviceName(name) {
      localStorage.setItem('device_name', name);
      SharedLogger.log(`[SharedDeviceState] Device name set: ${name}`);
    },

    // ==========================================================================
    // ATOMIC OPERATIONS (Phase 2: Complex state transitions)
    // ==========================================================================

    /**
     * Mark device as activated (atomic operation)
     * Sets device_id, status=active, and optional device_name + organization_id
     *
     * @param {string|number} deviceId - Device ID
     * @param {string} [deviceName] - Device name (optional)
     * @param {string|number} [orgId] - Organization ID (optional)
     */
    markAsActivated(deviceId, deviceName = null, orgId = null) {
      this.setDeviceId(deviceId);
      this.setDeviceStatus('active');

      if (deviceName) {
        this.setDeviceName(deviceName);
      }

      if (orgId) {
        this.setOrganizationId(orgId);
      }

      SharedLogger.log('[SharedDeviceState] ✅ Device marked as activated', {
        deviceId,
        deviceName,
        orgId
      });
    },

    /**
     * Clear device data from localStorage (atomic operation)
     *
     * @param {Object} [options] - Options
     * @param {boolean} [options.preserveAuth=false] - If true, preserve device_token and organization_id
     */
    clearDeviceData({ preserveAuth = false } = {}) {
      const keysToRemove = ['device_id', 'device_code', 'device_name', 'device_status', 'platform'];

      if (preserveAuth) {
        // Preserve auth data for re-registration
        const preservedToken = this.getDeviceToken();
        const preservedOrgId = this.getOrganizationId();

        SharedLogger.log('[SharedDeviceState] Clearing device data (preserving auth)...', {
          hasToken: !!preservedToken,
          hasOrgId: !!preservedOrgId
        });

        // Clear device-specific data
        keysToRemove.forEach(key => localStorage.removeItem(key));

        // Restore auth data
        if (preservedToken) {
          this.setDeviceToken(preservedToken);
        }
        if (preservedOrgId) {
          this.setOrganizationId(preservedOrgId);
        }

        SharedLogger.log('[SharedDeviceState] ✅ Device data cleared (auth preserved)');
      } else {
        // Clear everything including auth
        keysToRemove.forEach(key => localStorage.removeItem(key));
        localStorage.removeItem('device_token');
        localStorage.removeItem('organization_id');

        SharedLogger.log('[SharedDeviceState] ✅ Device data cleared (including auth)');
      }
    },

    // ==========================================================================
    // VERIFICATION HELPERS (Phase 2: Cleaner boolean checks)
    // ==========================================================================

    /**
     * Check if device has an ID (is registered)
     * @returns {boolean}
     */
    hasDeviceId() {
      return !!this.getDeviceId();
    },

    /**
     * Check if device is activated
     * @returns {boolean}
     */
    isActivated() {
      return this.getDeviceStatus() === 'active';
    },

    /**
     * Check if device has auth token
     * @returns {boolean}
     */
    hasDeviceToken() {
      return !!this.getDeviceToken();
    },

    // ==========================================================================
    // DIRECT LOCALSTORAGE ACCESSORS (for migration compatibility)
    // ==========================================================================

    /**
     * Generic localStorage getter (use sparingly, prefer specific methods)
     * @param {string} key - Storage key
     * @param {any} defaultValue - Default value
     * @returns {any}
     */
    get(key, defaultValue = null) {
      const value = localStorage.getItem(key);
      return value !== null ? value : defaultValue;
    },

    /**
     * Generic localStorage setter (use sparingly, prefer specific methods)
     * @param {string} key - Storage key
     * @param {any} value - Storage value
     */
    set(key, value) {
      localStorage.setItem(key, value);
    },

    /**
     * Generic localStorage remover (use sparingly, prefer specific methods)
     * @param {string} key - Storage key
     */
    remove(key) {
      localStorage.removeItem(key);
    }
  };

  // Export to window
  window.SharedDeviceState = SharedDeviceState;

  SharedLogger.log('[State/SharedDeviceState] Device state manager loaded');

})();
