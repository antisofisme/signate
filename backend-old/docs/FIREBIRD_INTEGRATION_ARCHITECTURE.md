# Firebird Database Integration Architecture

## Overview
This document outlines the architecture for integrating Firebird database read-only access into the digital signage system. The integration provides secure, efficient, and scalable access to external Firebird databases for retrieving guest information and other relevant data.

## Architecture Principles
- **Read-Only Access**: All database operations are strictly SELECT queries
- **Connection Pooling**: Efficient resource management with configurable pool size
- **Thread Safety**: Concurrent request handling with proper synchronization
- **Graceful Degradation**: System continues to function even if Firebird connection fails
- **Security First**: Encrypted credentials, SQL injection prevention, audit logging

## System Components

### 1. Database Schema

#### Firebird Configuration Table
```sql
-- Migration: 006_create_firebird_config.sql
CREATE TABLE IF NOT EXISTS firebird_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(50) UNIQUE NOT NULL,

    -- Connection Settings
    host VARCHAR(255),                     -- Server hostname/IP (NULL for embedded mode)
    port INTEGER DEFAULT 3050,             -- Server port (ignored in embedded mode)
    database_path VARCHAR(500) NOT NULL,   -- Full path to .fdb file
    username VARCHAR(100) NOT NULL,        -- Firebird username
    password VARCHAR(255) NOT NULL,        -- Encrypted password
    charset VARCHAR(50) DEFAULT 'UTF8',    -- Character encoding
    connection_mode VARCHAR(20) DEFAULT 'server', -- 'server' or 'embedded'

    -- Pool Configuration
    max_connections INTEGER DEFAULT 5,      -- Maximum pool size
    connection_timeout INTEGER DEFAULT 30,  -- Seconds to wait for connection
    query_timeout INTEGER DEFAULT 60,       -- Maximum query execution time

    -- Settings
    refresh_interval INTEGER DEFAULT 300,   -- Data refresh interval in seconds
    is_active BOOLEAN DEFAULT TRUE,

    -- Health Monitoring
    last_sync TIMESTAMP WITH TIME ZONE,
    last_error TEXT,
    error_count INTEGER DEFAULT 0,
    last_health_check TIMESTAMP WITH TIME ZONE,

    -- Additional Configuration
    config_json TEXT,                       -- JSON for table mappings, query templates
    notes TEXT,

    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Indexes
    INDEX idx_firebird_config_active (is_active),
    INDEX idx_firebird_config_key (config_key)
);

-- Audit Log Table
CREATE TABLE IF NOT EXISTS firebird_query_log (
    id SERIAL PRIMARY KEY,
    config_id INTEGER REFERENCES firebird_config(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    execution_time_ms INTEGER,
    row_count INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    executed_by VARCHAR(100),

    -- Indexes for performance
    INDEX idx_firebird_log_config (config_id),
    INDEX idx_firebird_log_time (executed_at),
    INDEX idx_firebird_log_success (success)
);
```

### 2. Service Layer Architecture

#### FirebirdService Class Structure
```python
# backend/app/services/firebird_service.py

class FirebirdConnectionPool:
    """
    Thread-safe connection pool manager

    Responsibilities:
    - Maintain pool of reusable connections
    - Handle connection lifecycle (create, validate, dispose)
    - Implement connection health checks
    - Auto-reconnect on failure
    """

    def __init__(self, config: FirebirdConfig):
        self.config = config
        self.pool = Queue(maxsize=config.max_connections)
        self.active_connections = []
        self._lock = threading.Lock()
        self._shutdown = False
        self._health_check_thread = None

    Methods:
    - get_connection() -> Connection (context manager)
    - _create_connection() -> fdb.Connection
    - _validate_connection(conn) -> bool
    - _return_connection(conn)
    - _health_check_loop()
    - shutdown()

class FirebirdService:
    """
    Singleton service for Firebird database operations

    Responsibilities:
    - Manage multiple Firebird configurations
    - Execute read-only queries
    - Handle query result transformation
    - Implement caching layer
    - Provide health status
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.pools = {}  # config_key -> ConnectionPool
        self.cache = {}   # Simple in-memory cache
        self._initialize_pools()

    Core Methods:
    - get_instance() -> FirebirdService (singleton)
    - initialize_pool(config_key: str) -> bool
    - execute_query(config_key: str, query: str, params: tuple) -> List[Dict]
    - test_connection(config_key: str) -> Dict
    - get_health_status(config_key: str) -> Dict
    - refresh_pool(config_key: str)
    - shutdown_pool(config_key: str)

    Query Methods:
    - fetch_guest_info(config_key: str, guest_id: str) -> Dict
    - fetch_table_data(config_key: str, table_name: str, limit: int) -> List[Dict]
    - execute_custom_query(config_key: str, query_template: str, params: Dict) -> List[Dict]

    Private Methods:
    - _initialize_pools()
    - _build_dsn(config: FirebirdConfig) -> str
    - _sanitize_query(query: str) -> str
    - _validate_read_only(query: str) -> bool
    - _transform_results(cursor) -> List[Dict]
    - _log_query(config_id: int, query: str, execution_time: float, success: bool)

class FirebirdQueryBuilder:
    """
    Safe query construction utility

    Responsibilities:
    - Build parameterized queries
    - Validate table/column names
    - Prevent SQL injection
    """

    Methods:
    - select(table: str, columns: List[str], conditions: Dict) -> Tuple[str, tuple]
    - validate_identifier(name: str) -> bool
    - escape_identifier(name: str) -> str
```

### 3. API Layer Structure

#### Endpoint Specifications

##### Configuration Management Endpoints
```yaml
# Configuration CRUD Operations

POST /api/firebird/configs
  Description: Create new Firebird configuration
  Request Body:
    - config_key: string (unique identifier)
    - host: string (optional for embedded mode)
    - port: integer (default 3050)
    - database_path: string (required)
    - username: string
    - password: string (will be encrypted)
    - connection_mode: enum ['server', 'embedded']
    - max_connections: integer (1-20)
    - config_json: object (optional)
  Response: Created configuration with ID
  Security: Admin role required

GET /api/firebird/configs
  Description: List all Firebird configurations
  Query Parameters:
    - is_active: boolean
    - limit: integer
    - offset: integer
  Response: Array of configurations (password excluded)
  Security: Admin role required

GET /api/firebird/configs/{config_key}
  Description: Get specific configuration details
  Response: Configuration object (password excluded)
  Security: Admin role required

PUT /api/firebird/configs/{config_key}
  Description: Update Firebird configuration
  Request Body: Same as POST (partial update allowed)
  Response: Updated configuration
  Security: Admin role required
  Note: Triggers pool refresh if connection params change

DELETE /api/firebird/configs/{config_key}
  Description: Delete Firebird configuration
  Response: 204 No Content
  Security: Admin role required
  Note: Closes all active connections
```

##### Connection Testing Endpoints
```yaml
POST /api/firebird/configs/{config_key}/test
  Description: Test connection with current configuration
  Response:
    - success: boolean
    - message: string
    - details:
        - connection_time_ms: integer
        - server_version: string
        - database_info: object
  Security: Admin role required

POST /api/firebird/test-connection
  Description: Test connection with provided credentials (without saving)
  Request Body: Same as config creation
  Response: Same as test endpoint
  Security: Admin role required
```

##### Data Query Endpoints
```yaml
GET /api/firebird/{config_key}/query
  Description: Execute custom SELECT query
  Request Body:
    - query: string (SELECT only)
    - params: object (named parameters)
    - limit: integer (max rows, default 1000)
  Response:
    - success: boolean
    - data: array of objects
    - row_count: integer
    - execution_time_ms: integer
  Security: Read permission required
  Validation: Query must be SELECT only

GET /api/firebird/{config_key}/tables
  Description: List available tables in database
  Response:
    - tables: array of table names
  Security: Admin role required

GET /api/firebird/{config_key}/tables/{table_name}
  Description: Fetch data from specific table
  Query Parameters:
    - limit: integer (default 100, max 1000)
    - offset: integer
    - sort: string (column name)
    - order: enum ['asc', 'desc']
  Response:
    - data: array of records
    - total: integer
    - columns: array of column definitions
  Security: Read permission required

GET /api/firebird/{config_key}/tables/{table_name}/schema
  Description: Get table schema information
  Response:
    - columns: array of column definitions
    - indexes: array of index definitions
    - row_count: integer
  Security: Admin role required
```

##### Health & Monitoring Endpoints
```yaml
GET /api/firebird/{config_key}/health
  Description: Get connection pool health status
  Response:
    - status: enum ['healthy', 'degraded', 'unhealthy']
    - pool_info:
        - total_connections: integer
        - active_connections: integer
        - idle_connections: integer
    - last_successful_query: timestamp
    - error_rate: float (last 5 minutes)
    - recent_errors: array
  Security: Admin role required

GET /api/firebird/{config_key}/logs
  Description: Get query execution logs
  Query Parameters:
    - start_date: datetime
    - end_date: datetime
    - success: boolean
    - limit: integer
  Response:
    - logs: array of query log entries
  Security: Admin role required

POST /api/firebird/{config_key}/refresh
  Description: Force refresh connection pool
  Response:
    - success: boolean
    - message: string
  Security: Admin role required
```

### 4. Security Architecture

#### Password Encryption
```python
# Using Fernet symmetric encryption
from cryptography.fernet import Fernet

class CredentialManager:
    """Handles secure storage and retrieval of credentials"""

    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key.encode())

    def encrypt_password(self, plain_password: str) -> str:
        """Encrypt password before storing in database"""
        return self.cipher.encrypt(plain_password.encode()).decode()

    def decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt password when creating connection"""
        return self.cipher.decrypt(encrypted_password.encode()).decode()
```

#### SQL Injection Prevention
```python
class QueryValidator:
    """Validates and sanitizes queries"""

    FORBIDDEN_KEYWORDS = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE',
        'ALTER', 'TRUNCATE', 'EXECUTE', 'EXEC', 'GRANT', 'REVOKE'
    ]

    def validate_read_only(self, query: str) -> bool:
        """Ensure query is read-only"""
        normalized = query.upper().strip()

        # Must start with SELECT
        if not normalized.startswith('SELECT'):
            return False

        # Check for forbidden keywords
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword in normalized:
                return False

        # Check for suspicious patterns
        if ';' in query and query.strip()[-1] != ';':
            return False  # Multiple statements

        return True

    def sanitize_identifier(self, identifier: str) -> str:
        """Sanitize table/column names"""
        # Only allow alphanumeric and underscore
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', identifier):
            raise ValueError(f"Invalid identifier: {identifier}")
        return identifier
```

#### Access Control
```python
class FirebirdAccessControl:
    """Role-based access control for Firebird operations"""

    PERMISSIONS = {
        'admin': ['config_create', 'config_update', 'config_delete',
                 'test_connection', 'view_logs', 'execute_query'],
        'operator': ['execute_query', 'view_data'],
        'viewer': ['view_data']
    }

    def check_permission(self, user_role: str, action: str) -> bool:
        """Check if role has permission for action"""
        return action in self.PERMISSIONS.get(user_role, [])
```

### 5. Error Handling Strategy

#### Error Categories
```python
class FirebirdError(Exception):
    """Base exception for Firebird operations"""
    pass

class ConnectionError(FirebirdError):
    """Connection-related errors"""
    pass

class QueryError(FirebirdError):
    """Query execution errors"""
    pass

class ConfigurationError(FirebirdError):
    """Configuration-related errors"""
    pass

class SecurityError(FirebirdError):
    """Security violation errors"""
    pass
```

#### Error Response Format
```json
{
    "error": {
        "type": "QueryError",
        "message": "Query execution failed",
        "details": {
            "query": "SELECT * FROM unknown_table",
            "error_code": -204,
            "firebird_message": "Table unknown_table not found"
        },
        "timestamp": "2024-10-27T10:30:00Z",
        "trace_id": "abc123"
    }
}
```

#### Retry Strategy
```python
class RetryPolicy:
    """Configurable retry behavior"""

    def __init__(self, max_retries=3, backoff_factor=2):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if operation should be retried"""
        if attempt >= self.max_retries:
            return False

        # Retry on connection errors
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True

        # Don't retry on security or query errors
        if isinstance(error, (SecurityError, QueryError)):
            return False

        return False

    def get_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay"""
        return self.backoff_factor ** attempt
```

### 6. Caching Strategy

#### Cache Implementation
```python
class FirebirdCache:
    """Simple TTL-based cache for query results"""

    def __init__(self, default_ttl=300):
        self.cache = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached value if not expired"""
        if key in self.cache:
            value, expiry = self.cache[key]
            if time.time() < expiry:
                return value
            del self.cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int = None):
        """Store value with TTL"""
        ttl = ttl or self.default_ttl
        self.cache[key] = (value, time.time() + ttl)

    def invalidate(self, pattern: str = None):
        """Invalidate cache entries"""
        if pattern:
            # Invalidate matching keys
            keys_to_delete = [k for k in self.cache if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]
        else:
            # Clear all
            self.cache.clear()
```

### 7. Health Monitoring

#### Health Check Implementation
```python
class HealthMonitor:
    """Monitor connection pool and query performance"""

    def __init__(self, pool: FirebirdConnectionPool):
        self.pool = pool
        self.metrics = {
            'queries_executed': 0,
            'queries_failed': 0,
            'total_execution_time': 0,
            'connection_failures': 0,
            'last_success': None,
            'last_failure': None
        }

    def check_health(self) -> Dict:
        """Perform health check"""
        status = 'healthy'
        issues = []

        # Check connection availability
        if self.pool.available_connections() == 0:
            status = 'degraded'
            issues.append('No available connections')

        # Check error rate
        error_rate = self.calculate_error_rate()
        if error_rate > 0.1:  # >10% errors
            status = 'unhealthy' if error_rate > 0.5 else 'degraded'
            issues.append(f'High error rate: {error_rate:.1%}')

        # Test query execution
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM RDB$DATABASE")
                cursor.close()
        except Exception as e:
            status = 'unhealthy'
            issues.append(f'Test query failed: {str(e)}')

        return {
            'status': status,
            'issues': issues,
            'metrics': self.metrics,
            'pool_stats': {
                'total': self.pool.max_connections,
                'available': self.pool.available_connections(),
                'in_use': self.pool.active_connections_count()
            }
        }
```

### 8. Integration Patterns

#### Dependency Injection
```python
# backend/app/core/dependencies.py

def get_firebird_service() -> FirebirdService:
    """Dependency injection for FastAPI"""
    return FirebirdService.get_instance()

# Usage in API endpoint
@router.get("/api/firebird/{config_key}/query")
async def execute_query(
    config_key: str,
    query_request: QueryRequest,
    service: FirebirdService = Depends(get_firebird_service),
    current_user: User = Depends(get_current_user)
):
    # Check permissions
    if not current_user.has_permission('execute_query'):
        raise HTTPException(403, "Insufficient permissions")

    # Execute query
    result = await service.execute_query(
        config_key,
        query_request.query,
        query_request.params
    )

    return result
```

#### Background Tasks
```python
# Periodic health checks
@repeat_every(seconds=60)
async def health_check_task():
    """Background task for health monitoring"""
    service = FirebirdService.get_instance()
    for config_key in service.get_active_configs():
        health = service.get_health_status(config_key)
        if health['status'] == 'unhealthy':
            # Send alert
            await send_admin_alert(f"Firebird connection {config_key} is unhealthy")

# Data synchronization
@repeat_every(seconds=300)
async def sync_data_task():
    """Periodic data synchronization"""
    service = FirebirdService.get_instance()
    for config in service.get_active_configs():
        if config.should_sync():
            await service.sync_data(config.config_key)
```

### 9. Configuration Examples

#### Server Mode Configuration
```json
{
    "config_key": "hotel_main",
    "host": "192.168.1.100",
    "port": 3050,
    "database_path": "/opt/firebird/data/HOTEL.FDB",
    "username": "SYSDBA",
    "password": "<encrypted>",
    "connection_mode": "server",
    "max_connections": 10,
    "config_json": {
        "tables": {
            "guests": "GUESTS",
            "reservations": "RESERVATIONS"
        },
        "queries": {
            "active_guests": "SELECT * FROM GUESTS WHERE STATUS = 'CHECKED_IN'"
        }
    }
}
```

#### Embedded Mode Configuration
```json
{
    "config_key": "local_db",
    "database_path": "C:\\Data\\LOCAL.FDB",
    "username": "SYSDBA",
    "password": "<encrypted>",
    "connection_mode": "embedded",
    "max_connections": 1,
    "config_json": {
        "read_only": true,
        "charset": "UTF8"
    }
}
```

### 10. Testing Strategy

#### Unit Tests
```python
# tests/test_firebird_service.py

class TestFirebirdService:
    def test_connection_pool_creation(self):
        """Test pool initialization"""

    def test_query_validation(self):
        """Test read-only query validation"""

    def test_connection_failure_handling(self):
        """Test graceful failure on connection error"""

    def test_query_sanitization(self):
        """Test SQL injection prevention"""

    def test_cache_functionality(self):
        """Test caching behavior"""
```

#### Integration Tests
```python
# tests/integration/test_firebird_integration.py

class TestFirebirdIntegration:
    def test_end_to_end_query_execution(self):
        """Test complete query flow"""

    def test_connection_pool_under_load(self):
        """Test concurrent connections"""

    def test_health_monitoring(self):
        """Test health check accuracy"""

    def test_error_recovery(self):
        """Test automatic reconnection"""
```

## Deployment Considerations

### Environment Variables
```bash
# .env configuration
FIREBIRD_ENCRYPTION_KEY=<base64_encoded_key>
FIREBIRD_MAX_GLOBAL_CONNECTIONS=50
FIREBIRD_HEALTH_CHECK_INTERVAL=60
FIREBIRD_CACHE_TTL=300
FIREBIRD_QUERY_LOG_ENABLED=true
FIREBIRD_QUERY_TIMEOUT=60
```

### Docker Configuration
```dockerfile
# Install Firebird client libraries
RUN apt-get update && apt-get install -y \
    firebird-dev \
    libfbclient2 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install fdb==2.0.2
```

### Resource Requirements
- **Memory**: ~50MB per connection pool
- **CPU**: Minimal overhead (query dependent)
- **Network**: Persistent connections to Firebird servers
- **Storage**: Query logs and cache (configurable)

## Migration Path

### Phase 1: Foundation (Week 1)
1. Create database migration for firebird_config table
2. Implement basic FirebirdService with connection pooling
3. Add configuration management endpoints
4. Implement password encryption

### Phase 2: Core Functionality (Week 2)
1. Implement query execution with validation
2. Add caching layer
3. Create health monitoring system
4. Add query logging and audit trail

### Phase 3: Integration (Week 3)
1. Integrate with existing authentication/authorization
2. Add background sync tasks
3. Implement admin UI for configuration
4. Create monitoring dashboard

### Phase 4: Optimization (Week 4)
1. Performance tuning and load testing
2. Add advanced caching strategies
3. Implement query templates and saved queries
4. Documentation and training

## Performance Benchmarks

### Expected Performance Metrics
- Connection establishment: <500ms
- Simple SELECT query: <100ms
- Complex JOIN query: <500ms
- Cache hit ratio: >80%
- Connection pool efficiency: >90%
- Concurrent request handling: 100+ req/sec

## Monitoring & Alerts

### Key Metrics to Track
- Connection pool utilization
- Query execution time (p50, p95, p99)
- Error rate by type
- Cache hit/miss ratio
- Active connections per configuration
- Failed authentication attempts

### Alert Thresholds
- Connection pool exhaustion: >90% utilized
- Query timeout rate: >5%
- Connection failure rate: >10%
- Health check failure: 3 consecutive failures
- Slow query: >5 seconds

## Security Best Practices

1. **Least Privilege**: Use read-only database users
2. **Encryption**: Always encrypt passwords at rest
3. **Validation**: Validate all input thoroughly
4. **Logging**: Log all queries for audit trail
5. **Rate Limiting**: Implement query rate limits per user
6. **Network Security**: Use SSL/TLS for connections
7. **Access Control**: Role-based permissions for all operations
8. **Monitoring**: Track and alert on suspicious patterns

## Appendix A: Common Query Patterns

### Guest Information Query
```sql
-- Parameterized query for guest lookup
SELECT
    G.GUEST_ID,
    G.FIRST_NAME,
    G.LAST_NAME,
    G.ROOM_NUMBER,
    R.CHECK_IN_DATE,
    R.CHECK_OUT_DATE,
    R.STATUS
FROM GUESTS G
JOIN RESERVATIONS R ON G.GUEST_ID = R.GUEST_ID
WHERE G.GUEST_ID = :guest_id
  AND R.STATUS = 'ACTIVE'
```

### Daily Report Query
```sql
-- Arrivals and departures for today
SELECT
    'ARRIVAL' as TYPE,
    COUNT(*) as COUNT
FROM RESERVATIONS
WHERE DATE(CHECK_IN_DATE) = CURRENT_DATE
UNION ALL
SELECT
    'DEPARTURE' as TYPE,
    COUNT(*) as COUNT
FROM RESERVATIONS
WHERE DATE(CHECK_OUT_DATE) = CURRENT_DATE
```

## Appendix B: Troubleshooting Guide

### Common Issues and Solutions

#### Connection Pool Exhausted
- **Symptom**: "No available connections" error
- **Solution**: Increase max_connections or optimize query execution time

#### Character Encoding Issues
- **Symptom**: Special characters displayed incorrectly
- **Solution**: Ensure charset configuration matches database encoding

#### Slow Query Performance
- **Symptom**: Queries taking >5 seconds
- **Solution**: Add appropriate indexes, optimize query structure

#### Authentication Failures
- **Symptom**: "Your user name and password are not defined"
- **Solution**: Verify credentials, check Firebird security database

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-10-27 | System Architect | Initial architecture document |

---

**Document Status**: FINAL
**Review Status**: Pending
**Implementation Status**: Not Started