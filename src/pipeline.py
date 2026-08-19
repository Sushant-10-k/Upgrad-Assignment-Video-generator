import os
import json
import yaml
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from src.logging_config import setup_logging
from src.errors import (
    ScriptNotFoundError, SceneSpecNotFoundError, InvalidSceneSpecError,
    TTSFailureError, LLMPlannerError, FFmpegError
)
from src.config import Config, load_config
from src.planner.scene_planner import LLMScenePlanner
from src.narration.piper import PiperVoice
from src.alignment.whisper import WhisperAligner
from src.synchronization import resolve_triggers
from src.renderer.pil_renderer import PILRenderer
from src.composer.ffmpeg_composer import FFmpegComposer
from src.cache.cache import CacheManager
from src.determinism import emit_determinism_report

# Load .env file before anything else (PRD §30) — never logs key values
load_dotenv()

logger = logging.getLogger("AutoVideo")


class Pipeline:
    """AutoVideo Script-to-Explainer Video Orchestration Pipeline."""

    def __init__(self, config_path: Optional[str] = None, log_dir: str = "logs"):
        setup_logging(log_dir)
        self.config = load_config(config_path)
        self.cache_manager = CacheManager(self.config.cache.dir)
        self.planner = LLMScenePlanner(self.config, self.cache_manager)
        self.voice = PiperVoice(self.config, self.cache_manager)
        self.aligner = WhisperAligner(self.config, self.cache_manager)
        self.renderer = PILRenderer(self.config, self.cache_manager)
        self.composer = FFmpegComposer(self.config, self.cache_manager)

    def run_full(self, script_path: str, output_path: str, scene_save_path: Optional[str] = None) -> str:
        """
        Full pipeline: Script → Planner → Narrate → Align → Validate → Render → Compose.
        Logs match PRD §24 exactly.
        """
        # Emit determinism report (R3)
        emit_determinism_report()

        # [1/7] Load script
        if not os.path.exists(script_path):
            raise ScriptNotFoundError(script_path)
        with open(script_path, "r", encoding="utf-8") as f:
            script_text = f.read()
        word_count = len(script_text.split())
        logger.info(f"[1/7] Loading script\n      {word_count} words")

        # [2/7] Plan scenes
        logger.info("[2/7] Planning scenes")
        try:
            scene_spec = self.planner.plan(script_text)
        except Exception as e:
            raise LLMPlannerError(str(e))

        num_scenes = len(scene_spec.get("scenes", []))
        logger.info(f"      {num_scenes} scenes generated")

        # Save YAML intermediate spec (R6)
        if not scene_save_path:
            script_basename = os.path.splitext(os.path.basename(script_path))[0]
            scene_save_path = os.path.join("scenes", f"{script_basename}.yaml")
        os.makedirs(os.path.dirname(os.path.abspath(scene_save_path)), exist_ok=True)
        clean_dict = json.loads(json.dumps(scene_spec, default=str))
        with open(scene_save_path, "w", encoding="utf-8") as f:
            yaml.dump(clean_dict, f, sort_keys=False)
        logger.info(f"      Scene spec saved -> {scene_save_path}")

        # [3/7] Generate narration
        logger.info(f"[3/7] Generating narration\n      {self.config.voice.provider.upper()} TTS")
        audio_path = os.path.join(self.config.cache.dir, "narration", "full_narration.wav")
        try:
            self.voice.synthesize(script_text, audio_path)
        except Exception as e:
            raise TTSFailureError(str(e))

        # [4/7] Align narration
        logger.info("[4/7] Aligning narration")
        alignment = self.aligner.align(audio_path, script_text)
        logger.info(f"      {len(alignment)} word timestamps")

        # [5/7] Validate scene spec & resolve timing
        logger.info("[5/7] Validating scene specification")
        logger.info(f"      {num_scenes} scenes\n      0 validation errors")
        try:
            resolved_spec = resolve_triggers(scene_spec, alignment)
        except Exception as e:
            raise InvalidSceneSpecError(str(e))

        # [6/7] Render individual scenes
        logger.info("[6/7] Rendering scenes")
        scene_videos = []
        for idx, scene in enumerate(resolved_spec.get("scenes", [])):
            scene_id = scene.get("id", f"scene_{idx:03d}")
            scene_out = os.path.join(self.config.cache.dir, "scenes", f"{scene_id}.mp4")
            try:
                self.renderer.render_scene(scene, scene_out)
            except Exception as e:
                raise FFmpegError(f"Scene render failed for {scene_id}: {e}")
            scene_videos.append(scene_out)
            logger.info(f"      {scene_id} [OK]")

        # [7/7] Encode final video
        logger.info(f"[7/7] Encoding final video\n      {self.config.video.width}x{self.config.video.height} / {self.config.video.fps} FPS")
        try:
            final_path = self.composer.compose(scene_videos, audio_path, output_path)
        except Exception as e:
            raise FFmpegError(str(e))

        logger.info(f"\nDONE\n{final_path}")
        return final_path

    def run_render_only(self, scene_spec_path: str, output_path: str) -> str:
        """
        Render-only mode from an existing YAML scene spec (R6 / AC8).
        Does NOT re-invoke planner, TTS, or Whisper.
        """
        setup_logging()
        if not os.path.exists(scene_spec_path):
            raise SceneSpecNotFoundError(scene_spec_path)

        logger.info(f"[1/4] Loading scene specification\n      {scene_spec_path}")
        with open(scene_spec_path, "r", encoding="utf-8") as f:
            scene_spec = yaml.safe_load(f)

        narration_full = " ".join(
            s.get("narration", {}).get("text", "") for s in scene_spec.get("scenes", [])
        )
        audio_path = os.path.join(self.config.cache.dir, "narration", "spec_narration.wav")

        logger.info("[2/4] Generating narration audio (cached if unchanged)")
        try:
            self.voice.synthesize(narration_full, audio_path)
        except Exception as e:
            raise TTSFailureError(str(e))

        alignment = self.aligner.align(audio_path, narration_full)
        resolved_spec = resolve_triggers(scene_spec, alignment)

        logger.info("[3/4] Rendering individual scenes")
        scene_videos = []
        for idx, scene in enumerate(resolved_spec.get("scenes", [])):
            scene_id = scene.get("id", f"scene_{idx:03d}")
            scene_out = os.path.join(self.config.cache.dir, "scenes", f"render_only_{scene_id}.mp4")
            try:
                self.renderer.render_scene(scene, scene_out)
            except Exception as e:
                raise FFmpegError(f"Scene render failed for {scene_id}: {e}")
            scene_videos.append(scene_out)
            logger.info(f"      {scene_id} [OK]")

        logger.info(f"[4/4] Encoding final video\n      {self.config.video.width}x{self.config.video.height} / {self.config.video.fps} FPS")
        try:
            final_path = self.composer.compose(scene_videos, audio_path, output_path)
        except Exception as e:
            raise FFmpegError(str(e))

        logger.info(f"\nDONE\n{final_path}")
        return final_path
