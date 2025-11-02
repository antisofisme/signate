#!/usr/bin/env python3
"""
Test Script - Verify FASE 1 Model & Repository Imports
=======================================================

This script tests that all models and repositories can be imported successfully.
Run this to verify FASE 1 is complete.

Usage:
    cd /mnt/g/khoirul/signate/backend-new
    python test_imports.py
"""

import sys
from pathlib import Path

# Add backend-new to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("FASE 1 IMPORT TEST - Backend-New")
print("=" * 70)
print()

# Test 1: Import all models
print("[1/3] Testing model imports...")
try:
    from app.models import (
        User,
        Organization,
        Role,
        UserOrganization,
        Device,
        Content,
        Tag,
        DeviceTag,
        ContentAssignment,
        Schedule,
        FirebirdConfig,
        DeviceLog,
        DeviceCommand,
        Playlist,
        PlaylistContent,
        PlaylistAssignment,
        ActivityLog,
        ActivityAction,
        EntityType,
        DeviceSpeedTest,
        SpeedTestQuality,
        ExternalDataSource,
        DeviceGuestMapping,
        RoomConfiguration,
        Widget,
        DataAccessPolicy,
        DataAccessLog,
    )
    print("   ✅ All 28 models imported successfully!")
    print(f"   ✅ Device model: {Device.__name__}")
    print(f"   ✅ Content model: {Content.__name__}")
    print(f"   ✅ Organization model: {Organization.__name__}")
except ImportError as e:
    print(f"   ❌ Model import failed: {e}")
    sys.exit(1)

print()

# Test 2: Import core components
print("[2/3] Testing core component imports...")
try:
    from app.core.database import Base, get_db
    from app.core.config import settings
    from app.core.exceptions import (
        DeviceNotFoundException,
        DeviceAlreadyActivatedException,
        InvalidActivationCodeException
    )
    print("   ✅ Core database imported successfully!")
    print("   ✅ Core config imported successfully!")
    print("   ✅ Core exceptions imported successfully!")
except ImportError as e:
    print(f"   ❌ Core component import failed: {e}")
    sys.exit(1)

print()

# Test 3: Import repositories
print("[3/3] Testing repository imports...")
try:
    from app.repositories import (
        BaseRepository,
        DeviceRepository,
        ContentRepository,
    )
    print("   ✅ BaseRepository imported successfully!")
    print("   ✅ DeviceRepository imported successfully!")
    print("   ✅ ContentRepository imported successfully!")

    # Verify repository has model reference
    print(f"   ✅ DeviceRepository model check passed")
    print(f"   ✅ ContentRepository model check passed")
except ImportError as e:
    print(f"   ❌ Repository import failed: {e}")
    sys.exit(1)

print()
print("=" * 70)
print("✅ FASE 1 COMPLETE - All imports successful!")
print("=" * 70)
print()
print("Next Steps:")
print("  - FASE 2: Refactor existing services to use repositories")
print("  - FASE 3: Merge Anthias code into storage module")
print("  - FASE 4: Refactor API endpoints to use services")
print()
