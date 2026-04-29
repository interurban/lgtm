"""
Download b-roll clips for LGTM episodes (Giphy, Pixabay, Pexels) per episode.json clip_sources.

Updates storyboard.json with clip_file, clip_id, clip_url, clip_source.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from render.env_util import load_dotenv


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _http_get_json(url: str, headers: dict | None = None, timeout: float = 60.0) -> dict:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "LGTM-clip-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _http_download(url: str, dest: Path, timeout: float = 120.0) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "LGTM-clip-fetch/1.0"})
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        dest.write_bytes(r.read())


def _giphy_pick_mp4(item: dict) -> tuple[str | None, str | None]:
    """Return (mp4_url, giphy_page_url)."""
    images = item.get("images") or {}
    for size in ("hd", "downsized_medium", "fixed_width", "original"):
        block = images.get(size) or {}
        u = block.get("mp4")
        if u:
            page = item.get("url") or f"https://giphy.com/gifs/{item.get('id', '')}"
            return u, page
    return None, None


def try_giphy(api_key: str, query: str, dest_mp4: Path, tmp_dir: Path, scene_id: str) -> dict | None:
    q = urllib.parse.quote(query)
    url = f"https://api.giphy.com/v1/gifs/search?api_key={api_key}&q={q}&limit=10&rating=g&lang=en"
    try:
        data = _http_get_json(url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  [giphy] search error: {e}", file=sys.stderr)
        return None
    for item in data.get("data", [])[:8]:
        gid = item.get("id") or "x"
        mp4_url, page_url = _giphy_pick_mp4(item)
        if not mp4_url:
            continue
        pre = tmp_dir / f"pre_{scene_id}_{gid}.mp4"
        try:
            _http_download(mp4_url, pre)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"  [giphy] download fail {gid}: {e}", file=sys.stderr)
            continue
        if pre.stat().st_size < 2048:
            pre.unlink(missing_ok=True)
            continue
        shutil.copy2(pre, dest_mp4)
        pre.unlink(missing_ok=True)
        return {
            "clip_source": "giphy",
            "clip_id": gid,
            "clip_url": page_url or "",
        }
    return None


def try_pixabay(api_key: str, query: str, dest_mp4: Path, tmp_dir: Path, scene_id: str) -> dict | None:
    q = urllib.parse.quote(query)
    url = f"https://pixabay.com/api/videos/?key={api_key}&q={q}&video_type=film&orientation=horizontal&per_page=8"
    try:
        data = _http_get_json(url)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  [pixabay] search error: {e}", file=sys.stderr)
        return None
    for hit in data.get("hits", [])[:6]:
        vids = hit.get("videos") or {}
        block = vids.get("large") or vids.get("medium") or vids.get("small")
        if not block:
            continue
        mp4_url = block.get("url")
        if not mp4_url:
            continue
        pid = str(hit.get("id", scene_id))
        pre = tmp_dir / f"pre_{scene_id}_px_{pid}.mp4"
        try:
            _http_download(mp4_url, pre)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"  [pixabay] download fail {pid}: {e}", file=sys.stderr)
            continue
        if pre.stat().st_size < 2048:
            pre.unlink(missing_ok=True)
            continue
        shutil.copy2(pre, dest_mp4)
        pre.unlink(missing_ok=True)
        return {"clip_source": "pixabay", "clip_id": pid, "clip_url": str(hit.get("pageURL", ""))}
    return None


def try_pexels(api_key: str, query: str, dest_mp4: Path, tmp_dir: Path, scene_id: str) -> dict | None:
    q = urllib.parse.quote(query)
    url = f"https://api.pexels.com/videos/search?query={q}&per_page=8&orientation=landscape&size=medium"
    headers = {"Authorization": api_key, "User-Agent": "LGTM-clip-fetch/1.0"}
    try:
        data = _http_get_json(url, headers=headers)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  [pexels] search error: {e}", file=sys.stderr)
        return None
    for vid in data.get("videos", [])[:6]:
        best = None
        for vf in vid.get("video_files") or []:
            if vf.get("quality") == "hd" and int(vf.get("width", 0)) >= 1280:
                best = vf
                break
        if not best:
            for vf in vid.get("video_files") or []:
                if vf.get("file_type") == "video/mp4":
                    best = vf
                    break
        if not best:
            continue
        mp4_url = best.get("link")
        if not mp4_url:
            continue
        pid = str(vid.get("id", scene_id))
        pre = tmp_dir / f"pre_{scene_id}_pex_{pid}.mp4"
        try:
            _http_download(mp4_url, pre)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"  [pexels] download fail {pid}: {e}", file=sys.stderr)
            continue
        if pre.stat().st_size < 2048:
            pre.unlink(missing_ok=True)
            continue
        shutil.copy2(pre, dest_mp4)
        pre.unlink(missing_ok=True)
        return {"clip_source": "pexels", "clip_id": pid, "clip_url": vid.get("url", "") or ""}
    return None


def fetch_clips(episode_json: Path, repo_root: Path) -> int:
    env_path = repo_root / ".env"
    env = load_dotenv(env_path)

    episode = load_json(episode_json)
    episode_dir = episode_json.parent
    storyboard_path = episode_dir / episode.get("storyboard_path", "storyboard.json")
    storyboard = load_json(storyboard_path)
    clips_rel = episode.get("paths", {}).get("clips_dir", "clips")
    clips_dir = episode_dir / clips_rel
    clips_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = clips_dir
    sources = episode.get("clip_sources") or ["giphy"]

    changed = False
    for scene in storyboard.get("scenes", []):
        if scene.get("type") != "broll":
            continue
        visual = scene.setdefault("visual", {})
        if visual.get("clip_file") and (episode_dir / visual["clip_file"]).exists():
            print(f"[clips] {scene['scene_id']}: already have {visual['clip_file']}")
            continue
        q = visual.get("clip_query") or "empty office fluorescent"
        dest = clips_dir / f"{scene['scene_id']}.mp4"
        meta = None
        for src in sources:
            if src == "giphy":
                key = env.get("GIPHY_API_KEY", "")
                if not key:
                    print("  [giphy] skip: GIPHY_API_KEY missing in .env")
                    continue
                print(f"[clips] {scene['scene_id']}: giphy search {q!r}")
                meta = try_giphy(key, q, dest, tmp_dir, scene["scene_id"])
            elif src == "pixabay":
                key = env.get("PIXABAY_API_KEY", "")
                if not key:
                    print("  [pixabay] skip: PIXABAY_API_KEY missing")
                    continue
                print(f"[clips] {scene['scene_id']}: pixabay search {q!r}")
                meta = try_pixabay(key, q, dest, tmp_dir, scene["scene_id"])
            elif src == "pexels":
                key = env.get("PEXELS_API_KEY", "")
                if not key:
                    print("  [pexels] skip: PEXELS_API_KEY missing")
                    continue
                print(f"[clips] {scene['scene_id']}: pexels search {q!r}")
                meta = try_pexels(key, q, dest, tmp_dir, scene["scene_id"])
            else:
                print(f"  [clips] unknown source {src!r}, skip")
                continue
            if meta:
                break
        if meta and dest.exists():
            rel = f"{clips_rel.rstrip('/')}/{dest.name}".replace("\\", "/")
            visual["clip_file"] = rel
            visual["clip_id"] = meta["clip_id"]
            visual["clip_url"] = meta["clip_url"]
            visual["clip_source"] = meta["clip_source"]
            changed = True
            print(f"[clips] {scene['scene_id']}: wrote {rel}")
        else:
            print(f"[clips] {scene['scene_id']}: no clip sourced (renderer will use fallback card)")

    # cleanup stray previews
    for p in clips_dir.glob("pre_*"):
        try:
            p.unlink()
        except OSError:
            pass

    if changed:
        write_json(storyboard_path, storyboard)
    print("[clips] done")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Download stock clips for b-roll scenes.")
    parser.add_argument("--episode", required=True, help="Path to episode.json")
    args = parser.parse_args()
    ep = Path(args.episode).resolve()
    if ep.parent.parent.name != "episodes":
        print("ERROR: episode.json must live under episodes/<id>/", file=sys.stderr)
        return 1
    repo_root = ep.parents[2]
    if not (repo_root / "render").is_dir():
        print("ERROR: repo root not found", file=sys.stderr)
        return 1
    return fetch_clips(ep, repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
