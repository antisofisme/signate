/**
 * Device Fingerprint Generator
 * Creates a persistent identifier for browser-based devices
 *
 * This is NOT for security/tracking, but for:
 * - Persisting activation code across cache clears
 * - Identifying same physical device after browser data reset
 */

/**
 * Generate device fingerprint based on browser/hardware characteristics
 * This fingerprint persists across cache clears but changes if:
 * - Different browser
 * - Different computer/hardware
 * - Browser settings significantly changed
 *
 * NOTE: Uses only STABLE components (no canvas) to ensure persistence
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
 */
export function getOrCreateDeviceUUID(): string {
  // Generate pure hardware+browser fingerprint
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
  });

  return uuid;
}
