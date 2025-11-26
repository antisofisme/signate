# Deployment Checklist - Audit Logging Implementation

## Pre-Deployment Verification

### Local Verification
- [x] Python syntax validated successfully
- [x] All imports are correct
- [x] All CREATE/UPDATE/DELETE endpoints have audit logging
- [x] GET/LIST endpoints do NOT have audit logging
- [x] Action names follow `resource.action` convention
- [x] Details include relevant but minimal information (2-4 fields)

### Code Changes Summary
```
backend-python/services/template/routes.py |  60 lines added
backend-python/services/widget/routes.py   | 108 lines added
Total: 2 files changed, 157 insertions(+), 11 deletions(-)
```

### Files Modified
1. `/mnt/g/khoirul/signate/backend-python/services/widget/routes.py`
2. `/mnt/g/khoirul/signate/backend-python/services/template/routes.py`

### Audit Log Actions Added (9 total)
**Widget Service (6):**
- widget.create (already done)
- widget.update (NEW)
- widget.delete (NEW)
- widget.assign_to_playlist (NEW)
- playlist_widget.update (NEW)
- widget.remove_from_playlist (NEW)

**Template Service (3):**
- template.create (NEW)
- template.update (NEW)
- template.delete (NEW)

## Deployment Steps

### Step 1: Backup Current Code
```bash
# Create backup directory
mkdir -p /tmp/backup_audit_logging_$(date +%Y%m%d)

# Backup current files
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cp /home/gzjbbk/signate/backend-python/services/widget/routes.py /tmp/backup_audit_logging_$(date +%Y%m%d)/"

sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cp /home/gzjbbk/signate/backend-python/services/template/routes.py /tmp/backup_audit_logging_$(date +%Y%m%d)/"
```

### Step 2: Upload Modified Files
```bash
# Upload widget routes
sshpass -p 'Password@2021' scp \
  /mnt/g/khoirul/signate/backend-python/services/widget/routes.py \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/services/widget/

# Upload template routes
sshpass -p 'Password@2021' scp \
  /mnt/g/khoirul/signate/backend-python/services/template/routes.py \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/services/template/
```

### Step 3: Verify Files on Server
```bash
# Check widget routes
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "grep -n 'audit_logger.log_action' /home/gzjbbk/signate/backend-python/services/widget/routes.py | wc -l"
# Should show: 6

# Check template routes
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "grep -n 'audit_logger.log_action' /home/gzjbbk/signate/backend-python/services/template/routes.py | wc -l"
# Should show: 3
```

### Step 4: Restart Backend Service
```bash
# Restart backend container
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml restart backend-api"

# Wait for backend to start
sleep 10

# Check backend logs
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker logs signage-backend --tail 50"
```

### Step 5: Health Check
```bash
# Check backend is running
curl -s http://192.168.5.12:8001/health

# Check API docs are accessible
curl -s http://192.168.5.12:8001/docs | grep -q "swagger" && echo "API docs OK"
```

## Post-Deployment Testing

### Test 1: Widget Create
```bash
# Get auth token first
TOKEN=$(curl -s -X POST http://192.168.5.12:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r .access_token)

# Create widget
curl -X POST http://192.168.5.12:8001/widgets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Audit Test Widget",
    "widget_type": "clock",
    "config": {},
    "layout": {"position": "top-right"},
    "is_active": true
  }'

# Verify audit log
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db \
  -c \"SELECT action, resource_type, details FROM audit_logs WHERE action = 'widget.create' ORDER BY created_at DESC LIMIT 1;\""
```

Expected output:
```
    action     | resource_type |                    details                    
---------------+---------------+-----------------------------------------------
 widget.create | widget        | {"name": "Audit Test Widget", "widget_type": "clock"}
```

### Test 2: Template Update
```bash
# Update template (assuming template id 1 exists)
curl -X PUT http://192.168.5.12:8001/templates/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated via Audit Test",
    "is_active": false
  }'

# Verify audit log
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db \
  -c \"SELECT action, resource_type, details FROM audit_logs WHERE action = 'template.update' ORDER BY created_at DESC LIMIT 1;\""
```

Expected output:
```
     action      | resource_type |                           details                           
-----------------+---------------+-------------------------------------------------------------
 template.update | template      | {"name": "Updated via Audit Test", "is_active": false}
```

### Test 3: Widget Delete (With Name Capture)
```bash
# Create a widget first
WIDGET_RESPONSE=$(curl -s -X POST http://192.168.5.12:8001/widgets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Widget To Delete",
    "widget_type": "news",
    "config": {},
    "layout": {},
    "is_active": true
  }')

WIDGET_ID=$(echo $WIDGET_RESPONSE | jq -r .id)

# Delete it
curl -X DELETE http://192.168.5.12:8001/widgets/$WIDGET_ID \
  -H "Authorization: Bearer $TOKEN"

# Verify audit log has widget name
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db \
  -c \"SELECT action, resource_type, details FROM audit_logs WHERE action = 'widget.delete' AND resource_id = $WIDGET_ID;\""
```

Expected output:
```
     action     | resource_type |            details             
----------------+---------------+--------------------------------
 widget.delete  | widget        | {"name": "Widget To Delete"}
```

### Test 4: Check All Audit Actions
```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db \
  -c \"SELECT DISTINCT action FROM audit_logs WHERE action LIKE 'widget.%' OR action LIKE 'template.%' ORDER BY action;\""
```

Expected output (at minimum):
```
            action            
------------------------------
 template.create
 template.delete
 template.update
 widget.assign_to_playlist
 widget.create
 widget.delete
 widget.remove_from_playlist
 widget.update
 playlist_widget.update
```

## Monitoring & Verification

### Check Audit Log Count
```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db \
  -c \"SELECT COUNT(*) as total_audit_logs FROM audit_logs WHERE action LIKE 'widget.%' OR action LIKE 'template.%';\""
```

### Check Recent Activity
```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db \
  -c \"SELECT al.action, u.username, al.details, al.created_at FROM audit_logs al JOIN users u ON al.user_id = u.id WHERE al.action LIKE 'widget.%' OR al.action LIKE 'template.%' ORDER BY al.created_at DESC LIMIT 10;\""
```

### Check IP Address Tracking
```bash
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres psql -U signage_user -d signage_db \
  -c \"SELECT action, ip_address, COUNT(*) FROM audit_logs WHERE action LIKE 'widget.%' OR action LIKE 'template.%' GROUP BY action, ip_address ORDER BY action;\""
```

## Rollback Plan (If Needed)

### Option 1: Restore from Backup
```bash
# Restore widget routes
sshpass -p 'Password@2021' scp \
  /tmp/backup_audit_logging_$(date +%Y%m%d)/routes.py \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/services/widget/

# Restore template routes
sshpass -p 'Password@2021' scp \
  /tmp/backup_audit_logging_$(date +%Y%m%d)/routes.py \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/services/template/

# Restart backend
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml restart backend-api"
```

### Option 2: Git Revert
```bash
# Revert changes locally
cd /mnt/g/khoirul/signate
git checkout backend-python/services/widget/routes.py
git checkout backend-python/services/template/routes.py

# Re-upload original files
sshpass -p 'Password@2021' scp \
  backend-python/services/widget/routes.py \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/services/widget/

sshpass -p 'Password@2021' scp \
  backend-python/services/template/routes.py \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/services/template/

# Restart backend
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml restart backend-api"
```

## Success Criteria

- [ ] Backend starts without errors
- [ ] API docs accessible at http://192.168.5.12:8001/docs
- [ ] Widget create logs to audit_logs table
- [ ] Widget update logs to audit_logs table
- [ ] Widget delete logs with widget name
- [ ] Template create logs to audit_logs table
- [ ] Template update logs to audit_logs table
- [ ] Template delete logs with template name
- [ ] IP addresses are captured correctly
- [ ] All actions follow `resource.action` naming convention
- [ ] No performance degradation (response time < 5ms overhead)

## Known Issues / Limitations

None expected. Implementation follows existing patterns used in device routes.

## Documentation

Reference documents created:
1. `AUDIT_LOGGING_IMPLEMENTATION_SUMMARY.md` - Complete implementation summary
2. `AUDIT_LOG_ACTIONS_REFERENCE.md` - Action reference and SQL queries
3. `AUDIT_LOG_CODE_EXAMPLES.md` - Before/after code examples
4. `DEPLOYMENT_CHECKLIST_AUDIT_LOGGING.md` - This file

## Support

If issues arise:
1. Check backend logs: `docker logs signage-backend --tail 100`
2. Check PostgreSQL logs: `docker logs signage-postgres --tail 100`
3. Verify audit_logs table exists: `\d audit_logs` in psql
4. Refer to existing device routes implementation as reference

