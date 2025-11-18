/**
 * Device Info Popup Component
 * Displays device information and backend details using SharedModal
 */

import { SharedLogger } from '@shared/logger';
import { SharedDeviceState } from '@shared/device';
import { SharedModal } from '@shared/ui';
import { config } from '@shared/config';
import { getOrCreateDeviceUUID } from '@shared/utils/device-fingerprint';

/**
 * Device Info Popup Manager
 */
class DeviceInfoPopupClass {
  private button: HTMLElement | null = null;
  private isInitialized = false;

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
      maxWidth: '800px',
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
      <div style="padding: 1.5rem;">
        <!-- Tabs -->
        <div style="display: flex; gap: 0.5rem; margin-bottom: 1.5rem; border-bottom: 2px solid rgba(255, 255, 255, 0.1);">
          <button id="tab-device" class="info-tab active" onclick="window.DeviceInfoPopup.switchTab('device')">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
              <line x1="8" y1="21" x2="16" y2="21"/>
              <line x1="12" y1="17" x2="12" y2="21"/>
            </svg>
            Device
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
        </div>

        <!-- Tab Contents -->
        <div id="content-device" class="tab-content active">
          <div class="info-grid">
            <div class="info-row">
              <span class="info-label">Device ID:</span>
              <span class="info-value" id="popup-device-id">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">Device Name:</span>
              <span class="info-value" id="popup-device-name">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">Activation Code:</span>
              <span class="info-value" id="popup-code">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">Status:</span>
              <span class="info-value" id="popup-status">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">UUID:</span>
              <span class="info-value" id="popup-uuid" style="font-family: monospace; font-size: 0.9em;">Loading...</span>
            </div>
          </div>
        </div>

        <div id="content-system" class="tab-content">
          <div class="info-grid">
            <div class="info-row">
              <span class="info-label">Platform:</span>
              <span class="info-value" id="popup-platform">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">Browser:</span>
              <span class="info-value" id="popup-browser">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">Screen:</span>
              <span class="info-value" id="popup-screen">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">CPU Cores:</span>
              <span class="info-value" id="popup-cores">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">Language:</span>
              <span class="info-value" id="popup-language">Loading...</span>
            </div>
          </div>
        </div>

        <div id="content-storage" class="tab-content">
          <div class="info-grid">
            <div class="info-row">
              <span class="info-label">Storage Used:</span>
              <span class="info-value" id="popup-storage-used">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">Storage Quota:</span>
              <span class="info-value" id="popup-storage-quota">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">Storage Usage:</span>
              <span class="info-value">
                <div style="width: 200px; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden;">
                  <div id="popup-storage-bar" style="height: 100%; background: linear-gradient(90deg, #3b82f6, #10b981); width: 0%; transition: width 0.3s ease;"></div>
                </div>
              </span>
            </div>
            <div class="info-row">
              <span class="info-label">Assigned Content:</span>
              <span class="info-value" id="popup-assigned-count">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">Cached for Offline:</span>
              <span class="info-value" id="popup-cached-count">Loading...</span>
            </div>
          </div>

          <!-- Assigned Content List -->
          <div style="margin-top: 1.5rem;">
            <h4 style="color: rgba(255,255,255,0.8); font-size: 0.95rem; font-weight: 600; margin-bottom: 1rem;">Assigned Content:</h4>
            <div id="popup-content-list" style="max-height: 250px; overflow-y: auto;">
              <p style="color: rgba(255,255,255,0.6); text-align: center; padding: 1rem;">Loading...</p>
            </div>
          </div>
        </div>

        <div id="content-backend" class="tab-content">
          <div class="info-grid">
            <div class="info-row">
              <span class="info-label">Organization:</span>
              <span class="info-value" id="popup-organization">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">Last Sync:</span>
              <span class="info-value" id="popup-last-sync">Loading...</span>
            </div>
            <div class="info-row">
              <span class="info-label">API URL:</span>
              <span class="info-value" style="font-family: monospace; font-size: 0.9em;">${config.api.baseURL}</span>
            </div>
          </div>
        </div>

        <!-- Styles -->
        <style>
          .info-tab {
            padding: 0.75rem 1.5rem;
            background: rgba(255, 255, 255, 0.05);
            border: none;
            border-bottom: 3px solid transparent;
            color: rgba(255, 255, 255, 0.7);
            cursor: pointer;
            font-size: 0.95rem;
            font-weight: 500;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
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
            gap: 1rem;
          }
          .info-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
          }
          .info-label {
            font-weight: 600;
            color: rgba(255, 255, 255, 0.8);
            font-size: 0.95rem;
          }
          .info-value {
            color: white;
            font-size: 0.95rem;
            text-align: right;
          }
          .status-active {
            color: #10b981 !important;
            font-weight: 600;
          }
          .status-pending {
            color: #f59e0b !important;
            font-weight: 600;
          }
        </style>
      </div>
    `;
  }

  /**
   * Switch tab
   */
  switchTab(tabName: string): void {
    // Update tab buttons
    const tabs = ['device', 'system', 'storage', 'backend'];
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
   * Load device information from localStorage and backend
   */
  private async loadDeviceInfo(): Promise<void> {
    try {
      // Get local device state
      const deviceId = SharedDeviceState.getDeviceId();
      const deviceCode = SharedDeviceState.getDeviceCode();
      const deviceStatus = SharedDeviceState.getDeviceStatus();
      const deviceName = SharedDeviceState.getDeviceName();
      const platform = SharedDeviceState.getPlatform();
      const organizationId = SharedDeviceState.getOrganizationId();
      const deviceUUID = getOrCreateDeviceUUID();

      // Update local info
      this.updateField('popup-device-id', deviceId ? `#${deviceId}` : 'Not registered');
      this.updateField('popup-device-name', deviceName || 'Unnamed Device');
      this.updateField('popup-code', deviceCode || '-');
      this.updateField('popup-platform', platform || navigator.platform || 'Unknown');
      this.updateField('popup-uuid', deviceUUID);

      // Browser info
      const browserInfo = this.getBrowserInfo();
      this.updateField('popup-browser', browserInfo);

      // Screen info
      const screenInfo = `${screen.width}x${screen.height} (${screen.colorDepth}-bit)`;
      this.updateField('popup-screen', screenInfo);

      // CPU cores
      const cores = navigator.hardwareConcurrency || 'Unknown';
      this.updateField('popup-cores', cores.toString());

      // Language
      this.updateField('popup-language', navigator.language || 'Unknown');

      // Update status with color
      const statusElement = document.getElementById('popup-status');
      if (statusElement) {
        statusElement.textContent = deviceStatus ? deviceStatus.toUpperCase() : 'UNKNOWN';
        statusElement.className = 'info-value';
        if (deviceStatus === 'active') {
          statusElement.classList.add('status-active');
        } else if (deviceStatus === 'pending') {
          statusElement.classList.add('status-pending');
        }
      }

      // Update organization info (no need to fetch from API)
      if (organizationId) {
        this.updateField('popup-organization', `Organization #${organizationId}`);
      } else {
        this.updateField('popup-organization', 'Not assigned');
      }

      // Update last sync time
      // Since heartbeat runs every 30s, if device is active, it means sync is recent
      if (deviceStatus === 'active') {
        this.updateField('popup-last-sync', 'Active (heartbeat running)');
      } else if (deviceStatus === 'pending') {
        this.updateField('popup-last-sync', 'Pending activation');
      } else {
        this.updateField('popup-last-sync', 'Unknown');
      }

      // Load storage & cache info
      await this.loadStorageInfo();
    } catch (error) {
      SharedLogger.error('[DeviceInfoPopup] Error loading device info:', error);
    }
  }

  /**
   * Update popup field value
   */
  private updateField(id: string, value: string): void {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = value;
    }
  }

  /**
   * Get browser name and version from user agent
   */
  private getBrowserInfo(): string {
    const ua = navigator.userAgent;
    let browser = 'Unknown';
    let version = '';

    // Check for common browsers
    if (ua.includes('Firefox/')) {
      browser = 'Firefox';
      version = ua.match(/Firefox\/([0-9.]+)/)?.[1] || '';
    } else if (ua.includes('Edg/')) {
      browser = 'Edge';
      version = ua.match(/Edg\/([0-9.]+)/)?.[1] || '';
    } else if (ua.includes('Chrome/')) {
      browser = 'Chrome';
      version = ua.match(/Chrome\/([0-9.]+)/)?.[1] || '';
    } else if (ua.includes('Safari/') && !ua.includes('Chrome')) {
      browser = 'Safari';
      version = ua.match(/Version\/([0-9.]+)/)?.[1] || '';
    } else if (ua.includes('Opera/') || ua.includes('OPR/')) {
      browser = 'Opera';
      version = ua.match(/(Opera|OPR)\/([0-9.]+)/)?.[2] || '';
    }

    return version ? `${browser} ${version}` : browser;
  }

  /**
   * Load storage and cache information
   */
  private async loadStorageInfo(): Promise<void> {
    try {
      // Get Storage API estimate
      if (navigator.storage && navigator.storage.estimate) {
        try {
          const estimate = await navigator.storage.estimate();
          const usedMB = ((estimate.usage || 0) / 1048576).toFixed(2);
          const quotaMB = ((estimate.quota || 0) / 1048576).toFixed(2);
          const usagePercent = estimate.quota ? ((estimate.usage || 0) / estimate.quota * 100).toFixed(1) : '0';

          this.updateField('popup-storage-used', `${usedMB} MB`);
          this.updateField('popup-storage-quota', `${quotaMB} MB`);

          // Update progress bar
          const progressBar = document.getElementById('popup-storage-bar');
          if (progressBar) {
            progressBar.style.width = `${usagePercent}%`;
          }
        } catch (err) {
          SharedLogger.warn('[DeviceInfoPopup] Storage API failed:', err);
          this.updateField('popup-storage-used', 'Not supported on HTTP');
          this.updateField('popup-storage-quota', 'Requires HTTPS');
        }
      } else {
        this.updateField('popup-storage-used', 'Not supported');
        this.updateField('popup-storage-quota', 'Not supported');
      }

      // Get cache info from PlayerHLSCache
      await this.loadCacheInfo();
    } catch (error) {
      SharedLogger.error('[DeviceInfoPopup] Error loading storage info:', error);
      this.updateField('popup-storage-used', 'Error loading');
      this.updateField('popup-storage-quota', 'Error loading');
    }
  }

  /**
   * Load assigned content and cache information
   */
  private async loadCacheInfo(): Promise<void> {
    try {
      // Import dynamically to avoid circular dependency
      const { ServiceRegistry } = await import('@shared/services');
      const PlayerPlaylistSync = ServiceRegistry.get('PlayerPlaylistSync') as any;
      const PlayerHLSCache = ServiceRegistry.get('PlayerHLSCache') as any;

      SharedLogger.log('[DeviceInfoPopup] PlayerPlaylistSync:', PlayerPlaylistSync);
      SharedLogger.log('[DeviceInfoPopup] PlayerHLSCache:', PlayerHLSCache);

      // Get assigned content from playlist
      let assignedContent: any[] = [];
      if (PlayerPlaylistSync && PlayerPlaylistSync.getCurrentPlaylist) {
        const playlist = PlayerPlaylistSync.getCurrentPlaylist();
        SharedLogger.log('[DeviceInfoPopup] Current playlist:', playlist);
        if (playlist && playlist.items) {
          assignedContent = playlist.items;
        }
      } else {
        SharedLogger.warn('[DeviceInfoPopup] PlayerPlaylistSync.getCurrentPlaylist not available');
      }

      // Get cached HLS videos
      let cachedVideos: any[] = [];
      if (PlayerHLSCache && PlayerHLSCache.getAllCachedContent) {
        cachedVideos = await PlayerHLSCache.getAllCachedContent();
        SharedLogger.log('[DeviceInfoPopup] Cached videos:', cachedVideos);
      } else {
        SharedLogger.warn('[DeviceInfoPopup] PlayerHLSCache.getAllCachedContent not available');
      }

      SharedLogger.log('[DeviceInfoPopup] Assigned content count:', assignedContent.length);
      SharedLogger.log('[DeviceInfoPopup] Cached videos count:', cachedVideos.length);

      // Update counts
      this.updateField('popup-assigned-count', `${assignedContent.length} item${assignedContent.length !== 1 ? 's' : ''}`);
      this.updateField('popup-cached-count', `${cachedVideos.length} video${cachedVideos.length !== 1 ? 's' : ''}`);

      // Build assigned content list
      const listElement = document.getElementById('popup-content-list');
      if (listElement) {
        if (assignedContent.length === 0) {
          listElement.innerHTML = '<p style="color: rgba(255,255,255,0.6); text-align: center; padding: 1rem;">No content assigned yet.<br><small>Assign content from CMS admin dashboard.</small></p>';
        } else {
          let listHtml = '';

          for (const item of assignedContent) {
            const content = item.content;
            const contentType = content.type || 'unknown';
            const contentName = content.name || `Content ${content.id}`;

            // Check if this video is cached
            const isCached = contentType === 'video' && cachedVideos.some(c => c.contentId === content.id);
            const cacheStatus = isCached ? '💾 Cached' : (contentType === 'video' ? '🌐 Online' : '✓ Ready');

            // Icon based on content type
            let typeIcon = '📄';
            if (contentType === 'video') typeIcon = '🎥';
            else if (contentType === 'image') typeIcon = '🖼️';
            else if (contentType === 'audio') typeIcon = '🎵';

            listHtml += `
              <div style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 6px; margin-bottom: 0.5rem; border: 1px solid rgba(255,255,255,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
                  <span style="color: white; font-size: 0.9rem; font-weight: 500;">
                    ${typeIcon} ${contentName}
                  </span>
                  <span style="color: ${isCached ? '#10b981' : 'rgba(255,255,255,0.6)'}; font-size: 0.8rem;">${cacheStatus}</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                  <span style="color: rgba(255,255,255,0.7);">Type: ${contentType}</span>
                  <span style="color: rgba(255,255,255,0.7);">ID: ${content.id}</span>
                </div>
              </div>
            `;
          }

          listElement.innerHTML = listHtml;
        }
      }
    } catch (error) {
      SharedLogger.error('[DeviceInfoPopup] Error loading cache info:', error);
      this.updateField('popup-assigned-count', 'Error loading');
      this.updateField('popup-cached-count', 'Error loading');
    }
  }
}

// Export singleton instance
export const DeviceInfoPopup = new DeviceInfoPopupClass();

// Make available globally for tab switching
if (typeof window !== 'undefined') {
  (window as any).DeviceInfoPopup = DeviceInfoPopup;
}
