"""Synthesize Kokoro TTS for every voiced scene and set vo.audio_file in storyboard.json."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_KOKORO_PY = Path(
    r"C:\Users\James\OneDrive\dev\warp-test\v1\local_tts\venv_kokoro\Scripts\python.exe"
)
DEFAULT_KOKORO_SYNTH = Path(r"C:\Users\James\OneDrive\dev\warp-test\v1\local_tts\kokoro_synth.py")


def _kokoro_paths(repo_root: Path) -> tuple[Path, Path]:
    py = Path(os.environ.get("LGTM_KOKORO_PYTHON", str(DEFAULT_KOKORO_PY)))
    synth = Path(os.environ.get("LGTM_KOKORO_SYNTH", str(DEFAULT_KOKORO_SYNTH)))
    return py, synth


def build_tts(episode_json: Path, repo_root: Path) -> int:
    episode_dir = episode_json.parent
    episode = json.loads(episode_json.read_text(encoding="utf-8"))
    sb_path = episode_dir / episode.get("storyboard_path", "storyboard.json")
    storyboard = json.loads(sb_path.read_text(encoding="utf-8"))
    tts_rel = episode.get("paths", {}).get("tts_dir", "tts")
    tts_dir = episode_dir / tts_rel
    tts_dir.mkdir(parents=True, exist_ok=True)

    py, synth = _kokoro_paths(repo_root)
    if not py.exists():
        print(f"ERROR: Kokoro python not found: {py}", file=sys.stderr)
        print("Set LGTM_KOKORO_PYTHON or install Kokoro per CLAUDE.md.", file=sys.stderr)
        return 1
    if not synth.exists():
        print(f"ERROR: kokoro_synth.py not found: {synth}", file=sys.stderr)
        print("Set LGTM_KOKORO_SYNTH.", file=sys.stderr)
        return 1

    changed = False
    for scene in storyboard.get("scenes", []):
        vo = scene.get("vo") or {}
        text = (vo.get("text") or "").strip()
        if not text:
            continue
        sid = scene["scene_id"]
        out_wav = tts_dir / f"{sid}.wav"
        rel = f"{tts_rel.rstrip('/')}/{sid}.wav".replace("\\", "/")
        print(f"[tts] {sid}", flush=True)
        r = subprocess.run(
            [str(py), str(synth), "--text", text, "--out", str(out_wav), "--voice", "am_michael"],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            print(f"ERROR: Kokoro failed for {sid}: {r.stderr or r.stdout}", file=sys.stderr)
            return 1
        vo["audio_file"] = rel
        changed = True

    if changed:
        sb_path.write_text(json.dumps(storyboard, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("[tts] done")
    return 0


def repo_root_from_episode_json(episode_json: Path) -> Path:
    p = episode_json.resolve()
    if p.parent.parent.name == "episodes" and (p.parents[2] / "render").is_dir():
        return p.parents[2]
    raise FileNotFoundError(
        f"Expected episodes/<id>/episode.json under repo root; got {p}. "
        "Run from LGTM repo layout."
    )


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(description="Build Kokoro WAVs for an episode and patch storyboard.json.")
    p.add_argument("--episode", required=True, help="Path to episode.json")
    args = p.parse_args()
    ep = Path(args.episode)
    try:
        repo_root = repo_root_from_episode_json(ep)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return build_tts(ep, repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
