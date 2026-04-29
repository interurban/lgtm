# Codex Agents for LGTM

These files are role prompts for `codex exec`. They intentionally reuse the canonical agent contracts in `.claude/agents/` so Claude, Antigravity, and Codex stay aligned.

Run an agent:

```powershell
.\scripts\codex-video.ps1 -Agent strategy -Episode ep007 -Brief "An AI pilot committee schedules a meeting to decide if meetings can be automated"
```

Run the orchestrator:

```powershell
.\scripts\codex-video.ps1 -Agent creative-director -Episode ep007 -Brief "..."
```

Render an approved episode:

```powershell
.\scripts\codex-video.ps1 -Agent renderer -Episode ep007
```

Available roles:

- `creative-director`
- `strategy`
- `script`
- `storyboard`
- `claim-review`
- `visual-brief`
- `audio-direction`
- `image-generator`
- `tts-builder`
- `clip-sourcer`
- `renderer`
- `distribution`

