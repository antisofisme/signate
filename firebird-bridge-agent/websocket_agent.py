#!/usr/bin/env python3
"""
Firebird Bridge Agent - WebSocket Version
Real-time sync using WebSocket connection to cloud backend
"""

import asyncio
import json
import logging
import signal
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional

import websockets
from websockets.exceptions import ConnectionClosed

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from table_mapper import TableMapper
from models import GuestData, RoomStatus

class WebSocketBridgeAgent:
    """WebSocket-based Bridge Agent for real-time sync"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self.load_config(config_path)
        self.running = False
        self.websocket = None
        self.table_mapper: Optional[TableMapper] = None
        self.setup_logging()

    def load_config(self, path: str) -> dict:
        """Load configuration from YAML file"""
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config['logging']
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
        self.logger = logging.getLogger('WebSocketBridge')

    def get_websocket_url(self) -> str:
        """Get WebSocket URL from API URL"""
        api_url = self.config['cloud']['api_url']
        # Convert http:// to ws:// or https:// to wss://
        ws_url = api_url.replace('http://', 'ws://').replace('https://', 'wss://')
        # Remove /api/v1 suffix and add /ws/pms/sync
        ws_url = ws_url.replace('/api/v1', '') + '/ws/pms/sync'
        return ws_url

    async def connect_websocket(self):
        """Establish WebSocket connection to cloud backend"""
        ws_url = self.get_websocket_url()

        headers = {
            'X-API-Key': self.config['cloud']['api_key'],
            'X-Organization-ID': str(self.config['cloud']['organization_id'])
        }

        self.logger.info(f"Connecting to WebSocket: {ws_url}")

        try:
            self.websocket = await websockets.connect(
                ws_url,
                extra_headers=headers,
                ping_interval=30,
                ping_timeout=10
            )
            self.logger.info("✓ WebSocket connected")
            return True
        except Exception as e:
            self.logger.error(f"✗ WebSocket connection failed: {e}")
            return False

    async def send_guests(self, guests_data: list):
        """Send guest data via WebSocket"""
        if not self.websocket:
            self.logger.error("WebSocket not connected")
            return False

        try:
            message = {
                'type': 'sync_guests',
                'data': {
                    'guests': [g.to_dict() for g in guests_data],
                    'timestamp': datetime.now().isoformat()
                }
            }

            await self.websocket.send(json.dumps(message))
            self.logger.info(f"Sent {len(guests_data)} guests")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send guests: {e}")
            return False

    async def send_rooms(self, rooms_data: list):
        """Send room data via WebSocket"""
        if not self.websocket:
            self.logger.error("WebSocket not connected")
            return False

        try:
            message = {
                'type': 'sync_rooms',
                'data': {
                    'rooms': [r.to_dict() for r in rooms_data],
                    'timestamp': datetime.now().isoformat()
                }
            }

            await self.websocket.send(json.dumps(message))
            self.logger.info(f"Sent {len(rooms_data)} rooms")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send rooms: {e}")
            return False

    async def sync_data(self):
        """Query Firebird and sync data using configured table mappings"""
        try:
            org_id = self.config['cloud']['organization_id']

            # Sync guests if enabled
            if self.config['tables']['guest_table']['enabled']:
                self.logger.info("Syncing guest data...")
                guest_config = self.config['tables']['guest_table']

                if not guest_config['table_name']:
                    self.logger.warning("Guest table not configured, skipping")
                else:
                    guests = self.table_mapper.query_guests_from_mapping(
                        guest_config,
                        minutes=self.config['sync']['interval_minutes']
                    )

                    if guests:
                        self.logger.info(f"Found {len(guests)} guest records")
                        guest_data = [
                            GuestData.from_firebird(g, org_id)
                            for g in guests
                        ]
                        await self.send_guests(guest_data)
                    else:
                        self.logger.info("No new guest records found")
            else:
                self.logger.info("Guest sync disabled")

            # Sync rooms if enabled
            if self.config['tables']['room_table']['enabled']:
                self.logger.info("Syncing room data...")
                room_config = self.config['tables']['room_table']

                if not room_config['table_name']:
                    self.logger.warning("Room table not configured, skipping")
                else:
                    rooms = self.table_mapper.query_rooms_from_mapping(room_config)

                    if rooms:
                        self.logger.info(f"Found {len(rooms)} room records")
                        room_data = [
                            RoomStatus.from_firebird(r, org_id)
                            for r in rooms
                        ]
                        await self.send_rooms(room_data)
                    else:
                        self.logger.warning("No room records found")
            else:
                self.logger.info("Room sync disabled")

        except Exception as e:
            self.logger.error(f"Error during sync: {e}", exc_info=True)

    async def handle_server_message(self, message: str):
        """Handle incoming messages from server"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')

            if msg_type == 'ack':
                self.logger.info(f"Server acknowledged: {data.get('message')}")
            elif msg_type == 'sync_request':
                self.logger.info("Server requested sync")
                await self.sync_data()
            elif msg_type == 'error':
                self.logger.error(f"Server error: {data.get('message')}")
            else:
                self.logger.warning(f"Unknown message type: {msg_type}")

        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON received: {message}")

    async def listen_for_messages(self):
        """Listen for messages from server"""
        try:
            async for message in self.websocket:
                await self.handle_server_message(message)
        except ConnectionClosed:
            self.logger.warning("WebSocket connection closed")
        except Exception as e:
            self.logger.error(f"Error listening for messages: {e}")

    async def periodic_sync(self):
        """Periodic sync task"""
        interval = self.config['sync']['interval_minutes'] * 60

        while self.running:
            self.logger.info("=" * 60)
            self.logger.info(f"Starting sync cycle at {datetime.now()}")

            await self.sync_data()

            self.logger.info("Sync cycle completed")
            self.logger.info("=" * 60)

            await asyncio.sleep(interval)

    async def run(self):
        """Main run loop"""
        self.running = True

        self.logger.info("=" * 80)
        self.logger.info("Firebird Bridge Agent (WebSocket) starting...")
        self.logger.info(f"Sync interval: {self.config['sync']['interval_minutes']} minutes")
        self.logger.info(f"Organization ID: {self.config['cloud']['organization_id']}")
        self.logger.info("=" * 80)

        # Initialize Table Mapper
        try:
            self.table_mapper = TableMapper(self.config['firebird'])
            self.table_mapper.connect()
        except Exception as e:
            self.logger.error(f"Failed to initialize Table Mapper: {e}")
            return

        # Connect to WebSocket
        if not await self.connect_websocket():
            self.logger.error("Cannot start agent without WebSocket connection")
            return

        # Run periodic sync and message listener concurrently
        try:
            await asyncio.gather(
                self.periodic_sync(),
                self.listen_for_messages()
            )
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, stopping...")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            await self.stop()

    async def stop(self):
        """Stop the agent gracefully"""
        self.logger.info("Stopping Firebird Bridge Agent...")
        self.running = False

        if self.websocket:
            await self.websocket.close()
            self.logger.info("WebSocket connection closed")

        if self.table_mapper:
            self.table_mapper.close()

        self.logger.info("Agent stopped")


async def main():
    """Main entry point"""
    agent = WebSocketBridgeAgent()

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()

    def signal_handler():
        loop.create_task(agent.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # Start the agent
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
