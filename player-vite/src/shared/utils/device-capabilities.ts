/**
 * Device Capabilities Detection Utility
 * Detects device hardware capabilities, codec support, and system info
 *
 * @features
 * - Video codec detection (H.264, H.265/HEVC, VP9, AV1)
 * - Audio codec detection (AAC, Opus)
 * - Hardware info (CPU cores, device memory)
 * - WebGL version detection
 * - Display refresh rate detection
 * - Type-safe with TypeScript
 */

import { SharedLogger } from '@shared/logger';

// ========================================
// Types
// ========================================

export interface VideoCodecSupport {
  h264: boolean;
  h265: boolean;
  vp9: boolean;
  av1: boolean;
}

export interface AudioCodecSupport {
  aac: boolean;
  opus: boolean;
}

export interface HardwareInfo {
  cpuCores: number;
  deviceMemoryGB: number | null;
}

export interface WebGLInfo {
  version: string;
  renderer: string | null;
  vendor: string | null;
}

export interface DisplayInfo {
  width: number;
  height: number;
  pixelRatio: number;
  refreshRate: number;
}

export interface DeviceCapabilities {
  // Screen & Display
  screenWidth: number;
  screenHeight: number;
  devicePixelRatio: number;
  displayRefreshRate: number;

  // Hardware
  hardwareConcurrency: number;
  deviceMemoryGB: number | null;

  // Video Codecs
  codecH264: boolean;
  codecH265: boolean;
  codecVP9: boolean;
  codecAV1: boolean;

  // Audio Codecs
  codecAAC: boolean;
  codecOpus: boolean;

  // Graphics
  webglVersion: string;
  webglRenderer: string | null;
  webglVendor: string | null;

  // Software
  userAgent: string;
  platform: string;
  playerVersion: string;
}

// ========================================
// Codec Detection
// ========================================

/**
 * Detect video codec support using HTMLVideoElement.canPlayType()
 * Returns support level: 'probably', 'maybe', or ''
 */
function canPlayVideoType(mimeType: string): boolean {
  try {
    const video = document.createElement('video');
    const support = video.canPlayType(mimeType);
    return support === 'probably' || support === 'maybe';
  } catch (error) {
    SharedLogger.error('[DeviceCapabilities] Error checking video codec:', error);
    return false;
  }
}

/**
 * Detect audio codec support using HTMLAudioElement.canPlayType()
 */
function canPlayAudioType(mimeType: string): boolean {
  try {
    const audio = document.createElement('audio');
    const support = audio.canPlayType(mimeType);
    return support === 'probably' || support === 'maybe';
  } catch (error) {
    SharedLogger.error('[DeviceCapabilities] Error checking audio codec:', error);
    return false;
  }
}

/**
 * Detect all video codec support
 */
export function detectVideoCodecs(): VideoCodecSupport {
  return {
    // H.264/AVC - Most common, widely supported
    h264: canPlayVideoType('video/mp4; codecs="avc1.42E01E"') ||
          canPlayVideoType('video/mp4; codecs="avc1.4D401E"') ||
          canPlayVideoType('video/mp4; codecs="avc1.64001E"'),

    // H.265/HEVC - Better compression, less support
    h265: canPlayVideoType('video/mp4; codecs="hev1.1.2.L93.B0"') ||
          canPlayVideoType('video/mp4; codecs="hvc1.1.2.L93.B0"') ||
          canPlayVideoType('video/mp4; codecs="hev1"'),

    // VP9 - Open codec, good support in Chrome/Firefox
    vp9: canPlayVideoType('video/webm; codecs="vp9"') ||
         canPlayVideoType('video/webm; codecs="vp09.00.10.08"'),

    // AV1 - Newest, best compression, growing support
    av1: canPlayVideoType('video/mp4; codecs="av01.0.05M.08"') ||
         canPlayVideoType('video/webm; codecs="av01.0.05M.08"'),
  };
}

/**
 * Detect all audio codec support
 */
export function detectAudioCodecs(): AudioCodecSupport {
  return {
    // AAC - Most common audio codec
    aac: canPlayAudioType('audio/mp4; codecs="mp4a.40.2"') ||
         canPlayAudioType('audio/aac'),

    // Opus - High quality, open codec
    opus: canPlayAudioType('audio/webm; codecs="opus"') ||
          canPlayAudioType('audio/ogg; codecs="opus"'),
  };
}

// ========================================
// Hardware Detection
// ========================================

/**
 * Get hardware information (CPU cores, memory)
 */
export function detectHardwareInfo(): HardwareInfo {
  return {
    // Number of logical CPU cores
    cpuCores: navigator.hardwareConcurrency || 1,

    // Device memory in GB (Chrome/Edge only)
    deviceMemoryGB: (navigator as any).deviceMemory ?? null,
  };
}

// ========================================
// WebGL Detection
// ========================================

/**
 * Detect WebGL version and renderer info
 */
export function detectWebGL(): WebGLInfo {
  const result: WebGLInfo = {
    version: 'none',
    renderer: null,
    vendor: null,
  };

  try {
    const canvas = document.createElement('canvas');

    // Try WebGL 2 first
    let gl: WebGLRenderingContext | WebGL2RenderingContext | null = canvas.getContext('webgl2');
    if (gl) {
      result.version = '2.0';
    } else {
      // Fall back to WebGL 1
      gl = canvas.getContext('webgl');
      if (gl) {
        result.version = '1.0';
      }
    }

    // Get renderer info if available
    if (gl) {
      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      if (debugInfo) {
        result.renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
        result.vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
      }
    }
  } catch (error) {
    SharedLogger.error('[DeviceCapabilities] Error detecting WebGL:', error);
  }

  return result;
}

// ========================================
// Display Detection
// ========================================

/**
 * Detect display refresh rate via requestAnimationFrame
 * Measures actual frame rate over 1 second
 */
export async function detectDisplayRefreshRate(): Promise<number> {
  return new Promise((resolve) => {
    let frameCount = 0;
    const startTime = performance.now();

    const countFrames = (timestamp: number): void => {
      frameCount++;
      if (timestamp - startTime < 1000) {
        requestAnimationFrame(countFrames);
      } else {
        // Map to common refresh rates
        const commonRates = [30, 48, 50, 60, 75, 90, 100, 120, 144, 165, 240];
        const closestRate = commonRates.reduce((prev, curr) =>
          Math.abs(curr - frameCount) < Math.abs(prev - frameCount) ? curr : prev
        );
        resolve(closestRate);
      }
    };

    requestAnimationFrame(countFrames);
  });
}

/**
 * Get display information
 */
export async function detectDisplayInfo(): Promise<DisplayInfo> {
  return {
    width: window.screen.width,
    height: window.screen.height,
    pixelRatio: window.devicePixelRatio || 1,
    refreshRate: await detectDisplayRefreshRate(),
  };
}

// ========================================
// Platform Detection
// ========================================

/**
 * Detect platform type from user agent
 */
export function detectPlatform(): string {
  const ua = navigator.userAgent.toLowerCase();

  // TV platforms
  if (ua.includes('webos') || ua.includes('web0s')) return 'webOS';
  if (ua.includes('tizen')) return 'Tizen';
  if (ua.includes('android tv')) return 'Android TV';
  if (ua.includes('firetv')) return 'Fire TV';
  if (ua.includes('roku')) return 'Roku';

  // Mobile platforms
  if (ua.includes('android')) return 'Android';
  if (ua.includes('iphone') || ua.includes('ipad')) return 'iOS';

  // Desktop browsers
  if (ua.includes('edg/') || ua.includes('edge')) return 'Edge';
  if (ua.includes('firefox')) return 'Firefox';
  if (ua.includes('chrome')) return 'Chrome';
  if (ua.includes('safari')) return 'Safari';

  return 'Unknown';
}

// ========================================
// Combined Detection
// ========================================

/**
 * Collect all device capabilities
 * This is the main function to call for getting complete device info
 */
export async function collectDeviceCapabilities(playerVersion: string): Promise<DeviceCapabilities> {
  SharedLogger.log('[DeviceCapabilities] Collecting device capabilities...');

  // Collect all info
  const videoCodecs = detectVideoCodecs();
  const audioCodecs = detectAudioCodecs();
  const hardware = detectHardwareInfo();
  const webgl = detectWebGL();
  const display = await detectDisplayInfo();
  const platform = detectPlatform();

  const capabilities: DeviceCapabilities = {
    // Screen & Display
    screenWidth: display.width,
    screenHeight: display.height,
    devicePixelRatio: display.pixelRatio,
    displayRefreshRate: display.refreshRate,

    // Hardware
    hardwareConcurrency: hardware.cpuCores,
    deviceMemoryGB: hardware.deviceMemoryGB,

    // Video Codecs
    codecH264: videoCodecs.h264,
    codecH265: videoCodecs.h265,
    codecVP9: videoCodecs.vp9,
    codecAV1: videoCodecs.av1,

    // Audio Codecs
    codecAAC: audioCodecs.aac,
    codecOpus: audioCodecs.opus,

    // Graphics
    webglVersion: webgl.version,
    webglRenderer: webgl.renderer,
    webglVendor: webgl.vendor,

    // Software
    userAgent: navigator.userAgent,
    platform,
    playerVersion,
  };

  SharedLogger.log('[DeviceCapabilities] Capabilities collected:', capabilities);

  return capabilities;
}

/**
 * Format codec support as a display string
 * Example: "H.264 ✓  H.265 ✗  VP9 ✓  AV1 ✗"
 */
export function formatVideoCodecSupport(codecs: VideoCodecSupport): string {
  const items = [
    `H.264 ${codecs.h264 ? '✓' : '✗'}`,
    `H.265 ${codecs.h265 ? '✓' : '✗'}`,
    `VP9 ${codecs.vp9 ? '✓' : '✗'}`,
    `AV1 ${codecs.av1 ? '✓' : '✗'}`,
  ];
  return items.join('  ');
}

/**
 * Format audio codec support as a display string
 * Example: "AAC ✓  Opus ✓"
 */
export function formatAudioCodecSupport(codecs: AudioCodecSupport): string {
  const items = [
    `AAC ${codecs.aac ? '✓' : '✗'}`,
    `Opus ${codecs.opus ? '✓' : '✗'}`,
  ];
  return items.join('  ');
}
