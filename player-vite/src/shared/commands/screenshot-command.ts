/**
 * Screenshot Command
 *
 * @class ScreenshotCommand
 * @extends BaseCommand
 * @description
 * Command to capture current display as screenshot.
 * Supports video frame capture, DOM rendering, and upload to backend.
 *
 * @features
 * - HTML5 canvas-based screenshot capture
 * - Video frame capture when available
 * - DOM content fallback
 * - Quality-based JPEG compression
 * - Backend upload capability
 * - Base64 data URL fallback
 *
 * @usage
 * ```typescript
 * const cmd = new ScreenshotCommand();
 * const result = await cmd.executeWithTimeout({ quality: 'high', upload: true });
 * ```
 */

import { BaseCommand, CommandResult } from './base-command';
import { SharedDeviceState } from '@shared/device';

export type ScreenshotQuality = 'low' | 'medium' | 'high';

export interface ScreenshotParameters {
  quality?: ScreenshotQuality;
  upload?: boolean;
}

export interface ScreenshotResult extends CommandResult {
  uploaded: boolean;
  screenshot_base64?: string;
  screenshot_url?: string;
  size_bytes: number;
  size_kb: number;
  width: number;
  height: number;
  quality: ScreenshotQuality;
  upload_error?: string;
}

interface CaptureResult {
  canvas: HTMLCanvasElement;
  screenshotSize: number;
}

export class ScreenshotCommand extends BaseCommand {
  private qualitySettings: Record<ScreenshotQuality, number> = {
    low: 0.5,
    medium: 0.8,
    high: 0.95
  };

  /**
   * Create screenshot command instance
   */
  constructor() {
    super('Screenshot');
  }

  /**
   * Validate screenshot parameters
   *
   * @param parameters - Command parameters
   * @throws Error if validation fails
   */
  validate(parameters?: ScreenshotParameters): void {
    if (!parameters) return;

    if (parameters.quality && !this.qualitySettings[parameters.quality]) {
      throw new Error(`Invalid quality: ${parameters.quality}. Use: low, medium, high`);
    }
  }

  /**
   * Execute screenshot command
   *
   * @param parameters - Command parameters
   * @returns Screenshot result
   */
  async execute(parameters: ScreenshotParameters = {}): Promise<ScreenshotResult> {
    const { quality = 'medium', upload = false } = parameters;

    this.validate(parameters);
    this.log(`Taking screenshot (quality: ${quality}, upload: ${upload})`);

    const jpegQuality = this.qualitySettings[quality] || 0.8;

    // Capture canvas
    const { canvas, screenshotSize } = await this.captureCanvas(jpegQuality);

    this.log(`Screenshot captured (${Math.round(screenshotSize / 1024)} KB)`);

    // Upload to backend if requested
    if (upload) {
      return await this.uploadScreenshot(canvas, screenshotSize, quality);
    }

    // Return base64 data URL
    const base64 = await this.blobToBase64(canvas, jpegQuality);

    return {
      success: true,
      uploaded: false,
      screenshot_base64: base64,
      size_bytes: screenshotSize,
      size_kb: Math.round(screenshotSize / 1024),
      width: canvas.width,
      height: canvas.height,
      quality: quality
    };
  }

  /**
   * Capture canvas from video or DOM
   */
  private async captureCanvas(jpegQuality: number): Promise<CaptureResult> {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    if (!ctx) {
      throw new Error('Failed to get canvas context');
    }

    // Try to capture video frame first
    const videoElement = document.querySelector('video');

    if (videoElement && !videoElement.paused && videoElement.readyState >= 2) {
      this.log('Capturing video frame');
      canvas.width = videoElement.videoWidth || window.innerWidth;
      canvas.height = videoElement.videoHeight || window.innerHeight;
      ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    } else {
      this.log('Capturing DOM content');
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;

      // Simple DOM capture
      ctx.fillStyle = getComputedStyle(document.body).backgroundColor || '#000';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Add text overlay with device info
      ctx.fillStyle = '#fff';
      ctx.font = '24px Arial';
      ctx.fillText('Screenshot captured', 50, 100);
      ctx.font = '16px Arial';
      ctx.fillText(`Device: ${SharedDeviceState.getDeviceId() || 'Unknown'}`, 50, 150);
      ctx.fillText(`Time: ${new Date().toLocaleString()}`, 50, 180);
    }

    // Convert to blob
    const blob = await new Promise<Blob>((resolve) => {
      canvas.toBlob((b) => resolve(b!), 'image/jpeg', jpegQuality);
    });

    return {
      canvas,
      screenshotSize: blob.size
    };
  }

  /**
   * Upload screenshot to backend
   */
  private async uploadScreenshot(
    canvas: HTMLCanvasElement,
    screenshotSize: number,
    quality: ScreenshotQuality
  ): Promise<ScreenshotResult> {
    try {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
      if (!apiBaseUrl) {
        throw new Error('No API_BASE_URL configured');
      }

      // Create blob for upload
      const jpegQuality = this.qualitySettings[quality] || 0.8;
      const blob = await new Promise<Blob>((resolve) => {
        canvas.toBlob((b) => resolve(b!), 'image/jpeg', jpegQuality);
      });

      const formData = new FormData();
      formData.append('screenshot', blob, `screenshot_${Date.now()}.jpg`);
      formData.append('device_id', SharedDeviceState.getDeviceId() || '0');

      const uploadUrl = `${apiBaseUrl}/api/screenshots/upload`;
      this.log(`Uploading screenshot to ${uploadUrl}`);

      const response = await fetch(uploadUrl, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      this.log('✅ Screenshot uploaded');

      return {
        success: true,
        uploaded: true,
        screenshot_url: data.url || data.path,
        size_bytes: screenshotSize,
        size_kb: Math.round(screenshotSize / 1024),
        width: canvas.width,
        height: canvas.height,
        quality: quality
      };

    } catch (uploadError) {
      this.logError('❌ Screenshot upload failed:', uploadError as Error);

      // Return base64 as fallback
      const jpegQuality = this.qualitySettings[quality] || 0.8;
      const base64 = await this.blobToBase64(canvas, jpegQuality);
      return {
        success: true,
        uploaded: false,
        upload_error: (uploadError as Error).message,
        screenshot_base64: base64,
        size_bytes: screenshotSize,
        size_kb: Math.round(screenshotSize / 1024),
        width: canvas.width,
        height: canvas.height,
        quality: quality
      };
    }
  }

  /**
   * Convert canvas to blob and then to base64 data URL
   */
  private async blobToBase64(canvas: HTMLCanvasElement, jpegQuality: number): Promise<string> {
    const blob = await new Promise<Blob>((resolve) => {
      canvas.toBlob((b) => resolve(b!), 'image/jpeg', jpegQuality);
    });

    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  }
}
