"""Reproduce raw contrasts from published arm means in Malmberg et al., Table 2."""

import csv
from decimal import Decimal
from pathlib import Path


def main():
    folder = Path(__file__).resolve().parent
    with (folder / "trial_arm_means.csv").open(encoding="utf-8") as source:
        records = {(row["outcome"], row["arm"]): row for row in csv.DictReader(source)}

    with (folder / "contrasts.csv").open("w", encoding="utf-8", newline="") as target:
        writer = csv.writer(target, lineterminator="\n")
        writer.writerow(["outcome", "role", "favourable_direction", "time",
                         "full_change", "reading_change", "difference_in_changes"])
        for outcome in ("HHIE total", "CSS total"):
            full = records[outcome, "full"]
            reading = records[outcome, "reading"]
            for time in ("post", "month_6"):
                full_change = Decimal(full[time]) - Decimal(full["baseline"])
                reading_change = Decimal(reading[time]) - Decimal(reading["baseline"])
                writer.writerow([outcome, full["role"], full["favourable_direction"],
                                 time, full_change, reading_change, full_change - reading_change])


if __name__ == "__main__":
    main()
