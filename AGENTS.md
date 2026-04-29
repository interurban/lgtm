# LGTM Codex Project Instructions

LGTM is a short-form video pipeline. A one-line brief becomes an episode package under `episodes/{episode_id}/`, then the render tools produce `output/episode.mp4`.

## Pipeline

Use this order unless the user asks for a narrower step:

1. `strategy` writes `strategy.md` from the brief.
2. `script` writes word-for-word VO in `script.md`.
3. `storyboard` writes validated `storyboard.json`.
4. Human approval gate: do not set `approved: true` yourself.
5. `claim-review`, `visual-brief`, and `audio-direction` can run after approval.
6. `tts-builder` and `clip-sourcer` can run after storyboard approval artifacts exist.
7. Run `python render/production_check.py --episode episodes/{episode_id}/episode.json` before rendering. Fix failures instead of rendering through them.
8. `renderer` runs the selected renderer and writes `output/episode.mp4`.
9. `distribution` writes publishing copy.

## Hard Rules

- New episode equals new JSON and markdown under `episodes/{episode_id}/`; do not create new render code for a single episode.
- Preserve the human gate. Rendering requires `episode.json` to have `"approved": true`; never bypass or silently change it.
- Agents write markdown and JSON. Tools synthesize audio, source clips, and render media.
- Keep paths in episode files relative to the episode directory.
- Missing b-roll should degrade to a fallback card, not a hard failure.
- Music bed volume must stay at or below `0.15`.
- LGTM label must remain upper-left on every frame.
- Card copy is one headline and one subtitle.
- A valid MP4 is not a completed episode. Completion requires a production-check pass, render QA pass, and a creative package with real visual variety.
- Do not let b-roll fallbacks become the episode. If clips are unavailable, rewrite those scenes as `mockup` or `kinetic` scenes before render.
- Use `kinetic` for numbers, concepts, and step changes; use `mockup` for fake Slack/JIRA/calendar/code artifacts; use cards only for hook, thesis, and button beats.
- Do not render if more than 60% of scenes are cards or fewer than 3 scenes are real visual scenes (`kinetic`, `mockup`, real b-roll, screen recording, or talking head).

## Codex Agent Files

Codex role prompts live in `.codex/agents/`. Each role points at the canonical project agent contract in `.claude/agents/` and adds Codex CLI execution rules. Use `scripts/codex-video.ps1` to invoke them.

## Quality Gate

Before TTS or render, run:

```powershell
python render/production_check.py --episode episodes/{episode_id}/episode.json
```

After TTS, run it again with audio validation:

```powershell
python render/production_check.py --episode episodes/{episode_id}/episode.json --require-audio
```

Only pass `--allow-fallbacks` for a draft render that is explicitly not final.
