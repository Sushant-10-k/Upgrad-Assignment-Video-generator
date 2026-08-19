# Cache Demonstration — Incremental Re-render (PRD §45 / R8 / AC12-13)

This document demonstrates that changing **one scene** in the scene specification
only regenerates that scene and the final composition — all other scenes remain
`[CACHE HIT]`.

---

## Step 1 — Run Full Pipeline (Cold Cache)

```bash
python run.py --script scripts/script_a.txt --out output/script_a.mp4
```

Expected log output:
```
[1/7] Loading script
      63 words
[2/7] Planning scenes
      6 scenes generated
      Scene spec saved → scenes\script_a.yaml
[3/7] Generating narration
      PIPER TTS
[4/7] Aligning narration
      63 word timestamps
[5/7] Validating scene specification
      6 scenes
      0 validation errors
[6/7] Rendering scenes
      scene_001 ✓
      scene_002 ✓
      scene_003 ✓
      scene_004 ✓
      scene_005 ✓
      scene_006 ✓
[7/7] Encoding final video
      854x480 / 30 FPS

DONE
output/script_a.mp4
```

---

## Step 2 — Run Again Immediately (Warm Cache)

```bash
python run.py --script scripts/script_a.txt --out output/script_a.mp4
```

Expected log output:
```
[1/7] Loading script
      63 words
[CACHE HIT] planner (b50a9565)
[CACHE HIT] narration (0d5e86d6)
[CACHE HIT] alignment (7068502e)
[5/7] Validating scene specification
      6 scenes
      0 validation errors
[6/7] Rendering scenes
[CACHE HIT] scene (0c249bb1)
      scene_001 ✓
[CACHE HIT] scene (1f0aa21e)
      scene_002 ✓
[CACHE HIT] scene (815a34d8)
      scene_003 ✓
[CACHE HIT] scene (776a8707)
      scene_004 ✓
[CACHE HIT] scene (5b727105)
      scene_005 ✓
[CACHE HIT] scene (31e72d24)
      scene_006 ✓
[CACHE HIT] final video (a5401530)

DONE
output/script_a.mp4
```

All 6 scenes and the final video are served from cache. ✅

---

## Step 3 — Edit scene_001 in the YAML Spec

Open `scenes/script_a.yaml` and change the `text` of scene_001's first visual:

```yaml
# Before
- type: text
  text: "COMPUTERS"
  animation: fade_in

# After
- type: text
  text: "DIGITAL COLOR"   # ← changed
  animation: fade_in
```

Save the file.

---

## Step 4 — Re-render Using render.py (Render-Only Mode)

```bash
python render.py --scene scenes/script_a.yaml --out output/script_a_v2.mp4
```

Expected log output:
```
[1/4] Loading scene specification
      scenes/script_a.yaml
[2/4] Generating narration audio (cached if unchanged)
[CACHE HIT] narration (0d5e86d6)
[3/4] Rendering individual scenes
      scene_001 ✓        ← REGENERATED (content hash changed)
[CACHE HIT] scene (1f0aa21e)
      scene_002 ✓        ← CACHE HIT (unchanged)
[CACHE HIT] scene (815a34d8)
      scene_003 ✓        ← CACHE HIT
[CACHE HIT] scene (776a8707)
      scene_004 ✓        ← CACHE HIT
[CACHE HIT] scene (5b727105)
      scene_005 ✓        ← CACHE HIT
[CACHE HIT] scene (31e72d24)
      scene_006 ✓        ← CACHE HIT
[4/4] Encoding final video
      854x480 / 30 FPS

DONE
output/script_a_v2.mp4
```

**Result**: Only `scene_001` was regenerated. Scenes 2–6 were all cache hits.
The final composition was rebuilt because one of its inputs changed. ✅

---

## How the Cache Keys Work (PRD §19-20)

Each scene cache key is:
```python
SHA256(scene_content + style_config + resolution + renderer_version)
```

Changing the text of scene_001 changes its `scene_content` → new hash → cache miss.
Scenes 2–6 have unchanged content → same hashes → cache hits.

The final video key is:
```python
SHA256(all_scene_hashes + narration_hash + video_config)
```

Since scene_001's hash changed, the final video key changes → recomposed.
Narration and alignment are unchanged → still cache hits.
