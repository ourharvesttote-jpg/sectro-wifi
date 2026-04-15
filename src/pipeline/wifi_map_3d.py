"""Simple 3D Wi-Fi map data sink used by the map builder pipeline."""

from __future__ import annotations

from typing import Dict, Mapping, Tuple

Vector3 = Tuple[float, float, float]


def render_wifi_map(ap_positions: Mapping[str, Vector3], metadata: Mapping[str, object] | None = None) -> Dict[str, object]:
    """Return a visualization payload for downstream rendering layers."""
    return {
        "ap_positions": dict(ap_positions),
        "metadata": dict(metadata or {}),
    }
