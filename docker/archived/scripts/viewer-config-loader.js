/**
 * Unified Configuration Loader for Viewer
 * This file should be included in the viewer to load configuration from environment
 */

(function() {
  'use strict';

  /**
   * Configuration loader for viewer
   * Supports multiple loading strategies:
   * 1. Meta tags in HTML (server-injected)
   * 2. Config endpoint (dynamic)
   * 3. Environment variables (build-time)
   * 4. Default values (fallback)
   */
  window.ViewerConfig = {
    // Store loaded configuration
    config: {},

    // Default configuration values
    defaults: {
      apiUrl: 'http://192.168.5.12:8001',
      heartbeatInterval: 30000,
      playlistRefreshInterval: 60000,
      logSendInterval: 5000,
      logBufferSize: 20,
      cacheEnabled: true,
      cacheMaxSize: 104857600,
      environment: 'production',
      debug: false
    },

    /**
     * Load configuration from meta tags
     * Server can inject config as meta tags in HTML
     */
    loadFromMeta: function() {
      const config = {};
      const metas = document.querySelectorAll('meta[name^="viewer-"]');

      metas.forEach(meta => {
        const key = meta.name.replace('viewer-', '')
          .replace(/-([a-z])/g, (g) => g[1].toUpperCase());

        let value = meta.content;

        // Parse boolean values
        if (value === 'true' || value === 'false') {
          value = value === 'true';
        }
        // Parse numeric values
        else if (!isNaN(value) && value !== '') {
          value = Number(value);
        }

        config[key] = value;
      });

      return config;
    },

    /**
     * Load configuration from server endpoint
     * Fetches dynamic configuration from backend
     */
    loadFromServer: async function() {
      try {
        // Try to get base URL from meta tag first
        const baseUrlMeta = document.querySelector('meta[name="viewer-api-url"]');
        const baseUrl = baseUrlMeta ? baseUrlMeta.content : this.defaults.apiUrl;

        const response = await fetch(`${baseUrl}/api/viewer/config`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          return data.config || {};
        }
      } catch (error) {
        console.warn('Failed to load config from server:', error);
      }
      return {};
    },

    /**
     * Load configuration from local storage
     * Useful for debugging and offline mode
     */
    loadFromLocalStorage: function() {
      try {
        const stored = localStorage.getItem('viewer-config');
        if (stored) {
          return JSON.parse(stored);
        }
      } catch (error) {
        console.warn('Failed to load config from localStorage:', error);
      }
      return {};
    },

    /**
     * Save configuration to local storage
     */
    saveToLocalStorage: function(config) {
      try {
        localStorage.setItem('viewer-config', JSON.stringify(config));
      } catch (error) {
        console.warn('Failed to save config to localStorage:', error);
      }
    },

    /**
     * Initialize configuration
     * Loads from multiple sources and merges
     */
    init: async function() {
      console.log('Initializing viewer configuration...');

      // 1. Start with defaults
      let config = { ...this.defaults };

      // 2. Load from local storage (cached config)
      const localConfig = this.loadFromLocalStorage();
      config = { ...config, ...localConfig };

      // 3. Load from meta tags (server-injected)
      const metaConfig = this.loadFromMeta();
      config = { ...config, ...metaConfig };

      // 4. Try to load from server (if online)
      if (navigator.onLine) {
        const serverConfig = await this.loadFromServer();
        config = { ...config, ...serverConfig };
      }

      // Store final configuration
      this.config = config;

      // Save to local storage for offline use
      this.saveToLocalStorage(config);

      // Apply configuration to global state objects
      this.applyConfig();

      // Log configuration in debug mode
      if (config.debug) {
        console.log('Viewer configuration loaded:', config);
      }

      return config;
    },

    /**
     * Apply configuration to global state objects
     */
    applyConfig: function() {
      // Update Shell state
      if (window.ShellState) {
        window.ShellState.API_BASE_URL = this.config.apiUrl;
        window.ShellState.HEARTBEAT_INTERVAL = this.config.heartbeatInterval;
        window.ShellState.LOG_SEND_INTERVAL = this.config.logSendInterval;
        window.ShellState.LOG_BUFFER_SIZE = this.config.logBufferSize;
      }

      // Update Player state
      if (window.PlayerState) {
        window.PlayerState.API_BASE_URL = this.config.apiUrl;
        window.PlayerState.REFRESH_INTERVAL = this.config.playlistRefreshInterval;
        window.PlayerState.LOG_SEND_INTERVAL = this.config.logSendInterval;
        window.PlayerState.LOG_BUFFER_SIZE = this.config.logBufferSize;
      }

      // Enable/disable debug features
      if (this.config.debug) {
        console.log('Debug mode enabled');
        window.DEBUG = true;
      }
    },

    /**
     * Get a configuration value
     */
    get: function(key, defaultValue) {
      return this.config[key] !== undefined ? this.config[key] : defaultValue;
    },

    /**
     * Set a configuration value (runtime override)
     */
    set: function(key, value) {
      this.config[key] = value;
      this.saveToLocalStorage(this.config);
      this.applyConfig();
    },

    /**
     * Reset configuration to defaults
     */
    reset: function() {
      this.config = { ...this.defaults };
      localStorage.removeItem('viewer-config');
      this.applyConfig();
    },

    /**
     * Reload configuration from server
     */
    reload: async function() {
      await this.init();
      console.log('Configuration reloaded');
    }
  };

  // Auto-initialize on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      window.ViewerConfig.init();
    });
  } else {
    // DOM already loaded
    window.ViewerConfig.init();
  }

  // Expose to global scope for debugging
  window.ViewerConfig = window.ViewerConfig;

})();