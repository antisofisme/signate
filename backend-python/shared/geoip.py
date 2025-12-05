"""
GeoIP Lookup Service
Phase 6: Server-Side Features

Provides geolocation information from IP addresses using free GeoIP APIs.
Supports multiple providers with fallback.

Features:
- City, Country, ISP, Timezone lookup
- Caching to reduce API calls
- Fallback to secondary providers
- Rate limiting aware
"""

import asyncio
import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class GeoIPResult:
    """GeoIP lookup result"""
    ip: str
    city: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    isp: Optional[str] = None
    timezone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    success: bool = False
    error: Optional[str] = None


class GeoIPService:
    """
    GeoIP lookup service with caching and fallback providers

    Primary provider: ip-api.com (free, 45 requests/minute)
    Fallback: ipapi.co (free, 1000/day)
    """

    def __init__(self):
        # Simple in-memory cache: {ip: (result, timestamp)}
        self._cache: Dict[str, tuple[GeoIPResult, datetime]] = {}
        self._cache_ttl = timedelta(hours=24)  # Cache for 24 hours
        self._max_cache_size = 10000

        # Rate limiting tracking
        self._request_count = 0
        self._rate_limit_reset = datetime.now()
        self._rate_limit_per_minute = 40  # Stay under 45/min limit

    def _is_rate_limited(self) -> bool:
        """Check if we're rate limited"""
        now = datetime.now()

        # Reset counter every minute
        if now > self._rate_limit_reset:
            self._request_count = 0
            self._rate_limit_reset = now + timedelta(minutes=1)
            return False

        return self._request_count >= self._rate_limit_per_minute

    def _get_cached(self, ip: str) -> Optional[GeoIPResult]:
        """Get cached result if valid"""
        if ip in self._cache:
            result, timestamp = self._cache[ip]
            if datetime.now() - timestamp < self._cache_ttl:
                return result
            else:
                # Expired, remove from cache
                del self._cache[ip]
        return None

    def _set_cache(self, ip: str, result: GeoIPResult):
        """Cache result"""
        # Evict old entries if cache is full
        if len(self._cache) >= self._max_cache_size:
            # Remove oldest 10%
            sorted_items = sorted(self._cache.items(), key=lambda x: x[1][1])
            for key, _ in sorted_items[:self._max_cache_size // 10]:
                del self._cache[key]

        self._cache[ip] = (result, datetime.now())

    async def lookup(self, ip: str) -> GeoIPResult:
        """
        Lookup geolocation for IP address

        Args:
            ip: IP address to lookup

        Returns:
            GeoIPResult with location data
        """
        # Skip private/local IPs
        if self._is_private_ip(ip):
            return GeoIPResult(
                ip=ip,
                success=False,
                error="Private IP address"
            )

        # Check cache first
        cached = self._get_cached(ip)
        if cached:
            logger.debug(f"GeoIP cache hit for {ip}")
            return cached

        # Check rate limiting
        if self._is_rate_limited():
            logger.warning("GeoIP rate limited, skipping lookup")
            return GeoIPResult(
                ip=ip,
                success=False,
                error="Rate limited"
            )

        # Try primary provider
        result = await self._lookup_ip_api(ip)

        # Fallback to secondary if primary fails
        if not result.success:
            result = await self._lookup_ipapi_co(ip)

        # Cache successful results
        if result.success:
            self._set_cache(ip, result)

        return result

    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is private/local"""
        if not ip:
            return True

        # Common private/local patterns
        private_prefixes = [
            '10.',
            '172.16.', '172.17.', '172.18.', '172.19.',
            '172.20.', '172.21.', '172.22.', '172.23.',
            '172.24.', '172.25.', '172.26.', '172.27.',
            '172.28.', '172.29.', '172.30.', '172.31.',
            '192.168.',
            '127.',
            '0.',
            '::1',
            'fe80:',
            'fc00:',
            'fd00:',
        ]

        for prefix in private_prefixes:
            if ip.startswith(prefix):
                return True

        return False

    async def _lookup_ip_api(self, ip: str) -> GeoIPResult:
        """
        Lookup using ip-api.com (primary)
        Free: 45 requests/minute
        """
        try:
            self._request_count += 1

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"http://ip-api.com/json/{ip}",
                    params={
                        "fields": "status,message,country,countryCode,region,city,lat,lon,timezone,isp,query"
                    }
                )

                if response.status_code != 200:
                    return GeoIPResult(
                        ip=ip,
                        success=False,
                        error=f"HTTP {response.status_code}"
                    )

                data = response.json()

                if data.get("status") == "fail":
                    return GeoIPResult(
                        ip=ip,
                        success=False,
                        error=data.get("message", "Unknown error")
                    )

                return GeoIPResult(
                    ip=ip,
                    city=data.get("city"),
                    country=data.get("country"),
                    country_code=data.get("countryCode"),
                    region=data.get("region"),
                    isp=data.get("isp"),
                    timezone=data.get("timezone"),
                    latitude=data.get("lat"),
                    longitude=data.get("lon"),
                    success=True
                )

        except httpx.TimeoutException:
            logger.warning(f"GeoIP lookup timeout for {ip}")
            return GeoIPResult(ip=ip, success=False, error="Timeout")
        except Exception as e:
            logger.error(f"GeoIP lookup error for {ip}: {e}")
            return GeoIPResult(ip=ip, success=False, error=str(e))

    async def _lookup_ipapi_co(self, ip: str) -> GeoIPResult:
        """
        Lookup using ipapi.co (fallback)
        Free: 1000 requests/day
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"https://ipapi.co/{ip}/json/"
                )

                if response.status_code != 200:
                    return GeoIPResult(
                        ip=ip,
                        success=False,
                        error=f"HTTP {response.status_code}"
                    )

                data = response.json()

                if data.get("error"):
                    return GeoIPResult(
                        ip=ip,
                        success=False,
                        error=data.get("reason", "Unknown error")
                    )

                return GeoIPResult(
                    ip=ip,
                    city=data.get("city"),
                    country=data.get("country_name"),
                    country_code=data.get("country_code"),
                    region=data.get("region"),
                    isp=data.get("org"),
                    timezone=data.get("timezone"),
                    latitude=data.get("latitude"),
                    longitude=data.get("longitude"),
                    success=True
                )

        except httpx.TimeoutException:
            logger.warning(f"GeoIP fallback lookup timeout for {ip}")
            return GeoIPResult(ip=ip, success=False, error="Timeout")
        except Exception as e:
            logger.error(f"GeoIP fallback lookup error for {ip}: {e}")
            return GeoIPResult(ip=ip, success=False, error=str(e))

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cache_size": len(self._cache),
            "max_cache_size": self._max_cache_size,
            "cache_ttl_hours": self._cache_ttl.total_seconds() / 3600,
            "requests_this_minute": self._request_count,
            "rate_limit_per_minute": self._rate_limit_per_minute
        }


# Global singleton instance
geoip_service = GeoIPService()


async def lookup_geoip(ip: str) -> GeoIPResult:
    """
    Convenience function for GeoIP lookup

    Args:
        ip: IP address to lookup

    Returns:
        GeoIPResult with location data
    """
    return await geoip_service.lookup(ip)
