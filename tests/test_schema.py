import pytest
import yaml
from pydantic import ValidationError
from src.validation.schema import SceneSpec, PrimitiveType


def test_schema_valid_yaml():
    yaml_content = """
    video:
      width: 854
      height: 480
      fps: 30
    scenes:
      - id: scene_001
        narration:
          text: "Test narration"
        visuals:
          - type: text
            text: "Hello World"
    """
    data = yaml.safe_load(yaml_content)
    spec = SceneSpec(**data)
    assert spec.scenes[0].id == "scene_001"
    assert spec.scenes[0].visuals[0].type == PrimitiveType.TEXT


def test_schema_invalid_visual_type():
    invalid_data = {
        "scenes": [
            {
                "id": "scene_001",
                "narration": {"text": "Test"},
                "visuals": [{"type": "unsupported_visual_type"}]
            }
        ]
    }
    with pytest.raises(ValidationError) as excinfo:
        SceneSpec(**invalid_data)
    assert "unsupported_visual_type" in str(excinfo.value) or "Input should be" in str(excinfo.value)


def test_schema_empty_scenes():
    invalid_data = {"scenes": []}
    with pytest.raises(ValidationError):
        SceneSpec(**invalid_data)
