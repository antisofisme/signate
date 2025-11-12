# 📡 API Endpoint Comparison Matrix

**Generated:** 2025-11-12
**Purpose:** Track endpoint implementation across Backend, CMS, and Player

---

## 📋 How to Read This Matrix

| Symbol | Meaning |
|--------|---------|
| ✅ | Fully implemented and working |
| ⚠️ | Partially implemented or has issues |
| ❌ | Not implemented |
| 🚫 | Not needed for this component |
| 🔴 | Critical missing feature |
| 🟡 | Important missing feature |
| 🟢 | Optional missing feature |

---

## 🔐 Auth Service

| Endpoint | Method | Backend | CMS | Player | Notes |
|----------|--------|---------|-----|--------|-------|
| `/api/v1/auth/login` | POST | ✅ | ✅ | ✅ | Perfect alignment |
| `/api/v1/auth/logout` | POST | ✅ | ✅ | ✅ | Perfect alignment |
| `/api/v1/auth/register` | POST | ✅ | ✅ | 🚫 | CMS only |
| `/api/v1/auth/me` | GET | ✅ | ✅ | ✅ | Perfect alignment |
| `/api/v1/auth/refresh` | POST | ✅ | ✅ | ✅ | Token refresh |
| `/api/v1/auth/forgot-password` | POST | ✅ | ✅ | 🚫 | CMS only |
| `/api/v1/auth/reset-password` | POST | ✅ | ✅ | 🚫 | CMS only |

**Coverage:** Backend 7/7 (100%) | CMS 7/7 (100%) | Player 4/7 (57% - expected)

---

## 🏢 Organization Service

| Endpoint | Method | Backend | CMS | Player | Notes |
|----------|--------|---------|-----|--------|-------|
| `/api/v1/organizations` | GET | ✅ | ✅ | 🚫 | List orgs |
| `/api/v1/organizations` | POST | ✅ | ✅ | 🚫 | Create org |
| `/api/v1/organizations/{id}` | GET | ✅ | ✅ | ✅ | Get org details |
| `/api/v1/organizations/{id}` | PUT | ✅ | ✅ | 🚫 | Update org |
| `/api/v1/organizations/{id}` | DELETE | ✅ | ✅ | 🚫 | Delete org |
| `/api/v1/organizations/{id}/validate-pin` | POST | ✅ | ✅ | 🚫 | PIN validation |

**Coverage:** Backend 6/6 (100%) | CMS 6/6 (100%) | Player 1/6 (17% - expected)

---

## 👥 User Service

| Endpoint | Method | Backend | CMS | Player | Notes |
|----------|--------|---------|-----|--------|-------|
| `/api/v1/users` | GET | ✅ | ✅ | 🚫 | List users |
| `/api/v1/users` | POST | ✅ | ✅ | 🚫 | Create user |
| `/api/v1/users/{id}` | GET | ✅ | ✅ | 🚫 | Get user |
| `/api/v1/users/{id}` | PUT | ✅ | ✅ | 🚫 | Update user |
| `/api/v1/users/{id}` | DELETE | ✅ | ✅ | 🚫 | Delete user |
| `/api/v1/users/{id}/change-password` | PUT | ✅ | ✅ | 🚫 | Change password |

**Coverage:** Backend 6/6 (100%) | CMS 6/6 (100%) | Player 0/6 (0% - not needed)

---

## 📱 Device Service

| Endpoint | Method | Backend | CMS | Player | Priority | Notes |
|----------|--------|---------|-----|--------|----------|-------|
| **CRUD Operations** |
| `/api/v1/devices` | GET | ✅ | ✅ | 🚫 | - | List devices |
| `/api/v1/devices` | POST | ✅ | ✅ | 🚫 | - | Create device |
| `/api/v1/devices/{id}` | GET | ✅ | ✅ | ✅ | - | Get device |
| `/api/v1/devices/{id}` | PATCH | ✅ | ✅ | 🚫 | - | Update device |
| `/api/v1/devices/{id}` | DELETE | ✅ | ✅ | 🚫 | - | Delete device |
| **Registration** |
| `/api/v1/devices/request-code` | POST | ✅ | 🚫 | ✅ | - | Player requests code |
| `/api/v1/devices/tv` | POST | ✅ | 🚫 | ✅ | - | TV registration |
| `/api/v1/devices/monitor` | POST | ✅ | 🚫 | ✅ | - | Monitor registration |
| `/api/v1/devices/activate` | POST | ✅ | ✅ | 🚫 | - | CMS activates device |
| `/api/v1/devices/check-activation/{code}` | GET | ✅ | 🚫 | ✅ | - | Player polls activation |
| **Monitoring** |
| `/api/v1/devices/{id}/heartbeat` | POST | ✅ | 🚫 | ✅ | - | Device heartbeat |
| `/api/v1/devices/{id}/logs` | GET | ✅ | ✅ | 🚫 | - | Get device logs |
| `/api/client/logs/batch` | POST | ✅ | 🚫 | ✅ | - | Batch log upload |
| **Content Resolution** |
| `/api/v1/devices/{id}/content/resolved` | GET | ✅ | ⚠️ | ⚠️ | 🟡 | CMS & Player may use different endpoint |
| `/api/client/playlist` | GET | ✅ | 🚫 | ✅ | - | Player fetches playlist |
| **Commands** |
| `/api/v1/devices/{id}/commands` | GET | ✅ | ✅ | ✅ | - | Get pending commands |
| `/api/v1/devices/{id}/commands` | POST | ✅ | ✅ | 🚫 | - | Send command |
| `/api/v1/devices/{id}/commands/{cmd_id}` | GET | ✅ | ✅ | ✅ | - | Get command status |
| **Network** |
| `/api/v1/devices/{id}/speed-test` | POST | ✅ | ❌ | ✅ | 🟢 | Record speed test |
| `/api/v1/devices/{id}/speed-tests` | GET | ✅ | ❌ | 🚫 | 🟢 | Get speed test history |
| **Device Groups** |
| `/api/v1/devices/groups` | GET | ✅ | ✅ | ❌ | 🟡 | List groups |
| `/api/v1/devices/groups` | POST | ✅ | ✅ | 🚫 | - | Create group |
| `/api/v1/devices/groups/roots` | GET | ✅ | ✅ | 🚫 | - | Get root groups |
| `/api/v1/devices/groups/{id}` | GET | ✅ | ✅ | ❌ | 🟡 | Get group |
| `/api/v1/devices/groups/{id}` | PATCH | ✅ | ✅ | 🚫 | - | Update group |
| `/api/v1/devices/groups/{id}` | DELETE | ✅ | ✅ | 🚫 | - | Delete group |
| `/api/v1/devices/groups/{id}/children` | GET | ✅ | ✅ | ❌ | 🟡 | Get child groups |
| `/api/v1/devices/groups/{id}/devices` | GET | ✅ | ✅ | 🚫 | - | Get devices in group |
| `/api/v1/devices/groups/{id}/stats` | GET | ✅ | ✅ | 🚫 | - | Get group stats |
| `/api/v1/devices/groups/{id}/devices` | POST | ✅ | ✅ | 🚫 | - | Add device to group |
| `/api/v1/devices/groups/{id}/devices/{did}` | DELETE | ✅ | ✅ | 🚫 | - | Remove device from group |

**Coverage:** Backend 31/31 (100%) | CMS 22/31 (71%) | Player 9/31 (29%)

**Issues:**
- 🟡 Player should fetch group info for better targeting
- 🟢 CMS missing speed test UI (low priority)

---

## 📁 Content Service

| Endpoint | Method | Backend | CMS | Player | Notes |
|----------|--------|---------|-----|--------|-------|
| `/api/v1/contents` | GET | ✅ | ✅ | 🚫 | List content |
| `/api/v1/contents/upload` | POST | ✅ | ✅ | 🚫 | Upload single file |
| `/api/v1/contents/bulk-upload` | POST | ✅ | ✅ | 🚫 | Bulk upload |
| `/api/v1/contents/{id}` | GET | ✅ | ✅ | ✅ | Get content details |
| `/api/v1/contents/{id}` | PUT | ✅ | ✅ | 🚫 | Update metadata |
| `/api/v1/contents/{id}` | DELETE | ✅ | ✅ | 🚫 | Delete content |
| `/api/v1/contents/bulk-delete` | POST | ✅ | ✅ | 🚫 | Bulk delete |
| `/api/v1/contents/bulk-update` | POST | ✅ | ✅ | 🚫 | Bulk update |
| `/api/v1/contents/{id}/download` | GET | ✅ | ✅ | ⚠️ | Player streams, not downloads |
| `/api/v1/contents/{id}/preview` | GET | ✅ | ✅ | 🚫 | Preview/thumbnail |
| `/api/v1/contents/stats` | GET | ✅ | ✅ | 🚫 | Storage statistics |
| `/api/client/content/{id}` | GET | ✅ | 🚫 | ✅ | Public content access |

**Coverage:** Backend 12/12 (100%) | CMS 11/12 (92%) | Player 3/12 (25% - expected)

---

## 📋 Playlist Service

| Endpoint | Method | Backend | CMS | Player | Notes |
|----------|--------|---------|-----|--------|-------|
| **CRUD** |
| `/api/v1/playlists` | GET | ✅ | ✅ | 🚫 | List playlists |
| `/api/v1/playlists` | POST | ✅ | ✅ | 🚫 | Create playlist |
| `/api/v1/playlists/{id}` | GET | ✅ | ✅ | ✅ | Get playlist |
| `/api/v1/playlists/{id}` | PATCH | ✅ | ✅ | 🚫 | Update playlist |
| `/api/v1/playlists/{id}` | DELETE | ✅ | ✅ | 🚫 | Delete playlist |
| **Content Management** |
| `/api/v1/playlists/{id}/content` | GET | ✅ | ✅ | 🚫 | Get content items |
| `/api/v1/playlists/{id}/content` | POST | ✅ | ✅ | 🚫 | Add content |
| `/api/v1/playlists/{id}/content/{item_id}` | DELETE | ✅ | ✅ | 🚫 | Remove content |
| `/api/v1/playlists/{id}/reorder` | PATCH | ✅ | ✅ | 🚫 | Reorder items |
| **Assignments** |
| `/api/v1/playlists/{id}/assignments` | GET | ✅ | ✅ | 🚫 | Get assignments |
| `/api/v1/playlists/{id}/assign/devices` | POST | ✅ | ✅ | 🚫 | Assign to devices |
| `/api/v1/playlists/{id}/assign/tags` | POST | ✅ | ✅ | 🚫 | Assign to tags |
| `/api/v1/playlists/{id}/assign/devices` | DELETE | ✅ | ✅ | 🚫 | Unassign from devices |
| `/api/v1/playlists/{id}/assign/tags` | DELETE | ✅ | ✅ | 🚫 | Unassign from tags |

**Coverage:** Backend 14/14 (100%) | CMS 14/14 (100%) | Player 1/14 (7% - expected)

---

## 🏷️ Tag Service

| Endpoint | Method | Backend | CMS | Player | Notes |
|----------|--------|---------|-----|--------|-------|
| `/api/v1/tags` | GET | ✅ | ✅ | 🚫 | List tags |
| `/api/v1/tags` | POST | ✅ | ✅ | 🚫 | Create tag |
| `/api/v1/tags/{id}` | GET | ✅ | ✅ | 🚫 | Get tag |
| `/api/v1/tags/{id}` | PUT | ✅ | ✅ | 🚫 | Update tag |
| `/api/v1/tags/{id}` | DELETE | ✅ | ✅ | 🚫 | Delete tag |
| `/api/v1/tags/{id}/usage` | GET | ✅ | ✅ | 🚫 | Tag usage stats |
| `/api/v1/tags/{id}/assign-content` | POST | ✅ | ✅ | 🚫 | Assign to content |
| `/api/v1/tags/{id}/assign-contents` | POST | ✅ | ✅ | 🚫 | Bulk assign |
| `/api/v1/tags/{id}/unassign-content` | DELETE | ✅ | ✅ | 🚫 | Unassign from content |
| `/api/v1/tags/{id}/unassign-contents` | DELETE | ✅ | ✅ | 🚫 | Bulk unassign |
| `/api/v1/contents/{id}/tags` | GET | ✅ | ✅ | 🚫 | Get content tags |

**Coverage:** Backend 11/11 (100%) | CMS 11/11 (100%) | Player 0/11 (0% - not needed)

---

## 📊 Analytics Service

| Endpoint | Method | Backend | CMS | Player | Priority | Notes |
|----------|--------|---------|-----|--------|----------|-------|
| `/api/v1/analytics/dashboard` | GET | ✅ | ✅ | 🚫 | - | Dashboard data |
| `/api/v1/analytics/activity-logs` | GET | ✅ | ✅ | 🚫 | - | Activity logs |
| `/api/v1/analytics/device-logs` | GET | ✅ | ✅ | 🚫 | - | Device logs |
| `/api/v1/analytics/reports` | GET | ✅ | ✅ | 🚫 | - | Generate reports |
| `/api/v1/analytics/playback/start` | POST | ✅ | 🚫 | ✅ | - | Log playback start |
| `/api/v1/analytics/playback/{id}/end` | PUT | ✅ | 🚫 | ✅ | - | Log playback end |
| `/api/v1/analytics/stats` | GET | ✅ | ⚠️ | 🚫 | 🟡 | CMS should show real-time stats |

**Coverage:** Backend 7/7 (100%) | CMS 5/7 (71%) | Player 2/7 (29%)

**Issues:**
- 🟡 CMS missing real-time stats display (needs WebSocket)

---

## 📝 Audit Service

| Endpoint | Method | Backend | CMS | Player | Notes |
|----------|--------|---------|-----|--------|-------|
| `/api/v1/audit-logs` | GET | ✅ | ✅ | 🚫 | List audit logs |
| `/api/v1/audit-logs/{id}` | GET | ✅ | ✅ | 🚫 | Get audit log |

**Coverage:** Backend 2/2 (100%) | CMS 2/2 (100%) | Player 0/2 (0% - not needed)

---

## 🔐 RBAC Service

| Endpoint | Method | Backend | CMS | Player | Priority | Notes |
|----------|--------|---------|-----|--------|----------|-------|
| `/api/v1/roles` | GET | ✅ | ❌ | 🚫 | 🔴 | List roles |
| `/api/v1/roles` | POST | ✅ | ❌ | 🚫 | 🔴 | Create role |
| `/api/v1/roles/{id}` | GET | ✅ | ❌ | 🚫 | 🔴 | Get role |
| `/api/v1/roles/{id}` | PUT | ✅ | ❌ | 🚫 | 🔴 | Update role |
| `/api/v1/roles/{id}` | DELETE | ✅ | ❌ | 🚫 | 🔴 | Delete role |
| `/api/v1/roles/system` | GET | ✅ | ❌ | 🚫 | 🔴 | System roles |
| `/api/v1/organizations/{id}/roles` | GET | ✅ | ❌ | 🚫 | 🔴 | Org roles |
| `/api/v1/roles/{id}/permissions` | GET | ✅ | ❌ | 🚫 | 🔴 | Get permissions |
| `/api/v1/roles/{id}/permissions` | POST | ✅ | ❌ | 🚫 | 🔴 | Add permission |
| `/api/v1/roles/{id}/permissions` | DELETE | ✅ | ❌ | 🚫 | 🔴 | Remove permission |
| `/api/v1/roles/{id}/permissions/check` | POST | ✅ | ❌ | 🚫 | 🔴 | Check permission |

**Coverage:** Backend 11/11 (100%) | CMS 0/11 (0%) | Player 0/11 (0%)

**Status:** 🔴 **CRITICAL - COMPLETELY MISSING IN CMS**

---

## 👤 Session Service

| Endpoint | Method | Backend | CMS | Player | Priority | Notes |
|----------|--------|---------|-----|--------|----------|-------|
| `/api/v1/sessions` | GET | ✅ | ❌ | 🚫 | 🟡 | List user sessions |
| `/api/v1/sessions/{id}` | GET | ✅ | ❌ | 🚫 | 🟡 | Get session |
| `/api/v1/sessions/{id}` | DELETE | ✅ | ❌ | 🚫 | 🟡 | Revoke session |
| `/api/v1/sessions/revoke-all` | POST | ✅ | ❌ | 🚫 | 🟡 | Logout all devices |
| `/api/v1/sessions/stats` | GET | ✅ | ❌ | 🚫 | 🟡 | Session statistics |
| `/api/v1/sessions/active` | GET | ✅ | ❌ | 🚫 | 🟡 | Active sessions |
| `/api/v1/sessions/user/{id}` | GET | ✅ | ❌ | 🚫 | 🟡 | Admin: user sessions |
| `/api/v1/sessions/ip/{ip}` | GET | ✅ | ❌ | 🚫 | 🟡 | Admin: sessions by IP |

**Coverage:** Backend 8/8 (100%) | CMS 0/8 (0%) | Player 0/8 (0%)

**Status:** 🟡 **HIGH PRIORITY - COMPLETELY MISSING IN CMS**

---

## 📅 Schedule Service

| Endpoint | Method | Backend | CMS | Player | Priority | Notes |
|----------|--------|---------|-----|--------|----------|-------|
| `/api/v1/schedules` | GET | ✅ | ⚠️ | ✅ | - | List schedules |
| `/api/v1/schedules` | POST | ✅ | ⚠️ | 🚫 | - | Create schedule |
| `/api/v1/schedules/{id}` | GET | ✅ | ⚠️ | ✅ | - | Get schedule |
| `/api/v1/schedules/{id}` | PUT | ✅ | ⚠️ | 🚫 | - | Update schedule |
| `/api/v1/schedules/{id}` | DELETE | ✅ | ⚠️ | 🚫 | - | Delete schedule |
| `/api/v1/schedules/{id}/activate` | POST | ✅ | ⚠️ | 🚫 | - | Activate schedule |
| `/api/v1/schedules/{id}/deactivate` | POST | ✅ | ⚠️ | 🚫 | - | Deactivate schedule |
| `/api/v1/schedules/{id}/pause` | POST | ✅ | ⚠️ | 🚫 | - | Pause schedule |
| `/api/v1/schedules/check-conflicts` | POST | ✅ | ⚠️ | 🚫 | 🟡 | Check conflicts |
| `/api/v1/schedules/occurrences` | POST | ✅ | ⚠️ | 🚫 | 🟡 | Get occurrences |
| `/api/v1/schedules/device/{id}` | GET | ✅ | ⚠️ | ✅ | - | Device schedules |
| `/api/v1/schedules/playlist/{id}` | GET | ✅ | ⚠️ | ✅ | - | Playlist schedules |

**Coverage:** Backend 12/12 (100%) | CMS 12/12 (100% basic) | Player 4/12 (33%)

**Issues:**
- ⚠️ CMS has basic implementation, needs UI enhancement
- 🟡 Missing visual calendar view
- 🟡 Missing conflict detection UI

---

## 🎨 Widget Service

| Endpoint | Method | Backend | CMS | Player | Priority | Notes |
|----------|--------|---------|-----|--------|----------|-------|
| `/api/v1/widgets` | GET | ✅ | ❌ | 🚫 | 🔴 | List widgets |
| `/api/v1/widgets` | POST | ✅ | ❌ | 🚫 | 🔴 | Create widget |
| `/api/v1/widgets/{id}` | GET | ✅ | ❌ | ✅ | 🔴 | Get widget |
| `/api/v1/widgets/{id}` | PUT | ✅ | ❌ | 🚫 | 🔴 | Update widget |
| `/api/v1/widgets/{id}` | DELETE | ✅ | ❌ | 🚫 | 🔴 | Delete widget |
| `/api/v1/widgets/playlists/{id}/widgets` | GET | ✅ | ❌ | ✅ | 🔴 | Playlist widgets |
| `/api/v1/widgets/playlists/{id}/widgets` | POST | ✅ | ❌ | 🚫 | 🔴 | Assign widget |
| `/api/v1/widgets/playlist-widgets/{id}` | PUT | ✅ | ❌ | 🚫 | 🔴 | Update assignment |
| `/api/v1/widgets/playlists/{id}/widgets/{wid}` | DELETE | ✅ | ❌ | 🚫 | 🔴 | Remove widget |

**Coverage:** Backend 9/9 (100%) | CMS 0/9 (0%) | Player 2/9 (22%)

**Status:** 🔴 **CRITICAL - WRONG API PATH IN CMS**
- CMS currently calls `/widgets` instead of `/api/v1/widgets`
- Must fix immediately!

---

## 📄 Template Service

| Endpoint | Method | Backend | CMS | Player | Priority | Notes |
|----------|--------|---------|-----|--------|----------|-------|
| `/api/v1/templates` | GET | ✅ | ❌ | 🚫 | 🔴 | List templates |
| `/api/v1/templates` | POST | ✅ | ❌ | 🚫 | 🔴 | Create template |
| `/api/v1/templates/{id}` | GET | ✅ | ❌ | ✅ | 🔴 | Get template |
| `/api/v1/templates/{id}` | PUT | ✅ | ❌ | 🚫 | 🔴 | Update template |
| `/api/v1/templates/{id}` | DELETE | ✅ | ❌ | 🚫 | 🔴 | Delete template |
| `/api/v1/templates/{id}/render` | POST | ✅ | ❌ | ✅ | 🔴 | Render template |
| `/api/v1/templates/validate` | POST | ✅ | ❌ | 🚫 | 🔴 | Validate template |
| `/api/v1/templates/extract-variables` | POST | ✅ | ❌ | 🚫 | 🔴 | Extract variables |

**Coverage:** Backend 8/8 (100%) | CMS 0/8 (0%) | Player 2/8 (25%)

**Status:** 🔴 **CRITICAL - WRONG API PATH IN CMS**
- CMS currently calls `/templates` instead of `/api/v1/templates`
- Must fix immediately!

---

## 🌐 Translation Service

| Endpoint | Method | Backend | CMS | Player | Priority | Notes |
|----------|--------|---------|-----|--------|----------|-------|
| `/api/v1/translations` | GET | ✅ | ⚠️ | ✅ | - | List translations |
| `/api/v1/translations` | POST | ✅ | ⚠️ | 🚫 | - | Create translation |
| `/api/v1/translations/{id}` | GET | ✅ | ⚠️ | ✅ | - | Get translation |
| `/api/v1/translations/{id}` | PUT | ✅ | ⚠️ | 🚫 | - | Update translation |
| `/api/v1/translations/{id}` | DELETE | ✅ | ⚠️ | 🚫 | - | Delete translation |
| `/api/v1/translations/{type}/{id}` | GET | ✅ | ⚠️ | ✅ | - | Entity translations |
| `/api/v1/translations/bulk` | POST | ✅ | ⚠️ | 🚫 | - | Bulk create |
| `/api/v1/translations/import` | POST | ✅ | ⚠️ | 🚫 | - | Import CSV/JSON |
| `/api/v1/translations/stats` | GET | ✅ | ⚠️ | 🚫 | - | Translation stats |
| `/api/v1/translations/{id}/approve` | POST | ✅ | ⚠️ | 🚫 | - | Approve translation |
| `/api/v1/translations/{id}/reject` | POST | ✅ | ⚠️ | 🚫 | - | Reject translation |

**Coverage:** Backend 11/11 (100%) | CMS 11/11 (100% new) | Player 3/11 (27%)

**Issues:**
- ⚠️ Recently added (Nov 11), needs thorough testing
- ⚠️ Should use `apiClient` instead of raw `axios`

---

## 🏨 PMS Service

| Endpoint | Method | Backend | CMS | Player | Priority | Notes |
|----------|--------|---------|-----|--------|----------|-------|
| `/api/v1/pms/config` | GET | ✅ | ❌ | 🚫 | 🟡 | Get PMS config |
| `/api/v1/pms/config` | PUT | ✅ | ❌ | 🚫 | 🟡 | Update config |
| `/api/v1/pms/guests` | GET | ✅ | ❌ | 🚫 | 🟡 | List guests |
| `/api/v1/pms/guests/current` | GET | ✅ | ❌ | 🚫 | 🟡 | Current guests |
| `/api/v1/pms/device/{id}/current-guest` | GET | ✅ | ❌ | ✅ | 🟡 | Device guest data |
| `/api/v1/pms/rooms` | GET | ✅ | ❌ | 🚫 | 🟡 | List rooms |
| `/api/v1/pms/stats` | GET | ✅ | ❌ | 🚫 | 🟡 | PMS statistics |
| `/api/v1/pms/sync/guests` | POST | ✅ | ❌ | 🚫 | 🟡 | Sync guests |
| `/api/v1/pms/sync/rooms` | POST | ✅ | ❌ | 🚫 | 🟡 | Sync rooms |
| `/api/v1/pms/trigger-sync/{org_id}` | POST | ✅ | ❌ | 🚫 | 🟡 | Trigger sync |
| `/ws/pms/sync` | WS | ✅ | ❌ | 🚫 | 🟡 | WebSocket sync |

**Coverage:** Backend 11/11 (100%) | CMS 0/11 (0%) | Player 1/11 (9%)

**Status:** 🟡 **HIGH PRIORITY - COMPLETELY MISSING IN CMS**

---

## 🌤️ Weather Service

| Endpoint | Method | Backend | CMS | Player | Priority | Notes |
|----------|--------|---------|-----|--------|----------|-------|
| `/api/v1/weather/current` | GET | ✅ | ❌ | ✅ | 🟢 | Current weather |
| `/api/v1/weather/forecast` | GET | ✅ | ❌ | ✅ | 🟢 | Weather forecast |
| `/api/v1/weather/locations` | GET | ✅ | ❌ | 🚫 | 🟢 | Saved locations |
| `/api/v1/weather/locations` | POST | ✅ | ❌ | 🚫 | 🟢 | Add location |
| `/api/v1/weather/locations/{id}` | DELETE | ✅ | ❌ | 🚫 | 🟢 | Remove location |

**Coverage:** Backend 5/5 (100%) | CMS 0/5 (0%) | Player 2/5 (40%)

**Status:** 🟢 **LOW PRIORITY - Optional feature**

---

## 🔌 WebSocket Endpoints

| Endpoint | Protocol | Backend | CMS | Player | Priority | Notes |
|----------|----------|---------|-----|--------|----------|-------|
| `/api/ws/device/{id}` | WS | ✅ | 🚫 | ✅ | - | Device WebSocket |
| `/api/ws/admin` | WS | ✅ | ❌ | 🚫 | 🔴 | Admin WebSocket |
| `/ws/pms/sync` | WS | ✅ | ❌ | 🚫 | 🟡 | PMS sync WS |

**Coverage:** Backend 3/3 (100%) | CMS 0/3 (0%) | Player 1/3 (33%)

**Status:** 🔴 **CRITICAL - CMS MISSING WEBSOCKET**

---

## 📊 Overall Coverage Summary

### By Component

| Component | Total Endpoints | Implemented | Coverage | Grade |
|-----------|----------------|-------------|----------|-------|
| **Backend** | ~180 | 180 | 100% | A+ |
| **CMS** | ~180 | 123 | 68% | C+ |
| **Player** | ~180 | 44 | 24% | D |

**Note:** Player low coverage is expected - it only needs client-side endpoints.

### By Priority

| Priority | Endpoints | CMS Missing | Status |
|----------|-----------|-------------|--------|
| 🔴 Critical | 35 | 35 | Fix immediately |
| 🟡 High | 28 | 28 | Fix this month |
| 🟢 Low | 8 | 8 | Optional |

### Critical Missing Endpoints in CMS

1. **RBAC** - 11 endpoints (0% coverage) 🔴
2. **Sessions** - 8 endpoints (0% coverage) 🟡
3. **PMS** - 11 endpoints (0% coverage) 🟡
4. **WebSocket** - 2 endpoints (0% coverage) 🔴
5. **Widgets** - Wrong API path 🔴
6. **Templates** - Wrong API path 🔴

---

## 🎯 Priority Actions

### This Week (Critical)

1. ✅ Fix Widgets API path: `/widgets` → `/api/v1/widgets`
2. ✅ Fix Templates API path: `/templates` → `/api/v1/templates`
3. ✅ Verify backend routes match this matrix

### Next 2 Weeks (High)

4. 🔴 Implement CMS WebSocket connection to `/api/ws/admin`
5. 🔴 Implement RBAC module (11 endpoints)
6. 🟡 Implement Sessions module (8 endpoints)

### Next Month (Medium)

7. 🟡 Implement PMS configuration (11 endpoints)
8. 🟢 Add Weather configuration (5 endpoints)

---

## 📝 Update Log

| Date | Updated By | Changes |
|------|-----------|---------|
| 2025-11-12 | AI Assistant | Initial matrix creation |
| | | |
| | | |

---

**Document Version:** 1.0
**Last Updated:** 2025-11-12
**Next Review:** 2025-11-19 (weekly)
