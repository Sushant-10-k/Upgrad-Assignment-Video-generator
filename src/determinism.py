"""
src/determinism.py — Determinism Documentation Module (PRD §21 / R3)
Emits a determinism report to logs/ listing deterministic vs non-deterministic
components per the requirement: "every non-deterministic component must be documented."
"""
import os
import logging
from datetime import datetime

logger = logging.getLogger("AutoVideo")

DETERMINISM_REPORT = """
================================================================================
  AUTOVIDEO DETERMINISM REPORT (PRD §21 / R3)
================================================================================

STRICTLY DETERMINISTIC COMPONENTS
  [✓] Numerical Engine (src/numerical/calculator.py)
        — Pure Python AST evaluation; identical inputs → identical outputs.
  [✓] Pydantic Schema Validation (src/validation/schema.py)
        — Structural validation is fully deterministic.
  [✓] Cache Key Computation (src/cache/cache.py)
        — SHA-256 content-addressed keys; stable across runs.
  [✓] PIL Renderer (src/renderer/pil_renderer.py)
        — Pillow draw operations are deterministic; no random seeds.
  [✓] Synchronization Engine (src/synchronization.py)
        — Word timestamp mapping is deterministic given same alignment input.
  [✓] FFmpeg Composition (src/composer/ffmpeg_composer.py)
        — Pinned flags (-c:v libx264, -r {fps}, -c:a aac, -pix_fmt yuv420p).
  [✓] Configuration Loader (src/config.py)
        — YAML-driven; same config.yaml → same Config object.

ENVIRONMENT-DEPENDENT / NON-DETERMINISTIC COMPONENTS
  [~] LLM Scene Planner (src/planner/scene_planner.py)
        — temperature=0 + pinned model maximises reproducibility but LLM API
          responses can vary with model updates. Mitigation: planner output is
          SHA-256 cached on first run; subsequent runs use cache (deterministic).
  [~] Piper TTS (src/narration/piper.py)
        — Local TTS engine output may differ across model versions or OS.
          Mitigation: narration audio is SHA-256 cached after first synthesis.
  [~] faster-whisper Alignment (src/alignment/whisper.py)
        — Whisper timestamp precision is structurally stable but not bit-identical
          across hardware/OS/model versions.
          Mitigation: alignment JSON is SHA-256 cached after first run.
          Test strategy: structural equivalence (monotonic, word count match)
          rather than byte-identical assertion.

DETERMINISM CLAIM SCOPE
  For strictly deterministic stages: byte/hash-identical outputs guaranteed.
  For non-deterministic stages: structural equivalence guaranteed on re-runs
  (via caching). First-run outputs may differ across environments.
================================================================================
"""


def emit_determinism_report(log_dir: str = "logs") -> str:
    """Write determinism report to logs/ and return the report string."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(log_dir, f"determinism_report_{timestamp}.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(DETERMINISM_REPORT)
    logger.info(DETERMINISM_REPORT)
    return report_path
