import pytest
from src.synchronization import resolve_triggers


def test_resolve_triggers():
    scene_spec = {
        "scenes": [
            {
                "id": "scene_001",
                "narration": {"text": "Computers represent color using 2^8 values."},
                "visuals": [
                    {
                        "type": "number",
                        "value_expression": "2^8",
                        "trigger": {"word": "values"}
                    }
                ]
            }
        ]
    }

    alignment = [
        {"word": "Computers", "start": 0.1, "end": 0.5},
        {"word": "represent", "start": 0.5, "end": 0.9},
        {"word": "color", "start": 0.9, "end": 1.3},
        {"word": "using", "start": 1.3, "end": 1.6},
        {"word": "2^8", "start": 1.6, "end": 2.0},
        {"word": "values.", "start": 2.0, "end": 2.5}
    ]

    resolved = resolve_triggers(scene_spec, alignment)
    scene = resolved["scenes"][0]
    visual = scene["visuals"][0]

    assert visual["computed_value"] == "256"
    assert visual["text"] == "256"
    assert abs(visual["start_time"] - 2.0) <= 0.15  # within ±150 ms tolerance
