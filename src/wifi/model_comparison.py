"""Compare RSSI-to-distance models and generate summary reports.

Assumptions and units:
- Input RSSI samples are in dBm.
- Output distances are in meters.

Limitations:
- Multipath and NLOS conditions bias both models in environment-specific ways.
- Temporal fading can inflate variance and reduce repeatability.
- The inverse model is a baseline scaler, not a propagation-physics model.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pvariance
from typing import Iterable

from .config import DistanceModelConfig
from .distance_models import inverse_model, log_distance_model


@dataclass(frozen=True)
class ModelSummary:
    """Summary statistics for a model's predicted distances in meters."""

    min_distance: float
    max_distance: float
    mean_distance: float
    variance_distance: float


@dataclass(frozen=True)
class ModelComparisonResult:
    """Structured output for per-sample comparison and aggregate summaries."""

    samples_rssi_dbm: list[float]
    per_sample_rows: list[dict[str, float]]
    summary_by_model: dict[str, ModelSummary]
    markdown_table: str


def _summary(values: list[float]) -> ModelSummary:
    if not values:
        return ModelSummary(0.0, 0.0, 0.0, 0.0)
    return ModelSummary(
        min_distance=min(values),
        max_distance=max(values),
        mean_distance=mean(values),
        variance_distance=pvariance(values),
    )


def compare_models(
    rssi_samples_dbm: Iterable[float],
    config: DistanceModelConfig,
) -> ModelComparisonResult:
    """Compare log-distance and inverse baseline models across RSSI samples.

    Args:
        rssi_samples_dbm: RSSI sample sequence in dBm.
        config: Shared model parameter configuration.

    Returns:
        ModelComparisonResult containing a markdown table and summary stats.
    """

    samples = [float(v) for v in rssi_samples_dbm]
    log_distances = [log_distance_model(v, A=config.A, n=config.n) for v in samples]
    inverse_distances = [
        inverse_model(v, k=config.inverse_k, epsilon=config.inverse_epsilon)
        for v in samples
    ]

    rows = [
        {
            "rssi_dbm": rssi,
            "log_distance_m": log_d,
            "inverse_distance_m": inv_d,
        }
        for rssi, log_d, inv_d in zip(samples, log_distances, inverse_distances)
    ]

    markdown_table = _build_markdown_table(rows)

    summaries = {
        "log_distance_model": _summary(log_distances),
        "inverse_model": _summary(inverse_distances),
    }

    return ModelComparisonResult(
        samples_rssi_dbm=samples,
        per_sample_rows=rows,
        summary_by_model=summaries,
        markdown_table=markdown_table,
    )


def _build_markdown_table(rows: list[dict[str, float]]) -> str:
    header = (
        "| RSSI (dBm) | Log-Distance (m) | Inverse Baseline (m) |\n"
        "|---:|---:|---:|"
    )
    body = "\n".join(
        f"| {row['rssi_dbm']:.1f} | {row['log_distance_m']:.3f} | {row['inverse_distance_m']:.3f} |"
        for row in rows
    )
    return f"{header}\n{body}" if body else header


def generate_markdown_report(
    rssi_samples_dbm: Iterable[float],
    config: DistanceModelConfig,
    output_path: str | Path = "reports/rssi_model_comparison.md",
) -> Path:
    """Generate a markdown comparison report for RSSI distance models.

    The report includes parameter rationale, per-sample table output, and model
    summary statistics. It is intended for calibration notes and quick reviews,
    not as a substitute for site-specific measurement campaigns.
    """

    result = compare_models(rssi_samples_dbm=rssi_samples_dbm, config=config)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    log_summary = result.summary_by_model["log_distance_model"]
    inv_summary = result.summary_by_model["inverse_model"]

    report = f"""# RSSI Distance Model Comparison

## Parameter rationale
- **A = {config.A:.1f} dBm** at 1 meter is a typical indoor anchor for commodity Wi‑Fi APs.
- **n = {config.n:.2f}** balances lower-loss open areas and higher-loss office clutter.
- **inverse_k = {config.inverse_k:.1f}**, **inverse_epsilon = {config.inverse_epsilon:g}** provide smooth inverse scaling over the common RSSI range (-30 to -90 dBm).

## Assumptions, units, and limitations
- RSSI inputs are in **dBm**; distance outputs are in **meters**.
- Log-distance model is physically motivated but sensitive to mis-calibrated `A` and `n`.
- Inverse model is monotonic and stable for ranking, but not RF-physical.
- Both are affected by multipath, non-line-of-sight bias, and temporal fading.

## Per-sample model output
{result.markdown_table}

## Summary statistics
| Model | Range (m) | Mean (m) | Variance (m²) |
|---|---:|---:|---:|
| Log-distance | {log_summary.min_distance:.3f} – {log_summary.max_distance:.3f} | {log_summary.mean_distance:.3f} | {log_summary.variance_distance:.6f} |
| Inverse baseline | {inv_summary.min_distance:.3f} – {inv_summary.max_distance:.3f} | {inv_summary.mean_distance:.3f} | {inv_summary.variance_distance:.6f} |

## When each model performs better/worse
- **Log-distance tends to perform better** when environment-specific calibration exists (measured reference RSSI and fitted path-loss exponent).
- **Log-distance performs worse** when layout changes or heavy NLOS/multipath invalidate calibration assumptions.
- **Inverse baseline performs better** for lightweight ranking, UI smoothing, and simple monotonic distance proxies.
- **Inverse baseline performs worse** for absolute ranging, cross-building transfer, or physics-based planning.
"""

    output.write_text(report, encoding="utf-8")
    return output
