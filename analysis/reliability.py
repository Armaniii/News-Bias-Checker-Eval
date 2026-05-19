"""
Phase 2 — Inter-judge reliability statistics.

Replaces ad-hoc agreement thresholds (e.g., abs_diff < 0.5 == "high agreement")
with proper kappa and Krippendorff's alpha, both with bootstrap 95% CIs.

Functions:
    cohens_kappa_ci(y1, y2, n_iter=2000) -> (kappa, lo, hi)
    krippendorff_alpha_ci(matrix, level='ordinal', n_iter=2000) -> (alpha, lo, hi)
    pearson_fisher_ci(x, y) -> (r, lo, hi, p)
"""

from __future__ import annotations
import numpy as np
from scipy import stats
import krippendorff


def _cohens_kappa(y1, y2) -> float:
    y1 = np.asarray(y1); y2 = np.asarray(y2)
    labels = sorted(set(y1) | set(y2))
    L = len(labels)
    if L < 2:
        return 1.0
    idx = {v: i for i, v in enumerate(labels)}
    M = np.zeros((L, L))
    for a, b in zip(y1, y2):
        M[idx[a], idx[b]] += 1
    n = M.sum()
    if n == 0:
        return float("nan")
    po = np.trace(M) / n
    pe = (M.sum(axis=0) * M.sum(axis=1)).sum() / (n * n)
    return (po - pe) / (1 - pe) if (1 - pe) > 0 else 1.0


def cohens_kappa_ci(y1, y2, n_iter: int = 2000, seed: int = 0):
    """Bootstrap-CI Cohen's kappa over paired observations."""
    y1 = np.asarray(y1); y2 = np.asarray(y2)
    n = len(y1)
    rng = np.random.default_rng(seed)
    point = _cohens_kappa(y1, y2)
    boots = []
    for _ in range(n_iter):
        idx = rng.integers(0, n, n)
        boots.append(_cohens_kappa(y1[idx], y2[idx]))
    boots = np.array([b for b in boots if not np.isnan(b)])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(point), float(lo), float(hi)


def krippendorff_alpha_ci(matrix, level: str = "ordinal",
                          n_iter: int = 2000, seed: int = 0):
    """
    matrix: shape (n_raters, n_items) with NaN for missing.
    Returns (alpha, lo, hi). Resamples columns (items) with replacement.
    """
    matrix = np.asarray(matrix, dtype=float)
    n_items = matrix.shape[1]
    point = krippendorff.alpha(reliability_data=matrix,
                               level_of_measurement=level)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_iter):
        idx = rng.integers(0, n_items, n_items)
        sub = matrix[:, idx]
        try:
            a = krippendorff.alpha(reliability_data=sub,
                                   level_of_measurement=level)
            if not np.isnan(a):
                boots.append(a)
        except Exception:
            continue
    if not boots:
        return float(point), float("nan"), float("nan")
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(point), float(lo), float(hi)


def pearson_fisher_ci(x, y, alpha: float = 0.05):
    """Pearson r with Fisher-z transform 95% CI and p-value."""
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]
    n = len(x)
    if n < 4:
        return float("nan"), float("nan"), float("nan"), float("nan")
    r, p = stats.pearsonr(x, y)
    # Clamp r to avoid arctanh blow-up
    r_c = max(min(r, 0.999999), -0.999999)
    z = np.arctanh(r_c)
    se = 1.0 / np.sqrt(n - 3)
    crit = stats.norm.ppf(1 - alpha / 2)
    lo = float(np.tanh(z - crit * se))
    hi = float(np.tanh(z + crit * se))
    return float(r), lo, hi, float(p)
