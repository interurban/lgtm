"""Entry animations and clip transforms."""

from __future__ import annotations

import numpy as np
from PIL import Image


def fade_in(clip, duration: float = 0.18):
    """Linear opacity ramp from 0 to 1 over `duration` seconds."""
    if duration <= 0:
        return clip
    d = min(duration, clip.duration * 0.5)

    def transform(get_frame, t):
        frame = get_frame(t)
        if t >= d:
            return frame
        return (frame.astype(np.float32) * (t / d)).astype(np.uint8)

    return clip.transform(transform, keep_duration=True)


def scale_in(clip, duration: float = 0.30, start_scale: float = 0.6):
    """Scale-in from start_scale to 1.0 with ease-out cubic. Center-anchored."""
    if duration <= 0:
        return clip
    d = min(duration, clip.duration * 0.6)
    w, h = clip.size

    def transform(get_frame, t):
        frame = get_frame(t)
        if t >= d:
            return frame
        progress = t / d
        eased = 1 - (1 - progress) ** 3
        scale = start_scale + (1.0 - start_scale) * eased
        if scale >= 0.995:
            return frame
        new_w = max(2, int(w * scale))
        new_h = max(2, int(h * scale))
        img = Image.fromarray(frame).resize((new_w, new_h), Image.LANCZOS)
        canvas = Image.new("RGB", (w, h), (0, 0, 0))
        canvas.paste(img, ((w - new_w) // 2, (h - new_h) // 2))
        opacity = min(1.0, progress * 2.0)
        return (np.array(canvas).astype(np.float32) * opacity).astype(np.uint8)

    return clip.transform(transform, keep_duration=True)


def apply_entry(clip, kind: str | None):
    """Dispatch an entry animation by name."""
    if not kind or kind == "none":
        return clip
    if kind == "fade":
        return fade_in(clip, 0.22)
    if kind == "scale":
        return scale_in(clip, 0.28)
    if kind == "snap":
        return scale_in(clip, 0.16, start_scale=0.85)
    return clip
