"""
LGTM Generative Asset Script.
Reads storyboard.json and queries OpenAI DALL-E 3 for any scene with 'clip_source' == 'generated'.
Writes a static MP4 to the clips directory.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from moviepy import ImageClip


def generate_image(prompt: str, output_image_path: Path):
    """Call Pollinations.ai to generate the image (free, no API key), download it to output_image_path."""
    # Pollinations.ai generates images via a simple GET request with the prompt in the URL.
    import urllib.parse
    
    # URL encode the prompt
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1920&height=1080&nologo=true"
    
    # We add a User-Agent just in case
    headers = {
        "User-Agent": "LGTM-Studio/1.0"
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        print(f"  -> Requesting image from pollinations.ai...")
        with urllib.request.urlopen(req) as response:
            with open(output_image_path, "wb") as f:
                f.write(response.read())
            print(f"  -> Generated and downloaded to {output_image_path.name}")
    except urllib.error.URLError as e:
        print(f"ERROR: Failed to generate image from Pollinations.ai: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", required=True, help="Path to episode.json")
    args = parser.parse_args()

    episode_path = Path(args.episode)
    if not episode_path.exists():
        print(f"ERROR: episode.json not found: {episode_path}")
        return 1

    episode_dir = episode_path.parent
    episode = json.loads(episode_path.read_text(encoding="utf-8"))
    
    storyboard_path = episode_dir / episode.get("storyboard_path", "storyboard.json")
    if not storyboard_path.exists():
        print(f"ERROR: storyboard.json not found: {storyboard_path}")
        return 1

    storyboard = json.loads(storyboard_path.read_text(encoding="utf-8"))
    clips_dir = episode_dir / "clips"
    clips_dir.mkdir(exist_ok=True)

    generated_count = 0
    for scene in storyboard.get("scenes", []):
        visual = scene.get("visual", {})
        if visual.get("clip_source") == "generated" and visual.get("generator_prompt"):
            prompt = visual["generator_prompt"]
            scene_id = scene["scene_id"]
            clip_file = f"{scene_id}.mp4"
            clip_path = clips_dir / clip_file
            
            if clip_path.exists():
                print(f"Skipping {scene_id}: {clip_file} already exists.")
                continue

            print(f"Generating image for {scene_id}...")
            print(f"  Prompt: {prompt}")
            
            temp_img = clips_dir / f"temp_{scene_id}.jpg"
            generate_image(prompt, temp_img)
            
            # Convert static image to a 10s video for the renderer to use as b-roll
            print(f"  -> Converting to video {clip_file}...")
            try:
                img_clip = ImageClip(str(temp_img)).with_duration(10.0)
                img_clip.write_videofile(str(clip_path), fps=24, logger=None)
                img_clip.close()
                temp_img.unlink() # Cleanup
                
                # Update visual block with the path
                visual["clip_file"] = f"clips/{clip_file}"
                generated_count += 1
            except Exception as e:
                print(f"ERROR: Failed to convert image to video: {e}")

    if generated_count > 0:
        storyboard_path.write_text(json.dumps(storyboard, indent=2), encoding="utf-8")
        print(f"\nGenerated {generated_count} assets and updated storyboard.json.")
    else:
        print("\nNo generated assets needed or all already exist.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
