from abc import ABC, abstractmethod
from typing import List, Dict, Any


class VoiceProvider(ABC):
    """Abstract base class for Voice Narration Providers."""

    @abstractmethod
    def synthesize(self, text: str, output_path: str) -> str:
        """Synthesize narration text into audio file at output_path. Returns output audio path."""
        pass


class Aligner(ABC):
    """Abstract base class for Word Alignment Providers."""

    @abstractmethod
    def align(self, audio_path: str, transcript: str) -> List[Dict[str, Any]]:
        """
        Align audio with transcript to produce word-level timestamps.
        Returns list of dicts: [{'word': str, 'start': float, 'end': float}]
        """
        pass
