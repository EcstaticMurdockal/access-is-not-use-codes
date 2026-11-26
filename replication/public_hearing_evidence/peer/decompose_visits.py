"""Unadjusted 12-month service use from Liu et al. (2011), Table 3, survivor subset."""
import csv
import itertools
import math
from pathlib import Path
from statistics import NormalDist

HERE = Path(__file__).resolve().parent
Z = NormalDist().inv_cdf(0.975)
METRICS = ("total", "first", "subsequent")


def moments(n, mean, fraction, sd):
    """Person-level mean and sample variance for N, I[N>0], and N-I[N>0]."""
    variance_i = n / (n - 1) * fraction * (1 - fraction)
    covariance = n / (n - 1) * mean * (1 - fraction)
    variance_repeat = sd ** 2 + variance_i - 2 * covariance
    return {
        "total": (mean, sd ** 2),
        "first": (fraction, variance_i),
        "subsequent": (mean - fraction, variance_repeat),
    }


def read_arms():
    with (HERE / "arm_data.csv").open(encoding="utf-8", newline="") as stream:
        arms = []
        for row in csv.DictReader(stream):
            n = int(row["n_surviving"])
            mean, sd = float(row["mean_visits"]), float(row["sd_visits"])
            fraction = float(row["any_visit_pct"]) / 100
            central = moments(n, mean, fraction, sd)
            # Sensitivity to published rounding. This deliberately allows pairs of
            # integer moments that need not jointly occur in a physical dataset.
            k_candidates = [
                k for k in range(n + 1) if abs(k / n - fraction) <= 0.0005 + 1e-12
            ]
            totals = [
                t for t in range(math.floor((mean - 0.005) * n), math.ceil((mean + 0.005) * n) + 1)
                if abs(t / n - mean) <= 0.005 + 1e-12
            ]
            assert k_candidates and totals
            rounded = [
                moments(n, t / n, k / n, candidate_sd)
                for k, t, candidate_sd in itertools.product(k_candidates, totals, (sd - .005, sd + .005))
                if t >= k
            ]
            arms.append((row["arm"], n, central, rounded))
        return arms


def contrast(test, control, metric, n_test, n_control):
    effect = test[metric][0] - control[metric][0]
    se = math.sqrt(test[metric][1] / n_test + control[metric][1] / n_control)
    return tuple(100 * v for v in (effect, effect - Z * se, effect + Z * se))


def main():
    control, *arms = read_arms()
    with (HERE / "visit_contrasts.csv").open("w", newline="", encoding="utf-8") as stream:
        w = csv.writer(stream)
        w.writerow(("screening_arm", "outcome", "difference_per_100", "approx_95_low", "approx_95_high", "rounding_low_delta", "rounding_high_delta", "rounding_95_envelope_low", "rounding_95_envelope_high"))
        for treatment in arms:
            for metric in METRICS:
                central = contrast(treatment[2], control[2], metric, treatment[1], control[1])
                possibilities = [
                    contrast(t, c, metric, treatment[1], control[1])
                    for t, c in itertools.product(treatment[3], control[3])
                ]
                summary = (min(res[0] for res in possibilities), max(res[0] for res in possibilities), min(res[1] for res in possibilities), max(res[2] for res in possibilities))
                w.writerow((treatment[0], metric, *(f"{value:.3f}" for value in central + summary)))


if __name__ == "__main__":
    main()
