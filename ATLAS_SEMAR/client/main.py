"""
JARVIS main entry point.

Week 1-5: Complete voice assistant implementation
Hotkey (F12) → Audio → STT → Classify → Route → Execute
"""

import sys
from jarvis.components.main_loop import MainLoopOrchestrator


def main():
    """
    Initialize and run JARVIS.

    Week 1-5 complete:
    - HotkeyListener detects F12 hotkey
    - AudioCapture records audio while hotkey held
    - STTAdapter transcribes with Whisper
    - InputBoundary classifies as command or voice
    - CommandExecutor handles help command
    - SafetyGate passes through all input (always ALLOW)
    - PromptShaper passes through text unchanged (no prefix)
    - CLIAdapter sends to Claude directly
    """

    print("=" * 80, file=sys.stdout, flush=True)
    print("🎙️  JARVIS VOICE ASSISTANT - Starting", file=sys.stdout, flush=True)
    print("=" * 80, file=sys.stdout, flush=True)
    print()

    print("[1/2] Initializing components...", file=sys.stdout, flush=True)

    try:
        # Language: "en" (English) or "id" (Indonesian)
        language = "id"  # Indonesian language

        orchestrator = MainLoopOrchestrator(
            hotkey_key="f12",
            sample_rate=44100,  # Use device native rate (Logitech: 44100 Hz)
            vad_timeout_ms=1500,
            duration_ceiling_ms=120000,
            stt_model="large",  # Cloud uses large model (95% accuracy)
            stt_language=language,
            stt_timeout_ms=120000,  # 120 seconds for cloud processing
        )
        print("✅ MainLoopOrchestrator initialized", file=sys.stdout, flush=True)
        print("   ├─ HotkeyListener: ready (F12)", file=sys.stdout, flush=True)
        print("   ├─ AudioCapture: ready (VAD + trimming)", file=sys.stdout, flush=True)
        print("   ├─ CloudSTTAdapter: ready (backend API - Whisper large)", file=sys.stdout, flush=True)
        print("   ├─ InputBoundary: ready (command/voice classification)", file=sys.stdout, flush=True)
        print("   ├─ CommandExecutor: ready (help only)", file=sys.stdout, flush=True)
        print("   ├─ SafetyGate: ready (pass-through)", file=sys.stdout, flush=True)
        print("   ├─ PromptShaper: ready (pass-through)", file=sys.stdout, flush=True)
        print("   └─ CLIAdapter: ready (fire-and-forget)", file=sys.stdout, flush=True)
        print()

        print("[2/2] Starting main loop...", file=sys.stdout, flush=True)
        print()
        print("=" * 80, file=sys.stdout, flush=True)
        print("🎤 WAITING FOR F12 HOTKEY...", file=sys.stdout, flush=True)
        print("=" * 80, file=sys.stdout, flush=True)
        print()
        print("To use JARVIS:", file=sys.stdout, flush=True)
        print("  1. Press and HOLD F12", file=sys.stdout, flush=True)
        print("  2. Speak your command or question", file=sys.stdout, flush=True)
        print("  3. Release F12", file=sys.stdout, flush=True)
        print("  4. See results in terminal", file=sys.stdout, flush=True)
        print()
        print("Example commands:", file=sys.stdout, flush=True)
        print("  - 'help' → Show all commands", file=sys.stdout, flush=True)
        print("  - 'what is Python?' → Send to Claude", file=sys.stdout, flush=True)
        print()
        print("Press Ctrl+C to exit", file=sys.stdout, flush=True)
        print()
        print("=" * 80, file=sys.stdout, flush=True)
        print()

        orchestrator.run()

    except KeyboardInterrupt:
        print()
        print("=" * 80, file=sys.stdout, flush=True)
        print("🛑 JARVIS stopped", file=sys.stdout, flush=True)
        print("=" * 80, file=sys.stdout, flush=True)
        sys.exit(0)

    except Exception as e:
        print()
        print("=" * 80, file=sys.stderr, flush=True)
        print(f"❌ JARVIS ERROR: {e}", file=sys.stderr, flush=True)
        print("=" * 80, file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
