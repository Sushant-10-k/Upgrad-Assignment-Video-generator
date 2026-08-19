import pytest
from src.planner.scene_planner import LLMScenePlanner
from src.validation.schema import SceneSpec
from src.cache.cache import CacheManager


def test_planner_generates_valid_spec(tmp_path):
    cache_dir = tmp_path / "cache"
    cm = CacheManager(cache_dir=str(cache_dir))
    planner = LLMScenePlanner(cache_manager=cm)

    script = "Water freezes at 0 degrees Celsius. It boils at 100 degrees Celsius."
    plan_dict = planner.plan(script)

    # Validate output against SceneSpec schema
    spec = SceneSpec(**plan_dict)
    assert len(spec.scenes) >= 1
    assert "Water" in spec.scenes[0].narration.text or "freezes" in spec.scenes[0].narration.text


def test_planner_caching(tmp_path):
    cache_dir = tmp_path / "cache"
    cm = CacheManager(cache_dir=str(cache_dir))
    planner = LLMScenePlanner(cache_manager=cm)

    script = "Sample script for testing cache key stability."
    plan1 = planner.plan(script)
    plan2 = planner.plan(script)

    assert plan1 == plan2
