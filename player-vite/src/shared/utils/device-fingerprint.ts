/**
 * Device Fingerprint Generator
 * Creates a persistent identifier for browser-based devices
 *
 * This is NOT for security/tracking, but for:
 * - Persisting activation code across cache clears
 * - Identifying same physical device after browser data reset
 */

// Cached local IP address (fetched once via WebRTC)
let cachedLocalIP: string | null = null;

/**
 * Get local IP address using WebRTC with STUN servers
 * This returns the device's local network IP (e.g., 192.168.1.100)
 * NOT the public IP - this is crucial for distinguishing devices on same network
 *
 * NOTE: Modern browsers (Chrome 74+) may hide local IPs with mDNS for privacy.
 * Using STUN servers helps bypass this in many cases.
 */
export async function getLocalIP(): Promise<string> {
  // Return cached value if available (and not 'unknown')
  if (cachedLocalIP && cachedLocalIP !== 'unknown') {
    return cachedLocalIP;
  }

  return new Promise((resolve) => {
    try {
      console.log('[DeviceFingerprint] Starting WebRTC local IP detection...');

      // Use STUN servers to help discover local IP
      // This bypasses some browser privacy restrictions
      const pc = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' },
          { urls: 'stun:stun2.l.google.com:19302' },
        ],
      });

      console.log('[DeviceFingerprint] RTCPeerConnection created');

      const foundIPs: string[] = [];
      let resolved = false;

      pc.createDataChannel('');
      pc.createOffer()
        .then((offer) => pc.setLocalDescription(offer))
        .catch((err) => console.warn('[DeviceFingerprint] createOffer error:', err));

      // Timeout after 5 seconds - use best available or fallback
      const timeout = setTimeout(() => {
        if (!resolved) {
          resolved = true;
          pc.close();

          // Pick the best IP from found ones (prefer 192.168.x.x, then 10.x.x.x)
          const bestIP = pickBestLocalIP(foundIPs);
          cachedLocalIP = bestIP || 'unknown';
          console.log('[DeviceFingerprint] Local IP timeout, best found:', cachedLocalIP, 'all:', foundIPs);
          resolve(cachedLocalIP);
        }
      }, 5000);

      pc.onicecandidate = (ice) => {
        if (ice && ice.candidate && ice.candidate.candidate) {
          const candidate = ice.candidate.candidate;
          // Log ALL candidates for debugging (including mDNS)
          console.log('[DeviceFingerprint] RAW ICE candidate:', candidate);

          // Check for mDNS hostname (*.local) - means browser is hiding IP
          if (candidate.includes('.local')) {
            console.warn('[DeviceFingerprint] Browser is using mDNS (IP hidden):', candidate);
          }

          // Match IPv4 address pattern
          const ipMatch = candidate.match(/(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/);

          if (ipMatch && ipMatch[1]) {
            const ip = ipMatch[1];
            // Skip loopback, link-local, and mDNS placeholder
            if (!ip.startsWith('127.') &&
                !ip.startsWith('169.254.') &&
                !ip.startsWith('0.') &&
                !foundIPs.includes(ip)) {
              foundIPs.push(ip);
              console.log('[DeviceFingerprint] Found IP:', ip);

              // If we found a private IP, use it immediately
              if (isPrivateIP(ip) && !resolved) {
                resolved = true;
                clearTimeout(timeout);
                pc.close();
                cachedLocalIP = ip;
                console.log('[DeviceFingerprint] Local IP detected:', ip);
                resolve(ip);
                return;
              }
            }
          }
        }

        // If candidate is null, ICE gathering is complete
        if (!ice.candidate && !resolved) {
          resolved = true;
          clearTimeout(timeout);
          pc.close();

          const bestIP = pickBestLocalIP(foundIPs);
          cachedLocalIP = bestIP || 'unknown';
          console.log('[DeviceFingerprint] ICE complete, best IP:', cachedLocalIP, 'all:', foundIPs);
          resolve(cachedLocalIP);
        }
      };

      pc.onicegatheringstatechange = () => {
        if (pc.iceGatheringState === 'complete' && !resolved) {
          resolved = true;
          clearTimeout(timeout);
          pc.close();

          const bestIP = pickBestLocalIP(foundIPs);
          cachedLocalIP = bestIP || 'unknown';
          console.log('[DeviceFingerprint] Gathering complete, best IP:', cachedLocalIP);
          resolve(cachedLocalIP);
        }
      };
    } catch (error) {
      console.warn('[DeviceFingerprint] WebRTC not available:', error);
      cachedLocalIP = 'unknown';
      resolve('unknown');
    }
  });
}

/**
 * Check if IP is a private/local network IP
 */
function isPrivateIP(ip: string): boolean {
  const parts = ip.split('.').map(Number);
  if (parts.length !== 4) return false;

  // 10.0.0.0 - 10.255.255.255
  if (parts[0] === 10) return true;

  // 172.16.0.0 - 172.31.255.255
  if (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) return true;

  // 192.168.0.0 - 192.168.255.255
  if (parts[0] === 192 && parts[1] === 168) return true;

  return false;
}

/**
 * Pick the best local IP from a list (prefer 192.168.x.x, then 10.x.x.x, then 172.x.x.x)
 */
function pickBestLocalIP(ips: string[]): string | null {
  // Filter to only private IPs
  const privateIPs = ips.filter(isPrivateIP);

  if (privateIPs.length === 0) return null;

  // Prefer 192.168.x.x (most common home/office network)
  const preferred = privateIPs.find(ip => ip.startsWith('192.168.'));
  if (preferred) return preferred;

  // Then 10.x.x.x
  const ten = privateIPs.find(ip => ip.startsWith('10.'));
  if (ten) return ten;

  // Then any other private IP
  return privateIPs[0];
}

/**
 * Initialize local IP early (call this on app startup)
 * This pre-fetches the local IP so fingerprint generation is fast
 */
export async function initializeLocalIP(): Promise<void> {
  await getLocalIP();
}

/**
 * Generate device fingerprint based on browser/hardware characteristics
 * This fingerprint persists across cache clears but changes if:
 * - Different browser
 * - Different computer/hardware
 * - Different local network IP (different device)
 * - Browser settings significantly changed
 *
 * NOTE: Uses only STABLE components (no canvas) to ensure persistence
 * IMPORTANT: Local IP is included to distinguish devices with identical hardware
 */
export function generateDeviceFingerprint(): string {
  const components: string[] = [];

  // Screen resolution (very stable - persists across cache clears)
  components.push(`screen:${screen.width}x${screen.height}x${screen.colorDepth}`);

  // Timezone offset (stable)
  components.push(`tz:${new Date().getTimezoneOffset()}`);

  // Platform (stable)
  components.push(`platform:${navigator.platform || 'unknown'}`);

  // CPU cores (stable - if available)
  if ('hardwareConcurrency' in navigator) {
    components.push(`cores:${navigator.hardwareConcurrency}`);
  }

  // FULL User agent (makes each browser unique even on same machine)
  // Chrome and Firefox will have different UAs = different fingerprints
  components.push(`ua:${navigator.userAgent}`);

  // Language (stable)
  components.push(`lang:${navigator.language || 'unknown'}`);

  // Max touch points (stable for touch devices)
  if ('maxTouchPoints' in navigator) {
    components.push(`touch:${navigator.maxTouchPoints}`);
  }

  // LOCAL IP address (crucial for distinguishing devices with same hardware)
  // This is the key differentiator: 192.168.1.100 vs 192.168.1.101
  if (cachedLocalIP) {
    components.push(`localip:${cachedLocalIP}`);
  }

  // DO NOT use canvas - it's not stable enough across sessions

  // Combine all components and hash
  const combined = components.join('|');
  return simpleHash(combined);
}

/**
 * Simple hash function (for fingerprint, not cryptographic security)
 */
function simpleHash(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  // Convert to hex and take first 12 characters
  return Math.abs(hash).toString(16).padStart(12, '0').substring(0, 12);
}

/**
 * Get or create device UUID
 * Pure hardware+browser fingerprint (persistent across cache clears)
 * Same browser on same machine = same UUID (even different windows/profiles)
 *
 * IMPORTANT: Call initializeLocalIP() before this for best accuracy
 * Local IP is included to distinguish devices with identical hardware specs
 */
export function getOrCreateDeviceUUID(): string {
  // Generate pure hardware+browser fingerprint (includes local IP if available)
  const fingerprint = generateDeviceFingerprint();
  const uuid = `fp-${fingerprint}`;

  console.log('[DeviceFingerprint] Generated UUID:', uuid);
  console.log('[DeviceFingerprint] Fingerprint components:', {
    screen: `${screen.width}x${screen.height}x${screen.colorDepth}`,
    timezone: new Date().getTimezoneOffset(),
    platform: navigator.platform,
    cores: navigator.hardwareConcurrency,
    userAgent: navigator.userAgent,
    language: navigator.language,
    touch: navigator.maxTouchPoints,
    localIP: cachedLocalIP || 'not yet fetched',
  });

  return uuid;
}

/**
 * Get cached local IP (for external use)
 */
export function getCachedLocalIP(): string | null {
  return cachedLocalIP;
}
