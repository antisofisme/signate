# Firebird Database Integration

## Overview

This backend provides integration with Firebird databases for the Smart TV Digital Signage system. It enables secure, read-only access to external Firebird databases (such as hotel PMS systems) to fetch dynamic data for display.

## Features

- **Read-Only Access**: Only SELECT queries allowed, ensuring data safety
- **Connection Pooling**: Thread-safe connection pool management (5 connections per config)
- **Encrypted Credentials**: API keys (username:password) encrypted using Fernet
- **Multiple Configurations**: Support multiple Firebird database connections
- **Health Monitoring**: Real-time connection health checks and pool status
- **Query Validation**: SQL injection prevention through strict query validation
- **Automatic Reconnection**: Failed connections automatically recovered

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  FastAPI Backend                     │
│                                                       │
│  ┌─────────────────────────────────────────────┐   │
│  │      Firebird API Endpoints                  │   │
│  │   /api/firebird/configs/* (CRUD)            │   │
│  │   /api/firebird/configs/{id}/test           │   │
│  │   /api/firebird/configs/{id}/query          │   │
│  │   /api/firebird/configs/{id}/health         │   │
│  └─────────────────┬───────────────────────────┘   │
│                    │                                 │
│  ┌─────────────────▼───────────────────────────┐   │
│  │        FirebirdService (Singleton)           │   │
│  │  • Manages multiple connection pools         │   │
│  │  • Encrypts/decrypts credentials            │   │
│  │  • Executes read-only queries               │   │
│  │  • Health monitoring                        │   │
│  └─────────────────┬───────────────────────────┘   │
│                    │                                 │
│  ┌─────────────────▼───────────────────────────┐   │
│  │   FirebirdConnectionPool (Per Config)       │   │
│  │  • Thread-safe Queue-based pool             │   │
│  │  • Max 5 connections per database           │   │
│  │  • Automatic connection recovery            │   │
│  │  • Connection health testing                │   │
│  └─────────────────┬───────────────────────────┘   │
└────────────────────┼───────────────────────────────┘
                     │
                     │ fdb library
                     │
         ┌───────────▼─────────────┐
         │  Firebird Database      │
         │  (External PMS System)  │
         └─────────────────────────┘
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The `fdb` library (Firebird database driver) is included in requirements.txt:

```
fdb==2.0.2  # Firebird database driver
```

### 2. Set Encryption Key

Add to `.env` file:

```bash
ENCRYPTION_KEY="your-secure-encryption-key-here"
```

**Important**: Generate a secure encryption key:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### 3. Run Migration

Apply the database migration to create the `firebird_config` table:

```bash
psql -U signage_user -d signage_db -f backend/migrations/006_create_firebird_config.sql
```

## API Documentation

### Authentication

All endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Endpoints

#### 1. Create Configuration

**POST** `/api/firebird/configs`

Create a new Firebird database configuration.

**Request Body:**
```json
{
  "config_key": "hotel_pms",
  "api_endpoint": "192.168.1.100:3050/opt/databases/powerfo.gdb",
  "api_key": "SYSDBA:masterkey",
  "refresh_interval": 300,
  "is_active": true,
  "notes": "Hotel PMS database connection"
}
```

**Fields:**
- `config_key`: Unique identifier (alphanumeric, underscore)
- `api_endpoint`: Firebird DSN
  - Server mode: `"host:port/path/to/db.gdb"`
  - Embedded mode: `"/path/to/db.fdb"`
- `api_key`: Credentials in format `"username:password"` (will be encrypted)
- `refresh_interval`: Data refresh interval in seconds (10-3600)
- `is_active`: Enable/disable this configuration
- `notes`: Admin notes (optional)

**Response:** `201 Created`
```json
{
  "id": 1,
  "config_key": "hotel_pms",
  "api_endpoint": "192.168.1.100:3050/opt/databases/powerfo.gdb",
  "refresh_interval": 300,
  "is_active": true,
  "last_sync": null,
  "notes": "Hotel PMS database connection",
  "created_at": "2025-10-27T10:00:00Z",
  "updated_at": "2025-10-27T10:00:00Z"
}
```

**Note**: `api_key` is NOT included in the response for security.

---

#### 2. List Configurations

**GET** `/api/firebird/configs`

Get list of all Firebird configurations.

**Query Parameters:**
- `is_active` (optional): Filter by active status (true/false)
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Max records to return (default: 100, max: 500)

**Response:** `200 OK`
```json
{
  "total": 2,
  "configs": [
    {
      "id": 1,
      "config_key": "hotel_pms",
      "api_endpoint": "192.168.1.100:3050/opt/databases/powerfo.gdb",
      "refresh_interval": 300,
      "is_active": true,
      "last_sync": "2025-10-27T10:30:00Z",
      "notes": "Hotel PMS database connection",
      "created_at": "2025-10-27T10:00:00Z",
      "updated_at": "2025-10-27T10:30:00Z"
    }
  ]
}
```

---

#### 3. Get Configuration

**GET** `/api/firebird/configs/{config_id}`

Get details of a specific configuration.

**Response:** `200 OK`
```json
{
  "id": 1,
  "config_key": "hotel_pms",
  "api_endpoint": "192.168.1.100:3050/opt/databases/powerfo.gdb",
  "refresh_interval": 300,
  "is_active": true,
  "last_sync": "2025-10-27T10:30:00Z",
  "notes": "Hotel PMS database connection",
  "created_at": "2025-10-27T10:00:00Z",
  "updated_at": "2025-10-27T10:30:00Z"
}
```

---

#### 4. Update Configuration

**PUT** `/api/firebird/configs/{config_id}`

Update an existing configuration.

**Request Body:** (all fields optional)
```json
{
  "config_key": "hotel_pms_updated",
  "api_endpoint": "192.168.1.101:3050/opt/databases/powerfo.gdb",
  "api_key": "SYSDBA:newpassword",
  "refresh_interval": 600,
  "is_active": false,
  "notes": "Updated configuration"
}
```

**Response:** `200 OK`

**Note**: If `api_endpoint` or `api_key` is updated, the connection pool will be recreated on next use.

---

#### 5. Delete Configuration

**DELETE** `/api/firebird/configs/{config_id}`

Delete a configuration and close its connection pool.

**Response:** `200 OK`
```json
{
  "message": "Configuration 'hotel_pms' deleted successfully",
  "config_id": 1
}
```

---

#### 6. Test Connection

**POST** `/api/firebird/configs/{config_id}/test`

Test database connection and optionally execute a test query.

**Request Body:** (optional)
```json
{
  "test_query": "SELECT FIRST 1 * FROM RDB$DATABASE"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Connection successful",
  "connection_time_ms": 45.2,
  "test_query_executed": true,
  "error_details": null
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Connection failed: Cannot connect to host",
  "connection_time_ms": 0.0,
  "test_query_executed": false,
  "error_details": "Cannot connect to host..."
}
```

---

#### 7. Execute Query

**POST** `/api/firebird/configs/{config_id}/query`

Execute a read-only SELECT query.

**Request Body:**
```json
{
  "query": "SELECT * FROM GUESTS WHERE CHECK_IN_DATE = CURRENT_DATE",
  "max_rows": 50
}
```

**Fields:**
- `query`: SQL SELECT statement (required)
- `max_rows`: Maximum rows to return (1-1000, default: 100)

**Response:** `200 OK`
```json
{
  "success": true,
  "row_count": 3,
  "columns": ["GUEST_ID", "GUEST_NAME", "ROOM_NUMBER", "CHECK_IN_DATE"],
  "rows": [
    {
      "GUEST_ID": 101,
      "GUEST_NAME": "John Doe",
      "ROOM_NUMBER": "205",
      "CHECK_IN_DATE": "2025-10-27"
    },
    {
      "GUEST_ID": 102,
      "GUEST_NAME": "Jane Smith",
      "ROOM_NUMBER": "312",
      "CHECK_IN_DATE": "2025-10-27"
    }
  ],
  "execution_time_ms": 23.5,
  "message": "Query executed successfully, 3 rows returned",
  "error_details": null
}
```

**Query Restrictions:**
- Only SELECT queries allowed
- Forbidden keywords: INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, EXECUTE, GRANT, REVOKE, TRUNCATE
- Results automatically limited by `max_rows`

**Error Response:**
```json
{
  "success": false,
  "row_count": 0,
  "columns": [],
  "rows": [],
  "execution_time_ms": 0.0,
  "message": "Query execution failed: Invalid column name",
  "error_details": "Invalid column name: GUEST..."
}
```

---

#### 8. Health Check

**GET** `/api/firebird/configs/{config_id}/health`

Check connection health and pool status.

**Response:** `200 OK`
```json
{
  "config_id": 1,
  "config_key": "hotel_pms",
  "is_healthy": true,
  "connection_status": "connected",
  "pool_status": {
    "total_connections": 5,
    "available_connections": 3,
    "active_connections": 2,
    "max_connections": 5
  },
  "last_check": "2025-10-27T10:35:00Z",
  "error_message": null
}
```

**Connection Status:**
- `"connected"`: Database is accessible
- `"disconnected"`: Database unreachable
- `"no_pool"`: Connection pool not initialized
- `"error"`: Connection error occurred

---

## Security Features

### 1. Credential Encryption

All credentials are encrypted using Fernet symmetric encryption:

```python
from app.services.firebird_service import firebird_service

# Encrypt before storing
encrypted = firebird_service.encrypt_api_key("SYSDBA:masterkey")

# Decrypt when needed (handled internally)
username, password = firebird_service._parse_credentials(encrypted)
```

### 2. Query Validation

Only SELECT queries are allowed. The system blocks:

- DML operations: INSERT, UPDATE, DELETE
- DDL operations: CREATE, DROP, ALTER, TRUNCATE
- Admin operations: GRANT, REVOKE, EXECUTE
- Stored procedures: PROCEDURE, TRIGGER

### 3. SQL Injection Prevention

- Query validation using regex patterns
- Parameterized queries (future enhancement)
- Row limit enforcement (FIRST clause)

### 4. Authentication

All endpoints require JWT authentication:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://192.168.5.12:8001/api/firebird/configs
```

---

## Usage Examples

### Example 1: Setup and Test Connection

```bash
# 1. Create configuration
curl -X POST http://192.168.5.12:8001/api/firebird/configs \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "config_key": "hotel_pms",
    "api_endpoint": "192.168.1.100:3050/opt/databases/powerfo.gdb",
    "api_key": "SYSDBA:masterkey",
    "refresh_interval": 300,
    "is_active": true,
    "notes": "Hotel PMS connection"
  }'

# 2. Test connection
curl -X POST http://192.168.5.12:8001/api/firebird/configs/1/test \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"test_query": "SELECT 1 FROM RDB$DATABASE"}'
```

### Example 2: Fetch Guest Information

```bash
# Query today's guests
curl -X POST http://192.168.5.12:8001/api/firebird/configs/1/query \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT GUEST_NAME, ROOM_NUMBER FROM GUESTS WHERE CHECK_IN_DATE = CURRENT_DATE",
    "max_rows": 10
  }'
```

### Example 3: Health Monitoring

```bash
# Check connection health
curl -X GET http://192.168.5.12:8001/api/firebird/configs/1/health \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Example 4: Python Client

```python
import requests

BASE_URL = "http://192.168.5.12:8001"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Create configuration
response = requests.post(
    f"{BASE_URL}/api/firebird/configs",
    headers=headers,
    json={
        "config_key": "hotel_pms",
        "api_endpoint": "192.168.1.100:3050/opt/databases/powerfo.gdb",
        "api_key": "SYSDBA:masterkey",
        "refresh_interval": 300,
        "is_active": True
    }
)
config_id = response.json()["id"]

# Execute query
response = requests.post(
    f"{BASE_URL}/api/firebird/configs/{config_id}/query",
    headers=headers,
    json={
        "query": "SELECT * FROM GUESTS WHERE CHECK_IN_DATE = CURRENT_DATE",
        "max_rows": 50
    }
)
result = response.json()

if result["success"]:
    print(f"Found {result['row_count']} guests:")
    for row in result["rows"]:
        print(f"  {row['GUEST_NAME']} - Room {row['ROOM_NUMBER']}")
```

---

## Firebird DSN Formats

### Server Mode (Network)

```
hostname:port/path/to/database.gdb
```

Examples:
```
192.168.1.100:3050/opt/databases/powerfo.gdb
localhost:3050/var/lib/firebird/data/mydb.fdb
server.domain.com:3050/C:/Databases/hotel.gdb
```

### Embedded Mode (Local)

```
/absolute/path/to/database.fdb
```

Examples:
```
/opt/databases/local.fdb
/var/lib/firebird/data/embedded.gdb
C:/Databases/local.fdb  (Windows)
```

---

## Connection Pool Configuration

Each configuration has its own connection pool:

- **Max Connections**: 5 connections per database
- **Connection Timeout**: 10 seconds
- **Charset**: UTF8
- **Thread-Safe**: Yes (Queue-based)
- **Auto-Recovery**: Yes (recreates failed connections)

**Pool Status:**
```json
{
  "total_connections": 5,
  "available_connections": 3,
  "active_connections": 2,
  "max_connections": 5
}
```

---

## Troubleshooting

### Connection Fails

**Error:** `"Connection failed: Cannot connect to host"`

**Solutions:**
1. Verify Firebird server is running
2. Check firewall rules (default port: 3050)
3. Verify DSN format (host:port/path)
4. Test with Firebird tools: `isql -u SYSDBA -p masterkey localhost:3050/path/to/db.gdb`

### Authentication Fails

**Error:** `"Connection failed: Your user name and password are not defined"`

**Solutions:**
1. Verify username/password in api_key field
2. Check Firebird user exists: `gsec -display`
3. Ensure password is correct

### Query Fails

**Error:** `"Query contains forbidden keyword: UPDATE"`

**Solution:** Only SELECT queries are allowed. Remove DML/DDL operations.

**Error:** `"Invalid column name"`

**Solution:** Check column names exist in Firebird database using isql.

### Pool Exhausted

**Error:** `"Connection pool exhausted - all connections in use"`

**Solution:**
1. Check if queries are taking too long
2. Reduce max_rows parameter
3. Monitor pool status via health endpoint
4. Close unused connections by restarting backend

---

## Performance Tips

1. **Limit Rows**: Always use `max_rows` parameter to limit result size
2. **Index Queries**: Ensure Firebird tables have appropriate indexes
3. **Connection Reuse**: Connection pool reuses connections automatically
4. **Batch Queries**: Combine multiple conditions in one query instead of multiple queries
5. **Cache Results**: Cache frequently accessed data in Redis (future enhancement)

---

## Future Enhancements

- [ ] Query result caching (Redis)
- [ ] Query templates for common operations
- [ ] Query history and audit logging
- [ ] Rate limiting per configuration
- [ ] Scheduled query execution
- [ ] Data transformation pipelines
- [ ] WebSocket support for real-time updates

---

## Files Created

```
backend/
├── app/
│   ├── api/
│   │   └── firebird.py                 # API endpoints
│   ├── models/
│   │   └── firebird.py                 # SQLAlchemy model (existing)
│   ├── schemas/
│   │   └── firebird.py                 # Pydantic schemas
│   └── services/
│       └── firebird_service.py         # Connection pool & service
├── migrations/
│   └── 006_create_firebird_config.sql  # Database migration
├── requirements.txt                     # Updated with fdb
└── FIREBIRD_INTEGRATION.md             # This documentation
```

---

## Support

For issues or questions:
1. Check logs: `docker logs signage-backend`
2. Test connection using Firebird tools
3. Verify credentials and DSN format
4. Check firewall rules and network connectivity

---

**Last Updated:** 2025-10-27
**Version:** 1.0.0
**Author:** System Architect
