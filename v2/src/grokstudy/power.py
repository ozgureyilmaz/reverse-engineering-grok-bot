"""Sample-size formulas for the v2 schedule.

These are design calculations, evidence class inferred_model. They are not
estimates from the October corpus. The worst-case proportion p=0.5 maximises
the binomial variance. Fresh bot per run is the sampling unit, because v1
showed that products inside one chat are not independent draws.
"""
from __future__ import annotations

import math

from .statsutil import Z95


def n_for_proportion(half_width: float, *, p: float = 0.5, z: float = Z95) -> int:
    """Smallest n such that the Wald half-width at proportion p is <= half_width.

    Wald and Wilson widths are close at p=0.5 and this n. The schedule uses
    this ceiling. It does not include a design effect on top, because the unit
    is already one fresh bot and one prompt.
    """
    if not 0 < half_width < 1:
        raise ValueError("half_width must be in (0, 1)")
    if not 0 < p < 1:
        raise ValueError("p must be in (0, 1)")
    n = (z ** 2) * p * (1 - p) / (half_width ** 2)
    return max(1, math.ceil(n - 1e-9))


def n_for_difference(
    delta: float,
    *,
    p1: float = 0.5,
    p2: float = 0.8,
    power: float = 0.8,
    alpha: float = 0.05,
) -> int:
    """Per-arm n for a two-sided test of a difference of independent proportions.

    Uses the normal approximation with unpooled variance. z_beta comes from a
    small inverse-Phi approximation so this file does not need SciPy.
    """
    if delta <= 0:
        raise ValueError("delta must be positive")
    z_a = _z_two_sided(alpha)
    z_b = _z_one_sided(power)
    var = p1 * (1 - p1) + p2 * (1 - p2)
    n = ((z_a + z_b) ** 2) * var / (delta ** 2)
    return max(1, math.ceil(n - 1e-9))


def expected_half_width(n: int, *, p: float = 0.5, z: float = Z95) -> float:
    if n <= 0:
        raise ValueError("n must be positive")
    return z * math.sqrt(p * (1 - p) / n)


def _z_two_sided(alpha: float) -> float:
    # 0.05 -> 1.95996. Other alphas go through the one-sided inverse at alpha/2.
    if abs(alpha - 0.05) < 1e-12:
        return Z95
    return _z_one_sided(1 - alpha / 2)


def _z_one_sided(prob: float) -> float:
    """Acklam's inverse normal, good to about 1e-9. prob is the cdf."""
    if not 0 < prob < 1:
        raise ValueError("prob must be in (0, 1)")
    a = [
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    ]
    b = [
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    ]
    c = [
        -7.784894002430293e-03,
        -3.223964580411385e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    ]
    d = [
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    ]
    plow = 0.02425
    phigh = 1 - plow
    if prob < plow:
        q = math.sqrt(-2 * math.log(prob))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        )
    if prob > phigh:
        q = math.sqrt(-2 * math.log(1 - prob))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        )
    q = prob - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (
        (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    )
