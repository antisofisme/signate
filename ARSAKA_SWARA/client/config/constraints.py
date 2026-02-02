"""
JARVIS Startup Constraints (Validation Only)

CRITICAL: Constraints are validated at STARTUP ONLY.
NOT during request processing.
NOT in hot paths.

If a constraint is violated at startup, Jarvis CRASHES immediately.
This is NOT a recoverable error. It's a BUG in configuration or deployment.
"""


class AudioConstraints:
    """Audio capture constraints (IMMUTABLE)."""

    SAMPLE_RATE_HZ = 16000
    AUDIO_DURATION_CEILING_MS = 120000
    VAD_SILENCE_TIMEOUT_MS = 1500
    MIN_AUDIO_DURATION_MS = 100


class STTConstraints:
    """STT constraints (IMMUTABLE)."""

    VALID_MODELS = {"tiny", "base", "small"}
    DEFAULT_MODEL = "base"
    LANGUAGE = "en"
    TIMEOUT_MS = 1000
    MIN_CONFIDENCE = 0.5


class CommandConstraints:
    """Command grammar constraints (IMMUTABLE)."""

    VALID_MODES = {"default", "coding", "debug", "explain"}
    DEFAULT_MODE = "default"
    MODE_PREFIXES = {
        "default": "",
        "coding": "[CODING] ",
        "debug": "[DEBUG] ",
        "explain": "[EXPLAIN] ",
    }
    VALID_COMMANDS = {"kirim", "ulang", "mode", "help"}


class SafetyConstraints:
    """Safety gate patterns (IMMUTABLE)."""

    DANGEROUS_PATTERNS = {
        "file_ops": ["rm -rf", "rm -r", "rmdir", "del ", "format "],
        "git_ops": ["git reset", "git rebase", "git force", "git push -f"],
        "db_ops": ["drop table", "delete from", "truncate "],
        "system_ops": ["killall", "shutdown", "reboot"],
    }


class UIConstraints:
    """UI signal constraints (IMMUTABLE)."""

    TOAST_DURATION_MIN_MS = 1000
    TOAST_DURATION_MAX_MS = 5000
    TOAST_DURATION_DEFAULT_MS = 3000
    DIALOG_TIMEOUT_MS = None


def validate_audio_constraints() -> None:
    """Validate audio capture constraints."""
    if AudioConstraints.VAD_SILENCE_TIMEOUT_MS < 500:
        raise ValueError(
            f"VAD timeout {AudioConstraints.VAD_SILENCE_TIMEOUT_MS}ms too short (<500ms). "
            "Will cut off legitimate pauses in speech."
        )

    if AudioConstraints.AUDIO_DURATION_CEILING_MS < 10000:
        raise ValueError(
            f"Audio ceiling {AudioConstraints.AUDIO_DURATION_CEILING_MS}ms too short (<10s). "
            "See JARVIS-DEC-001 for rationale."
        )


def validate_stt_constraints() -> None:
    """Validate STT model constraints."""
    if STTConstraints.DEFAULT_MODEL not in STTConstraints.VALID_MODELS:
        raise ValueError(
            f"STT model '{STTConstraints.DEFAULT_MODEL}' not in valid models: "
            f"{STTConstraints.VALID_MODELS}"
        )


def validate_ui_constraints() -> None:
    """Validate UI timing constraints."""
    if not (
        UIConstraints.TOAST_DURATION_MIN_MS
        <= UIConstraints.TOAST_DURATION_DEFAULT_MS
        <= UIConstraints.TOAST_DURATION_MAX_MS
    ):
        raise ValueError(
            f"Toast duration {UIConstraints.TOAST_DURATION_DEFAULT_MS}ms "
            f"outside valid range [{UIConstraints.TOAST_DURATION_MIN_MS}, "
            f"{UIConstraints.TOAST_DURATION_MAX_MS}]"
        )

    if UIConstraints.DIALOG_TIMEOUT_MS is not None:
        raise ValueError(
            "Dialog timeout MUST be None (user controls timing). "
            "See JARVIS-L3-ARCH-003."
        )


def validate_all_constraints() -> None:
    """
    Validate all constraints at startup.

    MUST be called in main() before starting MainLoop.

    If any constraint fails, Jarvis exits with error.
    This is NOT a recoverable condition.
    """
    errors = []

    try:
        validate_audio_constraints()
    except ValueError as e:
        errors.append(str(e))

    try:
        validate_stt_constraints()
    except ValueError as e:
        errors.append(str(e))

    try:
        validate_ui_constraints()
    except ValueError as e:
        errors.append(str(e))

    if errors:
        error_message = "JARVIS STARTUP CONSTRAINT VIOLATIONS:\n\n"
        error_message += "\n\n".join(errors)
        error_message += "\n\nJarvis cannot start with constraint violations."
        raise ValueError(error_message)
