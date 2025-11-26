/**
 * Smart Network Detection for Player
 * Auto-detect apakah akses dari LAN atau Internet
 *
 * Strategi:
 * - Jika hostname adalah IP lokal (192.168.x.x) → LAN (gunakan HTTP lokal)
 * - Jika hostname adalah domain HTTPS → Internet (gunakan HTTPS domain)
 */

/**
 * Cek apakah hostname adalah IP lokal (private network)
 */
function isLocalNetwork(): boolean {
  const hostname = window.location.hostname;

  // Check if accessing via local IP
  if (
    hostname.startsWith('192.168.') ||
    hostname.startsWith('10.') ||
    hostname.startsWith('172.16.') ||
    hostname.startsWith('172.17.') ||
    hostname.startsWith('172.18.') ||
    hostname.startsWith('172.19.') ||
    hostname.startsWith('172.20.') ||
    hostname.startsWith('172.21.') ||
    hostname.startsWith('172.22.') ||
    hostname.startsWith('172.23.') ||
    hostname.startsWith('172.24.') ||
    hostname.startsWith('172.25.') ||
    hostname.startsWith('172.26.') ||
    hostname.startsWith('172.27.') ||
    hostname.startsWith('172.28.') ||
    hostname.startsWith('172.29.') ||
    hostname.startsWith('172.30.') ||
    hostname.startsWith('172.31.') ||
    hostname === 'localhost' ||
    hostname === '127.0.0.1'
  ) {
    return true;
  }

  return false;
}

/**
 * Get API base URL - smart detection based on access method
 * - If accessed via local IP → use local backend URL (for LAN)
 * - If accessed via domain → use HTTPS domain (for Internet)
 * - Environment variable can override for testing
 */
export function getSmartApiUrl(envUrl?: string): string {
  // Use environment variable if explicitly configured (not 'auto')
  const configuredUrl = envUrl || import.meta.env.VITE_API_BASE_URL;

  if (configuredUrl && configuredUrl !== 'auto') {
    console.log('[Player NetworkDetector] Using configured API URL:', configuredUrl);
    return configuredUrl;
  }

  // Smart detection based on how Player is accessed
  if (isLocalNetwork()) {
    // Accessed via local IP → use local backend
    console.log('[Player NetworkDetector] LAN detected - Using local backend');
    return 'http://192.168.5.12:8001';
  } else {
    // Accessed via domain → use HTTPS domain
    console.log('[Player NetworkDetector] Internet access - Using HTTPS domain');
    return 'https://api.zhmhotels.online';
  }
}

/**
 * Get WebSocket URL - smart detection based on access method
 * - If accessed via local IP → use local backend WebSocket (for LAN)
 * - If accessed via domain → use WSS domain (for Internet)
 * - Environment variable can override for testing
 */
export function getSmartWebSocketUrl(envWsUrl?: string): string {
  // Use environment variable if explicitly configured (not 'auto')
  const configuredWsUrl = envWsUrl || import.meta.env.VITE_WS_BASE_URL;

  if (configuredWsUrl && configuredWsUrl !== 'auto') {
    console.log('[Player NetworkDetector] Using configured WebSocket URL:', configuredWsUrl);
    return configuredWsUrl;
  }

  // Smart detection based on how Player is accessed
  if (isLocalNetwork()) {
    // Accessed via local IP → use local backend WebSocket
    console.log('[Player NetworkDetector] LAN detected - Using local WebSocket');
    return 'ws://192.168.5.12:8001';
  } else {
    // Accessed via domain → use WSS domain
    console.log('[Player NetworkDetector] Internet access - Using WSS domain');
    return 'wss://api.zhmhotels.online';
  }
}

/**
 * Transform content URL for local network access
 * Replaces HTTPS domain URL with HTTP local URL when on LAN
 *
 * Examples:
 * - https://api.zhmhotels.online/content/... → http://192.168.5.12:8001/content/...
 * - http://192.168.5.12:8001/content/... → http://192.168.5.12:8001/content/... (no change)
 */
export function transformContentUrl(url: string): string {
  if (!url) return url;

  // If on local network, replace HTTPS domain with HTTP local
  if (isLocalNetwork()) {
    // Replace HTTPS domain with HTTP local server
    if (url.includes('https://api.zhmhotels.online')) {
      const transformed = url.replace('https://api.zhmhotels.online', 'http://192.168.5.12:8001');
      console.log('[NetworkDetector] 🔄 URL transformed for LAN:', url, '→', transformed);
      return transformed;
    }
  }

  // No transformation needed
  return url;
}

/**
 * Display current configuration (for debugging)
 */
export function showPlayerNetworkConfig(): void {
  console.log('🌐 Player Network Configuration:');
  console.log('  Location:', isLocalNetwork() ? 'LOCAL NETWORK' : 'INTERNET');
  console.log('  Hostname:', window.location.hostname);
  console.log('  Protocol:', window.location.protocol);
  console.log('  API URL:', getSmartApiUrl());
  console.log('  WebSocket URL:', getSmartWebSocketUrl());
}
