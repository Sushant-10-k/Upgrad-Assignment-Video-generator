"""
tests/test_pipeline.py — Phase 7 integration test (PRD §27)
Runs the full pipeline end-to-end on scripts/script_a.txt and validates output.
"""
import os
import pytest
from src.pipeline import Pipeline


def test_full_pipeline_script_a(tmp_path):
    """Integration test: script_a.txt → valid MP4 + scene spec YAML."""
    script_path = os.path.join("scripts", "script_a.txt")
    assert os.path.exists(script_path), "scripts/script_a.txt must exist"

    out_mp4 = str(tmp_path / "test_output.mp4")
    out_spec = str(tmp_path / "test_spec.yaml")

    pipeline = Pipeline(log_dir=str(tmp_path / "logs"))
    result_path = pipeline.run_full(script_path, out_mp4, scene_save_path=out_spec)

    assert os.path.exists(result_path), "Output MP4 must exist"
    assert os.path.getsize(result_path) > 0, "Output MP4 must not be empty"
    assert os.path.exists(out_spec), "Scene spec YAML must be saved"


def test_render_only_mode(tmp_path):
    """Integration test: scene YAML → valid MP4 without re-running planner/TTS."""
    script_path = os.path.join("scripts", "script_a.txt")
    assert os.path.exists(script_path)

    spec_path = str(tmp_path / "spec.yaml")
    out_mp4 = str(tmp_path / "output_full.mp4")
    out_rerender = str(tmp_path / "output_rerender.mp4")

    pipeline = Pipeline(log_dir=str(tmp_path / "logs"))
    pipeline.run_full(script_path, out_mp4, scene_save_path=spec_path)

    assert os.path.exists(spec_path)
    pipeline.run_render_only(spec_path, out_rerender)
    assert os.path.exists(out_rerender)
    assert os.path.getsize(out_rerender) > 0
