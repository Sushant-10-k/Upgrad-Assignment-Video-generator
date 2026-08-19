from abc import ABC, abstractmethod
from typing import Dict, Any


class Renderer(ABC):
    """Abstract base class for Visual Scene Renderers."""

    @abstractmethod
    def render_scene(self, scene_dict: Dict[str, Any], output_path: str) -> str:
        """
        Render a single scene specification dict to a video file at output_path.
        Returns the output video path.
        """
        pass
