# 🚀 PHASE 4: DEVICE MANAGEMENT - IMPLEMENTATION GUIDE

**Timeline:** Week 6-7 (after Phase 3)
**Duration:** 10-14 days
**Risk Level:** Medium
**Downtime:** None (backward compatible)

---

## 📋 OVERVIEW

Phase 4 enhances device management with advanced features:
- ✅ Device grouping and tagging
- ✅ Remote command execution
- ✅ Device health monitoring
- ✅ Bulk device operations
- ✅ Device activity timeline

**What changes:**
- Database: 3 new tables (device_groups, device_commands, device_health)
- Backend: Device management API enhancements
- CMS: Enhanced device dashboard
- Player: Command listener integration

---

## 🎯 WEEK-BY-WEEK PLAN

### **Week 6: Backend + Database (Days 1-7)**
### **Week 7: Frontend + Player (Days 8-14)**

---

## 📅 WEEK 6: BACKEND + DATABASE

### Day 1: Database Migrations

```bash
# Step 1: Run Migration 017 (Device Groups & Tags)
docker exec -i signage-postgres psql -U signage_user -d signage_db \
  < database/fix-database/migrations/017_add_device_groups.sql

# Verify tables created
docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
  SELECT table_name FROM information_schema.tables
  WHERE table_name IN ('device_groups', 'device_group_members', 'device_tags');"

# Step 2: Run Migration 018 (Device Commands)
docker exec -i signage-postgres psql -U signage_user -d signage_db \
  < database/fix-database/migrations/018_add_device_commands.sql

# Verify
docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
  SELECT table_name FROM information_schema.tables
  WHERE table_name = 'device_commands';"

# Step 3: Run Migration 019 (Device Health)
docker exec -i signage-postgres psql -U signage_user -d signage_db \
  < database/fix-database/migrations/019_add_device_health.sql

# Verify
docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
  SELECT table_name FROM information_schema.tables
  WHERE table_name = 'device_health_metrics';"
```

**Migration 017: Device Groups**
```sql
-- database/fix-database/migrations/017_add_device_groups.sql

BEGIN;

-- Device Groups
CREATE TABLE device_groups (
  id SERIAL PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(organization_id, name)
);

-- Group Members (Many-to-Many)
CREATE TABLE device_group_members (
  id SERIAL PRIMARY KEY,
  group_id INTEGER NOT NULL REFERENCES device_groups(id) ON DELETE CASCADE,
  device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  added_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(group_id, device_id)
);

-- Device Tags (flexible tagging)
CREATE TABLE device_tags (
  id SERIAL PRIMARY KEY,
  device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  tag VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(device_id, tag)
);

-- Indexes
CREATE INDEX idx_device_groups_org ON device_groups(organization_id);
CREATE INDEX idx_device_group_members_group ON device_group_members(group_id);
CREATE INDEX idx_device_group_members_device ON device_group_members(device_id);
CREATE INDEX idx_device_tags_device ON device_tags(device_id);
CREATE INDEX idx_device_tags_tag ON device_tags(tag);

COMMIT;
```

**Migration 018: Device Commands**
```sql
-- database/fix-database/migrations/018_add_device_commands.sql

BEGIN;

-- Device Commands (for remote control)
CREATE TABLE device_commands (
  id SERIAL PRIMARY KEY,
  device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  organization_id INTEGER NOT NULL REFERENCES organizations(id),
  command_type VARCHAR(50) NOT NULL, -- 'reboot', 'screenshot', 'update_content', etc.
  payload JSONB,
  status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'sent', 'executed', 'failed'
  result JSONB,
  created_by INTEGER REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  sent_at TIMESTAMP,
  executed_at TIMESTAMP,
  failed_at TIMESTAMP,
  error_message TEXT
);

-- Indexes
CREATE INDEX idx_device_commands_device ON device_commands(device_id);
CREATE INDEX idx_device_commands_org ON device_commands(organization_id);
CREATE INDEX idx_device_commands_status ON device_commands(status);
CREATE INDEX idx_device_commands_created ON device_commands(created_at DESC);

COMMIT;
```

**Migration 019: Device Health**
```sql
-- database/fix-database/migrations/019_add_device_health.sql

BEGIN;

-- Device Health Metrics (time-series data)
CREATE TABLE device_health_metrics (
  id SERIAL PRIMARY KEY,
  device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  organization_id INTEGER NOT NULL REFERENCES organizations(id),

  -- System metrics
  cpu_usage DECIMAL(5,2),      -- Percentage (0-100)
  memory_usage DECIMAL(5,2),   -- Percentage (0-100)
  disk_usage DECIMAL(5,2),     -- Percentage (0-100)
  temperature DECIMAL(5,2),    -- Celsius

  -- Network metrics
  network_status VARCHAR(20),  -- 'online', 'offline', 'unstable'
  bandwidth_up INTEGER,        -- Kbps
  bandwidth_down INTEGER,      -- Kbps
  latency INTEGER,             -- ms

  -- Display metrics
  display_status VARCHAR(20),  -- 'on', 'off', 'standby'
  resolution VARCHAR(20),      -- '1920x1080'
  refresh_rate INTEGER,        -- Hz

  -- Timestamps
  recorded_at TIMESTAMP DEFAULT NOW()
);

-- Partitioning by month for performance
CREATE INDEX idx_device_health_device_time ON device_health_metrics(device_id, recorded_at DESC);
CREATE INDEX idx_device_health_org ON device_health_metrics(organization_id);
CREATE INDEX idx_device_health_time ON device_health_metrics(recorded_at DESC);

COMMIT;
```

### Day 2-4: Backend Services

**Device Group Service:**
```python
# backend-python/services/device/group_service.py

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from .models import DeviceGroup, DeviceGroupMember, Device
from .dtos import DeviceGroupCreate, DeviceGroupUpdate

class DeviceGroupService:
    def __init__(self, db: Session):
        self.db = db

    def create_group(
        self,
        organization_id: int,
        data: DeviceGroupCreate
    ) -> DeviceGroup:
        """Create device group"""
        group = DeviceGroup(
            organization_id=organization_id,
            name=data.name,
            description=data.description
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)

        # Add initial devices
        if data.device_ids:
            self.add_devices_to_group(group.id, data.device_ids)

        return group

    def add_devices_to_group(
        self,
        group_id: int,
        device_ids: List[int]
    ):
        """Add devices to group"""
        for device_id in device_ids:
            member = DeviceGroupMember(
                group_id=group_id,
                device_id=device_id
            )
            self.db.add(member)

        self.db.commit()

    def remove_devices_from_group(
        self,
        group_id: int,
        device_ids: List[int]
    ):
        """Remove devices from group"""
        self.db.query(DeviceGroupMember).filter(
            and_(
                DeviceGroupMember.group_id == group_id,
                DeviceGroupMember.device_id.in_(device_ids)
            )
        ).delete(synchronize_session=False)
        self.db.commit()

    def get_group_devices(self, group_id: int) -> List[Device]:
        """Get all devices in group"""
        return self.db.query(Device).join(
            DeviceGroupMember,
            Device.id == DeviceGroupMember.device_id
        ).filter(
            DeviceGroupMember.group_id == group_id
        ).all()

    def get_device_groups(self, device_id: int) -> List[DeviceGroup]:
        """Get all groups a device belongs to"""
        return self.db.query(DeviceGroup).join(
            DeviceGroupMember,
            DeviceGroup.id == DeviceGroupMember.group_id
        ).filter(
            DeviceGroupMember.device_id == device_id
        ).all()
```

**Device Command Service:**
```python
# backend-python/services/device/command_service.py

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, Optional
from .models import DeviceCommand, Device
from .dtos import DeviceCommandCreate

class DeviceCommandService:
    def __init__(self, db: Session):
        self.db = db

    def create_command(
        self,
        device_id: int,
        organization_id: int,
        command_type: str,
        payload: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None
    ) -> DeviceCommand:
        """Create device command"""
        command = DeviceCommand(
            device_id=device_id,
            organization_id=organization_id,
            command_type=command_type,
            payload=payload,
            created_by=created_by,
            status='pending'
        )

        self.db.add(command)
        self.db.commit()
        self.db.refresh(command)

        # Publish to WebSocket for immediate delivery
        self.publish_command(command)

        return command

    def publish_command(self, command: DeviceCommand):
        """Publish command to WebSocket for device"""
        from shared.websocket import websocket_manager

        websocket_manager.send_to_device(
            device_id=command.device_id,
            message={
                'type': 'command',
                'command_id': command.id,
                'command_type': command.command_type,
                'payload': command.payload
            }
        )

        # Update status
        command.status = 'sent'
        command.sent_at = datetime.utcnow()
        self.db.commit()

    def mark_executed(
        self,
        command_id: int,
        result: Optional[Dict[str, Any]] = None
    ):
        """Mark command as executed"""
        command = self.db.query(DeviceCommand).filter(
            DeviceCommand.id == command_id
        ).first()

        if command:
            command.status = 'executed'
            command.executed_at = datetime.utcnow()
            command.result = result
            self.db.commit()

    def mark_failed(
        self,
        command_id: int,
        error_message: str
    ):
        """Mark command as failed"""
        command = self.db.query(DeviceCommand).filter(
            DeviceCommand.id == command_id
        ).first()

        if command:
            command.status = 'failed'
            command.failed_at = datetime.utcnow()
            command.error_message = error_message
            self.db.commit()

    def get_pending_commands(self, device_id: int) -> List[DeviceCommand]:
        """Get pending commands for device"""
        return self.db.query(DeviceCommand).filter(
            and_(
                DeviceCommand.device_id == device_id,
                DeviceCommand.status.in_(['pending', 'sent'])
            )
        ).order_by(DeviceCommand.created_at).all()

    def bulk_create_command(
        self,
        device_ids: List[int],
        organization_id: int,
        command_type: str,
        payload: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None
    ) -> List[DeviceCommand]:
        """Create command for multiple devices"""
        commands = []

        for device_id in device_ids:
            command = self.create_command(
                device_id=device_id,
                organization_id=organization_id,
                command_type=command_type,
                payload=payload,
                created_by=created_by
            )
            commands.append(command)

        return commands
```

**Device Health Service:**
```python
# backend-python/services/device/health_service.py

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import Dict, List
from .models import DeviceHealthMetric

class DeviceHealthService:
    def __init__(self, db: Session):
        self.db = db

    def record_metrics(
        self,
        device_id: int,
        organization_id: int,
        metrics: Dict
    ) -> DeviceHealthMetric:
        """Record device health metrics"""
        health = DeviceHealthMetric(
            device_id=device_id,
            organization_id=organization_id,
            cpu_usage=metrics.get('cpu_usage'),
            memory_usage=metrics.get('memory_usage'),
            disk_usage=metrics.get('disk_usage'),
            temperature=metrics.get('temperature'),
            network_status=metrics.get('network_status'),
            bandwidth_up=metrics.get('bandwidth_up'),
            bandwidth_down=metrics.get('bandwidth_down'),
            latency=metrics.get('latency'),
            display_status=metrics.get('display_status'),
            resolution=metrics.get('resolution'),
            refresh_rate=metrics.get('refresh_rate')
        )

        self.db.add(health)
        self.db.commit()

        return health

    def get_latest_metrics(self, device_id: int) -> DeviceHealthMetric:
        """Get latest health metrics for device"""
        return self.db.query(DeviceHealthMetric).filter(
            DeviceHealthMetric.device_id == device_id
        ).order_by(DeviceHealthMetric.recorded_at.desc()).first()

    def get_metrics_history(
        self,
        device_id: int,
        hours: int = 24
    ) -> List[DeviceHealthMetric]:
        """Get health metrics history"""
        since = datetime.utcnow() - timedelta(hours=hours)

        return self.db.query(DeviceHealthMetric).filter(
            and_(
                DeviceHealthMetric.device_id == device_id,
                DeviceHealthMetric.recorded_at >= since
            )
        ).order_by(DeviceHealthMetric.recorded_at).all()

    def get_average_metrics(
        self,
        device_id: int,
        hours: int = 24
    ) -> Dict:
        """Get average metrics for time period"""
        since = datetime.utcnow() - timedelta(hours=hours)

        avg = self.db.query(
            func.avg(DeviceHealthMetric.cpu_usage).label('avg_cpu'),
            func.avg(DeviceHealthMetric.memory_usage).label('avg_memory'),
            func.avg(DeviceHealthMetric.disk_usage).label('avg_disk'),
            func.avg(DeviceHealthMetric.temperature).label('avg_temp'),
            func.avg(DeviceHealthMetric.latency).label('avg_latency')
        ).filter(
            and_(
                DeviceHealthMetric.device_id == device_id,
                DeviceHealthMetric.recorded_at >= since
            )
        ).first()

        return {
            'cpu_usage': round(float(avg.avg_cpu or 0), 2),
            'memory_usage': round(float(avg.avg_memory or 0), 2),
            'disk_usage': round(float(avg.avg_disk or 0), 2),
            'temperature': round(float(avg.avg_temp or 0), 2),
            'latency': round(float(avg.avg_latency or 0), 2)
        }

    def check_health_alerts(self, device_id: int) -> List[Dict]:
        """Check for health alerts"""
        latest = self.get_latest_metrics(device_id)
        alerts = []

        if latest:
            # CPU alert
            if latest.cpu_usage and latest.cpu_usage > 90:
                alerts.append({
                    'type': 'cpu',
                    'severity': 'critical',
                    'message': f'CPU usage at {latest.cpu_usage}%'
                })

            # Memory alert
            if latest.memory_usage and latest.memory_usage > 90:
                alerts.append({
                    'type': 'memory',
                    'severity': 'critical',
                    'message': f'Memory usage at {latest.memory_usage}%'
                })

            # Temperature alert
            if latest.temperature and latest.temperature > 80:
                alerts.append({
                    'type': 'temperature',
                    'severity': 'warning',
                    'message': f'Temperature at {latest.temperature}°C'
                })

        return alerts
```

### Day 5-7: API Routes

```python
# backend-python/services/device/routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from shared.database import get_db_session
from shared.auth import get_current_user
from .group_service import DeviceGroupService
from .command_service import DeviceCommandService
from .health_service import DeviceHealthService
from .dtos import *

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])

# ============================================================================
# Device Groups
# ============================================================================

@router.post("/groups", response_model=DeviceGroupResponse)
async def create_group(
    data: DeviceGroupCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Create device group"""
    service = DeviceGroupService(db)
    return service.create_group(current_user.organization_id, data)

@router.post("/groups/{group_id}/devices")
async def add_devices_to_group(
    group_id: int,
    device_ids: List[int],
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Add devices to group"""
    service = DeviceGroupService(db)
    service.add_devices_to_group(group_id, device_ids)
    return {"status": "success"}

@router.get("/groups/{group_id}/devices")
async def get_group_devices(
    group_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get devices in group"""
    service = DeviceGroupService(db)
    return service.get_group_devices(group_id)

# ============================================================================
# Device Commands
# ============================================================================

@router.post("/{device_id}/commands", response_model=DeviceCommandResponse)
async def send_command(
    device_id: int,
    data: DeviceCommandCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Send command to device"""
    service = DeviceCommandService(db)
    return service.create_command(
        device_id=device_id,
        organization_id=current_user.organization_id,
        command_type=data.command_type,
        payload=data.payload,
        created_by=current_user.id
    )

@router.post("/commands/bulk")
async def send_bulk_command(
    data: BulkDeviceCommandCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Send command to multiple devices"""
    service = DeviceCommandService(db)
    commands = service.bulk_create_command(
        device_ids=data.device_ids,
        organization_id=current_user.organization_id,
        command_type=data.command_type,
        payload=data.payload,
        created_by=current_user.id
    )
    return {"count": len(commands), "commands": commands}

@router.get("/{device_id}/commands")
async def get_device_commands(
    device_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get device command history"""
    service = DeviceCommandService(db)
    return service.get_pending_commands(device_id)

# ============================================================================
# Device Health
# ============================================================================

@router.post("/{device_id}/health")
async def record_health(
    device_id: int,
    data: DeviceHealthMetricsCreate,
    db: Session = Depends(get_db_session)
):
    """Record device health metrics (called by player)"""
    service = DeviceHealthService(db)
    return service.record_metrics(
        device_id=device_id,
        organization_id=data.organization_id,
        metrics=data.metrics
    )

@router.get("/{device_id}/health")
async def get_device_health(
    device_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get latest device health"""
    service = DeviceHealthService(db)
    latest = service.get_latest_metrics(device_id)
    alerts = service.check_health_alerts(device_id)

    return {
        "metrics": latest,
        "alerts": alerts
    }

@router.get("/{device_id}/health/history")
async def get_health_history(
    device_id: int,
    hours: int = 24,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get device health history"""
    service = DeviceHealthService(db)
    history = service.get_metrics_history(device_id, hours)
    avg = service.get_average_metrics(device_id, hours)

    return {
        "history": history,
        "average": avg
    }
```

---

## 📅 WEEK 7: FRONTEND + PLAYER

### Day 8-10: CMS Device Dashboard

**Device Groups UI:**
```typescript
// cms-vite/src/features/devices/components/DeviceGroups.tsx

import { useQuery, useMutation } from '@tanstack/react-query'
import { deviceApi } from '../api'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export function DeviceGroups() {
  const { data: groups } = useQuery({
    queryKey: ['device-groups'],
    queryFn: deviceApi.getGroups
  })

  const createGroup = useMutation({
    mutationFn: deviceApi.createGroup,
    onSuccess: () => {
      // Refetch groups
    }
  })

  return (
    <div className="space-y-4">
      <div className="flex justify-between">
        <h2 className="text-2xl font-bold">Device Groups</h2>
        <Button onClick={() => {/* Open create modal */}}>
          Create Group
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {groups?.map(group => (
          <Card key={group.id}>
            <CardHeader>
              <CardTitle>{group.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">{group.description}</p>
              <p className="mt-2">{group.device_count} devices</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
```

**Device Health Dashboard:**
```typescript
// cms-vite/src/features/devices/components/DeviceHealth.tsx

import { useQuery } from '@tanstack/react-query'
import { deviceApi } from '../api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'

interface Props {
  deviceId: number
}

export function DeviceHealth({ deviceId }: Props) {
  const { data: health } = useQuery({
    queryKey: ['device-health', deviceId],
    queryFn: () => deviceApi.getHealth(deviceId),
    refetchInterval: 30000 // 30s
  })

  const { data: history } = useQuery({
    queryKey: ['device-health-history', deviceId],
    queryFn: () => deviceApi.getHealthHistory(deviceId, 24)
  })

  return (
    <div className="space-y-4">
      {/* Health Alerts */}
      {health?.alerts?.length > 0 && (
        <div className="bg-red-50 border border-red-200 p-4 rounded">
          <h3 className="font-bold text-red-800">Health Alerts</h3>
          {health.alerts.map((alert, i) => (
            <div key={i} className="text-red-700">
              {alert.message}
            </div>
          ))}
        </div>
      )}

      {/* Current Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <MetricCard
          label="CPU"
          value={health?.metrics?.cpu_usage}
          unit="%"
        />
        <MetricCard
          label="Memory"
          value={health?.metrics?.memory_usage}
          unit="%"
        />
        <MetricCard
          label="Disk"
          value={health?.metrics?.disk_usage}
          unit="%"
        />
        <MetricCard
          label="Temp"
          value={health?.metrics?.temperature}
          unit="°C"
        />
        <MetricCard
          label="Latency"
          value={health?.metrics?.latency}
          unit="ms"
        />
      </div>

      {/* History Chart */}
      <Card>
        <CardHeader>
          <CardTitle>CPU Usage (24h)</CardTitle>
        </CardHeader>
        <CardContent>
          <LineChart width={600} height={300} data={history?.history}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="recorded_at" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="cpu_usage" stroke="#8884d8" />
          </LineChart>
        </CardContent>
      </Card>
    </div>
  )
}
```

### Day 11-13: Player Integration

**Health Metrics Reporter:**
```typescript
// player-vite/src/services/health-reporter.ts

export class HealthReporter {
  private deviceId: number
  private organizationId: number
  private interval: NodeJS.Timer | null = null

  constructor(deviceId: number, organizationId: number) {
    this.deviceId = deviceId
    this.organizationId = organizationId
  }

  start() {
    // Report every 5 minutes
    this.interval = setInterval(() => {
      this.reportHealth()
    }, 5 * 60 * 1000)

    // Report immediately
    this.reportHealth()
  }

  stop() {
    if (this.interval) {
      clearInterval(this.interval)
    }
  }

  async reportHealth() {
    const metrics = await this.collectMetrics()

    try {
      await apiClient.post(
        `/devices/${this.deviceId}/health`,
        {
          organization_id: this.organizationId,
          metrics
        }
      )

      console.log('[Health] Metrics reported')
    } catch (error) {
      console.error('[Health] Failed to report:', error)
    }
  }

  async collectMetrics() {
    return {
      cpu_usage: await this.getCPUUsage(),
      memory_usage: await this.getMemoryUsage(),
      disk_usage: await this.getDiskUsage(),
      temperature: await this.getTemperature(),
      network_status: navigator.onLine ? 'online' : 'offline',
      latency: await this.measureLatency(),
      display_status: 'on',
      resolution: `${window.screen.width}x${window.screen.height}`,
      refresh_rate: 60
    }
  }

  async getCPUUsage(): Promise<number> {
    // Browser doesn't have direct CPU access
    // Return estimated based on performance
    const start = performance.now()
    let sum = 0
    for (let i = 0; i < 1000000; i++) {
      sum += Math.random()
    }
    const duration = performance.now() - start

    // Rough estimate: slower = higher CPU usage
    return Math.min(100, duration * 10)
  }

  async getMemoryUsage(): Promise<number> {
    if ('memory' in performance) {
      const mem = (performance as any).memory
      return (mem.usedJSHeapSize / mem.jsHeapSizeLimit) * 100
    }
    return 0
  }

  async getDiskUsage(): Promise<number> {
    if ('storage' in navigator && 'estimate' in (navigator as any).storage) {
      const estimate = await (navigator as any).storage.estimate()
      return (estimate.usage / estimate.quota) * 100
    }
    return 0
  }

  async getTemperature(): Promise<number> {
    // Browser doesn't have temperature access
    // Return 0 or estimate based on performance
    return 0
  }

  async measureLatency(): Promise<number> {
    const start = performance.now()

    try {
      await fetch(`${apiClient.defaults.baseURL}/health`)
      return Math.round(performance.now() - start)
    } catch {
      return 0
    }
  }
}
```

**Command Listener:**
```typescript
// player-vite/src/services/command-listener.ts

import { apiClient } from './api-client'

export class CommandListener {
  private deviceId: number
  private ws: WebSocket | null = null

  constructor(deviceId: number) {
    this.deviceId = deviceId
  }

  connect() {
    const wsUrl = `ws://192.168.5.12:8001/ws/devices/${this.deviceId}`

    this.ws = new WebSocket(wsUrl)

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data)

      if (message.type === 'command') {
        this.handleCommand(message)
      }
    }

    this.ws.onerror = (error) => {
      console.error('[Command] WebSocket error:', error)
    }

    this.ws.onclose = () => {
      console.log('[Command] WebSocket closed, reconnecting...')
      setTimeout(() => this.connect(), 5000)
    }
  }

  async handleCommand(message: any) {
    const { command_id, command_type, payload } = message

    console.log(`[Command] Received: ${command_type}`, payload)

    try {
      let result: any = {}

      switch (command_type) {
        case 'reboot':
          result = await this.executeReboot()
          break

        case 'screenshot':
          result = await this.executeScreenshot()
          break

        case 'update_content':
          result = await this.executeUpdateContent(payload)
          break

        case 'clear_cache':
          result = await this.executeClearCache()
          break

        default:
          throw new Error(`Unknown command: ${command_type}`)
      }

      // Mark as executed
      await apiClient.post(`/commands/${command_id}/executed`, { result })

      console.log(`[Command] Executed: ${command_type}`)
    } catch (error) {
      console.error(`[Command] Failed: ${command_type}`, error)

      // Mark as failed
      await apiClient.post(`/commands/${command_id}/failed`, {
        error_message: error.message
      })
    }
  }

  async executeReboot() {
    // Reload page
    window.location.reload()
    return { status: 'rebooting' }
  }

  async executeScreenshot() {
    // Use html2canvas or similar
    return { status: 'screenshot_taken' }
  }

  async executeUpdateContent(payload: any) {
    // Force content refresh
    window.location.reload()
    return { status: 'content_updated' }
  }

  async executeClearCache() {
    // Clear localStorage/sessionStorage
    localStorage.clear()
    sessionStorage.clear()
    return { status: 'cache_cleared' }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
    }
  }
}
```

### Day 14: Testing & Deployment

```bash
# Test device commands
curl -X POST http://localhost:8001/api/v1/devices/1/commands \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "command_type": "reboot",
    "payload": {}
  }'

# Test bulk commands
curl -X POST http://localhost:8001/api/v1/devices/commands/bulk \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "device_ids": [1, 2, 3],
    "command_type": "update_content",
    "payload": {"content_version": "1.2.3"}
  }'

# Deploy to production
ssh gzjbbk@192.168.5.12 << 'EOF'
  cd /home/gzjbbk/signate

  # Run migrations
  docker exec -i signage-postgres psql -U signage_user -d signage_db \
    < database/fix-database/migrations/017_add_device_groups.sql
  docker exec -i signage-postgres psql -U signage_user -d signage_db \
    < database/fix-database/migrations/018_add_device_commands.sql
  docker exec -i signage-postgres psql -U signage_user -d signage_db \
    < database/fix-database/migrations/019_add_device_health.sql

  # Deploy backend
  docker-compose -f docker/docker-compose.yml up -d --build backend-api
EOF
```

---

## ✅ SUCCESS CRITERIA

- ✅ Device grouping and bulk operations working
- ✅ Remote commands executed successfully
- ✅ Health metrics collected every 5 minutes
- ✅ Health dashboard shows real-time data
- ✅ Alerts triggered for critical metrics

---

## 🎯 DELIVERABLES

- ✅ 3 new database tables (groups, commands, health)
- ✅ Device group management API
- ✅ Remote command execution system
- ✅ Health monitoring service
- ✅ Enhanced CMS device dashboard
- ✅ Player health reporter & command listener

**Phase 4 Complete! Ready for Phase 5.** 🚀
