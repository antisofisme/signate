# 👥 USER CREDENTIALS - SISTEM SIGNAGE

## 📋 RINGKASAN

Dokumen ini berisi kredensial untuk semua user test yang tersedia di sistem Digital Signage.

**Catatan Penting**:
- ⚠️ **JANGAN** share kredensial ini di public repository
- ✅ Gunakan hanya untuk development dan testing
- ✅ Untuk production, buat user baru dengan password yang aman

---

## 🔴 SUPER_ADMIN (System Owner)

### Kredensial

```
Username:     superadmin
Password:     SuperAdmin123!@#
Role:         SUPER_ADMIN
Organization: NULL (system-wide access)
```

### Akses & Permissions

✅ **Full System Access**
- Manage semua organizations di sistem
- Manage semua users lintas organization
- Access ke semua resources tanpa batasan organization
- System-wide configuration dan settings

❌ **Tidak Terikat Organization**
- Organization ID = NULL
- Tidak masuk quota organization manapun
- Akses data dari semua organization

### Kapan Menggunakan

| Use Case | Deskripsi |
|----------|-----------|
| ✅ System Administration | Setup system, manage system settings |
| ✅ Create Organizations | Membuat organization baru untuk tenant |
| ✅ Cross-Org User Management | Manage users dari berbagai organization |
| ✅ System Monitoring | Monitor seluruh system health |
| ✅ Troubleshooting | Debug issues lintas organization |

### Login Command

```bash
curl -X POST "http://192.168.5.12:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "superadmin", "password": "SuperAdmin123!@#"}'
```

### Response Example

```json
{
  "success": true,
  "data": {
    "user": {
      "id": 24,
      "username": "superadmin",
      "email": "superadmin@system.local",
      "role": "SUPER_ADMIN",
      "organization_id": null,
      "is_active": true
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "organizations": [
      { "id": 4, "name": "TestOrg2" },
      { "id": 5, "name": "TestAuditOrg" },
      { "id": 20, "name": "Test Tenant Organization" }
      // ... semua organizations di sistem
    ]
  }
}
```

---

## 🟦 TENANT TEST USERS

**Organization**: Test Tenant Organization (ID: 20)

Semua user tenant test ini berada dalam satu organization yang sama untuk testing purposes.

---

### 🔵 1. TENANT ADMIN

#### Kredensial

```
Username:     tenant_admin
Password:     Admin123!@#
Email:        tenant_admin@test.com
Full Name:    Tenant Administrator
Role:         ADMIN
Organization: 20 (Test Tenant Organization)
```

#### Akses & Permissions

✅ **Apa yang BISA dilakukan**
- Manage users dalam organization sendiri (org 20)
- Create, read, update, delete devices dalam org 20
- Upload, manage content dalam org 20
- Create, manage playlists dalam org 20
- Assign playlists ke devices
- View organization statistics (org 20)

❌ **Apa yang TIDAK BISA dilakukan**
- Manage users dari organization lain
- Access data dari organization lain
- Create atau delete organizations
- Manage system-wide settings

#### Kapan Menggunakan

| Use Case | Deskripsi |
|----------|-----------|
| ✅ Organization Admin Tasks | Daily administration dalam organization |
| ✅ User Management | Add/remove users, reset passwords |
| ✅ Device Management | Register devices, view device status |
| ✅ Content Management | Upload content, create playlists |
| ✅ Testing Admin Permissions | Test role-based access control |

#### Login Command

```bash
curl -X POST "http://192.168.5.12:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "tenant_admin", "password": "Admin123!@#"}'
```

---

### 🟡 2. TENANT MANAGER (Content Manager)

#### Kredensial

```
Username:     tenant_manager
Password:     Manager123!@#
Email:        tenant_manager@test.com
Full Name:    Tenant Content Manager
Role:         CONTENT_MANAGER
Organization: 20 (Test Tenant Organization)
```

#### Akses & Permissions

✅ **Apa yang BISA dilakukan**
- Upload dan manage content (images, videos, documents)
- Create dan manage playlists
- Add/remove content dari playlists
- Reorder playlist items
- Assign playlists ke devices
- View devices dan device status
- Create dan manage content tags
- View organization content statistics

❌ **Apa yang TIDAK BISA dilakukan**
- Manage users (create, update, delete users)
- Manage organization settings
- Delete devices
- Access data dari organization lain

#### Kapan Menggunakan

| Use Case | Deskripsi |
|----------|-----------|
| ✅ Content Management | Upload images/videos, organize content |
| ✅ Playlist Creation | Create playlists untuk different scenarios |
| ✅ Playlist Scheduling | Schedule playlists by time/day |
| ✅ Daily Operations | Daily content updates dan management |
| ✅ Testing Manager Permissions | Test content manager role restrictions |

#### Login Command

```bash
curl -X POST "http://192.168.5.12:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "tenant_manager", "password": "Manager123!@#"}'
```

#### Typical Workflow

```bash
# 1. Login as manager
TOKEN=$(curl -X POST "http://192.168.5.12:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "tenant_manager", "password": "Manager123!@#"}' | jq -r '.data.token')

# 2. Upload content
curl -X POST "http://192.168.5.12:8001/api/v1/contents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@image.jpg" \
  -F "title=Morning Promotion" \
  -F "duration=15"

# 3. Create playlist
curl -X POST "http://192.168.5.12:8001/api/v1/playlists" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Morning Playlist", "is_active": true}'

# 4. Assign to device
curl -X PUT "http://192.168.5.12:8001/api/v1/devices/{device_id}/assign-playlist" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"playlist_id": 123}'
```

---

### 🟢 3. TENANT VIEWER (Read-Only)

#### Kredensial

```
Username:     tenant_viewer
Password:     Viewer123!@#
Email:        tenant_viewer@test.com
Full Name:    Tenant Viewer
Role:         VIEWER
Organization: 20 (Test Tenant Organization)
```

#### Akses & Permissions

✅ **Apa yang BISA dilakukan** (Read-Only)
- View devices dan device status
- View content list dan content details
- View playlists dan playlist items
- View organization information
- View dashboards dan statistics

❌ **Apa yang TIDAK BISA dilakukan**
- Create, update, atau delete APAPUN
- Upload content
- Create playlists
- Manage devices
- Manage users
- Assign playlists

#### Kapan Menggunakan

| Use Case | Deskripsi |
|----------|-----------|
| ✅ Monitoring Dashboards | View device status, online/offline |
| ✅ Viewing Reports | View content usage, statistics |
| ✅ Read-Only Access | Stakeholders yang butuh visibility |
| ✅ Testing Viewer Restrictions | Test bahwa viewer tidak bisa edit |

#### Login Command

```bash
curl -X POST "http://192.168.5.12:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "tenant_viewer", "password": "Viewer123!@#"}'
```

#### Typical Usage

```bash
# 1. Login as viewer
TOKEN=$(curl -X POST "http://192.168.5.12:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "tenant_viewer", "password": "Viewer123!@#"}' | jq -r '.data.token')

# 2. View devices (READ ONLY)
curl -X GET "http://192.168.5.12:8001/api/v1/devices" \
  -H "Authorization: Bearer $TOKEN"

# 3. View content (READ ONLY)
curl -X GET "http://192.168.5.12:8001/api/v1/contents" \
  -H "Authorization: Bearer $TOKEN"

# 4. Try to upload (SHOULD FAIL with 403)
curl -X POST "http://192.168.5.12:8001/api/v1/contents/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@image.jpg"
# Response: 403 Forbidden
```

---

## 📊 PERMISSION MATRIX

| Feature | SUPER_ADMIN | ADMIN | CONTENT_MANAGER | VIEWER |
|---------|-------------|-------|-----------------|--------|
| **Organizations** | | | | |
| View All Organizations | ✅ | ✅ | ❌ | ❌ |
| View Own Organization | ✅ | ✅ | ✅ | ✅ |
| Create Organization | ✅ | ❌ | ❌ | ❌ |
| Update Organization | ✅ | ✅ (own) | ❌ | ❌ |
| Delete Organization | ✅ | ❌ | ❌ | ❌ |
| **Users** | | | | |
| List Users (All Orgs) | ✅ | ✅ | ❌ | ❌ |
| List Users (Own Org) | ✅ | ✅ | ✅ | ✅ |
| Create User | ✅ | ✅ (own org) | ❌ | ❌ |
| Update User | ✅ | ✅ (own org) | ❌ | ❌ |
| Delete User | ✅ | ✅ (own org) | ❌ | ❌ |
| Change Own Password | ✅ | ✅ | ✅ | ✅ |
| Reset Other Password | ✅ | ✅ (own org) | ❌ | ❌ |
| **Devices** | | | | |
| List Devices | ✅ | ✅ | ✅ | ✅ |
| View Device Details | ✅ | ✅ | ✅ | ✅ |
| Register Device | ✅ | ✅ | ✅ | ❌ |
| Update Device | ✅ | ✅ | ✅ | ❌ |
| Delete Device | ✅ | ✅ | ❌ | ❌ |
| Assign Playlist | ✅ | ✅ | ✅ | ❌ |
| Send Commands | ✅ | ✅ | ✅ | ❌ |
| **Content** | | | | |
| List Content | ✅ | ✅ | ✅ | ✅ |
| View Content Details | ✅ | ✅ | ✅ | ✅ |
| Upload Content | ✅ | ✅ | ✅ | ❌ |
| Update Content | ✅ | ✅ | ✅ | ❌ |
| Delete Content | ✅ | ✅ | ✅ | ❌ |
| Manage Tags | ✅ | ✅ | ✅ | ❌ |
| **Playlists** | | | | |
| List Playlists | ✅ | ✅ | ✅ | ✅ |
| View Playlist Details | ✅ | ✅ | ✅ | ✅ |
| Create Playlist | ✅ | ✅ | ✅ | ❌ |
| Update Playlist | ✅ | ✅ | ✅ | ❌ |
| Delete Playlist | ✅ | ✅ | ✅ | ❌ |
| Add/Remove Items | ✅ | ✅ | ✅ | ❌ |
| Create Schedule | ✅ | ✅ | ✅ | ❌ |

---

## 🧪 TESTING SCENARIOS

### Scenario 1: Multi-Tenant Isolation Testing

**Tujuan**: Verify bahwa user dari satu organization tidak bisa access data organization lain

```bash
# 1. Login sebagai tenant_admin (org 20)
TOKEN_ORG20=$(curl -X POST "http://192.168.5.12:8001/api/v1/auth/login" \
  -d '{"username": "tenant_admin", "password": "Admin123!@#"}' | jq -r '.data.token')

# 2. Try to access org 4 data (SHOULD FAIL)
curl -X GET "http://192.168.5.12:8001/api/v1/organizations/4" \
  -H "Authorization: Bearer $TOKEN_ORG20"
# Expected: 403 Forbidden atau filtered results

# 3. Login sebagai superadmin (no org restriction)
TOKEN_SUPER=$(curl -X POST "http://192.168.5.12:8001/api/v1/auth/login" \
  -d '{"username": "superadmin", "password": "SuperAdmin123!@#"}' | jq -r '.data.token')

# 4. Access org 4 data (SHOULD SUCCEED)
curl -X GET "http://192.168.5.12:8001/api/v1/organizations/4" \
  -H "Authorization: Bearer $TOKEN_SUPER"
# Expected: 200 OK
```

### Scenario 2: Role-Based Access Control Testing

**Tujuan**: Verify bahwa setiap role hanya bisa access fitur sesuai permission

```bash
# Test VIEWER cannot upload content
TOKEN_VIEWER=$(curl -X POST "http://192.168.5.12:8001/api/v1/auth/login" \
  -d '{"username": "tenant_viewer", "password": "Viewer123!@#"}' | jq -r '.data.token')

curl -X POST "http://192.168.5.12:8001/api/v1/contents/upload" \
  -H "Authorization: Bearer $TOKEN_VIEWER" \
  -F "file=@test.jpg"
# Expected: 403 Forbidden

# Test MANAGER can upload content
TOKEN_MANAGER=$(curl -X POST "http://192.168.5.12:8001/api/v1/auth/login" \
  -d '{"username": "tenant_manager", "password": "Manager123!@#"}' | jq -r '.data.token')

curl -X POST "http://192.168.5.12:8001/api/v1/contents/upload" \
  -H "Authorization: Bearer $TOKEN_MANAGER" \
  -F "file=@test.jpg" \
  -F "title=Test Upload"
# Expected: 200 OK

# Test MANAGER cannot create users
curl -X POST "http://192.168.5.12:8001/api/v1/users" \
  -H "Authorization: Bearer $TOKEN_MANAGER" \
  -d '{"username": "newuser", "password": "Pass123!@#", "role": "viewer"}'
# Expected: 403 Forbidden

# Test ADMIN can create users
TOKEN_ADMIN=$(curl -X POST "http://192.168.5.12:8001/api/v1/auth/login" \
  -d '{"username": "tenant_admin", "password": "Admin123!@#"}' | jq -r '.data.token')

curl -X POST "http://192.168.5.12:8001/api/v1/users" \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "email": "new@test.com", "password": "Pass123!@#", "role": "viewer", "organization_id": 20}'
# Expected: 200 OK
```

### Scenario 3: Password Change & Session Revocation (P0-16)

**Tujuan**: Verify bahwa password change invalidates semua active sessions

```bash
# 1. Login tenant_viewer dan simpan token
OLD_TOKEN=$(curl -X POST "http://192.168.5.12:8001/api/v1/auth/login" \
  -d '{"username": "tenant_viewer", "password": "Viewer123!@#"}' | jq -r '.data.token')

# 2. Verify token works
curl -X GET "http://192.168.5.12:8001/api/v1/devices" \
  -H "Authorization: Bearer $OLD_TOKEN"
# Expected: 200 OK

# 3. Change password
curl -X PUT "http://192.168.5.12:8001/api/v1/users/{viewer_id}/change-password" \
  -H "Authorization: Bearer $OLD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_password": "NewViewer123!@#"}'
# Expected: 200 OK

# 4. Try old token (SHOULD FAIL)
curl -X GET "http://192.168.5.12:8001/api/v1/devices" \
  -H "Authorization: Bearer $OLD_TOKEN"
# Expected: 401 Unauthorized with SESSION_REVOKED code

# 5. Login dengan new password
NEW_TOKEN=$(curl -X POST "http://192.168.5.12:8001/api/v1/auth/login" \
  -d '{"username": "tenant_viewer", "password": "NewViewer123!@#"}' | jq -r '.data.token')

# 6. Verify new token works
curl -X GET "http://192.168.5.12:8001/api/v1/devices" \
  -H "Authorization: Bearer $NEW_TOKEN"
# Expected: 200 OK
```

---

## 🔐 SECURITY BEST PRACTICES

### Development

✅ **DO**:
- Gunakan kredensial ini HANYA untuk development dan testing
- Rotate passwords secara berkala
- Test semua security features dengan user ini
- Dokumentasikan test scenarios

❌ **DON'T**:
- Commit kredensial ini ke public repository
- Share kredensial di chat/email tanpa enkripsi
- Gunakan kredensial ini di production
- Hardcode password di source code

### Production

✅ **DO**:
- Create user baru dengan strong password
- Implement password complexity requirements
- Enable 2FA jika tersedia
- Monitor failed login attempts
- Implement account lockout policies
- Audit user access regularly

❌ **DON'T**:
- Use default passwords (admin/admin123)
- Share credentials antar multiple people
- Skip password expiration
- Ignore failed login notifications

---

## 📝 CHANGELOG

### 2025-01-14 - Initial Setup
- Created SUPER_ADMIN (superadmin) - system owner
- Created Test Tenant Organization (ID: 20)
- Created tenant_admin (ADMIN role)
- Created tenant_manager (CONTENT_MANAGER role)
- Created tenant_viewer (VIEWER role)
- All users tested and verified working

---

## 📞 SUPPORT

Jika ada issues dengan credentials atau permissions:

1. Check backend logs: `docker logs signage-backend-python`
2. Verify user in database:
   ```sql
   SELECT id, username, role, organization_id, is_active
   FROM users
   WHERE username = 'tenant_admin';
   ```
3. Clear Redis rate limiting: `docker exec signage-redis redis-cli FLUSHDB`
4. Restart backend: `docker-compose restart backend-api`

**API Documentation**: http://192.168.5.12:8001/docs
