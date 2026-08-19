import os
import pytest
from src.narration.piper import PiperVoice
from src.alignment.whisper import WhisperAligner
from src.cache.cache import CacheManager


def test_word_alignment(tmp_path):
    cache_dir = tmp_path / "cache"
    audio_path = str(tmp_path / "narration.wav")
    cm = CacheManager(cache_dir=str(cache_dir))

    voice = PiperVoice(cache_manager=cm)
    aligner = WhisperAligner(cache_manager=cm)

    transcript = "Computers represent color using numbers."
    voice.synthesize(transcript, audio_path)

    alignment = aligner.align(audio_path, transcript)
    assert len(alignment) > 0
    assert alignment[0]["word"].strip().lower() == "computers"
    assert alignment[-1]["end"] > alignment[0]["start"]
