"""
Firebird Database Reader
Connects to local Firebird PMS and extracts guest/room data
"""

import fdb
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


class FirebirdReader:
    """Read data from Firebird PMS database"""

    def __init__(self, config: dict):
        self.config = config
        self.connection: Optional[fdb.Connection] = None
        self.logger = logging.getLogger('FirebirdReader')
        self.connect()

    def connect(self):
        """Establish connection to Firebird database"""
        try:
            self.connection = fdb.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database_path'],
                user=self.config['username'],
                password=self.config['password'],
                charset=self.config['charset']
            )
            self.logger.info("Connected to Firebird database")
        except Exception as e:
            self.logger.error(f"Failed to connect to Firebird: {e}")
            raise

    def get_recent_checkins(self, minutes: int = 5) -> List[Dict[str, Any]]:
        """
        Get guest check-ins from last N minutes

        Assumes Firebird PMS has table structure like:
        GUESTS (GUEST_ID, GUEST_NAME, ROOM_NO, CHECKIN_DATE, CHECKOUT_DATE, ...)

        IMPORTANT: Adjust table/column names to match your actual PMS schema!
        """
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()

        # Calculate time threshold
        threshold = datetime.now() - timedelta(minutes=minutes)

        # Query (adjust table/column names to match your PMS schema)
        query = """
            SELECT
                GUEST_ID,
                GUEST_NAME,
                ROOM_NO,
                CHECKIN_DATE,
                CHECKOUT_DATE,
                GUEST_EMAIL,
                GUEST_PHONE,
                GUEST_COUNTRY,
                RESERVATION_NO
            FROM GUESTS
            WHERE CHECKIN_DATE >= ?
            AND STATUS = 'CHECKED_IN'
            ORDER BY CHECKIN_DATE DESC
        """

        try:
            cursor.execute(query, (threshold,))
            columns = [desc[0] for desc in cursor.description]
            results = []

            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return results
        except Exception as e:
            self.logger.error(f"Error querying check-ins: {e}")
            return []
        finally:
            cursor.close()

    def get_room_status(self) -> List[Dict[str, Any]]:
        """
        Get current room availability status

        Assumes table structure like:
        ROOMS (ROOM_NO, ROOM_TYPE, STATUS, FLOOR, ...)

        IMPORTANT: Adjust table/column names to match your actual PMS schema!
        """
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()

        query = """
            SELECT
                ROOM_NO,
                ROOM_TYPE,
                STATUS,
                FLOOR,
                BED_TYPE,
                MAX_OCCUPANCY
            FROM ROOMS
            ORDER BY ROOM_NO
        """

        try:
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = []

            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return results
        except Exception as e:
            self.logger.error(f"Error querying room status: {e}")
            return []
        finally:
            cursor.close()

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.logger.info("Firebird connection closed")
