"""Reusable visual style constants for neon/cyberpunk Wi-Fi 3D renders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

ColorHex = str
RGBTuple = Tuple[int, int, int]


@dataclass(frozen=True)
class GlowStyle:
    """Simple glow profile used across markers, traces, and labels."""

    core_color: ColorHex
    halo_color: ColorHex
    core_opacity: float
    halo_opacity: float
    halo_scale: float


BACKGROUND_DARK: ColorHex = "#020406"
GRID_LINE: ColorHex = "#103240"
TEXT_PRIMARY: ColorHex = "#B8F3FF"
TEXT_SECONDARY: ColorHex = "#77B9C8"

NEON_GREEN: ColorHex = "#39FF14"
NEON_CYAN: ColorHex = "#00F5FF"
NEON_MAGENTA: ColorHex = "#FF2BD6"
NEON_AMBER: ColorHex = "#FFD447"

PALETTE: Dict[str, ColorHex] = {
    "background": BACKGROUND_DARK,
    "grid": GRID_LINE,
    "text_primary": TEXT_PRIMARY,
    "text_secondary": TEXT_SECONDARY,
    "ap_node": NEON_CYAN,
    "ap_halo": NEON_GREEN,
    "coverage": NEON_MAGENTA,
    "receiver": NEON_AMBER,
}

AP_GLOW = GlowStyle(
    core_color=PALETTE["ap_node"],
    halo_color=PALETTE["ap_halo"],
    core_opacity=0.95,
    halo_opacity=0.26,
    halo_scale=1.9,
)

COVERAGE_GLOW = GlowStyle(
    core_color=PALETTE["coverage"],
    halo_color=PALETTE["coverage"],
    core_opacity=0.15,
    halo_opacity=0.06,
    halo_scale=1.25,
)

RECEIVER_GLOW = GlowStyle(
    core_color=PALETTE["receiver"],
    halo_color=NEON_GREEN,
    core_opacity=1.0,
    halo_opacity=0.4,
    halo_scale=2.1,
)


def hex_to_rgb(color: ColorHex) -> RGBTuple:
    """Convert #RRGGBB to an RGB tuple."""

    color = color.removeprefix("#")
    if len(color) != 6:
        msg = f"Expected #RRGGBB color format, got: {color!r}"
        raise ValueError(msg)
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def rgba(color: ColorHex, alpha: float) -> str:
    """Return CSS rgba() string from hex + alpha."""

    r, g, b = hex_to_rgb(color)
    return f"rgba({r}, {g}, {b}, {alpha:.3f})"
