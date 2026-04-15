"""Generate a demo Wi-Fi 3D scene from synthetic AP data."""

from __future__ import annotations

import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.visualization.wifi_map_3d import AccessPointEstimate, render_wifi_scene


def synthetic_access_points(seed: int = 12) -> list[AccessPointEstimate]:
    rng = random.Random(seed)
    ssids = ["AP-North", "AP-South", "AP-East", "AP-West", "AP-Ceiling"]
    points = []
    for idx, ssid in enumerate(ssids):
        x = rng.uniform(-8.0, 8.0)
        y = rng.uniform(-8.0, 8.0)
        z = rng.uniform(1.0, 5.0)
        rssi = rng.uniform(-82.0, -38.0)
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


def main() -> None:
    ap_data = synthetic_access_points()
    fig = render_wifi_scene(ap_data, title="Synthetic Wi-Fi Coverage Demo")

    out_dir = REPO_ROOT / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    html_path = out_dir / "wifi_map_demo.html"
    fig.write_html(html_path, include_plotlyjs="cdn")
    print(f"Wrote interactive demo: {html_path}")

    png_path = out_dir / "wifi_map_demo.png"
    try:
        fig.write_image(png_path, width=1400, height=900, scale=2)
        print(f"Wrote static frame: {png_path}")
    except Exception as exc:  # noqa: BLE001
        print(f"PNG export skipped ({exc!r}); install 'kaleido' for static export.")


if __name__ == "__main__":
    main()
