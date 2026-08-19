import os
import shutil
import pytest
from src.cache.cache import compute_cache_key, CacheManager


def test_cache_key_stability():
    key1 = compute_cache_key("script_text", "model_v1", 0)
    key2 = compute_cache_key("script_text", "model_v1", 0)
    key3 = compute_cache_key("script_text_mutated", "model_v1", 0)

    assert key1 == key2
    assert key1 != key3


def test_cache_manager_operations(tmp_path):
    cache_dir = tmp_path / "test_cache"
    cm = CacheManager(cache_dir=str(cache_dir))

    key = compute_cache_key("test_content")
    assert not cm.exists("planner", key)

    cm.put("planner", key, "hello planner", extension="json")
    assert cm.exists("planner", key, extension="json")

    content = cm.get("planner", key, extension="json")
    assert content == "hello planner"
