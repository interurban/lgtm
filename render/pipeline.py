"""
LGTM episode build pipeline - one entry point after creative agents + human approval.

Runs (in order): optional Pollinations assets, Kokoro TTS, stock clip download,
production_check, MoviePy renderer.

Creative markdown (strategy, script, storyboard, etc.) still comes from agents; this tool
materializes binaries and the MP4 without skipping steps.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _episode_json_path(raw: str) -> Path:
    p = Path(raw).resolve()
    if p.is_dir():
        p = p / "episode.json"
    if p.name != "episode.json":
        p = p / "episode.json"
    return p


def _run(py: list[str], *, cwd: Path) -> int:
    print("+", " ".join(py), flush=True)
    r = subprocess.run(py, cwd=str(cwd))
    return r.returncode


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build episode: TTS + clips + production_check + render (MoviePy)."
    )
    ap.add_argument(
        "--episode",
        required=True,
        help="Path to episode.json or episodes/ep00N/",
    )
    ap.add_argument(
        "--draft",
        action="store_true",
        help="Allow b-roll fallbacks in production_check only; render still requires approved:true.",
    )
    ap.add_argument("--skip-tts", action="store_true")
    ap.add_argument("--skip-clips", action="store_true")
    ap.add_argument(
        "--skip-generated",
        action="store_true",
        help="Skip render/generate_assets.py (Pollinations stills to MP4).",
    )
    ap.add_argument(
        "--skip-production-check",
        action="store_true",
        help="Danger: skip production_check before render.",
    )
    ap.add_argument(
        "--no-render",
        action="store_true",
        help="Stop after TTS/clips/assets (no production_check, no MP4). Use before human approval.",
    )
    args = ap.parse_args()

    episode_json = _episode_json_path(args.episode)
    if not episode_json.exists():
        print(f"ERROR: {episode_json} not found", file=sys.stderr)
        return 1

    episode_data = json.loads(episode_json.read_text(encoding="utf-8"))
    want_render = not args.no_render
    if want_render and not episode_data.get("approved"):
        print(
            "ERROR: episode.json approved must be true before render. "
            "Use --no-render to only generate TTS/clips/assets, or set approved after storyboard review.",
            file=sys.stderr,
        )
        return 1

    py = sys.executable
    cwd = _REPO

    if not args.skip_generated:
        gen = _REPO / "render" / "generate_assets.py"
        if gen.exists():
            c = _run([py, str(gen), "--episode", str(episode_json)], cwd=cwd)
            if c != 0:
                return c

    if not args.skip_tts:
        c = _run([py, str(_REPO / "render" / "tts_build.py"), "--episode", str(episode_json)], cwd=cwd)
        if c != 0:
            return c

    if not args.skip_clips:
        c = _run([py, str(_REPO / "render" / "clip_fetch.py"), "--episode", str(episode_json)], cwd=cwd)
        if c != 0:
            return c

    if want_render and not args.skip_production_check:
        pc = [
            py,
            str(_REPO / "render" / "production_check.py"),
            "--episode",
            str(episode_json),
            "--require-audio",
        ]
        if args.draft:
            pc.append("--allow-fallbacks")
        c = _run(pc, cwd=cwd)
        if c != 0:
            return c

    if not want_render:
        print("[pipeline] stopped (--no-render): TTS/clips/assets only.")
        return 0

    c = _run([py, str(_REPO / "render" / "renderer.py"), "--episode", str(episode_json)], cwd=cwd)
    return c


if __name__ == "__main__":
    raise SystemExit(main())
