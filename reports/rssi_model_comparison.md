# RSSI Distance Model Comparison

## Parameter rationale
- **A = -50.0 dBm** at 1 meter is a typical indoor anchor for commodity Wi‑Fi APs.
- **n = 2.40** balances lower-loss open areas and higher-loss office clutter.
- **inverse_k = 100.0**, **inverse_epsilon = 1e-06** provide smooth inverse scaling over the common RSSI range (-30 to -90 dBm).

## Assumptions, units, and limitations
- RSSI inputs are in **dBm**; distance outputs are in **meters**.
- Log-distance model is physically motivated but sensitive to mis-calibrated `A` and `n`.
- Inverse model is monotonic and stable for ranking, but not RF-physical.
- Both are affected by multipath, non-line-of-sight bias, and temporal fading.

## Per-sample model output
| RSSI (dBm) | Log-Distance (m) | Inverse Baseline (m) |
|---:|---:|---:|
| -30.0 | 0.147 | 3.333 |
| -40.0 | 0.383 | 2.500 |
| -50.0 | 1.000 | 2.000 |
| -60.0 | 2.610 | 1.667 |
| -70.0 | 6.813 | 1.429 |
| -80.0 | 17.783 | 1.250 |
| -90.0 | 46.416 | 1.111 |

## Summary statistics
| Model | Range (m) | Mean (m) | Variance (m²) |
|---|---:|---:|---:|
| Log-distance | 0.147 – 46.416 | 10.736 | 245.462149 |
| Inverse baseline | 1.111 – 3.333 | 1.899 | 0.535138 |

## When each model performs better/worse
- **Log-distance tends to perform better** when environment-specific calibration exists (measured reference RSSI and fitted path-loss exponent).
- **Log-distance performs worse** when layout changes or heavy NLOS/multipath invalidate calibration assumptions.
- **Inverse baseline performs better** for lightweight ranking, UI smoothing, and simple monotonic distance proxies.
- **Inverse baseline performs worse** for absolute ranging, cross-building transfer, or physics-based planning.
