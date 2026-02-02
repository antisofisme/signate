#!/usr/bin/env python3
"""
Debug JARVIS - untuk lihat step-by-step apa yang terjadi
"""
import sys
import traceback

print("=" * 80, flush=True)
print("🎙️  JARVIS DEBUG - Testing Step by Step", flush=True)
print("=" * 80, flush=True)
print()

# Test 1: Imports
print("[1/5] Testing imports...", flush=True)
try:
    from jarvis.components.main_loop import MainLoopOrchestrator
    from jarvis.components.hotkey_listener import HotkeyListener
    from jarvis.components.audio_capture import AudioCapture
    from jarvis.components.stt_adapter import STTAdapter
    from jarvis.components.input_boundary import InputBoundary
    from jarvis.components.command_executor import CommandExecutor
    from jarvis.components.safety_gate import SafetyGate
    from jarvis.components.prompt_shaper import PromptShaper
    from jarvis.components.cli_adapter import CLIAdapter
    print("✅ All imports successful!", flush=True)
except Exception as e:
    print(f"❌ Import failed: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

print()

# Test 2: Initialize HotkeyListener
print("[2/5] Testing HotkeyListener...", flush=True)
try:
    hotkey = HotkeyListener(hotkey_key="f12")
    print("✅ HotkeyListener created", flush=True)
except Exception as e:
    print(f"❌ HotkeyListener failed: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

print()

# Test 3: Initialize AudioCapture
print("[3/5] Testing AudioCapture...", flush=True)
try:
    audio = AudioCapture()
    print("✅ AudioCapture created", flush=True)
except Exception as e:
    print(f"❌ AudioCapture failed: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

print()

# Test 4: Initialize STTAdapter
print("[4/5] Testing STTAdapter...", flush=True)
try:
    stt = STTAdapter(model="base", timeout_ms=1000, language="en")
    print("✅ STTAdapter created (Whisper loaded)", flush=True)
except Exception as e:
    print(f"❌ STTAdapter failed: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

print()

# Test 5: Initialize MainLoopOrchestrator
print("[5/5] Testing MainLoopOrchestrator...", flush=True)
try:
    print("   Creating orchestrator...", flush=True)
    orchestrator = MainLoopOrchestrator(
        hotkey_key="f12",
        stt_model="base",
        stt_timeout_ms=1000,
        duration_ceiling_ms=120000,
    )
    print("✅ MainLoopOrchestrator created successfully!", flush=True)
except Exception as e:
    print(f"❌ MainLoopOrchestrator failed: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80, flush=True)
print("✅ ALL TESTS PASSED!", flush=True)
print("=" * 80, flush=True)
print()
print("JARVIS is ready to run.", flush=True)
print("Now run: python -m jarvis.main", flush=True)
print()
