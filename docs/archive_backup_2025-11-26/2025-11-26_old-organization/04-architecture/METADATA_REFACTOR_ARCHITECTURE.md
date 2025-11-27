# Metadata Architecture: Current vs Proposed

## Current Architecture (Duplicated Metadata)

```
┌─────────────────────┐
│   Web Admin         │
│   (Upload)          │
└──────────┬──────────┘
           │
           ├─→ Update PostgreSQL (title, duration, mime_type, is_active)
           │   ├─ Content.title
           │   ├─ Content.duration
           │   ├─ Content.mime_type
           │   └─ Content.is_active
           │
           └─→ Upload to Anthias (file + metadata)
               ├─ File (binary content)
               ├─ name (DUPLICATE of title)
               ├─ duration (DUPLICATE)
               ├─ mimetype (DUPLICATE of mime_type)
               └─ is_enabled (DUPLICATE of is_active)

┌──────────────────────────┐
│  PostgreSQL              │
│  Content Table           │
├──────────────────────────┤
│ id                       │
│ title                    │ ← Single source
│ duration                 │ ← Single source
│ mime_type                │ ← Single source
│ is_active                │ ← Single source
│ anthias_asset_id         │
│ anthias_url              │
│ [20+ metadata fields]    │
└──────────────────────────┘

┌────────────────────────────┐
│  Anthias (Digital Signage) │
│  Asset Table               │
├────────────────────────────┤
│ asset_id                   │
│ uri                        │
│ name                       │ ← DUPLICATE (stale!)
│ duration                   │ ← DUPLICATE (stale!)
│ mimetype                   │ ← DUPLICATE (stale!)
│ is_enabled                 │ ← DUPLICATE (stale!)
└────────────────────────────┘

Playlist Generation Flow:
─────────────────────────

Device → /playlist endpoint
         │
         └─→ Query PostgreSQL (get content list)
             │
             └─→ For each content:
                 ├─ Get content.anthias_asset_id
                 ├─ FETCH from Anthias API (130ms latency!)
                 │   GET /api/v1/assets/{asset_id}
                 │   Response: { uri, name, duration, mimetype, ... }
                 ├─ Extract uri from Anthias
                 └─ Build URL
                     duration = content.duration (PostgreSQL)
                     mime_type = content.mime_type (PostgreSQL)
                     [Anthias data IGNORED]

Problem Summary:
────────────────
❌ Redundant API calls to Anthias per playlist request (-130ms latency)
❌ Metadata duplication (4 fields)
❌ Risk of inconsistency (Anthias metadata becomes stale)
❌ Tight coupling (can't remove Anthias without updating metadata)
❌ 2 sources of truth = confusion
```

## Proposed Architecture (Single Source of Truth)

```
┌─────────────────────┐
│   Web Admin         │
│   (Upload)          │
└──────────┬──────────┘
           │
           ├─→ Update PostgreSQL (title, duration, mime_type, is_active)
           │   ├─ Content.title
           │   ├─ Content.duration
           │   ├─ Content.mime_type
           │   └─ Content.is_active
           │
           └─→ Upload to Anthias (FILE ONLY)
               ├─ File (binary content)
               └─ Return: uri, asset_id
                          ↓
                   Save to PostgreSQL.anthias_file_uri
                   (Cache for later use)

┌──────────────────────────┐
│  PostgreSQL              │
│  Content Table           │
├──────────────────────────┤
│ id                       │
│ title                    │ ← SINGLE SOURCE
│ duration                 │ ← SINGLE SOURCE
│ mime_type                │ ← SINGLE SOURCE
│ is_active                │ ← SINGLE SOURCE
│ anthias_asset_id         │ (for deletion reference)
│ anthias_file_uri         │ (NEW: cached URI) ← SINGLE SOURCE
│ [20+ metadata fields]    │
└──────────────────────────┘

┌────────────────────────┐
│  Anthias (File Store)  │
│  Asset Table           │
├────────────────────────┤
│ asset_id               │
│ uri                    │
│ [file storage only]    │
└────────────────────────┘

Playlist Generation Flow:
─────────────────────────

Device → /playlist endpoint
         │
         └─→ Query PostgreSQL (get content list)
             │
             └─→ For each content:
                 ├─ Get content from PostgreSQL
                 │   ├─ content.anthias_file_uri (NO API CALL!)
                 │   ├─ content.duration
                 │   └─ content.mime_type
                 ├─ Build URL from cached uri
                 └─ Return with PostgreSQL metadata
                     (Fast, no external calls!)

Benefits:
─────────
✓ No Anthias API calls per playlist request (-130ms)
✓ Single source of truth for metadata
✓ Update content → immediate effect (no Anthias sync needed)
✓ Loose coupling (Anthias is pure file storage)
✓ Better performance & consistency
```

## Data Consistency Comparison

### Current (Problematic)
```
Scenario: Update content title via Web Admin

1. Web Admin PATCH /api/contents/{id}
   ├─ Update PostgreSQL: title = "New Title"
   │   ✓ Immediate
   │
   └─ Send to Anthias: name = "New Title"
       └─ Async? Network latency? Fails silently?
           → Users see "New Title" in admin
           → Devices see old "Old Title" in playlist (INCONSISTENT!)

Timeline:
─────────
t=0   Web admin updates PostgreSQL
t=100ms  Anthias sync call sent
t=200ms  Anthias response received
t=200ms  Device requests playlist
         (if Anthias update failed, device gets stale name)
```

### Proposed (Consistent)
```
Scenario: Update content title via Web Admin

1. Web Admin PATCH /api/contents/{id}
   └─ Update PostgreSQL: title = "New Title"
      ✓ Immediate
      ✓ URI cached, no Anthias interaction needed

Timeline:
─────────
t=0   Web admin updates PostgreSQL
t=1ms   Update complete
t=500ms Device requests playlist
        ✓ Gets fresh "New Title" from PostgreSQL
        ✓ Uses cached URI (no API call)
        ✓ Consistent, fast, reliable
```

## Migration Path

### Phase 1: Add URI Cache (Backward Compatible)
```sql
ALTER TABLE contents ADD COLUMN anthias_file_uri VARCHAR(500);
```

### Phase 2: Populate Cache
```python
for content in all_contents:
    asset = anthias_service.get_asset(content.anthias_asset_id)
    content.anthias_file_uri = asset['uri']
    db.commit()
```

### Phase 3: Use Cache in Playlist
```python
# OLD: fetch from Anthias
asset = anthias_service.get_asset(content.anthias_asset_id)
uri = asset['uri']

# NEW: use cache
uri = content.anthias_file_uri
```

### Phase 4: Simplify Upload (Optional Future)
```python
# Remove name, duration, is_enabled sync from AnthiasService
```

## Summary Table

| Aspect | Current | Proposed |
|--------|---------|----------|
| **Metadata Fields Sent to Anthias** | 5 | 0 |
| **URI Source** | Anthias API call | PostgreSQL cache |
| **Playlist API Latency** | 250ms+ | ~120ms |
| **Data Consistency** | Eventual | Immediate |
| **Sources of Truth** | 2 (PostgreSQL + Anthias) | 1 (PostgreSQL) |
| **Sync Complexity** | High | Low |
| **Update Propagation** | Network-dependent | Instant |
| **Anthias Dependency** | Critical (metadata) | Minimal (files) |
