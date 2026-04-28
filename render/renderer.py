"""
LGTM renderer. Reads episode.json + storyboard.json, assembles MP4.
One script, all episodes. New episode = new JSON, never new Python.

Usage:
    python render/renderer.py --episode episodes/ep001/episode.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
    concatenate_audioclips,
)
from moviepy.audio.AudioClip import AudioArrayClip

# Make this script runnable both as a module and as a top-level script
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).parent.parent))

from render.config import RenderConfig
from render.effects import apply_entry
from render.kinetic import make_kinetic_scene
from render.mockups import render_mockup
from render.sfx import SFX_DIR, SR as SFX_SR, load_sfx
from render.text import lgtm_label, text_clip


# ---------------------------------------------------------------------------
# Classic scene types
# ---------------------------------------------------------------------------

def make_background(cfg: RenderConfig, duration: float) -> ColorClip:
    return ColorClip(size=cfg.resolution, color=cfg.background_color, duration=duration)


def make_lower_third(lt: dict, cfg: RenderConfig, duration: float) -> list:
    layers = []
    w, h = cfg.resolution
    scrim_h = 110
    scrim_y = h - scrim_h

    scrim = ColorClip(
        size=(w, scrim_h), color=(0, 0, 0), duration=duration,
    ).with_opacity(0.65).with_position((0, scrim_y))
    layers.append(scrim)

    if lt.get("headline"):
        hl = text_clip(lt["headline"], cfg.font_headline, 28, cfg.accent_color, duration)
        layers.append(hl.with_position((72, scrim_y + 12)))
    if lt.get("subtitle"):
        sub = text_clip(lt["subtitle"], cfg.font_headline, 22, (255, 255, 255), duration)
        layers.append(sub.with_position((72, scrim_y + 54)))
    return layers


def make_card_scene(scene: dict, cfg: RenderConfig) -> CompositeVideoClip:
    duration = scene["duration"]
    visual = scene["visual"]
    headline = visual.get("headline", "")
    subtitle = visual.get("subtitle", "")

    layers = [make_background(cfg, duration)]
    w, h = cfg.resolution
    cy = h // 2

    if headline:
        # Larger headline if there's no subtitle (card has more breathing room)
        size = visual.get("headline_size") or (cfg.font_size_headline + 24 if not subtitle else cfg.font_size_headline)
        hl_y = cy - 40 if subtitle else cy - size // 2
        hl = text_clip(headline, cfg.font_headline, size, cfg.accent_color, duration)
        layers.append(hl.with_position(("center", hl_y)))

    if subtitle:
        sub = text_clip(subtitle, cfg.font_headline, cfg.font_size_subtitle, (255, 255, 255), duration)
        layers.append(sub.with_position(("center", cy + 60)))

    layers.append(lgtm_label(cfg.font_headline, cfg.lgtm_label_size, duration))
    return CompositeVideoClip(layers, size=cfg.resolution).with_duration(duration)


def loop_clip_to_duration(clip, duration: float):
    if clip.duration >= duration:
        return clip.subclipped(0, duration)
    times = int(np.ceil(duration / clip.duration))
    return concatenate_videoclips([clip] * times).subclipped(0, duration)


def make_broll_scene(scene: dict, cfg: RenderConfig, episode_dir: Path) -> CompositeVideoClip:
    duration = scene["duration"]
    visual = scene["visual"]
    clip_file = visual.get("clip_file")
    clip_path = episode_dir / clip_file if clip_file else None

    if not clip_path or not clip_path.exists():
        print(f"  [fallback] {scene['scene_id']}: clip not found, using card")
        fallback = visual.get("fallback", {})
        fake_scene = {"duration": duration, "visual": fallback, "scene_id": scene["scene_id"]}
        return make_card_scene(fake_scene, cfg)

    raw = VideoFileClip(str(clip_path))
    tw, th = cfg.resolution
    rw, rh = raw.size
    scale = max(tw / rw, th / rh)
    new_w, new_h = int(rw * scale), int(rh * scale)
    clip = raw.resized((new_w, new_h))

    x_off = (new_w - tw) // 2
    y_off = (new_h - th) // 2
    clip = clip.cropped(x1=x_off, y1=y_off, x2=x_off + tw, y2=y_off + th)
    clip = loop_clip_to_duration(clip, duration)

    dim_layer = ColorClip(
        size=cfg.resolution, color=(0, 0, 0), duration=duration,
    ).with_opacity(1.0 - cfg.broll_dim)

    layers = [clip, dim_layer]

    lt = visual.get("lower_third")
    if lt:
        layers.extend(make_lower_third(lt, cfg, duration))

    layers.append(lgtm_label(cfg.font_headline, cfg.lgtm_label_size, duration))
    return CompositeVideoClip(layers, size=cfg.resolution).with_duration(duration)


def make_screen_recording_scene(scene: dict, cfg: RenderConfig, episode_dir: Path) -> CompositeVideoClip:
    duration = scene["duration"]
    visual = scene["visual"]
    clip_path = episode_dir / visual["clip_file"]
    clip = VideoFileClip(str(clip_path)).subclipped(0, duration)
    layers = [clip]
    lt = visual.get("lower_third")
    if lt:
        layers.extend(make_lower_third(lt, cfg, duration))
    layers.append(lgtm_label(cfg.font_headline, cfg.lgtm_label_size, duration))
    return CompositeVideoClip(layers, size=cfg.resolution).with_duration(duration)


def make_talking_head_scene(scene: dict, cfg: RenderConfig, episode_dir: Path) -> CompositeVideoClip:
    return make_screen_recording_scene(scene, cfg, episode_dir)


def make_mockup_scene(scene: dict, cfg: RenderConfig) -> CompositeVideoClip:
    """Render a fake-asset scene (slack/jira/calendar). Optional Ken-Burns pan."""
    duration = scene["duration"]
    visual = scene["visual"]
    mockup_type = visual["mockup_type"]
    data = visual.get("mockup_data", {})

    img = render_mockup(mockup_type, data, cfg.font_headline, cfg.resolution)
    base = ImageClip(np.array(img), duration=duration)

    layers = [base]
    lt = visual.get("lower_third")
    if lt:
        layers.extend(make_lower_third(lt, cfg, duration))
    layers.append(lgtm_label(cfg.font_headline, cfg.lgtm_label_size, duration))
    return CompositeVideoClip(layers, size=cfg.resolution).with_duration(duration)


# ---------------------------------------------------------------------------
# Scene dispatch
# ---------------------------------------------------------------------------

def build_scene(scene: dict, cfg: RenderConfig, episode_dir: Path):
    scene_type = scene["type"]
    sid = scene["scene_id"]
    print(f"  building {sid} ({scene_type}, {scene['duration']:.1f}s)")

    if scene_type == "card":
        clip = make_card_scene(scene, cfg)
    elif scene_type == "broll":
        clip = make_broll_scene(scene, cfg, episode_dir)
    elif scene_type == "screen-recording":
        clip = make_screen_recording_scene(scene, cfg, episode_dir)
    elif scene_type == "talking-head":
        clip = make_talking_head_scene(scene, cfg, episode_dir)
    elif scene_type == "kinetic":
        clip = make_kinetic_scene(scene, cfg)
    elif scene_type == "mockup":
        clip = make_mockup_scene(scene, cfg)
    else:
        raise ValueError(f"Unknown scene type: {scene_type}")

    # Entry animation (default: fade for card/broll/mockup, none for kinetic which has its own anim)
    default_entry = "none" if scene_type == "kinetic" else "fade"
    entry = scene.get("enter", default_entry)
    clip = apply_entry(clip, entry)

    # Attach VO audio
    vo = scene.get("vo", {})
    audio_file = vo.get("audio_file")
    if audio_file:
        audio_path = episode_dir / audio_file
        if audio_path.exists():
            vo_audio = AudioFileClip(str(audio_path))
            if vo_audio.duration < scene["duration"]:
                silence_len = scene["duration"] - vo_audio.duration
                silence = AudioArrayClip(np.zeros((int(silence_len * 44100), 2)), fps=44100)
                vo_audio = concatenate_audioclips([vo_audio, silence])
            else:
                vo_audio = vo_audio.subclipped(0, scene["duration"])
            clip = clip.with_audio(vo_audio)
        else:
            print(f"  [warn] {sid}: audio_file set but not found: {audio_path}")

    return clip


# ---------------------------------------------------------------------------
# SFX track composition
# ---------------------------------------------------------------------------

def build_sfx_track(scenes: list[dict], total_duration: float, cfg: RenderConfig) -> AudioArrayClip | None:
    """Walk all scenes, collect sfx cues with absolute times, return mixed AudioArrayClip."""
    cues = []
    t = 0.0
    for s in scenes:
        for cue in s.get("sfx", []):
            cues.append({
                "at": t + cue["at"],
                "name": cue["name"],
                "vol": cue.get("vol", 1.0),
            })
        t += s["duration"]

    if not cues:
        return None

    # Stereo float buffer at 44.1kHz
    sr = SFX_SR
    n = int(total_duration * sr) + sr  # one second tail
    track = np.zeros((n, 2), dtype=np.float32)

    for cue in cues:
        try:
            sfx = load_sfx(cue["name"])
        except FileNotFoundError as e:
            print(f"  [warn] sfx not found: {cue['name']}")
            continue
        # Mono → stereo
        stereo = np.column_stack([sfx, sfx])
        start = int(cue["at"] * sr)
        end = start + len(stereo)
        if start >= n:
            continue
        if end > n:
            stereo = stereo[: n - start]
        track[start:start + len(stereo)] += stereo * cue["vol"] * cfg.sfx_volume

    # Soft clip
    track = np.tanh(track * 1.05)
    # Trim silence tail
    track = track[: int(total_duration * sr)]
    return AudioArrayClip(track, fps=sr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="LGTM renderer — one script, all episodes.")
    parser.add_argument("--episode", required=True, help="Path to episode.json")
    args = parser.parse_args()

    episode_path = Path(args.episode)
    if not episode_path.exists():
        print(f"ERROR: episode.json not found: {episode_path}", file=sys.stderr)
        return 1

    episode = json.loads(episode_path.read_text(encoding="utf-8"))
    episode_dir = episode_path.parent

    if not episode.get("approved"):
        print(
            f"ERROR: Episode {episode['episode_id']} is not approved. "
            "Set approved: true in episode.json before rendering.",
            file=sys.stderr,
        )
        return 1

    print(f"Rendering episode: {episode['episode_id']} — {episode['title']}")
    cfg = RenderConfig.from_dict(episode["render_config"])

    storyboard_path = episode_dir / episode.get("storyboard_path", "storyboard.json")
    if not storyboard_path.exists():
        print(f"ERROR: storyboard.json not found: {storyboard_path}", file=sys.stderr)
        return 1

    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
    scenes = storyboard["scenes"]

    missing_audio = []
    for s in scenes:
        vo = s.get("vo", {})
        if vo.get("text") and not vo.get("audio_file"):
            missing_audio.append(s["scene_id"])
    if missing_audio:
        print(f"ERROR: Missing audio_file for scenes: {missing_audio}", file=sys.stderr)
        return 1

    print(f"Building {len(scenes)} scenes...")
    scene_clips = [build_scene(s, cfg, episode_dir) for s in scenes]

    print("Concatenating scenes...")
    final = concatenate_videoclips(scene_clips, method="compose")

    # --- Audio composition: VO + SFX + music ---
    audio_layers = []
    if final.audio is not None:
        audio_layers.append(final.audio)

    sfx_track = build_sfx_track(scenes, final.duration, cfg)
    if sfx_track is not None:
        sfx_count = sum(len(s.get("sfx", [])) for s in scenes)
        print(f"Mixing {sfx_count} SFX cues...")
        audio_layers.append(sfx_track)

    music = episode.get("music", {})
    music_path = music.get("track_path")
    if music_path:
        music_file = episode_dir / music_path
        if music_file.exists():
            print(f"Mixing music bed: {music_path}")
            music_clip = AudioFileClip(str(music_file))
            vol = min(music.get("volume_override", cfg.music_volume), 0.15)
            music_clip = music_clip.with_volume_scaled(vol)
            fade_start = music.get("fade_out_start", final.duration - 2.0)
            fade_dur = min(2.0, max(0.5, final.duration - fade_start))
            music_clip = music_clip.subclipped(0, final.duration).audio_fadeout(fade_dur)
            audio_layers.append(music_clip)
        else:
            print(f"[warn] Music track not found: {music_file}, skipping.")

    if len(audio_layers) > 1:
        final = final.with_audio(CompositeAudioClip(audio_layers))
    elif len(audio_layers) == 1:
        final = final.with_audio(audio_layers[0])

    output_dir = episode_dir / episode.get("paths", {}).get("output_dir", "output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "episode.mp4"

    print(f"Writing {output_path} ({final.duration:.1f}s @ {cfg.fps}fps)...")
    final.write_videofile(
        str(output_path),
        fps=cfg.fps,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=str(output_dir / "temp_audio.m4a"),
        remove_temp=True,
        logger="bar",
    )

    print(f"\nDone. Output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
