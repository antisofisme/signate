#!/usr/bin/env python3
"""
Firebird Bridge Agent
Local service that syncs Firebird PMS data to cloud backend
"""

import time
import logging
import yaml
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from firebird_reader import FirebirdReader
from cloud_sync import CloudSyncClient
from models import GuestData, RoomStatus


class FirebirdBridgeAgent:
    """Main agent orchestrator"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self.load_config(config_path)
        self.running = False
        self.setup_logging()
        self.firebird_reader: Optional[FirebirdReader] = None
        self.cloud_client: Optional[CloudSyncClient] = None

    def load_config(self, path: str) -> dict:
        """Load configuration from YAML file"""
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config['logging']

        # Create log directory if not exists
        log_file = Path(log_config['file'])
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=getattr(logging, log_config['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_config['file']),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('FirebirdBridge')

    def initialize_services(self):
        """Initialize Firebird reader and cloud client"""
        try:
            self.logger.info("Initializing services...")
            self.firebird_reader = FirebirdReader(self.config['firebird'])
            self.cloud_client = CloudSyncClient(self.config['cloud'])
            self.logger.info("Services initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}")
            raise

    def sync_guest_data(self):
        """Sync guest check-in data from Firebird to cloud"""
        try:
            # 1. Query new check-ins from Firebird
            self.logger.info("Querying guest check-ins from Firebird...")
            guests = self.firebird_reader.get_recent_checkins(
                minutes=self.config['sync']['interval_minutes']
            )

            if not guests:
                self.logger.info("No new check-ins found")
                return

            self.logger.info(f"Found {len(guests)} new check-ins")

            # 2. Transform to cloud format
            guest_data = [
                GuestData.from_firebird(g, self.config['cloud']['organization_id'])
                for g in guests
            ]

            # 3. Send to cloud in batches
            batch_size = self.config['sync']['batch_size']
            for i in range(0, len(guest_data), batch_size):
                batch = guest_data[i:i+batch_size]
                self.logger.info(f"Syncing batch {i//batch_size + 1}...")

                success = self.cloud_client.sync_guests(batch)
                if success:
                    self.logger.info(f"Batch synced successfully")
                else:
                    self.logger.error(f"Failed to sync batch")

        except Exception as e:
            self.logger.error(f"Error syncing guest data: {e}", exc_info=True)

    def sync_room_status(self):
        """Sync room availability from Firebird to cloud"""
        try:
            self.logger.info("Querying room status from Firebird...")
            rooms = self.firebird_reader.get_room_status()

            if not rooms:
                self.logger.warning("No room data found")
                return

            self.logger.info(f"Found {len(rooms)} rooms")

            # Transform and send
            room_data = [
                RoomStatus.from_firebird(r, self.config['cloud']['organization_id'])
                for r in rooms
            ]

            success = self.cloud_client.sync_rooms(room_data)
            if success:
                self.logger.info(f"Room status synced successfully")
            else:
                self.logger.error(f"Failed to sync room status")

        except Exception as e:
            self.logger.error(f"Error syncing room status: {e}", exc_info=True)

    def run_sync_cycle(self):
        """Run one complete sync cycle"""
        self.logger.info("=" * 60)
        self.logger.info(f"Starting sync cycle at {datetime.now()}")

        # Test connection first
        if not self.cloud_client.test_connection():
            self.logger.error("Cannot connect to cloud backend!")
            return

        # Sync guest data (check-ins)
        self.sync_guest_data()

        # Sync room status
        self.sync_room_status()

        self.logger.info("Sync cycle completed")
        self.logger.info("=" * 60)

    def start(self):
        """Start the agent daemon"""
        self.running = True
        interval = self.config['sync']['interval_minutes'] * 60  # Convert to seconds

        self.logger.info("Firebird Bridge Agent starting...")
        self.logger.info(f"Sync interval: {self.config['sync']['interval_minutes']} minutes")
        self.logger.info(f"Cloud API: {self.config['cloud']['api_url']}")
        self.logger.info(f"Organization ID: {self.config['cloud']['organization_id']}")

        # Initialize services
        self.initialize_services()

        # Run initial sync
        self.run_sync_cycle()

        # Run periodic sync
        while self.running:
            try:
                time.sleep(interval)
                self.run_sync_cycle()
            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal, stopping...")
                self.stop()
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}", exc_info=True)
                time.sleep(60)  # Wait 1 minute before retry

    def stop(self):
        """Stop the agent gracefully"""
        self.logger.info("Stopping Firebird Bridge Agent...")
        self.running = False
        if self.firebird_reader:
            self.firebird_reader.close()
        self.logger.info("Agent stopped")


def main():
    """Main entry point"""
    agent = FirebirdBridgeAgent()

    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        agent.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the agent
    agent.start()


if __name__ == "__main__":
    main()
