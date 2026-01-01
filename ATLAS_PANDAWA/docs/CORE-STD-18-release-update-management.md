# STD-18: Release & Update Management Standard

This standard establishes **unified discipline** for versioning and distribution across all non-web modules and applications in ATLAS_PANDAWA. The principles ensure that:
- Application builds and updates are **deterministic and auditable**
- Version information is **single source of truth**
- Deployment is **fully automated** with zero manual steps
- Client applications, websites, and documentation are **always synchronized**

---

## Core Principles (Locked)

1. **Single Build Pipeline**
   One build process produces all distribution artifacts (binaries, containers, packages).

2. **Single Source of Truth (Manifest)**
   Application version is determined exclusively by a single release manifest file, never by filesystem metadata or manual versioning.

3. **Immutable Artifacts**
   Artifacts created during build are never modified, patched, or overwritten after creation.

4. **Zero Manual Deployment**
   No manual uploads, file replacements, or production modifications. All deployment is automated via CI/CD pipeline.

---

## Global Architecture

```
BUILD PIPELINE
  ↓
ARTIFACT STORAGE (versioned, immutable)
  ↓
RELEASE MANIFEST (release.json)
  ↓
─────────────────────────────────────
↓              ↓              ↓
AUTO-UPDATER   WEBSITE        DOCS
(Device)       (Download)     (Versioned)
```

---

## System Components

### 1. Artifact Storage

Stores all distribution binaries with version embedded in filename.

**Example (Digital Signage Player):**
```
/release/
  player-win-1.4.3.exe          (Windows binary)
  player-linux-1.4.3.AppImage   (Linux binary)
  player-android-1.4.3.apk      (Android binary)
```

**Example (Future Module - PMS Service):**
```
/release/
  pms-service-linux-2.1.0.tar.gz       (Linux container)
  pms-service-docker-2.1.0.tar         (Docker image)
  pms-installer-win-2.1.0.msi          (Windows installer)
```

---

### 2. Release Manifest (Source of Truth)

Single `release.json` file determining all version information.

**Example format:**
```json
{
  "version": "1.4.3",
  "channel": "stable",
  "published_at": "2025-12-21T02:10:00Z",
  "mandatory": false,
  "artifacts": {
    "windows": {
      "url": "/release/player-win-1.4.3.exe",
      "sha256": "abc123def456",
      "size_bytes": 45215232
    },
    "linux": {
      "url": "/release/player-linux-1.4.3.AppImage",
      "sha256": "ghi789jkl012",
      "size_bytes": 78942156
    },
    "android": {
      "url": "/release/player-android-1.4.3.apk",
      "sha256": "mno345pqr678",
      "size_bytes": 34567890
    }
  },
  "changelog": "Bugfix playback issues, improve stability",
  "min_version": "1.0.0"
}
```

**Rules:**
- Manifest is **the only authoritative version reference**
- All systems (auto-updater, website, documentation) read from manifest
- Manifest is published to immutable, distributed location (CDN or static storage)
- Each release version gets its own manifest (never modified after publish)

---

## Auto-Updater Pattern (Device/Desktop/Mobile)

Applies to: Player, future desktop modules, mobile apps, native helpers.

### Principles
- Application **never updates itself** (security/stability)
- Dedicated updater process handles installation and atomic swap
- Updates are **pull-based**, not pushed

### Update Lifecycle
1. Updater polls `release.json` periodically (e.g., every 6 hours)
2. Compare remote version with local version
3. If newer: download artifact from URL in manifest
4. Verify artifact integrity using checksum from manifest
5. Wait for safe point (app idle, user idle, or scheduled window)
6. Stop/terminate running application
7. Atomic swap: rename old binary, move new binary into place
8. Start application with new binary
9. Log update event with version, timestamp, checksum verification result

### Guarantees
- Update is **atomic** - either complete success or complete rollback
- Downtime target: **< 500ms**
- Failed update: application continues running previous version
- No partial updates or corrupted binaries possible

### Error Handling
- Network failure: retry with exponential backoff
- Checksum mismatch: delete downloaded file, retry later
- Insufficient disk space: defer update, alert administrator
- Update failure: keep previous version running, log incident

---

## Website Download Integration

Applies to: Any public download page, app store listings, documentation sites.

### Principles
- Website **never embeds version numbers** in code
- Website **never hosts binary files** (no duplicate storage)
- Website is **read-only consumer** of manifest

### Mechanism
1. Website build-time or runtime fetches `release.json`
2. Extract current version and artifact URLs
3. Render download interface with latest version

**Example:**
```typescript
async function getLatestRelease() {
  const manifest = await fetch('/api/release.json');
  const data = await manifest.json();

  return {
    version: data.version,
    windows: {
      url: data.artifacts.windows.url,
      label: `Download Player ${data.version} (Windows)`
    },
    linux: {
      url: data.artifacts.linux.url,
      label: `Download Player ${data.version} (Linux)`
    }
  };
}
```

### Result
- Manual downloads = **same version as auto-updater**
- No version skew or inconsistency
- Website automatically reflects new releases without code change

---

## Documentation Versioning

Documentation **must be versioned** alongside releases.

### Structure
```
/docs/
  /latest/          (symlink or redirect to current version)
    installation.md
    troubleshooting.md
    changelog.md
  /v1.4.3/
    installation.md
    troubleshooting.md
    changelog.md
  /v1.4.2/
    installation.md
    troubleshooting.md
    changelog.md
```

### Rules
- Each release includes updated documentation snapshot
- Default documentation URL (e.g., `/docs/latest/`) = **current version docs**
- Previous version documentation remains accessible (e.g., `/docs/v1.4.2/`)
- Changelog includes upgrade instructions for version jumps

---

## Release Pipeline (End-to-End)

**Steps (all automated, zero manual intervention):**

1. Developer merges code to release branch (e.g., `release/v1.4.3`)
2. CI/CD pipeline triggered automatically
3. Build all platform-specific artifacts (Windows, Linux, Android, etc.)
4. Run full test suite
5. Sign artifacts (code signing certificate)
6. Upload artifacts to immutable storage
7. Generate `release.json` with artifact URLs and checksums
8. Publish manifest to CDN/static location
9. Generate/update versioned documentation
10. Update website to reflect new release
11. Post release notification (optional: Slack, email)

**No manual steps.** Pipeline succeeds or fails atomically.

---

## Version Numbering

Use **semantic versioning** (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes, new architecture
- **MINOR**: New features, backward-compatible
- **PATCH**: Bug fixes, no new functionality

Example progression: `1.0.0` → `1.1.0` → `1.1.1` → `2.0.0`

---

## Release Channels

Support multiple stability channels if needed:

```json
{
  "channels": {
    "stable": { "version": "1.4.3" },
    "beta": { "version": "1.5.0-beta.1" },
    "dev": { "version": "1.5.0-dev.42" }
  }
}
```

**Rules:**
- Default channel: `stable`
- Beta/dev channels for early testing
- Each channel has own manifest entry
- Updater respects channel preference from user settings

---

## Manifest Location & Availability

**Critical:** Manifest must be highly available and uncacheable by mistake.

```
Production:  https://api.example.com/api/release.json
(or CDN)     https://cdn.example.com/release.json

Headers:
  Cache-Control: no-cache, no-store, must-revalidate
  ETag: [content-hash]
```

**Redundancy:**
- Multiple CDN endpoints
- Geographic distribution
- Health checks and failover
- Monitoring for manifest delivery latency

---

## Mandatory vs. Optional Updates

Flag in manifest indicates update urgency:

```json
{
  "version": "1.4.3",
  "mandatory": false,
  "min_version": "1.0.0"
}
```

- **`mandatory: true`** → Older versions stop working, force immediate update
- **`mandatory: false`** → Optional, users can defer
- **`min_version`** → Versions older than this are unsupported
- If installed version < `min_version`, **must update** regardless of `mandatory` flag

---

## Rollback Strategy

If critical bug discovered post-release:

1. Fix the bug
2. Build new version (e.g., `1.4.4`)
3. Publish new `release.json` pointing to fixed version
4. Auto-updaters pull new manifest and update to fixed version
5. If very urgent: set `mandatory: true` to force all clients

**Old version binaries remain in storage** (immutability) but manifest no longer references them.

---

## Monitoring & Observability

Each module must track:
- Version distribution across deployed instances
- Update success/failure rates
- Time-to-update (how long until majority reach new version)
- Failed update diagnostics (network? disk space? permissions?)

**Example metrics:**
```
player_active_version{version="1.4.2"}    = 342 instances
player_active_version{version="1.4.3"}    = 1285 instances
player_update_failures_total{reason="checksum_mismatch"} = 3
```

---

## Scope & Applicability

This standard applies to:
- ✅ Desktop applications (Player, native helpers)
- ✅ Mobile applications
- ✅ Service containers with versioning requirements
- ✅ Browser extensions with auto-update

This standard does **NOT** apply to:
- ❌ Web applications (use continuous deployment/blue-green instead)
- ❌ Internal tools with manual rollout
- ❌ Development builds

---

## Exceptions & Deviations

Any deviation from this standard requires **architecture review and explicit documentation**. Common exceptions:

- **Air-gapped environments**: May require manual download + manifest verification
- **Corporate proxies**: May require manifest mirror/caching with TTL
- **Offline-first apps**: May bundle initial manifest, with periodic sync

Document exception in module's `SERVICE_CONTRACT.md`.

---

## Compliance Checklist

For any module implementing auto-update:

- [ ] Single build pipeline produces all artifacts
- [ ] `release.json` is single version source of truth
- [ ] Artifacts stored immutably with version in filename
- [ ] Checksums (SHA256) included in manifest
- [ ] Auto-updater polls manifest and verifies checksums
- [ ] Atomic binary swap with < 500ms downtime
- [ ] Website/docs read from manifest (no hardcoded versions)
- [ ] Documentation versioned alongside releases
- [ ] CI/CD fully automates pipeline (zero manual uploads)
- [ ] Rollback mechanism tested and documented
- [ ] Monitoring/metrics for version distribution
- [ ] Manifest available on multiple CDNs/endpoints

---

## References

- **ARCH-04**: Digital Signage Module Architecture (Player implementation example)
- **STD-03**: Registries & Events (manifest storage patterns)
- **STD-12**: Configuration Governance (environment-specific manifest URLs)
