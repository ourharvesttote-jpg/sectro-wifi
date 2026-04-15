"""Synthetic RSSI simulation and multilateration demo."""

from __future__ import annotations

import random
from dataclasses import dataclass
from math import log10, sqrt
from typing import Dict, Iterable, List, Sequence, Tuple

from wifi.multilateration import APFitResult, DistanceModel, multilaterate_access_points

Vector3 = Tuple[float, float, float]


@dataclass(frozen=True)
class SimulatedAP:
    ap_id: str
    true_position: Vector3


@dataclass(frozen=True)
class SimulationConfig:
    noise_stddev_db: float = 1.5
    random_seed: int = 42


def generate_receiver_layout() -> List[Vector3]:
    """Generate four receiver points near origin in a tetrahedral-like arrangement."""
    return [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.5, 0.9, 0.0),
        (0.5, 0.3, 0.8),
    ]


def _distance(a: Vector3, b: Vector3) -> float:
    return sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def _distance_to_rssi(distance_m: float, distance_model: DistanceModel) -> float:
    cfg = distance_model.config
    d = max(distance_m, 1e-6)
    return cfg.tx_power_dbm - 10.0 * cfg.path_loss_exponent * log10(d / cfg.reference_distance_m)


def simulate_rssi_measurements(
    receiver_positions: Sequence[Vector3],
    aps: Sequence[SimulatedAP],
    distance_model: DistanceModel,
    simulation_config: SimulationConfig | None = None,
) -> Dict[str, List[float]]:
    """Simulate RSSI observations for each AP at each receiver point."""
    cfg = simulation_config or SimulationConfig()
    rng = random.Random(cfg.random_seed)

    measurements: Dict[str, List[float]] = {}
    for ap in aps:
        samples: List[float] = []
        for receiver in receiver_positions:
            ideal_rssi = _distance_to_rssi(_distance(ap.true_position, receiver), distance_model)
            noisy_rssi = ideal_rssi + rng.gauss(0.0, cfg.noise_stddev_db)
            samples.append(noisy_rssi)
        measurements[ap.ap_id] = samples
    return measurements


def run_multilateration_simulation(
    aps: Sequence[SimulatedAP],
    distance_model: DistanceModel,
    simulation_config: SimulationConfig | None = None,
) -> Dict[str, Dict[str, object]]:
    """Run end-to-end simulation and return estimates plus confidence/error summaries."""
    receiver_positions = generate_receiver_layout()
    measurements = simulate_rssi_measurements(receiver_positions, aps, distance_model, simulation_config)
    estimates = multilaterate_access_points(receiver_positions, measurements, distance_model)

    report: Dict[str, Dict[str, object]] = {}
    for ap in aps:
        fit = estimates[ap.ap_id]
        true_error = _distance(ap.true_position, fit.estimated_position)
        report[ap.ap_id] = {
            "true_position": ap.true_position,
            "estimated_position": fit.estimated_position,
            "solver": {
                "converged": fit.converged,
                "iterations": fit.iterations,
            },
            "error_summary": {
                "fit_rmse_m": fit.rmse,
                "fit_max_error_m": fit.max_error,
                "true_position_error_m": true_error,
                "confidence": _confidence_label(fit),
            },
        }
    return report


def _confidence_label(fit: APFitResult) -> str:
    if not fit.converged:
        return "low"
    if fit.rmse <= 0.5 and fit.max_error <= 1.0:
        return "high"
    if fit.rmse <= 1.5 and fit.max_error <= 3.0:
        return "medium"
    return "low"
