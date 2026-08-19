import os
import json
import yaml
import logging
from typing import Dict, Any, Optional
from src.planner.base import ScenePlanner
from src.validation.schema import SceneSpec
from src.cache.cache import CacheManager, compute_cache_key
from src.config import Config, load_config

logger = logging.getLogger(__name__)

# General prompt: ZERO domain-specific keywords or Script A references.
GENERIC_SYSTEM_PROMPT = """You are an expert video director and animator.
Your task is to take a plain-text narration script and break it down into an ordered series of visual scenes for an educational explainer video.

Return ONLY a valid JSON object matching this schema:
{
  "scenes": [
    {
      "id": "scene_001",
      "narration": {
        "text": "Exact sentence or clause from script for this scene."
      },
      "visuals": [
        {
          "type": "text | number | circle | rectangle | line | arrow | icon | image | equation | chart",
          "text": "Text to render on screen if type is text",
          "expression": "Mathematical expression if equation/number",
          "value_expression": "Expression to evaluate if number",
          "computed_value": null,
          "animation": "fade_in | fade_out | slide_left | slide_right | slide_up | slide_down | scale | highlight | draw | counter",
          "trigger": {
            "word": "Specific word in narration text when visual should appear"
          }
        }
      ],
      "transition": {
        "type": "cut | fade | crossfade | slide",
        "duration": 0.5
      }
    }
  ]
}

Rules:
1. Divide script into logical scenes (1-2 sentences per scene).
2. For each scene, create 1-3 visual elements that illustrate the concept.
3. If narration mentions math or numbers (e.g., 2^8, 256*256), use type 'equation' or 'number' with expression set to the formula.
4. Set trigger.word to an exact word present in narration text for precise audio synchronization.
5. Do NOT include markdown code fences or explanations outside the JSON object.
"""


class LLMScenePlanner(ScenePlanner):
    """LLM-based Scene Planner with schema validation and SHA-256 caching."""

    PROMPT_VERSION = "v1.0"

    def __init__(self, config: Optional[Config] = None, cache_manager: Optional[CacheManager] = None):
        self.config = config or load_config()
        self.cache_manager = cache_manager or CacheManager(self.config.cache.dir)

    def _call_llm(self, prompt: str, system_prompt: str) -> str:
        """Execute LLM call using OpenAI API or fallback if key not configured."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment. Generating rule-based scene specification.")
            return self._generate_fallback_plan(prompt)

        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=self.config.llm.model,
                temperature=self.config.llm.temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Script to animate:\n\n{prompt}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM API call failed: {e}. Falling back to rule-based planner.")
            return self._generate_fallback_plan(prompt)

    def _generate_fallback_plan(self, script_text: str) -> str:
        """Deterministic rule-based fallback scene spec generator for offline/testing use."""
        paragraphs = [p.strip() for p in script_text.split(".") if p.strip()]
        scenes = []
        for idx, sentence in enumerate(paragraphs, start=1):
            words = sentence.split()
            first_word = words[0] if words else ""
            last_word = words[-1] if words else ""

            visuals = [
                {
                    "type": "text",
                    "text": sentence[:30].upper(),
                    "animation": "fade_in",
                    "trigger": {"word": first_word}
                }
            ]

            # Detect math/numbers in sentence
            import re
            math_exprs = re.findall(r"\b(?:\d+\^\d+|\d+\s*[\*\+x×]\s*\d+|\d+\s*to\s*\d+|\(\d+,\s*\d+,\s*\d+\))\b", sentence)
            for expr in math_exprs:
                visuals.append({
                    "type": "number" if "^" in expr or "*" in expr or "x" in expr else "text",
                    "expression": expr,
                    "value_expression": expr,
                    "animation": "highlight",
                    "trigger": {"word": last_word}
                })

            scenes.append({
                "id": f"scene_{idx:03d}",
                "narration": {"text": sentence + "."},
                "visuals": visuals,
                "transition": {"type": "fade", "duration": 0.5}
            })

        return json.dumps({"scenes": scenes}, indent=2)

    def plan(self, script_text: str) -> Dict[str, Any]:
        """Generate validated Scene Specification dictionary from script."""
        cache_key = compute_cache_key(
            script_text,
            self.PROMPT_VERSION,
            self.config.llm.model,
            self.config.llm.temperature
        )

        # Check Cache (PRD §19 / R8)
        if self.config.cache.enabled and self.cache_manager.exists("planner", cache_key, extension="json"):
            logger.info(f"[CACHE HIT] planner ({cache_key[:8]})")
            cached_json = self.cache_manager.get("planner", cache_key, extension="json")
            return json.loads(cached_json)

        logger.info("[2/7] Planning scenes via LLM Planner")

        raw_response = self._call_llm(script_text, GENERIC_SYSTEM_PROMPT)

        # Parse & Validate with Pydantic
        try:
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json") or cleaned.startswith("yaml"):
                    cleaned = "\n".join(cleaned.split("\n")[1:])
            data = json.loads(cleaned)

            # Ensure video and style configs from system config are populated
            if "video" not in data:
                data["video"] = self.config.video.model_dump()
            if "style" not in data:
                data["style"] = self.config.style.model_dump()

            spec = SceneSpec(**data)
            spec_dict = spec.model_dump(mode="json")

            # Save to Cache
            if self.config.cache.enabled:
                self.cache_manager.put("planner", cache_key, json.dumps(spec_dict, indent=2), extension="json")

            return spec_dict
        except Exception as err:
            logger.error(f"ERROR: Invalid scene specification produced by LLM: {err}")
            raise ValueError(f"ERROR: Invalid scene specification produced by LLM planner: {err}")
