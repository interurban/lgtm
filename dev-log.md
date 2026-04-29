# Development Log

## Date
- 2026-04-28

## Timestamps
- Start: 2026-04-28T16:05:00Z
- End: 2026-04-28T16:42:00Z

## Work completed
- Hardened `render/renderer.py` to avoid chunk file locks and to improve FFmpeg error reporting.
- Added explicit cleanup for scene clips and master audio clips after rendering.
- Updated episode `ep006` storyboard from a single card to a three-scene structure:
  - `s01`: title card
  - `s02`: calendar/mockup kickoff meeting
  - `s03`: closing punchline card
- Synced `episodes/ep006/script.md`, `strategy.md`, `visual-brief.md`, and `audio-direction.md` with the expanded storyboard.
- Added `render/tts_builder.py` and `render/clip_sourcer.py` support scripts for TTS generation and clip assignment.
- Added `.vscode/tasks.json` and `requirements.txt` for reproducible workflow and dependency installation.

## Validation
- Verified Python syntax for `render/renderer.py`, `render/tts_builder.py`, and `render/clip_sourcer.py`.
- Confirmed TTS builder generated `episodes/ep006/tts/s01.wav`, `s02.wav`, and `s03.wav`.
- Confirmed renderer successfully produced `episodes/ep006/output/episode.mp4` with correct duration and audio/video streams.

## Notes
- The previous single-card episode output was caused by a placeholder storyboard rather than a renderer bug.
- The current pipeline is now usable from VS Code tasks and better suited for follow-up episode content work.

---

## Date
- 2026-04-28

## Timestamps
- Entry: 2026-04-28T18:55:22-07:00

## Work completed
- Added a Codex CLI agent framework under `.codex/agents/` and `scripts/codex-video.ps1` so LGTM episodes can be driven through Codex role prompts.
- Added `AGENTS.md` with Codex-specific project rules, pipeline order, and production quality gates.
- Added `render/production_check.py` to fail weak episode packages before render:
  - too many card-only scenes
  - too few real visual scenes
  - missing b-roll clips that would silently fall back to cards
  - missing required creative docs
  - missing VO audio when `--require-audio` is used
- Updated `schemas/storyboard.schema.json` to match renderer-supported scene types and fields, including `kinetic`, `mockup`, `burst`, captions, and `at`/`name` SFX cues.
- Updated README / requirements docs with the Codex workflow and "valid MP4 is not done" production gate.
- Rebuilt `episodes/ep007` ("DHH's Take on Codex") from a fallback-card render into a 10-scene package using cards, kinetic typography, and rendered mockups.
- Regenerated ep007 TTS and rendered `episodes/ep007/output/episode.mp4`.

## Validation
- `python render/production_check.py --episode episodes/ep007/episode.json --require-audio` passed.
- `render.qa.qa_check(Path("episodes/ep007/output/episode.mp4"), 41.6)` passed.
- Sampled rendered frames from ep007 and fixed visible mockup issues before finalizing.

## Notes
- The first ep007 render failed creatively because missing b-roll was allowed to degrade into fallback cards. The new production check makes that failure mode explicit and blocks final render unless the storyboard is rewritten or clips are actually sourced.
