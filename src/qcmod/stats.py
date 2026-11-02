"""Small statistics helpers: intervals, group tests, multiple-test correction."""
import math

import numpy as np
from scipy.stats import chi2_contingency


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% interval for a proportion k/n."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def chi2_groups(successes, totals) -> dict:
    """Chi-squared test that a rate is the same in every group, plus Cramer's V as an effect size."""
    s, t = np.asarray(successes), np.asarray(totals)
    table = np.array([s, t - s])
    chi2, p, _, _ = chi2_contingency(table)
    v = math.sqrt(chi2 / t.sum())  # two rows, so min(r-1, c-1) is 1
    return {"chi2": float(chi2), "p": float(p), "cramers_v": float(v)}


def holm(pvals: dict) -> dict:
    """Holm-Bonferroni adjusted p-values for a dict of name -> p."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    out, running = {}, 0.0
    for i, (name, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[name] = running
    return out


def bootstrap_diff(a, b, n_boot: int = 2000, seed: int = 0) -> tuple[float, float, float]:
    """Difference in means (a - b) with a percentile bootstrap interval."""
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    diffs = [rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(n_boot)]
    return float(a.mean() - b.mean()), float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))
