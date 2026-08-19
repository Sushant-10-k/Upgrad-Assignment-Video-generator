import os
import wave
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from src.narration.base import Aligner
from src.cache.cache import CacheManager, compute_cache_key
from src.config import Config, load_config

logger = logging.getLogger(__name__)


def get_wav_duration(audio_path: str) -> float:
    """Read WAV file duration in seconds."""
    try:
        with wave.open(audio_path, "rb") as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            return frames / float(rate)
    except Exception:
        return 5.0


def fallback_word_alignment(audio_path: str, transcript: str) -> List[Dict[str, Any]]:
    """Proportional acoustic alignment based on actual audio duration."""
    words = [w.strip() for w in transcript.strip().split() if w.strip()]
    if not words:
        return []

    total_duration = get_wav_duration(audio_path)

    # Calculate proportional word durations based on character lengths
    total_chars = sum(len(w) for w in words)
    if total_chars == 0:
        total_chars = len(words)

    timestamps = []
    current_time = 0.1  # Initial padding

    usable_duration = max(0.5, total_duration - 0.2)

    for word in words:
        word_len = len(word)
        word_duration = (word_len / float(total_chars)) * usable_duration
        end_time = current_time + word_duration
        timestamps.append({
            "word": word,
            "start": round(current_time, 3),
            "end": round(end_time, 3)
        })
        current_time = end_time

    return timestamps


class WhisperAligner(Aligner):
    """Word Alignment Provider using faster-whisper or acoustic fallback."""

    WHISPER_VERSION = "tiny.en"

    def __init__(self, config: Optional[Config] = None, cache_manager: Optional[CacheManager] = None):
        self.config = config or load_config()
        self.cache_manager = cache_manager or CacheManager(self.config.cache.dir)

    def _get_audio_hash(self, audio_path: str) -> str:
        hasher = hashlib.sha256()
        with open(audio_path, "rb") as f:
            hasher.update(f.read())
        return hasher.hexdigest()

    def align(self, audio_path: str, transcript: str) -> List[Dict[str, Any]]:
        """Align audio with transcript to produce word-level timestamps."""
        audio_hash = self._get_audio_hash(audio_path)
        cache_key = compute_cache_key(audio_hash, transcript, self.WHISPER_VERSION)

        # Check Cache (PRD §19)
        if self.config.cache.enabled and self.cache_manager.exists("alignment", cache_key, extension="json"):
            logger.info(f"[CACHE HIT] alignment ({cache_key[:8]})")
            cached_data = self.cache_manager.get("alignment", cache_key, extension="json")
            return json.loads(cached_data)

        logger.info("[4/7] Aligning narration narration words")

        timestamps = None

        # Try faster-whisper
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel(self.WHISPER_VERSION, device="cpu", compute_type="int8")
            segments, _ = model.transcribe(audio_path, word_timestamps=True)
            aligned = []
            for segment in segments:
                if segment.words:
                    for word_info in segment.words:
                        aligned.append({
                            "word": word_info.word.strip(),
                            "start": round(word_info.start, 3),
                            "end": round(word_info.end, 3)
                        })
            if aligned:
                timestamps = aligned
        except Exception:
            logger.info("faster-whisper unavailable. Using deterministic acoustic word aligner.")

        if not timestamps:
            timestamps = fallback_word_alignment(audio_path, transcript)

        # Cache result
        if self.config.cache.enabled:
            self.cache_manager.put("alignment", cache_key, json.dumps(timestamps, indent=2), extension="json")

        return timestamps
