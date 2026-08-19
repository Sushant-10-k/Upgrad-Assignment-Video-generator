# AutoVideo — Acceptance Criteria Sign-off (PRD §32)

Final sign-off table against all 14 Acceptance Criteria.

| AC | Description | Status | Evidence |
|---|---|---|---|
| **AC1** | One command generates a finished MP4 | ✅ PASS | `python run.py --script scripts/script_a.txt --out output/script_a.mp4` runs unattended to a valid MP4 |
| **AC2** | Same command works on unseen Script B without code modification | ✅ PASS | `python run.py --script scripts/script_b.txt --out output/script_b.mp4` — zero code/prompt/config changes; Water Cycle topic |
| **AC3** | Running same script twice yields deterministic output | ✅ PASS | `tests/test_determinism.py` — scene spec structure identical, numerical values identical, cache keys stable |
| **AC4** | All numerical values in Script A appear correctly | ✅ PASS | `tests/test_numerical.py` — `2^8=256`, `256*256*256=16,777,216`, `0–255`, `(255,0,0)` all verified |
| **AC5** | Numerical values are programmatically calculated | ✅ PASS | `src/numerical/calculator.py` — Python AST evaluator, never LLM |
| **AC6** | Visual events synchronize within ±150 ms | ✅ PASS | `tests/test_sync.py` — trigger word resolution asserts `abs(start_time - expected) <= 0.15` |
| **AC7** | Human-readable scene specification is generated | ✅ PASS | `scenes/script_a.yaml` produced every run; human-editable YAML |
| **AC8** | Editing scene spec changes rendered output | ✅ PASS | `python render.py --scene scenes/script_a.yaml --out output/rerender.mp4` rerenders from edited YAML |
| **AC9** | Voice and renderer can be swapped via config | ✅ PASS | `config/config.yaml` `voice.provider` and `renderer.provider` control selection; abstract interfaces in `src/narration/base.py` and `src/renderer/base.py` |
| **AC10** | 16:9 output is supported | ✅ PASS | `config.yaml` `aspect_ratio: "16:9"` → 854×480; `tests/test_renderer.py` validates |
| **AC11** | 9:16 output is supported | ✅ PASS | `config.yaml` `aspect_ratio: "9:16"` → 480×854; `tests/test_renderer.py` validates both |
| **AC12** | Changing one scene does not regenerate unrelated scenes | ✅ PASS | `tests/test_incremental.py` — SHA-256 cache keys per-scene; unedited scenes show `[CACHE HIT]` |
| **AC13** | Cache behavior is visible in logs | ✅ PASS | `[CACHE HIT] planner (b50a9565)`, `[CACHE HIT] narration (0d5e86d6)`, etc. printed to stdout and `logs/pipeline_*.log` |
| **AC14** | README allows new developer to clone, install, run | ✅ PASS | `README.md` — complete clone → `pip install -r requirements.txt` → `python run.py ...` instructions |

---

## Hard Requirements Cross-check

| Requirement | Satisfied | Mechanism |
|---|---|---|
| R1 — One Command | ✅ | `run.py` orchestrates all 7 stages |
| R2 — Generalisation | ✅ | Generic prompt; Script B tested without modification |
| R3 — Determinism | ✅ | SHA-256 caching + `determinism.py` report |
| R4 — Computed On-Screen Values | ✅ | `calculator.py` AST evaluator |
| R5 — Auto Narration Sync | ✅ | `whisper.py` + `synchronization.py` (±150 ms) |
| R6 — Inspectable IR | ✅ | `scenes/*.yaml` — human-readable, editable |
| R7 — Swappable Components | ✅ | Abstract interfaces + config-driven selection |
| R8 — Incremental Re-render | ✅ | Content-addressed cache; per-scene SHA-256 keys |
