"""Re-express Korean KNHANES survey-weighted percentages on two scales."""
import csv
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
rates = {}
with (ROOT / "source_cells.csv").open() as source:
    for row in csv.DictReader(source):
        key = (row["age_band"], row["group"])
        assert key not in rates
        early, late = (Decimal(row[field]) for field in ("early_pct", "late_pct"))
        assert 0 < early < 100 and 0 < late < 100
        rates[key] = (early, late)

with (ROOT / "usage_contrasts.csv").open("w", newline="") as destination:
    writer = csv.writer(destination)
    writer.writerow(["age_band", "eligible_group", "eligible_change_pp",
                     "unsupported_change_pp", "difference_of_changes_pp",
                     "eligible_growth_factor", "unsupported_growth_factor",
                     "ratio_of_growth_factors"])
    for (age, group), (early, late) in rates.items():
        if group == "unsupported_disabling":
            continue
        comparison_early, comparison_late = rates[age, "unsupported_disabling"]
        difference = late - early
        comparison_difference = comparison_late - comparison_early
        growth = late / early
        comparison_growth = comparison_late / comparison_early
        writer.writerow([age, group, difference, comparison_difference,
                         difference - comparison_difference, f"{growth:.4f}",
                         f"{comparison_growth:.4f}", f"{growth/comparison_growth:.4f}"])
