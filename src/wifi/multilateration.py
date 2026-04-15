"""Multilateration utilities for estimating AP positions from RSSI observations."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Dict, Iterable, List, Sequence, Tuple

Vector3 = Tuple[float, float, float]


@dataclass(frozen=True)
class LogDistanceModelConfig:
    """Configuration for the log-distance path loss model.

    distance_m = reference_distance_m * 10 ** ((tx_power_dbm - rssi_dbm) / (10 * path_loss_exponent))
    """

    tx_power_dbm: float = -40.0
    path_loss_exponent: float = 2.0
    reference_distance_m: float = 1.0


@dataclass(frozen=True)
class DistanceModel:
    """Distance conversion model definition."""

    model_type: str = "log_distance"
    config: LogDistanceModelConfig = LogDistanceModelConfig()


@dataclass(frozen=True)
class SolverConfig:
    """Settings for nonlinear least-squares optimization."""

    max_iterations: int = 80
    tolerance: float = 1e-6
    damping: float = 1e-4


@dataclass(frozen=True)
class APFitResult:
    """Result of multilateration for a single AP."""

    estimated_position: Vector3
    rmse: float
    max_error: float
    converged: bool
    iterations: int


def rssi_to_distance(rssi_dbm: float, model: DistanceModel) -> float:
    """Convert RSSI to distance in meters."""
    if model.model_type != "log_distance":
        raise ValueError(f"Unsupported model_type: {model.model_type}")

    cfg = model.config
    exponent = 10.0 * cfg.path_loss_exponent
    return cfg.reference_distance_m * (10.0 ** ((cfg.tx_power_dbm - rssi_dbm) / exponent))


def _vsub(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _norm(v: Vector3) -> float:
    return sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


def _solve_3x3(mat: Sequence[Sequence[float]], vec: Sequence[float]) -> Vector3:
    """Gaussian elimination for 3x3 linear systems."""
    a = [list(row) + [rhs] for row, rhs in zip(mat, vec)]

    for col in range(3):
        pivot = max(range(col, 3), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-12:
            raise ValueError("Singular matrix in linear solve")
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]

        pivot_value = a[col][col]
        for j in range(col, 4):
            a[col][j] /= pivot_value

        for row in range(3):
            if row == col:
                continue
            factor = a[row][col]
            for j in range(col, 4):
                a[row][j] -= factor * a[col][j]

    return (a[0][3], a[1][3], a[2][3])


def _compute_residuals(ap_pos: Vector3, receivers: Sequence[Vector3], distances: Sequence[float]) -> List[float]:
    residuals: List[float] = []
    for rpos, dist in zip(receivers, distances):
        residuals.append(_norm(_vsub(ap_pos, rpos)) - dist)
    return residuals


def _initial_guess(receivers: Sequence[Vector3]) -> Vector3:
    n = float(len(receivers))
    return (
        sum(r[0] for r in receivers) / n,
        sum(r[1] for r in receivers) / n,
        sum(r[2] for r in receivers) / n,
    )


def solve_ap_position(
    receiver_positions: Sequence[Vector3],
    estimated_distances: Sequence[float],
    solver_config: SolverConfig | None = None,
) -> APFitResult:
    """Estimate AP coordinates from receiver points and per-point distances."""
    if len(receiver_positions) < 3:
        raise ValueError("At least 3 receiver positions are required")
    if len(receiver_positions) != len(estimated_distances):
        raise ValueError("receiver_positions and estimated_distances length mismatch")

    cfg = solver_config or SolverConfig()
    x = _initial_guess(receiver_positions)

    converged = False
    iteration = 0

    for iteration in range(1, cfg.max_iterations + 1):
        residuals = _compute_residuals(x, receiver_positions, estimated_distances)

        jtj = [[0.0, 0.0, 0.0] for _ in range(3)]
        jtr = [0.0, 0.0, 0.0]

        for rpos, resid in zip(receiver_positions, residuals):
            dx, dy, dz = _vsub(x, rpos)
            distance = sqrt(dx * dx + dy * dy + dz * dz)
            if distance < 1e-9:
                continue

            grad = (dx / distance, dy / distance, dz / distance)
            for i in range(3):
                for j in range(3):
                    jtj[i][j] += grad[i] * grad[j]
                jtr[i] += grad[i] * resid

        for i in range(3):
            jtj[i][i] += cfg.damping

        try:
            step = _solve_3x3(jtj, jtr)
        except ValueError:
            break

        x_next = (x[0] - step[0], x[1] - step[1], x[2] - step[2])
        step_norm = _norm(step)
        x = x_next

        if step_norm < cfg.tolerance:
            converged = True
            break

    final_residuals = _compute_residuals(x, receiver_positions, estimated_distances)
    squared = [r * r for r in final_residuals]
    rmse = sqrt(sum(squared) / len(squared)) if squared else 0.0
    max_error = max(abs(r) for r in final_residuals) if final_residuals else 0.0

    return APFitResult(
        estimated_position=x,
        rmse=rmse,
        max_error=max_error,
        converged=converged,
        iterations=iteration,
    )


def multilaterate_access_points(
    receiver_positions: Sequence[Vector3],
    rssi_measurements_by_ap: Dict[str, Sequence[float]],
    distance_model: DistanceModel,
    solver_config: SolverConfig | None = None,
) -> Dict[str, APFitResult]:
    """Run multilateration for each AP from RSSI measurements.

    Args:
        receiver_positions: Known receiver coordinates.
        rssi_measurements_by_ap: map AP ID -> RSSI list aligned to receiver_positions.
        distance_model: RSSI-to-distance conversion model.
        solver_config: Nonlinear least squares solver settings.
    """
    results: Dict[str, APFitResult] = {}
    for ap_id, rssi_values in rssi_measurements_by_ap.items():
        if len(rssi_values) != len(receiver_positions):
            raise ValueError(
                f"AP {ap_id} has {len(rssi_values)} RSSI values but expected {len(receiver_positions)}"
            )

        distances = [rssi_to_distance(rssi, distance_model) for rssi in rssi_values]
        results[ap_id] = solve_ap_position(receiver_positions, distances, solver_config)

    return results
