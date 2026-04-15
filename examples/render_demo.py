"""Generate a demo Wi-Fi 3D scene from synthetic AP data.

Usage:
    python examples/render_demo.py
    python examples/render_demo.py --png
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.visualization.wifi_map_3d import AccessPointEstimate, render_wifi_scene


def synthetic_access_points(seed: int = 12) -> list[AccessPointEstimate]:
    """Build deterministic synthetic AP points for demos/tests."""

    rng = random.Random(seed)
    ssids = ["AP-North", "AP-South", "AP-East", "AP-West", "AP-Ceiling"]
    points = []
    for idx, ssid in enumerate(ssids):
        x = rng.uniform(-8.0, 8.0)
        y = rng.uniform(-8.0, 8.0)
        z = rng.uniform(1.0, 5.0)
        rssi = rng.uniform(-82.0, -38.0)
        # Lightweight log-distance-inspired synthetic model for demo radius.
        distance = max(1.0, min(12.0, 10 ** ((-45 - rssi) / 22)))
        points.append(
            AccessPointEstimate(
                ssid=f"{ssid}-{idx + 1}",
                x=x,
                y=y,
                z=z,
                rssi_dbm=rssi,
                distance_m=distance,
            )
        )
    return points


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render synthetic Wi-Fi 3D demo scene.")
    parser.add_argument("--seed", type=int, default=12, help="Random seed for synthetic AP data.")
    parser.add_argument(
        "--png",
        action="store_true",
        help="Also export a PNG frame (requires kaleido + Chrome runtime).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ap_data = synthetic_access_points(seed=args.seed)
    fig = render_wifi_scene(
        ap_data,
        title="Synthetic Wi-Fi Coverage Demo",
        distance_model_label="synthetic log-distance estimator",
    )

    out_dir = REPO_ROOT / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    html_path = out_dir / "wifi_map_demo.html"
    fig.write_html(html_path, include_plotlyjs="cdn")
    print(f"Wrote interactive demo: {html_path}")

    if args.png:
        png_path = out_dir / "wifi_map_demo.png"
        try:
            fig.write_image(png_path, width=1400, height=900, scale=2)
            print(f"Wrote static frame: {png_path}")
        except Exception as exc:  # noqa: BLE001
            print(f"PNG export skipped ({exc!r}); install kaleido and Chrome to enable --png.")


if __name__ == "__main__":
    main()
