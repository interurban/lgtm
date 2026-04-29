"""RenderConfig — single source of truth for visual/audio constants per episode."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_FONT_SEARCH = [
    Path("C:/Windows/Fonts/consolab.ttf"),
    Path("C:/Windows/Fonts/consola.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("assets/fonts/consolab.ttf"),
]


def resolve_font(name: str) -> str:
    candidate = Path(name)
    if candidate.exists():
        return str(candidate)
    for p in _FONT_SEARCH:
        if p.exists():
            return str(p)
    raise FileNotFoundError(
        f"Cannot resolve font '{name}'. Add the .ttf to assets/fonts/ or update _FONT_SEARCH."
    )


@dataclass
class RenderConfig:
    resolution: tuple[int, int]
    fps: int
    background_color: tuple[int, int, int]
    accent_color: tuple[int, int, int]
    font_headline: str
    font_size_headline: int
    font_size_subtitle: int
    font_size_kinetic: int
    lgtm_label_size: int
    music_volume: float
    sfx_enabled: bool
    sfx_volume: float
    broll_dim: float
    ken_burns_scale: float

    @classmethod
    def from_dict(cls, d: dict) -> "RenderConfig":
        return cls(
            resolution=tuple(d["resolution"]),
            fps=d["fps"],
            background_color=tuple(d["background_color"]),
            accent_color=tuple(d["accent_color"]),
            font_headline=resolve_font(d["font_headline"]),
            font_size_headline=d.get("font_size_headline", 96),
            font_size_subtitle=d.get("font_size_subtitle", 42),
            font_size_kinetic=d.get("font_size_kinetic", 360),
            lgtm_label_size=d.get("lgtm_label_size", 28),
            music_volume=min(d.get("music_volume", 0.10), 0.15),
            sfx_enabled=d.get("sfx_enabled", True),
            sfx_volume=d.get("sfx_volume", 0.55),
            broll_dim=d.get("broll_dim", 0.58),
            ken_burns_scale=d.get("ken_burns_scale", 1.07),
        )
