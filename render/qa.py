"""Post-render QA validation for LGTM episodes."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def qa_check(output_path: Path, expected_duration: float) -> bool:
    """
    Verify the rendered MP4 has a live video stream and a real audio stream.
    Returns True if all checks pass.
    """
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(output_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  [qa] FAIL: ffprobe could not read {output_path}", file=sys.stderr)
        return False

    try:
        streams = json.loads(result.stdout).get("streams", [])
    except json.JSONDecodeError:
        print("  [qa] FAIL: could not parse ffprobe output", file=sys.stderr)
        return False

    video = [s for s in streams if s.get("codec_type") == "video"]
    audio = [s for s in streams if s.get("codec_type") == "audio"]

    ok = True

    if not video:
        print("  [qa] FAIL: no video stream", file=sys.stderr)
        ok = False
    else:
        actual = float(video[0].get("duration", 0))
        if abs(actual - expected_duration) > 0.5:
            print(
                f"  [qa] FAIL: duration {actual:.1f}s vs expected {expected_duration:.1f}s",
                file=sys.stderr,
            )
            ok = False

    if not audio:
        print("  [qa] FAIL: no audio stream", file=sys.stderr)
        ok = False
    else:
        bit_rate = int(audio[0].get("bit_rate", 0))
        if bit_rate < 10_000:
            print(
                f"  [qa] FAIL: audio bit_rate {bit_rate} bps — stream is silent or missing",
                file=sys.stderr,
            )
            ok = False

    if ok:
        print("  [qa] PASS")
    return ok
