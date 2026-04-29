# LGTM — Project Guide

Short-form video pipeline. Input: one-line brief. Output: render-ready MP4 package.
Tone: Mike Judge meets Gary Larson. Deadpan. The situation is the joke.

## Episode directory layout

Every episode lives under `episodes/{episode_id}/`. The `episode_id` is `ep001`, `ep002`, etc.

```
episodes/
  ep001/
    episode.json          ← master config + human approval gate
    storyboard.json       ← timecoded scene list (storyboard agent output)
    script.md             ← word-for-word VO (script agent output)
    strategy.md           ← hook angles + format plan (strategy agent output)
    visual-brief.md       ← shot list + overlay specs (visual-brief agent output)
    audio-direction.md    ← music + SFX direction (audio-direction agent output)
    claim-review.md       ← fact-check results (claim-review agent output)
    distribution.md       ← captions + hashtags (distribution agent output)
    tts/
      s01.wav             ← per-scene Kokoro TTS (tts-builder output)
      s02.wav
    clips/
      s02.mp4             ← per-scene stock video (clip-sourcer output)
      s04.mp4
    output/
      episode.mp4         ← final render (renderer output)
```

All paths in `episode.json` and `storyboard.json` are **relative to the episode directory root** (e.g. `tts/s01.wav`, not an absolute path).

New episode = new directory + new JSON. Do not add **episode-specific** Python; shared tooling under `render/` is OK.

## Pipeline order

```
strategy → script → storyboard → [HUMAN GATE: approved: true]
  → claim-review + visual-brief + audio-direction (parallel)
    → episode materialization (see below)
      → renderer → distribution
```

**Episode materialization (binaries):** run **`python render/pipeline.py --episode episodes/{id}/episode.json`** so Kokoro TTS, stock APIs (Giphy/Pixabay/Pexels via `.env`), optional Pollinations assets from `generate_assets.py`, `production_check.py`, and **`render/renderer.py`** all run in order. Use **`--no-render`** before approval to only build `tts/` + `clips/`. Override Kokoro paths with **`LGTM_KOKORO_PYTHON`** and **`LGTM_KOKORO_SYNTH`** if defaults in this file do not match your machine.

## Hard rules

1. One renderer: `render/renderer.py`. All episodes, one script.
2. Human gate: renderer exits if `episode.json` `approved` is not `true`.
3. Graceful degradation: missing broll clip → fallback card, never crash.
4. No magic numbers in `renderer.py` — all values come from `episode.json` `render_config`.
5. Music bed ≤ 0.15 volume.
6. LGTM label: upper-left, every frame, every scene.
7. Copy discipline: one headline + one subtitle per card, never more.

## Brand constants

| Token | Value |
|---|---|
| Background | `rgb(10, 10, 16)` |
| Accent | `rgb(232, 160, 32)` |
| Font | Consolas |
| VO voice | Kokoro `am_michael` |

## Key files

| File | Purpose |
|---|---|
| `schemas/episode.schema.json` | JSON Schema for episode.json |
| `schemas/storyboard.schema.json` | JSON Schema for storyboard.json |
| `render/renderer.py` | Single renderer — reads episode.json + storyboard.json |
| `.claude/agents/` | All agent definitions |
| `.env` | API keys (not committed) |
| `REQUIREMENTS.md` | Full brand and technical spec |

## Environment

- `PIXABAY_API_KEY` — in `.env`, set
- `PEXELS_API_KEY` — in `.env`, not yet set
- Kokoro venv: `C:\Users\James\OneDrive\dev\warp-test\v1\local_tts\venv_kokoro`
- Kokoro CLI: `C:\Users\James\OneDrive\dev\warp-test\v1\local_tts\kokoro_synth.py`
- Usage: `python kokoro_synth.py --text "..." --out tts/s01.wav --voice am_michael`
