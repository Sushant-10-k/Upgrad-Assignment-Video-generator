import os
import shutil
import tempfile
import subprocess
import logging
import imageio_ffmpeg
from typing import List, Optional
from src.cache.cache import CacheManager, compute_cache_key
from src.config import Config, load_config

logger = logging.getLogger(__name__)


class FFmpegComposer:
    """Video Composition Engine using FFmpeg."""

    def __init__(self, config: Optional[Config] = None, cache_manager: Optional[CacheManager] = None):
        self.config = config or load_config()
        self.cache_manager = cache_manager or CacheManager(self.config.cache.dir)

    def compose(self, scene_video_paths: List[str], narration_audio_path: str, output_path: str) -> str:
        """
        Concatenate scene video clips, mux narration audio, and encode final MP4.
        """
        if not scene_video_paths:
            raise ValueError("ERROR: Cannot compose video without scene video segments.")

        video_cfg = self.config.video
        cache_key = compute_cache_key(
            "".join(scene_video_paths),
            narration_audio_path,
            f"{video_cfg.width}x{video_cfg.height}@{video_cfg.fps}"
        )

        if self.config.cache.enabled and self.cache_manager.exists("scenes", cache_key, extension="final.mp4"):
            logger.info(f"[CACHE HIT] final video ({cache_key[:8]})")
            cached_mp4 = self.cache_manager.get_path("scenes", cache_key, extension="final.mp4")
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(cached_mp4, "rb") as src, open(output_path, "wb") as dst:
                dst.write(src.read())
            return output_path

        logger.info("[7/7] Encoding final video via FFmpeg")

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        temp_dir = tempfile.mkdtemp()
        concat_file = os.path.join(temp_dir, "concat.txt")

        # Write FFmpeg concat list
        with open(concat_file, "w", encoding="utf-8") as f:
            for v_path in scene_video_paths:
                clean_path = os.path.abspath(v_path).replace("\\", "/")
                f.write(f"file '{clean_path}'\n")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Step 1: Concatenate videos
        concat_video_temp = os.path.join(temp_dir, "concat_temp.mp4")
        cmd_concat = [
            ffmpeg_exe, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            concat_video_temp
        ]
        proc1 = subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc1.returncode != 0:
            logger.error(f"FFmpeg concat error: {proc1.stderr.decode('utf-8')}")
            raise RuntimeError(f"FFmpeg video concatenation failed: {proc1.stderr.decode('utf-8')}")

        # Step 2: Mux audio and encode final MP4 (H.264/AAC, §16)
        cmd_mux = [
            ffmpeg_exe, "-y",
            "-i", concat_video_temp,
            "-i", os.path.abspath(narration_audio_path),
            "-c:v", "libx264",
            "-r", str(video_cfg.fps),
            "-c:a", "aac",
            "-shortest",
            "-pix_fmt", "yuv420p",
            output_path
        ]
        proc2 = subprocess.run(cmd_mux, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc2.returncode != 0:
            logger.error(f"FFmpeg mux error: {proc2.stderr.decode('utf-8')}")
            raise RuntimeError(f"FFmpeg audio muxing failed: {proc2.stderr.decode('utf-8')}")

        # Cache result
        if self.config.cache.enabled and os.path.exists(output_path):
            with open(output_path, "rb") as f:
                self.cache_manager.put("scenes", cache_key, f.read(), extension="final.mp4")

        shutil.rmtree(temp_dir, ignore_errors=True)
        return output_path
