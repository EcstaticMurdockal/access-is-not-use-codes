"""Reweight reported Korean prescription-and-payment rates by severity at registration."""

import csv
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent
YEARS = ((2014, 2016), (2013, 2016), (2014, 2017), (2013, 2017))
HALF_PRINT_UNIT = Fraction(1, 20)  # Percentage points, reported to one decimal.


def load_cohorts():
    with (ROOT / "published_cohorts.csv").open(newline="") as f:
        raw = list(csv.DictReader(f))
    cohorts = {}
    for row in raw:
        year = int(row["year"])
        grades = [int(row[f"grade_{k}"]) for k in range(2, 7)]
        total = int(row["published_total"])
        assert sum(grades) == total
        weight = Fraction(sum(grades[:2]), total)
        rates = (Fraction(row["grades_2_3_claim_pct"]), Fraction(row["grades_4_6_claim_pct"]))
        overall = Fraction(row["all_claim_pct"])
        # The underlying individual percentages and the overall percentage were
        # independently rounded once to one decimal place.
        pooled = weight * rates[0] + (1 - weight) * rates[1]
        assert abs(pooled - overall) <= 2 * HALF_PRINT_UNIT, (year, float(pooled), float(overall))
        cohorts[year] = (weight, rates, overall)
    return cohorts


def main():
    cohorts = load_cohorts()
    fields = ["before", "after", "standard_population", "observed_difference_pp",
              "standardized_before_pct", "standardized_after_pct", "standardized_difference_pp",
              "rounding_min_pp", "rounding_max_pp"]
    with (ROOT / "grade_standardization.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for before, after in YEARS:
            w, old, raw_before = cohorts[before]
            _, new, raw_after = cohorts[after]
            reference = w * old[0] + (1 - w) * old[1]
            reweighted = w * new[0] + (1 - w) * new[1]
            change = reweighted - reference
            error = 2 * HALF_PRINT_UNIT
            estimates = [raw_after - raw_before, reference, reweighted, change, change - error, change + error]
            writer.writerow([before, after, before] + [f"{float(x):.4f}" for x in estimates])


if __name__ == "__main__":
    main()
