/**
 * Device Info Popup Component - Redesigned
 * Displays comprehensive device information using centralized DeviceInfoCollector
 *
 * @features
 * - 3 organized tabs: Status, Storage, Debug
 * - Status: Device + Network + Backend essential info
 * - Storage: Cache and content status
 * - Debug: Collapsible sections for technical info
 * - Uses DeviceInfoCollector service for all data
 * - Clean, modular architecture
 * - Real-time information updates
 */

import { SharedLogger } from '@shared/logger';
import { SharedModal } from '@shared/ui';
import { DeviceInfoCollector } from '@shared/services/device-info';
import { formatUptime } from '@shared/utils/performance-info';
import { SharedEventBus, EventNames } from '@shared/events/shared-event-bus';
import { getSharedWebSocket, getPlayerCapabilitiesReporter } from '@shared/services/service-registry';
import { detectVideoCodecs, detectAudioCodecs } from '@shared/utils/device-capabilities';
import type { CompleteDeviceInfo } from '@shared/services/device-info';

/**
 * Device Info Popup Manager
 */
class DeviceInfoPopupClass {
  private button: HTMLElement | null = null;
  private isInitialized = false;
  private deviceInfo: CompleteDeviceInfo | null = null;
  private collapsedSections: Set<string> = new Set();
  private wsEventUnsubscribe: (() => void) | null = null;
  private isPopupOpen = false;
  private activeTab: 'status' | 'debug' = 'status';
  private liveUpdateInterval: ReturnType<typeof setInterval> | null = null;
  private networkListener: (() => void) | null = null;

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

    // Initialize all sections as expanded by default (empty set = none collapsed)
    this.collapsedSections = new Set();

    this.isInitialized = true;
    SharedLogger.log('[DeviceInfoPopup] ✅ Initialized');
  }

  /**
   * Open popup and load device info
   */
  async open(): Promise<void> {
    this.isPopupOpen = true;
    const content = this.buildContent();

    SharedModal.showCustom({
      title: 'Device Information',
      content,
      width: '90%',
      maxWidth: '800px',
      showCloseButton: true,
      className: 'device-info-modal',
      onClose: () => this.cleanup()
    });

    // Load device info after modal is shown
    await this.loadDeviceInfo();
  }

  /**
   * Cleanup event listeners when popup closes
   */
  private cleanup(): void {
    this.isPopupOpen = false;

    // Stop all live updates
    this.stopLiveUpdates();

    // Cleanup WebSocket event listener
    if (this.wsEventUnsubscribe) {
      this.wsEventUnsubscribe();
      this.wsEventUnsubscribe = null;
    }

    // Reset active tab to default
    this.activeTab = 'status';

    SharedLogger.log('[DeviceInfoPopup] Cleaned up event listeners');
  }

  /**
   * Build HTML content for the modal
   */
  private buildContent(): string {
    return `
      <div style="display: flex; flex-direction: column; height: 600px; max-height: 80vh;">
        <!-- Tabs - Fixed at top (2 tabs: Status & Debug) -->
        <div class="tab-header">
          <div class="tab-nav">
            <button id="tab-status" class="tab-btn active" onclick="window.DeviceInfoPopup.switchTab('status')">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
              Status
            </button>
            <button id="tab-debug" class="tab-btn" onclick="window.DeviceInfoPopup.switchTab('debug')">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
              </svg>
              Debug
            </button>
          </div>
        </div>

        <!-- Tab Contents -->
        <div class="tab-contents-wrapper">
          ${this.buildStatusTab()}
          ${this.buildDebugTab()}
        </div>

        <!-- Styles -->
        ${this.buildStyles()}
      </div>
    `;
  }

  /**
   * Build Status tab content - Storage bar + Now Playing on top, then 3 columns below
   * This tab does NOT scroll - only Content List scrolls
   */
  private buildStatusTab(): string {
    return `
      <div id="content-status" class="tab-content active status-tab-fixed">
        <!-- Storage Bar (Full Width) -->
        <div class="storage-usage-compact">
          <div class="storage-header-row">
            <span class="storage-label">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
              </svg>
              Storage
            </span>
            <span class="storage-values">
              <span id="storage-used-text">...</span>
              <span style="color: rgba(255,255,255,0.4);">/</span>
              <span id="storage-quota-text" style="color: rgba(255,255,255,0.6);">...</span>
              <span id="storage-percent-badge" class="storage-badge-compact">0%</span>
            </span>
          </div>
          <div class="storage-bar-container-compact">
            <div id="storage-bar" class="storage-bar"></div>
          </div>
        </div>

        <!-- Now Playing (Full Width) -->
        <div class="now-playing-bar">
          <span class="now-playing-label">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            Now Playing
          </span>
          <span class="now-playing-value" id="status-playing">Loading...</span>
        </div>

        <!-- Three Column Layout -->
        <div class="status-combined-layout">
          <!-- Column 1: Device + Connection -->
          <div class="status-column-left">
            <!-- Device Section -->
            <div class="collapsible-section">
              <div class="collapsible-header" onclick="window.DeviceInfoPopup.toggleSection('status-device')">
                <span class="collapsible-icon expanded" id="icon-status-device">▶</span>
                <span>Device</span>
              </div>
              <div id="section-status-device" class="collapsible-content">
                <div class="debug-info-grid compact">
                  <div class="debug-info-row">
                    <span class="debug-info-label">ID</span>
                    <span class="debug-info-value code" id="status-device-id">Loading...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Name</span>
                    <span class="debug-info-value" id="status-device-name">Loading...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Status</span>
                    <span class="debug-info-value" id="status-device-status">Loading...</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Connection Section -->
            <div class="collapsible-section">
              <div class="collapsible-header" onclick="window.DeviceInfoPopup.toggleSection('status-connection')">
                <span class="collapsible-icon expanded" id="icon-status-connection">▶</span>
                <span>Connection</span>
              </div>
              <div id="section-status-connection" class="collapsible-content">
                <div class="debug-info-grid compact">
                  <div class="debug-info-row">
                    <span class="debug-info-label" style="display: flex; align-items: center; gap: 0.3rem;">
                      <span id="wifi-icon" class="icon-wrapper icon-pulse">${this.getWifiIcon(true)}</span>
                      Network
                    </span>
                    <span class="debug-info-value" id="status-network">Loading...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label" style="display: flex; align-items: center; gap: 0.3rem;">
                      <span id="db-icon" class="icon-wrapper icon-pulse">${this.getDatabaseIcon(true)}</span>
                      Backend
                    </span>
                    <span class="debug-info-value" id="status-connection">Loading...</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Column 2: Content Status + Cache Breakdown -->
          <div class="status-column-middle">
            <!-- Content Status Section -->
            <div class="collapsible-section">
              <div class="collapsible-header" onclick="window.DeviceInfoPopup.toggleSection('storage-status')">
                <span class="collapsible-icon expanded" id="icon-storage-status">▶</span>
                <span>Content Status</span>
              </div>
              <div id="section-storage-status" class="collapsible-content">
                <div class="debug-info-grid compact">
                  <div class="debug-info-row">
                    <span class="debug-info-label">Assigned</span>
                    <span class="debug-info-value" id="storage-assigned">0</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Cached</span>
                    <span class="debug-info-value" id="storage-cached-count">0</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Hit Rate</span>
                    <span class="debug-info-value status-online" id="storage-hit-rate">0%</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Cache Breakdown Section -->
            <div class="collapsible-section">
              <div class="collapsible-header" onclick="window.DeviceInfoPopup.toggleSection('storage-cache')">
                <span class="collapsible-icon expanded" id="icon-storage-cache">▶</span>
                <span>Cache Breakdown</span>
              </div>
              <div id="section-storage-cache" class="collapsible-content">
                <div class="debug-info-grid compact">
                  <div class="debug-info-row">
                    <span class="debug-info-label">${this.getCacheIcon('video')} Video</span>
                    <span class="debug-info-value" id="storage-video">0 MB</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">${this.getCacheIcon('image')} Images</span>
                    <span class="debug-info-value" id="storage-images">0 MB</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">${this.getCacheIcon('audio')} Audio</span>
                    <span class="debug-info-value" id="storage-audio">0 MB</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">${this.getCacheIcon('video')} HLS</span>
                    <span class="debug-info-value" id="storage-hls">0 MB</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Column 3: Content List -->
          <div class="status-column-right">
            <div class="collapsible-section">
              <div class="collapsible-header" onclick="window.DeviceInfoPopup.toggleSection('content-list')">
                <span class="collapsible-icon expanded" id="icon-content-list">▶</span>
                <span>Content List</span>
              </div>
              <div id="section-content-list" class="collapsible-content">
                <div id="storage-content-list" class="content-list-compact">
                  <p style="color: rgba(255,255,255,0.5); text-align: center; padding: 0.5rem; font-size: 0.7rem;">Loading...</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Build Debug tab content - 3-column optimized layout
   * Column 1 (LIVE): Network + Playback - real-time monitoring
   * Column 2 (HEALTH): Performance - system health metrics
   * Column 3 (DEVICE): System + Capabilities - static device info
   */
  private buildDebugTab(): string {
    return `
      <div id="content-debug" class="tab-content">
        <!-- Three Column Layout: LIVE | HEALTH | DEVICE -->
        <div class="debug-three-column">
          <!-- Column 1: LIVE (Network + Playback) -->
          <div class="debug-column">
            <!-- Network Section - connection status first -->
            <div class="collapsible-section">
              <div class="collapsible-header" onclick="window.DeviceInfoPopup.toggleSection('debug-network')">
                <span class="collapsible-icon expanded" id="icon-debug-network">▶</span>
                <span>Network</span>
              </div>
              <div id="section-debug-network" class="collapsible-content">
                <div class="debug-info-grid compact">
                  <div class="debug-info-row">
                    <span class="debug-info-label">Connection</span>
                    <span class="debug-info-value" id="debug-connection-type">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Speed</span>
                    <span class="debug-info-value" id="debug-speed">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Client IP</span>
                    <span class="debug-info-value code" id="debug-client-ip">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Public IP</span>
                    <span class="debug-info-value code" id="debug-public-ip">...</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Playback Section - errors first for quick diagnosis -->
            <div class="collapsible-section">
              <div class="collapsible-header" onclick="window.DeviceInfoPopup.toggleSection('debug-playback')">
                <span class="collapsible-icon expanded" id="icon-debug-playback">▶</span>
                <span>Playback</span>
              </div>
              <div id="section-debug-playback" class="collapsible-content">
                <div class="debug-info-grid compact">
                  <div class="debug-info-row highlight-error">
                    <span class="debug-info-label">Error %</span>
                    <span class="debug-info-value" id="debug-error-rate">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Stalls</span>
                    <span class="debug-info-value" id="debug-stalls">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Buffers</span>
                    <span class="debug-info-value" id="debug-buffers">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Failures</span>
                    <span class="debug-info-value" id="debug-load-failures">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Plays</span>
                    <span class="debug-info-value" id="debug-content-plays">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Quality SW</span>
                    <span class="debug-info-value" id="debug-quality-switches">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">First Play</span>
                    <span class="debug-info-value" id="debug-ttfp">...</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Column 2: HEALTH (Performance only) -->
          <div class="debug-column">
            <div class="collapsible-section">
              <div class="collapsible-header" onclick="window.DeviceInfoPopup.toggleSection('debug-performance')">
                <span class="collapsible-icon expanded" id="icon-debug-performance">▶</span>
                <span>Performance</span>
              </div>
              <div id="section-debug-performance" class="collapsible-content">
                <div class="debug-info-grid compact">
                  <div class="debug-info-row">
                    <span class="debug-info-label">Memory</span>
                    <span class="debug-info-value" id="debug-perf-memory">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">FPS</span>
                    <span class="debug-info-value" id="debug-fps">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">CPU</span>
                    <span class="debug-info-value" id="debug-cpu-pressure">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Long Tasks</span>
                    <span class="debug-info-value" id="debug-long-tasks">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">TTFB</span>
                    <span class="debug-info-value" id="debug-ttfb">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Load Time</span>
                    <span class="debug-info-value" id="debug-load-time">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Uptime</span>
                    <span class="debug-info-value" id="debug-uptime">...</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Column 3: DEVICE (System + Capabilities) -->
          <div class="debug-column">
            <!-- System Info -->
            <div class="collapsible-section">
              <div class="collapsible-header" onclick="window.DeviceInfoPopup.toggleSection('debug-system')">
                <span class="collapsible-icon expanded" id="icon-debug-system">▶</span>
                <span>System</span>
              </div>
              <div id="section-debug-system" class="collapsible-content">
                <div class="debug-info-grid compact">
                  <div class="debug-info-row">
                    <span class="debug-info-label">Platform</span>
                    <span class="debug-info-value" id="debug-platform">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Browser</span>
                    <span class="debug-info-value" id="debug-browser">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Resolution</span>
                    <span class="debug-info-value" id="debug-resolution">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Rotation</span>
                    <span class="debug-info-value" id="debug-rotation">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">SW Status</span>
                    <span class="debug-info-value" id="debug-sw">...</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Device Capabilities -->
            <div class="collapsible-section">
              <div class="collapsible-header" onclick="window.DeviceInfoPopup.toggleSection('debug-capabilities')">
                <span class="collapsible-icon expanded" id="icon-debug-capabilities">▶</span>
                <span>Capabilities</span>
              </div>
              <div id="section-debug-capabilities" class="collapsible-content">
                <div class="debug-info-grid compact">
                  <div class="debug-info-row">
                    <span class="debug-info-label">Video</span>
                    <span class="debug-info-value codec-badges" id="debug-video-codecs">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Audio</span>
                    <span class="debug-info-value codec-badges" id="debug-audio-codecs">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Hardware</span>
                    <span class="debug-info-value" id="debug-hardware">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">Display</span>
                    <span class="debug-info-value" id="debug-display">...</span>
                  </div>
                  <div class="debug-info-row">
                    <span class="debug-info-label">WebGL</span>
                    <span class="debug-info-value" id="debug-webgl-details">...</span>
                  </div>
                </div>
              </div>
            </div>
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
        /* Tab Header - Fixed at top (matching connection-log-popup) */
        .tab-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem 1rem 0 1rem;
          border-bottom: 2px solid rgba(255, 255, 255, 0.1);
          flex-shrink: 0;
        }

        /* Tab Navigation - Matching connection-log-popup */
        .tab-nav {
          display: flex;
          gap: 0.35rem;
          overflow-x: auto;
          overflow-y: hidden;
          -webkit-overflow-scrolling: touch;
          scrollbar-width: thin;
          flex: 1;
        }
        .tab-btn {
          padding: 0.5rem 0.75rem;
          background: rgba(255, 255, 255, 0.05);
          border: none;
          border-bottom: 2px solid transparent;
          color: rgba(255, 255, 255, 0.7);
          cursor: pointer;
          font-size: 0.75rem;
          font-weight: 500;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          gap: 0.35rem;
          white-space: nowrap;
          flex: 1;
          justify-content: center;
          border-radius: 6px 6px 0 0;
        }
        .tab-btn:hover {
          background: rgba(255, 255, 255, 0.1);
          color: white;
        }
        .tab-btn.active {
          background: rgba(59, 130, 246, 0.1);
          border-bottom-color: #3b82f6;
          color: white;
        }
        .tab-btn svg {
          width: 14px;
          height: 14px;
        }

        /* Tab scrollbar (horizontal) */
        .tab-nav::-webkit-scrollbar {
          height: 4px;
        }
        .tab-nav::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.03);
          border-radius: 2px;
        }
        .tab-nav::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.15);
          border-radius: 2px;
        }
        .tab-nav::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.25);
        }
        .tab-contents-wrapper {
          flex: 1;
          overflow: hidden;
          padding: 1rem;
          display: flex;
          flex-direction: column;
        }
        .tab-content {
          display: none;
          flex: 1;
          min-height: 0;
        }
        .tab-content.active {
          display: flex;
          flex-direction: column;
        }
        /* Status tab - no scroll, fixed height */
        .status-tab-fixed {
          overflow: hidden;
        }
        .status-tab-fixed .status-combined-layout {
          flex: 1;
          min-height: 0;
        }
        .status-tab-fixed .status-column-right {
          display: flex;
          flex-direction: column;
          min-height: 0;
        }
        .status-tab-fixed .status-column-right .collapsible-section {
          flex: 1;
          display: flex;
          flex-direction: column;
          min-height: 0;
        }
        .status-tab-fixed .status-column-right .collapsible-content {
          flex: 1;
          min-height: 0;
          overflow: hidden;
        }
        .status-tab-fixed .content-list-compact {
          max-height: none;
          height: 100%;
          overflow-y: auto;
        }
        /* Debug tab - scrollable */
        #content-debug {
          overflow-y: auto;
          -webkit-overflow-scrolling: touch;
        }
        .info-section-header {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          font-size: 0.75rem;
          font-weight: 600;
          color: rgba(255, 255, 255, 0.5);
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 0.5rem;
          margin-top: 1rem;
        }
        .info-section-header:first-child {
          margin-top: 0;
        }
        .info-grid {
          display: flex;
          flex-direction: column;
        }
        .info-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.35rem 0;
          border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .info-row:last-child {
          border-bottom: none;
        }
        .info-label {
          color: rgba(255, 255, 255, 0.6);
          font-size: 0.85rem;
        }
        .info-value {
          color: white;
          font-size: 0.85rem;
          text-align: right;
        }
        .info-value.code {
          font-family: monospace;
          font-size: 0.8rem;
          color: rgba(255, 255, 255, 0.8);
        }

        /* Styled Info Grid - with background rows */
        .info-grid-styled {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .info-row-styled {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem 0.75rem;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 6px;
        }
        .info-row-styled .info-label {
          color: rgba(255, 255, 255, 0.6);
          font-size: 0.85rem;
        }
        .info-row-styled .info-value {
          color: white;
          font-size: 0.85rem;
          font-weight: 500;
          text-align: right;
        }

        /* Storage Usage - Compact Header */
        .storage-usage-compact {
          margin-bottom: 0.5rem;
          padding-bottom: 0.5rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }
        .storage-header-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.4rem;
        }
        .storage-label {
          display: flex;
          align-items: center;
          gap: 0.3rem;
          font-size: 0.75rem;
          font-weight: 600;
          color: rgba(255, 255, 255, 0.7);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        /* Now Playing Bar */
        .now-playing-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem 0.75rem;
          margin-bottom: 0.75rem;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 6px;
          border-left: 3px solid #10b981;
        }
        .now-playing-label {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          font-size: 0.75rem;
          font-weight: 600;
          color: rgba(255, 255, 255, 0.7);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .now-playing-value {
          font-size: 0.8rem;
          font-weight: 500;
          color: white;
          max-width: 60%;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .storage-values {
          display: flex;
          align-items: baseline;
          gap: 0.25rem;
          font-size: 0.8rem;
          color: white;
        }
        .storage-badge-compact {
          color: #60a5fa;
          font-size: 0.7rem;
          font-weight: 600;
          background: rgba(96, 165, 250, 0.15);
          padding: 0.1rem 0.35rem;
          border-radius: 3px;
          margin-left: 0.25rem;
        }
        .storage-bar-container-compact {
          height: 4px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 2px;
          overflow: hidden;
        }
        .storage-bar {
          height: 100%;
          background: linear-gradient(90deg, #3b82f6, #10b981);
          width: 0%;
          transition: width 0.5s ease;
          border-radius: 2px;
        }

        /* Content List Compact */
        .content-list-compact {
          max-height: 350px;
          overflow-y: auto;
        }
        .content-list-compact::-webkit-scrollbar {
          width: 4px;
        }
        .content-list-compact::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 2px;
        }
        .content-list-compact::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.15);
          border-radius: 2px;
        }

        /* Combined Status Tab Layout - 3 equal columns */
        .status-combined-layout {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 0.75rem;
          width: 100%;
          min-width: 0;
        }
        .status-column-left,
        .status-column-middle,
        .status-column-right {
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
          min-width: 0;
          overflow: hidden;
        }
        .status-column-left .collapsible-section,
        .status-column-middle .collapsible-section,
        .status-column-right .collapsible-section {
          margin-top: 0;
          border-top: none;
        }
        .status-column-left .collapsible-header,
        .status-column-middle .collapsible-header,
        .status-column-right .collapsible-header {
          padding: 0.4rem 0.5rem;
          font-size: 0.75rem;
        }
        .status-column-left .collapsible-content,
        .status-column-middle .collapsible-content,
        .status-column-right .collapsible-content {
          padding: 0.4rem;
        }

        /* Three Column Layout for Debug Tab - Same gap as Status tab */
        .debug-three-column {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 0.75rem;
        }
        .debug-column {
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
        }
        .debug-column .collapsible-section {
          margin-top: 0;
          border-top: none;
        }
        .debug-column .collapsible-section:first-child {
          margin-top: 0;
        }
        .debug-column .collapsible-header {
          padding: 0.4rem 0.5rem;
          font-size: 0.75rem;
        }
        .debug-column .collapsible-content {
          padding: 0.4rem;
        }

        /* Debug Info Grid - compact styled rows */
        .debug-info-grid {
          display: flex;
          flex-direction: column;
          gap: 0.3rem;
          min-width: 0;
          width: 100%;
        }
        .debug-info-grid.compact {
          gap: 0.2rem;
        }
        .debug-info-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.25rem 0.4rem;
          background: rgba(255, 255, 255, 0.03);
          border-radius: 4px;
          min-width: 0;
        }
        .debug-info-label {
          color: rgba(255, 255, 255, 0.6);
          font-size: 0.7rem;
          flex-shrink: 0;
        }
        .debug-info-value {
          color: white;
          font-size: 0.7rem;
          font-weight: 500;
          text-align: right;
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .debug-info-value.code {
          font-family: monospace;
          font-size: 0.65rem;
          color: rgba(255, 255, 255, 0.85);
        }
        .debug-info-value.codec-badges {
          font-size: 0.6rem;
        }
        /* Highlight row for critical info like errors */
        .debug-info-row.highlight-error {
          background: rgba(239, 68, 68, 0.1);
          border-left: 2px solid #ef4444;
        }

        /* Legacy Content Status Summary (keep for compatibility) */
        .content-status-summary {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          text-align: center;
          border-bottom: 1px solid rgba(255, 255, 255, 0.06);
          padding-bottom: 0.75rem;
          margin-bottom: 0.5rem;
        }
        .content-stat {
          display: flex;
          flex-direction: column;
          align-items: center;
        }
        .content-stat-value {
          font-size: 1.25rem;
          font-weight: 700;
          color: white;
        }
        .content-stat-label {
          font-size: 0.7rem;
          color: rgba(255, 255, 255, 0.5);
        }

        /* Collapsible Sections */
        .collapsible-section {
          margin-top: 0.5rem;
          border-top: 1px solid rgba(255, 255, 255, 0.06);
          min-width: 0;
          overflow: hidden;
        }
        .collapsible-section:first-child {
          border-top: none;
          margin-top: 0;
        }
        .collapsible-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 0;
          cursor: pointer;
          font-weight: 500;
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.8);
          transition: color 0.2s ease;
        }
        .collapsible-header:hover {
          color: white;
        }
        .collapsible-icon {
          font-size: 0.65rem;
          transition: transform 0.2s ease;
          color: rgba(255, 255, 255, 0.4);
          flex-shrink: 0;
        }
        .collapsible-icon.expanded {
          transform: rotate(90deg);
        }
        .collapsible-content {
          padding-left: 1rem;
          transition: max-height 0.3s ease, padding 0.3s ease;
          max-height: 1000px;
          overflow: hidden;
          min-width: 0;
        }
        .collapsible-content.collapsed {
          max-height: 0;
          padding: 0;
        }

        /* Content List */
        .content-list {
          max-height: 200px;
          overflow-y: auto;
        }
        .content-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.3rem 0;
          font-size: 0.8rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        }
        .content-item:last-child {
          border-bottom: none;
        }

        /* Status Colors */
        .status-online, .status-good {
          color: #10b981 !important;
        }
        .status-offline, .status-error {
          color: #ef4444 !important;
        }
        .status-warning {
          color: #f59e0b !important;
        }
        .status-active {
          color: #10b981 !important;
        }
        .status-pending {
          color: #f59e0b !important;
        }

        /* Icon Animations */
        .icon-wrapper {
          display: inline-flex;
          align-items: center;
          justify-content: center;
        }

        /* Smooth pulse animation for online/connected state */
        @keyframes iconPulse {
          0%, 100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.6;
            transform: scale(0.95);
          }
        }
        .icon-pulse {
          animation: iconPulse 2s ease-in-out infinite;
        }

        /* Warning blink animation: 2 blinks, pause, repeat */
        @keyframes iconWarningBlink {
          0%, 10% { opacity: 1; }
          15%, 25% { opacity: 0.2; }
          30%, 40% { opacity: 1; }
          45%, 55% { opacity: 0.2; }
          60%, 100% { opacity: 1; }
        }
        .icon-warning-blink {
          animation: iconWarningBlink 2.5s ease-in-out infinite;
        }

        /* Custom Scrollbar */
        .content-list::-webkit-scrollbar,
        div[style*="overflow-y: auto"]::-webkit-scrollbar {
          width: 4px;
        }
        .content-list::-webkit-scrollbar-track,
        div[style*="overflow-y: auto"]::-webkit-scrollbar-track {
          background: transparent;
        }
        .content-list::-webkit-scrollbar-thumb,
        div[style*="overflow-y: auto"]::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.15);
          border-radius: 2px;
        }

        /* Codec badge styles - compact for 3-column layout */
        .codec-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.15rem;
          padding: 0.1rem 0.25rem;
          border-radius: 3px;
          font-size: 0.55rem;
          font-weight: 600;
        }
        .codec-badge.supported {
          background: rgba(16, 185, 129, 0.15);
          color: #10b981;
          border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .codec-badge.not-supported {
          background: rgba(239, 68, 68, 0.1);
          color: rgba(239, 68, 68, 0.6);
          border: 1px solid rgba(239, 68, 68, 0.2);
        }
        .codec-badges {
          display: flex;
          gap: 0.2rem;
          flex-wrap: wrap;
          justify-content: flex-end;
        }
      </style>
    `;
  }

  /**
   * Toggle collapsible section
   */
  toggleSection(sectionId: string): void {
    const section = document.getElementById(`section-${sectionId}`);
    const icon = document.getElementById(`icon-${sectionId}`);

    if (section && icon) {
      section.classList.toggle('collapsed');
      icon.classList.toggle('expanded');

      // Track state
      if (section.classList.contains('collapsed')) {
        this.collapsedSections.add(sectionId);
      } else {
        this.collapsedSections.delete(sectionId);
      }
    }
  }

  /**
   * Switch tab
   */
  switchTab(tabName: string): void {
    const tabs = ['status', 'storage', 'debug'];
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

    // Track active tab for live updates
    this.activeTab = tabName as 'status' | 'debug';
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
      this.populateStatusTab();
      this.populateStorageTab();
      this.populateDebugTab();

      // Listen for WebSocket connection changes while popup is open
      // This fixes the race condition where popup opens before WS connects
      this.wsEventUnsubscribe = SharedEventBus.on(EventNames.WS_CONNECTED, () => {
        SharedLogger.log('[DeviceInfoPopup] WebSocket connected - updating status');
        this.updateConnectionStatus();
      });

      // Also check WebSocket status after a short delay (fallback for timing issues)
      setTimeout(() => {
        if (this.isPopupOpen) {
          this.updateConnectionStatus();
        }
      }, 1000);

      // Start live updates for all tabs
      this.startLiveUpdates();
    } catch (error) {
      SharedLogger.error('[DeviceInfoPopup] Error loading device info:', error);
    }
  }

  /**
   * Start live updates for all tabs (updates active tab every 2 seconds)
   */
  private startLiveUpdates(): void {
    // Clear any existing interval
    if (this.liveUpdateInterval) {
      clearInterval(this.liveUpdateInterval);
    }

    // Main update loop - runs every 2 seconds
    this.liveUpdateInterval = setInterval(async () => {
      if (!this.isPopupOpen) {
        this.stopLiveUpdates();
        return;
      }

      // Update based on active tab
      switch (this.activeTab) {
        case 'status':
          await this.updateStatusTabLive();
          await this.updateStorageTabLive(); // Storage is now part of Status tab
          break;
        case 'debug':
          await this.updateDebugTabLive();
          break;
      }
    }, 2000);

    // Add network event listeners
    this.setupNetworkListeners();
  }

  /**
   * Stop live updates
   */
  private stopLiveUpdates(): void {
    if (this.liveUpdateInterval) {
      clearInterval(this.liveUpdateInterval);
      this.liveUpdateInterval = null;
    }
    if (this.networkListener) {
      this.networkListener();
      this.networkListener = null;
    }
  }

  /**
   * Setup network online/offline event listeners
   */
  private setupNetworkListeners(): void {
    const updateNetwork = () => {
      if (this.isPopupOpen) {
        this.updateStatusTabLive();
      }
    };

    window.addEventListener('online', updateNetwork);
    window.addEventListener('offline', updateNetwork);

    this.networkListener = () => {
      window.removeEventListener('online', updateNetwork);
      window.removeEventListener('offline', updateNetwork);
    };
  }

  /**
   * Update Status tab fields live
   */
  private async updateStatusTabLive(): Promise<void> {
    try {
      const freshInfo = await DeviceInfoCollector.collectAll();
      if (!freshInfo) return;

      // Update Now Playing
      if (freshInfo.device.currentPlaying) {
        this.setText('status-playing', `${freshInfo.device.currentPlaying.name} (${freshInfo.device.currentPlaying.type})`);
      } else {
        this.setText('status-playing', 'Nothing playing');
      }

      // Update Network Status + WiFi icon
      const networkEl = document.getElementById('status-network');
      const wifiIconEl = document.getElementById('wifi-icon');
      if (networkEl) {
        const connType = freshInfo.network.connectionType !== 'Unknown'
          ? ` (${freshInfo.network.connectionType})` : '';
        networkEl.innerHTML = freshInfo.network.online
          ? `<span class="status-online">Online${connType}</span>`
          : `<span class="status-offline">Offline</span>`;
      }
      if (wifiIconEl) {
        wifiIconEl.innerHTML = this.getWifiIcon(freshInfo.network.online);
        // Update animation class based on status
        wifiIconEl.classList.remove('icon-pulse', 'icon-warning-blink');
        wifiIconEl.classList.add(freshInfo.network.online ? 'icon-pulse' : 'icon-warning-blink');
      }

      // Update Backend status + Database icon
      const connEl = document.getElementById('status-connection');
      const dbIconEl = document.getElementById('db-icon');
      const apiOk = freshInfo.backend.connectionStatus === 'connected';
      const wsOk = freshInfo.backend.websocketStatus === 'connected';
      const backendConnected = apiOk || wsOk;

      if (connEl) {
        if (apiOk && wsOk) {
          connEl.innerHTML = '<span class="status-online">API + WS Connected</span>';
        } else if (apiOk) {
          connEl.innerHTML = '<span class="status-pending">API Only</span>';
        } else if (wsOk) {
          connEl.innerHTML = '<span class="status-pending">WS Only</span>';
        } else {
          connEl.innerHTML = '<span class="status-offline">Disconnected</span>';
        }
      }
      if (dbIconEl) {
        dbIconEl.innerHTML = this.getDatabaseIcon(backendConnected);
        // Update animation class based on status
        dbIconEl.classList.remove('icon-pulse', 'icon-warning-blink');
        dbIconEl.classList.add(backendConnected ? 'icon-pulse' : 'icon-warning-blink');
      }
    } catch (error) {
      // Silently ignore errors during polling
    }
  }

  /**
   * Update Storage tab fields live
   */
  private async updateStorageTabLive(): Promise<void> {
    try {
      const freshInfo = await DeviceInfoCollector.collectAll();
      if (!freshInfo) return;

      const { storage } = freshInfo;

      // Update storage bar
      const usedMB = (storage.total.used / 1048576).toFixed(1);
      this.setText('storage-used-text', `${usedMB} MB`);

      const storagePercent = storage.total.percentage;
      const percentDisplay = storagePercent < 1 && storagePercent > 0
        ? `${storagePercent.toFixed(1)}%`
        : `${Math.round(storagePercent)}%`;

      // Color storage percentage based on usage
      const storageBadge = document.getElementById('storage-percent-badge');
      if (storageBadge) {
        storageBadge.textContent = percentDisplay;
        storageBadge.className = 'storage-badge-compact';
        if (storagePercent >= 80) {
          storageBadge.classList.add('status-error');
        } else if (storagePercent >= 50) {
          storageBadge.classList.add('status-warning');
        }
      }

      // Update progress bar width
      const progressBar = document.getElementById('storage-bar');
      if (progressBar) {
        (progressBar as HTMLElement).style.width = `${Math.min(storagePercent, 100)}%`;
      }

      // Update cache breakdown
      this.setText('storage-video', `${(storage.breakdown.videos / 1048576).toFixed(1)} MB`);
      this.setText('storage-images', `${(storage.breakdown.images / 1048576).toFixed(1)} MB`);
      this.setText('storage-audio', `${(storage.breakdown.audio / 1048576).toFixed(1)} MB`);

      // Update cached count
      this.setText('storage-cached-count', String(storage.cachedCount));

      // Update hit rate with color
      const hitRate = storage.cacheHitRate;
      const hitRateEl = document.getElementById('storage-hit-rate');
      if (hitRateEl) {
        hitRateEl.textContent = `${hitRate}%`;
        hitRateEl.className = 'debug-info-value';
        if (hitRate >= 80) {
          hitRateEl.classList.add('status-good');
        } else if (hitRate >= 50) {
          hitRateEl.classList.add('status-warning');
        } else {
          hitRateEl.classList.add('status-error');
        }
      }
    } catch (error) {
      // Silently ignore errors during polling
    }
  }

  /**
   * Update Debug tab fields live
   */
  private async updateDebugTabLive(): Promise<void> {
    try {
      const freshInfo = await DeviceInfoCollector.collectAll();
      if (!freshInfo) return;

      const { performance, system, playbackStats } = freshInfo;

      // Update Performance section - Basic
      this.setText('debug-uptime', formatUptime(performance.uptime));
      this.setText('debug-load-time', `${performance.loadTime} ms`);

      // FPS with color
      this.setHtml('debug-fps', this.formatFps(performance.fps));

      if (performance.memory) {
        this.setText('debug-perf-memory', `${performance.memory.used.toFixed(0)} MB / ${performance.memory.limit.toFixed(0)} MB`);
      }

      // Update Performance section - Advanced (Phase 4)
      this.setHtml('debug-cpu-pressure', this.formatCpuPressure(performance.cpuPressure));
      this.setHtml('debug-long-tasks', this.formatLongTasks(performance.longTasksCount));
      this.setText('debug-ttfb', performance.ttfbMs !== null ? `${performance.ttfbMs}ms` : 'N/A');

      // Update Playback Stats section (Phase 3: Behavioral Metrics)
      this.setText('debug-ttfp', playbackStats.timeToFirstPlaybackMs !== null
        ? `${playbackStats.timeToFirstPlaybackMs.toFixed(0)}ms`
        : 'N/A');
      this.setText('debug-content-plays', `${playbackStats.contentPlayCount}`);
      this.setHtml('debug-stalls', this.formatCount(playbackStats.playbackStallsCount));
      this.setHtml('debug-buffers', this.formatCount(playbackStats.bufferUnderrunsCount));
      this.setText('debug-quality-switches', `${playbackStats.qualitySwitchesCount}`);
      this.setHtml('debug-load-failures', this.formatCount(playbackStats.contentLoadFailuresCount));
      this.setHtml('debug-error-rate', this.formatErrorRate(playbackStats.errorRatePercent));

      // Update online status in Network section
      const onlineEl = document.getElementById('debug-online');
      if (onlineEl) {
        onlineEl.innerHTML = system.online
          ? '<span class="status-online">● Online</span>'
          : '<span class="status-offline">● Offline</span>';
      }
    } catch (error) {
      // Silently ignore errors during polling
    }
  }

  /**
   * Update connection status dynamically (called when WebSocket connects)
   */
  private updateConnectionStatus(): void {
    if (!this.isPopupOpen) return;

    const connEl = document.getElementById('status-connection');
    const dbIconEl = document.getElementById('db-icon');

    // Check current WebSocket status directly
    const SharedWebSocket = getSharedWebSocket();
    const wsState = (SharedWebSocket as any)?.state;
    const wsReadyState = (SharedWebSocket as any)?.ws?.readyState;
    const wsConnected = wsState === 'connected' || wsReadyState === 1; // WebSocket.OPEN = 1

    // API status from cached deviceInfo
    const apiOk = this.deviceInfo?.backend?.connectionStatus === 'connected';
    const backendConnected = apiOk || wsConnected;

    SharedLogger.log('[DeviceInfoPopup] Updating connection status:', {
      apiOk,
      wsConnected,
      wsState,
      wsReadyState
    });

    if (connEl) {
      if (apiOk && wsConnected) {
        connEl.innerHTML = '<span class="status-online">API + WS Connected</span>';
      } else if (apiOk) {
        connEl.innerHTML = '<span class="status-pending">API Only</span>';
      } else if (wsConnected) {
        connEl.innerHTML = '<span class="status-pending">WS Only</span>';
      } else {
        connEl.innerHTML = '<span class="status-offline">Disconnected</span>';
      }
    }

    // Update database icon with animation
    if (dbIconEl) {
      dbIconEl.innerHTML = this.getDatabaseIcon(backendConnected);
      // Update animation class based on status
      dbIconEl.classList.remove('icon-pulse', 'icon-warning-blink');
      dbIconEl.classList.add(backendConnected ? 'icon-pulse' : 'icon-warning-blink');
    }
  }

  /**
   * Populate Status tab
   */
  private populateStatusTab(): void {
    if (!this.deviceInfo) return;

    const { device, network, backend, storage } = this.deviceInfo;

    // Device section
    this.setText('status-device-id', device.deviceId ? `#${device.deviceId}` : 'Not registered');
    this.setText('status-device-name', device.deviceName || 'Unnamed Device');

    // Status with color
    const statusEl = document.getElementById('status-device-status');
    if (statusEl) {
      statusEl.textContent = device.status ? device.status.toUpperCase() : 'UNKNOWN';
      statusEl.className = 'info-value';
      if (device.status === 'active') {
        statusEl.classList.add('status-active');
      } else if (device.status === 'pending') {
        statusEl.classList.add('status-pending');
      }
    }

    // Content section - show breakdown by source
    const contentEl = document.getElementById('status-content');
    if (contentEl) {
      const totalContent = storage.assignedContent.length;
      const directCount = storage.assignedContent.filter(c => c.source === 'direct').length;
      const tagCount = storage.assignedContent.filter(c => c.source === 'tag').length;
      const playlistCount = storage.assignedContent.filter(c => c.source === 'playlist').length;

      if (totalContent > 0) {
        const parts: string[] = [];
        if (directCount > 0) parts.push(`${directCount} direct`);
        if (tagCount > 0) parts.push(`${tagCount} tag`);
        if (playlistCount > 0) parts.push(`${playlistCount} playlist`);

        contentEl.textContent = `${totalContent} content (${parts.join(', ')})`;
      } else {
        contentEl.textContent = 'No content assigned';
      }
    }

    // Now playing section
    if (device.currentPlaying) {
      this.setText('status-playing', `${device.currentPlaying.name} (${device.currentPlaying.type})`);
    } else {
      this.setText('status-playing', 'Nothing playing');
    }

    // Connection section - Network status + WiFi icon
    const networkEl = document.getElementById('status-network');
    const wifiIconEl = document.getElementById('wifi-icon');
    if (networkEl) {
      const connType = network.connectionType !== 'Unknown' ? ` (${network.connectionType})` : '';
      networkEl.innerHTML = network.online
        ? `<span class="status-online">Online${connType}</span>`
        : `<span class="status-offline">Offline</span>`;
    }
    if (wifiIconEl) {
      wifiIconEl.innerHTML = this.getWifiIcon(network.online);
      // Update animation class based on status
      wifiIconEl.classList.remove('icon-pulse', 'icon-warning-blink');
      wifiIconEl.classList.add(network.online ? 'icon-pulse' : 'icon-warning-blink');
    }

    // Combined API + WebSocket status + Database icon
    const connEl = document.getElementById('status-connection');
    const dbIconEl = document.getElementById('db-icon');
    const apiOk = backend.connectionStatus === 'connected';
    const wsOk = backend.websocketStatus === 'connected';
    const backendConnected = apiOk || wsOk;

    if (connEl) {
      if (apiOk && wsOk) {
        connEl.innerHTML = '<span class="status-online">API + WS Connected</span>';
      } else if (apiOk) {
        connEl.innerHTML = '<span class="status-pending">API Only</span>';
      } else if (wsOk) {
        connEl.innerHTML = '<span class="status-pending">WS Only</span>';
      } else {
        connEl.innerHTML = '<span class="status-offline">Disconnected</span>';
      }
    }
    if (dbIconEl) {
      dbIconEl.innerHTML = this.getDatabaseIcon(backendConnected);
      // Update animation class based on status
      dbIconEl.classList.remove('icon-pulse', 'icon-warning-blink');
      dbIconEl.classList.add(backendConnected ? 'icon-pulse' : 'icon-warning-blink');
    }
  }

  /**
   * Populate Storage tab
   */
  private populateStorageTab(): void {
    if (!this.deviceInfo) return;

    const { storage } = this.deviceInfo;

    // Debug logging - shows in console
    console.warn('[DeviceInfoPopup] Storage Tab Data:', {
      used: storage.total.used,
      quota: storage.total.quota,
      percentage: storage.total.percentage,
      breakdown: storage.breakdown,
      cachedCount: storage.cachedCount,
      assignedCount: storage.assignedContent.length,
    });

    // Total storage
    const usedMB = (storage.total.used / 1048576).toFixed(1);
    const quotaMB = (storage.total.quota / 1048576).toFixed(1);

    this.setText('storage-used-text', `${usedMB} MB`);
    this.setText('storage-quota-text', `/ ${quotaMB} MB`);

    // Display percentage with proper formatting
    const percentDisplay = storage.total.percentage < 1 && storage.total.percentage > 0
      ? `${storage.total.percentage.toFixed(1)}%`
      : `${Math.round(storage.total.percentage)}%`;
    this.setText('storage-percent-badge', percentDisplay);

    const progressBar = document.getElementById('storage-bar');
    if (progressBar) {
      // Ensure minimum 1% width if there's any usage, so bar is visible
      const displayPercent = storage.total.percentage > 0 ? Math.max(1, storage.total.percentage) : 0;
      progressBar.style.width = `${displayPercent}%`;
      console.warn('[DeviceInfoPopup] Storage bar width set to:', `${displayPercent}%`);
    }

    // Breakdown - show video and HLS separately for better visibility
    this.setText('storage-video', `${(storage.breakdown.videos / 1048576).toFixed(1)} MB`);
    this.setText('storage-images', `${(storage.breakdown.images / 1048576).toFixed(1)} MB`);
    this.setText('storage-audio', `${(storage.breakdown.audio / 1048576).toFixed(1)} MB`);
    this.setText('storage-hls', `${(storage.breakdown.hls / 1048576).toFixed(1)} MB`);

    // Summary - count only assigned content that is cached
    const cachedAssignedCount = storage.assignedContent.filter(c => c.cached).length;
    this.setText('storage-assigned', storage.assignedContent.length.toString());
    this.setText('storage-cached-count', cachedAssignedCount.toString());
    this.setText('storage-hit-rate', `${storage.cacheHitRate}%`);

    // Content list - grouped by source (Direct, Tag, Playlist)
    const listEl = document.getElementById('storage-content-list');
    if (listEl && storage.assignedContent.length > 0) {
      // Group content by source
      const directContent = storage.assignedContent.filter(c => c.source === 'direct');
      const tagContent = storage.assignedContent.filter(c => c.source === 'tag');
      const playlistContent = storage.assignedContent.filter(c => c.source === 'playlist');

      // Format size helper
      const formatSize = (bytes: number): string => {
        if (bytes === 0) return '0';
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1048576) return `${(bytes / 1024).toFixed(0)} KB`;
        return `${(bytes / 1048576).toFixed(1)} MB`;
      };

      // Build content item HTML
      const buildContentItem = (content: any) => {
        const typeIcon = this.getTypeIcon(content.type);
        const isCached = content.cached;
        const realCacheSize = isCached ? (content.cachedSize || 0) : 0;
        const sizeText = formatSize(realCacheSize);
        const sizeAndStatus = isCached
          ? `<span style="color: #10b981; font-weight: 600;">${sizeText}</span> <span style="color: #10b981;">✓</span>`
          : `<span style="color: rgba(255,255,255,0.4);">-</span> <span style="color: #ef4444;">✗</span>`;

        return `
          <div class="content-item" style="display: flex; justify-content: space-between; align-items: center; padding: 0.3rem 0.5rem;">
            <span style="color: rgba(255,255,255,0.9); font-size: 0.8rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; min-width: 0;">${typeIcon} ${content.name}</span>
            <span style="flex-shrink: 0; margin-left: 0.5rem; font-size: 0.8rem;">${sizeAndStatus}</span>
          </div>
        `;
      };

      // Build section HTML
      const buildSection = (title: string, icon: string, items: any[]) => {
        if (items.length === 0) return '';
        return `
          <div style="margin-bottom: 0.5rem;">
            <div style="color: rgba(255,255,255,0.6); font-size: 0.75rem; font-weight: 600; padding: 0.3rem 0.5rem; background: rgba(255,255,255,0.05); border-radius: 4px; margin-bottom: 0.25rem;">
              ${icon} ${title} (${items.length})
            </div>
            ${items.map(buildContentItem).join('')}
          </div>
        `;
      };

      let html = '';

      // ========================================================================
      // ACTIVE SCHEDULE INFO - Show when override mode is active
      // ========================================================================
      if (storage.activeSchedule) {
        const schedule = storage.activeSchedule;
        const isOverride = schedule.mode === 'override';
        const scheduleIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 14h.01"/><path d="M8 18h.01"/><path d="M12 18h.01"/></svg>`;

        const modeColor = isOverride ? '#f59e0b' : '#10b981';
        const modeText = isOverride ? 'OVERRIDE' : 'ROTATE';
        const modeDesc = isOverride
          ? 'Only playing scheduled playlist content'
          : 'Playing all content (merged)';

        html += `
          <div style="margin-bottom: 0.75rem; padding: 0.5rem; background: linear-gradient(135deg, rgba(245,158,11,0.15) 0%, rgba(245,158,11,0.05) 100%); border: 1px solid rgba(245,158,11,0.3); border-radius: 8px;">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.35rem;">
              <span style="color: ${modeColor};">${scheduleIcon}</span>
              <span style="color: white; font-weight: 600; font-size: 0.85rem;">Active Schedule</span>
              <span style="background: ${modeColor}; color: #000; padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.65rem; font-weight: 700;">${modeText}</span>
            </div>
            <div style="color: rgba(255,255,255,0.9); font-size: 0.8rem; margin-bottom: 0.25rem;">
              <strong>${schedule.name}</strong>${schedule.playlistName ? ` → ${schedule.playlistName}` : ''}
            </div>
            <div style="color: rgba(255,255,255,0.5); font-size: 0.7rem;">
              ⏰ ${schedule.startTime} - ${schedule.endTime} | ${modeDesc}
            </div>
          </div>
        `;
      }

      html += buildSection('Direct', this.getSectionIcon('direct'), directContent);
      html += buildSection('Tag', this.getSectionIcon('tag'), tagContent);
      html += buildSection('Playlist', this.getSectionIcon('playlist'), playlistContent);

      listEl.innerHTML = html || '<p style="color: rgba(255,255,255,0.4); text-align: center; padding: 0.5rem; font-size: 0.8rem;">No content assigned</p>';
    } else if (listEl) {
      listEl.innerHTML = '<p style="color: rgba(255,255,255,0.4); text-align: center; padding: 0.5rem; font-size: 0.8rem;">No content assigned</p>';
    }
  }

  /**
   * Populate Debug tab
   */
  private populateDebugTab(): void {
    if (!this.deviceInfo) return;

    const { device, network, system, performance, playbackStats } = this.deviceInfo;

    // Network Details
    this.setText('debug-client-ip', network.clientIP || 'Not detected');
    this.setText('debug-public-ip', network.publicIP || 'Detecting...');
    this.setText('debug-connection-type', network.connectionType);
    this.setText('debug-speed', network.downlinkSpeed || 'N/A');

    // System Info (simplified - cores/memory/webgl moved to Capabilities)
    this.setText('debug-platform', system.platform);
    this.setText('debug-browser', `${system.browser.name} ${system.browser.version}`);
    this.setText('debug-resolution', `${system.screen.width}x${system.screen.height}`);
    this.setText('debug-rotation', `${device.rotation}°`);
    this.setText('debug-sw', system.serviceWorkerStatus);

    // Performance - Basic
    this.setText('debug-uptime', formatUptime(performance.uptime));
    this.setText('debug-fps', `${performance.fps} FPS`);
    this.setText('debug-load-time', `${performance.loadTime}ms`);

    if (performance.memory) {
      this.setText('debug-perf-memory', `${performance.memory.used.toFixed(1)} MB / ${performance.memory.limit.toFixed(1)} MB`);
    } else {
      this.setText('debug-perf-memory', 'N/A');
    }

    // Performance - Advanced (Phase 4)
    this.setHtml('debug-cpu-pressure', this.formatCpuPressure(performance.cpuPressure));
    this.setText('debug-long-tasks', `${performance.longTasksCount}`);
    this.setText('debug-ttfb', performance.ttfbMs !== null ? `${performance.ttfbMs}ms` : 'N/A');

    // Playback Stats (Phase 3: Behavioral Metrics)
    this.setText('debug-ttfp', playbackStats.timeToFirstPlaybackMs !== null
      ? `${playbackStats.timeToFirstPlaybackMs.toFixed(0)}ms`
      : 'N/A');
    this.setText('debug-content-plays', `${playbackStats.contentPlayCount}`);
    this.setText('debug-stalls', `${playbackStats.playbackStallsCount}`);
    this.setText('debug-buffers', `${playbackStats.bufferUnderrunsCount}`);
    this.setText('debug-quality-switches', `${playbackStats.qualitySwitchesCount}`);
    this.setText('debug-load-failures', `${playbackStats.contentLoadFailuresCount}`);
    this.setHtml('debug-error-rate', this.formatErrorRate(playbackStats.errorRatePercent));

    // Device Capabilities
    this.populateDeviceCapabilities();
  }

  /**
   * Format CPU pressure with color coding
   */
  private formatCpuPressure(pressure: string | null): string {
    if (!pressure) return 'N/A';

    const colors: Record<string, string> = {
      'nominal': '#10b981', // green
      'fair': '#f59e0b',    // amber
      'serious': '#f97316', // orange
      'critical': '#ef4444', // red
    };

    const color = colors[pressure] || 'white';
    return `<span style="color: ${color}; font-weight: 600;">${pressure.toUpperCase()}</span>`;
  }

  /**
   * Format error rate with color coding
   */
  private formatErrorRate(rate: number): string {
    let color = '#10b981'; // green - 0%
    if (rate > 0) color = '#f59e0b'; // amber - any error
    if (rate > 5) color = '#ef4444'; // red - significant errors

    return `<span style="color: ${color}; font-weight: 600;">${rate.toFixed(1)}%</span>`;
  }

  /**
   * Format FPS with color coding
   */
  private formatFps(fps: number): string {
    let color = '#10b981'; // green - good (>= 30)
    if (fps < 30) color = '#f59e0b'; // amber - warning (15-29)
    if (fps < 15) color = '#ef4444'; // red - bad (< 15)

    return `<span style="color: ${color}; font-weight: 600;">${fps} FPS</span>`;
  }

  /**
   * Format Long Tasks count with color coding
   */
  private formatLongTasks(count: number): string {
    let color = '#10b981'; // green - good (0-5)
    if (count > 5) color = '#f59e0b'; // amber - warning (6-20)
    if (count > 20) color = '#ef4444'; // red - bad (> 20)

    return `<span style="color: ${color}; font-weight: 600;">${count}</span>`;
  }

  /**
   * Format count with color coding (0 = green, >0 = warning/error)
   */
  private formatCount(count: number): string {
    let color = '#10b981'; // green - 0
    if (count > 0) color = '#f59e0b'; // amber - some issues
    if (count > 5) color = '#ef4444'; // red - many issues

    return `<span style="color: ${color}; font-weight: 600;">${count}</span>`;
  }

  /**
   * Populate Device Capabilities section
   */
  private populateDeviceCapabilities(): void {
    const capabilitiesReporter = getPlayerCapabilitiesReporter();
    const capabilities = capabilitiesReporter?.getCapabilities?.();

    // Video Codecs - formatted with badges
    const videoCodecsEl = document.getElementById('debug-video-codecs');
    if (videoCodecsEl) {
      if (capabilities) {
        videoCodecsEl.innerHTML = this.formatCodecBadges({
          'H.264': capabilities.codecH264,
          'H.265': capabilities.codecH265,
          'VP9': capabilities.codecVP9,
          'AV1': capabilities.codecAV1,
        });
      } else {
        // Fallback: detect codecs directly
        const detectedVideoCodecs = detectVideoCodecs();
        videoCodecsEl.innerHTML = this.formatCodecBadges({
          'H.264': detectedVideoCodecs.h264,
          'H.265': detectedVideoCodecs.h265,
          'VP9': detectedVideoCodecs.vp9,
          'AV1': detectedVideoCodecs.av1,
        });
      }
    }

    // Audio Codecs - formatted with badges
    const audioCodecsEl = document.getElementById('debug-audio-codecs');
    if (audioCodecsEl) {
      if (capabilities) {
        audioCodecsEl.innerHTML = this.formatCodecBadges({
          'AAC': capabilities.codecAAC,
          'Opus': capabilities.codecOpus,
        });
      } else {
        // Fallback: detect codecs directly
        const detectedAudioCodecs = detectAudioCodecs();
        audioCodecsEl.innerHTML = this.formatCodecBadges({
          'AAC': detectedAudioCodecs.aac,
          'Opus': detectedAudioCodecs.opus,
        });
      }
    }

    // Hardware
    const hardwareEl = document.getElementById('debug-hardware');
    if (hardwareEl) {
      const cores = capabilities?.hardwareConcurrency || navigator.hardwareConcurrency || 'N/A';
      const memory = capabilities?.deviceMemoryGB || (navigator as any).deviceMemory || null;
      const memoryStr = memory ? `${memory} GB` : 'N/A';
      hardwareEl.textContent = `${cores} cores • ${memoryStr} RAM`;
    }

    // Display
    const displayEl = document.getElementById('debug-display');
    if (displayEl) {
      const width = capabilities?.screenWidth || window.screen.width;
      const height = capabilities?.screenHeight || window.screen.height;
      const refreshRate = capabilities?.displayRefreshRate || 60;
      displayEl.textContent = `${width}x${height} @ ${refreshRate}Hz`;
    }

    // WebGL Details
    const webglEl = document.getElementById('debug-webgl-details');
    if (webglEl) {
      if (capabilities?.webglVersion) {
        const version = capabilities.webglVersion;
        const renderer = capabilities.webglRenderer || 'Unknown';
        // Truncate long renderer strings
        const shortRenderer = renderer.length > 30 ? renderer.substring(0, 27) + '...' : renderer;
        webglEl.innerHTML = `<span style="color: #10b981;">${version}</span> <span style="color: rgba(255,255,255,0.5); font-size: 0.7rem;">(${shortRenderer})</span>`;
      } else {
        // Fallback: detect WebGL
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
        if (gl) {
          const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
          const renderer = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'Unknown';
          const version = canvas.getContext('webgl2') ? '2.0' : '1.0';
          const shortRenderer = renderer.length > 30 ? renderer.substring(0, 27) + '...' : renderer;
          webglEl.innerHTML = `<span style="color: #10b981;">${version}</span> <span style="color: rgba(255,255,255,0.5); font-size: 0.7rem;">(${shortRenderer})</span>`;
        } else {
          webglEl.innerHTML = '<span style="color: #ef4444;">Not Supported</span>';
        }
      }
    }
  }

  /**
   * Format codec support as HTML badges
   */
  private formatCodecBadges(codecs: Record<string, boolean>): string {
    return Object.entries(codecs)
      .map(([name, supported]) => {
        const className = supported ? 'supported' : 'not-supported';
        const icon = supported ? '✓' : '✗';
        return `<span class="codec-badge ${className}">${name} ${icon}</span>`;
      })
      .join('');
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
   * Helper: Set HTML content (for formatted/colored values)
   */
  private setHtml(id: string, html: string): void {
    const el = document.getElementById(id);
    if (el) {
      el.innerHTML = html;
    }
  }

  /**
   * Helper: Get content type icon (SVG)
   */
  private getTypeIcon(type: string): string {
    const size = 14;
    const stroke = 'currentColor';

    const icons: Record<string, string> = {
      video: `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.87a.5.5 0 0 0-.752-.432L16 10.5"/><rect x="2" y="6" width="14" height="12" rx="2"/></svg>`,
      image: `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>`,
      audio: `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>`,
      url: `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>`,
      widget: `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>`,
    };

    // Default file icon
    const defaultIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>`;

    return icons[type] || defaultIcon;
  }

  /**
   * Helper: Get section icon (SVG) for content groups
   */
  private getSectionIcon(section: 'direct' | 'tag' | 'playlist'): string {
    const size = 12;
    const stroke = 'currentColor';

    const icons: Record<string, string> = {
      direct: `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 17v5"/><path d="M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z"/></svg>`,
      tag: `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z"/><circle cx="7.5" cy="7.5" r=".5" fill="currentColor"/></svg>`,
      playlist: `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15V6"/><path d="M18.5 18a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z"/><path d="M12 12H3"/><path d="M16 6H3"/><path d="M12 18H3"/></svg>`,
    };

    return icons[section] || '';
  }

  /**
   * Helper: Get cache type icon (SVG)
   */
  private getCacheIcon(type: 'video' | 'image' | 'audio'): string {
    const size = 12;
    const stroke = 'rgba(255, 255, 255, 0.6)';
    const style = 'vertical-align: middle; margin-right: 2px;';

    const icons: Record<string, string> = {
      video: `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="${style}"><path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.87a.5.5 0 0 0-.752-.432L16 10.5"/><rect x="2" y="6" width="14" height="12" rx="2"/></svg>`,
      image: `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="${style}"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>`,
      audio: `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="${style}"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>`,
    };

    return icons[type] || '';
  }

  /**
   * Helper: Get WiFi icon SVG based on connection status
   */
  private getWifiIcon(isOnline: boolean): string {
    if (isOnline) {
      // WiFi connected icon (green)
      return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 20h.01"/>
        <path d="M2 8.82a15 15 0 0 1 20 0"/>
        <path d="M5 12.859a10 10 0 0 1 14 0"/>
        <path d="M8.5 16.429a5 5 0 0 1 7 0"/>
      </svg>`;
    } else {
      // WiFi disconnected icon (red with slash)
      return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 20h.01"/>
        <path d="M8.5 16.429a5 5 0 0 1 7 0"/>
        <path d="M5 12.859a10 10 0 0 1 5.17-2.69"/>
        <path d="M13.83 10.17A10 10 0 0 1 19 12.86"/>
        <path d="M2 8.82a15 15 0 0 1 4.17-2.65"/>
        <path d="M10.66 5a15 15 0 0 1 11.34 3.82"/>
        <line x1="2" y1="2" x2="22" y2="22"/>
      </svg>`;
    }
  }

  /**
   * Helper: Get Database icon SVG based on connection status
   */
  private getDatabaseIcon(isConnected: boolean): string {
    if (isConnected) {
      // Database connected icon (green)
      return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <ellipse cx="12" cy="5" rx="9" ry="3"/>
        <path d="M3 5v14a9 3 0 0 0 18 0V5"/>
        <path d="M3 12a9 3 0 0 0 18 0"/>
      </svg>`;
    } else {
      // Database disconnected icon (red with X)
      return `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <ellipse cx="12" cy="5" rx="9" ry="3"/>
        <path d="M3 5v14a9 3 0 0 0 18 0V5"/>
        <path d="M3 12a9 3 0 0 0 18 0"/>
        <line x1="8" y1="15" x2="16" y2="23" stroke="#ef4444" stroke-width="2.5"/>
        <line x1="16" y1="15" x2="8" y2="23" stroke="#ef4444" stroke-width="2.5"/>
      </svg>`;
    }
  }
}

// Export singleton instance
export const DeviceInfoPopup = new DeviceInfoPopupClass();

// Make available globally for tab switching and section toggling
if (typeof window !== 'undefined') {
  (window as any).DeviceInfoPopup = DeviceInfoPopup;
}
