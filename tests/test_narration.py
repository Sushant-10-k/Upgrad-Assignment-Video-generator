import os
import pytest
from src.narration.piper import PiperVoice
from src.cache.cache import CacheManager


def test_narration_synthesis(tmp_path):
    cache_dir = tmp_path / "cache"
    out_file = str(tmp_path / "test_audio.wav")
    cm = CacheManager(cache_dir=str(cache_dir))
    voice = PiperVoice(cache_manager=cm)

    res_path = voice.synthesize("Hello test narration script.", out_file)
    assert os.path.exists(res_path)
    assert os.path.getsize(res_path) > 0


def test_narration_cache(tmp_path):
    cache_dir = tmp_path / "cache"
    out_file1 = str(tmp_path / "audio1.wav")
    out_file2 = str(tmp_path / "audio2.wav")
    cm = CacheManager(cache_dir=str(cache_dir))
    voice = PiperVoice(cache_manager=cm)

    text = "Caching narration synthesis test."
    voice.synthesize(text, out_file1)
    voice.synthesize(text, out_file2)

    assert os.path.exists(out_file1)
    assert os.path.exists(out_file2)
