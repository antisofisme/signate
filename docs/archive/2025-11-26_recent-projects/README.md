# Archived Documentation

This folder contains historical documentation that is no longer actively used but kept for reference.

## Folder Structure

### `dangerous-site/`
Documentation related to the "Dangerous Site" warning issue encountered with portainer.zhmhotels.online subdomain.

**Status**: Issue postponed (decided to use Cloudflare proxy later)

**Files**:
- `DANGEROUS_SITE_STATUS.md` - Status tracking and timeline
- `GOOGLE_SAFE_BROWSING_FIX.md` - Complete troubleshooting guide
- `QUICK_FIX_DANGEROUS_SITE.md` - Quick bypass workaround
- `SUBMIT_GOOGLE_REVIEW.md` - Google Safe Browsing review submission
- `SUBDOMAIN_RENAME_SOLUTION.md` - Attempted fix by renaming subdomain
- `PORTAINER_FIX_SUMMARY.md` - Portainer troubleshooting summary

**Key Finding**: Problem was VPS IP reputation (72.61.209.158), NOT subdomain name.

---

### `fase-2-cleanup/`
Documentation from Phase 2 architecture cleanup and code standardization project.

**Status**: Completed

**Files**:
- `ARCHITECTURE_SCORECARD.md` - Architecture quality metrics
- `CLEANUP_CHECKLIST.md` - Cleanup tasks checklist
- `CLEANUP_REPORT.md` - Cleanup completion report
- `FASE_2_AGENT_6_ARCHITECTURE_CLEANUP_REVIEW.md` - Agent 6 review
- `FASE_2_SUMMARY.md` - Phase 2 summary
- `FASE_3_AGENT_7_FINAL_REPORT.md` - Agent 7 final report
- `READ_ME_FIRST_FASE_2.md` - Phase 2 overview

**Achievements**: Database schema standardization (Grade A+), code cleanup, architecture improvements.

---

### `deployment/`
Documentation from initial production deployment to VPS zhmhotels.online.

**Status**: Completed - All services running in production

**Files**:
- `DEPLOYMENT_VISUAL_SUMMARY.md` - Visual deployment progress
- `FINAL_DEPLOYMENT_PLAN.md` - Comprehensive deployment plan
- `READ_ME_FIRST_DEPLOYMENT.md` - Quick start deployment guide
- `ACCESS_GUIDE.md` - Server access and credentials guide
- `UNIFIED_DOMAIN_ACCESS_PLAN.md` - Domain and subdomain planning
- `URL_MIGRATION_SUMMARY.md` - URL migration from old to new domains

**Production Services**:
- Backend API: https://api.zhmhotels.online/ (port 8001)
- CMS Admin: https://admin.zhmhotels.online/ (port 3000)
- Player/Viewer: https://player.zhmhotels.online/ (port 8080)
- Database: PostgreSQL 15.14 (port 5433)
- PgBouncer: Connection pooling (port 6432)
- Redis: Cache/broker (port 6379)
- ClamAV: Antivirus (port 3310)
- Celery: Background tasks

---

## Current Documentation

For active documentation, see:
- `/CLAUDE.md` - Main project instructions and server info
- `/README.md` - Project overview
- `/docs/` - Active documentation (if any)

---

**Last Updated**: 2025-11-26
**Archived By**: Claude Code
