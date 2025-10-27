"""
Firebird Database Service
Connection pooling and query execution for Firebird databases

This service provides:
- Thread-safe connection pooling for multiple Firebird configurations
- Secure credential encryption/decryption
- Read-only query execution
- Connection health monitoring
- Automatic reconnection on failures
"""

import fdb
import time
import logging
from queue import Queue, Empty
from contextlib import contextmanager
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from threading import Lock
from cryptography.fernet import Fernet

from app.core.config import settings
from app.models.firebird import FirebirdConfig

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Service for encrypting/decrypting sensitive data
    Uses Fernet symmetric encryption from cryptography library
    """

    def __init__(self, encryption_key: str):
        """
        Initialize encryption service

        Args:
            encryption_key: Base64-encoded Fernet key
        """
        try:
            # Ensure key is bytes
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()

            # Generate a valid Fernet key if the provided one is invalid
            try:
                self.cipher = Fernet(encryption_key)
            except Exception:
                # If invalid, generate a new key from the provided string
                # Use SHA256 hash and base64 encode to get valid Fernet key
                import hashlib
                import base64
                key_hash = hashlib.sha256(encryption_key).digest()
                fernet_key = base64.urlsafe_b64encode(key_hash)
                self.cipher = Fernet(fernet_key)
                logger.warning("Generated Fernet key from encryption_key string")

        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string

        Args:
            plaintext: String to encrypt

        Returns:
            Encrypted string (base64 encoded)
        """
        try:
            encrypted_bytes = self.cipher.encrypt(plaintext.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext string

        Args:
            ciphertext: Encrypted string (base64 encoded)

        Returns:
            Decrypted plaintext string
        """
        try:
            decrypted_bytes = self.cipher.decrypt(ciphertext.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise


class FirebirdConnectionPool:
    """
    Thread-safe connection pool for Firebird database
    Manages a fixed pool of connections with automatic recovery
    """

    def __init__(
        self,
        dsn: str,
        user: str,
        password: str,
        charset: str = 'UTF8',
        max_connections: int = 5,
        connection_timeout: int = 10
    ):
        """
        Initialize connection pool

        Args:
            dsn: Data Source Name (server mode: "host:port/path" or embedded: "path")
            user: Database username
            password: Database password
            charset: Character set (default: UTF8)
            max_connections: Maximum number of connections in pool (default: 5)
            connection_timeout: Connection timeout in seconds (default: 10)
        """
        self.dsn = dsn
        self.user = user
        self.password = password
        self.charset = charset
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout

        self.pool: Queue = Queue(maxsize=max_connections)
        self.pool_lock = Lock()
        self.total_connections = 0
        self.active_connections = 0

        # Create initial connections
        self._initialize_pool()

        logger.info(f"Firebird connection pool initialized: DSN={dsn}, Max={max_connections}")

    def _initialize_pool(self):
        """Create initial connections and populate pool"""
        try:
            for _ in range(self.max_connections):
                conn = self._create_connection()
                self.pool.put(conn)
                self.total_connections += 1
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    def _create_connection(self) -> fdb.Connection:
        """
        Create a new Firebird database connection

        Returns:
            fdb.Connection: New database connection

        Raises:
            Exception: If connection fails
        """
        try:
            conn = fdb.connect(
                dsn=self.dsn,
                user=self.user,
                password=self.password,
                charset=self.charset
            )
            logger.debug(f"Created new Firebird connection to {self.dsn}")
            return conn
        except Exception as e:
            logger.error(f"Failed to create Firebird connection: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool (context manager)

        Usage:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM TABLE")

        Yields:
            fdb.Connection: Database connection from pool

        Raises:
            Exception: If no connection available or connection failed
        """
        conn = None
        try:
            # Get connection from pool (wait up to connection_timeout seconds)
            conn = self.pool.get(timeout=self.connection_timeout)

            with self.pool_lock:
                self.active_connections += 1

            # Test if connection is still alive
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM RDB$DATABASE")
                cursor.fetchone()
                cursor.close()
            except Exception as e:
                logger.warning(f"Connection test failed, creating new connection: {e}")
                try:
                    conn.close()
                except:
                    pass
                conn = self._create_connection()

            yield conn

        except Empty:
            logger.error("Connection pool timeout - no connections available")
            raise Exception("Connection pool exhausted - all connections in use")

        except Exception as e:
            logger.error(f"Error getting connection from pool: {e}")
            raise

        finally:
            # Return connection to pool
            if conn:
                try:
                    # Rollback any uncommitted transactions
                    conn.rollback()
                    self.pool.put(conn)
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")
                    # Try to create a new connection if this one is broken
                    try:
                        new_conn = self._create_connection()
                        self.pool.put(new_conn)
                    except Exception as e2:
                        logger.error(f"Failed to create replacement connection: {e2}")

                with self.pool_lock:
                    self.active_connections -= 1

    def get_pool_status(self) -> Dict[str, int]:
        """
        Get current pool status

        Returns:
            Dict with pool statistics
        """
        with self.pool_lock:
            return {
                "total_connections": self.total_connections,
                "available_connections": self.pool.qsize(),
                "active_connections": self.active_connections,
                "max_connections": self.max_connections
            }

    def close_all(self):
        """Close all connections in the pool"""
        logger.info("Closing all connections in pool")
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
                self.total_connections -= 1
            except Empty:
                break
            except Exception as e:
                logger.error(f"Error closing connection: {e}")


class FirebirdService:
    """
    Singleton service for managing multiple Firebird database connections
    Provides connection pooling, query execution, and health monitoring
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Singleton pattern - only one instance allowed"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Firebird service"""
        if not hasattr(self, '_initialized'):
            self.pools: Dict[int, FirebirdConnectionPool] = {}
            self.pools_lock = Lock()
            self.encryption_service = EncryptionService(settings.ENCRYPTION_KEY)
            self._initialized = True
            logger.info("FirebirdService initialized")

    def _parse_credentials(self, api_key_encrypted: str) -> Tuple[str, str]:
        """
        Parse and decrypt API key to get username and password

        Args:
            api_key_encrypted: Encrypted "username:password" string

        Returns:
            Tuple of (username, password)

        Raises:
            ValueError: If API key format is invalid
        """
        try:
            # Decrypt the API key
            api_key = self.encryption_service.decrypt(api_key_encrypted)

            # Split into username:password
            if ':' not in api_key:
                raise ValueError("API key must be in format 'username:password'")

            parts = api_key.split(':', 1)
            if len(parts) != 2:
                raise ValueError("Invalid API key format")

            return parts[0], parts[1]

        except Exception as e:
            logger.error(f"Failed to parse credentials: {e}")
            raise

    def encrypt_api_key(self, api_key: str) -> str:
        """
        Encrypt API key for storage

        Args:
            api_key: Plaintext "username:password" string

        Returns:
            Encrypted API key string
        """
        return self.encryption_service.encrypt(api_key)

    def get_or_create_pool(self, config: FirebirdConfig) -> FirebirdConnectionPool:
        """
        Get existing connection pool or create new one

        Args:
            config: FirebirdConfig model instance

        Returns:
            FirebirdConnectionPool instance

        Raises:
            Exception: If pool creation fails
        """
        with self.pools_lock:
            # Check if pool already exists
            if config.id in self.pools:
                return self.pools[config.id]

            # Parse credentials
            username, password = self._parse_credentials(config.api_key)

            # Create new pool
            try:
                pool = FirebirdConnectionPool(
                    dsn=config.api_endpoint,
                    user=username,
                    password=password,
                    charset='UTF8',
                    max_connections=5,
                    connection_timeout=10
                )

                self.pools[config.id] = pool
                logger.info(f"Created connection pool for config_id={config.id}")
                return pool

            except Exception as e:
                logger.error(f"Failed to create connection pool for config_id={config.id}: {e}")
                raise

    def remove_pool(self, config_id: int):
        """
        Remove and close connection pool

        Args:
            config_id: Configuration ID
        """
        with self.pools_lock:
            if config_id in self.pools:
                pool = self.pools[config_id]
                pool.close_all()
                del self.pools[config_id]
                logger.info(f"Removed connection pool for config_id={config_id}")

    async def test_connection(
        self,
        config: FirebirdConfig,
        test_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Test database connection and optionally execute a test query

        Args:
            config: FirebirdConfig model instance
            test_query: Optional SELECT query to test (default: "SELECT 1 FROM RDB$DATABASE")

        Returns:
            Dictionary with test results
        """
        start_time = time.time()
        result = {
            "success": False,
            "message": "",
            "connection_time_ms": 0.0,
            "test_query_executed": False,
            "error_details": None
        }

        try:
            # Get or create pool
            pool = self.get_or_create_pool(config)

            # Test connection
            with pool.get_connection() as conn:
                connection_time = (time.time() - start_time) * 1000

                # Execute test query if provided
                if test_query:
                    cursor = conn.cursor()
                    cursor.execute(test_query)
                    cursor.fetchone()
                    cursor.close()
                    result["test_query_executed"] = True

                result["success"] = True
                result["message"] = "Connection successful"
                result["connection_time_ms"] = round(connection_time, 2)

        except Exception as e:
            result["message"] = f"Connection failed: {str(e)}"
            result["error_details"] = str(e)
            logger.error(f"Connection test failed for config_id={config.id}: {e}")

        return result

    async def execute_query(
        self,
        config: FirebirdConfig,
        query: str,
        max_rows: int = 100
    ) -> Dict[str, Any]:
        """
        Execute a read-only SELECT query

        Args:
            config: FirebirdConfig model instance
            query: SQL SELECT query to execute
            max_rows: Maximum number of rows to return (default: 100)

        Returns:
            Dictionary with query results
        """
        start_time = time.time()
        result = {
            "success": False,
            "row_count": 0,
            "columns": [],
            "rows": [],
            "execution_time_ms": 0.0,
            "message": "",
            "error_details": None
        }

        try:
            # Get or create pool
            pool = self.get_or_create_pool(config)

            # Execute query
            with pool.get_connection() as conn:
                cursor = conn.cursor()

                # Execute query with FIRST clause to limit rows
                # Firebird uses FIRST instead of LIMIT
                query_with_limit = query.strip()
                query_upper = query_with_limit.upper()

                # Add FIRST clause if not present and not using FIRST/ROWS
                if 'FIRST' not in query_upper and 'ROWS' not in query_upper:
                    # Insert FIRST after SELECT
                    if query_upper.startswith('SELECT'):
                        query_with_limit = f"SELECT FIRST {max_rows} " + query_with_limit[6:]

                cursor.execute(query_with_limit)

                # Get column names
                columns = [desc[0] for desc in cursor.description]

                # Fetch rows
                rows = []
                for row in cursor.fetchall():
                    row_dict = {}
                    for i, col_name in enumerate(columns):
                        value = row[i]
                        # Convert datetime objects to ISO format
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        row_dict[col_name] = value
                    rows.append(row_dict)

                cursor.close()

                execution_time = (time.time() - start_time) * 1000

                result["success"] = True
                result["row_count"] = len(rows)
                result["columns"] = columns
                result["rows"] = rows
                result["execution_time_ms"] = round(execution_time, 2)
                result["message"] = f"Query executed successfully, {len(rows)} rows returned"

        except Exception as e:
            result["message"] = f"Query execution failed: {str(e)}"
            result["error_details"] = str(e)
            logger.error(f"Query execution failed for config_id={config.id}: {e}")

        return result

    async def health_check(self, config: FirebirdConfig) -> Dict[str, Any]:
        """
        Check connection health and pool status

        Args:
            config: FirebirdConfig model instance

        Returns:
            Dictionary with health status
        """
        result = {
            "config_id": config.id,
            "config_key": config.config_key,
            "is_healthy": False,
            "connection_status": "disconnected",
            "pool_status": None,
            "last_check": datetime.utcnow(),
            "error_message": None
        }

        try:
            # Check if pool exists
            with self.pools_lock:
                if config.id not in self.pools:
                    result["connection_status"] = "no_pool"
                    result["error_message"] = "Connection pool not initialized"
                    return result

                pool = self.pools[config.id]

            # Get pool status
            result["pool_status"] = pool.get_pool_status()

            # Test connection
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM RDB$DATABASE")
                cursor.fetchone()
                cursor.close()

                result["is_healthy"] = True
                result["connection_status"] = "connected"

        except Exception as e:
            result["connection_status"] = "error"
            result["error_message"] = str(e)
            logger.error(f"Health check failed for config_id={config.id}: {e}")

        return result

    def shutdown(self):
        """Shutdown service and close all connection pools"""
        logger.info("Shutting down FirebirdService")
        with self.pools_lock:
            for config_id, pool in self.pools.items():
                try:
                    pool.close_all()
                except Exception as e:
                    logger.error(f"Error closing pool for config_id={config_id}: {e}")
            self.pools.clear()


# Create singleton instance
firebird_service = FirebirdService()
