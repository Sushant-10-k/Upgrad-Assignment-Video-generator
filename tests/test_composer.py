import os
import pytest
from src.narration.piper import PiperVoice
from src.renderer.pil_renderer import PILRenderer
from src.composer.ffmpeg_composer import FFmpegComposer
from src.cache.cache import CacheManager


def test_composer_end_to_end(tmp_path):
    cache_dir = tmp_path / "cache"
    cm = CacheManager(cache_dir=str(cache_dir))

    voice = PiperVoice(cache_manager=cm)
    renderer = PILRenderer(cache_manager=cm)
    composer = FFmpegComposer(cache_manager=cm)

    # Generate test narration audio
    audio_path = str(tmp_path / "test_narration.wav")
    voice.synthesize("Testing end to end composition.", audio_path)

    # Render a test scene
    scene = {
        "id": "scene_001",
        "duration": 1.0,
        "video": {"width": 854, "height": 480, "fps": 30, "aspect_ratio": "16:9"},
        "visuals": [{"type": "text", "text": "TEST END TO END", "animation": "fade_in"}]
    }
    scene_video = str(tmp_path / "scene_001.mp4")
    renderer.render_scene(scene, scene_video)

    out_mp4 = str(tmp_path / "final_output.mp4")
    res = composer.compose([scene_video], audio_path, out_mp4)

    assert os.path.exists(res)
    assert os.path.getsize(res) > 0
