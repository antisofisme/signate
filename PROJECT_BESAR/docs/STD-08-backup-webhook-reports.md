# Development Standards V8

> Standards #31-33: Backup & Disaster Recovery, Webhook System, Report Generation

---

## Table of Contents

- [Standard #31: Backup & Disaster Recovery](#standard-31-backup--disaster-recovery)
- [Standard #32: Webhook System](#standard-32-webhook-system)
- [Standard #33: Report Generation](#standard-33-report-generation)

---

## Standard #31: Backup & Disaster Recovery

### 31.1 Overview

Backup & Disaster Recovery (DR) memastikan data dan sistem dapat dipulihkan jika terjadi kegagalan. Strategi ini mencakup backup reguler, replikasi, dan prosedur recovery yang teruji.

### 31.2 Backup Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        BACKUP STRATEGY (3-2-1 Rule)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  3 COPIES    │    2 DIFFERENT MEDIA    │    1 OFFSITE                   │
│              │                          │                                │
│  ┌────────┐  │  ┌────────┐ ┌────────┐  │  ┌────────┐                   │
│  │Original│  │  │  SSD   │ │ Object │  │  │ Cloud  │                   │
│  │  Data  │  │  │Storage │ │Storage │  │  │(R2/S3) │                   │
│  └────────┘  │  └────────┘ └────────┘  │  └────────┘                   │
│  ┌────────┐  │                          │                                │
│  │Backup 1│  │  Primary    Secondary    │  Offsite backup               │
│  └────────┘  │  (local)    (NAS/SAN)    │  (different region)           │
│  ┌────────┐  │                          │                                │
│  │Backup 2│  │                          │                                │
│  └────────┘  │                          │                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 31.3 Backup Types & Schedule

| Backup Type | Frequency | Retention | Description |
|-------------|-----------|-----------|-------------|
| **Full Backup** | Weekly (Sunday 02:00) | 4 weeks | Complete database dump |
| **Incremental** | Daily (02:00) | 7 days | Only changed data since last backup |
| **WAL Archive** | Continuous | 7 days | PostgreSQL Write-Ahead Logs |
| **Point-in-Time** | On-demand | 30 days | Restore to specific timestamp |
| **Config Backup** | On change | 90 days | Application & infra configs |

### 31.4 Database Backup Implementation

#### PostgreSQL Backup Script

```bash
#!/bin/bash
# scripts/backup/database_backup.sh

set -e

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-signage_db}"
DB_USER="${DB_USER:-signage_user}"
BACKUP_DIR="/backups/postgresql"
S3_BUCKET="${S3_BUCKET:-signage-backups}"
RETENTION_DAYS=7
RETENTION_WEEKS=4

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DAY_OF_WEEK=$(date +%u)

# Determine backup type
if [ "$DAY_OF_WEEK" -eq 7 ]; then
    BACKUP_TYPE="full"
    RETENTION=$RETENTION_WEEKS
else
    BACKUP_TYPE="incremental"
    RETENTION=$RETENTION_DAYS
fi

BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${BACKUP_TYPE}_${TIMESTAMP}.sql.gz"

echo "Starting ${BACKUP_TYPE} backup: ${BACKUP_FILE}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Full backup
if [ "$BACKUP_TYPE" = "full" ]; then
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --format=custom \
        --compress=9 \
        --verbose \
        --file="${BACKUP_FILE}"
else
    # Incremental using pg_basebackup (for WAL shipping)
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --format=custom \
        --compress=9 \
        --verbose \
        --file="${BACKUP_FILE}"
fi

# Verify backup
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file not created!"
    exit 1
fi

BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "Backup completed: ${BACKUP_FILE} (${BACKUP_SIZE})"

# Upload to S3/R2
echo "Uploading to cloud storage..."
aws s3 cp "${BACKUP_FILE}" "s3://${S3_BUCKET}/database/${BACKUP_TYPE}/" \
    --storage-class STANDARD_IA

# Calculate checksum
CHECKSUM=$(sha256sum "${BACKUP_FILE}" | cut -d' ' -f1)
echo "${CHECKSUM}" > "${BACKUP_FILE}.sha256"
aws s3 cp "${BACKUP_FILE}.sha256" "s3://${S3_BUCKET}/database/${BACKUP_TYPE}/"

# Cleanup old backups (local)
echo "Cleaning up old local backups..."
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +${RETENTION} -delete
find "${BACKUP_DIR}" -name "*.sha256" -mtime +${RETENTION} -delete

# Cleanup old backups (S3)
echo "Cleaning up old cloud backups..."
aws s3 ls "s3://${S3_BUCKET}/database/${BACKUP_TYPE}/" | \
    while read -r line; do
        FILE_DATE=$(echo "$line" | awk '{print $1}')
        FILE_NAME=$(echo "$line" | awk '{print $4}')
        if [ -n "$FILE_NAME" ]; then
            DAYS_OLD=$(( ($(date +%s) - $(date -d "$FILE_DATE" +%s)) / 86400 ))
            if [ "$DAYS_OLD" -gt "$RETENTION" ]; then
                aws s3 rm "s3://${S3_BUCKET}/database/${BACKUP_TYPE}/${FILE_NAME}"
            fi
        fi
    done

# Log backup metadata
cat << EOF >> "${BACKUP_DIR}/backup_log.json"
{
    "timestamp": "${TIMESTAMP}",
    "type": "${BACKUP_TYPE}",
    "file": "${BACKUP_FILE}",
    "size": "${BACKUP_SIZE}",
    "checksum": "${CHECKSUM}",
    "retention_days": ${RETENTION}
}
EOF

echo "Backup completed successfully!"
```

#### WAL Archiving Configuration

```ini
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'aws s3 cp %p s3://signage-backups/wal/%f'
archive_timeout = 300  # 5 minutes

# For Point-in-Time Recovery
restore_command = 'aws s3 cp s3://signage-backups/wal/%f %p'
recovery_target_time = '2025-01-15 14:30:00'
```

### 31.5 Application Backup

#### File Storage Backup

```python
# services/backup/use_cases/backup_files.py
import asyncio
from datetime import datetime
from typing import List
import boto3

class BackupFilesUseCase:
    """Backup application files to cloud storage"""

    def __init__(self, s3_client, config):
        self.s3 = s3_client
        self.source_bucket = config.PRIMARY_BUCKET
        self.backup_bucket = config.BACKUP_BUCKET

    async def execute(self, backup_type: str = "incremental") -> dict:
        """Execute file backup"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_prefix = f"files/{backup_type}/{timestamp}/"

        if backup_type == "full":
            # Copy all files
            files = await self._list_all_files()
        else:
            # Only files modified since last backup
            last_backup = await self._get_last_backup_time()
            files = await self._list_modified_files(since=last_backup)

        # Copy files to backup bucket
        copied = 0
        errors = []

        for file_key in files:
            try:
                await self._copy_file(
                    source_key=file_key,
                    dest_key=f"{backup_prefix}{file_key}"
                )
                copied += 1
            except Exception as e:
                errors.append({"file": file_key, "error": str(e)})

        # Create manifest
        manifest = {
            "timestamp": timestamp,
            "type": backup_type,
            "files_count": len(files),
            "copied": copied,
            "errors": errors
        }

        await self._save_manifest(backup_prefix, manifest)

        return manifest

    async def _copy_file(self, source_key: str, dest_key: str):
        """Copy file between buckets"""
        copy_source = {"Bucket": self.source_bucket, "Key": source_key}
        self.s3.copy_object(
            CopySource=copy_source,
            Bucket=self.backup_bucket,
            Key=dest_key,
            StorageClass="STANDARD_IA"
        )

    async def _list_modified_files(self, since: datetime) -> List[str]:
        """List files modified since timestamp"""
        files = []
        paginator = self.s3.get_paginator('list_objects_v2')

        for page in paginator.paginate(Bucket=self.source_bucket):
            for obj in page.get('Contents', []):
                if obj['LastModified'] > since:
                    files.append(obj['Key'])

        return files
```

#### Configuration Backup

```python
# services/backup/use_cases/backup_config.py
import json
from datetime import datetime
from pathlib import Path

class BackupConfigUseCase:
    """Backup application and infrastructure configuration"""

    def __init__(self, s3_client, config):
        self.s3 = s3_client
        self.backup_bucket = config.BACKUP_BUCKET

    async def execute(self) -> dict:
        """Execute configuration backup"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        configs_to_backup = []

        # 1. Docker Compose files
        docker_configs = self._backup_docker_configs()
        configs_to_backup.extend(docker_configs)

        # 2. Nginx configurations
        nginx_configs = self._backup_nginx_configs()
        configs_to_backup.extend(nginx_configs)

        # 3. Application environment (sanitized)
        env_config = self._backup_env_config()
        configs_to_backup.append(env_config)

        # 4. Database schema (structure only)
        schema_config = await self._backup_db_schema()
        configs_to_backup.append(schema_config)

        # Upload all configs as single archive
        archive_key = f"config/{timestamp}/config_backup.json"
        self.s3.put_object(
            Bucket=self.backup_bucket,
            Key=archive_key,
            Body=json.dumps(configs_to_backup, indent=2),
            ContentType="application/json"
        )

        return {
            "timestamp": timestamp,
            "configs_count": len(configs_to_backup),
            "archive_key": archive_key
        }

    def _backup_env_config(self) -> dict:
        """Backup environment config (sanitized - no secrets)"""
        # Only backup non-sensitive keys
        safe_keys = [
            "APP_NAME", "APP_ENV", "LOG_LEVEL",
            "DB_HOST", "DB_PORT", "DB_NAME",
            "REDIS_HOST", "REDIS_PORT",
            "CORS_ORIGINS", "TIMEZONE"
        ]

        import os
        config = {}
        for key in safe_keys:
            if key in os.environ:
                config[key] = os.environ[key]

        return {
            "type": "environment",
            "name": ".env.sanitized",
            "content": config
        }
```

### 31.6 Recovery Procedures

#### Database Recovery

```python
# services/backup/use_cases/restore_database.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import subprocess

@dataclass
class RestoreRequest:
    backup_file: str  # S3 key or local path
    target_time: Optional[datetime] = None  # For PITR
    target_database: str = "signage_db_restore"  # Restore to different DB first

@dataclass
class RestoreResult:
    success: bool
    database: str
    backup_used: str
    restored_at: datetime
    error: Optional[str] = None

class RestoreDatabaseUseCase:
    """Restore database from backup"""

    def __init__(self, s3_client, db_config):
        self.s3 = s3_client
        self.db_config = db_config

    async def execute(self, request: RestoreRequest) -> RestoreResult:
        """Execute database restoration"""
        try:
            # 1. Download backup from S3
            local_path = await self._download_backup(request.backup_file)

            # 2. Create target database
            await self._create_target_database(request.target_database)

            # 3. Restore backup
            if request.target_time:
                await self._restore_point_in_time(
                    local_path,
                    request.target_database,
                    request.target_time
                )
            else:
                await self._restore_full(local_path, request.target_database)

            # 4. Verify restoration
            await self._verify_restoration(request.target_database)

            return RestoreResult(
                success=True,
                database=request.target_database,
                backup_used=request.backup_file,
                restored_at=datetime.utcnow()
            )

        except Exception as e:
            return RestoreResult(
                success=False,
                database=request.target_database,
                backup_used=request.backup_file,
                restored_at=datetime.utcnow(),
                error=str(e)
            )

    async def _restore_full(self, backup_path: str, target_db: str):
        """Restore from full backup"""
        cmd = [
            "pg_restore",
            "-h", self.db_config.host,
            "-p", str(self.db_config.port),
            "-U", self.db_config.user,
            "-d", target_db,
            "--verbose",
            "--clean",
            "--if-exists",
            backup_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Restore failed: {result.stderr}")

    async def _verify_restoration(self, database: str):
        """Verify restored database integrity"""
        # Check table counts
        # Verify foreign keys
        # Check indexes
        pass
```

### 31.7 Disaster Recovery Plan

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DISASTER RECOVERY PLAN                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  RTO (Recovery Time Objective): 4 hours                                 │
│  RPO (Recovery Point Objective): 1 hour                                 │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  DISASTER SEVERITY LEVELS                                        │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │                                                                   │   │
│  │  Level 1: Service Degradation                                    │   │
│  │  ├─ Impact: Single component failure                             │   │
│  │  ├─ Response: Auto-recovery, container restart                   │   │
│  │  └─ Time: < 5 minutes                                            │   │
│  │                                                                   │   │
│  │  Level 2: Partial Outage                                         │   │
│  │  ├─ Impact: Multiple components, but core services up           │   │
│  │  ├─ Response: Manual intervention, failover                     │   │
│  │  └─ Time: < 30 minutes                                           │   │
│  │                                                                   │   │
│  │  Level 3: Full Outage                                            │   │
│  │  ├─ Impact: All services down                                    │   │
│  │  ├─ Response: Full recovery from backup                         │   │
│  │  └─ Time: < 4 hours                                              │   │
│  │                                                                   │   │
│  │  Level 4: Data Center Disaster                                   │   │
│  │  ├─ Impact: Infrastructure destroyed                             │   │
│  │  ├─ Response: Rebuild in different region                       │   │
│  │  └─ Time: < 24 hours                                             │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Recovery Runbook

```yaml
# runbooks/disaster_recovery.yaml
name: Disaster Recovery Runbook
version: "1.0"
last_updated: "2025-01-15"

scenarios:
  database_failure:
    description: "PostgreSQL database is corrupted or unavailable"
    steps:
      - name: "Assess damage"
        action: "Check PostgreSQL logs and status"
        command: "docker logs signage-postgres --tail 100"

      - name: "Attempt recovery from replica"
        condition: "If replica is healthy"
        action: "Promote replica to primary"
        command: "pg_ctl promote -D /var/lib/postgresql/data"

      - name: "Restore from backup"
        condition: "If no replica or replica also failed"
        action: "Restore from latest backup"
        commands:
          - "aws s3 ls s3://signage-backups/database/full/ --recursive | tail -1"
          - "python scripts/restore_database.py --backup <latest_backup>"

      - name: "Restore WAL logs"
        condition: "For point-in-time recovery"
        action: "Apply WAL logs to reach target time"
        command: "python scripts/apply_wal.py --target-time '2025-01-15 14:30:00'"

      - name: "Verify data integrity"
        action: "Run integrity checks"
        command: "python scripts/verify_database.py"

      - name: "Update DNS/Load Balancer"
        condition: "If using new database server"
        action: "Point to new database"

      - name: "Restart application services"
        action: "Restart all dependent services"
        command: "docker-compose restart backend-api"

  complete_system_failure:
    description: "All systems are down, need full rebuild"
    steps:
      - name: "Provision new infrastructure"
        action: "Deploy infrastructure using Terraform"
        command: "terraform apply -var-file=disaster_recovery.tfvars"

      - name: "Restore database"
        action: "Restore from latest backup"

      - name: "Restore file storage"
        action: "Sync files from backup bucket"
        command: "aws s3 sync s3://signage-backups/files/latest/ s3://signage-primary/"

      - name: "Restore configuration"
        action: "Apply configuration from backup"
        command: "python scripts/restore_config.py"

      - name: "Deploy application"
        action: "Deploy application containers"
        command: "docker-compose up -d"

      - name: "Run smoke tests"
        action: "Verify all services are working"
        command: "python scripts/smoke_test.py"

      - name: "Update DNS"
        action: "Point domain to new infrastructure"

      - name: "Notify stakeholders"
        action: "Send recovery notification"
```

### 31.8 Monitoring & Alerting

```python
# services/backup/monitoring.py
from prometheus_client import Gauge, Counter, Histogram

# Metrics
backup_last_success = Gauge(
    'backup_last_success_timestamp',
    'Timestamp of last successful backup',
    ['backup_type']
)

backup_size_bytes = Gauge(
    'backup_size_bytes',
    'Size of last backup in bytes',
    ['backup_type']
)

backup_duration_seconds = Histogram(
    'backup_duration_seconds',
    'Time taken to complete backup',
    ['backup_type'],
    buckets=[60, 300, 600, 1800, 3600]
)

backup_failures = Counter(
    'backup_failures_total',
    'Total number of backup failures',
    ['backup_type', 'error_type']
)

# Alert rules
"""
# prometheus/alerts/backup.yaml
groups:
  - name: backup_alerts
    rules:
      - alert: BackupMissing
        expr: time() - backup_last_success_timestamp > 86400
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "Backup has not run in 24 hours"
          description: "{{ $labels.backup_type }} backup missing"

      - alert: BackupFailed
        expr: increase(backup_failures_total[1h]) > 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Backup failed"
          description: "{{ $labels.backup_type }} backup failed: {{ $labels.error_type }}"

      - alert: BackupSizeAnomaly
        expr: |
          abs(backup_size_bytes - backup_size_bytes offset 1d)
          / backup_size_bytes offset 1d > 0.5
        for: 0m
        labels:
          severity: warning
        annotations:
          summary: "Backup size changed significantly"
          description: "Backup size changed by more than 50%"
"""
```

### 31.9 Best Practices

| # | Practice | Description |
|---|----------|-------------|
| 1 | 3-2-1 Rule | 3 copies, 2 media types, 1 offsite |
| 2 | Test Restores | Regularly test restoration process |
| 3 | Encrypt Backups | Encrypt sensitive data at rest |
| 4 | Monitor Backups | Alert on missing or failed backups |
| 5 | Document Runbooks | Maintain up-to-date recovery procedures |
| 6 | Automate | Automate backup and recovery processes |
| 7 | Version Control | Keep backup scripts in version control |
| 8 | Separate Credentials | Use separate credentials for backups |

---

## Standard #32: Webhook System

### 32.1 Overview

Webhook System memungkinkan sistem mengirim notifikasi real-time ke external services ketika event tertentu terjadi. Ini memungkinkan integrasi dengan third-party systems.

### 32.2 Webhook Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        WEBHOOK ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      APPLICATION                                  │   │
│  │                                                                   │   │
│  │   Event Occurs ──► Event Bus ──► Webhook Dispatcher              │   │
│  │   (booking.created)              │                                │   │
│  │                                  │                                │   │
│  └──────────────────────────────────┼────────────────────────────────┘   │
│                                     │                                    │
│                                     ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    WEBHOOK QUEUE (Redis/RabbitMQ)                │   │
│  │                                                                   │   │
│  │   [webhook_job_1] [webhook_job_2] [webhook_job_3] ...           │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                     │                                    │
│                                     ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    WEBHOOK WORKER (Celery)                       │   │
│  │                                                                   │   │
│  │   1. Get webhook config                                          │   │
│  │   2. Build payload                                               │   │
│  │   3. Sign request (HMAC)                                         │   │
│  │   4. Send HTTP POST                                              │   │
│  │   5. Handle response/retry                                       │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                     │                                    │
│              ┌──────────────────────┼──────────────────────┐            │
│              ▼                      ▼                      ▼            │
│     ┌─────────────┐        ┌─────────────┐        ┌─────────────┐      │
│     │  External   │        │  External   │        │  External   │      │
│     │  Service A  │        │  Service B  │        │  Service C  │      │
│     │  (PMS)      │        │  (Slack)    │        │  (Custom)   │      │
│     └─────────────┘        └─────────────┘        └─────────────┘      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 32.3 Database Schema

```sql
-- Webhook endpoints configuration
CREATE TABLE webhook_endpoints (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Endpoint info
    name VARCHAR(200) NOT NULL,
    url VARCHAR(2000) NOT NULL,
    description TEXT,

    -- Authentication
    secret_key VARCHAR(255) NOT NULL,  -- For HMAC signing
    auth_type VARCHAR(50) DEFAULT 'hmac',  -- hmac, bearer, basic, none
    auth_config JSONB DEFAULT '{}',  -- Additional auth config

    -- Events to subscribe
    events TEXT[] NOT NULL,  -- ['booking.created', 'booking.updated']

    -- Configuration
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    timeout_seconds INTEGER DEFAULT 30,
    retry_count INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 60,

    -- Headers
    custom_headers JSONB DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT valid_url CHECK (url ~ '^https?://'),
    CONSTRAINT valid_timeout CHECK (timeout_seconds BETWEEN 5 AND 120)
);

-- Webhook delivery logs
CREATE TABLE webhook_deliveries (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    endpoint_id INTEGER NOT NULL REFERENCES webhook_endpoints(id) ON DELETE CASCADE,

    -- Event info
    event_type VARCHAR(100) NOT NULL,
    event_id VARCHAR(100) NOT NULL,  -- Unique event identifier
    payload JSONB NOT NULL,

    -- Delivery status
    status VARCHAR(50) NOT NULL,  -- pending, success, failed, retrying
    attempt_count INTEGER DEFAULT 0,
    next_retry_at TIMESTAMP WITH TIME ZONE,

    -- Response info
    response_status_code INTEGER,
    response_body TEXT,
    response_headers JSONB,
    response_time_ms INTEGER,

    -- Error info
    error_message TEXT,
    error_type VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    delivered_at TIMESTAMP WITH TIME ZONE,

    -- Indexes
    CONSTRAINT valid_status CHECK (status IN ('pending', 'success', 'failed', 'retrying'))
);

-- Indexes
CREATE INDEX idx_webhook_endpoints_org ON webhook_endpoints(organization_id);
CREATE INDEX idx_webhook_endpoints_active ON webhook_endpoints(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_webhook_deliveries_endpoint ON webhook_deliveries(endpoint_id);
CREATE INDEX idx_webhook_deliveries_status ON webhook_deliveries(status);
CREATE INDEX idx_webhook_deliveries_retry ON webhook_deliveries(next_retry_at) WHERE status = 'retrying';
```

### 32.4 Webhook Events

```python
# shared/webhooks/events.py
from enum import Enum
from typing import Dict, Any

class WebhookEvent(str, Enum):
    """Available webhook events"""

    # Booking events
    BOOKING_CREATED = "booking.created"
    BOOKING_UPDATED = "booking.updated"
    BOOKING_CANCELLED = "booking.cancelled"
    BOOKING_CHECKED_IN = "booking.checked_in"
    BOOKING_CHECKED_OUT = "booking.checked_out"

    # Guest events
    GUEST_CREATED = "guest.created"
    GUEST_UPDATED = "guest.updated"

    # Payment events
    PAYMENT_RECEIVED = "payment.received"
    PAYMENT_REFUNDED = "payment.refunded"
    PAYMENT_FAILED = "payment.failed"

    # Room events
    ROOM_STATUS_CHANGED = "room.status_changed"
    ROOM_MAINTENANCE = "room.maintenance"

    # Order events (POS)
    ORDER_CREATED = "order.created"
    ORDER_COMPLETED = "order.completed"
    ORDER_CANCELLED = "order.cancelled"

    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DEACTIVATED = "user.deactivated"

    # System events
    SYSTEM_HEALTH = "system.health"
    BACKUP_COMPLETED = "backup.completed"


# Event payload schemas
WEBHOOK_PAYLOAD_SCHEMAS: Dict[WebhookEvent, Dict[str, Any]] = {
    WebhookEvent.BOOKING_CREATED: {
        "type": "object",
        "properties": {
            "booking_id": {"type": "integer"},
            "confirmation_number": {"type": "string"},
            "guest_name": {"type": "string"},
            "check_in_date": {"type": "string", "format": "date"},
            "check_out_date": {"type": "string", "format": "date"},
            "room_type": {"type": "string"},
            "total_amount": {"type": "number"},
            "status": {"type": "string"}
        },
        "required": ["booking_id", "confirmation_number", "status"]
    },
    # ... other schemas
}
```

### 32.5 Webhook Dispatcher

```python
# shared/webhooks/dispatcher.py
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import List, Optional
from celery import shared_task
import httpx

class WebhookDispatcher:
    """Dispatch webhooks to registered endpoints"""

    def __init__(self, endpoint_repo, delivery_repo, event_bus):
        self.endpoint_repo = endpoint_repo
        self.delivery_repo = delivery_repo
        self.event_bus = event_bus

    async def dispatch(
        self,
        event_type: str,
        payload: dict,
        organization_id: int
    ):
        """Dispatch webhook to all subscribed endpoints"""

        # Get active endpoints for this event
        endpoints = await self.endpoint_repo.get_by_event(
            organization_id=organization_id,
            event_type=event_type
        )

        if not endpoints:
            return

        # Generate unique event ID
        event_id = self._generate_event_id(event_type, payload)

        # Create delivery records and queue jobs
        for endpoint in endpoints:
            # Create delivery record
            delivery = await self.delivery_repo.create({
                "endpoint_id": endpoint.id,
                "event_type": event_type,
                "event_id": event_id,
                "payload": payload,
                "status": "pending"
            })

            # Queue delivery job
            deliver_webhook.delay(delivery.id)

    def _generate_event_id(self, event_type: str, payload: dict) -> str:
        """Generate unique event ID"""
        timestamp = datetime.utcnow().isoformat()
        data = f"{event_type}:{timestamp}:{json.dumps(payload, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,)
)
def deliver_webhook(self, delivery_id: int):
    """Celery task to deliver webhook"""
    from shared.database import get_db_sync
    from shared.webhooks.delivery import WebhookDeliveryService

    with get_db_sync() as db:
        service = WebhookDeliveryService(db)
        result = service.deliver(delivery_id)

        if not result.success:
            # Retry with exponential backoff
            retry_delay = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=retry_delay)
```

### 32.6 Webhook Delivery Service

```python
# shared/webhooks/delivery.py
import hmac
import hashlib
import json
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import httpx

@dataclass
class DeliveryResult:
    success: bool
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    response_time_ms: Optional[int] = None
    error: Optional[str] = None

class WebhookDeliveryService:
    """Service for delivering webhooks"""

    def __init__(self, db):
        self.db = db

    def deliver(self, delivery_id: int) -> DeliveryResult:
        """Deliver a webhook"""
        # Get delivery and endpoint
        delivery = self.db.query(WebhookDelivery).get(delivery_id)
        endpoint = delivery.endpoint

        if not endpoint.is_active:
            return self._mark_failed(delivery, "Endpoint is disabled")

        # Build request
        payload = self._build_payload(delivery)
        headers = self._build_headers(endpoint, payload)

        # Send request
        start_time = datetime.utcnow()
        try:
            with httpx.Client(timeout=endpoint.timeout_seconds) as client:
                response = client.post(
                    endpoint.url,
                    json=payload,
                    headers=headers
                )

            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Update delivery record
            delivery.response_status_code = response.status_code
            delivery.response_body = response.text[:10000]  # Truncate
            delivery.response_headers = dict(response.headers)
            delivery.response_time_ms = int(response_time)
            delivery.attempt_count += 1

            if 200 <= response.status_code < 300:
                delivery.status = "success"
                delivery.delivered_at = datetime.utcnow()
                self.db.commit()

                return DeliveryResult(
                    success=True,
                    status_code=response.status_code,
                    response_body=response.text,
                    response_time_ms=int(response_time)
                )
            else:
                return self._handle_failure(
                    delivery,
                    f"HTTP {response.status_code}: {response.text[:500]}"
                )

        except httpx.TimeoutException:
            return self._handle_failure(delivery, "Request timeout")
        except httpx.RequestError as e:
            return self._handle_failure(delivery, f"Request error: {str(e)}")
        except Exception as e:
            return self._handle_failure(delivery, f"Unexpected error: {str(e)}")

    def _build_payload(self, delivery) -> dict:
        """Build webhook payload"""
        return {
            "id": delivery.event_id,
            "type": delivery.event_type,
            "created_at": delivery.created_at.isoformat(),
            "data": delivery.payload
        }

    def _build_headers(self, endpoint, payload: dict) -> dict:
        """Build request headers with signature"""
        timestamp = str(int(datetime.utcnow().timestamp()))
        payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)

        # HMAC signature
        signature_payload = f"{timestamp}.{payload_str}"
        signature = hmac.new(
            endpoint.secret_key.encode(),
            signature_payload.encode(),
            hashlib.sha256
        ).hexdigest()

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"t={timestamp},v1={signature}",
            "X-Webhook-ID": str(endpoint.id),
            "X-Event-Type": payload["type"],
            "User-Agent": "SignageWebhook/1.0"
        }

        # Add custom headers
        if endpoint.custom_headers:
            headers.update(endpoint.custom_headers)

        # Add auth headers
        if endpoint.auth_type == "bearer":
            headers["Authorization"] = f"Bearer {endpoint.auth_config.get('token')}"
        elif endpoint.auth_type == "basic":
            import base64
            credentials = f"{endpoint.auth_config.get('username')}:{endpoint.auth_config.get('password')}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        return headers

    def _handle_failure(self, delivery, error: str) -> DeliveryResult:
        """Handle delivery failure"""
        delivery.attempt_count += 1
        delivery.error_message = error
        delivery.error_type = error.split(":")[0] if ":" in error else "unknown"

        if delivery.attempt_count >= delivery.endpoint.retry_count:
            delivery.status = "failed"
        else:
            delivery.status = "retrying"
            # Exponential backoff
            delay = delivery.endpoint.retry_delay_seconds * (2 ** (delivery.attempt_count - 1))
            delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)

        self.db.commit()

        return DeliveryResult(
            success=False,
            error=error
        )
```

### 32.7 Webhook Signature Verification (Client Side)

```python
# Example: How webhook receivers should verify signatures
import hmac
import hashlib
from datetime import datetime

def verify_webhook_signature(
    payload: str,
    signature_header: str,
    secret: str,
    tolerance_seconds: int = 300
) -> bool:
    """
    Verify webhook signature.
    Call this in your webhook receiver endpoint.
    """
    try:
        # Parse signature header
        # Format: t=1234567890,v1=abc123...
        parts = dict(p.split("=") for p in signature_header.split(","))
        timestamp = int(parts["t"])
        signature = parts["v1"]

        # Check timestamp (prevent replay attacks)
        now = int(datetime.utcnow().timestamp())
        if abs(now - timestamp) > tolerance_seconds:
            return False

        # Verify signature
        expected_payload = f"{timestamp}.{payload}"
        expected_signature = hmac.new(
            secret.encode(),
            expected_payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    except Exception:
        return False


# Example webhook receiver (FastAPI)
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

@app.post("/webhooks/signage")
async def receive_webhook(request: Request):
    # Get raw body
    body = await request.body()
    payload = body.decode()

    # Get signature header
    signature = request.headers.get("X-Webhook-Signature")
    if not signature:
        raise HTTPException(400, "Missing signature")

    # Verify signature
    secret = "your-webhook-secret"
    if not verify_webhook_signature(payload, signature, secret):
        raise HTTPException(401, "Invalid signature")

    # Process webhook
    data = json.loads(payload)
    event_type = data["type"]
    event_data = data["data"]

    # Handle different event types
    if event_type == "booking.created":
        await handle_new_booking(event_data)
    elif event_type == "booking.cancelled":
        await handle_booking_cancellation(event_data)

    # Return 200 to acknowledge receipt
    return {"status": "received"}
```

### 32.8 API Endpoints

```python
# services/webhook/routes.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.get("/endpoints", response_model=List[WebhookEndpointResponse])
async def list_endpoints(
    current_user = Depends(get_current_user),
    endpoint_repo = Depends(get_endpoint_repo)
):
    """List all webhook endpoints for organization"""
    return await endpoint_repo.get_all(
        organization_id=current_user.organization_id
    )

@router.post("/endpoints", response_model=WebhookEndpointResponse)
async def create_endpoint(
    request: CreateWebhookEndpointRequest,
    current_user = Depends(get_current_user),
    endpoint_repo = Depends(get_endpoint_repo)
):
    """Create a new webhook endpoint"""
    # Generate secret key
    import secrets
    secret_key = secrets.token_hex(32)

    endpoint = await endpoint_repo.create({
        "organization_id": current_user.organization_id,
        "name": request.name,
        "url": request.url,
        "description": request.description,
        "secret_key": secret_key,
        "events": request.events,
        "custom_headers": request.custom_headers,
        "created_by_id": current_user.id
    })

    # Return with secret (only shown once)
    return {
        **endpoint.__dict__,
        "secret_key": secret_key  # Only returned on creation
    }

@router.post("/endpoints/{endpoint_id}/test")
async def test_endpoint(
    endpoint_id: int,
    current_user = Depends(get_current_user),
    delivery_service = Depends(get_delivery_service)
):
    """Send a test webhook to endpoint"""
    test_payload = {
        "type": "test",
        "message": "This is a test webhook",
        "timestamp": datetime.utcnow().isoformat()
    }

    result = await delivery_service.send_test(endpoint_id, test_payload)

    return {
        "success": result.success,
        "status_code": result.status_code,
        "response_time_ms": result.response_time_ms,
        "error": result.error
    }

@router.get("/endpoints/{endpoint_id}/deliveries")
async def list_deliveries(
    endpoint_id: int,
    status: Optional[str] = None,
    limit: int = 50,
    current_user = Depends(get_current_user),
    delivery_repo = Depends(get_delivery_repo)
):
    """List webhook deliveries for endpoint"""
    return await delivery_repo.get_by_endpoint(
        endpoint_id=endpoint_id,
        status=status,
        limit=limit
    )

@router.post("/endpoints/{endpoint_id}/deliveries/{delivery_id}/retry")
async def retry_delivery(
    endpoint_id: int,
    delivery_id: int,
    current_user = Depends(get_current_user)
):
    """Manually retry a failed delivery"""
    deliver_webhook.delay(delivery_id)
    return {"status": "queued"}
```

### 32.9 Best Practices

| # | Practice | Description |
|---|----------|-------------|
| 1 | Sign Requests | Always sign webhooks dengan HMAC |
| 2 | Idempotency | Include unique event ID untuk idempotent handling |
| 3 | Retry with Backoff | Exponential backoff untuk failed deliveries |
| 4 | Timeout | Set reasonable timeout (30s default) |
| 5 | Log Everything | Log all delivery attempts dan responses |
| 6 | Test Endpoint | Provide test endpoint untuk debugging |
| 7 | Rate Limit | Limit webhook frequency per endpoint |
| 8 | Async Delivery | Deliver webhooks asynchronously |

---

## Standard #33: Report Generation

### 33.1 Overview

Report Generation memungkinkan user membuat laporan dari data sistem. Reports dapat di-generate on-demand atau scheduled, dan di-export dalam berbagai format (PDF, Excel, CSV).

### 33.2 Report Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       REPORT GENERATION ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        USER REQUEST                              │   │
│  │                                                                   │   │
│  │   1. Select report type                                          │   │
│  │   2. Set parameters (date range, filters)                        │   │
│  │   3. Choose format (PDF/Excel/CSV)                              │   │
│  │   4. Submit                                                       │   │
│  │                                                                   │   │
│  └───────────────────────────┬─────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     REPORT SERVICE                               │   │
│  │                                                                   │   │
│  │   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │   │
│  │   │   Report     │   │    Data      │   │   Export     │        │   │
│  │   │  Definition  │──►│  Aggregator  │──►│   Engine     │        │   │
│  │   │  (Template)  │   │   (Query)    │   │  (PDF/XLSX)  │        │   │
│  │   └──────────────┘   └──────────────┘   └──────────────┘        │   │
│  │                                                                   │   │
│  └───────────────────────────┬─────────────────────────────────────┘   │
│                              │                                          │
│              ┌───────────────┴───────────────┐                         │
│              ▼                               ▼                         │
│  ┌───────────────────┐           ┌───────────────────┐                 │
│  │  SYNC (< 30s)     │           │  ASYNC (> 30s)    │                 │
│  │                   │           │                   │                 │
│  │  Return file      │           │  Queue job        │                 │
│  │  directly         │           │  Notify when done │                 │
│  │                   │           │  Download link    │                 │
│  └───────────────────┘           └───────────────────┘                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 33.3 Database Schema

```sql
-- Report definitions (templates)
CREATE TABLE report_definitions (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,  -- NULL = system report

    -- Report info
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,  -- financial, operational, guest, inventory

    -- Query & Template
    query_template TEXT NOT NULL,  -- SQL with parameters
    parameters_schema JSONB NOT NULL,  -- JSON Schema for parameters
    columns_config JSONB NOT NULL,  -- Column definitions

    -- Options
    available_formats TEXT[] DEFAULT ARRAY['pdf', 'xlsx', 'csv'],
    default_format VARCHAR(10) DEFAULT 'pdf',
    is_scheduled_enabled BOOLEAN DEFAULT FALSE,
    max_rows INTEGER DEFAULT 10000,

    -- Access control
    required_permission VARCHAR(100),

    -- Metadata
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Report generation jobs
CREATE TABLE report_jobs (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    definition_id INTEGER NOT NULL REFERENCES report_definitions(id),

    -- Job info
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed
    parameters JSONB NOT NULL,
    output_format VARCHAR(10) NOT NULL,

    -- Progress
    progress_percent INTEGER DEFAULT 0,
    progress_message TEXT,
    rows_processed INTEGER DEFAULT 0,
    total_rows INTEGER,

    -- Output
    file_path VARCHAR(500),
    file_size_bytes BIGINT,
    file_url VARCHAR(2000),
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Audit
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled'))
);

-- Scheduled reports
CREATE TABLE report_schedules (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    definition_id INTEGER NOT NULL REFERENCES report_definitions(id),

    -- Schedule info
    name VARCHAR(200) NOT NULL,
    cron_expression VARCHAR(100) NOT NULL,  -- "0 8 * * 1" = Every Monday 8am
    timezone VARCHAR(50) DEFAULT 'UTC',

    -- Parameters
    parameters JSONB NOT NULL,
    output_format VARCHAR(10) NOT NULL,

    -- Delivery
    delivery_method VARCHAR(50) NOT NULL,  -- email, webhook, storage
    delivery_config JSONB NOT NULL,  -- Email addresses, webhook URL, etc.

    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    last_status VARCHAR(50),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_report_jobs_org ON report_jobs(organization_id);
CREATE INDEX idx_report_jobs_status ON report_jobs(status);
CREATE INDEX idx_report_schedules_next_run ON report_schedules(next_run_at) WHERE is_active = TRUE;
```

### 33.4 Report Definitions

```python
# services/reports/definitions.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class ReportCategory(str, Enum):
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    GUEST = "guest"
    INVENTORY = "inventory"
    HR = "hr"
    ANALYTICS = "analytics"

@dataclass
class ReportColumn:
    """Column definition for report"""
    key: str
    label: str
    type: str  # string, number, currency, date, datetime, boolean
    width: Optional[int] = None
    format: Optional[str] = None  # Format string (e.g., "0.00" for numbers)
    align: str = "left"  # left, center, right
    aggregate: Optional[str] = None  # sum, avg, count, min, max

@dataclass
class ReportParameter:
    """Parameter definition for report"""
    key: str
    label: str
    type: str  # string, number, date, date_range, select, multi_select
    required: bool = True
    default: Any = None
    options: Optional[List[Dict]] = None  # For select types

# Example: Daily Revenue Report
DAILY_REVENUE_REPORT = {
    "code": "daily_revenue",
    "name": "Daily Revenue Report",
    "description": "Summary of daily revenue by department",
    "category": ReportCategory.FINANCIAL,

    "parameters_schema": {
        "type": "object",
        "properties": {
            "date_from": {
                "type": "string",
                "format": "date",
                "title": "From Date"
            },
            "date_to": {
                "type": "string",
                "format": "date",
                "title": "To Date"
            },
            "department": {
                "type": "string",
                "title": "Department",
                "enum": ["all", "rooms", "fnb", "spa", "other"]
            }
        },
        "required": ["date_from", "date_to"]
    },

    "query_template": """
        SELECT
            DATE(transaction_date) as date,
            department,
            COUNT(*) as transaction_count,
            SUM(amount) as gross_revenue,
            SUM(discount) as total_discount,
            SUM(tax) as total_tax,
            SUM(amount - discount + tax) as net_revenue
        FROM transactions
        WHERE organization_id = :organization_id
            AND transaction_date >= :date_from
            AND transaction_date <= :date_to
            AND (:department = 'all' OR department = :department)
        GROUP BY DATE(transaction_date), department
        ORDER BY date DESC, department
    """,

    "columns_config": [
        {"key": "date", "label": "Date", "type": "date", "width": 100},
        {"key": "department", "label": "Department", "type": "string", "width": 120},
        {"key": "transaction_count", "label": "Transactions", "type": "number", "align": "right"},
        {"key": "gross_revenue", "label": "Gross Revenue", "type": "currency", "align": "right", "aggregate": "sum"},
        {"key": "total_discount", "label": "Discounts", "type": "currency", "align": "right", "aggregate": "sum"},
        {"key": "total_tax", "label": "Tax", "type": "currency", "align": "right", "aggregate": "sum"},
        {"key": "net_revenue", "label": "Net Revenue", "type": "currency", "align": "right", "aggregate": "sum"}
    ],

    "available_formats": ["pdf", "xlsx", "csv"],
    "required_permission": "reports.financial.view"
}
```

### 33.5 Report Generation Service

```python
# services/reports/generator.py
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

@dataclass
class ReportResult:
    success: bool
    job_id: Optional[int] = None
    file_url: Optional[str] = None
    file_path: Optional[str] = None
    error: Optional[str] = None
    is_async: bool = False

class ReportGenerator:
    """Generate reports from definitions"""

    def __init__(
        self,
        db,
        definition_repo,
        job_repo,
        storage_service,
        exporters: Dict[str, 'ReportExporter']
    ):
        self.db = db
        self.definition_repo = definition_repo
        self.job_repo = job_repo
        self.storage = storage_service
        self.exporters = exporters

    async def generate(
        self,
        definition_code: str,
        parameters: Dict[str, Any],
        output_format: str,
        organization_id: int,
        user_id: int,
        force_async: bool = False
    ) -> ReportResult:
        """Generate a report"""

        # Get definition
        definition = await self.definition_repo.get_by_code(definition_code)
        if not definition:
            return ReportResult(success=False, error="Report definition not found")

        # Validate parameters
        is_valid, errors = self._validate_parameters(definition, parameters)
        if not is_valid:
            return ReportResult(success=False, error=f"Invalid parameters: {errors}")

        # Estimate size to determine sync/async
        estimated_rows = await self._estimate_rows(definition, parameters, organization_id)

        if estimated_rows > 1000 or force_async:
            # Generate asynchronously
            return await self._generate_async(
                definition, parameters, output_format, organization_id, user_id
            )
        else:
            # Generate synchronously
            return await self._generate_sync(
                definition, parameters, output_format, organization_id, user_id
            )

    async def _generate_sync(
        self,
        definition,
        parameters: Dict,
        output_format: str,
        organization_id: int,
        user_id: int
    ) -> ReportResult:
        """Generate report synchronously (for small reports)"""
        try:
            # Execute query
            data = await self._execute_query(definition, parameters, organization_id)

            # Export to format
            exporter = self.exporters[output_format]
            file_bytes = await exporter.export(
                data=data,
                columns=definition.columns_config,
                title=definition.name,
                parameters=parameters
            )

            # Save to storage
            filename = self._generate_filename(definition.code, output_format)
            file_url = await self.storage.upload(
                file_bytes,
                filename,
                content_type=exporter.content_type
            )

            return ReportResult(
                success=True,
                file_url=file_url,
                is_async=False
            )

        except Exception as e:
            return ReportResult(success=False, error=str(e))

    async def _generate_async(
        self,
        definition,
        parameters: Dict,
        output_format: str,
        organization_id: int,
        user_id: int
    ) -> ReportResult:
        """Queue report for async generation"""

        # Create job record
        job = await self.job_repo.create({
            "organization_id": organization_id,
            "definition_id": definition.id,
            "parameters": parameters,
            "output_format": output_format,
            "status": "pending",
            "created_by_id": user_id
        })

        # Queue Celery task
        from tasks.reports import generate_report_task
        generate_report_task.delay(job.id)

        return ReportResult(
            success=True,
            job_id=job.id,
            is_async=True
        )

    async def _execute_query(
        self,
        definition,
        parameters: Dict,
        organization_id: int
    ) -> List[Dict]:
        """Execute report query with parameters"""

        # Add organization_id to parameters
        params = {**parameters, "organization_id": organization_id}

        # Execute query
        result = await self.db.execute(
            definition.query_template,
            params
        )

        # Convert to list of dicts
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]

    async def _estimate_rows(
        self,
        definition,
        parameters: Dict,
        organization_id: int
    ) -> int:
        """Estimate number of rows in report"""
        # Simple estimation using COUNT
        count_query = f"""
            SELECT COUNT(*) FROM ({definition.query_template}) AS subquery
        """
        params = {**parameters, "organization_id": organization_id}
        result = await self.db.execute(count_query, params)
        return result.scalar() or 0

    def _generate_filename(self, code: str, format: str) -> str:
        """Generate unique filename"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"reports/{code}_{timestamp}.{format}"
```

### 33.6 Export Engines

```python
# services/reports/exporters/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ReportExporter(ABC):
    """Base class for report exporters"""

    @property
    @abstractmethod
    def content_type(self) -> str:
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        pass

    @abstractmethod
    async def export(
        self,
        data: List[Dict],
        columns: List[Dict],
        title: str,
        parameters: Dict[str, Any]
    ) -> bytes:
        """Export data to format"""
        pass


# services/reports/exporters/pdf.py
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

class PDFExporter(ReportExporter):
    """Export reports to PDF"""

    @property
    def content_type(self) -> str:
        return "application/pdf"

    @property
    def file_extension(self) -> str:
        return "pdf"

    async def export(
        self,
        data: List[Dict],
        columns: List[Dict],
        title: str,
        parameters: Dict[str, Any]
    ) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        elements = []
        styles = getSampleStyleSheet()

        # Title
        elements.append(Paragraph(title, styles['Heading1']))
        elements.append(Spacer(1, 12))

        # Parameters summary
        param_text = " | ".join([f"{k}: {v}" for k, v in parameters.items()])
        elements.append(Paragraph(param_text, styles['Normal']))
        elements.append(Spacer(1, 20))

        # Table header
        header = [col['label'] for col in columns]

        # Table data
        table_data = [header]
        for row in data:
            table_row = []
            for col in columns:
                value = row.get(col['key'], '')
                formatted = self._format_value(value, col)
                table_row.append(formatted)
            table_data.append(table_row)

        # Add totals row if aggregates defined
        totals = self._calculate_totals(data, columns)
        if any(totals):
            table_data.append(totals)

        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(table)

        # Build PDF
        doc.build(elements)
        return buffer.getvalue()

    def _format_value(self, value, column: Dict) -> str:
        """Format value based on column type"""
        if value is None:
            return ""

        col_type = column.get('type', 'string')

        if col_type == 'currency':
            return f"Rp {value:,.0f}"
        elif col_type == 'number':
            format_str = column.get('format', ',.0f')
            return f"{value:{format_str}}"
        elif col_type == 'date':
            if isinstance(value, str):
                return value
            return value.strftime('%Y-%m-%d')
        elif col_type == 'datetime':
            if isinstance(value, str):
                return value
            return value.strftime('%Y-%m-%d %H:%M')
        elif col_type == 'boolean':
            return "Yes" if value else "No"

        return str(value)

    def _calculate_totals(self, data: List[Dict], columns: List[Dict]) -> List[str]:
        """Calculate totals for columns with aggregates"""
        totals = []
        first_col = True

        for col in columns:
            aggregate = col.get('aggregate')

            if first_col:
                totals.append("TOTAL")
                first_col = False
                continue

            if not aggregate:
                totals.append("")
                continue

            values = [row.get(col['key'], 0) or 0 for row in data]

            if aggregate == 'sum':
                result = sum(values)
            elif aggregate == 'avg':
                result = sum(values) / len(values) if values else 0
            elif aggregate == 'count':
                result = len(values)
            elif aggregate == 'min':
                result = min(values) if values else 0
            elif aggregate == 'max':
                result = max(values) if values else 0
            else:
                result = ""

            totals.append(self._format_value(result, col))

        return totals


# services/reports/exporters/excel.py
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO

class ExcelExporter(ReportExporter):
    """Export reports to Excel"""

    @property
    def content_type(self) -> str:
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    @property
    def file_extension(self) -> str:
        return "xlsx"

    async def export(
        self,
        data: List[Dict],
        columns: List[Dict],
        title: str,
        parameters: Dict[str, Any]
    ) -> bytes:
        wb = Workbook()
        ws = wb.active
        ws.title = title[:31]  # Excel limit

        # Styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # Title row
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(columns))
        ws.cell(row=1, column=1, value=title).font = Font(bold=True, size=14)

        # Parameters row
        param_text = " | ".join([f"{k}: {v}" for k, v in parameters.items()])
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(columns))
        ws.cell(row=2, column=1, value=param_text)

        # Header row
        header_row = 4
        for col_idx, col in enumerate(columns, 1):
            cell = ws.cell(row=header_row, column=col_idx, value=col['label'])
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = border

            # Set column width
            width = col.get('width', 100) / 7  # Approximate conversion
            ws.column_dimensions[get_column_letter(col_idx)].width = width

        # Data rows
        for row_idx, row_data in enumerate(data, header_row + 1):
            for col_idx, col in enumerate(columns, 1):
                value = row_data.get(col['key'], '')
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = border

                # Alignment based on column type
                if col.get('type') in ['number', 'currency']:
                    cell.alignment = Alignment(horizontal="right")
                elif col.get('align'):
                    cell.alignment = Alignment(horizontal=col['align'])

                # Number formatting
                if col.get('type') == 'currency':
                    cell.number_format = '#,##0'
                elif col.get('type') == 'number' and col.get('format'):
                    cell.number_format = col['format']

        # Totals row
        totals_row = header_row + len(data) + 1
        for col_idx, col in enumerate(columns, 1):
            aggregate = col.get('aggregate')
            if col_idx == 1:
                cell = ws.cell(row=totals_row, column=col_idx, value="TOTAL")
                cell.font = Font(bold=True)
            elif aggregate == 'sum':
                # Excel formula for sum
                start_cell = f"{get_column_letter(col_idx)}{header_row + 1}"
                end_cell = f"{get_column_letter(col_idx)}{totals_row - 1}"
                cell = ws.cell(row=totals_row, column=col_idx, value=f"=SUM({start_cell}:{end_cell})")
                cell.font = Font(bold=True)
                if col.get('type') == 'currency':
                    cell.number_format = '#,##0'

            cell = ws.cell(row=totals_row, column=col_idx)
            cell.border = border

        # Save to buffer
        buffer = BytesIO()
        wb.save(buffer)
        return buffer.getvalue()


# services/reports/exporters/csv.py
import csv
from io import StringIO

class CSVExporter(ReportExporter):
    """Export reports to CSV"""

    @property
    def content_type(self) -> str:
        return "text/csv"

    @property
    def file_extension(self) -> str:
        return "csv"

    async def export(
        self,
        data: List[Dict],
        columns: List[Dict],
        title: str,
        parameters: Dict[str, Any]
    ) -> bytes:
        buffer = StringIO()
        writer = csv.writer(buffer)

        # Header
        header = [col['label'] for col in columns]
        writer.writerow(header)

        # Data
        for row in data:
            row_data = [row.get(col['key'], '') for col in columns]
            writer.writerow(row_data)

        return buffer.getvalue().encode('utf-8-sig')  # BOM for Excel compatibility
```

### 33.7 Scheduled Reports

```python
# services/reports/scheduler.py
from celery import shared_task
from celery.schedules import crontab
from datetime import datetime, timedelta

@shared_task
def process_scheduled_reports():
    """Process due scheduled reports - runs every minute"""
    from shared.database import get_db_sync

    with get_db_sync() as db:
        # Get due schedules
        now = datetime.utcnow()
        schedules = db.query(ReportSchedule).filter(
            ReportSchedule.is_active == True,
            ReportSchedule.next_run_at <= now
        ).all()

        for schedule in schedules:
            try:
                # Generate report
                generate_scheduled_report.delay(schedule.id)

                # Update next run time
                schedule.next_run_at = calculate_next_run(
                    schedule.cron_expression,
                    schedule.timezone
                )
                schedule.last_run_at = now

            except Exception as e:
                schedule.last_status = f"error: {str(e)}"

            db.commit()

@shared_task
def generate_scheduled_report(schedule_id: int):
    """Generate a scheduled report and deliver it"""
    from shared.database import get_db_sync

    with get_db_sync() as db:
        schedule = db.query(ReportSchedule).get(schedule_id)

        # Generate report
        generator = ReportGenerator(...)
        result = await generator.generate(
            definition_code=schedule.definition.code,
            parameters=schedule.parameters,
            output_format=schedule.output_format,
            organization_id=schedule.organization_id,
            user_id=schedule.created_by_id,
            force_async=False  # Run synchronously in task
        )

        if result.success:
            # Deliver report
            await deliver_scheduled_report(schedule, result.file_url)
            schedule.last_status = "success"
        else:
            schedule.last_status = f"failed: {result.error}"

        db.commit()

async def deliver_scheduled_report(schedule, file_url: str):
    """Deliver report based on delivery method"""

    if schedule.delivery_method == "email":
        await send_report_email(
            to=schedule.delivery_config.get("recipients", []),
            subject=f"Scheduled Report: {schedule.name}",
            report_url=file_url,
            report_name=schedule.definition.name
        )

    elif schedule.delivery_method == "webhook":
        await send_webhook(
            url=schedule.delivery_config.get("url"),
            payload={
                "report_name": schedule.name,
                "report_url": file_url,
                "generated_at": datetime.utcnow().isoformat()
            }
        )

    elif schedule.delivery_method == "storage":
        # Copy to specific storage location
        destination = schedule.delivery_config.get("path")
        await copy_to_storage(file_url, destination)
```

### 33.8 API Endpoints

```python
# services/reports/routes.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/definitions")
async def list_report_definitions(
    category: Optional[str] = None,
    current_user = Depends(get_current_user),
    definition_repo = Depends(get_definition_repo)
):
    """List available report definitions"""
    definitions = await definition_repo.get_all(
        organization_id=current_user.organization_id,
        category=category
    )

    # Filter by permissions
    return [
        d for d in definitions
        if not d.required_permission or d.required_permission in current_user.permissions
    ]

@router.post("/generate")
async def generate_report(
    request: GenerateReportRequest,
    current_user = Depends(get_current_user),
    generator: ReportGenerator = Depends()
):
    """Generate a report"""
    result = await generator.generate(
        definition_code=request.definition_code,
        parameters=request.parameters,
        output_format=request.format,
        organization_id=current_user.organization_id,
        user_id=current_user.id
    )

    if not result.success:
        raise HTTPException(400, result.error)

    if result.is_async:
        return {
            "status": "processing",
            "job_id": result.job_id,
            "message": "Report is being generated. You will be notified when ready."
        }
    else:
        return {
            "status": "completed",
            "file_url": result.file_url
        }

@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: int,
    current_user = Depends(get_current_user),
    job_repo = Depends(get_job_repo)
):
    """Get report job status"""
    job = await job_repo.get_by_id(job_id)

    if not job or job.organization_id != current_user.organization_id:
        raise HTTPException(404, "Job not found")

    return {
        "id": job.id,
        "status": job.status,
        "progress": job.progress_percent,
        "message": job.progress_message,
        "file_url": job.file_url if job.status == "completed" else None,
        "error": job.error_message if job.status == "failed" else None
    }

@router.get("/jobs/{job_id}/download")
async def download_report(
    job_id: int,
    current_user = Depends(get_current_user),
    job_repo = Depends(get_job_repo),
    storage = Depends(get_storage)
):
    """Download generated report"""
    job = await job_repo.get_by_id(job_id)

    if not job or job.organization_id != current_user.organization_id:
        raise HTTPException(404, "Job not found")

    if job.status != "completed":
        raise HTTPException(400, "Report not ready")

    # Stream file from storage
    file_stream = await storage.get_stream(job.file_path)
    filename = f"{job.definition.code}_{job.id}.{job.output_format}"

    return StreamingResponse(
        file_stream,
        media_type=get_content_type(job.output_format),
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.post("/schedules")
async def create_schedule(
    request: CreateScheduleRequest,
    current_user = Depends(get_current_user),
    schedule_repo = Depends(get_schedule_repo)
):
    """Create a scheduled report"""
    # Validate cron expression
    if not is_valid_cron(request.cron_expression):
        raise HTTPException(400, "Invalid cron expression")

    schedule = await schedule_repo.create({
        "organization_id": current_user.organization_id,
        "definition_id": request.definition_id,
        "name": request.name,
        "cron_expression": request.cron_expression,
        "timezone": request.timezone,
        "parameters": request.parameters,
        "output_format": request.format,
        "delivery_method": request.delivery_method,
        "delivery_config": request.delivery_config,
        "created_by_id": current_user.id,
        "next_run_at": calculate_next_run(request.cron_expression, request.timezone)
    })

    return schedule
```

### 33.9 Best Practices

| # | Practice | Description |
|---|----------|-------------|
| 1 | Async for Large Reports | Generate large reports asynchronously |
| 2 | Progress Updates | Provide progress updates untuk long-running reports |
| 3 | Row Limits | Set max row limits untuk prevent timeout |
| 4 | Caching | Cache frequently accessed reports |
| 5 | Parameterized Queries | Always use parameterized queries |
| 6 | Permission Checks | Check permissions before generating |
| 7 | Expiring Downloads | Set expiry untuk generated files |
| 8 | Audit Trail | Log all report generations |

---

## Summary

| Standard | Key Points |
|----------|------------|
| #31 Backup & DR | 3-2-1 rule, WAL archiving, tested recovery procedures |
| #32 Webhook System | HMAC signing, retry with backoff, delivery logs |
| #33 Report Generation | Async for large reports, multiple formats, scheduling |

---

*Last Updated: 2025-12-09*
