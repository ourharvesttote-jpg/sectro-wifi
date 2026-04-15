"""3D neon-style Wi-Fi map renderer using Plotly.

The renderer visualizes access points (APs), estimated coverage spheres,
and a fixed receiver origin marker at the coordinate-frame origin.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
import plotly.graph_objects as go

from .style_matrix import AP_GLOW, COVERAGE_GLOW, PALETTE, RECEIVER_GLOW, rgba


@dataclass(frozen=True)
class AccessPointEstimate:
    """AP estimate used for visualization."""

    ssid: str
    x: float
    y: float
    z: float
    rssi_dbm: float
    distance_m: float


def _scale_sizes(rssi_values: Sequence[float], min_size: float = 7.0, max_size: float = 26.0) -> np.ndarray:
    """Map RSSI values to marker sizes (stronger RSSI -> larger marker)."""

    rssi = np.asarray(rssi_values, dtype=float)
    if rssi.size == 0:
        return np.asarray([], dtype=float)

    lo, hi = np.min(rssi), np.max(rssi)
    if np.isclose(lo, hi):
        return np.full_like(rssi, (min_size + max_size) / 2)

    # RSSI is typically negative; larger value (e.g., -45) is stronger than -80.
    norm = (rssi - lo) / (hi - lo)
    return min_size + norm * (max_size - min_size)


def _sphere_mesh(center: tuple[float, float, float], radius: float, u_steps: int = 20, v_steps: int = 18):
    """Generate x/y/z mesh arrays for a sphere."""

    u = np.linspace(0, 2 * np.pi, u_steps)
    v = np.linspace(0, np.pi, v_steps)
    x0, y0, z0 = center

    x = x0 + radius * np.outer(np.cos(u), np.sin(v))
    y = y0 + radius * np.outer(np.sin(u), np.sin(v))
    z = z0 + radius * np.outer(np.ones_like(u), np.cos(v))
    return x, y, z


def _sanitize_aps(access_points: Iterable[AccessPointEstimate]) -> list[AccessPointEstimate]:
    """Normalize AP inputs to finite coordinates and positive radii."""

    sanitized: list[AccessPointEstimate] = []
    for ap in access_points:
        if not np.isfinite([ap.x, ap.y, ap.z, ap.rssi_dbm, ap.distance_m]).all():
            continue
        sanitized.append(
            AccessPointEstimate(
                ssid=ap.ssid,
                x=float(ap.x),
                y=float(ap.y),
                z=float(ap.z),
                rssi_dbm=float(ap.rssi_dbm),
                distance_m=max(float(ap.distance_m), 0.01),
            )
        )
    return sanitized


def _axis_ranges(aps: Sequence[AccessPointEstimate], pad: float = 1.5) -> dict[str, list[float]]:
    """Return equalized axis ranges so spheres are not visually distorted."""

    if not aps:
        return {"x": [-8, 8], "y": [-8, 8], "z": [-2, 8]}

    points = np.array([[ap.x, ap.y, ap.z] for ap in aps] + [[0.0, 0.0, 0.0]], dtype=float)
    radii = np.array([ap.distance_m for ap in aps] + [0.0], dtype=float)

    mins = points.min(axis=0) - radii.max() - pad
    maxs = points.max(axis=0) + radii.max() + pad

    spans = maxs - mins
    half = max(spans) / 2.0
    center = (mins + maxs) / 2.0

    return {
        "x": [center[0] - half, center[0] + half],
        "y": [center[1] - half, center[1] + half],
        "z": [center[2] - half, center[2] + half],
    }


def render_wifi_scene(
    access_points: Iterable[AccessPointEstimate],
    title: str = "3D Wi-Fi Coverage Map",
    ascii_overlay: bool = True,
    distance_model_label: str = "distance model",
) -> go.Figure:
    """Render APs and coverage in a neon-styled 3D scene."""

    aps = _sanitize_aps(access_points)
    fig = go.Figure()

    if aps:
        xs = np.asarray([ap.x for ap in aps], dtype=float)
        ys = np.asarray([ap.y for ap in aps], dtype=float)
        zs = np.asarray([ap.z for ap in aps], dtype=float)
        rssi = np.asarray([ap.rssi_dbm for ap in aps], dtype=float)
        labels = [
            f"<b>{ap.ssid}</b><br>RSSI: {ap.rssi_dbm:.1f} dBm<br>Estimated distance: {ap.distance_m:.2f} m<br>(x, y, z)=({ap.x:.2f}, {ap.y:.2f}, {ap.z:.2f})"
            for ap in aps
        ]

        sizes = _scale_sizes(rssi)

        # Coverage spheres (translucent shells)
        for ap in aps:
            sx, sy, sz = _sphere_mesh((ap.x, ap.y, ap.z), ap.distance_m)
            fig.add_trace(
                go.Surface(
                    x=sx,
                    y=sy,
                    z=sz,
                    opacity=COVERAGE_GLOW.core_opacity,
                    colorscale=[[0, COVERAGE_GLOW.core_color], [1, COVERAGE_GLOW.core_color]],
                    showscale=False,
                    hoverinfo="skip",
                    name=f"Coverage: {ap.ssid}",
                    showlegend=False,
                )
            )

        # AP halo for glow effect
        fig.add_trace(
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="markers",
                marker=dict(
                    size=sizes * AP_GLOW.halo_scale,
                    color=rgba(AP_GLOW.halo_color, AP_GLOW.halo_opacity),
                    symbol="circle",
                    line=dict(width=0),
                ),
                hoverinfo="skip",
                name="AP Glow",
                showlegend=False,
            )
        )

        # AP core nodes
        fig.add_trace(
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="markers+text",
                marker=dict(
                    size=sizes,
                    color=rgba(AP_GLOW.core_color, AP_GLOW.core_opacity),
                    symbol="circle",
                    line=dict(color=rgba(PALETTE["ap_halo"], 0.85), width=1),
                ),
                text=[ap.ssid for ap in aps],
                textposition="top center",
                textfont=dict(color=PALETTE["text_primary"], size=11),
                hovertemplate="%{customdata}<extra></extra>",
                customdata=labels,
                name="Access Points (node size ∝ RSSI)",
            )
        )

    # Receiver origin marker at (0, 0, 0)
    fig.add_trace(
        go.Scatter3d(
            x=[0.0],
            y=[0.0],
            z=[0.0],
            mode="markers+text",
            marker=dict(
                size=11,
                color=rgba(RECEIVER_GLOW.core_color, RECEIVER_GLOW.core_opacity),
                symbol="diamond",
                line=dict(color=rgba(RECEIVER_GLOW.halo_color, 0.8), width=3),
            ),
            text=["Receiver Origin"],
            textposition="bottom center",
            textfont=dict(color=PALETTE["receiver"], size=12),
            hovertemplate="Receiver Origin<br>(0, 0, 0)<extra></extra>",
            name="Receiver Origin",
        )
    )

    # Optional ASCII-ish backdrop hints.
    annotations = []
    if ascii_overlay:
        annotations.append(
            dict(
                text="+----+  WIFI-MATRIX  +----+", x=0.02, y=0.98, xref="paper", yref="paper",
                font=dict(color=PALETTE["text_secondary"], family="Courier New, monospace", size=12),
                showarrow=False, align="left",
            )
        )
        annotations.append(
            dict(
                text="| x →, y →, z ↑ |", x=0.02, y=0.94, xref="paper", yref="paper",
                font=dict(color=PALETTE["text_secondary"], family="Courier New, monospace", size=11),
                showarrow=False, align="left",
            )
        )

    legend_text = (
        "<b>Legend</b><br>"
        "• AP nodes: larger node = stronger RSSI (less negative dBm)<br>"
        f"• Translucent spheres: AP radius estimated from {distance_model_label}<br>"
        "• Receiver Origin: fixed coordinate-frame reference at (0, 0, 0)"
    )
    annotations.append(
        dict(
            text=legend_text,
            x=0.99,
            y=0.03,
            xref="paper",
            yref="paper",
            xanchor="right",
            yanchor="bottom",
            align="left",
            bgcolor=rgba(PALETTE["background"], 0.65),
            bordercolor=rgba(PALETTE["grid"], 0.85),
            borderwidth=1,
            font=dict(color=PALETTE["text_primary"], size=11),
            showarrow=False,
        )
    )

    axis_ranges = _axis_ranges(aps)

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(color=PALETTE["text_primary"], size=20)),
        paper_bgcolor=PALETTE["background"],
        plot_bgcolor=PALETTE["background"],
        legend=dict(
            bgcolor=rgba(PALETTE["background"], 0.4),
            bordercolor=rgba(PALETTE["grid"], 0.9),
            borderwidth=1,
            font=dict(color=PALETTE["text_primary"]),
        ),
        margin=dict(l=0, r=0, b=0, t=54),
        scene=dict(
            bgcolor=PALETTE["background"],
            aspectmode="cube",
            xaxis=dict(
                title="X (m)",
                range=axis_ranges["x"],
                showbackground=True,
                backgroundcolor=rgba(PALETTE["background"], 0.92),
                gridcolor=rgba(PALETTE["grid"], 0.9),
                zerolinecolor=rgba(PALETTE["ap_halo"], 0.45),
                color=PALETTE["text_secondary"],
            ),
            yaxis=dict(
                title="Y (m)",
                range=axis_ranges["y"],
                showbackground=True,
                backgroundcolor=rgba(PALETTE["background"], 0.92),
                gridcolor=rgba(PALETTE["grid"], 0.9),
                zerolinecolor=rgba(PALETTE["ap_halo"], 0.45),
                color=PALETTE["text_secondary"],
            ),
            zaxis=dict(
                title="Z (m)",
                range=axis_ranges["z"],
                showbackground=True,
                backgroundcolor=rgba(PALETTE["background"], 0.92),
                gridcolor=rgba(PALETTE["grid"], 0.9),
                zerolinecolor=rgba(PALETTE["ap_halo"], 0.45),
                color=PALETTE["text_secondary"],
            ),
            camera=dict(eye=dict(x=1.55, y=1.35, z=1.15)),
            annotations=[],
        ),
        annotations=annotations,
    )

    return fig
