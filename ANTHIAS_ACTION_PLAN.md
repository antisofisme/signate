# ANTHIAS ACTION PLAN

## Executive Summary

Anthias is well-integrated but heavily over-engineered for our use case. We use **7 out of 50+ features** (14%). The system is stable and functional, but optimization opportunities exist.

**Recommendation**: Keep as-is for now. Plan minimal fork or replacement in 6-12 months.

---

## IMMEDIATE ACTIONS (Week 1)

### 1. Document Current Usage
- [x] Identify all Anthias API calls in codebase
- [x] Map data flow from upload to display
- [x] Catalog used vs unused features
- [x] Create dependency map

**Files Modified**:
- `ANTHIAS_COMPREHENSIVE_ANALYSIS.md` - Full analysis
- `ANTHIAS_QUICK_REFERENCE.md` - Developer reference

### 2. Add Monitoring
**Action**: Add health check monitoring
```bash
# Add to monitoring dashboard
curl -s http://192.168.5.12:8000/api/v1/assets?limit=1 | grep -q asset_id
```

**File**: Create `/backend/app/health/anthias_check.py`
```python
async def check_anthias_health():
    try:
        await anthias_service.check_connection()
        return {"status": "healthy", "timestamp": datetime.now()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### 3. Document Risk Mitigation
**Action**: Create disaster recovery plan
- Backup volumes: `anthias-data` and `anthias-assets` daily
- Test restore process monthly
- Document at: `/docs/ANTHIAS_DISASTER_RECOVERY.md`

---

## SHORT-TERM IMPROVEMENTS (1-3 months)

### 1. Optimize Docker Build (30% reduction)
**Problem**: Building full Anthias takes 5-10 minutes
**Solution**: Remove unused components before build

```dockerfile
# Dockerfile.server changes
# Before: Copies all source code (~500MB)
# After: Copy only essentials
COPY anthias_app/ /app/anthias_app/
COPY api/ /app/api/
COPY lib/ /app/lib/
# Remove: /static/src, /webview, /viewer, /ansible, /tools
```

**Estimated Savings**: 3-5 minutes build time, 200-300 MB image size

### 2. Add API Documentation
**Action**: Document Anthias v1 API endpoints we use
**File**: `/backend/docs/ANTHIAS_API.md`
- Document all 7 endpoints we use
- Add curl examples
- Document field mappings

### 3. Create Backup Strategy
**Current State**: No automated backups
**Action**: Add daily backup script

```bash
#!/bin/bash
# backup-anthias.sh
BACKUP_DIR="/backups/anthias"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup volumes
docker cp anthias-server:/data $BACKUP_DIR/data_$TIMESTAMP
docker cp signage-redis:/data $BACKUP_DIR/redis_$TIMESTAMP

# Keep last 7 days
find $BACKUP_DIR -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \;
```

**File**: `/docker/scripts/backup-anthias.sh` (make executable)
**Cron**: Add to `/etc/cron.daily/`

---

## MEDIUM-TERM PLANNING (3-6 months)

### 1. Evaluate Alternatives (Proof of Concept)

#### Option A: Minimal Anthias Fork
**Approach**: Remove unused features
**Effort**: 1 week
**Benefit**: Faster build, smaller footprint
**Risk**: Medium (maintain fork)

```
Files to keep:
✓ /anthias/api/views/v1.py
✓ /anthias/anthias_app/models.py
✓ /anthias/docker/Dockerfile.server
✓ /anthias/docker/Dockerfile.nginx
✓ /anthias/requirements/

Files to remove:
✗ /anthias/static/src/ (-2 MB)
✗ /anthias/webview/ (-3 MB)
✗ /anthias/viewer/ (-0.5 MB)
✗ /anthias/ansible/ (-0.2 MB)
✗ /anthias/api/v1_1, v1_2, v2 (-0.3 MB)

Total savings: ~6 MB (3%), ~2-3 min build time
```

#### Option B: Direct S3 Integration
**Approach**: Replace Anthias file storage with AWS S3
**Effort**: 2 weeks
**Benefit**: Simpler, scalable, managed service
**Risk**: AWS costs, vendor lock-in

```
Changes needed:
1. Modify anthias_service.py to use boto3
2. Update storage path logic
3. Add S3 credentials to .env
4. Keep PostgreSQL for metadata

Implementation:
- upload_asset() → s3.put_object()
- get_asset_url() → s3.generate_presigned_url()
- delete_asset() → s3.delete_object()
- get_asset_content() → s3.get_object()
```

#### Option C: MinIO (S3-Compatible)
**Approach**: Self-hosted S3 clone
**Effort**: 3 weeks
**Benefit**: S3 API without AWS, self-hosted control
**Risk**: Operational overhead

```
Docker addition:
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio-data:/data
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin

Code changes: Same as Option B (uses boto3 with different endpoint)
```

### 2. Test Data Migration
**Action**: Create migration plan document

```
Migration Steps:
1. Export current assets from Anthias
   SELECT asset_id, uri FROM assets;
2. Export content metadata from PostgreSQL
   SELECT id, anthias_asset_id, title FROM content;
3. Map relationships (content → asset)
4. Copy files to new storage (S3/MinIO)
5. Update asset URIs in content table
6. Validate mappings (spot check 10 random)
7. Switch to new storage
8. Keep Anthias as fallback for 1 week
9. Archive old Anthias data
```

**File**: `/docs/ANTHIAS_MIGRATION_PLAN.md`

### 3. Create Abstraction Layer
**Current**: Direct calls to `anthias_service`
**Improved**: Abstraction for easier switching

```python
# /backend/app/services/storage.py
class StorageService(ABC):
    @abstractmethod
    async def upload_asset(self, file: UploadFile) -> dict:
        pass

class AnthiasStorage(StorageService):
    async def upload_asset(self, file: UploadFile) -> dict:
        # Current implementation

class S3Storage(StorageService):
    async def upload_asset(self, file: UploadFile) -> dict:
        # S3 implementation

class MinIOStorage(StorageService):
    async def upload_asset(self, file: UploadFile) -> dict:
        # MinIO implementation
```

**File**: `/backend/app/services/storage.py`
**Benefit**: Swap implementations at config time

---

## LONG-TERM STRATEGY (6-12 months)

### 1. Make Decision on Anthias
**Decision Matrix**:

| Factor | Keep Anthias | Use S3 | Use MinIO |
|--------|--------------|--------|-----------|
| Build time | 5-10 min | <1 min | <1 min |
| Complexity | High | Low | Medium |
| Cost | Free | $0.023/GB | Free |
| Maintenance | Medium | None | Medium |
| Scalability | Limited | Unlimited | Limited |
| Self-hosted | Yes | No | Yes |
| Vendor lock-in | Low | High | None |

**Recommended**: S3 if cloud-native, MinIO if self-hosted preference

### 2. If Keeping Anthias

Create minimal fork:
1. Fork from current repo
2. Remove directories: webview, viewer, ansible, tools, raspberry_pi_imager
3. Remove API versions: v1_1, v1_2, v2
4. Remove frontend: static/src
5. Optimize Dockerfiles
6. Update documentation
7. Tag as "signate-assets-lite"

**Repository**: `github.com/yourorg/signate-assets`
**Benefits**: 
- Faster builds (3-4 min vs 5-10 min)
- Smaller footprint (1.5 MB vs 6.2 MB)
- Easier to maintain (focus on essentials)
- Clear scope (asset storage only)

### 3. If Switching to S3/MinIO

Implementation roadmap:
```
Week 1: Setup infrastructure
  - Launch S3 bucket or MinIO container
  - Configure credentials in .env
  - Setup backup/retention policies

Week 2: Implement abstraction layer
  - Create StorageService interface
  - Implement S3StorageProvider
  - Add tests

Week 3: Data migration
  - Export all assets from Anthias
  - Copy files to S3/MinIO
  - Update database URIs
  - Validate completeness

Week 4: Testing
  - Test upload flow
  - Test file serving
  - Test deletion flow
  - Stress test with large files

Week 5: Migration cutover
  - Update config to use new storage
  - Monitor for issues
  - Keep Anthias as fallback
  - Plan Anthias deprecation
```

---

## MONTHLY MAINTENANCE

### Week 1: Monitoring
- Check Anthias disk usage
- Monitor upload/download success rates
- Review error logs
- Test API endpoints

### Week 2: Backups
- Verify daily backups are running
- Test restore process
- Document any issues

### Week 3: Updates
- Check for Anthias security updates
- Check for dependency updates
- Plan upgrade if needed

### Week 4: Documentation
- Update runbooks as needed
- Document any new issues/resolutions
- Update disaster recovery plan

---

## CHECKLISTS

### Immediate (Before deploying changes)
- [ ] Backup all asset data
- [ ] Document current upload flow
- [ ] Identify all Anthias dependencies
- [ ] Get list of uploaded files
- [ ] Test disaster recovery

### Before removing components
- [ ] Verify feature is truly unused
- [ ] Search entire codebase for references
- [ ] Test that removal doesn't break anything
- [ ] Tag old version before deletion
- [ ] Document what was removed and why

### Before switching to new storage
- [ ] Have 100% test coverage of storage service
- [ ] Test migration with sample data
- [ ] Test rollback procedure
- [ ] Have clear rollback plan
- [ ] Notify team of change
- [ ] Monitor closely for 1 week

---

## COST ANALYSIS

### Current (Anthias)
```
Infrastructure: Free (self-hosted)
Development: 2-3 hours/month maintenance
Build time: 5-10 min per deploy
Disk space: 6.2 MB code + asset storage
```

### S3 Option
```
Infrastructure: $0.023/GB/month for data
Development: <1 hour/month maintenance
Build time: <1 min per deploy
Disk space: Unlimited (pay for what you use)
Feasibility: Easy if already on AWS
```

### MinIO Option
```
Infrastructure: Free (self-hosted)
Development: 2-3 hours/month maintenance
Build time: <1 min per deploy
Disk space: Limited to available storage
Feasibility: Need to manage MinIO cluster
```

**Breakeven Analysis**:
- If storage < 1 TB/year: S3 costs < $300/year (cheaper than dev time)
- If storage > 1 TB/year: MinIO more economical

---

## TESTING CHECKLIST

### Upload Tests
- [x] Small image (< 1 MB)
- [ ] Large image (> 50 MB)
- [x] Small video (< 10 MB)
- [ ] Large video (> 500 MB)
- [ ] Various formats (JPG, PNG, MP4, WebM)
- [ ] Invalid files (DOC, PDF, etc.) - should reject
- [ ] Duplicate upload - should create new asset
- [ ] Concurrent uploads - should not conflict

### Download Tests
- [ ] Image via `/content/{id}/image` endpoint
- [ ] Video via `/content/{id}/video` endpoint
- [ ] Asset via direct Anthias URL
- [ ] Missing asset - should 404
- [ ] Content-Type headers correct
- [ ] Large file streaming (not loaded all in memory)

### Delete Tests
- [ ] Delete asset from Anthias
- [ ] Delete metadata from PostgreSQL
- [ ] Re-upload with same name - should work
- [ ] Cascading delete of assignments

### Integration Tests
- [ ] Full upload → store → display → delete flow
- [ ] Playlist assignment with content
- [ ] Device fetches correct content
- [ ] Update asset metadata updates everywhere

---

## DECISION TREE

```
Does Anthias cause problems?
├─ YES
│  ├─ Build time too long?
│  │  └─ Option A: Minimal fork
│  ├─ Files missing or lost?
│  │  └─ Add backup system
│  ├─ Hard to maintain/deploy?
│  │  └─ Option B or C: Replace with S3/MinIO
│  └─ Scaling issues?
│     └─ Option B: AWS S3 (easiest to scale)
│
└─ NO
   ├─ Keep as-is for now
   ├─ Re-evaluate quarterly
   └─ Consider fork for future optimization
```

---

## CONCLUSION

**Current Status**: Anthias works fine but is overengineered
**Recommendation**: Keep for next 6 months, plan optimization
**Next Review**: 3 months (evaluate pain points)
**Decision Point**: 6 months (commit to Anthias or migrate)

**Three Scenarios**:
1. **Happy Path** (70% likely): Anthias continues to work, we create minimal fork for optimization
2. **Problem Path** (20% likely): Issues arise, we migrate to S3/MinIO
3. **Scaling Path** (10% likely): Scale dramatically, we must use S3 or similar

All three paths are viable and documented.
