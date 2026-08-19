"""
src/errors.py — Categorized Error Classes (PRD §25)
All pipeline errors produce human-readable messages, nothing fails silently.
"""


class AutoVideoError(Exception):
    """Base class for all AutoVideo pipeline errors."""
    pass


class ScriptNotFoundError(AutoVideoError):
    def __init__(self, path: str):
        super().__init__(f"ERROR: Script file does not exist: {path}")


class SceneSpecNotFoundError(AutoVideoError):
    def __init__(self, path: str):
        super().__init__(f"ERROR: Scene specification file does not exist: {path}")


class InvalidSceneSpecError(AutoVideoError):
    def __init__(self, detail: str):
        super().__init__(f"ERROR: Invalid scene specification — {detail}")


class UnsupportedVisualTypeError(AutoVideoError):
    def __init__(self, scene_id: str, vtype: str):
        super().__init__(f"ERROR: Scene {scene_id} contains unsupported visual type: '{vtype}'")


class FontNotFoundError(AutoVideoError):
    def __init__(self, font_name: str):
        super().__init__(f"ERROR: Configured font was not found: '{font_name}'")


class TTSFailureError(AutoVideoError):
    def __init__(self, detail: str = ""):
        msg = "ERROR: Voice provider failed to generate narration."
        if detail:
            msg += f" Detail: {detail}"
        super().__init__(msg)


class NumericalEvalWarning(UserWarning):
    """WARNING: Could not safely evaluate a numerical expression."""
    pass


class LLMPlannerError(AutoVideoError):
    def __init__(self, detail: str):
        super().__init__(f"ERROR: LLM scene planner failed to produce a valid specification — {detail}")


class FFmpegError(AutoVideoError):
    def __init__(self, detail: str):
        super().__init__(f"ERROR: FFmpeg video composition failed — {detail}")


class ConfigurationError(AutoVideoError):
    def __init__(self, detail: str):
        super().__init__(f"ERROR: Configuration is invalid — {detail}")
