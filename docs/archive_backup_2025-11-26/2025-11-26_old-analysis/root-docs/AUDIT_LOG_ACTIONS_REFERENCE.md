# Audit Log Actions Reference

## Complete List of Logged Actions

### Widget Service (6 actions)

| Action | Endpoint | HTTP Method | Details Logged |
|--------|----------|-------------|----------------|
| `widget.create` | `/widgets` | POST | `name`, `widget_type` |
| `widget.update` | `/widgets/{id}` | PUT | `name`, `is_active` |
| `widget.delete` | `/widgets/{id}` | DELETE | `name` |
| `widget.assign_to_playlist` | `/widgets/playlists/{playlist_id}/widgets` | POST | `playlist_id`, `widget_id` |
| `playlist_widget.update` | `/widgets/playlist-widgets/{id}` | PUT | `position`, `z_index` |
| `widget.remove_from_playlist` | `/widgets/playlists/{playlist_id}/widgets/{widget_id}` | DELETE | `playlist_id`, `widget_id` |

### Template Service (3 actions)

| Action | Endpoint | HTTP Method | Details Logged |
|--------|----------|-------------|----------------|
| `template.create` | `/templates` | POST | `name`, `template_type` |
| `template.update` | `/templates/{id}` | PUT | `name`, `is_active` |
| `template.delete` | `/templates/{id}` | DELETE | `name` |

## Sample Audit Log Entries

### Widget Create
```json
{
  "user_id": 1,
  "action": "widget.create",
  "resource_type": "widget",
  "resource_id": 123,
  "details": {
    "name": "Clock Widget",
    "widget_type": "clock"
  },
  "ip_address": "192.168.1.100",
  "organization_id": 1,
  "created_at": "2025-01-21T10:30:00Z"
}
```

### Widget Update
```json
{
  "user_id": 1,
  "action": "widget.update",
  "resource_type": "widget",
  "resource_id": 123,
  "details": {
    "name": "Updated Clock Widget",
    "is_active": true
  },
  "ip_address": "192.168.1.100",
  "organization_id": 1,
  "created_at": "2025-01-21T10:35:00Z"
}
```

### Widget Delete
```json
{
  "user_id": 1,
  "action": "widget.delete",
  "resource_type": "widget",
  "resource_id": 123,
  "details": {
    "name": "Clock Widget"
  },
  "ip_address": "192.168.1.100",
  "organization_id": 1,
  "created_at": "2025-01-21T10:40:00Z"
}
```

### Widget Assign to Playlist
```json
{
  "user_id": 1,
  "action": "widget.assign_to_playlist",
  "resource_type": "widget",
  "resource_id": 123,
  "details": {
    "playlist_id": 456,
    "widget_id": 123
  },
  "ip_address": "192.168.1.100",
  "organization_id": 1,
  "created_at": "2025-01-21T10:45:00Z"
}
```

### Playlist Widget Update
```json
{
  "user_id": 1,
  "action": "playlist_widget.update",
  "resource_type": "playlist_widget",
  "resource_id": 789,
  "details": {
    "position": "top-right",
    "z_index": 100
  },
  "ip_address": "192.168.1.100",
  "organization_id": 1,
  "created_at": "2025-01-21T10:50:00Z"
}
```

### Template Create
```json
{
  "user_id": 1,
  "action": "template.create",
  "resource_type": "template",
  "resource_id": 234,
  "details": {
    "name": "Greeting Template",
    "template_type": "greeting"
  },
  "ip_address": "192.168.1.100",
  "organization_id": 1,
  "created_at": "2025-01-21T11:00:00Z"
}
```

## Querying Audit Logs

### Get all widget operations
```sql
SELECT * FROM audit_logs 
WHERE action LIKE 'widget.%' 
ORDER BY created_at DESC;
```

### Get all template operations
```sql
SELECT * FROM audit_logs 
WHERE action LIKE 'template.%' 
ORDER BY created_at DESC;
```

### Get all create operations
```sql
SELECT * FROM audit_logs 
WHERE action LIKE '%.create' 
ORDER BY created_at DESC;
```

### Get all delete operations
```sql
SELECT * FROM audit_logs 
WHERE action LIKE '%.delete' 
ORDER BY created_at DESC;
```

### Get operations by user
```sql
SELECT al.*, u.username 
FROM audit_logs al 
JOIN users u ON al.user_id = u.id 
WHERE u.username = 'admin' 
  AND (al.action LIKE 'widget.%' OR al.action LIKE 'template.%')
ORDER BY al.created_at DESC;
```

### Get operations by organization
```sql
SELECT al.*, u.username 
FROM audit_logs al 
JOIN users u ON al.user_id = u.id 
WHERE al.organization_id = 1 
  AND (al.action LIKE 'widget.%' OR al.action LIKE 'template.%')
ORDER BY al.created_at DESC;
```

### Get operations on specific resource
```sql
SELECT * FROM audit_logs 
WHERE resource_type = 'widget' 
  AND resource_id = 123 
ORDER BY created_at DESC;
```

## API Response After Operations

All CREATE/UPDATE/DELETE operations now return the normal response PLUS create an audit log entry in the background.

Example:
```python
# When creating a widget, the response is:
{
  "id": 123,
  "name": "Clock Widget",
  "widget_type": "clock",
  "is_active": true,
  ...
}

# AND an audit log is created silently in the database
```

## Monitoring & Reporting

### Activity Summary by User
```sql
SELECT 
    u.username,
    COUNT(*) as total_operations,
    COUNT(CASE WHEN al.action LIKE '%.create' THEN 1 END) as creates,
    COUNT(CASE WHEN al.action LIKE '%.update' THEN 1 END) as updates,
    COUNT(CASE WHEN al.action LIKE '%.delete' THEN 1 END) as deletes
FROM audit_logs al
JOIN users u ON al.user_id = u.id
WHERE al.action LIKE 'widget.%' OR al.action LIKE 'template.%'
GROUP BY u.username
ORDER BY total_operations DESC;
```

### Activity Summary by Day
```sql
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_operations,
    COUNT(DISTINCT user_id) as unique_users
FROM audit_logs
WHERE action LIKE 'widget.%' OR action LIKE 'template.%'
GROUP BY DATE(created_at)
ORDER BY date DESC
LIMIT 30;
```

### Recent Activity Dashboard
```sql
SELECT 
    al.action,
    u.username,
    al.resource_type,
    al.resource_id,
    al.details,
    al.created_at
FROM audit_logs al
JOIN users u ON al.user_id = u.id
WHERE al.action LIKE 'widget.%' OR al.action LIKE 'template.%'
ORDER BY al.created_at DESC
LIMIT 50;
```

