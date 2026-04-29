# Create an LGTM Video with Codex CLI

This workflow uses `scripts/codex-video.ps1`, which wraps `codex exec` with an LGTM role prompt.

## Start a New Episode

```powershell
.\scripts\codex-video.ps1 -Agent creative-director -Episode ep007 -Brief "One-line episode brief"
```

The orchestrator should create or complete:

- `episodes/ep007/episode.json`
- `episodes/ep007/strategy.md`
- `episodes/ep007/script.md`
- `episodes/ep007/storyboard.json`

Codex must stop before render work until a human sets `"approved": true`.

Before approval or render, the package must pass:

```powershell
python render/production_check.py --episode episodes/ep007/episode.json
```

After TTS, require audio too:

```powershell
python render/production_check.py --episode episodes/ep007/episode.json --require-audio
```

## Run Individual Steps

```powershell
.\scripts\codex-video.ps1 -Agent strategy -Episode ep007 -Brief "..."
.\scripts\codex-video.ps1 -Agent script -Episode ep007
.\scripts\codex-video.ps1 -Agent storyboard -Episode ep007
.\scripts\codex-video.ps1 -Agent claim-review -Episode ep007
.\scripts\codex-video.ps1 -Agent visual-brief -Episode ep007
.\scripts\codex-video.ps1 -Agent audio-direction -Episode ep007
.\scripts\codex-video.ps1 -Agent tts-builder -Episode ep007
.\scripts\codex-video.ps1 -Agent clip-sourcer -Episode ep007
.\scripts\codex-video.ps1 -Agent renderer -Episode ep007
.\scripts\codex-video.ps1 -Agent distribution -Episode ep007
```

## Useful Flags

- `-Search` passes `--search` to Codex for current web lookup.
- `-Model gpt-5.4` selects a model explicitly.
- `-FullAuto` uses Codex CLI `--full-auto`.
- `-Json` emits Codex JSONL events.
- `-DryRun` prints the assembled prompt without starting Codex.
