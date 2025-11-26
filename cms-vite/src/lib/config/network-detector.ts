/**
 * Smart Network Detection for CMS Admin
 * Auto-detect whether accessing from LAN or Internet
 *
 * Strategy:
 * - If hostname is local IP (192.168.x.x) → LAN (use HTTP local)
 * - If hostname is domain HTTPS → Internet (use HTTPS domain)
 */

// Network Configuration Constants
// These are fallback values when environment variables are not configured
const NETWORK_CONFIG = {
  LAN: {
    API_URL: import.meta.env.VITE_LAN_API_URL || 'http://192.168.5.12:8001',
    WS_URL: import.meta.env.VITE_LAN_WS_URL || 'ws://192.168.5.12:8001',
  },
  INTERNET: {
    API_URL: import.meta.env.VITE_INTERNET_API_URL || 'https://api.zhmhotels.online',
    WS_URL: import.meta.env.VITE_INTERNET_WS_URL || 'wss://api.zhmhotels.online',
  },
} as const;

/**
 * Check if hostname is a local IP (private network)
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
  const configuredUrl = envUrl || import.meta.env.VITE_API_URL;

  if (configuredUrl && configuredUrl !== 'auto') {
    console.log('[CMS NetworkDetector] Using configured API URL:', configuredUrl);
    return configuredUrl;
  }

  // Smart detection based on how CMS is accessed
  if (isLocalNetwork()) {
    // Accessed via local IP → use local backend
    console.log('[CMS NetworkDetector] LAN detected - Using local backend');
    return NETWORK_CONFIG.LAN.API_URL;
  } else {
    // Accessed via domain → use HTTPS domain
    console.log('[CMS NetworkDetector] Internet access - Using HTTPS domain');
    return NETWORK_CONFIG.INTERNET.API_URL;
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
  const configuredWsUrl = envWsUrl || import.meta.env.VITE_WS_URL;

  if (configuredWsUrl && configuredWsUrl !== 'auto') {
    console.log('[CMS NetworkDetector] Using configured WebSocket URL:', configuredWsUrl);
    return configuredWsUrl;
  }

  // Smart detection based on how CMS is accessed
  if (isLocalNetwork()) {
    // Accessed via local IP → use local backend WebSocket
    console.log('[CMS NetworkDetector] LAN detected - Using local WebSocket');
    return NETWORK_CONFIG.LAN.WS_URL;
  } else {
    // Accessed via domain → use WSS domain
    console.log('[CMS NetworkDetector] Internet access - Using WSS domain');
    return NETWORK_CONFIG.INTERNET.WS_URL;
  }
}

/**
 * Display current configuration (for debugging)
 */
export function showCMSNetworkConfig(): void {
  console.log('🌐 CMS Network Configuration:');
  console.log('  Location:', isLocalNetwork() ? 'LOCAL NETWORK' : 'INTERNET');
  console.log('  Hostname:', window.location.hostname);
  console.log('  Protocol:', window.location.protocol);
  console.log('  API URL:', getSmartApiUrl());
  console.log('  WebSocket URL:', getSmartWebSocketUrl());
}
