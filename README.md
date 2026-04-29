# LGTM — Looks Good To Merge

Short-form video pipeline aimed at enterprise IT culture: **Mike Judge × Gary Larson** energy — deadpan, bureaucratic, the situation is the joke. Inputs are **one-line briefs** plus JSON; outputs are **render-ready MP4s** with optional distribution copy.

**Founding premise (show framing):** the code was AI-written; the humans approved it. LGTM.

---

## What’s in this repo

| Piece | Purpose |
|--------|---------|
| `episodes/ep001/` … | Per-episode folder: `episode.json`, `storyboard.json`, markdown from agents, `tts/`, `clips/`, `output/` |
| `schemas/` | JSON Schema for `episode.json` and `storyboard.json` |
| `render/renderer.py` | **MoviePy** renderer — composites cards, b-roll, kinetic text, Slack/JIRA/calendar mocks, mixes VO + music + synthesized SFX |
| `render/remotion_renderer.py` | **Remotion** renderer — React/CSS motion graphics; Python builds the audio mix; FFmpeg muxes silent video + WAV |
| `render/remotion/` | Remotion project (card, kinetic, b-roll, burst, Amiga bumper styles, captions, mockup PNG staging) |
| `render/mockups.py` | PIL mockups (`slack`, `jira`, `calendar`, `code`) exported as PNG for Remotion or MoviePy |
| `render/sfx.py` | Generates `assets/sfx/*.wav`; run `python render/sfx.py` after changing synth code |
| `render/qa.py` | Optional post-render checks (streams, bitrate, duration); Remotion path runs this when wired |
| `render/generate_assets.py` | Fetches custom generative b-roll imagery from Pollinations.ai for hyper-specific scenes |
| `render/distribute.py` | Reads `distribution.md` and posts the video to Slack (defaults to dry-run unless `--execute` is passed) |
| `.claude/agents/` | Claude Code agent definitions for the creative pipeline |
| `.codex/agents/` | Codex CLI role prompts that mirror the creative pipeline |
| `scripts/codex-video.ps1` | PowerShell wrapper for running LGTM agents with `codex exec` |
| `render/pipeline.py` | **Episode builder** — Pollinations (optional) → Kokoro TTS → Giphy/Pixabay/Pexels clips → `production_check` → `renderer.py` |
| `scripts/build-episode.ps1` | Thin wrapper around `render/pipeline.py` for Windows |
| `REQUIREMENTS.md` | Brand + technical spec |
| `CLAUDE.md` | Cursor / assistant project guide (paths, rules) |

Paths inside `episode.json` / `storyboard.json` are **relative to the episode directory** (e.g. `tts/s01.wav`).

---

## Pipeline (conceptual)

```
brief → strategy → script → storyboard → [human approval: episode.json approved: true]
  → optional: claim-review, visual-brief, audio-direction
  → tts-builder + clip-sourcer (can run in parallel)
  → render → optional: distribution.md
```

**Human gate:** production render expects `episode.json` to have `"approved": true`. The render scripts refuse to render otherwise.

---

## Prerequisites

- **Python 3** with packages used by `render/` (e.g. `moviepy`, `numpy`, Pillow, and dependencies Remotion muxing relies on).
- **FFmpeg** and **ffprobe** on `PATH` (mux, probes, QA).
- **Node.js** — only needed for **`remotion_renderer.py`** (`npm install` inside `render/remotion/` once).
- **Kokoro TTS** — local WAV generation for VO (`am_michael` voice). Paths vary by machine; see **`CLAUDE.md`** for the project’s Kokoro venv and `kokoro_synth.py` usage.
- **`.env`** at repo root (not committed) for stock/Giphy APIs as needed, e.g. `PIXABAY_API_KEY`, `PEXELS_API_KEY`, `GIPHY_API_KEY`.

---

## Which renderer to use

- **`render/remotion_renderer.py`** — **(Recommended)** Use when **`episode.json`** sets **`"renderer": "remotion"`** (as in newer episodes). Renders visuals with Remotion, mixes audio in Python (music bed + VO + SFX), then FFmpeg-combines video and audio.
- **`render/renderer.py`** — **(MoviePy fallback)** Full **MoviePy** stack: all scene types. Now supports parallel chunk rendering under the hood for much faster performance.
  ```bash
  python render/renderer.py --episode episodes/ep001/episode.json
  ```

After **first** Remotion setup:

```bash
cd render/remotion && npm install
cd ../..
python render/remotion_renderer.py --episode episodes/ep003/episode.json
```

Output defaults to **`episodes/<id>/output/episode.mp4`**.

---

## One-off tasks

| Task | Command / note |
|------|----------------|
| Regenerate SFX library | `python render/sfx.py` → writes `assets/sfx/*.wav` |
| Validate a rendered file | `python -c "from render.qa import qa_check; from pathlib import Path; print(qa_check(Path('episodes/ep004/output/episode.mp4'), 19.8))"` (adjust duration) |
| Generate custom assets | `python render/generate_assets.py --episode episodes/ep001/episode.json` |
| Distribute episode | `python render/distribute.py --episode episodes/ep001/episode.json --execute` |

---

## New episode workflow (manual summary)

1. Copy an existing `episodes/ep00X/` layout or create `episodes/ep00N/` with `tts/`, `clips/`, `output/`.
2. Fill **`episode.json`** (metadata, **`render_config`**, **`approved`** when ready, optional **`renderer`**, **`clip_sources`**).
3. Write **`storyboard.json`** matching **`schemas/storyboard.schema.json`** (scene types: `card`, `kinetic`, `broll`, `mockup`, etc.).
4. **Materialize assets + render** (recommended — pulls/creates what the storyboard references):

   ```bash
   python render/pipeline.py --episode episodes/ep00N/episode.json
   ```

   Or before approval, only WAVs + clips:

   ```bash
   python render/pipeline.py --episode episodes/ep00N/episode.json --no-render
   ```

   Manual path: produce **`tts/*.wav`** (Kokoro), place **`clips/<scene_id>.mp4`**, run **`production_check.py`**, then the **renderer**.

Creative steps (strategy, script, claiming, clip sourcing) are usually driven via **agents in `.claude/agents/`** — see **`REQUIREMENTS.md`** for roster and rules.

### Codex CLI workflow

Codex can run the same pipeline through `.codex/agents/`:

```powershell
.\scripts\codex-video.ps1 -Agent creative-director -Episode ep007 -Brief "One-line episode brief"
```

Run a single step:

```powershell
.\scripts\codex-video.ps1 -Agent storyboard -Episode ep007
.\scripts\codex-video.ps1 -Agent renderer -Episode ep007
```

Useful flags: `-Search` enables Codex web search, `-Model <model>` selects a model, and `-FullAuto` passes Codex CLI `--full-auto`. Full workflow notes live in `.codex/workflows/create-video.md`.

Before final render, run the production gate:

```powershell
python render/production_check.py --episode episodes/ep007/episode.json --require-audio
```

This fails all-card/fallback-card packages before they become technically valid but creatively weak MP4s.

---

## Brand constants (defaults)

Defined in **`render_config`** inside each **`episode.json`** (no magic numbers in render code):

- Background **`rgb(10, 10, 16)`**, accent **`rgb(232, 160, 32)`**
- VO: Kokoro **`am_michael`**
- Music bed level capped (see schema / **REQUIREMENTS.md** — typically ≤ **0.15**)
- **LGTM** label upper-left; cards: one headline + one subtitle

---

## Docs index

- **`REQUIREMENTS.md`** — full requirements and v1 scope
- **`CLAUDE.md`** — assistant-oriented guide (Kokoro paths, keys, pipeline order)
- **`schemas/*.schema.json`** — contracts for JSON editors and validation

---

## License / third-party

Stock clips, Giphy IDs, fonts, and Remotion toolchain are subject to **their respective licenses**. Review usage before publishing publicly.
