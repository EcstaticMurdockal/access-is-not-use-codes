"""Bound uncertainty for contrasts with unknown cross-equation covariance."""
import csv
from pathlib import Path
from statistics import NormalDist

folder = Path(__file__).resolve().parent
with (folder / 'provider_contrasts.csv').open() as source:
    contrasts = list(csv.DictReader(source))

# All three physician-level splits reported in the source table.
quantile = NormalDist().inv_cdf(1 - 0.05 / (2 * len(contrasts)))
half_rounding_unit = 0.0005  # published coefficients and SEs use three decimal places
fields = ['contrast', 'difference_minutes', 'lower_minutes', 'upper_minutes']
with (folder / 'contrast_intervals.csv').open('w', newline='') as output:
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for contrast in contrasts:
        difference = float(contrast['beta_first']) - float(contrast['beta_second'])
        # Cauchy-Schwarz accounts for every admissible correlation, including -1.
        max_se = sum(float(contrast[k]) + half_rounding_unit for k in ['se_first', 'se_second'])
        margin = 2 * half_rounding_unit + quantile * max_se
        writer.writerow(dict(zip(fields, [
            contrast['contrast'], round(60 * difference, 4),
            round(60 * (difference - margin), 4), round(60 * (difference + margin), 4)
        ])))
