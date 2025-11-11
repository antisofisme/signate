"""
Cloud Sync Client
Sends data to cloud backend via REST API
"""

import requests
import logging
from typing import List, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class CloudSyncClient:
    """Client for syncing data to cloud backend"""

    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger('CloudSync')
        self.session = self.create_session()

    def create_session(self) -> requests.Session:
        """Create HTTP session with retry logic"""
        session = requests.Session()

        # Retry strategy
        retry = Retry(
            total=self.config.get('retry_attempts', 3),
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        # Set headers
        session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': self.config['api_key'],
            'X-Organization-ID': str(self.config['organization_id'])
        })

        return session

    def test_connection(self) -> bool:
        """Test connection to cloud backend"""
        try:
            url = f"{self.config['api_url']}/health"
            response = self.session.get(
                url,
                timeout=10,
                verify=self.config.get('verify_ssl', False)
            )

            if response.status_code == 200:
                self.logger.info("Cloud connection OK")
                return True
            else:
                self.logger.error(f"Cloud health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Cannot connect to cloud: {e}")
            return False

    def sync_guests(self, guests: List[Dict[str, Any]]) -> bool:
        """Sync guest check-in data to cloud"""
        try:
            url = f"{self.config['api_url']}/pms/sync/guests"

            # Convert dataclass objects to dicts if needed
            guest_dicts = [g.to_dict() if hasattr(g, 'to_dict') else g for g in guests]

            response = self.session.post(
                url,
                json={'guests': guest_dicts},
                timeout=30,
                verify=self.config.get('verify_ssl', False)
            )

            if response.status_code in [200, 201]:
                self.logger.info(f"Synced {len(guests)} guests successfully")
                return True
            else:
                self.logger.error(f"Guest sync failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error syncing guests: {e}")
            return False

    def sync_rooms(self, rooms: List[Dict[str, Any]]) -> bool:
        """Sync room status to cloud"""
        try:
            url = f"{self.config['api_url']}/pms/sync/rooms"

            # Convert dataclass objects to dicts if needed
            room_dicts = [r.to_dict() if hasattr(r, 'to_dict') else r for r in rooms]

            response = self.session.post(
                url,
                json={'rooms': room_dicts},
                timeout=30,
                verify=self.config.get('verify_ssl', False)
            )

            if response.status_code in [200, 201]:
                self.logger.info(f"Synced {len(rooms)} rooms successfully")
                return True
            else:
                self.logger.error(f"Room sync failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error syncing rooms: {e}")
            return False
