# AutoVideo — Engineering Log (PRD §35–36)

This document records all architectural alternatives evaluated, trade-offs weighed,
and dead ends encountered during development of AutoVideo.

---

## LLM Scene Planner (PRD §35)

### Options Evaluated

| Option | Structured Output | Reasoning Quality | Determinism | Cost | Decision |
|---|---|---|---|---|---|
| **OpenAI GPT-4o-mini** | Native JSON mode | High | temperature=0 + cache | Low | ✅ Selected |
| Groq LLaMA-3 | JSON schema mode | High | temperature=0 | Free tier | Viable alternative |
| Local Ollama | Varies by model | Medium | Full local | Zero | Viable fallback |

### Decision: OpenAI with offline rule-based fallback
- `temperature=0` and pinned model string maximise LLM-side determinism.
- Planner output is SHA-256 cached so repeated runs never call the API.
- Offline fallback planner (`_generate_fallback_plan`) ensures 100% pipeline
  execution even without an API key—critical for unattended CI runs.
- **Prompt design**: zero domain-specific keywords. The prompt never mentions
  "color", "pixel", "RGB" or any Script A vocabulary. Validated against
  Script B ("Water Cycle") without modification.

---

## TTS (PRD §35)

### Options Evaluated

| Option | Voice Quality | Reproducibility | Local | Cost | Decision |
|---|---|---|---|---|---|
| **Piper TTS** | Good | High (pinned model) | ✅ | Zero | ✅ Selected |
| OpenAI TTS | Excellent | Medium (API) | ❌ | Per-character | Future option |
| ElevenLabs | Excellent | Medium | ❌ | Per-character | Future option |
| Edge TTS | Good | Medium | Partial | Zero | Alternative |

### Decision: Piper with deterministic fallback synthesizer
- Local execution ensures offline operation and zero cloud cost.
- Narration output is SHA-256 cached so synthesis only runs once per script.
- A deterministic wave-based fallback synthesizer (proportional word timing)
  ensures the pipeline works even without the Piper binary installed.

---

## Word Alignment (PRD §35)

### Options Evaluated

| Option | Timing Accuracy | Automated | Cost | Decision |
|---|---|---|---|---|
| **faster-whisper** | ±50–150 ms | ✅ | Zero | ✅ Selected |
| Manual estimation (word_count / rate) | ±500–2000 ms | ✅ | Zero | Dead End |
| TTS native timestamps | Varies | Piper: ❌ | Zero | Future option |

### Decision: faster-whisper with acoustic fallback
- Generates alignment from actual speech — the only way to hit the ±150 ms
  target specified in R5.
- Acoustic proportional fallback used if faster-whisper is unavailable;
  structurally correct (monotonic, word-count-matched) though less precise.

---

## Visual Generation (PRD §35)

### Options Evaluated

| Option | Numerical Accuracy | Determinism | Decision |
|---|---|---|---|
| **Pillow programmatic rendering** | Perfect | ✅ | ✅ Selected |
| AI image generation (DALL-E, SD) | Fails R4 | ❌ | Dead End |
| SVG + browser rendering | Good | Partial | Future option |
| OpenCV | Good | ✅ | Alternative |

### Decision: Pillow frame-by-frame renderer
- Only programmatic rendering guarantees exact numerical text (R4).
- See Dead End 1 below.

---

## Video Rendering (PRD §35)

| Option | Determinism | Windows-compatible | Decision |
|---|---|---|---|
| **Pillow frames → FFmpeg** | ✅ | ✅ | ✅ Selected |
| MoviePy | Partial | ✅ | Considered |
| Remotion (Node.js) | High | ✅ | Future |
| OpenCV VideoWriter | ✅ | ✅ | Alternative |

### Decision: Pillow + imageio-ffmpeg
- `imageio-ffmpeg` bundles a platform-specific FFmpeg binary via pip,
  eliminating the "FFmpeg not in PATH" install step for users on Windows/macOS.
- Pinned FFmpeg flags (`-c:v libx264`, `-r {fps}`, `-c:a aac`, `-pix_fmt yuv420p`)
  ensure deterministic codec and encoding settings.

---

## Dead Ends (PRD §36)

### Dead End 1 — AI Image Generation

**Hypothesis**: DALL-E or Stable Diffusion would provide rich visuals automatically.

**Experiment**: Asked GPT-4o to render "the number 16,777,216" and "the equation 2^8=256".

**Result**:
- Generated images contained distorted glyphs, incorrect digit sequences,
  inconsistent typography, and non-reproducible layouts.
- Every run produced a different image — violating R3 (determinism).
- Numbers were occasionally wrong — violating R4 (computed on-screen values).

**Decision**: AI for semantic planning only. Pillow for all pixel production.

---

### Dead End 2 — Word Count Timing Estimation

**Hypothesis**: `duration = word_count / 150` words-per-minute would give adequate timing.

**Experiment**: Timed Piper TTS output vs estimated durations.

**Result**:
- Technical terms ("evapotranspiration", "16,777,216") take 2-3× longer than short words.
- Punctuation pauses add 0.3–0.8 s per sentence.
- Visual events drifted 0.5–2.0 s from spoken words — far outside ±150 ms target.

**Decision**: Generate actual audio first, then use faster-whisper word alignment.

---

### Dead End 3 — Direct LLM Code Generation for Rendering

**Hypothesis**: Ask LLM to write Pillow Python code per scene.

**Result**:
- LLM-generated code contained subtle bugs (wrong coordinate systems, off-by-one
  errors, hardcoded dimensions, unsafe `eval()` calls).
- Violates R3 (non-deterministic code), R4 (unreliable numerics), R7 (not swappable).

**Decision**: LLM outputs only a validated YAML scene spec. Renderer is fixed Python.
