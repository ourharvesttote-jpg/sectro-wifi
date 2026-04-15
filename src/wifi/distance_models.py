"""Distance estimation models derived from RSSI samples.

Assumptions:
- Input RSSI is in dBm and typically negative for Wi‑Fi links.
- Returned distance is in meters and is only a coarse estimate.

Limitations:
- Multipath reflections can strengthen or attenuate RSSI unpredictably.
- NLOS (non-line-of-sight) links often bias estimates to appear farther.
- Temporal fading and interference can cause per-packet oscillations.
"""

from __future__ import annotations


def log_distance_model(rssi_dbm: float, A: float = -50.0, n: float = 2.4) -> float:
    """Estimate distance in meters with a log-distance path-loss model.

    The model assumes the reference RSSI ``A`` is measured at 1 meter and uses
    path-loss exponent ``n`` to represent environmental attenuation:

    ``d = 10 ** ((A - rssi_dbm) / (10 * n))``

    Args:
        rssi_dbm: Measured received signal strength in dBm.
        A: Reference RSSI in dBm at 1 meter.
        n: Path-loss exponent (lower in open space, higher in cluttered areas).

    Returns:
        Estimated distance in meters.

    Raises:
        ValueError: If ``n`` is zero, which would cause division by zero.
    """

    if n == 0:
        raise ValueError("Path-loss exponent 'n' must be non-zero.")
    return 10 ** ((A - rssi_dbm) / (10 * n))


def inverse_model(rssi_dbm: float, k: float = 100.0, epsilon: float = 1e-6) -> float:
    """Estimate distance in meters with a monotonic inverse baseline.

    This baseline does not model RF propagation physics. It provides a smooth,
    monotonic transformation useful for ranking or rough scaling when calibration
    data is unavailable:

    ``d = k / max(abs(rssi_dbm), epsilon)``

    Args:
        rssi_dbm: Measured received signal strength in dBm.
        k: Scaling constant tuned to the expected RSSI range.
        epsilon: Small lower bound that prevents division by zero.

    Returns:
        Estimated distance in meters (relative baseline, not physically rigorous).
    """

    return k / max(abs(rssi_dbm), epsilon)
