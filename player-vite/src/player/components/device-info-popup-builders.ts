/**
 * Device Info Popup - HTML Builders
 * Contains all HTML generation methods for device info tabs
 */

/**
 * Build complete HTML content structure with tabs
 */
export function buildPopupContent(): string {
  return `
    ${buildStyles()}
    <div class="device-info-container">
      <!-- Tab navigation -->
      <div class="tab-nav">
        <button class="tab-btn active" data-tab="device">
          <span class="tab-icon">📱</span> Device
        </button>
        <button class="tab-btn" data-tab="network">
          <span class="tab-icon">🌐</span> Network
        </button>
        <button class="tab-btn" data-tab="system">
          <span class="tab-icon">⚙️</span> System
        </button>
        <button class="tab-btn" data-tab="storage">
          <span class="tab-icon">💾</span> Storage
        </button>
        <button class="tab-btn" data-tab="backend">
          <span class="tab-icon">🔗</span> Backend
        </button>
        <button class="tab-btn" data-tab="audio">
          <span class="tab-icon">🔊</span> Audio
        </button>
        <button class="tab-btn" data-tab="performance">
          <span class="tab-icon">⚡</span> Performance
        </button>
      </div>

      <!-- Tab content panels -->
      <div class="tab-content">
        <div class="tab-panel active" id="device-tab">${buildDeviceTab()}</div>
        <div class="tab-panel" id="network-tab">${buildNetworkTab()}</div>
        <div class="tab-panel" id="system-tab">${buildSystemTab()}</div>
        <div class="tab-panel" id="storage-tab">${buildStorageTab()}</div>
        <div class="tab-panel" id="backend-tab">${buildBackendTab()}</div>
        <div class="tab-panel" id="audio-tab">${buildAudioTab()}</div>
        <div class="tab-panel" id="performance-tab">${buildPerformanceTab()}</div>
      </div>
    </div>
  `;
}

/**
 * Build Device tab HTML
 */
export function buildDeviceTab(): string {
  return `
    <div class="info-section">
      <h3>Device Information</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">Device ID:</span>
          <span class="info-value" id="device-id">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Device Code:</span>
          <span class="info-value" id="device-code">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Device Name:</span>
          <span class="info-value" id="device-name">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Status:</span>
          <span class="info-value" id="device-status">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Organization ID:</span>
          <span class="info-value" id="organization-id">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Room Number:</span>
          <span class="info-value" id="room-number">Loading...</span>
        </div>
      </div>
    </div>

    <div class="info-section">
      <h3>Platform Information</h3>
      <div class="info-grid">
        <div class="info-item full-width">
          <span class="info-label">User Agent:</span>
          <span class="info-value" id="user-agent">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Platform:</span>
          <span class="info-value" id="platform">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Language:</span>
          <span class="info-value" id="language">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Screen Resolution:</span>
          <span class="info-value" id="screen-resolution">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Viewport Size:</span>
          <span class="info-value" id="viewport-size">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Color Depth:</span>
          <span class="info-value" id="color-depth">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Pixel Ratio:</span>
          <span class="info-value" id="pixel-ratio">Loading...</span>
        </div>
      </div>
    </div>
  `;
}

/**
 * Build Network tab HTML
 */
export function buildNetworkTab(): string {
  return `
    <div class="info-section">
      <h3>Network Status</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">Status:</span>
          <span class="info-value" id="network-status">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Type:</span>
          <span class="info-value" id="connection-type">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Effective Type:</span>
          <span class="info-value" id="effective-type">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Downlink:</span>
          <span class="info-value" id="downlink">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">RTT:</span>
          <span class="info-value" id="rtt">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Save Data:</span>
          <span class="info-value" id="save-data">Loading...</span>
        </div>
      </div>
    </div>
  `;
}

/**
 * Build System tab HTML
 */
export function buildSystemTab(): string {
  return `
    <div class="info-section">
      <h3>System Information</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">CPU Cores:</span>
          <span class="info-value" id="cpu-cores">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Memory (Used):</span>
          <span class="info-value" id="memory-used">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Memory (Total):</span>
          <span class="info-value" id="memory-total">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Memory (Limit):</span>
          <span class="info-value" id="memory-limit">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Uptime:</span>
          <span class="info-value" id="uptime">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Timezone:</span>
          <span class="info-value" id="timezone">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Touch Support:</span>
          <span class="info-value" id="touch-support">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Cookies Enabled:</span>
          <span class="info-value" id="cookies-enabled">Loading...</span>
        </div>
      </div>
    </div>
  `;
}

/**
 * Build Storage tab HTML
 */
export function buildStorageTab(): string {
  return `
    <div class="info-section">
      <h3>Storage Quota</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">Usage:</span>
          <span class="info-value" id="storage-usage">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Quota:</span>
          <span class="info-value" id="storage-quota">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Percent Used:</span>
          <span class="info-value" id="storage-percent">Loading...</span>
        </div>
      </div>
    </div>

    <div class="info-section">
      <h3>localStorage</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">Keys Count:</span>
          <span class="info-value" id="localstorage-keys">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Size (Estimated):</span>
          <span class="info-value" id="localstorage-size">Loading...</span>
        </div>
      </div>
    </div>

    <div class="info-section">
      <h3>IndexedDB</h3>
      <div class="info-grid">
        <div class="info-item full-width">
          <span class="info-label">Databases:</span>
          <span class="info-value" id="indexeddb-databases">Loading...</span>
        </div>
      </div>
    </div>

    <div class="info-section">
      <h3>Media Cache Statistics</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">Total Items:</span>
          <span class="info-value" id="cache-total-items">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Total Size:</span>
          <span class="info-value" id="cache-total-size">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Oldest Cache:</span>
          <span class="info-value" id="cache-oldest">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Newest Cache:</span>
          <span class="info-value" id="cache-newest">Loading...</span>
        </div>
      </div>
    </div>
  `;
}

/**
 * Build Backend tab HTML
 */
export function buildBackendTab(): string {
  return `
    <div class="info-section">
      <h3>Backend Connection</h3>
      <div class="info-grid">
        <div class="info-item full-width">
          <span class="info-label">API Base URL:</span>
          <span class="info-value" id="api-base-url">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Connection Status:</span>
          <span class="info-value" id="backend-status">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Latency:</span>
          <span class="info-value" id="backend-latency">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Last Heartbeat:</span>
          <span class="info-value" id="last-heartbeat">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">WebSocket:</span>
          <span class="info-value" id="websocket-status">Loading...</span>
        </div>
      </div>
    </div>
  `;
}

/**
 * Build Audio tab HTML
 */
export function buildAudioTab(): string {
  return `
    <div class="info-section">
      <h3>Audio Capabilities</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">MP3 Support:</span>
          <span class="info-value" id="audio-mp3">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">AAC Support:</span>
          <span class="info-value" id="audio-aac">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">WAV Support:</span>
          <span class="info-value" id="audio-wav">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">OGG Support:</span>
          <span class="info-value" id="audio-ogg">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">FLAC Support:</span>
          <span class="info-value" id="audio-flac">Loading...</span>
        </div>
      </div>
    </div>

    <div class="info-section">
      <h3>Video Capabilities</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">MP4/H.264:</span>
          <span class="info-value" id="video-mp4">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">WebM:</span>
          <span class="info-value" id="video-webm">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">OGG:</span>
          <span class="info-value" id="video-ogg">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">HLS:</span>
          <span class="info-value" id="video-hls">Loading...</span>
        </div>
      </div>
    </div>
  `;
}

/**
 * Build Performance tab HTML
 */
export function buildPerformanceTab(): string {
  return `
    <div class="info-section">
      <h3>Performance Metrics</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">DOM Load Time:</span>
          <span class="info-value" id="dom-load-time">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Page Load Time:</span>
          <span class="info-value" id="page-load-time">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">FPS (avg):</span>
          <span class="info-value" id="fps-avg">Loading...</span>
        </div>
        <div class="info-item">
          <span class="info-label">Frame Budget:</span>
          <span class="info-value" id="frame-budget">Loading...</span>
        </div>
      </div>
    </div>
  `;
}

/**
 * Build CSS styles
 */
export function buildStyles(): string {
  return `
    <style>
      .device-info-container {
        padding: 0;
      }

      .tab-nav {
        display: flex;
        gap: 8px;
        margin-bottom: 20px;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        flex-wrap: wrap;
      }

      .tab-btn {
        padding: 12px 20px;
        background: rgba(255, 255, 255, 0.05);
        border: none;
        border-bottom: 3px solid transparent;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.7);
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 6px;
        border-radius: 8px 8px 0 0;
      }

      .tab-btn:hover {
        background: rgba(255, 255, 255, 0.1);
        color: white;
      }

      .tab-btn.active {
        background: rgba(59, 130, 246, 0.1);
        color: white;
        border-bottom-color: #3b82f6;
      }

      .tab-icon {
        font-size: 16px;
      }

      .tab-panel {
        display: none;
        animation: fadeIn 0.3s;
      }

      .tab-panel.active {
        display: block;
      }

      @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }

      .info-section {
        margin-bottom: 24px;
      }

      .info-section h3 {
        margin: 0 0 12px 0;
        font-size: 16px;
        font-weight: 600;
        color: white;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 8px;
      }

      .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 12px;
      }

      .info-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }

      .info-item.full-width {
        grid-column: 1 / -1;
      }

      .info-label {
        font-size: 12px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.5);
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      .info-value {
        font-size: 14px;
        color: white;
        word-break: break-word;
      }

      .status-online {
        color: #10b981;
        font-weight: 600;
      }

      .status-offline {
        color: #ef4444;
        font-weight: 600;
      }

      @media (max-width: 768px) {
        .info-grid {
          grid-template-columns: 1fr;
        }

        .tab-nav {
          overflow-x: auto;
          flex-wrap: nowrap;
        }

        .tab-btn {
          flex-shrink: 0;
        }
      }
    </style>
  `;
}
