"""Kinetic typography scenes — animated number/word reveals."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ColorClip, CompositeVideoClip, ImageClip, VideoClip

from render.config import RenderConfig
from render.text import lgtm_label, render_text_image


def _bounce_scale(t: float, in_dur: float = 0.32) -> float:
    """Overshoot bounce: 0 → 1.12 → 1.0 over in_dur seconds, then hold at 1.0."""
    if t >= in_dur:
        return 1.0
    p = t / in_dur
    if p < 0.7:
        # ease-out cubic to 1.12
        eased = 1 - (1 - p / 0.7) ** 3
        return 0.4 + (1.12 - 0.4) * eased
    # settle from 1.12 back to 1.0
    settle_p = (p - 0.7) / 0.3
    return 1.12 - 0.12 * settle_p


def make_kinetic_scene(scene: dict, cfg: RenderConfig) -> CompositeVideoClip:
    """Big animated number/value with optional label below.

    visual:
      value: str — the big text (e.g. "18", "0", "$2.4M")
      label: str — optional smaller line below
      color: "accent" | "white" | "red" — defaults to accent
      label_color: "accent" | "white" — defaults to white
    """
    duration = scene["duration"]
    visual = scene["visual"]
    value = visual["value"]
    label = visual.get("label", "")
    color_name = visual.get("color", "accent")
    label_color_name = visual.get("label_color", "white")

    color_map = {
        "accent": cfg.accent_color,
        "white": (255, 255, 255),
        "red": (220, 60, 60),
    }
    value_color = color_map.get(color_name, cfg.accent_color)
    label_color = color_map.get(label_color_name, (255, 255, 255))

    w, h = cfg.resolution
    bg = ColorClip(size=cfg.resolution, color=cfg.background_color, duration=duration)

    # Pre-render value at full size to a tight bbox image
    value_img = render_text_image(value, cfg.font_headline, cfg.font_size_kinetic, value_color)
    vw, vh = value_img.size
    value_arr = np.array(value_img)

    # Animated value: scale from 0.4 → 1.12 → 1.0 (bounce), centered slightly above middle
    def value_frame(t):
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        scale = _bounce_scale(t)
        new_w = max(4, int(vw * scale))
        new_h = max(4, int(vh * scale))
        scaled = Image.fromarray(value_arr).resize((new_w, new_h), Image.LANCZOS)
        # Center horizontally, slightly above mid-height
        cx = w // 2 - new_w // 2
        cy = (h // 2 - new_h // 2) - 40
        canvas.paste(scaled, (cx, cy), scaled)
        return np.array(canvas)

    def value_mask(t):
        # opacity ramp: 0→1 in first 0.15s
        opacity = 1.0 if t > 0.15 else (t / 0.15)
        canvas = Image.new("L", (w, h), 0)
        scale = _bounce_scale(t)
        new_w = max(4, int(vw * scale))
        new_h = max(4, int(vh * scale))
        alpha = value_arr[:, :, 3]
        scaled = Image.fromarray(alpha).resize((new_w, new_h), Image.LANCZOS)
        cx = w // 2 - new_w // 2
        cy = (h // 2 - new_h // 2) - 40
        canvas.paste(Image.eval(scaled, lambda v: int(v * opacity)), (cx, cy))
        return np.array(canvas).astype(np.float32) / 255.0

    value_clip = VideoClip(value_frame, duration=duration).with_mask(
        VideoClip(value_mask, duration=duration, is_mask=True)
    )

    layers = [bg, value_clip]

    # Label fades in after the bounce, below the number
    if label:
        label_img = render_text_image(label, cfg.font_headline, cfg.font_size_subtitle, label_color)
        lw, lh = label_img.size
        label_arr = np.array(label_img)
        label_y = h // 2 + vh // 2 + 10

        def label_frame(t):
            canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            opacity = 0.0 if t < 0.30 else min(1.0, (t - 0.30) / 0.25)
            if opacity <= 0:
                return np.array(canvas)
            faded = Image.eval(Image.fromarray(label_arr), lambda v: v)  # passthrough
            cx = w // 2 - lw // 2
            cy = label_y
            # apply opacity via separate alpha channel manipulation
            arr = label_arr.copy()
            arr[:, :, 3] = (arr[:, :, 3].astype(np.float32) * opacity).astype(np.uint8)
            scaled_img = Image.fromarray(arr)
            canvas.paste(scaled_img, (cx, cy), scaled_img)
            return np.array(canvas)

        def label_mask(t):
            opacity = 0.0 if t < 0.30 else min(1.0, (t - 0.30) / 0.25)
            canvas = Image.new("L", (w, h), 0)
            if opacity <= 0:
                return np.zeros((h, w), dtype=np.float32)
            alpha = label_arr[:, :, 3]
            cx = w // 2 - lw // 2
            cy = label_y
            scaled_alpha = Image.eval(Image.fromarray(alpha), lambda v: int(v * opacity))
            canvas.paste(scaled_alpha, (cx, cy))
            return np.array(canvas).astype(np.float32) / 255.0

        label_clip = VideoClip(label_frame, duration=duration).with_mask(
            VideoClip(label_mask, duration=duration, is_mask=True)
        )
        layers.append(label_clip)

    layers.append(lgtm_label(cfg.font_headline, cfg.lgtm_label_size, duration))
    return CompositeVideoClip(layers, size=cfg.resolution).with_duration(duration)
