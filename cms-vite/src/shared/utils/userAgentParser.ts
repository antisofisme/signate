/**
 * User Agent Parser
 * Parse user agent string into readable browser and OS information
 */

export interface ParsedUserAgent {
  browser: string;
  browserVersion: string;
  os: string;
  osVersion: string;
  device: 'desktop' | 'mobile' | 'tablet' | 'unknown';
}

/**
 * Parse user agent string into structured data
 */
export function parseUserAgent(userAgent: string | undefined | null): ParsedUserAgent {
  if (!userAgent) {
    return {
      browser: 'Unknown',
      browserVersion: '',
      os: 'Unknown',
      osVersion: '',
      device: 'unknown',
    };
  }

  const ua = userAgent.toLowerCase();

  // Detect browser
  let browser = 'Unknown';
  let browserVersion = '';

  if (ua.includes('edg/') || ua.includes('edge/')) {
    browser = 'Edge';
    browserVersion = extractVersion(userAgent, /edg(?:e|a|ios)?\/(\d+(?:\.\d+)*)/i);
  } else if (ua.includes('opr/') || ua.includes('opera')) {
    browser = 'Opera';
    browserVersion = extractVersion(userAgent, /(?:opr|opera)\/(\d+(?:\.\d+)*)/i);
  } else if (ua.includes('chrome') && !ua.includes('chromium')) {
    browser = 'Chrome';
    browserVersion = extractVersion(userAgent, /chrome\/(\d+(?:\.\d+)*)/i);
  } else if (ua.includes('firefox')) {
    browser = 'Firefox';
    browserVersion = extractVersion(userAgent, /firefox\/(\d+(?:\.\d+)*)/i);
  } else if (ua.includes('safari') && !ua.includes('chrome')) {
    browser = 'Safari';
    browserVersion = extractVersion(userAgent, /version\/(\d+(?:\.\d+)*)/i);
  } else if (ua.includes('msie') || ua.includes('trident')) {
    browser = 'Internet Explorer';
    browserVersion = extractVersion(userAgent, /(?:msie |rv:)(\d+(?:\.\d+)*)/i);
  }

  // Detect OS
  let os = 'Unknown';
  let osVersion = '';

  if (ua.includes('windows nt')) {
    os = 'Windows';
    const ntVersion = extractVersion(userAgent, /windows nt (\d+(?:\.\d+)*)/i);
    osVersion = mapWindowsVersion(ntVersion);
  } else if (ua.includes('mac os x')) {
    os = 'macOS';
    osVersion = extractVersion(userAgent, /mac os x (\d+[._]\d+(?:[._]\d+)*)/i).replace(/_/g, '.');
  } else if (ua.includes('android')) {
    os = 'Android';
    osVersion = extractVersion(userAgent, /android (\d+(?:\.\d+)*)/i);
  } else if (ua.includes('iphone') || ua.includes('ipad') || ua.includes('ipod')) {
    os = 'iOS';
    osVersion = extractVersion(userAgent, /os (\d+[._]\d+(?:[._]\d+)*)/i).replace(/_/g, '.');
  } else if (ua.includes('linux')) {
    os = 'Linux';
  } else if (ua.includes('cros')) {
    os = 'Chrome OS';
  }

  // Detect device type
  let device: 'desktop' | 'mobile' | 'tablet' | 'unknown' = 'desktop';

  if (ua.includes('mobile') || ua.includes('iphone') || ua.includes('ipod')) {
    device = 'mobile';
  } else if (ua.includes('tablet') || ua.includes('ipad')) {
    device = 'tablet';
  } else if (ua.includes('android')) {
    // Android without "mobile" is usually tablet
    device = ua.includes('mobile') ? 'mobile' : 'tablet';
  }

  return {
    browser,
    browserVersion: browserVersion ? browserVersion.split('.')[0] : '', // Major version only
    os,
    osVersion,
    device,
  };
}

/**
 * Extract version number from user agent using regex
 */
function extractVersion(userAgent: string, regex: RegExp): string {
  const match = userAgent.match(regex);
  return match ? match[1] : '';
}

/**
 * Map Windows NT version to marketing name
 */
function mapWindowsVersion(ntVersion: string): string {
  const versionMap: Record<string, string> = {
    '10.0': '10/11',
    '6.3': '8.1',
    '6.2': '8',
    '6.1': '7',
    '6.0': 'Vista',
    '5.2': 'XP x64',
    '5.1': 'XP',
  };
  return versionMap[ntVersion] || ntVersion;
}

/**
 * Get formatted browser string (e.g., "Chrome 142")
 */
export function getBrowserString(parsed: ParsedUserAgent): string {
  if (parsed.browserVersion) {
    return `${parsed.browser} ${parsed.browserVersion}`;
  }
  return parsed.browser;
}

/**
 * Get formatted OS string (e.g., "Windows 10")
 */
export function getOSString(parsed: ParsedUserAgent): string {
  if (parsed.osVersion) {
    return `${parsed.os} ${parsed.osVersion}`;
  }
  return parsed.os;
}

/**
 * Get short device info string
 */
export function getDeviceInfoString(userAgent: string | undefined | null): string {
  const parsed = parseUserAgent(userAgent);
  return `${getBrowserString(parsed)} on ${getOSString(parsed)}`;
}
