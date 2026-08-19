import os
import yaml
from typing import Optional
from pydantic import BaseModel, Field


class VideoConfig(BaseModel):
    width: int = 854
    height: int = 480
    fps: int = 30
    aspect_ratio: str = "16:9"

    def apply_aspect_ratio(self):
        """Ensure width and height match aspect ratio if set to standard presets."""
        if self.aspect_ratio == "9:16":
            self.width, self.height = 480, 854
        elif self.aspect_ratio == "16:9":
            self.width, self.height = 854, 480


class StyleConfig(BaseModel):
    background: str = "#0B1020"
    primary: str = "#FFFFFF"
    accent: str = "#4CC9F0"
    secondary: str = "#F72585"
    font: str = "arial.ttf"
    font_size: int = 48


class VoiceConfig(BaseModel):
    provider: str = "piper"
    model: str = "en_US-lessac-medium"


class RendererConfig(BaseModel):
    provider: str = "pil"


class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.0


class CacheConfig(BaseModel):
    enabled: bool = True
    dir: str = "cache"


class Config(BaseModel):
    video: VideoConfig = Field(default_factory=VideoConfig)
    style: StyleConfig = Field(default_factory=StyleConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    renderer: RendererConfig = Field(default_factory=RendererConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from YAML file or return default Config."""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")

    config_path = os.path.abspath(config_path)

    if not os.path.exists(config_path):
        cfg = Config()
        cfg.video.apply_aspect_ratio()
        return cfg

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    cfg = Config(**data)
    cfg.video.apply_aspect_ratio()
    return cfg
