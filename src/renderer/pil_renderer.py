import os
import math
import tempfile
import subprocess
import logging
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

from src.renderer.base import Renderer
from src.cache.cache import CacheManager, compute_cache_key
from src.config import Config, load_config

logger = logging.getLogger(__name__)


def parse_color(hex_str: str, default: Tuple[int, int, int] = (255, 255, 255)) -> Tuple[int, int, int]:
    """Parse hex color string like #0B1020 into RGB tuple."""
    if not hex_str or not isinstance(hex_str, str):
        return default
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 6:
        try:
            return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))
        except ValueError:
            pass
    return default


def get_default_font(size: int) -> ImageFont.ImageFont:
    """Load default font or fallback font."""
    try:
        return ImageFont.truetype("arial.ttf", size)
    except IOError:
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size)
        except IOError:
            return ImageFont.load_default()


class PILRenderer(Renderer):
    """Deterministic Pillow Frame-by-Frame Scene Renderer."""

    RENDERER_VERSION = "v1.0"

    def __init__(self, config: Optional[Config] = None, cache_manager: Optional[CacheManager] = None):
        self.config = config or load_config()
        self.cache_manager = cache_manager or CacheManager(self.config.cache.dir)

    def render_scene(self, scene_dict: Dict[str, Any], output_path: str) -> str:
        """
        Render a single scene dictionary to a video MP4 file.
        """
        # Determine video & style config from scene_dict or system config
        video_cfg = scene_dict.get("video") or self.config.video.model_dump()
        style_cfg = scene_dict.get("style") or self.config.style.model_dump()

        width = video_cfg.get("width", 854)
        height = video_cfg.get("height", 480)
        fps = video_cfg.get("fps", 30)

        # Cache key calculation (PRD §19 / R8)
        cache_key = compute_cache_key(
            json_str := str(scene_dict),
            str(style_cfg),
            f"{width}x{height}@{fps}",
            self.RENDERER_VERSION
        )

        if self.config.cache.enabled and self.cache_manager.exists("scenes", cache_key, extension="mp4"):
            logger.info(f"[CACHE HIT] scene ({cache_key[:8]})")
            cached_mp4 = self.cache_manager.get_path("scenes", cache_key, extension="mp4")
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(cached_mp4, "rb") as src, open(output_path, "wb") as dst:
                dst.write(src.read())
            return output_path

        duration = max(scene_dict.get("duration", 2.0), 1.0)
        total_frames = max(int(duration * fps), 1)

        bg_color = parse_color(style_cfg.get("background", "#0B1020"))
        primary_color = parse_color(style_cfg.get("primary", "#FFFFFF"))
        accent_color = parse_color(style_cfg.get("accent", "#4CC9F0"))
        secondary_color = parse_color(style_cfg.get("secondary", "#F72585"))

        font_size = style_cfg.get("font_size", 48)
        font = get_default_font(font_size)
        small_font = get_default_font(int(font_size * 0.6))

        temp_dir = tempfile.mkdtemp()
        frame_pattern = os.path.join(temp_dir, "frame_%05d.png")

        # Generate frames
        for frame_idx in range(total_frames):
            frame_time = frame_idx / float(fps)
            progress = frame_idx / float(total_frames)

            img = Image.new("RGB", (width, height), color=bg_color)
            draw = ImageDraw.Draw(img)

            visuals = scene_dict.get("visuals", [])
            num_visuals = max(len(visuals), 1)

            for v_idx, vis in enumerate(visuals):
                v_type = vis.get("type", "text")
                anim = vis.get("animation", "fade_in")
                text_content = str(vis.get("computed_value") or vis.get("text") or vis.get("expression") or "")

                v_start = vis.get("start_time", 0.0)
                v_end = vis.get("end_time", duration)

                # Local animation factor (0.0 to 1.0)
                if frame_time < v_start:
                    alpha = 0.0
                else:
                    anim_dur = 0.4
                    alpha = min(1.0, (frame_time - v_start) / anim_dur)

                if anim == "fade_out" and frame_time > v_end - 0.4:
                    alpha = max(0.0, (v_end - frame_time) / 0.4)

                if alpha <= 0.0:
                    continue

                # Calculate placement center
                center_x = width // 2
                center_y = int(height * (0.35 + 0.3 * (v_idx / float(num_visuals))))

                # Animation offset/scaling
                offset_x, offset_y = 0, 0
                scale_factor = 1.0

                if anim == "slide_left":
                    offset_x = int((1.0 - alpha) * 200)
                elif anim == "slide_right":
                    offset_x = -int((1.0 - alpha) * 200)
                elif anim == "slide_up":
                    offset_y = int((1.0 - alpha) * 150)
                elif anim == "slide_down":
                    offset_y = -int((1.0 - alpha) * 150)
                elif anim in ["scale", "scale_in"]:
                    scale_factor = 0.2 + 0.8 * alpha

                pos_x = center_x + offset_x
                pos_y = center_y + offset_y

                # Render Primitives (§10)
                if v_type in ["text", "number", "equation"]:
                    disp_text = text_content
                    if anim == "counter" and text_content.replace(",", "").isdigit():
                        target_val = int(text_content.replace(",", ""))
                        current_val = int(target_val * alpha)
                        disp_text = f"{current_val:,}"

                    cur_font = get_default_font(int(font_size * scale_factor))
                    bbox = draw.textbbox((0, 0), disp_text, font=cur_font)
                    t_w, t_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

                    color = accent_color if v_type in ["number", "equation"] or anim == "highlight" else primary_color
                    draw.text((pos_x - t_w // 2, pos_y - t_h // 2), disp_text, font=cur_font, fill=color)

                elif v_type == "circle":
                    r = int(60 * scale_factor)
                    draw.ellipse([pos_x - r, pos_y - r, pos_x + r, pos_y + r], outline=accent_color, width=4)

                elif v_type == "rectangle":
                    rw, rh = int(140 * scale_factor), int(80 * scale_factor)
                    draw.rectangle([pos_x - rw // 2, pos_y - rh // 2, pos_x + rw // 2, pos_y + rh // 2], outline=secondary_color, width=4)

                elif v_type == "arrow":
                    draw.line([pos_x - 100, pos_y, pos_x + 100, pos_y], fill=accent_color, width=6)
                    draw.polygon([pos_x + 100, pos_y - 12, pos_x + 120, pos_y, pos_x + 100, pos_y + 12], fill=accent_color)

                elif v_type == "line":
                    draw.line([pos_x - 120, pos_y, pos_x + 120, pos_y], fill=primary_color, width=4)

                elif v_type == "chart":
                    # Draw a bar chart
                    labels = vis.get("labels") or ["R", "G", "B"]
                    vals = vis.get("values") or [255, 128, 64]
                    bar_w = 40
                    chart_h = 100
                    for b_i, val in enumerate(vals):
                        b_x = pos_x - 80 + b_i * 60
                        h_px = int((val / 255.0) * chart_h * alpha)
                        draw.rectangle([b_x, pos_y + 50 - h_px, b_x + bar_w, pos_y + 50], fill=accent_color if b_i == 0 else secondary_color)
                        draw.text((b_x + 10, pos_y + 55), labels[b_i] if b_i < len(labels) else "", font=small_font, fill=primary_color)

                elif v_type in ["icon", "image"]:
                    # Draw icon placeholder graphic
                    r = int(50 * scale_factor)
                    draw.rectangle([pos_x - r, pos_y - r, pos_x + r, pos_y + r], fill=secondary_color)
                    draw.text((pos_x - r + 10, pos_y - 10), vis.get("asset", "ICON").upper(), font=small_font, fill=primary_color)

            # Draw step watermark/footer
            draw.text((20, height - 30), f"Scene {scene_dict.get('id', '')}", font=small_font, fill=(120, 140, 160))

            frame_path = frame_pattern % frame_idx
            img.save(frame_path)

        # Assemble frames into MP4 video using FFmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        cmd = [
            ffmpeg_exe, "-y",
            "-framerate", str(fps),
            "-i", frame_pattern,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            output_path
        ]

        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            logger.error(f"FFmpeg scene render error: {proc.stderr.decode('utf-8')}")
            raise RuntimeError(f"FFmpeg failed to assemble scene video: {proc.stderr.decode('utf-8')}")

        # Save to Cache
        if self.config.cache.enabled and os.path.exists(output_path):
            with open(output_path, "rb") as f:
                self.cache_manager.put("scenes", cache_key, f.read(), extension="mp4")

        # Cleanup temp frames
        shutil = __import__("shutil")
        shutil.rmtree(temp_dir, ignore_errors=True)

        return output_path
