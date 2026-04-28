"""
LGTM Distribution Script.
Reads episode.json and distribution.md, then uploads the final MP4 to a specified Slack channel.
Uses SLACK_BOT_TOKEN and SLACK_CHANNEL_ID.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path


def parse_distribution_md(dist_path: Path) -> dict:
    """Extracts caption and hashtags from distribution.md"""
    lines = dist_path.read_text(encoding="utf-8").splitlines()
    caption = ""
    hashtags = ""
    
    in_caption = False
    in_hashtags = False
    
    for line in lines:
        if line.startswith("## Caption"):
            in_caption = True
            in_hashtags = False
            continue
        elif line.startswith("## Hashtags"):
            in_caption = False
            in_hashtags = True
            continue
        elif line.startswith("## "):
            in_caption = False
            in_hashtags = False
            
        if in_caption and line.strip() and not line.startswith("{"):
            caption += line + "\n"
        elif in_hashtags and line.strip() and not line.startswith("{"):
            hashtags += line + "\n"
            
    return {
        "caption": caption.strip(),
        "hashtags": hashtags.strip()
    }


def post_to_slack(file_path: Path, message: str, execute: bool = False):
    """Uploads file and posts message to Slack. If execute is False, just logs."""
    if not execute:
        print("[DRY RUN] Would have posted to Slack:")
        print(f"--- Message ---\n{message}\n---------------")
        print(f"File: {file_path}")
        return

    token = os.environ.get("SLACK_BOT_TOKEN")
    channel = os.environ.get("SLACK_CHANNEL_ID")
    
    if not token or not channel:
        print("[WARN] SLACK_BOT_TOKEN or SLACK_CHANNEL_ID not set.")
        print(f"Would have posted to Slack:\n{message}\nFile: {file_path}")
        return

    # Simplified Slack files.upload using urllib and multipart/form-data
    import mimetypes
    import uuid
    
    url = "https://slack.com/api/files.upload"
    boundary = uuid.uuid4().hex
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    }
    
    # Build multipart payload
    body = bytearray()
    
    def add_field(name, value):
        body.extend(f"--{boundary}\r\n".encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode('utf-8'))
        body.extend(f"{value}\r\n".encode('utf-8'))

    add_field("channels", channel)
    add_field("initial_comment", message)
    
    filename = file_path.name
    mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    
    body.extend(f"--{boundary}\r\n".encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.format(filename).encode('utf-8'))
    body.extend(f'Content-Type: {mimetype}\r\n\r\n'.encode('utf-8'))
    
    with open(file_path, "rb") as f:
        body.extend(f.read())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode('utf-8'))
    
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get("ok"):
                print("Successfully posted to Slack.")
            else:
                print(f"Slack API error: {res.get('error')}")
    except urllib.error.URLError as e:
        print(f"ERROR: Failed to reach Slack API: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", required=True, help="Path to episode.json")
    parser.add_argument("--execute", action="store_true", help="Actually post to Slack instead of dry-run")
    args = parser.parse_args()

    episode_path = Path(args.episode)
    if not episode_path.exists():
        print(f"ERROR: episode.json not found: {episode_path}")
        return 1

    episode_dir = episode_path.parent
    episode = json.loads(episode_path.read_text(encoding="utf-8"))
    
    dist_path = episode_dir / "distribution.md"
    if not dist_path.exists():
        print(f"ERROR: distribution.md not found for episode {episode.get('episode_id')}")
        return 1
        
    output_dir = episode_dir / episode.get("paths", {}).get("output_dir", "output")
    mp4_path = output_dir / "episode.mp4"
    
    if not mp4_path.exists():
        print(f"ERROR: rendered output not found at {mp4_path}")
        return 1

    dist_data = parse_distribution_md(dist_path)
    message = f"{dist_data['caption']}\n\n{dist_data['hashtags']}"
    
    print(f"Distributing episode {episode.get('episode_id')}...")
    post_to_slack(mp4_path, message, execute=args.execute)
    
    if args.execute:
        # Update episode.json status only if we actually posted
        episode["status"] = "distributed"
        episode_path.write_text(json.dumps(episode, indent=2), encoding="utf-8")
        print("Updated episode.json status to 'distributed'.")
    else:
        print("Dry run complete. Use --execute to actually distribute.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
