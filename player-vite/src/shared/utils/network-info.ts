/**
 * Network Information Utilities
 * Get IP Address and Network info from browser
 *
 * NOTE: Local IP detection removed - browser privacy (mDNS) blocks WebRTC detection.
 * Use backend-provided IP instead (from HTTP request headers).
 */

export interface NetworkInfo {
  localIP: string | null;  // Deprecated - always null due to browser privacy
  publicIP: string | null;
  connectionType: string;
  online: boolean;
}

/**
 * DEPRECATED: Local IP detection via WebRTC
 * Always returns null due to browser mDNS privacy mode
 * @deprecated Use backend-provided IP from device API instead
 */
export async function getLocalIP(): Promise<string | null> {
  // Browser privacy (mDNS RFC 8828) blocks local IP detection
  // Use backend-provided IP from HTTP request headers instead
  console.log('[NetworkInfo] ℹ️ Local IP detection skipped (browser privacy blocks WebRTC)');
  return null;
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
