"""
JARVIS main entry point.

Week 1: HotkeyListener + AudioCapture + MainLoop skeleton
"""

from jarvis.components.main_loop import MainLoopOrchestrator


def main():
    """
    Initialize and run JARVIS.

    Current scope (Week 1):
    - HotkeyListener detects hotkey press
    - AudioCapture blocks until hotkey release or VAD timeout
    - MainLoop orchestrates both
    - SessionState holds audio and error state

    Future scope (Week 2+):
    - STT transcription
    - Input classification
    - Command execution
    - Safety gating
    - Prompt shaping
    - CLI interaction
    """
    orchestrator = MainLoopOrchestrator(
        hotkey_key="f12",
        sample_rate=16000,
        vad_timeout_ms=1500,
        duration_ceiling_ms=120000,
    )

    orchestrator.run()


if __name__ == "__main__":
    main()
