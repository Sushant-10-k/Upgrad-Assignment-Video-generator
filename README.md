# AutoVideo — Deterministic Script-to-Explainer Video Pipeline

> **Design Principle**: *Use AI to understand the script; use deterministic software to produce the pixels.*

AutoVideo converts a plain-text narration script into a fully synchronized MP4 explainer
video using an LLM for semantic planning, Piper for TTS narration, Whisper for
word-level alignment, Pillow for programmatic rendering, and FFmpeg for final composition.

---

## Features

| Capability | Detail |
|---|---|
| **One-command generation** | `python run.py --script scripts/my_script.txt --out output/video.mp4` |
| **Generalizes to any topic** | No hardcoded vocabulary — same code runs Script A (Color Theory) and Script B (Water Cycle) |
| **Deterministic rendering** | SHA-256 content-addressed cache; same input → same output every run |
| **Computed numerical values** | Python AST evaluator — never LLM-hallucinated numbers |
| **Synchronized visuals** | Whisper word alignment within ±150 ms of narration |
| **Human-editable YAML IR** | Inspect, adjust, and re-render `scenes/*.yaml` without re-running the LLM |
| **Incremental re-render** | Edit one scene → only that scene is re-rendered (`[CACHE HIT]` for others) |
| **Swappable components** | Config-driven voice/renderer providers via abstract interfaces |

---

## Requirements

- Python 3.10+
- FFmpeg (bundled via `imageio-ffmpeg` — no manual install needed)
- OpenAI API key (for scene planning)
- Optional: [Piper TTS](https://github.com/rhasspy/piper) for high-quality narration
- Optional: [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for precise alignment

---

## Installation

```bash
# 1. Clone
git clone https://github.com/Sushant-10-k/Upgrad-Assignment-Video-generator.git
cd Upgrad-Assignment-Video-generator

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API key
cp .env.example .env
# Edit .env and set:  OPENAI_API_KEY=sk-...
```

---

## Quick Start

### Full Pipeline (Script → MP4)

```bash
python run.py --script scripts/script_a.txt --out output/script_a.mp4
```

This runs all 7 stages and saves:
- `output/script_a.mp4` — final video
- `scenes/script_a.yaml` — editable scene specification

### Render-Only Mode (Edit YAML → MP4)

After editing `scenes/script_a.yaml`:

```bash
python render.py --scene scenes/script_a.yaml --out output/script_a_v2.mp4
```

Only changed scenes are re-rendered. Unchanged scenes show `[CACHE HIT]`.

---

## CLI Reference

### `run.py` — Full Pipeline

```
python run.py --script SCRIPT --out OUTPUT [--config CONFIG] [--save-spec SPEC]

  --script    Path to input UTF-8 plain-text narration script  (required)
  --out       Path to output MP4 video file                    (required)
  --config    Path to custom config.yaml                       (optional)
  --save-spec Path to save generated scene specification YAML  (optional)
```

### `render.py` — Render-Only Mode

```
python render.py --scene SCENE_YAML --out OUTPUT [--config CONFIG]

  --scene     Path to scene specification YAML file  (required)
  --out       Path to output MP4 video file          (required)
  --config    Path to custom config.yaml             (optional)
```

---

## Configuration (`config/config.yaml`)

```yaml
video:
  width: 854
  height: 480
  fps: 30
  aspect_ratio: "16:9"  # or "9:16" for vertical

voice:
  provider: "piper"     # or "edge_tts", "openai"

cache:
  dir: "cache"
```

---

## Pipeline Stages

```
Script (TXT)
    │
    ▼ [1/7] Load script
    │
    ▼ [2/7] LLM Scene Planner (GPT-4o-mini, temperature=0)
    │       ↳ Produces scenes/*.yaml  ← human-editable
    │
    ▼ [3/7] TTS Narration (Piper / fallback synthesizer)
    │
    ▼ [4/7] Word Alignment (faster-whisper / acoustic fallback)
    │
    ▼ [5/7] Schema Validation + Trigger Resolution (±150 ms sync)
    │
    ▼ [6/7] PIL Frame Renderer (10 visual types, 11 animations)
    │       ↳ Per-scene SHA-256 cache keys
    │
    ▼ [7/7] FFmpeg Composition → output/*.mp4
```

---

## Cache Behavior

All stages are SHA-256 content-addressed. On re-runs:

```
[CACHE HIT] planner (55e77e25)
[CACHE HIT] narration (a7ff4d25)
[CACHE HIT] alignment (8cf45c86)
[CACHE HIT] scene (77793547)      scene_001 [OK]
[CACHE HIT] scene (23721835)      scene_002 [OK]
[CACHE HIT] final video (c5bef2c9)
```

Editing scene_002 in the YAML only invalidates that scene + final composition.
All other scenes remain cache hits.

See [`docs/cache_demo.md`](docs/cache_demo.md) for a full walkthrough.

---

## Running Tests

```bash
# All unit + determinism tests (fast, no LLM calls for cached runs)
python -m pytest tests/ -v

# Expected: 19 passed
```

---

## Project Structure

```
autovideo/
├── run.py                    # Full pipeline entry point
├── render.py                 # Render-only entry point
├── config/
│   └── config.yaml           # Pipeline configuration
├── scripts/
│   ├── script_a.txt          # Script A: Color Theory (primary)
│   └── script_b.txt          # Script B: Water Cycle (held-out validation)
├── scenes/                   # Auto-generated scene specification YAMLs
├── output/                   # Final MP4 videos
├── cache/                    # SHA-256 content-addressed cache
├── logs/                     # Timestamped pipeline logs + determinism reports
├── docs/
│   ├── cache_demo.md         # Incremental re-render walkthrough
│   ├── engineering_log.md    # Alternatives evaluated + dead ends
│   └── acceptance_criteria.md # AC1–14 sign-off table
├── src/
│   ├── pipeline.py           # Orchestrator
│   ├── config.py             # Configuration loader
│   ├── errors.py             # Categorized error classes
│   ├── logging_config.py     # Structured logger
│   ├── determinism.py        # Determinism report emitter
│   ├── cache/cache.py        # SHA-256 content-addressed cache
│   ├── planner/              # LLM scene planner + fallback
│   ├── narration/            # TTS voice providers
│   ├── alignment/            # Whisper word aligner + acoustic fallback
│   ├── numerical/            # AST-based numerical calculator
│   ├── synchronization.py    # Trigger resolution engine
│   ├── renderer/             # PIL frame renderer
│   ├── composer/             # FFmpeg composition
│   └── validation/           # Pydantic schema
└── tests/                    # Full test suite (19 tests)
```

---

## Determinism

AutoVideo is designed for reproducible outputs. On each run it emits a
`logs/determinism_report_*.txt` categorising every component as:

- **Strictly deterministic**: byte-identical outputs guaranteed (numerical engine, renderer, cache)
- **Non-deterministic but cached**: LLM planner, TTS, Whisper — non-deterministic on first run,
  deterministic on all subsequent runs via SHA-256 cache

See [docs/engineering_log.md](docs/engineering_log.md) for full design rationale.

---

## Extending the Pipeline

### Add a new Voice Provider

1. Subclass `src.narration.base.VoiceProvider`
2. Implement `synthesize(text, output_path) -> str`
3. Set `voice.provider: "your_provider"` in `config.yaml`

### Add a new Visual Type

1. Add a handler in `src.renderer.pil_renderer.PILRenderer._draw_visual()`
2. Register the type string in `src/validation/schema.py`

---

## License

MIT
