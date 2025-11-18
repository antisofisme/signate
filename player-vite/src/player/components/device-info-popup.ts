/**
 * Device Info Popup Component
 * Displays comprehensive device information using centralized DeviceInfoCollector
 *
 * @features
 * - 7 organized tabs: Device, Network, System, Storage, Backend, Audio, Performance
 * - Uses DeviceInfoCollector service for all data
 * - Clean, modular architecture
 * - Real-time information updates
 */

import { SharedLogger } from '@shared/logger';
import { SharedModal } from '@shared/ui';
import { DeviceInfoCollector } from '@shared/services/device-info';
import { formatUptime } from '@shared/utils/performance-info';
import type { CompleteDeviceInfo } from '@shared/services/device-info';

/**
 * Device Info Popup Manager
 */
class DeviceInfoPopupClass {
  private button: HTMLElement | null = null;
  private isInitialized = false;
  private deviceInfo: CompleteDeviceInfo | null = null;

  /**
   * Initialize device info popup
   */
  init(): void {
    if (this.isInitialized) {
      SharedLogger.log('[DeviceInfoPopup] Already initialized');
      return;
    }

    SharedLogger.log('[DeviceInfoPopup] Initializing...');

    this.button = document.getElementById('device-info-btn');

    if (!this.button) {
      SharedLogger.error('[DeviceInfoPopup] Button not found - will retry in 1s');
      setTimeout(() => {
        this.isInitialized = false;
        this.init();
      }, 1000);
      return;
    }

    // Open popup on button click
    this.button.addEventListener('click', () => {
      SharedLogger.log('[DeviceInfoPopup] Button clicked');
      this.open();
    });

    this.isInitialized = true;
    SharedLogger.log('[DeviceInfoPopup] ✅ Initialized');
  }

  /**
   * Open popup and load device info
   */
  async open(): Promise<void> {
    const content = this.buildContent();

    SharedModal.showCustom({
      title: 'Device Information',
      content,
      width: '90%',
      maxWidth: '900px',
      showCloseButton: true,
      className: 'device-info-modal'
    });

    // Load device info after modal is shown
    await this.loadDeviceInfo();
  }

  /**
   * Build HTML content for the modal
   */
  private buildContent(): string {
    return `
      <div style="display: flex; flex-direction: column; height: 600px; max-height: 80vh;">
        <!-- Tabs - Fixed at top -->
        <div style="display: flex; gap: 0.5rem; padding: 1.5rem 1.5rem 0 1.5rem; border-bottom: 2px solid rgba(255, 255, 255, 0.1); overflow-x: auto; overflow-y: hidden; -webkit-overflow-scrolling: touch; scrollbar-width: thin; flex-shrink: 0;">
          <button id="tab-device" class="info-tab active" onclick="window.DeviceInfoPopup.switchTab('device')">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
              <line x1="8" y1="21" x2="16" y2="21"/>
              <line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
            Device
          </button>
          <button id="tab-network" class="info-tab" onclick="window.DeviceInfoPopup.switchTab('network')">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
            Network
          </button>
          <button id="tab-system" class="info-tab" onclick="window.DeviceInfoPopup.switchTab('system')">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="2" y1="12" x2="22" y2="12"/>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
            </svg>
            System
          </button>
          <button id="tab-storage" class="info-tab" onclick="window.DeviceInfoPopup.switchTab('storage')">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
              <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
              <line x1="12" y1="22.08" x2="12" y2="12"/>
            </svg>
            Storage
          </button>
          <button id="tab-backend" class="info-tab" onclick="window.DeviceInfoPopup.switchTab('backend')">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
              <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
              <line x1="6" y1="6" x2="6.01" y2="6"/>
              <line x1="6" y1="18" x2="6.01" y2="18"/>
            </svg>
            Backend
          </button>
          <button id="tab-audio" class="info-tab" onclick="window.DeviceInfoPopup.switchTab('audio')">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
              <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
            </svg>
            Audio
          </button>
          <button id="tab-performance" class="info-tab" onclick="window.DeviceInfoPopup.switchTab('performance')">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
            Performance
          </button>
        </div>

        <!-- Tab Contents - Scrollable area -->
        <div style="flex: 1; overflow-y: auto; overflow-x: hidden; padding: 1.5rem; -webkit-overflow-scrolling: touch;">
          ${this.buildDeviceTab()}
          ${this.buildNetworkTab()}
          ${this.buildSystemTab()}
          ${this.buildStorageTab()}
          ${this.buildBackendTab()}
          ${this.buildAudioTab()}
          ${this.buildPerformanceTab()}
        </div>

        <!-- Styles -->
        ${this.buildStyles()}
      </div>
    `;
  }

  /**
   * Build Device tab content
   */
  private buildDeviceTab(): string {
    return `
      <div id="content-device" class="tab-content active">
        <div class="info-grid">
          <div class="info-row">
            <span class="info-label">Device ID:</span>
            <span class="info-value" id="device-id">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Device Name:</span>
            <span class="info-value" id="device-name">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Activation Code:</span>
            <span class="info-value" id="device-code">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Status:</span>
            <span class="info-value" id="device-status">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">UUID:</span>
            <span class="info-value code" id="device-uuid">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Organization:</span>
            <span class="info-value" id="device-org">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Rotation:</span>
            <span class="info-value" id="device-rotation">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Current Playlist:</span>
            <span class="info-value" id="device-playlist">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Currently Playing:</span>
            <span class="info-value" id="device-playing">Loading...</span>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Build Network tab content
   */
  private buildNetworkTab(): string {
    return `
      <div id="content-network" class="tab-content">
        <div class="info-grid">
          <div class="info-row">
            <span class="info-label">Client IP Address:</span>
            <span class="info-value code" id="network-client-ip">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Public IP Address:</span>
            <span class="info-value code" id="network-public-ip">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Connection Type:</span>
            <span class="info-value" id="network-type">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Download Speed:</span>
            <span class="info-value" id="network-speed">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Online Status:</span>
            <span class="info-value" id="network-online">Loading...</span>
          </div>
        </div>
        <div style="margin-top: 1rem; padding: 0.75rem; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 8px; font-size: 0.85rem; color: rgba(255, 255, 255, 0.8);">
          ℹ️ Client IP is detected by backend server from HTTP request headers (most reliable). Browser-based detection blocked by mDNS privacy.
        </div>
      </div>
    `;
  }

  /**
   * Build System tab content
   */
  private buildSystemTab(): string {
    return `
      <div id="content-system" class="tab-content">
        <div class="info-grid">
          <div class="info-row">
            <span class="info-label">Platform:</span>
            <span class="info-value" id="system-platform">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Browser:</span>
            <span class="info-value" id="system-browser">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Screen Resolution:</span>
            <span class="info-value" id="system-screen">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">CPU Cores:</span>
            <span class="info-value" id="system-cores">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Language:</span>
            <span class="info-value" id="system-language">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Uptime:</span>
            <span class="info-value" id="system-uptime">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Online Status:</span>
            <span class="info-value" id="system-online">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">WebGL Support:</span>
            <span class="info-value" id="system-webgl">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Service Worker:</span>
            <span class="info-value" id="system-sw">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Device Memory:</span>
            <span class="info-value" id="system-memory">Loading...</span>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Build Storage tab content
   */
  private buildStorageTab(): string {
    return `
      <div id="content-storage" class="tab-content">
        <div class="info-grid">
          <div class="info-row">
            <span class="info-label">Storage Used:</span>
            <span class="info-value" id="storage-used">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Storage Quota:</span>
            <span class="info-value" id="storage-quota">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Usage Progress:</span>
            <span class="info-value">
              <div style="width: 200px; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden;">
                <div id="storage-bar" style="height: 100%; background: linear-gradient(90deg, #3b82f6, #10b981); width: 0%; transition: width 0.3s ease;"></div>
              </div>
              <small id="storage-percent" style="color: rgba(255,255,255,0.6); font-size: 0.85rem;">0%</small>
            </span>
          </div>
        </div>

        <div class="info-section">
          <h4 class="section-title">Cache Breakdown:</h4>
          <div class="info-grid">
            <div class="info-row">
              <span class="info-label">Videos:</span>
              <span class="info-value" id="storage-videos">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">Images:</span>
              <span class="info-value" id="storage-images">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">Audio:</span>
              <span class="info-value" id="storage-audio">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">HLS Segments:</span>
              <span class="info-value" id="storage-hls">Loading...</span>
            </div>
          </div>
        </div>

        <div class="info-section">
          <h4 class="section-title">Content Summary:</h4>
          <div class="info-grid">
            <div class="info-row">
              <span class="info-label">Assigned Content:</span>
              <span class="info-value" id="storage-assigned">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">Cached Items:</span>
              <span class="info-value" id="storage-cached-count">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">Cache Hit Rate:</span>
              <span class="info-value" id="storage-hit-rate">Loading...</span>
            </div>
          </div>
        </div>

        <!-- Assigned Content List -->
        <div class="info-section">
          <h4 class="section-title">Assigned Content:</h4>
          <div id="storage-content-list" class="content-list">
            <p style="color: rgba(255,255,255,0.6); text-align: center; padding: 1rem;">Loading...</p>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Build Backend tab content
   */
  private buildBackendTab(): string {
    return `
      <div id="content-backend" class="tab-content">
        <div class="info-grid">
          <div class="info-row">
            <span class="info-label">API URL:</span>
            <span class="info-value code" id="backend-url">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Connection Status:</span>
            <span class="info-value" id="backend-connection">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">WebSocket Status:</span>
            <span class="info-value" id="backend-ws">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Last Heartbeat:</span>
            <span class="info-value" id="backend-heartbeat">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Last Sync:</span>
            <span class="info-value" id="backend-sync">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">API Response Time:</span>
            <span class="info-value" id="backend-ping">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Sync Frequency:</span>
            <span class="info-value" id="backend-frequency">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Backend Version:</span>
            <span class="info-value" id="backend-version">Loading...</span>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Build Audio tab content
   */
  private buildAudioTab(): string {
    return `
      <div id="content-audio" class="tab-content">
        <div class="info-grid">
          <div class="info-row">
            <span class="info-label">Volume Level:</span>
            <span class="info-value" id="audio-volume">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Volume Enabled:</span>
            <span class="info-value" id="audio-enabled">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Background Audio:</span>
            <span class="info-value" id="audio-bg">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">BG Audio Status:</span>
            <span class="info-value" id="audio-bg-status">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">BG Audio Source:</span>
            <span class="info-value" id="audio-bg-source">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Muted Items:</span>
            <span class="info-value" id="audio-muted">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Supported Formats:</span>
            <span class="info-value" id="audio-formats">Loading...</span>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Build Performance tab content
   */
  private buildPerformanceTab(): string {
    return `
      <div id="content-performance" class="tab-content">
        <div class="info-grid">
          <div class="info-row">
            <span class="info-label">Uptime:</span>
            <span class="info-value" id="perf-uptime">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Memory Used:</span>
            <span class="info-value" id="perf-memory">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">FPS:</span>
            <span class="info-value" id="perf-fps">Loading...</span>
          </div>
          <div class="info-row">
            <span class="info-label">Page Load Time:</span>
            <span class="info-value" id="perf-load">Loading...</span>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Build styles
   */
  private buildStyles(): string {
    return `
      <style>
        .info-tab {
          padding: 0.75rem 1.25rem;
          background: rgba(255, 255, 255, 0.05);
          border: none;
          border-bottom: 3px solid transparent;
          color: rgba(255, 255, 255, 0.7);
          cursor: pointer;
          font-size: 0.9rem;
          font-weight: 500;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          white-space: nowrap;
          flex-shrink: 0;
        }
        .info-tab:hover {
          background: rgba(255, 255, 255, 0.1);
          color: white;
        }
        .info-tab.active {
          background: rgba(59, 130, 246, 0.1);
          border-bottom-color: #3b82f6;
          color: white;
        }
        .tab-content {
          display: none;
        }
        .tab-content.active {
          display: block;
        }
        .info-grid {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }
        .info-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.875rem 1rem;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 8px;
          border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .info-label {
          font-weight: 600;
          color: rgba(255, 255, 255, 0.8);
          font-size: 0.9rem;
        }
        .info-value {
          color: white;
          font-size: 0.9rem;
          text-align: right;
        }
        .info-value.code {
          font-family: monospace;
          font-size: 0.85rem;
        }
        .info-section {
          margin-top: 1.5rem;
        }
        .section-title {
          color: rgba(255,255,255,0.9);
          font-size: 0.95rem;
          font-weight: 600;
          margin-bottom: 0.75rem;
        }
        .content-list {
          max-height: 300px;
          overflow-y: auto;
          padding: 0.5rem 0;
        }
        .status-online {
          color: #10b981 !important;
          font-weight: 600;
        }
        .status-offline {
          color: #ef4444 !important;
          font-weight: 600;
        }
        .status-active {
          color: #10b981 !important;
          font-weight: 600;
        }
        .status-pending {
          color: #f59e0b !important;
          font-weight: 600;
        }
        .status-playing {
          color: #10b981 !important;
          font-weight: 600;
        }
        .status-paused {
          color: #f59e0b !important;
          font-weight: 600;
        }

        /* Custom scrollbar styling */
        div[style*="overflow-y: auto"]::-webkit-scrollbar {
          width: 8px;
        }
        div[style*="overflow-y: auto"]::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 4px;
        }
        div[style*="overflow-y: auto"]::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 4px;
        }
        div[style*="overflow-y: auto"]::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }

        /* Tab container scrollbar (horizontal) */
        div[style*="overflow-x: auto"]::-webkit-scrollbar {
          height: 6px;
        }
        div[style*="overflow-x: auto"]::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 3px;
        }
        div[style*="overflow-x: auto"]::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 3px;
        }
        div[style*="overflow-x: auto"]::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      </style>
    `;
  }

  /**
   * Switch tab
   */
  switchTab(tabName: string): void {
    const tabs = ['device', 'network', 'system', 'storage', 'backend', 'audio', 'performance'];
    tabs.forEach(tab => {
      const tabBtn = document.getElementById(`tab-${tab}`);
      const content = document.getElementById(`content-${tab}`);

      if (tab === tabName) {
        tabBtn?.classList.add('active');
        content?.classList.add('active');
      } else {
        tabBtn?.classList.remove('active');
        content?.classList.remove('active');
      }
    });
  }

  /**
   * Load device information from DeviceInfoCollector
   */
  private async loadDeviceInfo(): Promise<void> {
    try {
      SharedLogger.log('[DeviceInfoPopup] Loading device info...');

      // Collect all information from DeviceInfoCollector
      this.deviceInfo = await DeviceInfoCollector.collectAll();

      SharedLogger.log('[DeviceInfoPopup] Device info loaded:', this.deviceInfo);

      // Populate all tabs
      this.populateDeviceTab();
      this.populateNetworkTab();
      this.populateSystemTab();
      this.populateStorageTab();
      this.populateBackendTab();
      this.populateAudioTab();
      this.populatePerformanceTab();
    } catch (error) {
      SharedLogger.error('[DeviceInfoPopup] Error loading device info:', error);
    }
  }

  /**
   * Populate Device tab
   */
  private populateDeviceTab(): void {
    if (!this.deviceInfo) return;

    const { device } = this.deviceInfo;

    this.setText('device-id', device.deviceId ? `#${device.deviceId}` : 'Not registered');
    this.setText('device-name', device.deviceName || 'Unnamed Device');
    this.setText('device-code', device.deviceCode || '-');
    this.setText('device-uuid', device.uuid);
    this.setText('device-org', device.organizationId ? `Organization #${device.organizationId}` : 'Not assigned');
    this.setText('device-rotation', `${device.rotation}°`);

    // Status with color
    const statusEl = document.getElementById('device-status');
    if (statusEl) {
      statusEl.textContent = device.status ? device.status.toUpperCase() : 'UNKNOWN';
      statusEl.className = 'info-value';
      if (device.status === 'active') {
        statusEl.classList.add('status-active');
      } else if (device.status === 'pending') {
        statusEl.classList.add('status-pending');
      }
    }

    // Current playlist
    if (device.currentPlaylist) {
      this.setText('device-playlist', `${device.currentPlaylist.name} (${device.currentPlaylist.itemsCount} items, ${Math.floor(device.currentPlaylist.totalDuration / 60)}min)`);
    } else {
      this.setText('device-playlist', 'No playlist assigned');
    }

    // Currently playing
    if (device.currentPlaying) {
      this.setText('device-playing', `${device.currentPlaying.name} (${device.currentPlaying.type}${device.currentPlaying.isMuted ? ', muted' : ''})`);
    } else {
      this.setText('device-playing', 'Nothing playing');
    }
  }

  /**
   * Populate Network tab
   */
  private populateNetworkTab(): void {
    if (!this.deviceInfo) return;

    const { network } = this.deviceInfo;

    this.setText('network-client-ip', network.clientIP || 'Not detected');
    this.setText('network-public-ip', network.publicIP || 'Detecting...');
    this.setText('network-type', network.connectionType);
    this.setText('network-speed', network.downlinkSpeed || 'N/A');

    // Online status with color
    const onlineEl = document.getElementById('network-online');
    if (onlineEl) {
      onlineEl.textContent = network.online ? 'Online' : 'Offline';
      onlineEl.className = 'info-value';
      onlineEl.classList.add(network.online ? 'status-online' : 'status-offline');
    }
  }

  /**
   * Populate System tab
   */
  private populateSystemTab(): void {
    if (!this.deviceInfo) return;

    const { system } = this.deviceInfo;

    this.setText('system-platform', system.platform);
    this.setText('system-browser', `${system.browser.name} ${system.browser.version}`);
    this.setText('system-screen', `${system.screen.width}x${system.screen.height}`);
    this.setText('system-cores', system.cpuCores.toString());
    this.setText('system-language', system.language);
    this.setText('system-uptime', formatUptime(system.uptime));
    this.setText('system-webgl', system.webglSupport ? 'Supported' : 'Not Supported');
    this.setText('system-sw', system.serviceWorkerStatus);
    this.setText('system-memory', system.deviceMemory ? `${system.deviceMemory} GB` : 'N/A');

    // Online status with color
    const onlineEl = document.getElementById('system-online');
    if (onlineEl) {
      onlineEl.textContent = system.online ? 'Online' : 'Offline';
      onlineEl.className = 'info-value';
      onlineEl.classList.add(system.online ? 'status-online' : 'status-offline');
    }
  }

  /**
   * Populate Storage tab
   */
  private populateStorageTab(): void {
    if (!this.deviceInfo) return;

    const { storage } = this.deviceInfo;

    // Total storage
    this.setText('storage-used', `${(storage.total.used / 1048576).toFixed(2)} MB`);
    this.setText('storage-quota', `${(storage.total.quota / 1048576).toFixed(2)} MB`);
    this.setText('storage-percent', `${storage.total.percentage}%`);

    const progressBar = document.getElementById('storage-bar');
    if (progressBar) {
      progressBar.style.width = `${storage.total.percentage}%`;
    }

    // Breakdown
    this.setText('storage-videos', `${(storage.breakdown.videos / 1048576).toFixed(2)} MB`);
    this.setText('storage-images', `${(storage.breakdown.images / 1048576).toFixed(2)} MB`);
    this.setText('storage-audio', `${(storage.breakdown.audio / 1048576).toFixed(2)} MB`);
    this.setText('storage-hls', `${(storage.breakdown.hls / 1048576).toFixed(2)} MB`);

    // Summary
    this.setText('storage-assigned', `${storage.assignedContent.length} items`);
    this.setText('storage-cached-count', `${storage.cachedCount} items`);
    this.setText('storage-hit-rate', `${storage.cacheHitRate}%`);

    // Content list
    const listEl = document.getElementById('storage-content-list');
    if (listEl && storage.assignedContent.length > 0) {
      let html = '';
      for (const content of storage.assignedContent) {
        const typeIcon = this.getTypeIcon(content.type);
        const cacheStatus = content.cached ? '💾 Cached' : '🌐 Online';
        const cacheColor = content.cached ? '#10b981' : 'rgba(255,255,255,0.6)';

        html += `
          <div style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 6px; margin-bottom: 0.5rem; border: 1px solid rgba(255,255,255,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
              <span style="color: white; font-size: 0.9rem; font-weight: 500;">
                ${typeIcon} ${content.name}
              </span>
              <span style="color: ${cacheColor}; font-size: 0.8rem;">${cacheStatus}</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
              <span style="color: rgba(255,255,255,0.7);">Type: ${content.type}</span>
              <span style="color: rgba(255,255,255,0.7);">Size: ${(content.size / 1048576).toFixed(2)} MB</span>
            </div>
          </div>
        `;
      }
      listEl.innerHTML = html;
    } else if (listEl) {
      listEl.innerHTML = '<p style="color: rgba(255,255,255,0.6); text-align: center; padding: 1rem;">No content assigned yet.</p>';
    }
  }

  /**
   * Populate Backend tab
   */
  private populateBackendTab(): void {
    if (!this.deviceInfo) return;

    const { backend } = this.deviceInfo;

    this.setText('backend-url', backend.apiUrl);
    this.setText('backend-frequency', `${backend.syncFrequency}s`);
    this.setText('backend-version', backend.backendVersion || 'Unknown');

    // Connection status with color
    const connEl = document.getElementById('backend-connection');
    if (connEl) {
      connEl.textContent = backend.connectionStatus.toUpperCase();
      connEl.className = 'info-value';
      if (backend.connectionStatus === 'connected') {
        connEl.classList.add('status-online');
      } else {
        connEl.classList.add('status-offline');
      }
    }

    // WebSocket status
    const wsEl = document.getElementById('backend-ws');
    if (wsEl) {
      wsEl.textContent = backend.websocketStatus.toUpperCase();
      wsEl.className = 'info-value';
      if (backend.websocketStatus === 'connected') {
        wsEl.classList.add('status-online');
      } else {
        wsEl.classList.add('status-offline');
      }
    }

    // Heartbeat
    if (backend.lastHeartbeat) {
      const diff = Math.floor((Date.now() - backend.lastHeartbeat.getTime()) / 1000);
      this.setText('backend-heartbeat', `${diff}s ago`);
    } else {
      this.setText('backend-heartbeat', 'Never');
    }

    // Sync
    if (backend.lastSync) {
      const diff = Math.floor((Date.now() - backend.lastSync.getTime()) / 1000);
      this.setText('backend-sync', `${diff}s ago`);
    } else {
      this.setText('backend-sync', 'Never');
    }

    // Ping
    if (backend.apiResponseTime !== null) {
      this.setText('backend-ping', `${backend.apiResponseTime}ms`);
    } else {
      this.setText('backend-ping', 'N/A');
    }
  }

  /**
   * Populate Audio tab
   */
  private populateAudioTab(): void {
    if (!this.deviceInfo) return;

    const { audio } = this.deviceInfo;

    this.setText('audio-volume', `${audio.volumeLevel}%`);
    this.setText('audio-enabled', audio.volumeEnabled ? 'Yes' : 'No');

    // Background audio
    if (audio.backgroundAudio) {
      this.setText('audio-bg', audio.backgroundAudio.name);

      const statusEl = document.getElementById('audio-bg-status');
      if (statusEl) {
        statusEl.textContent = audio.backgroundAudio.status.toUpperCase();
        statusEl.className = 'info-value';
        if (audio.backgroundAudio.status === 'playing') {
          statusEl.classList.add('status-playing');
        } else if (audio.backgroundAudio.status === 'paused') {
          statusEl.classList.add('status-paused');
        }
      }

      this.setText('audio-bg-source', audio.backgroundAudio.source === 'device' ? 'Device Level' : 'Playlist Level');
    } else {
      this.setText('audio-bg', 'None');
      this.setText('audio-bg-status', 'N/A');
      this.setText('audio-bg-source', 'N/A');
    }

    // Muted items
    if (audio.mutedItems.length > 0) {
      this.setText('audio-muted', audio.mutedItems.join(', '));
    } else {
      this.setText('audio-muted', 'None');
    }

    // Supported formats
    this.setText('audio-formats', audio.supportedFormats.join(', '));
  }

  /**
   * Populate Performance tab
   */
  private populatePerformanceTab(): void {
    if (!this.deviceInfo) return;

    const { performance } = this.deviceInfo;

    this.setText('perf-uptime', formatUptime(performance.uptime));
    this.setText('perf-fps', `${performance.fps} FPS`);
    this.setText('perf-load', `${performance.loadTime}ms`);

    // Memory
    if (performance.memory) {
      this.setText('perf-memory', `${performance.memory.used.toFixed(2)} MB / ${performance.memory.limit.toFixed(2)} MB (${performance.memory.percentage}%)`);
    } else {
      this.setText('perf-memory', 'N/A');
    }
  }

  /**
   * Helper: Set text content
   */
  private setText(id: string, value: string): void {
    const el = document.getElementById(id);
    if (el) {
      el.textContent = value;
    }
  }

  /**
   * Helper: Get content type icon
   */
  private getTypeIcon(type: string): string {
    const icons: Record<string, string> = {
      video: '🎥',
      image: '🖼️',
      audio: '🎵',
      url: '🌐',
      widget: '⚙️',
    };
    return icons[type] || '📄';
  }
}

// Export singleton instance
export const DeviceInfoPopup = new DeviceInfoPopupClass();

// Make available globally for tab switching
if (typeof window !== 'undefined') {
  (window as any).DeviceInfoPopup = DeviceInfoPopup;
}
