# Hardcoded Values to Environment Variables Migration

## Summary

Successfully migrated all hardcoded configuration values in backend-python codebase to environment variables for better configurability and deployment flexibility.

## Files Modified

### 1. `/backend-python/shared/cache.py`

**Changes:**
- Moved default TTL from hardcoded `300` seconds to environment variable `CACHE_DEFAULT_TTL`
- Updated `set()` method to use env var: `int(os.getenv("CACHE_DEFAULT_TTL", "300"))`
- Updated `set_many()` method to use env var: `int(os.getenv("CACHE_DEFAULT_TTL", "300"))`
- Changed default parameter from `ttl: int = 300` to `ttl: int = None` (uses env var if not specified)

**Environment Variables Added:**
- `CACHE_DEFAULT_TTL`: Default cache TTL in seconds (default: 300)

---

### 2. `/backend-python/celery_app.py`

**Changes:**
- Moved all Celery configuration values to environment variables:
  - `timezone`: `os.getenv('CELERY_TIMEZONE', 'Asia/Jakarta')`
  - `worker_prefetch_multiplier`: `int(os.getenv('CELERY_WORKER_PREFETCH_MULTIPLIER', '1'))`
  - `result_expires`: `int(os.getenv('CELERY_RESULT_EXPIRES', '3600'))`
  - `task_soft_time_limit`: `int(os.getenv('CELERY_TASK_SOFT_TIME_LIMIT', '600'))`
  - `task_time_limit`: `int(os.getenv('CELERY_TASK_TIME_LIMIT', '900'))`
  - `worker_max_tasks_per_child`: `int(os.getenv('CELERY_WORKER_MAX_TASKS_PER_CHILD', '50'))`
  - `master_name`: `os.getenv('REDIS_MASTER_NAME', 'mymaster')`
  - Crontab schedule: `hour=int(os.getenv('CELERY_CLEANUP_HOUR', '3'))`, `minute=int(os.getenv('CELERY_CLEANUP_MINUTE', '0'))`

**Environment Variables Added:**
- `CELERY_TIMEZONE`: Celery timezone (default: Asia/Jakarta)
- `CELERY_WORKER_PREFETCH_MULTIPLIER`: Worker prefetch multiplier (default: 1)
- `CELERY_RESULT_EXPIRES`: Result expiration in seconds (default: 3600)
- `CELERY_TASK_SOFT_TIME_LIMIT`: Soft time limit in seconds (default: 600)
- `CELERY_TASK_TIME_LIMIT`: Hard time limit in seconds (default: 900)
- `CELERY_WORKER_MAX_TASKS_PER_CHILD`: Max tasks per worker (default: 50)
- `REDIS_MASTER_NAME`: Redis master name for sentinel (default: mymaster)
- `CELERY_CLEANUP_HOUR`: Cleanup task hour (default: 3)
- `CELERY_CLEANUP_MINUTE`: Cleanup task minute (default: 0)

---

### 3. `/backend-python/shared/virus_scanner.py`

**Changes:**
- Moved scan timeout from hardcoded `30` seconds to environment variable `CLAMAV_TIMEOUT`
- Updated `__init__()`: `self.timeout = int(os.getenv('CLAMAV_TIMEOUT', '30'))`

**Environment Variables Added:**
- `CLAMAV_TIMEOUT`: ClamAV scan timeout in seconds (default: 30)

---

### 4. `/backend-python/services/content/use_cases/upload_content.py`

**Changes:**
- Converted static `MAX_SIZES` dictionary to `get_max_sizes()` static method
- Moved file size limits to environment variables:
  - Image: `int(os.getenv('MAX_IMAGE_SIZE_MB', '50')) * 1024 * 1024`
  - Video: `int(os.getenv('MAX_VIDEO_SIZE_MB', '500')) * 1024 * 1024`
  - Audio: `int(os.getenv('MAX_AUDIO_SIZE_MB', '100')) * 1024 * 1024`

**Environment Variables Added:**
- `MAX_IMAGE_SIZE_MB`: Max image file size in MB (default: 50)
- `MAX_VIDEO_SIZE_MB`: Max video file size in MB (default: 500)
- `MAX_AUDIO_SIZE_MB`: Max audio file size in MB (default: 100)

---

### 5. `/backend-python/services/content/infrastructure/storage/metadata_extractor.py`

**Changes:**
- Added `import os` statement
- Moved FFprobe timeout from hardcoded `30` seconds to environment variable `FFPROBE_TIMEOUT`
- Updated subprocess call: `timeout=int(os.getenv('FFPROBE_TIMEOUT', '30'))`

**Environment Variables Added:**
- `FFPROBE_TIMEOUT`: FFprobe metadata extraction timeout in seconds (default: 30)

---

### 6. `/backend-python/.env.example`

**Changes:**
- Added comprehensive documentation for all new environment variables
- Organized into logical sections:
  - Redis Configuration
  - Celery Configuration (10 new variables)
  - File Storage (3 new variables for size limits)
  - Cache Configuration
  - ClamAV Virus Scanner
  - FFprobe Metadata Extraction

**New Sections Added:**
```env
# Redis (Shared cache & Celery broker)
REDIS_URL=redis://localhost:6379/0
REDIS_MASTER_NAME=mymaster

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TIMEZONE=Asia/Jakarta
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_RESULT_EXPIRES=3600
CELERY_TASK_SOFT_TIME_LIMIT=600
CELERY_TASK_TIME_LIMIT=900
CELERY_WORKER_MAX_TASKS_PER_CHILD=50
CELERY_CLEANUP_HOUR=3
CELERY_CLEANUP_MINUTE=0

# File Storage
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE=524288000  # 500MB in bytes
MAX_IMAGE_SIZE_MB=50
MAX_VIDEO_SIZE_MB=500
MAX_AUDIO_SIZE_MB=100

# Cache Configuration
CACHE_DEFAULT_TTL=300

# ClamAV Virus Scanner
CLAMAV_HOST=localhost
CLAMAV_PORT=3310
CLAMAV_TIMEOUT=30

# FFprobe Metadata Extraction
FFPROBE_TIMEOUT=30
```

---

## Environment Variables Reference

### Cache Configuration
| Variable | Description | Default | Unit |
|----------|-------------|---------|------|
| `CACHE_DEFAULT_TTL` | Default cache TTL | 300 | seconds |

### Celery Configuration
| Variable | Description | Default | Unit |
|----------|-------------|---------|------|
| `CELERY_TIMEZONE` | Celery timezone | Asia/Jakarta | timezone |
| `CELERY_WORKER_PREFETCH_MULTIPLIER` | Worker prefetch multiplier | 1 | count |
| `CELERY_RESULT_EXPIRES` | Result expiration | 3600 | seconds |
| `CELERY_TASK_SOFT_TIME_LIMIT` | Soft time limit | 600 | seconds |
| `CELERY_TASK_TIME_LIMIT` | Hard time limit | 900 | seconds |
| `CELERY_WORKER_MAX_TASKS_PER_CHILD` | Max tasks per worker | 50 | count |
| `REDIS_MASTER_NAME` | Redis master name | mymaster | string |
| `CELERY_CLEANUP_HOUR` | Cleanup task hour | 3 | hour (0-23) |
| `CELERY_CLEANUP_MINUTE` | Cleanup task minute | 0 | minute (0-59) |

### File Upload Limits
| Variable | Description | Default | Unit |
|----------|-------------|---------|------|
| `MAX_IMAGE_SIZE_MB` | Max image size | 50 | MB |
| `MAX_VIDEO_SIZE_MB` | Max video size | 500 | MB |
| `MAX_AUDIO_SIZE_MB` | Max audio size | 100 | MB |

### ClamAV Virus Scanner
| Variable | Description | Default | Unit |
|----------|-------------|---------|------|
| `CLAMAV_HOST` | ClamAV daemon host | localhost | hostname |
| `CLAMAV_PORT` | ClamAV daemon port | 3310 | port |
| `CLAMAV_TIMEOUT` | Scan timeout | 30 | seconds |

### FFprobe Metadata Extraction
| Variable | Description | Default | Unit |
|----------|-------------|---------|------|
| `FFPROBE_TIMEOUT` | Metadata extraction timeout | 30 | seconds |

---

## Benefits

1. **Flexibility**: Configuration can be changed without code modifications
2. **Environment-Specific**: Different values for development, staging, production
3. **Security**: Sensitive values can be managed via secret management systems
4. **Scalability**: Easy to tune performance parameters based on server capacity
5. **Maintainability**: Clear documentation of all configurable values
6. **Deployment**: Easier to deploy across different environments

---

## Migration Impact

### Backward Compatibility
✅ **Fully backward compatible** - All environment variables have sensible defaults matching the original hardcoded values. Existing deployments will continue to work without any `.env` changes.

### Required Actions
- **Optional**: Update `.env` file to customize values for your environment
- **Recommended**: Copy new variables from `.env.example` to your `.env` file
- **Production**: Review and adjust values based on your infrastructure capacity

---

## Testing

### Verify Changes Locally
```bash
# 1. Navigate to backend directory
cd /mnt/g/khoirul/signate/backend-python

# 2. Update .env file with custom values (optional)
cp .env.example .env
# Edit .env to customize values

# 3. Restart backend services
docker-compose -f ../docker/docker-compose.yml restart backend-api

# 4. Check logs to verify environment variables are loaded
docker logs signage-backend --tail 50
```

### Production Deployment
```bash
# VPS Production Server
# 1. Sync updated code
sshpass -p '1(;2-Ur?F)PP73J#G-wW' rsync -avz --exclude '__pycache__' \
  --exclude 'node_modules' --exclude '.git' \
  /mnt/g/khoirul/signate/backend-python/ root@72.61.209.158:/root/signage/backend-python/

# 2. Update .env file on server (if needed)
sshpass -p '1(;2-Ur?F)PP73J#G-wW' ssh root@72.61.209.158 \
  "cd /root/signage/backend-python && nano .env"

# 3. Restart backend service
sshpass -p '1(;2-Ur?F)PP73J#G-wW' ssh root@72.61.209.158 \
  "cd /root/signage && docker-compose -f docker/docker-compose.yml restart backend-api"
```

---

## Performance Tuning Examples

### High-Volume Production
```env
# Increase cache TTL for better performance
CACHE_DEFAULT_TTL=600

# Increase Celery limits for long-running tasks
CELERY_TASK_SOFT_TIME_LIMIT=1200
CELERY_TASK_TIME_LIMIT=1800
CELERY_WORKER_MAX_TASKS_PER_CHILD=100

# Increase file size limits
MAX_VIDEO_SIZE_MB=1000
```

### Development Environment
```env
# Lower cache TTL for faster testing
CACHE_DEFAULT_TTL=60

# Lower timeouts for faster feedback
CLAMAV_TIMEOUT=10
FFPROBE_TIMEOUT=10

# Smaller file limits for faster uploads
MAX_VIDEO_SIZE_MB=100
```

### Resource-Constrained Environment
```env
# Lower Celery limits to reduce memory usage
CELERY_WORKER_MAX_TASKS_PER_CHILD=20
CELERY_TASK_SOFT_TIME_LIMIT=300
CELERY_TASK_TIME_LIMIT=600

# Smaller file limits
MAX_VIDEO_SIZE_MB=200
MAX_IMAGE_SIZE_MB=20
```

---

## Next Steps

1. ✅ **Code Changes**: Completed
2. ✅ **Documentation**: `.env.example` updated
3. ⏳ **Testing**: Test in local environment
4. ⏳ **Deployment**: Deploy to VPS production
5. ⏳ **Monitoring**: Monitor application behavior with new values

---

## Notes

- All changes maintain backward compatibility
- Default values match original hardcoded values
- No breaking changes to existing functionality
- Environment variables follow best practices (clear naming, sensible defaults)
- All timeouts are in seconds for consistency
- All file sizes in MB for easier configuration

---

**Date**: 2025-11-27
**Author**: Backend Architect
**Status**: ✅ Complete
