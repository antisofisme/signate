/**
 * Network Utilities
 * Functions for detecting network information
 */

/**
 * Detect local IP address using WebRTC
 * Returns the local/private IP address (e.g., 192.168.x.x)
 *
 * Note: This may not work in all browsers due to privacy restrictions
 * Falls back to 'unknown' if detection fails
 */
export async function getLocalIP(): Promise<string> {
  return new Promise((resolve) => {
    // Timeout after 3 seconds
    const timeout = setTimeout(() => {
      resolve('unknown');
    }, 3000);

    try {
      // Create RTCPeerConnection to detect local IP
      const rtc = new RTCPeerConnection({
        iceServers: []
      });

      rtc.createDataChannel('');

      rtc.onicecandidate = (event) => {
        if (event.candidate) {
          // Extract IP from candidate string
          const candidate = event.candidate.candidate;
          const ipMatch = candidate.match(/(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/);

          if (ipMatch) {
            const ip = ipMatch[1];
            // Check if it's a private IP (not public)
            if (isPrivateIP(ip)) {
              clearTimeout(timeout);
              rtc.close();
              resolve(ip);
            }
          }
        }
      };

      rtc.onicegatheringstatechange = () => {
        if (rtc.iceGatheringState === 'complete') {
          clearTimeout(timeout);
          rtc.close();
          resolve('unknown');
        }
      };

      rtc.createOffer()
        .then((offer) => rtc.setLocalDescription(offer))
        .catch(() => {
          clearTimeout(timeout);
          resolve('unknown');
        });

    } catch (error) {
      clearTimeout(timeout);
      resolve('unknown');
    }
  });
}

/**
 * Check if an IP address is private/local
 */
function isPrivateIP(ip: string): boolean {
  const parts = ip.split('.').map(Number);

  // 10.x.x.x
  if (parts[0] === 10) return true;

  // 172.16.x.x - 172.31.x.x
  if (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) return true;

  // 192.168.x.x
  if (parts[0] === 192 && parts[1] === 168) return true;

  // 169.254.x.x (link-local)
  if (parts[0] === 169 && parts[1] === 254) return true;

  return false;
}

/**
 * Get device information including local IP
 */
export async function getDeviceInfo(): Promise<{
  platform: string;
  user_agent: string;
  local_ip?: string;
}> {
  const userAgent = navigator.userAgent;
  let platform = 'unknown';

  // Detect platform
  if (userAgent.includes('Windows')) {
    platform = 'Windows';
  } else if (userAgent.includes('Mac')) {
    platform = 'macOS';
  } else if (userAgent.includes('Linux') && !userAgent.includes('Android')) {
    platform = 'Linux';
  } else if (userAgent.includes('Android')) {
    platform = 'Android';
  } else if (/iPhone|iPad|iPod/.test(userAgent)) {
    platform = 'iOS';
  }

  // Try to get local IP
  const localIP = await getLocalIP();

  return {
    platform,
    user_agent: userAgent,
    local_ip: localIP !== 'unknown' ? localIP : undefined
  };
}
