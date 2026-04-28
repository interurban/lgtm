"""
Remotion-based renderer for LGTM episodes.

Renders the video via Remotion (React/CSS motion graphics) and mixes audio
(music bed + VO + SFX) in Python, then combines with FFmpeg.

Usage:
    python render/remotion_renderer.py --episode episodes/ep003/episode.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np
from moviepy import AudioFileClip
from moviepy.audio.AudioClip import AudioArrayClip

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).parent.parent))

from render.config import RenderConfig
from render.music import generate_music_bed
from render.sfx import SR as SFX_SR, load_sfx

REMOTION_DIR = Path(__file__).parent / "remotion"
REMOTION_CLI = REMOTION_DIR / "node_modules" / ".bin" / "remotion.cmd"
ENTRY = "src/index.ts"
COMPOSITION_ID = "Episode"


def build_audio_track(
    scenes: list[dict],
    total_duration: float,
    episode_dir: Path,
    cfg: RenderConfig,
) -> AudioArrayClip | None:
    """Mix music bed + VO + SFX into a single stereo audio track."""
    sr = SFX_SR  # 44100
    n = int(total_duration * sr) + sr
    track = np.zeros((n, 2), dtype=np.float32)

    # Music bed layer (generated ambient drone)
    if cfg.music_volume > 0:
        music = generate_music_bed(total_duration + 1.0, volume=cfg.music_volume)
        music_n = min(len(music), n)
        track[:music_n] += music[:music_n]

    # VO layer: place each scene's WAV at its start time
    vo_missing = []
    for scene in scenes:
        vo = scene.get("vo", {})
        audio_file = vo.get("audio_file")
        if not audio_file:
            continue
        audio_path = episode_dir / audio_file
        if not audio_path.exists():
            vo_missing.append(str(audio_path))
            continue
        clip = AudioFileClip(str(audio_path))
        arr = clip.to_soundarray(fps=sr)
        clip.close()
        if arr.ndim == 1:
            arr = np.column_stack([arr, arr])
        start = int(scene["start"] * sr)
        if start >= n:
            continue
        end = start + len(arr)
        if end > n:
            arr = arr[: n - start]
        track[start : start + len(arr)] += arr * 0.90

    if vo_missing:
        print(f"  [warn] {len(vo_missing)} VO file(s) not found — scenes will be silent:")
        for p in vo_missing:
            print(f"    {p}")

    # SFX layer
    for scene in scenes:
        scene_start = scene["start"]
        for cue in scene.get("sfx", []):
            abs_t = scene_start + cue["at"]
            try:
                sfx = load_sfx(cue["name"])
            except FileNotFoundError:
                print(f"  [warn] sfx not found: {cue['name']}")
                continue
            stereo = np.column_stack([sfx, sfx])
            start = int(abs_t * sr)
            end = start + len(stereo)
            if start >= n:
                continue
            if end > n:
                stereo = stereo[: n - start]
            vol = cue.get("vol", 1.0) * cfg.sfx_volume
            track[start : start + len(stereo)] += stereo * vol

    # Soft clip + trim
    track = np.tanh(track * 1.05)
    track = track[: int(total_duration * sr)]

    if np.max(np.abs(track)) < 1e-6:
        return None
    return AudioArrayClip(track, fps=sr)


def _prep_scenes_for_remotion(
    scenes: list[dict],
    episode: dict,
    public_mockups: Path,
) -> list[dict]:
    """
    Pre-render mockup scenes to PNG. On failure, degrades the scene to a
    fallback card so Remotion never receives an undefined mockup_image.
    """
    from render.mockups import render_mockup

    font_path = episode["render_config"]["font_headline"]
    resolution = tuple(episode["render_config"]["resolution"])
    result = []

    for scene in scenes:
        s = {**scene}

        if s.get("type") != "mockup":
            result.append(s)
            continue

        visual = {**s.get("visual", {})}
        mockup_type = visual.get("mockup_type")
        mockup_data = visual.get("mockup_data", {})

        if not mockup_type:
            result.append(s)
            continue

        try:
            img = render_mockup(mockup_type, mockup_data, font_path, resolution)
            png_name = f"{s['scene_id']}.png"
            img.save(str(public_mockups / png_name))
            visual["mockup_image"] = f"mockups/{png_name}"
            s["visual"] = visual
            print(f"  Pre-rendered mockup: {png_name}")
        except Exception as exc:
            print(f"  [warn] mockup render failed for {s['scene_id']}: {exc} — falling back to card")
            fallback = visual.get("fallback") or {
                "scene_type": "card",
                "headline": mockup_type.upper(),
                "subtitle": s["scene_id"],
            }
            s["type"] = "card"
            s["visual"] = fallback

        result.append(s)

    return result


def render(episode_path: Path) -> int:
    episode = json.loads(episode_path.read_text(encoding="utf-8"))
    episode_dir = episode_path.parent

    if not episode.get("approved"):
        print("ERROR: episode not approved", file=sys.stderr)
        return 1

    cfg = RenderConfig.from_dict(episode["render_config"])
    storyboard_path = episode_dir / episode.get("storyboard_path", "storyboard.json")
    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
    scenes = storyboard["scenes"]
    total_duration = storyboard["total_duration"]

    output_dir = episode_dir / episode.get("paths", {}).get("output_dir", "output")
    output_dir.mkdir(parents=True, exist_ok=True)
    silent_path = output_dir / "video_silent.mp4"
    audio_path = output_dir / "audio_mix.wav"
    output_path = output_dir / "episode.mp4"

    # --- Step 1: stage broll clips into Remotion public/ ---
    public_clips = REMOTION_DIR / "public" / "clips"
    public_clips.mkdir(parents=True, exist_ok=True)
    for scene in scenes:
        if scene.get("type") == "broll":
            clip_file = scene.get("visual", {}).get("clip_file")
            if clip_file:
                src = episode_dir / clip_file
                if src.exists():
                    shutil.copy2(str(src), str(public_clips / src.name))
                    print(f"  Staged clip: {src.name}")

    # --- Step 1b: pre-render mockup PNGs (with card fallback on failure) ---
    public_mockups = REMOTION_DIR / "public" / "mockups"
    public_mockups.mkdir(parents=True, exist_ok=True)
    scenes_for_props = _prep_scenes_for_remotion(scenes, episode, public_mockups)

    # --- Step 2: Remotion render (silent video) ---
    props = {"scenes": scenes_for_props, "total_duration": total_duration}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(props, f)
        props_file = f.name

    print(f"Rendering {len(scenes)} scenes via Remotion ({total_duration:.1f}s)...")
    result = subprocess.run(  # noqa: S603
        [
            str(REMOTION_CLI),
            "render",
            ENTRY,
            COMPOSITION_ID,
            f"--props={props_file}",
            f"--output={silent_path.resolve()}",
            "--log=verbose",
            "--concurrency=4",
        ],
        cwd=str(REMOTION_DIR),
        capture_output=False,
    )
    Path(props_file).unlink(missing_ok=True)
    if public_clips.exists():
        shutil.rmtree(str(public_clips))
    if public_mockups.exists():
        shutil.rmtree(str(public_mockups))

    if result.returncode != 0:
        print("ERROR: Remotion render failed", file=sys.stderr)
        return 1

    # --- Step 3: build audio track (music bed + VO + SFX) ---
    print("Building audio track (music + VO + SFX)...")
    audio_track = build_audio_track(scenes, total_duration, episode_dir, cfg)

    if audio_track is not None:
        arr = audio_track.to_soundarray(fps=SFX_SR)
        arr_int16 = (arr * 32767).clip(-32768, 32767).astype(np.int16)
        with wave.open(str(audio_path), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(SFX_SR)
            wf.writeframes(arr_int16.tobytes())
        has_audio = True
    else:
        has_audio = False

    # --- Step 4: combine video + audio with FFmpeg ---
    print("Combining video + audio...")
    if has_audio:
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", str(silent_path),
            "-i", str(audio_path),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            str(output_path),
        ]
    else:
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", str(silent_path),
            "-c:v", "copy",
            str(output_path),
        ]

    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: FFmpeg failed:\n{result.stderr}", file=sys.stderr)
        shutil.copy(str(silent_path), str(output_path))
        print("Falling back to silent video.")

    # --- Step 5: QA ---
    from render.qa import qa_check
    qa_ok = qa_check(output_path, total_duration)

    print(f"\nDone. Output: {output_path}")
    return 0 if qa_ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", required=True)
    args = parser.parse_args()
    return render(Path(args.episode))


if __name__ == "__main__":
    raise SystemExit(main())
