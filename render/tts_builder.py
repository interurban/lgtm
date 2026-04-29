import argparse
import contextlib
import json
import subprocess
import sys
import wave
from pathlib import Path


DEFAULT_KOKORO_PY = Path(
    "C:/Users/James/OneDrive/dev/warp-test/v1/local_tts/venv_kokoro/Scripts/python.exe"
)
DEFAULT_KOKORO_SCRIPT = Path(
    "C:/Users/James/OneDrive/dev/warp-test/v1/local_tts/kokoro_synth.py"
)


def get_wav_duration(path: Path) -> float:
    with contextlib.closing(wave.open(str(path), "rb")) as reader:
        frames = reader.getnframes()
        rate = reader.getframerate()
        return frames / float(rate)


def run_kokoro(kokoro_py: Path, kokoro_script: Path, text: str, out_path: Path) -> None:
    cmd = [
        str(kokoro_py),
        str(kokoro_script),
        "--text",
        text,
        "--out",
        str(out_path),
        "--voice",
        "am_michael",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Kokoro TTS failed for {out_path.name}: {result.stderr.strip() or result.stdout.strip()}"
        )


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate TTS audio for an LGTM episode.")
    parser.add_argument("--episode", required=True, help="Path to episode.json")
    parser.add_argument("--kokoro-py", default=str(DEFAULT_KOKORO_PY), help="Path to Kokoro Python executable")
    parser.add_argument("--kokoro-script", default=str(DEFAULT_KOKORO_SCRIPT), help="Path to Kokoro synthesis script")
    args = parser.parse_args()

    episode_path = Path(args.episode)
    if not episode_path.exists():
        print(f"ERROR: episode.json not found: {episode_path}", file=sys.stderr)
        return 1

    storyboard_path = episode_path.parent / "storyboard.json"
    if not storyboard_path.exists():
        print(f"ERROR: storyboard.json not found: {storyboard_path}", file=sys.stderr)
        return 1

    kokoro_py = Path(args.kokoro_py)
    kokoro_script = Path(args.kokoro_script)
    if not kokoro_py.exists():
        print(f"ERROR: Kokoro python not found: {kokoro_py}", file=sys.stderr)
        return 1
    if not kokoro_script.exists():
        print(f"ERROR: Kokoro synth script not found: {kokoro_script}", file=sys.stderr)
        return 1

    episode = load_json(episode_path)
    storyboard = load_json(storyboard_path)
    tts_dir = episode.get("paths", {}).get("tts_dir", "tts")
    tts_path = episode_path.parent / tts_dir
    tts_path.mkdir(parents=True, exist_ok=True)

    scenes = storyboard.get("scenes", [])
    if not scenes:
        print("ERROR: No scenes found in storyboard.", file=sys.stderr)
        return 1

    changed = False
    summary = []

    for scene in scenes:
        vo = scene.get("vo", {})
        text = vo.get("text", "")
        audio_file = vo.get("audio_file")
        if not text:
            summary.append((scene["scene_id"], "skipped", "silent scene"))
            continue
        if audio_file:
            summary.append((scene["scene_id"], "skipped", "already has audio_file"))
            continue

        out_filename = f"{scene['scene_id']}.wav"
        out_path = tts_path / out_filename
        try:
            print(f"Synthesizing {scene['scene_id']} to {out_path}...")
            run_kokoro(kokoro_py, kokoro_script, text, out_path)
            if not out_path.exists() or out_path.stat().st_size == 0:
                raise RuntimeError("Generated WAV is empty")
            duration = get_wav_duration(out_path)
            vo["audio_file"] = str(Path(tts_dir) / out_filename).replace("\\", "/")
            vo["duration_hint"] = round(duration, 2)
            scene["vo"] = vo
            changed = True
            summary.append((scene["scene_id"], "generated", f"{duration:.2f}s"))
            write_json(storyboard_path, storyboard)
        except Exception as exc:
            summary.append((scene["scene_id"], "error", str(exc)))
            print(f"ERROR: {exc}", file=sys.stderr)

    print("\nTTS builder summary:")
    for scene_id, status, note in summary:
        print(f"- {scene_id}: {status} ({note})")

    if not changed:
        print("No new TTS assets were generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
