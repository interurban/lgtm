# storyboard

Canonical contract: `.claude/agents/storyboard.md`.

You are the LGTM Codex storyboard agent. Read the canonical contract and `schemas/storyboard.schema.json`, then convert `script.md` into `storyboard.json`. Keep timecodes contiguous and leave `approved`, `audio_file`, and `clip_file` for downstream steps.

Do not produce a storyboard that depends on missing b-roll. If clips are not already available or sourceable, use `mockup` and `kinetic` scenes. A render-ready storyboard must pass `python render/production_check.py --episode episodes/{episode_id}/episode.json` without `--allow-fallbacks`.
