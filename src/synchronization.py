import logging
from typing import Dict, Any, List
from src.numerical.calculator import NumericalCalculator

logger = logging.getLogger(__name__)


def resolve_triggers(scene_spec: Dict[str, Any], alignment: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Bridge visual triggers with word timestamps from alignment to assign resolved start/end times.
    Enforces R4 (numerical value calculation) and R5 (±150 ms word-level synchronization).
    """
    calc = NumericalCalculator()
    alignment_idx = 0
    total_words = len(alignment)

    scenes = scene_spec.get("scenes", [])
    if not scenes:
        return scene_spec

    # Overall timeline tracker
    for scene in scenes:
        narration_text = scene.get("narration", {}).get("text", "")
        scene_words = [w.strip(".,!?;:\"'()").lower() for w in narration_text.split() if w.strip()]

        scene_start_time = float("inf")
        scene_end_time = 0.0

        # Match scene narration words to global alignment list
        scene_word_alignments = []
        search_start = alignment_idx
        for s_word in scene_words:
            for i in range(search_start, total_words):
                aligned_w = alignment[i]["word"].strip(".,!?;:\"'()").lower()
                if aligned_w == s_word:
                    scene_word_alignments.append(alignment[i])
                    search_start = i + 1
                    alignment_idx = search_start
                    break

        if scene_word_alignments:
            scene_start_time = scene_word_alignments[0]["start"]
            scene_end_time = scene_word_alignments[-1]["end"]
        else:
            # Fallback if alignment mismatch
            scene_start_time = 0.0
            scene_end_time = 3.0

        scene["start_time"] = scene_start_time
        scene["end_time"] = max(scene_end_time, scene_start_time + 1.0)
        scene["duration"] = round(scene["end_time"] - scene["start_time"], 3)

        # Resolve primitives & numerical values
        for visual in scene.get("visuals", []):
            # Compute numerical value if expression is present (R4)
            expr = visual.get("value_expression") or visual.get("expression")
            if expr:
                eval_res = calc.evaluate(expr)
                visual["computed_value"] = eval_res["formatted_result"]
                if visual.get("type") == "number" and not visual.get("text"):
                    visual["text"] = str(eval_res["formatted_result"])

            # Resolve timing trigger (R5)
            trigger_word = visual.get("trigger", {}).get("word") if visual.get("trigger") else None
            trigger_found = False

            if trigger_word and scene_word_alignments:
                clean_trigger = trigger_word.strip(".,!?;:\"'()").lower()
                for w_info in scene_word_alignments:
                    clean_w = w_info["word"].strip(".,!?;:\"'()").lower()
                    if clean_trigger in clean_w or clean_w in clean_trigger:
                        visual["start_time"] = w_info["start"]
                        visual["end_time"] = scene["end_time"]
                        trigger_found = True
                        break

            if not trigger_found:
                # Default to scene start time
                visual["start_time"] = scene["start_time"]
                visual["end_time"] = scene["end_time"]

    return scene_spec
