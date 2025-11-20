# Archive Index - January 20, 2025

## Overview
File-file dokumentasi dan testing yang sudah tidak aktif digunakan telah diarsipkan untuk menjaga kebersihan repository.

## Archive Summary
**Total files archived**: 164 files

## Archive Structure

### 1. Root Documentation (86 files)
**Location**: `docs/archive/2025-01-20_root-documentation/`

File-file dokumentasi yang sebelumnya ada di root directory `/mnt/g/khoirul/signate/`:
- Analysis reports (*.md, *.txt)
- Test reports dan logs
- Deployment documentation
- Architecture documentation
- API documentation

**Excluded from archive**:
- README.md (kept in root)
- CLAUDE.md (kept in root - project instructions)
- package.json (kept in root - npm config)
- package-lock.json (kept in root - npm dependencies)

### 2. Player-Vite Documentation (17 files)
**Location**: `docs/archive/2025-01-20_player-vite-docs/`

File-file dokumentasi dari `player-vite/`:
- ADVANCED_FEATURES_DOCUMENTATION.md
- CLEANUP_COMPLETION_REPORT.md
- DECISION_SUMMARY.md
- HLS_IMPLEMENTATION_PROGRESS.md
- OPTIMIZATION_ROADMAP.md
- PERFORMANCE_ANALYSIS_*.md
- TESTING_*.md
- dll.

**Excluded from archive**:
- README.md (tidak ada di player-vite)

### 3. Testing Tools & Scripts (61 files)
**Location**: `docs/archive/2025-01-20_testing-tools/`

File-file testing configuration, test scripts, dan test directory:

**Test Configurations:**
- playwright.config.ts
- vitest.config.ts
- vitest.integration.config.ts

**Python Test Scripts:**
- analyze_naming_conventions.py
- content_api_tests.py
- deep_backend_test.py
- device_api_tests.py
- integration_tests.py
- integration_tests_v2.py
- phase3_audit_multitenancy_test.py
- dll.

**JavaScript Test Scripts:**
- playwright-mcp-test.js
- playwright-test-click.js
- playwright-test-v2.js
- test-all-popups-consistency.js
- test-check-logs-simple.js
- test-check-visibility.js
- test-clear-cache-close-button.js
- test-click-domready.js
- test-connection-log-api.js
- dll. (40+ test scripts)

**Test Reports & Results:**
- BACKEND_TEST_REPORT.json
- integration_test_coordinator.json
- phase3_test_results.json
- retest_fixed_services.json
- service-mapping.json

**Test HTML Files:**
- test-manual-browser.html

**Shell Scripts:**
- quick_org_test.sh

**Test Directory:**
- tests/ (entire directory with e2e, unit, helpers, etc.)

**Note**: File-file ini masih bisa digunakan kembali jika diperlukan, tinggal copy kembali ke folder asalnya.

## Clean State After Archive

**Root directory** (`/mnt/g/khoirul/signate/`):
- CLAUDE.md (project instructions)
- README.md (project readme)
- package.json (npm config)
- package-lock.json (npm dependencies)
- All project folders (backend-python, player-vite, cms-vite, dll.)

**Player-vite directory** (`/mnt/g/khoirul/signate/player-vite/`):
- 0 dokumentasi files (clean)
- 0 test files (clean)
- Hanya source code dan config yang essential

## Why Archived?

1. **Cleanup**: Mengurangi clutter di root directory dan player-vite
2. **History Preservation**: File tetap tersimpan untuk referensi di masa depan
3. **Organization**: Dokumentasi terorganisir berdasarkan tanggal dan kategori
4. **Performance**: Mengurangi jumlah file yang perlu di-scan oleh tools
5. **Development Focus**: Hanya file essential yang tersisa untuk development

## How to Restore

Jika diperlukan kembali:

```bash
# Restore specific documentation
cp docs/archive/2025-01-20_root-documentation/FILENAME.md .

# Restore player-vite docs
cp docs/archive/2025-01-20_player-vite-docs/FILENAME.md player-vite/

# Restore testing tools
cp docs/archive/2025-01-20_testing-tools/playwright.config.ts player-vite/
cp -r docs/archive/2025-01-20_testing-tools/tests player-vite/

# Restore specific test script
cp docs/archive/2025-01-20_testing-tools/test-*.js .
cp docs/archive/2025-01-20_testing-tools/*_tests.py .
```

## Archive Statistics

| Category | Files Count | Location |
|----------|-------------|----------|
| Root Documentation | 86 | docs/archive/2025-01-20_root-documentation/ |
| Player-Vite Docs | 17 | docs/archive/2025-01-20_player-vite-docs/ |
| Testing Tools | 61 | docs/archive/2025-01-20_testing-tools/ |
| **Total** | **164** | **3 archive directories** |

## Archive Date
**Created**: January 20, 2025  
**By**: Automated cleanup process  
**Reason**: Repository cleanup and organization

---

**Important Note**: File-file ini TIDAK dihapus, hanya dipindahkan ke folder archive untuk referensi. Semua file masih dapat diakses dan di-restore kapan saja jika diperlukan.
