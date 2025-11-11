"""
Table Mapper
Dynamic query builder based on user-selected tables and column mappings
"""

import fdb
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class TableMapper:
    """Map Firebird tables to guest/room data structures"""

    def __init__(self, config: dict):
        self.config = config
        self.connection: Optional[fdb.Connection] = None
        self.logger = logging.getLogger('TableMapper')

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

    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all columns for a specific table"""
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()

        query = """
            SELECT
                r.RDB$FIELD_NAME AS field_name,
                f.RDB$FIELD_TYPE AS field_type,
                f.RDB$FIELD_LENGTH AS field_length
            FROM RDB$RELATION_FIELDS r
            LEFT JOIN RDB$FIELDS f ON r.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
            WHERE r.RDB$RELATION_NAME = ?
            ORDER BY r.RDB$FIELD_POSITION
        """

        type_map = {
            7: 'SMALLINT', 8: 'INTEGER', 10: 'FLOAT', 12: 'DATE',
            13: 'TIME', 14: 'CHAR', 16: 'BIGINT', 27: 'DOUBLE',
            35: 'TIMESTAMP', 37: 'VARCHAR', 261: 'BLOB'
        }

        try:
            cursor.execute(query, (table_name,))
            columns = []

            for row in cursor.fetchall():
                field_name = row[0].strip()
                field_type = type_map.get(row[1], f'TYPE_{row[1]}')
                field_length = row[2]

                if field_type in ['CHAR', 'VARCHAR'] and field_length:
                    field_type = f'{field_type}({field_length})'

                columns.append({
                    'name': field_name,
                    'type': field_type
                })

            cursor.close()
            return columns
        except Exception as e:
            self.logger.error(f"Error getting columns for {table_name}: {e}")
            cursor.close()
            return []

    def query_custom_table(
        self,
        table_name: str,
        column_mapping: Dict[str, str],
        where_clause: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query custom table with column mapping

        Args:
            table_name: Name of table to query
            column_mapping: Dict mapping target fields to source columns
                Example: {'guest_name': 'NAME_COLUMN', 'room_number': 'ROOM_COL'}
            where_clause: Optional WHERE clause (without WHERE keyword)
            limit: Maximum records to return

        Returns:
            List of mapped records
        """
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()

        # Build SELECT clause
        select_columns = []
        for target_field, source_column in column_mapping.items():
            select_columns.append(f"{source_column} AS {target_field}")

        select_clause = ", ".join(select_columns)

        # Build full query
        query = f"SELECT FIRST {limit} {select_clause} FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"

        try:
            self.logger.info(f"Executing: {query}")
            cursor.execute(query)

            columns = [desc[0].strip() for desc in cursor.description]
            results = []

            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            cursor.close()
            return results
        except Exception as e:
            self.logger.error(f"Error querying {table_name}: {e}")
            cursor.close()
            return []

    def query_guests_from_mapping(
        self,
        table_config: Dict[str, Any],
        minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query guest data using user-defined table and column mapping

        Args:
            table_config: Configuration for guest table
                {
                    'table_name': 'GUESTS',
                    'columns': {
                        'guest_name': 'GUEST_NAME_COL',
                        'room_number': 'ROOM_NO_COL',
                        'checkin_date': 'CHECKIN_DATE_COL',
                        'checkout_date': 'CHECKOUT_DATE_COL',
                        'email': 'EMAIL_COL',
                        'phone': 'PHONE_COL',
                        'country': 'COUNTRY_COL',
                        'reservation_no': 'RESERVATION_COL'
                    },
                    'where_clause': 'STATUS = ''CHECKED_IN'' AND CHECKIN_DATE >= ?'
                }
            minutes: Minutes to look back

        Returns:
            List of guest records with standard field names
        """
        table_name = table_config['table_name']
        column_mapping = table_config['columns']
        where_template = table_config.get('where_clause', '')

        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()

        # Build SELECT clause
        select_columns = []
        for target_field, source_column in column_mapping.items():
            if source_column:  # Only include if column is mapped
                select_columns.append(f"{source_column} AS {target_field}")

        select_clause = ", ".join(select_columns)

        # Build query
        query = f"SELECT {select_clause} FROM {table_name}"
        if where_template:
            query += f" WHERE {where_template}"

        try:
            # Calculate time threshold
            threshold = datetime.now() - timedelta(minutes=minutes)

            # Execute with parameters if needed
            if '?' in where_template:
                cursor.execute(query, (threshold,))
            else:
                cursor.execute(query)

            columns = [desc[0].strip().lower() for desc in cursor.description]
            results = []

            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            cursor.close()
            return results
        except Exception as e:
            self.logger.error(f"Error querying guests from {table_name}: {e}")
            cursor.close()
            return []

    def query_rooms_from_mapping(
        self,
        table_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Query room data using user-defined table and column mapping

        Args:
            table_config: Configuration for room table
                {
                    'table_name': 'ROOMS',
                    'columns': {
                        'room_number': 'ROOM_NO_COL',
                        'room_type': 'TYPE_COL',
                        'status': 'STATUS_COL',
                        'floor': 'FLOOR_COL',
                        'bed_type': 'BED_TYPE_COL',
                        'max_occupancy': 'MAX_GUESTS_COL'
                    },
                    'where_clause': ''  # Optional
                }

        Returns:
            List of room records with standard field names
        """
        table_name = table_config['table_name']
        column_mapping = table_config['columns']
        where_clause = table_config.get('where_clause', '')

        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()

        # Build SELECT clause
        select_columns = []
        for target_field, source_column in column_mapping.items():
            if source_column:  # Only include if column is mapped
                select_columns.append(f"{source_column} AS {target_field}")

        select_clause = ", ".join(select_columns)

        # Build query
        query = f"SELECT {select_clause} FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        query += f" ORDER BY {column_mapping.get('room_number', 'RDB$DB_KEY')}"

        try:
            cursor.execute(query)

            columns = [desc[0].strip().lower() for desc in cursor.description]
            results = []

            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            cursor.close()
            return results
        except Exception as e:
            self.logger.error(f"Error querying rooms from {table_name}: {e}")
            cursor.close()
            return []

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.logger.info("Firebird connection closed")
