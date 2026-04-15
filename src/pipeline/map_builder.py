"""Integration flow: scan/simulate -> distance estimation -> multilateration -> visualization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Mapping, MutableMapping, Sequence, Tuple

from pipeline.wifi_map_3d import render_wifi_map
from wifi.multilateration import APFitResult, DistanceModel, SolverConfig, multilaterate_access_points
from wifi.simulation import SimulatedAP, SimulationConfig, generate_receiver_layout, run_multilateration_simulation, simulate_rssi_measurements

Vector3 = Tuple[float, float, float]


@dataclass(frozen=True)
class ScanData:
    receiver_positions: Sequence[Vector3]
    rssi_measurements_by_ap: Mapping[str, Sequence[float]]


ScanProvider = Callable[[], ScanData]


def build_wifi_map(
    distance_model: DistanceModel,
    scan_provider: ScanProvider | None = None,
    *,
    simulated_aps: Sequence[SimulatedAP] | None = None,
    simulation_config: SimulationConfig | None = None,
    solver_config: SolverConfig | None = None,
) -> Dict[str, object]:
    """Build a Wi-Fi map from either real scan data or simulated measurements."""
    if scan_provider is not None:
        scan = scan_provider()
        receiver_positions = list(scan.receiver_positions)
        rssi_measurements = dict(scan.rssi_measurements_by_ap)
        simulation_report = None
    else:
        receiver_positions = generate_receiver_layout()
        aps = list(simulated_aps or _default_simulated_aps())
        rssi_measurements = simulate_rssi_measurements(
            receiver_positions=receiver_positions,
            aps=aps,
            distance_model=distance_model,
            simulation_config=simulation_config,
        )
        simulation_report = run_multilateration_simulation(
            aps=aps,
            distance_model=distance_model,
            simulation_config=simulation_config,
        )

    fits = multilaterate_access_points(
        receiver_positions=receiver_positions,
        rssi_measurements_by_ap=rssi_measurements,
        distance_model=distance_model,
        solver_config=solver_config,
    )

    ap_positions = {ap_id: fit.estimated_position for ap_id, fit in fits.items()}
    metadata = {
        "fit_summary": {
            ap_id: {
                "rmse": fit.rmse,
                "max_error": fit.max_error,
                "converged": fit.converged,
                "iterations": fit.iterations,
            }
            for ap_id, fit in fits.items()
        },
        "receiver_positions": receiver_positions,
    }
    if simulation_report is not None:
        metadata["simulation_report"] = simulation_report

    visualization_payload = render_wifi_map(ap_positions, metadata=metadata)
    return {
        "receiver_positions": receiver_positions,
        "rssi_measurements_by_ap": rssi_measurements,
        "fit_results": fits,
        "visualization": visualization_payload,
    }


def _default_simulated_aps() -> Sequence[SimulatedAP]:
    return [
        SimulatedAP(ap_id="ap-1", true_position=(2.5, 1.2, 1.5)),
        SimulatedAP(ap_id="ap-2", true_position=(-1.5, 2.0, 1.0)),
        SimulatedAP(ap_id="ap-3", true_position=(0.8, -2.2, 1.7)),
    ]
