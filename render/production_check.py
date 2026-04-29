"""Production quality gate for LGTM episodes.

This is deliberately stricter than render QA. QA proves the MP4 is valid.
Production check proves the episode is ready to render.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


MIN_SCENES = 6
MIN_VISUAL_SCENES = 3
MAX_CARD_RATIO = 0.60
# Heuristic “punchy short-form” pacing (Fireship-ish). Warn only — not a hard fail.
WARN_AVG_SCENE_DURATION_S = 3.2
WARN_SFX_CUES_PER_MINUTE = 12.0


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _visual_scene_count(scenes: list[dict]) -> int:
    count = 0
    for scene in scenes:
        scene_type = scene.get("type")
        visual = scene.get("visual", {})
        if scene_type in {"kinetic", "mockup", "screen-recording", "talking-head"}:
            count += 1
        elif scene_type == "broll" and visual.get("clip_file"):
            count += 1
    return count


def check_episode(
    episode_path: Path, allow_fallbacks: bool = False, require_audio: bool = False
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not episode_path.exists():
        return [f"episode.json not found: {episode_path}"], []

    episode = _load(episode_path)
    episode_dir = episode_path.parent
    storyboard_path = episode_dir / episode.get("storyboard_path", "storyboard.json")
    if not storyboard_path.exists():
        return [f"storyboard.json not found: {storyboard_path}"], []

    storyboard = _load(storyboard_path)
    scenes = storyboard.get("scenes", [])
    if len(scenes) < MIN_SCENES:
        errors.append(f"storyboard has {len(scenes)} scenes; minimum is {MIN_SCENES}")

    expected = 0.0
    for scene in scenes:
        scene_id = scene.get("scene_id", "<unknown>")
        start = float(scene.get("start", -1))
        duration = float(scene.get("duration", 0))
        if abs(start - expected) > 0.01:
            errors.append(f"{scene_id} starts at {start:.2f}; expected {expected:.2f}")
        expected = round(expected + duration, 2)

        if not scene.get("visual"):
            errors.append(f"{scene_id} has no visual block")

        vo = scene.get("vo", {})
        if require_audio and vo.get("text"):
            audio_file = vo.get("audio_file")
            if not audio_file:
                errors.append(f"{scene_id} has VO but no audio_file")
            elif not (episode_dir / audio_file).exists():
                errors.append(f"{scene_id} audio_file missing on disk: {audio_file}")

    total = float(storyboard.get("total_duration", 0))
    if abs(total - expected) > 0.01:
        errors.append(f"total_duration is {total:.2f}; expected {expected:.2f}")

    card_count = sum(1 for scene in scenes if scene.get("type") == "card")
    card_ratio = card_count / max(1, len(scenes))
    if card_ratio > MAX_CARD_RATIO:
        errors.append(
            f"too many card scenes: {card_count}/{len(scenes)} "
            f"({card_ratio:.0%}); maximum is {MAX_CARD_RATIO:.0%}"
        )

    visual_count = _visual_scene_count(scenes)
    if visual_count < MIN_VISUAL_SCENES:
        errors.append(
            f"not enough rendered visual scenes: {visual_count}; "
            f"minimum is {MIN_VISUAL_SCENES} from kinetic/mockup/real b-roll/video"
        )

    missing_broll = []
    for scene in scenes:
        if scene.get("type") != "broll":
            continue
        visual = scene.get("visual", {})
        clip_file = visual.get("clip_file")
        if not clip_file or not (episode_dir / clip_file).exists():
            missing_broll.append(scene.get("scene_id", "<unknown>"))

    if missing_broll and not allow_fallbacks:
        errors.append(
            "b-roll scenes would fall back to cards: "
            + ", ".join(missing_broll)
            + ". Source clips, convert them to mockups/kinetics, or pass --allow-fallbacks for a draft render."
        )

    if not (episode_dir / episode.get("paths", {}).get("script", "script.md")).exists():
        errors.append("script.md is missing")
    if not (episode_dir / episode.get("paths", {}).get("visual_brief", "visual-brief.md")).exists():
        errors.append("visual-brief.md is missing")
    if not (episode_dir / episode.get("paths", {}).get("audio_direction", "audio-direction.md")).exists():
        errors.append("audio-direction.md is missing")
    if not (episode_dir / "claim-review.md").exists():
        errors.append("claim-review.md is missing")

    # --- Heuristic warnings (eval tier: “would this feel flat / noisy?”) ---
    n = len(scenes)
    total_d = sum(float(s.get("duration", 0)) for s in scenes)
    if n:
        avg_d = total_d / n
        if avg_d > WARN_AVG_SCENE_DURATION_S:
            warnings.append(
                f"average scene duration is {avg_d:.2f}s (>{WARN_AVG_SCENE_DURATION_S}s); "
                "short-form punch usually wants faster cuts unless mockups need dwell time"
            )

    sfx_total = sum(len(s.get("sfx", [])) for s in scenes)
    if total_d > 0 and sfx_total:
        per_min = sfx_total / (total_d / 60.0)
        rc = episode.get("render_config") or {}
        if rc.get("sfx_enabled", True) and per_min > WARN_SFX_CUES_PER_MINUTE:
            warnings.append(
                f"SFX density is {sfx_total} cues in {total_d:.1f}s ({per_min:.1f}/min); "
                f"typical comfortable ceiling is ~{WARN_SFX_CUES_PER_MINUTE:.0f}/min when mixed under VO"
            )

    music = episode.get("music") or {}
    if not music.get("track_path"):
        warnings.append(
            "no episode.music.track_path - final mix is VO (+SFX if enabled) only; "
            "Fireship pace usually carries a low music bed"
        )

    broll_scenes = [s for s in scenes if s.get("type") == "broll"]
    if broll_scenes:
        sourced = 0
        for s in broll_scenes:
            cf = (s.get("visual") or {}).get("clip_file")
            if cf and (episode_dir / cf).exists():
                sourced += 1
        if sourced < len(broll_scenes):
            warnings.append(
                f"{len(broll_scenes) - sourced}/{len(broll_scenes)} b-roll scene(s) lack a real clip on disk "
                "(renderer will fall back to cards unless you source clips)"
            )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail fast on weak LGTM episode packages.")
    parser.add_argument("--episode", required=True, help="Path to episode.json")
    parser.add_argument("--allow-fallbacks", action="store_true", help="Allow b-roll scenes without clips.")
    parser.add_argument("--require-audio", action="store_true", help="Require VO audio files to exist.")
    parser.add_argument(
        "--quiet-warnings",
        action="store_true",
        help="Do not print heuristic warnings (errors still print).",
    )
    args = parser.parse_args()

    errors, warnings = check_episode(Path(args.episode), args.allow_fallbacks, args.require_audio)
    if errors:
        print("[production-check] FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("[production-check] PASS")
    if warnings and not args.quiet_warnings:
        print("[production-check] WARN (heuristic eval - review before calling it done)")
        for w in warnings:
            print(f"- {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

