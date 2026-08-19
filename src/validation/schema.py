from enum import Enum
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator


class PrimitiveType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    LINE = "line"
    ARROW = "arrow"
    ICON = "icon"
    IMAGE = "image"
    EQUATION = "equation"
    CHART = "chart"


class AnimationType(str, Enum):
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    SCALE = "scale"
    SCALE_IN = "scale_in"
    HIGHLIGHT = "highlight"
    DRAW = "draw"
    COUNTER = "counter"
    NONE = "none"


class TransitionType(str, Enum):
    CUT = "cut"
    FADE = "fade"
    CROSSFADE = "crossfade"
    SLIDE = "slide"


class Trigger(BaseModel):
    word: Optional[str] = None
    at_second: Optional[float] = None


class VisualPrimitive(BaseModel):
    type: PrimitiveType
    text: Optional[str] = None
    expression: Optional[str] = None
    value_expression: Optional[str] = None
    computed_value: Optional[Union[int, float, str]] = None
    asset: Optional[str] = None
    color: Optional[str] = None
    size: Optional[int] = None
    x: Optional[Union[int, float]] = None
    y: Optional[Union[int, float]] = None
    width: Optional[Union[int, float]] = None
    height: Optional[Union[int, float]] = None
    radius: Optional[Union[int, float]] = None
    animation: Optional[AnimationType] = AnimationType.FADE_IN
    trigger: Optional[Trigger] = None
    labels: Optional[List[str]] = None
    values: Optional[List[Union[int, float]]] = None


class NarrationSpec(BaseModel):
    text: str


class TransitionSpec(BaseModel):
    type: TransitionType = TransitionType.CUT
    duration: float = 0.5


class Scene(BaseModel):
    id: str
    narration: NarrationSpec
    visuals: List[VisualPrimitive] = Field(default_factory=list)
    transition: Optional[TransitionSpec] = Field(default_factory=TransitionSpec)
    duration: Optional[float] = None


class VideoSpec(BaseModel):
    width: int = 854
    height: int = 480
    fps: int = 30
    aspect_ratio: str = "16:9"


class StyleSpec(BaseModel):
    background: str = "#0B1020"
    primary: str = "#FFFFFF"
    accent: str = "#4CC9F0"
    secondary: str = "#F72585"
    font: str = "arial.ttf"
    font_size: int = 48


class SceneSpec(BaseModel):
    video: Optional[VideoSpec] = Field(default_factory=VideoSpec)
    style: Optional[StyleSpec] = Field(default_factory=StyleSpec)
    scenes: List[Scene]

    @field_validator("scenes")
    @classmethod
    def check_scenes_not_empty(cls, v):
        if not v:
            raise ValueError("Scene specification must contain at least one scene.")
        return v
