"""Configuration objects for Wi‑Fi RSSI distance estimation.

All parameters assume RSSI values are provided in dBm and output distances are
interpreted in meters. These defaults are pragmatic indoor starting points and
should be recalibrated for each deployment environment.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DistanceModelConfig:
    """Parameter set shared across RSSI distance models.

    Attributes:
        A: Reference RSSI at 1 meter in dBm.
            Default: ``-50.0`` dBm, a common indoor anchor for commodity APs.
        n: Path-loss exponent for the log-distance model.
            Default: ``2.4``, a balanced indoor value between open areas and
            cluttered office layouts.
        inverse_k: Scale constant for the inverse baseline model.
            Default: ``100.0`` for smooth scaling within roughly -30 to -90 dBm.
        inverse_epsilon: Positive lower bound for inverse-model denominator.
            Default: ``1e-6`` to avoid divide-by-zero while preserving monotonicity.
    """

    A: float = -50.0
    n: float = 2.4
    inverse_k: float = 100.0
    inverse_epsilon: float = 1e-6
