# Phase 5 - Table Selection & Column Mapping - COMPLETE ✅

**Completed Date**: 2025-01-11
**Status**: All Features ✅ | Multi-Tenant Secure ✅ | Read-Only ✅

---

## Overview

Added **Table Selection & Column Mapping** feature yang memungkinkan user untuk:
- ✅ **Pilih tabel mana saja** yang mau di-sync (tidak semua tabel)
- ✅ **Mapping kolom** dari Firebird ke format standard
- ✅ **Custom WHERE clause** untuk filter data
- ✅ **Enable/Disable** sync per tabel (Guest dan Room terpisah)
- ✅ **Multi-tenant secure** - hanya sync ke organization sendiri
- ✅ **Read-only** - hanya SELECT, tidak bisa edit database Firebird

---

## New Features

### 1. Table Mapper (`table_mapper.py`)

**File**: `/mnt/g/khoirul/signate/firebird-bridge-agent/table_mapper.py`

**Capabilities**:
- Get list of columns untuk table tertentu
- Dynamic query builder based on column mapping
- Query guests dengan custom table & columns
- Query rooms dengan custom table & columns
- **Read-only** - hanya SELECT queries

**Example Usage**:
```python
from table_mapper import TableMapper

mapper = TableMapper(firebird_config)
mapper.connect()

# Get columns for a table
columns = mapper.get_table_columns('GUESTS_TABLE')
# Returns: [{'name': 'GUEST_NAME', 'type': 'VARCHAR(100)'}, ...]

# Query dengan custom mapping
guest_config = {
    'table_name': 'GUESTS_TABLE',
    'columns': {
        'guest_name': 'GUEST_NAME_COL',
        'room_number': 'ROOM_NO_COL',
        'checkin_date': 'CHECKIN_DATE_COL',
        'checkout_date': 'CHECKOUT_DATE_COL'
    },
    'where_clause': "STATUS = 'CHECKED_IN' AND CHECKIN_DATE >= ?"
}

guests = mapper.query_guests_from_mapping(guest_config, minutes=5)
mapper.close()
```

### 2. Table Mapping Web UI

**New Page**: http://localhost:5000/tables

**Features**:

#### Guest Table Configuration
- ☑️ **Enable/Disable** guest sync
- 📋 **Select table** dari dropdown (dengan suggestions)
- 🔄 **Load Tables** button (scan Firebird database)
- 🗂️ **Column Mapping** (8 fields):
  - guest_name (required)
  - room_number (required)
  - checkin_date (required)
  - checkout_date (required)
  - email (optional)
  - phone (optional)
  - country (optional)
  - reservation_no (optional)
- 🔍 **WHERE Clause** for filtering
- 💾 **Save** mapping to config

#### Room Table Configuration
- ☑️ **Enable/Disable** room sync
- 📋 **Select table** dari dropdown
- 🔄 **Load Tables** button
- 🗂️ **Column Mapping** (6 fields):
  - room_number (required)
  - room_type (optional)
  - status (required)
  - floor (optional)
  - bed_type (optional)
  - max_occupancy (optional)
- 🔍 **WHERE Clause** for filtering
- 💾 **Save** mapping to config

**UI Features**:
- Auto-detect guest/room tables (suggested tables)
- Show all tables in optgroup
- Load columns when table selected
- Show column data types
- Multi-Tenant security notice
- Read-only reminder

### 3. Updated Config Structure

**New Config Format** (config.yaml):
```yaml
cloud:
  api_url: "http://192.168.5.12:8001/api/v1"
  organization_id: 1  # ← Multi-tenant: hanya sync ke org ini
  api_key: "your-api-key"
  verify_ssl: false

firebird:
  host: "localhost"
  port: 3050
  database_path: "/mnt/g/khoirul/signate/powerbo.gdb"
  username: "SYSDBA"
  password: "masterkey"
  charset: "UTF8"

tables:
  guest_table:
    enabled: true  # ← Enable/disable guest sync
    table_name: "GUESTS"  # ← User-selected table
    columns:
      guest_name: "GUEST_NAME"  # ← Column mapping
      room_number: "ROOM_NO"
      checkin_date: "CHECKIN_DATE"
      checkout_date: "CHECKOUT_DATE"
      email: "EMAIL"
      phone: "PHONE"
      country: "COUNTRY"
      reservation_no: "RESERVATION_NO"
    where_clause: "STATUS = 'CHECKED_IN' AND CHECKIN_DATE >= ?"

  room_table:
    enabled: true  # ← Enable/disable room sync
    table_name: "ROOMS"  # ← User-selected table
    columns:
      room_number: "ROOM_NO"
      room_type: "ROOM_TYPE"
      status: "STATUS"
      floor: "FLOOR"
      bed_type: "BED_TYPE"
      max_occupancy: "MAX_GUESTS"
    where_clause: ""  # Optional filter

sync:
  interval_minutes: 5
  batch_size: 100
  retry_attempts: 3

logging:
  level: "INFO"
  file: "/var/log/firebird-bridge/agent.log"
```

### 4. Updated WebSocket Agent

**File**: `websocket_agent.py`

**Changes**:
- ✅ Use `TableMapper` instead of `FirebirdReader`
- ✅ Check `enabled` flag before syncing
- ✅ Skip if table not configured
- ✅ Use custom table & column mappings
- ✅ Dynamic WHERE clause support
- ✅ Multi-tenant: always send with organization_id

**Log Output Example**:
```
================================================================================
Firebird Bridge Agent (WebSocket) starting...
Sync interval: 5 minutes
Organization ID: 1  ← Multi-tenant security
================================================================================
Connecting to WebSocket: ws://192.168.5.12:8001/ws/pms/sync
✓ WebSocket connected
================================================================================
Starting sync cycle at 2025-01-11 14:30:00
Syncing guest data...
Found 3 guest records
Sent 3 guests
Syncing room data...
Found 50 room records
Sent 50 rooms
Sync cycle completed
================================================================================
```

---

## Multi-Tenant Security

### 1. Organization ID Isolation
```yaml
cloud:
  organization_id: 1  # ← CRITICAL: Hanya sync ke org ini
  api_key: "unique-per-organization"  # ← Unique per hotel
```

### 2. API Key Authentication
- Setiap organization punya **API key unik**
- Backend verify API key + organization ID
- WebSocket connection **ditolak** jika tidak match

### 3. Data Isolation
- Guest data: `organization_id = 1` → Hanya visible untuk org 1
- Room data: `organization_id = 1` → Hanya visible untuk org 1
- User lain **tidak bisa akses** data organization Anda

### 4. Backend Validation
```python
# backend-python/services/pms/websocket_routes.py
def verify_websocket_auth(api_key: str, organization_id: int, db: Session) -> bool:
    config = repo.get_config_by_api_key(api_key)

    if not config:
        return False  # API key not found

    if config.organization_id != organization_id:
        return False  # Organization mismatch!

    if not config.is_active:
        return False  # PMS integration disabled

    return True
```

---

## Read-Only Security

### Agent Only Does SELECT

```sql
-- ✅ ALLOWED (Read-only)
SELECT GUEST_NAME, ROOM_NO FROM GUESTS WHERE STATUS = 'CHECKED_IN'
SELECT ROOM_NO, STATUS FROM ROOMS

-- ❌ NOT ALLOWED (Agent doesn't do these)
INSERT INTO GUESTS ...
UPDATE GUESTS SET ...
DELETE FROM GUESTS ...
DROP TABLE ...
```

### Firebird Permissions

**Recommended**: Create read-only user untuk agent:

```sql
-- Create read-only user (di Firebird)
CREATE USER pms_agent PASSWORD 'secure_password';
GRANT SELECT ON GUESTS TO pms_agent;
GRANT SELECT ON ROOMS TO pms_agent;
-- DO NOT GRANT INSERT, UPDATE, DELETE
```

Then use in config:
```yaml
firebird:
  username: "pms_agent"  # ← Read-only user
  password: "secure_password"
```

---

## How To Use

### Step 1: Configure Firebird Connection

1. Go to http://localhost:5000/settings
2. Set Firebird settings (host, port, path, **username: SYSDBA**, **password: masterkey**)
3. Click **Test Connection** ✅
4. Click **Save Firebird Settings**

### Step 2: Select Tables & Map Columns

1. Go to http://localhost:5000/tables
2. **Guest Table**:
   - Check ☑️ "Enable Guest Sync"
   - Click **Load Tables from Database**
   - Select guest table from dropdown (e.g., GUESTS, RESERVATIONS)
   - Map columns:
     - Guest Name → Select column (e.g., GUEST_NAME)
     - Room Number → Select column (e.g., ROOM_NO)
     - Check-in Date → Select column (e.g., CHECKIN_DATE)
     - Check-out Date → Select column (e.g., CHECKOUT_DATE)
     - (Optional) Email, Phone, Country, Reservation No
   - (Optional) Add WHERE clause: `STATUS = 'CHECKED_IN' AND CHECKIN_DATE >= ?`

3. **Room Table**:
   - Check ☑️ "Enable Room Sync"
   - Click **Load Tables from Database**
   - Select room table from dropdown (e.g., ROOMS, KAMAR)
   - Map columns:
     - Room Number → Select column
     - Room Type → Select column (optional)
     - Status → Select column
     - Floor, Bed Type, Max Occupancy (optional)
   - (Optional) Add WHERE clause

4. Click **💾 Save Table Mapping**

### Step 3: Run WebSocket Agent

```bash
python3 websocket_agent.py
```

### Step 4: Verify Sync

Check logs:
```
Syncing guest data...
Found 3 guest records
Sent 3 guests
Syncing room data...
Found 50 room records
Sent 50 rooms
```

Check database:
```bash
docker exec signage-postgres psql -U signage_user -d signage_db \
  -c "SELECT guest_name, room_number, organization_id FROM pms_guests WHERE organization_id = 1 LIMIT 10;"
```

---

## API Endpoints

### 1. List Tables
```
POST /api/list-tables
Body: {firebird config}
Response: {
  "tables": ["GUESTS", "ROOMS", ...],
  "guest_tables": ["GUESTS", "RESERVATIONS"],
  "room_tables": ["ROOMS", "KAMAR"]
}
```

### 2. Get Table Columns
```
POST /api/table-columns
Body: {
  ...firebird config,
  "table_name": "GUESTS"
}
Response: {
  "columns": [
    {"name": "GUEST_NAME", "type": "VARCHAR(100)"},
    {"name": "ROOM_NO", "type": "VARCHAR(10)"},
    ...
  ]
}
```

### 3. Save Table Mapping
```
POST /api/table-mapping
Body: {
  "tables": {
    "guest_table": {...},
    "room_table": {...}
  }
}
```

---

## Example Configurations

### Example 1: Simple Hotel PMS

```yaml
tables:
  guest_table:
    enabled: true
    table_name: "GUESTS"
    columns:
      guest_name: "NAME"
      room_number: "ROOM"
      checkin_date: "CHECKIN"
      checkout_date: "CHECKOUT"
      email: ""  # Not available
      phone: "TELEPHONE"
      country: ""
      reservation_no: "BOOKING_NO"
    where_clause: "STATUS = 1 AND CHECKIN >= ?"

  room_table:
    enabled: true
    table_name: "ROOMS"
    columns:
      room_number: "ROOM_NO"
      room_type: "TYPE"
      status: "STATUS"
      floor: "FLOOR_NO"
      bed_type: ""
      max_occupancy: "MAX_PERSON"
    where_clause: "ACTIVE = 1"
```

### Example 2: Complex PMS with Multiple Tables

```yaml
tables:
  guest_table:
    enabled: true
    table_name: "TB_RESERVASI"
    columns:
      guest_name: "NAMA_TAMU"
      room_number: "NO_KAMAR"
      checkin_date: "TGL_CHECKIN"
      checkout_date: "TGL_CHECKOUT"
      email: "EMAIL_TAMU"
      phone: "NO_TELP"
      country: "NEGARA"
      reservation_no: "NO_RESERVASI"
    where_clause: "STATUS_RESERVASI = 'AKTIF' AND TGL_CHECKIN >= ?"

  room_table:
    enabled: true
    table_name: "TB_KAMAR"
    columns:
      room_number: "KODE_KAMAR"
      room_type: "TIPE_KAMAR"
      status: "STATUS_KAMAR"
      floor: "LANTAI"
      bed_type: "TIPE_BED"
      max_occupancy: "KAPASITAS"
    where_clause: "DELETED_AT IS NULL"
```

### Example 3: Only Guest Sync (No Room)

```yaml
tables:
  guest_table:
    enabled: true
    table_name: "GUEST_MASTER"
    columns:
      guest_name: "FULL_NAME"
      room_number: "ASSIGNED_ROOM"
      checkin_date: "CHECK_IN_DATETIME"
      checkout_date: "CHECK_OUT_DATETIME"
      email: "EMAIL_ADDRESS"
      phone: "MOBILE_NO"
      country: "NATIONALITY"
      reservation_no: "CONFIRMATION_NO"
    where_clause: "GUEST_STATUS = 'IN_HOUSE'"

  room_table:
    enabled: false  # ← Disabled
    table_name: ""
    columns: {}
    where_clause: ""
```

---

## Benefits

### 1. Flexibility
- ✅ Support **berbagai schema** Firebird PMS
- ✅ Tidak perlu edit code untuk custom table
- ✅ User bisa **configure sendiri** via Web UI

### 2. Selective Sync
- ✅ Sync **hanya tabel yang dipilih**
- ✅ Disable sync untuk tabel yang tidak perlu
- ✅ Custom WHERE clause untuk filter data

### 3. Security
- ✅ **Multi-tenant**: Data isolated per organization
- ✅ **Read-only**: Hanya SELECT, no write to Firebird
- ✅ **API Key** authentication per organization

### 4. Easy Configuration
- ✅ **No code editing** required
- ✅ Visual column mapping
- ✅ Test connection before saving
- ✅ See all tables and columns

---

## Files Created/Modified

### New Files
1. `table_mapper.py` - Dynamic query builder (343 lines)
2. `templates/tables.html` - Table mapping UI (456 lines)

### Modified Files
1. `web_ui.py` - Added table routes (3 new endpoints)
2. `websocket_agent.py` - Use TableMapper instead of FirebirdReader
3. `templates/base.html` - Added "Table Mapping" nav link

---

## Testing Checklist

- [ ] Open http://localhost:5000/settings
- [ ] Configure Firebird connection
- [ ] Test Firebird connection ✅
- [ ] Go to http://localhost:5000/tables
- [ ] Click "Load Tables from Database" for Guest
- [ ] Select guest table from dropdown
- [ ] See columns loaded automatically
- [ ] Map all required columns
- [ ] Add WHERE clause (optional)
- [ ] Enable/disable guest sync checkbox
- [ ] Repeat for Room table
- [ ] Click "Save Table Mapping"
- [ ] Run `python3 websocket_agent.py`
- [ ] Verify sync in logs
- [ ] Check data in PostgreSQL

---

## Summary

**Phase 5 - Table Selection & Column Mapping COMPLETE!** ✅

**Achievements**:
- ✅ Table Mapper with dynamic query builder
- ✅ Web UI for table selection
- ✅ Column mapping configuration
- ✅ Enable/disable per table
- ✅ Custom WHERE clause support
- ✅ Multi-tenant secure (organization isolation)
- ✅ Read-only security (SELECT only)
- ✅ Support berbagai schema Firebird
- ✅ No code editing required

**Architecture**:
- User pilih tabel di Web UI
- Map kolom ke format standard
- Agent query dengan custom mapping
- Data sync dengan organization_id
- Multi-tenant secure & read-only

**Ready For**: Testing dengan powerbo.gdb atau powerfo.gdb!
