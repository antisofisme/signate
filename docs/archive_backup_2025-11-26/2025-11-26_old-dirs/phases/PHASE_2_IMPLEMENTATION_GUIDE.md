# 🚀 PHASE 2: CONTENT MANAGEMENT - IMPLEMENTATION GUIDE

**Timeline:** Week 3-4 (after Phase 1)
**Duration:** 10-14 days
**Risk Level:** Medium
**Downtime:** < 5 minutes

---

## 📋 OVERVIEW

Phase 2 adds content analytics and performance optimization:
- ✅ Content playback logging
- ✅ Performance analytics dashboard
- ✅ 40+ composite indexes for query optimization
- ✅ Player tracking integration

**What changes:**
- Database: 1 new table + 40+ indexes
- Backend: Analytics API
- CMS: Analytics dashboard UI
- Player: Playback event tracking

---

## 🎯 WEEK-BY-WEEK PLAN

### **Week 3: Backend + Database (Days 1-7)**
### **Week 4: Frontend + Player (Days 8-14)**

---

## 📅 WEEK 3: BACKEND + DATABASE

### Day 1: Database Migrations

```bash
# Step 1: Run Migration 014 (Playback Logs)
docker exec -i signage-postgres psql -U signage_user -d signage_db \
  < database/fix-database/migrations/014_add_content_playback_logs.sql

# Verify table created
docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
  SELECT table_name FROM information_schema.tables
  WHERE table_name = 'content_playback_logs';"

# Step 2: Run Migration 015 (Performance Indexes)
docker exec -i signage-postgres psql -U signage_user -d signage_db \
  < database/fix-database/migrations/015_add_composite_indexes.sql

# Verify indexes created
docker exec -it signage-postgres psql -U signage_user -d signage_db -c "
  SELECT count(*) as total_indexes
  FROM pg_indexes
  WHERE schemaname = 'public'
    AND indexname LIKE 'idx_%';"

# Expected: 50+ indexes
```

### Day 2-3: Backend Implementation

**Create Models:**
```python
# backend-python/services/content/models.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric
from app.core.database import Base
from datetime import datetime

class ContentPlaybackLog(Base):
    """Content playback tracking"""
    __tablename__ = "content_playback_logs"

    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"))
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    duration_played = Column(Integer)  # seconds
    quality = Column(String(20))  # 'auto', 'hd', 'sd'
    buffering_time = Column(Integer)  # milliseconds

    played_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    content = relationship("Content")
    device = relationship("Device")
```

**Create Services:**
```python
# backend-python/services/content/playback_service.py

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Dict, List
from .models import ContentPlaybackLog

class PlaybackService:
    def __init__(self, db: Session):
        self.db = db

    def log_playback(
        self,
        content_id: int,
        device_id: int,
        organization_id: int,
        duration_played: int,
        quality: str = "auto",
        buffering_time: int = 0
    ):
        """Log content playback event"""
        log = ContentPlaybackLog(
            content_id=content_id,
            device_id=device_id,
            organization_id=organization_id,
            duration_played=duration_played,
            quality=quality,
            buffering_time=buffering_time,
            played_at=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()
        return log

    def get_content_analytics(self, content_id: int) -> Dict:
        """Get analytics for specific content"""
        stats = self.db.query(
            func.count(ContentPlaybackLog.id).label('total_plays'),
            func.count(func.distinct(ContentPlaybackLog.device_id)).label('unique_devices'),
            func.avg(ContentPlaybackLog.duration_played).label('avg_duration'),
            func.max(ContentPlaybackLog.played_at).label('last_played')
        ).filter(
            ContentPlaybackLog.content_id == content_id
        ).first()

        return {
            "content_id": content_id,
            "total_plays": stats.total_plays or 0,
            "unique_devices": stats.unique_devices or 0,
            "avg_duration_seconds": round(float(stats.avg_duration or 0), 2),
            "last_played": stats.last_played
        }

    def get_trending_content(self, organization_id: int, days: int = 7) -> List[Dict]:
        """Get trending content for organization"""
        since = datetime.utcnow() - timedelta(days=days)

        trending = self.db.query(
            ContentPlaybackLog.content_id,
            func.count(ContentPlaybackLog.id).label('plays'),
            func.count(func.distinct(ContentPlaybackLog.device_id)).label('devices')
        ).filter(
            and_(
                ContentPlaybackLog.organization_id == organization_id,
                ContentPlaybackLog.played_at >= since
            )
        ).group_by(
            ContentPlaybackLog.content_id
        ).order_by(
            func.count(ContentPlaybackLog.id).desc()
        ).limit(10).all()

        return [
            {
                "content_id": t.content_id,
                "plays": t.plays,
                "devices": t.devices
            }
            for t in trending
        ]
```

**Create API Endpoints:**
```python
# backend-python/services/content/routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .playback_service import PlaybackService
from .schemas import PlaybackLogCreate, ContentAnalytics
from app.core.deps import get_db, get_current_user

router = APIRouter(prefix="/api/v1/contents", tags=["contents"])

@router.post("/{content_id}/playback")
async def log_playback(
    content_id: int,
    data: PlaybackLogCreate,
    db: Session = Depends(get_db)
):
    """Log content playback (called by player)"""
    service = PlaybackService(db)
    service.log_playback(
        content_id=content_id,
        device_id=data.device_id,
        organization_id=data.organization_id,
        duration_played=data.duration_played,
        quality=data.quality
    )
    return {"status": "logged"}

@router.get("/{content_id}/analytics", response_model=ContentAnalytics)
async def get_analytics(
    content_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get content analytics"""
    service = PlaybackService(db)
    return service.get_content_analytics(content_id)

@router.get("/trending")
async def get_trending(
    days: int = 7,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trending content"""
    service = PlaybackService(db)
    return service.get_trending_content(
        organization_id=current_user.organization_id,
        days=days
    )
```

### Day 4: Testing Backend

```bash
# Test playback logging
curl -X POST http://localhost:8001/api/v1/contents/1/playback \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 1,
    "organization_id": 1,
    "duration_played": 120,
    "quality": "hd"
  }'

# Test analytics
curl http://localhost:8001/api/v1/contents/1/analytics

# Test trending
curl http://localhost:8001/api/v1/contents/trending?days=7
```

---

## 📅 WEEK 4: FRONTEND + PLAYER

### Day 8-10: CMS Implementation

**Enable Feature Flag:**
```typescript
// cms-vite/src/config/features.ts
export const FEATURES = {
  CONTENT_ANALYTICS: true,  // Enable!
  // ... other flags
}
```

**Create Analytics Components:**
```typescript
// cms-vite/src/features/contents/components/ContentAnalytics.tsx

import { useQuery } from '@tanstack/react-query'
import { contentApi } from '../api'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'

interface Props {
  contentId: number
}

export function ContentAnalytics({ contentId }: Props) {
  const { data: analytics, isLoading } = useQuery({
    queryKey: ['content-analytics', contentId],
    queryFn: () => contentApi.getAnalytics(contentId),
    refetchInterval: 30000 // Refresh every 30s
  })

  if (isLoading) {
    return <div>Loading analytics...</div>
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Total Plays</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{analytics?.total_plays || 0}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Unique Devices</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{analytics?.unique_devices || 0}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Avg Duration</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {Math.round(analytics?.avg_duration_seconds || 0)}s
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
```

**Create API Client:**
```typescript
// cms-vite/src/features/contents/api/content-api.ts

import { apiClient } from '@/lib/api-client'

export const contentApi = {
  getAnalytics: async (contentId: number) => {
    const { data } = await apiClient.get(`/contents/${contentId}/analytics`)
    return data
  },

  getTrending: async (days: number = 7) => {
    const { data } = await apiClient.get(`/contents/trending?days=${days}`)
    return data
  },

  logPlayback: async (contentId: number, payload: PlaybackLog) => {
    await apiClient.post(`/contents/${contentId}/playback`, payload)
  }
}

interface PlaybackLog {
  device_id: number
  organization_id: number
  duration_played: number
  quality: string
}
```

### Day 11-13: Player Implementation

**Create Playback Logger:**
```typescript
// player-vite/src/services/playback-logger.ts

import { apiClient } from './api-client'

interface PlaybackSession {
  contentId: number
  startTime: number
  quality: string
}

export class PlaybackLogger {
  private deviceId: number
  private organizationId: number
  private currentSession: PlaybackSession | null = null

  constructor(deviceId: number, organizationId: number) {
    this.deviceId = deviceId
    this.organizationId = organizationId
  }

  startPlayback(contentId: number, quality: string = 'auto') {
    this.currentSession = {
      contentId,
      startTime: Date.now(),
      quality
    }

    console.log(`[Playback] Started: content=${contentId}, quality=${quality}`)
  }

  async endPlayback() {
    if (!this.currentSession) {
      return
    }

    const duration = Math.round((Date.now() - this.currentSession.startTime) / 1000)

    try {
      await apiClient.post(
        `/contents/${this.currentSession.contentId}/playback`,
        {
          device_id: this.deviceId,
          organization_id: this.organizationId,
          duration_played: duration,
          quality: this.currentSession.quality
        }
      )

      console.log(`[Playback] Logged: ${duration}s`)
    } catch (error) {
      console.error('[Playback] Failed to log:', error)
    } finally {
      this.currentSession = null
    }
  }
}
```

**Integrate into Player:**
```typescript
// player-vite/src/app/Player.tsx

import { useEffect, useMemo } from 'react'
import { PlaybackLogger } from '../services/playback-logger'
import { useDeviceStore } from '../stores/device-store'

export function Player() {
  const { deviceId, organizationId } = useDeviceStore()
  const logger = useMemo(
    () => new PlaybackLogger(deviceId, organizationId),
    [deviceId, organizationId]
  )

  const handleContentStart = (content: Content) => {
    logger.startPlayback(content.id, 'auto')
  }

  const handleContentEnd = () => {
    logger.endPlayback()
  }

  return (
    <video
      onPlay={() => handleContentStart(currentContent)}
      onEnded={handleContentEnd}
      onError={handleContentEnd}
    />
  )
}
```

### Day 14: Testing & Deployment

```bash
# 1. Deploy to staging
ssh gzjbbk@192.168.5.12 << 'EOF'
  cd /home/gzjbbk/staging

  # Run migrations
  docker exec -i signage-postgres psql -U signage_user -d signage_db_staging \
    < database/fix-database/migrations/014_add_content_playback_logs.sql
  docker exec -i signage-postgres psql -U signage_user -d signage_db_staging \
    < database/fix-database/migrations/015_add_composite_indexes.sql

  # Deploy backend
  docker-compose up -d --build backend-api

  # Deploy CMS
  # (upload built files)

  # Deploy player
  # (upload built files)
EOF

# 2. Test end-to-end
# - Open player
# - Play content for 30 seconds
# - Open CMS analytics
# - Verify playback logged

# 3. Deploy to production (if tests pass)
```

---

## ✅ SUCCESS CRITERIA

- ✅ Playback logs stored in database
- ✅ CMS shows content analytics
- ✅ Player sends playback events
- ✅ 40+ indexes improve query performance
- ✅ No performance degradation

---

## 🎯 DELIVERABLES

- ✅ content_playback_logs table
- ✅ 40+ performance indexes
- ✅ Backend analytics API
- ✅ CMS analytics dashboard
- ✅ Player tracking integration

**Phase 2 Complete! Ready for Phase 3.** 🚀
