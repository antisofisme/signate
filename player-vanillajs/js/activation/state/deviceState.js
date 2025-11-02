/**
 * Device State Management
 * Reactive state management for device using EventBus pattern
 */

(function() {
  'use strict';

  // Private state
  let _currentDevice = null;

  /**
   * Device State Manager
   */
  const deviceState = {
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
        console.error('[DeviceState] Invalid device data:', validation.errors);
      }

      // Save to localStorage
      _currentDevice.saveToStorage();

      // Emit event for reactive UI updates
      if (window.eventBus) {
        window.eventBus.emit('device:loaded', _currentDevice);
      }

      console.log('[DeviceState] Device set:', _currentDevice.toJSON());
    },

    /**
     * Update device status (triggers device:status-changed event)
     * @param {string} status - pending, active, inactive
     */
    setStatus(status) {
      if (!_currentDevice) {
        console.warn('[DeviceState] No device loaded');
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

      console.log('[DeviceState] Status changed:', status);
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

      // Clear localStorage
      [
        'device_id',
        'device_code',
        'device_name',
        'device_status',
        'organization_id',
        'platform'
      ].forEach(key => localStorage.removeItem(key));

      // Emit event
      if (window.eventBus) {
        window.eventBus.emit('device:cleared');
      }

      console.log('[DeviceState] Device cleared');
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

        console.log('[DeviceState] Device restored from storage');
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
    }
  };

  // Export to window
  window.deviceState = deviceState;

  console.log('[State/DeviceState] Device state manager loaded');

})();
