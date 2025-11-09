/**
 * Quality Selector Component
 * Manages quality selection UI and user preferences
 *
 * @features
 * - Show/hide quality selector
 * - Populate quality levels from HLS manifest
 * - Update current quality display
 * - Update bandwidth and buffer display
 * - Show network status indicator
 * - Show quality change notification
 * - Update HLS stats in debug overlay
 */

import { SharedLogger } from '@shared/logger';
import { SharedDeviceState } from '@shared/device/shared-device-state';

/**
 * Quality level configuration
 */
export interface QualityLevel {
  height: number;
  width: number;
  bitrate: number;
}

/**
 * Quality option configuration
 */
interface QualityOptionConfig {
  label: string;
  description?: string;
  value: number | 'auto';
  isAuto?: boolean;
  level?: QualityLevel;
}

/**
 * HLS statistics
 */
export interface HLSStats {
  mode?: string;
  qualityChanges?: number;
  bufferingEvents?: number;
  errors?: number;
}

/**
 * Network status type
 */
export type NetworkStatus = 'excellent' | 'good' | 'slow' | 'poor';

/**
 * Quality Selector Manager Class
 * Singleton pattern for quality selector management
 */
class QualitySelectorManager {
  private static instance: QualitySelectorManager;

  private constructor() {
    // Private constructor for singleton
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): QualitySelectorManager {
    if (!QualitySelectorManager.instance) {
      QualitySelectorManager.instance = new QualitySelectorManager();
    }
    return QualitySelectorManager.instance;
  }

  /**
   * Initialize quality selector
   */
  public init(): void {
    SharedLogger.log('[QualitySelector] Initializing...');

    // Close button handler
    const closeBtn = document.querySelector('.quality-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.hide());
    }

    // Hide selector when clicking outside
    document.addEventListener('click', (e: MouseEvent) => {
      const selector = document.getElementById('quality-selector');
      const target = e.target as HTMLElement;

      // Check if click is outside selector and not on a video element
      if (
        selector &&
        selector.classList.contains('visible') &&
        !selector.contains(target) &&
        target.tagName !== 'VIDEO'
      ) {
        this.hide();
      }
    });

    // Keyboard shortcut: 'q' to toggle quality selector
    document.addEventListener('keydown', (e: KeyboardEvent) => {
      if (e.key === 'q' || e.key === 'Q') {
        this.toggle();
      }
    });

    SharedLogger.log('[QualitySelector] Ready ✅');
  }

  /**
   * Show quality selector
   */
  public show(): void {
    const selector = document.getElementById('quality-selector');
    if (selector) {
      selector.classList.add('visible');
      SharedLogger.log('[QualitySelector] Shown');
    }
  }

  /**
   * Hide quality selector
   */
  public hide(): void {
    const selector = document.getElementById('quality-selector');
    if (selector) {
      selector.classList.remove('visible');
      SharedLogger.log('[QualitySelector] Hidden');
    }
  }

  /**
   * Toggle quality selector visibility
   */
  public toggle(): void {
    const selector = document.getElementById('quality-selector');
    if (selector) {
      if (selector.classList.contains('visible')) {
        this.hide();
      } else {
        this.show();
      }
    }
  }

  /**
   * Populate quality levels from HLS manifest
   */
  public populateLevels(
    levels: QualityLevel[],
    onSelect: (value: number | 'auto') => void
  ): void {
    const container = document.getElementById('quality-levels');
    if (!container) return;

    // Clear existing levels
    container.innerHTML = '';

    // Get saved preference
    const savedQuality = SharedDeviceState.getPreference('preferredQuality') || 'auto';

    // Add "Auto" option
    const autoOption = this.createQualityOption(
      {
        label: 'Auto',
        description: 'Adaptive quality based on connection',
        value: 'auto',
        isAuto: true,
      },
      onSelect
    );

    if (savedQuality === 'auto') {
      autoOption.classList.add('active');
    }

    container.appendChild(autoOption);

    // Sort levels by height (highest first)
    const sortedLevels = [...levels].sort((a, b) => b.height - a.height);

    // Add quality level options
    sortedLevels.forEach((level, index) => {
      const option = this.createQualityOption(
        {
          label: this.getQualityLabel(level.height),
          description: `${level.width}x${level.height} @ ${this.formatBitrate(level.bitrate)}`,
          value: index,
          level: level,
        },
        onSelect
      );

      if (savedQuality === index.toString()) {
        option.classList.add('active');
      }

      container.appendChild(option);
    });

    SharedLogger.log(`[QualitySelector] Populated ${levels.length} quality levels`);
  }

  /**
   * Create quality option element
   */
  private createQualityOption(
    config: QualityOptionConfig,
    onSelect: (value: number | 'auto') => void
  ): HTMLDivElement {
    const option = document.createElement('div');
    option.className = 'quality-level';

    const label = document.createElement('div');
    label.className = 'quality-level-label';
    label.textContent = config.label;

    option.appendChild(label);

    // Add badge for recommended/current quality
    if (config.isAuto) {
      const badge = document.createElement('span');
      badge.className = 'quality-level-badge';
      badge.textContent = 'Recommended';
      option.appendChild(badge);
    }

    // Click handler
    option.addEventListener('click', () => {
      // Update active state
      document.querySelectorAll('.quality-level').forEach((el) => {
        el.classList.remove('active');
      });
      option.classList.add('active');

      // Call selection callback
      if (onSelect) {
        onSelect(config.value);
      }

      // Hide selector after selection
      setTimeout(() => this.hide(), 300);
    });

    return option;
  }

  /**
   * Get quality label from height
   */
  private getQualityLabel(height: number): string {
    if (height >= 2160) return '4K';
    if (height >= 1440) return '1440p';
    if (height >= 1080) return '1080p';
    if (height >= 720) return '720p';
    if (height >= 480) return '480p';
    if (height >= 360) return '360p';
    return `${height}p`;
  }

  /**
   * Format bitrate for display
   */
  private formatBitrate(bitrate: number): string {
    const mbps = (bitrate / 1000000).toFixed(1);
    return `${mbps} Mbps`;
  }

  /**
   * Update current quality display
   */
  public updateCurrentQuality(level: QualityLevel | 'auto'): void {
    const labelEl = document.getElementById('current-quality-label');
    if (labelEl && level) {
      const qualityText =
        level === 'auto' ? 'Auto' : this.getQualityLabel(level.height);
      labelEl.textContent = qualityText;
    }
  }

  /**
   * Update bandwidth display
   */
  public updateBandwidth(bandwidth: number): void {
    const bandwidthEl = document.getElementById('current-bandwidth');
    if (bandwidthEl && bandwidth) {
      bandwidthEl.textContent = this.formatBitrate(bandwidth);
    }
  }

  /**
   * Update buffer display
   */
  public updateBuffer(bufferLength: number): void {
    const bufferEl = document.getElementById('current-buffer');
    if (bufferEl && bufferLength !== undefined) {
      bufferEl.textContent = `${bufferLength.toFixed(1)}s`;
    }
  }

  /**
   * Show network status indicator
   */
  public showNetworkStatus(status: NetworkStatus): void {
    const statusEl = document.getElementById('network-status');
    const indicatorEl = statusEl?.querySelector('.network-indicator') as HTMLElement;
    const labelEl = document.getElementById('network-label');

    if (!statusEl || !indicatorEl || !labelEl) return;

    // Update indicator color and label
    indicatorEl.className = 'network-indicator';

    switch (status) {
      case 'excellent':
        labelEl.textContent = 'Excellent Connection';
        break;
      case 'good':
        labelEl.textContent = 'Good Connection';
        break;
      case 'slow':
        indicatorEl.classList.add('slow');
        labelEl.textContent = 'Slow Connection';
        break;
      case 'poor':
        indicatorEl.classList.add('poor');
        labelEl.textContent = 'Poor Connection';
        break;
    }

    // Show status for 3 seconds
    statusEl.classList.add('visible');
    setTimeout(() => {
      statusEl.classList.remove('visible');
    }, 3000);
  }

  /**
   * Show quality change notification
   */
  public showQualityNotification(qualityText: string): void {
    const notificationEl = document.getElementById('quality-notification');
    const textEl = document.getElementById('quality-notification-text');

    if (!notificationEl || !textEl) return;

    textEl.textContent = qualityText;
    notificationEl.classList.add('visible');

    // Hide after 2 seconds
    setTimeout(() => {
      notificationEl.classList.remove('visible');
    }, 2000);
  }

  /**
   * Update HLS stats in debug overlay
   */
  public updateHLSStats(stats: HLSStats): void {
    const hlsStatsEl = document.getElementById('hls-stats');
    if (!hlsStatsEl) return;

    // Show HLS stats section
    hlsStatsEl.style.display = 'block';

    // Update individual stats
    if (stats.mode !== undefined) {
      const modeEl = document.getElementById('hls-mode');
      if (modeEl) modeEl.textContent = stats.mode;
    }

    if (stats.qualityChanges !== undefined) {
      const changesEl = document.getElementById('hls-quality-changes');
      if (changesEl) changesEl.textContent = String(stats.qualityChanges);
    }

    if (stats.bufferingEvents !== undefined) {
      const bufferEl = document.getElementById('hls-buffer-events');
      if (bufferEl) bufferEl.textContent = String(stats.bufferingEvents);
    }

    if (stats.errors !== undefined) {
      const errorsEl = document.getElementById('hls-errors');
      if (errorsEl) errorsEl.textContent = String(stats.errors);
    }
  }
}

// Export singleton instance
export const QualitySelector = QualitySelectorManager.getInstance();
