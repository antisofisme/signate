/**
 * Network Information Utilities
 * Get IP Address and Network info from browser
 *
 * Local IP detection is now handled by device-fingerprint.ts using WebRTC
 * and cached for reuse across the application.
 */

import { getCachedLocalIP, getLocalIP as getLocalIPFromFingerprint } from './device-fingerprint';

export interface NetworkInfo {
  localIP: string | null;  // From WebRTC (cached in device-fingerprint)
  publicIP: string | null;
  connectionType: string;
  online: boolean;
}

/**
 * Get local IP address from cached fingerprint
 * Uses WebRTC-based detection from device-fingerprint module
 * Returns cached value if available, otherwise fetches new
 */
export async function getLocalIP(): Promise<string | null> {
  // First try cached value (fast path)
  const cached = getCachedLocalIP();
  if (cached && cached !== 'unknown') {
    console.log('[NetworkInfo] ✅ Using cached local IP:', cached);
    return cached;
  }

  // If not cached yet, fetch it
  const ip = await getLocalIPFromFingerprint();
  console.log('[NetworkInfo] 🌐 Fetched local IP:', ip);
  return ip !== 'unknown' ? ip : null;
}

/**
 * Get public IP address from external service
 */
export async function getPublicIP(): Promise<string | null> {
  try {
    // Try multiple services in case one fails
    const services = [
      'https://api.ipify.org?format=json',
      'https://api.ip.sb/jsonip',
      'https://ipapi.co/json'
    ];

    for (const service of services) {
      try {
        const response = await fetch(service, {
          method: 'GET',
          signal: AbortSignal.timeout(3000) // 3s timeout
        });

        if (response.ok) {
          const data = await response.json();
          return data.ip || data.query || null;
        }
      } catch (err) {
        continue; // Try next service
      }
    }

    return null;
  } catch (error) {
    console.error('[NetworkInfo] Failed to get public IP:', error);
    return null;
  }
}

/**
 * Get connection type
 */
export function getConnectionType(): string {
  // @ts-ignore - navigator.connection is experimental
  const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;

  if (!connection) {
    return 'Unknown';
  }

  const type = connection.effectiveType || connection.type;

  // Map to readable names
  const typeMap: Record<string, string> = {
    'slow-2g': '2G (Slow)',
    '2g': '2G',
    '3g': '3G',
    '4g': '4G',
    '5g': '5G',
    'wifi': 'WiFi',
    'ethernet': 'Ethernet',
    'bluetooth': 'Bluetooth',
    'cellular': 'Cellular',
    'none': 'Offline'
  };

  return typeMap[type] || type || 'Unknown';
}

/**
 * Get full network info
 */
export async function getNetworkInfo(): Promise<NetworkInfo> {
  const [localIP, publicIP] = await Promise.all([
    getLocalIP(),
    getPublicIP()
  ]);

  return {
    localIP,
    publicIP,
    connectionType: getConnectionType(),
    online: navigator.onLine
  };
}

/**
 * Get download speed estimate (if supported)
 */
export function getDownloadSpeed(): string | null {
  // @ts-ignore
  const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;

  if (!connection || !connection.downlink) {
    return null;
  }

  const mbps = connection.downlink;
  return `${mbps} Mbps`;
}

/**
 * MAC Address cannot be retrieved from browser for security reasons
 * This function returns a placeholder message
 */
export function getMACAddress(): string {
  return 'Not available (Browser security)';
}
