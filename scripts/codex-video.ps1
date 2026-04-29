param(
    [ValidateSet(
        "creative-director",
        "strategy",
        "script",
        "storyboard",
        "claim-review",
        "visual-brief",
        "audio-direction",
        "image-generator",
        "tts-builder",
        "clip-sourcer",
        "renderer",
        "distribution"
    )]
    [string]$Agent = "creative-director",

    [string]$Episode,
    [string]$Brief,
    [string]$Model,
    [switch]$Search,
    [switch]$FullAuto,
    [switch]$Json,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptPath "..")
$agentPath = Join-Path $repoRoot ".codex\agents\$Agent.md"

if (-not (Test-Path $agentPath)) {
    throw "Codex agent not found: $agentPath"
}

$codex = Get-Command codex -ErrorAction SilentlyContinue
if (-not $codex) {
    throw "Codex CLI was not found on PATH."
}

$agentPrompt = Get-Content $agentPath -Raw
$episodeText = if ($Episode) { $Episode } else { "(not supplied)" }
$briefText = if ($Brief) { $Brief } else { "(not supplied)" }

$prompt = @"
You are running inside the LGTM repo through Codex CLI.

Selected LGTM agent: $Agent
Episode: $episodeText
Brief: $briefText

Follow these instructions:

$agentPrompt

Operational context:
- Working root is the repository root.
- Read AGENTS.md first, then the canonical contract named in the selected agent prompt.
- Use existing repo scripts before writing custom one-off logic.
- Keep all episode paths relative to episodes/{episode_id}/.
- Do not set approved: true. Stop and report when human approval is required.
- If an external API, network download, or unsafe command is needed, ask for approval through Codex CLI instead of bypassing the gate.

User request:
Run the selected LGTM agent for the supplied episode and brief. Complete the step end to end if the required inputs are present. If the next step is blocked by the human approval gate or missing credentials, stop with a concise status and exact next action.
"@

$argsList = @("exec", "-C", $repoRoot.Path)

if ($FullAuto) {
    $argsList += "--full-auto"
} else {
    $argsList += @("--sandbox", "workspace-write", "--ask-for-approval", "on-request")
}

if ($Search) {
    $argsList += "--search"
}

if ($Model) {
    $argsList += @("--model", $Model)
}

if ($Json) {
    $argsList += "--json"
}

$argsList += "-"

if ($DryRun) {
    $prompt
    exit 0
}

$prompt | & $codex.Source @argsList
exit $LASTEXITCODE
