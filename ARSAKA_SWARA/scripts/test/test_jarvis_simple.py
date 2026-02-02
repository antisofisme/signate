#!/usr/bin/env python3
"""
Simple JARVIS test - untuk debug apakah aplikasi berjalan
"""

print("=" * 80)
print("🎙️  JARVIS TEST - Checking if application works")
print("=" * 80)
print()

# Test 1: Import modules
print("TEST 1: Checking imports...")
try:
    from jarvis.components.main_loop import MainLoopOrchestrator
    print("✅ MainLoopOrchestrator imported successfully")
except Exception as e:
    print(f"❌ Failed to import: {e}")
    exit(1)

try:
    from jarvis.components.hotkey_listener import HotkeyListener
    print("✅ HotkeyListener imported successfully")
except Exception as e:
    print(f"❌ Failed to import: {e}")
    exit(1)

try:
    from jarvis.components.audio_capture import AudioCapture
    print("✅ AudioCapture imported successfully")
except Exception as e:
    print(f"❌ Failed to import: {e}")
    exit(1)

print()

# Test 2: Initialize components
print("TEST 2: Initializing components...")
try:
    hotkey = HotkeyListener(hotkey_key="f12")
    print("✅ HotkeyListener initialized")
except Exception as e:
    print(f"❌ HotkeyListener failed: {e}")
    exit(1)

try:
    audio = AudioCapture()
    print("✅ AudioCapture initialized")
except Exception as e:
    print(f"❌ AudioCapture failed: {e}")
    exit(1)

print()

# Test 3: Initialize full orchestrator
print("TEST 3: Initializing MainLoopOrchestrator...")
try:
    orchestrator = MainLoopOrchestrator(
        hotkey_key="f12",
        stt_model="base",
        stt_timeout_ms=1000,
        duration_ceiling_ms=120000,
    )
    print("✅ MainLoopOrchestrator initialized successfully!")
    print()
    print("=" * 80)
    print("🎉 ALL TESTS PASSED - JARVIS is ready!")
    print("=" * 80)
    print()
    print("Now testing hotkey detection...")
    print("PRESS F12 and speak for 2-3 seconds, then release")
    print()

    # Run one iteration
    orchestrator.run()

except Exception as e:
    print(f"❌ MainLoopOrchestrator failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
