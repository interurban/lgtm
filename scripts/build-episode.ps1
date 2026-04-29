param(
    [Parameter(Mandatory = $true)]
    [string]$Episode,

    [switch]$Draft,
    [switch]$NoRender,
    [switch]$SkipTts,
    [switch]$SkipClips,
    [switch]$SkipGenerated,
    [switch]$SkipProductionCheck
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$py = (Get-Command python).Source
$argsList = @(
    "$repoRoot\render\pipeline.py",
    "--episode", $Episode
)
if ($Draft) { $argsList += "--draft" }
if ($NoRender) { $argsList += "--no-render" }
if ($SkipTts) { $argsList += "--skip-tts" }
if ($SkipClips) { $argsList += "--skip-clips" }
if ($SkipGenerated) { $argsList += "--skip-generated" }
if ($SkipProductionCheck) { $argsList += "--skip-production-check" }

& $py @argsList
exit $LASTEXITCODE
