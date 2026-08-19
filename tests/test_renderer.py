import os
import pytest
from src.renderer.pil_renderer import PILRenderer
from src.cache.cache import CacheManager


def test_renderer_output(tmp_path):
    cache_dir = tmp_path / "cache"
    out_16_9 = str(tmp_path / "scene_16_9.mp4")
    out_9_16 = str(tmp_path / "scene_9_16.mp4")

    cm = CacheManager(cache_dir=str(cache_dir))
    renderer = PILRenderer(cache_manager=cm)

    scene_16_9 = {
        "id": "scene_001",
        "duration": 1.0,
        "video": {"width": 854, "height": 480, "fps": 30, "aspect_ratio": "16:9"},
        "visuals": [
            {
                "type": "number",
                "computed_value": "16,777,216",
                "text": "16,777,216",
                "animation": "fade_in"
            }
        ]
    }

    res_16_9 = renderer.render_scene(scene_16_9, out_16_9)
    assert os.path.exists(res_16_9)
    assert os.path.getsize(res_16_9) > 0

    scene_9_16 = {
        "id": "scene_001",
        "duration": 1.0,
        "video": {"width": 480, "height": 854, "fps": 30, "aspect_ratio": "9:16"},
        "visuals": [
            {
                "type": "number",
                "computed_value": "16,777,216",
                "text": "16,777,216",
                "animation": "fade_in"
            }
        ]
    }

    res_9_16 = renderer.render_scene(scene_9_16, out_9_16)
    assert os.path.exists(res_9_16)
    assert os.path.getsize(res_9_16) > 0
