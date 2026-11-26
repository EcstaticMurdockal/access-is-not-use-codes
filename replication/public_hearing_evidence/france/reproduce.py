"""Reconstruct eight-year claim-history groups from Cour des comptes 2022, pp. 27–28."""
from csv import DictReader
from itertools import product
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent


def compute(n18, n21, pct18, pct21):
    a18 = n18 * (1 - pct18 / 100)
    a21 = n21 * (1 - pct21 / 100)
    change = a21 - a18
    return {
        'no_prior_2018_thousands': a18,
        'no_prior_2021_thousands': a21,
        'increase_no_prior_thousands': change,
        'increase_with_prior_thousands': (n21 - n18) - change,
        'total_increase_thousands': n21 - n18,
        'fraction_net_growth_no_prior_percent': 100 * change / (n21 - n18),
        'composition_change_percentage_points': pct18 - pct21,
        'break_even_misclassified_2021_percent_if_zero_in_2018': 100 * change / a21,
    }


with (ROOT / 'receipt_history.csv').open() as f:
    records = {(r['coverage'], int(r['year'])): r for r in DictReader(f)}

output = {}
for group in ('non-CSS', 'CSS'):
    a, b = (records[group, year] for year in (2018, 2021))
    mid = tuple(float(v) for v in
                (a['purchasers_thousands'], b['purchasers_thousands'],
                 a['prior_eight_year_claim_percent'], b['prior_eight_year_claim_percent']))
    center = compute(*mid)
    # Standard rounding to the nearest thousand and nearest percentage point.
    # Results are monotone in each separate input on this box, including the ratio
    # (its numerator and denominator are separately affine in each input).
    corners = [compute(*(m + e for m, e in zip(mid, eps))) for eps in product((-.5, .5), repeat=4)]
    output[group] = {
        name: {'central': round(point, 3),
               'rounding_envelope': [round(min(r[name] for r in corners), 3),
                                     round(max(r[name] for r in corners), 3)]}
        for name, point in center.items()
    }

assert abs(output['non-CSS']['increase_no_prior_thousands']['central'] - 256.32) < 1e-8
assert abs(output['CSS']['increase_no_prior_thousands']['central'] - 25.76) < 1e-8
data = json.dumps(output, indent=2)
(ROOT / 'results.json').write_text(data + '\n')
print(data)
