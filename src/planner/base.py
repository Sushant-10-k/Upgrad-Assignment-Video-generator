from abc import ABC, abstractmethod
from typing import Dict, Any


class ScenePlanner(ABC):
    """Abstract base class for Script Scene Planners."""

    @abstractmethod
    def plan(self, script_text: str) -> Dict[str, Any]:
        """
        Analyze script_text and produce a valid Scene Specification dictionary conforming to the Pydantic schema.
        """
        pass
