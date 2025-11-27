# Dashboard Service - Quick Reference

## 📁 File Structure

```
services/dashboard/
├── domain/
│   └── dashboard_stats.py          # 12 domain entities
├── repositories/
│   └── dashboard_repo.py           # All DB queries
├── use_cases/
│   ├── get_dashboard_stats.py      # Stats use case
│   ├── get_device_health.py        # Health use case
│   ├── get_live_devices.py         # Live devices use case
│   ├── get_content_performance.py  # Content metrics use case
│   ├── get_active_playlists.py     # Playlists use case
│   ├── get_playback_timeline.py    # Timeline use case
│   ├── get_recent_activity.py      # Activity use case
│   ├── get_system_alerts.py        # Alerts use case
│   └── get_system_info.py          # System info use case
├── dtos.py                          # Request/Response DTOs
└── routes.py                        # HTTP handlers (301 lines)
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/dashboard/stats` | GET | Overall dashboard statistics |
| `/api/v1/dashboard/device-health` | GET | Device health summary |
| `/api/v1/dashboard/live-devices` | GET | Live device status list |
| `/api/v1/dashboard/content-performance` | GET | Content performance metrics |
| `/api/v1/dashboard/active-playlists` | GET | Active playlist assignments |
| `/api/v1/dashboard/playback-timeline` | GET | Playback timeline data |
| `/api/v1/dashboard/recent-activity` | GET | Recent activity feed |
| `/api/v1/dashboard/alerts` | GET | System alerts |
| `/api/v1/dashboard/alerts/{id}/acknowledge` | POST | Acknowledge alert |
| `/api/v1/dashboard/system-info` | GET | System information |

## 🏗️ Architecture Layers

**Dependency Flow**: Routes → Use Cases → Repository → Domain Entities

1. **Domain** - Pure business entities (dataclasses)
2. **Repository** - Data access layer (all DB queries)
3. **Use Cases** - Business logic layer
4. **Routes** - HTTP handlers (thin layer)

## 📊 Key Metrics

- Routes.py: **301 lines** (reduced from 581)
- Code reduction: **48%**
- Domain entities: **12**
- Use cases: **9**
- Repository methods: **9**
- API endpoints: **10**

**Last Updated**: 2025-11-27
**Status**: ✅ Production Ready
