"""PIL-direct text rendering. Bypasses MoviePy TextClip/FreeType glyph bugs."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip


def render_text_image(text: str, font_path: str, font_size: int, color) -> Image.Image:
    """Render text via PIL ImageDraw to a tight-bbox RGBA Image."""
    font = ImageFont.truetype(font_path, font_size)
    dummy = Image.new("RGBA", (1, 1))
    bbox = ImageDraw.Draw(dummy).textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0] + 4
    h = bbox[3] - bbox[1] + 4
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fill = (*color, 255) if isinstance(color, tuple) else color
    ImageDraw.Draw(img).text((-bbox[0] + 2, -bbox[1] + 2), text, font=font, fill=fill)
    return img


def text_clip(text: str, font_path: str, font_size: int, color, duration: float) -> ImageClip:
    img = render_text_image(text, font_path, font_size, color)
    return ImageClip(np.array(img), duration=duration)


def lgtm_label(font_path: str, label_size: int, duration: float) -> ImageClip:
    """LGTM watermark clip, positioned upper-left."""
    size = max(label_size, 36)
    img = render_text_image("LGTM", font_path, size, (255, 255, 255))
    return ImageClip(np.array(img), duration=duration).with_position((64, 36))
