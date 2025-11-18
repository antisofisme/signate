/**
 * Connection Log Popup
 * Shows connection activity logs with tab navigation and table format
 */

import { SharedLogger } from '@shared/logger';
import { SharedModal } from '@shared/ui';
import { ConnectionLogger } from '@shared/services/connection-logger';
import { NetworkSpeedTest } from '@shared/services/network-speed-test';
import type { ConnectionLogEntry } from '@shared/storage/connection-log-storage';

class ConnectionLogPopupClass {
  private activeTab: 'all' | 'network' | 'server' | 'speed_test' = 'all';
  private logs: ConnectionLogEntry[] = [];

  /**
   * Initialize popup and attach event handlers
   */
  init(): void {
    requestAnimationFrame(() => {
      this.attachStatusIconHandlers();
      SharedLogger.log('[ConnectionLogPopup] ✅ Initialized');
    });
  }

  /**
   * Attach click handlers to network and server status icons
   */
  private attachStatusIconHandlers(): void {
    const networkStatus = document.getElementById('network-status');
    const serverStatus = document.getElementById('server-status');

    if (networkStatus) {
      networkStatus.style.cursor = 'pointer';
      networkStatus.addEventListener('click', () => {
        SharedLogger.log('[ConnectionLogPopup] Network icon clicked!');
        this.show('network');
      });
    }

    if (serverStatus) {
      serverStatus.style.cursor = 'pointer';
      serverStatus.addEventListener('click', () => {
        SharedLogger.log('[ConnectionLogPopup] Server icon clicked!');
        this.show('server');
      });
    }
  }

  /**
   * Show popup with optional initial tab
   */
  async show(initialTab?: typeof this.activeTab): Promise<void> {
    if (initialTab) {
      this.activeTab = initialTab;
    }

    // Load logs
    await this.loadLogs();

    // Build and show modal
    const content = this.buildContent();

    SharedModal.showCustom({
      title: 'Connection Activity Log',
      content,
      width: '95%',
      maxWidth: '1200px',
      showCloseButton: true,
      className: 'connection-log-modal'
    });

    // Attach handlers and render
    setTimeout(() => {
      this.attachTabHandlers();
      this.attachActionHandlers();
      this.renderActiveTab();
    }, 100);

    SharedLogger.log('[ConnectionLogPopup] Popup shown');
  }

  /**
   * Build HTML content
   */
  private buildContent(): string {
    const networkCount = this.logs.filter(l => l.eventType === 'network').length;
    const serverCount = this.logs.filter(l => l.eventType === 'server').length;
    const speedTestCount = this.logs.filter(l => l.eventType === 'speed_test').length;

    return `
      <div class="log-viewer">
        <!-- Header with Tabs and Actions -->
        <div class="log-header">
          <!-- Tab Navigation -->
          <div class="tab-nav">
            <button class="tab-btn ${this.activeTab === 'all' ? 'active' : ''}" data-tab="all">
              All (${this.logs.length})
            </button>
            <button class="tab-btn ${this.activeTab === 'network' ? 'active' : ''}" data-tab="network">
              Network (${networkCount})
            </button>
            <button class="tab-btn ${this.activeTab === 'server' ? 'active' : ''}" data-tab="server">
              Server (${serverCount})
            </button>
            <button class="tab-btn ${this.activeTab === 'speed_test' ? 'active' : ''}" data-tab="speed_test">
              Speed Test (${speedTestCount})
            </button>
          </div>

          <!-- Action Buttons -->
          <div class="log-actions">
            <button id="refresh-logs-btn" class="action-btn" title="Refresh">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
              </svg>
            </button>
            <button id="speed-test-btn" class="action-btn" title="Run Speed Test">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2v10M12 12l-3-3M12 12l3-3"/>
                <path d="M4.93 4.93l4.24 4.24M7.17 7.17l2.12-2.12M19.07 4.93l-4.24 4.24M16.83 7.17l-2.12-2.12"/>
                <circle cx="12" cy="12" r="10"/>
              </svg>
            </button>
            <button id="export-logs-btn" class="action-btn" title="Export CSV">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Table Container with fixed height -->
        <div id="table-container" class="table-container">
          <!-- Table will be rendered here -->
        </div>

        ${this.buildStyles()}
      </div>
    `;
  }

  /**
   * Build CSS styles
   */
  private buildStyles(): string {
    return `
      <style>
        .log-viewer {
          display: flex;
          flex-direction: column;
          height: 600px;
          max-height: 80vh;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        /* Header - Fixed at top */
        .log-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1.5rem 1.5rem 0 1.5rem;
          border-bottom: 2px solid rgba(255, 255, 255, 0.1);
          flex-shrink: 0;
        }

        /* Tab Navigation */
        .tab-nav {
          display: flex;
          gap: 0.5rem;
          overflow-x: auto;
          overflow-y: hidden;
          -webkit-overflow-scrolling: touch;
          scrollbar-width: thin;
        }
        .tab-btn {
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
          border-radius: 8px 8px 0 0;
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

        /* Action Buttons */
        .log-actions {
          display: flex;
          gap: 0.5rem;
          flex-shrink: 0;
        }
        .action-btn {
          padding: 0.5rem;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          color: rgba(255, 255, 255, 0.7);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s ease;
        }
        .action-btn:hover {
          background: rgba(255, 255, 255, 0.1);
          color: white;
          border-color: rgba(255, 255, 255, 0.2);
        }
        .action-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        /* Table Container - Scrollable area */
        .table-container {
          flex: 1;
          overflow-y: auto;
          overflow-x: auto;
          padding: 0 1.5rem 1.5rem 1.5rem;
          -webkit-overflow-scrolling: touch;
        }

        /* Table */
        .log-table {
          width: 100%;
          border-collapse: collapse;
        }
        .log-table thead {
          position: sticky;
          top: 0;
          z-index: 10;
          background: linear-gradient(to bottom,
            rgba(30, 41, 59, 1) 0%,
            rgba(30, 41, 59, 0.98) 50%,
            rgba(30, 41, 59, 0.95) 100%
          );
          backdrop-filter: blur(8px);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }
        .log-table th {
          padding: 0.5rem 1rem;
          text-align: left;
          font-weight: 600;
          font-size: 0.85rem;
          color: rgba(255, 255, 255, 0.9);
          border-bottom: 2px solid rgba(255, 255, 255, 0.1);
          white-space: nowrap;
        }
        .log-table tbody tr {
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          transition: all 0.2s ease;
        }
        .log-table tbody tr:hover {
          background: rgba(255, 255, 255, 0.05);
        }
        .log-table td {
          padding: 0.5rem 1rem;
          font-size: 0.875rem;
          color: rgba(255, 255, 255, 0.85);
          white-space: nowrap;
        }
        .log-table td.timestamp {
          color: rgba(255, 255, 255, 0.6);
          font-family: 'Consolas', 'Monaco', monospace;
          font-size: 0.8rem;
        }

        /* Status Badge */
        .status-badge {
          display: inline-block;
          padding: 0.25rem 0.75rem;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .status-online {
          background: rgba(16, 185, 129, 0.15);
          color: #10b981;
          border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .status-offline {
          background: rgba(239, 68, 68, 0.15);
          color: #ef4444;
          border: 1px solid rgba(239, 68, 68, 0.3);
        }
        .status-connected {
          background: rgba(59, 130, 246, 0.15);
          color: #3b82f6;
          border: 1px solid rgba(59, 130, 246, 0.3);
        }
        .status-disconnected {
          background: rgba(239, 68, 68, 0.15);
          color: #ef4444;
          border: 1px solid rgba(239, 68, 68, 0.3);
        }
        .status-tested {
          background: rgba(139, 92, 246, 0.15);
          color: #8b5cf6;
          border: 1px solid rgba(139, 92, 246, 0.3);
        }

        /* Empty State */
        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 4rem 2rem;
          color: rgba(255, 255, 255, 0.5);
        }
        .empty-state-text {
          font-size: 1rem;
          margin-top: 1rem;
        }

        /* Latency Color Coding */
        .latency-good {
          color: #10b981;
          font-weight: 600;
        }
        .latency-ok {
          color: #f59e0b;
          font-weight: 600;
        }
        .latency-slow {
          color: #ef4444;
          font-weight: 600;
        }

        /* Speed Color Coding */
        .speed-good {
          color: #3b82f6;
          font-weight: 600;
        }

        /* Quality Score Color Coding */
        .quality-excellent {
          color: #10b981;
          font-weight: 700;
        }
        .quality-good {
          color: #3b82f6;
          font-weight: 600;
        }
        .quality-fair {
          color: #f59e0b;
          font-weight: 600;
        }
        .quality-poor {
          color: #ef4444;
          font-weight: 600;
        }

        /* Custom Scrollbar */
        .table-container::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }
        .table-container::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 4px;
        }
        .table-container::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 4px;
        }
        .table-container::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }

        /* Tab scrollbar (horizontal) */
        .tab-nav::-webkit-scrollbar {
          height: 6px;
        }
        .tab-nav::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 3px;
        }
        .tab-nav::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 3px;
        }
        .tab-nav::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      </style>
    `;
  }

  /**
   * Attach tab click handlers
   */
  private attachTabHandlers(): void {
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = (btn as HTMLElement).dataset.tab as typeof this.activeTab;
        this.switchTab(tab);
      });
    });
  }

  /**
   * Attach action button handlers
   */
  private attachActionHandlers(): void {
    const refreshBtn = document.getElementById('refresh-logs-btn');
    refreshBtn?.addEventListener('click', () => {
      this.loadLogs().then(() => {
        this.renderActiveTab();
        SharedLogger.log('[ConnectionLogPopup] Logs refreshed');
      });
    });

    const speedTestBtn = document.getElementById('speed-test-btn') as HTMLButtonElement;
    speedTestBtn?.addEventListener('click', async () => {
      SharedLogger.log('[ConnectionLogPopup] Manual speed test triggered');
      speedTestBtn.disabled = true;
      speedTestBtn.style.opacity = '0.5';

      try {
        await NetworkSpeedTest.triggerManualTest();
        await this.loadLogs();
        this.renderActiveTab();
        SharedLogger.log('[ConnectionLogPopup] Speed test completed and logs refreshed');
      } catch (error) {
        SharedLogger.error('[ConnectionLogPopup] Speed test failed:', error);
      } finally {
        speedTestBtn.disabled = false;
        speedTestBtn.style.opacity = '1';
      }
    });

    const exportBtn = document.getElementById('export-logs-btn');
    exportBtn?.addEventListener('click', () => this.exportLogs());
  }

  /**
   * Switch active tab
   */
  private switchTab(tab: typeof this.activeTab): void {
    this.activeTab = tab;

    // Update tab button states
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.classList.toggle('active', (btn as HTMLElement).dataset.tab === tab);
    });

    // Re-render table
    this.renderActiveTab();
  }

  /**
   * Load logs from storage
   */
  private async loadLogs(): Promise<void> {
    try {
      this.logs = await ConnectionLogger.getLogs(100);
      SharedLogger.log(`[ConnectionLogPopup] Loaded ${this.logs.length} logs`);
    } catch (error) {
      SharedLogger.error('[ConnectionLogPopup] Failed to load logs:', error);
      this.logs = [];
    }
  }

  /**
   * Render active tab content
   */
  private renderActiveTab(): void {
    const container = document.getElementById('table-container');
    if (!container) return;

    // Filter logs by active tab
    const filteredLogs = this.activeTab === 'all'
      ? this.logs
      : this.logs.filter(l => l.eventType === this.activeTab);

    // Sort by timestamp (newest first)
    const sortedLogs = filteredLogs.sort((a, b) => b.timestamp - a.timestamp);

    // Render appropriate table
    if (sortedLogs.length === 0) {
      container.innerHTML = this.renderEmptyState();
      return;
    }

    switch (this.activeTab) {
      case 'all':
        container.innerHTML = this.renderAllLogsTable(sortedLogs);
        break;
      case 'network':
        container.innerHTML = this.renderNetworkTable(sortedLogs);
        break;
      case 'server':
        container.innerHTML = this.renderServerTable(sortedLogs);
        break;
      case 'speed_test':
        container.innerHTML = this.renderSpeedTestTable(sortedLogs);
        break;
    }
  }

  /**
   * Render empty state
   */
  private renderEmptyState(): string {
    return `
      <div class="empty-state">
        <div class="empty-state-text">No logs</div>
      </div>
    `;
  }

  /**
   * Render all logs table
   */
  private renderAllLogsTable(logs: ConnectionLogEntry[]): string {
    const rows = logs.map(log => {
      const datetime = this.formatDateTime(log.timestamp);
      const statusBadge = this.formatStatusBadge(log.status);
      const details = this.formatLogDetails(log);

      return `
        <tr>
          <td class="timestamp">${datetime}</td>
          <td>${this.formatEventType(log.eventType)}</td>
          <td>${statusBadge}</td>
          <td>${details}</td>
        </tr>
      `;
    }).join('');

    return `
      <table class="log-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Type</th>
            <th>Status</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    `;
  }

  /**
   * Render network logs table
   */
  private renderNetworkTable(logs: ConnectionLogEntry[]): string {
    // Get last speed test result
    const lastSpeedTest = this.logs
      .filter(l => l.eventType === 'speed_test' && l.downloadSpeedMbps)
      .sort((a, b) => b.timestamp - a.timestamp)[0];

    const rows = logs.map(log => {
      const datetime = this.formatDateTime(log.timestamp);
      const statusBadge = this.formatStatusBadge(log.status);

      // Get network information from metadata or current state
      const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;

      const connectionType = log.metadata?.connectionType || connection?.type || '-';
      const effectiveType = log.metadata?.effectiveType || connection?.effectiveType || '-';
      const rtt = log.metadata?.rtt || connection?.rtt || '-';
      const saveData = log.metadata?.saveData !== undefined ? log.metadata.saveData : (connection?.saveData || false);
      const details = log.metadata?.event || log.errorMessage || '-';

      // Use actual speed test result instead of browser estimate
      const speedTest = lastSpeedTest
        ? `↓${lastSpeedTest.downloadSpeedMbps?.toFixed(1)} / ↑${lastSpeedTest.uploadSpeedMbps?.toFixed(1)} Mbps`
        : '-';

      return `
        <tr>
          <td class="timestamp">${datetime}</td>
          <td>${statusBadge}</td>
          <td>${connectionType}</td>
          <td>${effectiveType}</td>
          <td>${speedTest}</td>
          <td>${typeof rtt === 'number' ? rtt + ' ms' : rtt}</td>
          <td>${saveData ? 'Yes' : 'No'}</td>
          <td>${details}</td>
        </tr>
      `;
    }).join('');

    return `
      <table class="log-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Status</th>
            <th>Type</th>
            <th>Eff. Type</th>
            <th>Speed Test</th>
            <th>RTT</th>
            <th>Save Data</th>
            <th>Event</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    `;
  }

  /**
   * Render server logs table
   */
  private renderServerTable(logs: ConnectionLogEntry[]): string {
    const rows = logs.map(log => {
      const datetime = this.formatDateTime(log.timestamp);
      const statusBadge = this.formatStatusBadge(log.status);
      const latency = log.latencyMs ? `${log.latencyMs}ms` : '-';

      // Extract more info from metadata
      const endpoint = log.metadata?.endpoint || log.metadata?.url || 'health';
      const httpStatus = log.metadata?.statusCode || log.metadata?.httpStatus || '-';
      const responseTime = log.metadata?.responseTime || latency;
      const errorCode = log.errorMessage ? (log.metadata?.errorCode || 'ERROR') : '-';
      const details = log.metadata?.event || log.errorMessage || '-';

      // Color code latency
      let latencyClass = '';
      if (log.latencyMs) {
        if (log.latencyMs < 100) latencyClass = 'latency-good';
        else if (log.latencyMs < 300) latencyClass = 'latency-ok';
        else latencyClass = 'latency-slow';
      }

      return `
        <tr>
          <td class="timestamp">${datetime}</td>
          <td>${statusBadge}</td>
          <td>${endpoint}</td>
          <td>${httpStatus}</td>
          <td class="${latencyClass}">${responseTime}</td>
          <td>${errorCode}</td>
          <td>${details}</td>
        </tr>
      `;
    }).join('');

    return `
      <table class="log-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Status</th>
            <th>Endpoint</th>
            <th>HTTP</th>
            <th>Response Time</th>
            <th>Error Code</th>
            <th>Event</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    `;
  }

  /**
   * Render speed test logs table
   */
  private renderSpeedTestTable(logs: ConnectionLogEntry[]): string {
    const rows = logs.map(log => {
      const datetime = this.formatDateTime(log.timestamp);
      const download = log.downloadSpeedMbps ? `${log.downloadSpeedMbps.toFixed(2)}` : '-';
      const upload = log.uploadSpeedMbps ? `${log.uploadSpeedMbps.toFixed(2)}` : '-';
      const latency = log.latencyMs ? `${log.latencyMs}` : '-';

      // Extract additional info from metadata
      const duration = log.metadata?.testDurationMs
        ? `${(log.metadata.testDurationMs / 1000).toFixed(1)}s`
        : '-';
      const trigger = log.metadata?.trigger || 'auto';

      // Calculate quality score (0-100)
      let quality = '-';
      let qualityClass = '';
      if (log.downloadSpeedMbps && log.uploadSpeedMbps && log.latencyMs) {
        // Score based on: Download (40%), Upload (40%), Latency (20%)
        const dlScore = Math.min(100, (log.downloadSpeedMbps / 100) * 40);
        const ulScore = Math.min(100, (log.uploadSpeedMbps / 100) * 40);
        const latScore = Math.max(0, 20 - (log.latencyMs / 10));
        const totalScore = Math.round(dlScore + ulScore + latScore);

        quality = `${totalScore}`;
        if (totalScore >= 80) qualityClass = 'quality-excellent';
        else if (totalScore >= 60) qualityClass = 'quality-good';
        else if (totalScore >= 40) qualityClass = 'quality-fair';
        else qualityClass = 'quality-poor';
      }

      const statusBadge = log.errorMessage ? this.formatStatusBadge('disconnected') : this.formatStatusBadge('tested');

      return `
        <tr>
          <td class="timestamp">${datetime}</td>
          <td class="speed-good">${download}</td>
          <td class="speed-good">${upload}</td>
          <td class="${latency !== '-' && parseInt(latency) < 100 ? 'latency-good' : (latency !== '-' && parseInt(latency) < 300 ? 'latency-ok' : 'latency-slow')}">${latency}ms</td>
          <td class="${qualityClass}">${quality}</td>
          <td>${duration}</td>
          <td>${trigger}</td>
          <td>${statusBadge}</td>
        </tr>
      `;
    }).join('');

    return `
      <table class="log-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Download (Mbps)</th>
            <th>Upload (Mbps)</th>
            <th>Latency</th>
            <th>Quality</th>
            <th>Duration</th>
            <th>Trigger</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    `;
  }

  /**
   * Format status badge
   */
  private formatStatusBadge(status: string): string {
    const statusMap: Record<string, string> = {
      online: 'online',
      offline: 'offline',
      connected: 'connected',
      disconnected: 'disconnected',
      tested: 'success'
    };

    const text = statusMap[status] || status;
    return `<span class="status-badge status-${status}">${text}</span>`;
  }

  /**
   * Format event type
   */
  private formatEventType(type: string): string {
    const typeMap: Record<string, string> = {
      network: 'Network',
      server: 'Server',
      speed_test: 'Speed Test'
    };
    return typeMap[type] || type;
  }

  /**
   * Format date and time in one line
   */
  private formatDateTime(timestamp: number): string {
    const date = new Date(timestamp);
    const dateStr = date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
    const timeStr = date.toLocaleTimeString('en-GB', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
    return `${dateStr} ${timeStr}`;
  }

  /**
   * Format log details for all logs table
   */
  private formatLogDetails(log: ConnectionLogEntry): string {
    const parts: string[] = [];

    if (log.latencyMs) {
      parts.push(`Latency: ${log.latencyMs}ms`);
    }

    if (log.downloadSpeedMbps) {
      parts.push(`DL: ${log.downloadSpeedMbps.toFixed(2)} Mbps`);
    }

    if (log.uploadSpeedMbps) {
      parts.push(`UL: ${log.uploadSpeedMbps.toFixed(2)} Mbps`);
    }

    if (log.errorMessage) {
      parts.push(log.errorMessage);
    }

    if (log.metadata?.event) {
      parts.push(log.metadata.event);
    }

    return parts.length > 0 ? parts.join(' • ') : '-';
  }

  /**
   * Export logs to CSV
   */
  private exportLogs(): void {
    if (this.logs.length === 0) {
      alert('No logs to export');
      return;
    }

    const csv = this.logsToCSV(this.logs);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `connection-logs-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);

    SharedLogger.log('[ConnectionLogPopup] Logs exported to CSV');
  }

  /**
   * Convert logs to CSV format
   */
  private logsToCSV(logs: ConnectionLogEntry[]): string {
    const headers = ['Timestamp', 'Type', 'Status', 'Latency (ms)', 'Download (Mbps)', 'Upload (Mbps)', 'Error', 'Metadata'];
    const rows = logs.map(log => [
      new Date(log.timestamp).toISOString(),
      log.eventType,
      log.status,
      log.latencyMs || '',
      log.downloadSpeedMbps || '',
      log.uploadSpeedMbps || '',
      log.errorMessage || '',
      JSON.stringify(log.metadata || {})
    ]);

    return [headers, ...rows].map(row => row.join(',')).join('\n');
  }
}

// Export singleton instance
export const ConnectionLogPopup = new ConnectionLogPopupClass();

// Make available globally
if (typeof window !== 'undefined') {
  (window as any).ConnectionLogPopup = ConnectionLogPopup;
}
