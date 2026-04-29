import argparse
import json
import sys
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Simple clip sourcer for LGTM episodes.")
    parser.add_argument("--episode", required=True, help="Path to episode.json")
    args = parser.parse_args()

    episode_path = Path(args.episode)
    if not episode_path.exists():
        print(f"ERROR: episode.json not found: {episode_path}", file=sys.stderr)
        return 1

    episode = load_json(episode_path)
    episode_dir = episode_path.parent
    storyboard_path = episode_dir / episode.get("storyboard_path", "storyboard.json")
    if not storyboard_path.exists():
        print(f"ERROR: storyboard.json not found: {storyboard_path}", file=sys.stderr)
        return 1

    storyboard = load_json(storyboard_path)
    clips_dir = episode_dir / episode.get("paths", {}).get("clips_dir", "clips")
    clips_dir.mkdir(parents=True, exist_ok=True)

    changed = False
    summary = []

    for scene in storyboard.get("scenes", []):
        if scene.get("type") != "broll":
            continue

        visual = scene.get("visual", {})
        if visual.get("clip_file"):
            summary.append((scene["scene_id"], "skipped", "clip already assigned"))
            continue

        local_file = clips_dir / f"{scene['scene_id']}.mp4"
        if local_file.exists():
            visual["clip_file"] = str(Path(episode.get("paths", {}).get("clips_dir", "clips")) / local_file.name).replace("\\", "/")
            visual["clip_source"] = "local"
            summary.append((scene["scene_id"], "assigned", "local clip found"))
            changed = True
        else:
            summary.append((scene["scene_id"], "fallback", "no local clip found"))
            print(f"[info] {scene['scene_id']}: no clip found in {clips_dir}, leaving fallback card")

    if changed:
        write_json(storyboard_path, storyboard)
        print(f"Updated storyboard.json with {episode.get('paths', {}).get('clips_dir', 'clips')} assignments.")
    else:
        print("No clip assignments were changed.")

    print("\nClip sourcer summary:")
    for scene_id, status, note in summary:
        print(f"- {scene_id}: {status} ({note})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
