# LGTM — Requirements

## Show Identity

| Property | Value |
|---|---|
| Show name | LGTM |
| Tagline | Looks Good To Merge |
| Founding premise | 100% of this show's code was written by AI. The humans approved it. LGTM. |
| Format | Short-form video (target 60–90 s) |
| Voice | Dry, authoritative, slightly bureaucratic |
| Tone reference | Mike Judge (Office Space, Silicon Valley) × Gary Larson (Far Side) |
| Tone rule | Deadpan, zero irony signaling. The situation is the joke. Never wink at the camera. |

## Brand Constants

| Token | Value |
|---|---|
| Background | `rgb(10, 10, 16)` near-black |
| Accent | `rgb(232, 160, 32)` amber — one accent, used consistently |
| Headline font | Consolas (monospace) — technical authority |
| LGTM label | Upper-left, every frame, every scene, no exceptions |
| Copy discipline | One headline + one subtitle per card, never more |
| VO voice | Kokoro `am_michael` — neutral, authoritative |

## Pipeline

```
Brief
  └─ strategy          hook angles, format, retention structure
       └─ script        word-for-word VO in brand voice
            └─ storyboard    timecoded scene list → storyboard.json
                 └─ [HUMAN GATE]   approved: true required to proceed
                      ├─ claim-review      fact-check stats and superlatives
                      ├─ visual-brief      shot list, B-roll direction, text overlay specs
                      └─ audio-direction   music direction, SFX cues, energy arc
                           ├─ tts-builder   Kokoro TTS synthesis per VO segment → tts/*.wav
                           └─ clip-sourcer  stock video per scene → clips/*.mp4
                                └─ renderer      MoviePy assembly → output/episode.mp4
                                     └─ distribution   captions, hashtags, thumbnails per platform
```

Human gate is non-negotiable. Renderer reads `approved` from episode.json and exits if `false`.

### Rules posture (strict vs loose)

| Strict (machine / gate) | Loose (creative / taste) |
|-------------------------|---------------------------|
| `approved: true` before final render | Hook wording, scene count, mockup copy |
| `python render/production_check.py` before calling a build “done” | Whether a Giphy read is *funny* |
| Schema-valid `storyboard.json` | Pacing inside a mockup scene |
| `python render/pipeline.py` so TTS + clip download + check + render are not skipped | Brand voice micro-choices in strategy.md |

**Operational rigidity was too loose** when only markdown agents ran and someone invoked `renderer.py` alone. **Creative rigidity is too tight** if JSON/schema work blocks iteration — use `--draft` on production check and iterate storyboard before locking approval.

### One-command materialization

After the human gate and post-approval markdown exist, build binaries and MP4 with:

```bash
python render/pipeline.py --episode episodes/ep008/episode.json
```

`--no-render` builds TTS + clips (+ optional Pollinations assets) only, for work-in-progress before approval. `--draft` relaxes b-roll file requirements in `production_check` only.

## Agent Roster

| Agent | File | Role |
|---|---|---|
| creative-director | `.claude/agents/creative-director.md` | Orchestrator — intake, dispatch, QA, package |
| strategy | `.claude/agents/strategy.md` | Hook angles, format, retention structure |
| script | `.claude/agents/script.md` | Word-for-word VO script in brand voice |
| storyboard | `.claude/agents/storyboard.md` | Timecoded scene list → storyboard.json |
| claim-review | `.claude/agents/claim-review.md` | Fact-check stats and superlatives |
| visual-brief | `.claude/agents/visual-brief.md` | Shot list, B-roll direction, text overlay specs |
| audio-direction | `.claude/agents/audio-direction.md` | Music direction, SFX cues, energy arc |
| tts-builder | `.claude/agents/tts-builder.md` | Kokoro TTS synthesis per VO segment |
| clip-sourcer | `.claude/agents/clip-sourcer.md` | Stock video procurement (Pexels / Pixabay) per scene |
| renderer | `.claude/agents/renderer.md` | MoviePy assembly → MP4 |
| distribution | `.claude/agents/distribution.md` | Captions, hashtags, thumbnails per platform |

## Visual Scene Types

| Type | Description |
|---|---|
| `card` | Dark background + LGTM label + headline + subtitle |
| `kinetic` | Animated number/phrase reveal for concepts, counts, and turns |
| `mockup` | Fake Slack, JIRA, calendar, or code artifact rendered as an image scene |
| `broll` | Stock clip + 0.58 dim + Ken Burns 1.07× zoom + optional lower-third scrim |
| `screen-recording` | Local video file + optional lower-third |
| `talking-head` | Local video clip |

## Hard Rules

1. **One renderer script** reads all episodes. New episode = new JSON, never new Python.
2. **One visual system.** Use the shared card, kinetic, mockup, b-roll, and video scene types. No one-off episode render code.
3. **Human approval gate is non-negotiable.** Renderer exits if `approved: false`.
4. **Agents write markdown. Tools write files.** Never mix creative logic and render logic.
5. **Graceful degradation:** missing B-roll clip → fall back to `card`, never hard-fail.
6. **No magic numbers in render code.** Everything flows from a `RenderConfig` built from episode JSON.
7. **Music bed ≤ 0.15 volume.** VO is the signal.
8. **Production check before render.** `python render/production_check.py --episode episodes/{id}/episode.json --require-audio` must pass before a render can be called final.
9. **No fallback-card final videos.** Missing B-roll must be sourced, replaced with `mockup`/`kinetic`, or explicitly marked as draft-only.

## Episode eval (know problems before export)

Automated checks cannot taste humor, but they **can** catch the issues that made ep008 feel wrong: missing clips, slow pacing, SFX mud, no music.

**Tier 0 — mandatory (machine, fast)**  
Run `render/production_check.py` **before** `renderer.py`:

- **FAIL:** missing b-roll files (unless `--allow-fallbacks` for an explicit draft), sparse visuals, bad timecodes, missing agent markdown, optional `--require-audio` for TTS on disk.
- **WARN (heuristic “eval”):** average scene length too high for punchy cuts, SFX cue density too high when `sfx_enabled` is true, no `episode.music.track_path`, b-roll scenes without a clip even when fallbacks are allowed.

Treat **WARN** like a review checklist: fix or consciously accept before calling the episode done.

**Tier 1 — optional (signal analysis)**  
After render: `ffprobe` duration/codecs; `ffmpeg astats` / `volumedetect` on the final mix to catch clipping or a second bed fighting the VO. Wire this as a small script later if needed.

**Tier 2 — optional (LLM-as-judge)**  
Export a **contact sheet** (`ffmpeg` every N seconds) plus `script.md` → one multimodal prompt with a fixed **rubric** (pacing, variety, legibility, audio description). Useful for “Fireship-ish?” scoring; costs money and is non-deterministic.

**Renderer:** set `render_config.sfx_enabled` to `false` to ship **VO (+ music only)** and ignore all `sfx` arrays in the storyboard for that episode.

## Directory Layout

```
lgtm/
├── .claude/
│   └── agents/              # Agent definitions (markdown)
├── assets/
│   └── fonts/               # Brand fonts (Consolas or fallback)
├── briefs/                  # One-line brief inputs
├── episodes/
│   └── {episode_id}/
│       ├── episode.json     # Episode config + approval gate
│       ├── storyboard.json  # Timecoded scene list (storyboard agent output)
│       ├── script.md        # Full VO script (script agent output)
│       ├── visual-brief.md  # Shot list and overlay specs (visual-brief agent output)
│       ├── audio-direction.md  # Music and SFX direction (audio-direction agent output)
│       ├── tts/             # Per-scene WAV files (tts-builder output)
│       ├── clips/           # Per-scene stock video (clip-sourcer output)
│       └── output/          # Final rendered MP4s
├── render/
│   └── renderer.py          # Single renderer — reads episode.json + storyboard.json
├── schemas/
│   ├── episode.schema.json
│   └── storyboard.schema.json
└── REQUIREMENTS.md
```

## Tech Stack

| Component | Choice |
|---|---|
| Render engine | Python + MoviePy |
| TTS | Kokoro-82M (local, existing venv) |
| Stock video | Pexels API + Pixabay API + Pollinations.ai (Generative) |
| Agent system | Claude Code `.claude/agents/` |
| Codex runner | `.codex/agents/` plus `scripts/codex-video.ps1` wrapping `codex exec` |
| Episode config | JSON (episode.schema.json) |
| Storyboard | JSON (storyboard.schema.json) |
| Distribution copy | Markdown per platform |

## Out of Scope (v1)

- 9:16 vertical crop
- Auto-caption burn-in
- Direct platform upload
- Web UI — CLI only
