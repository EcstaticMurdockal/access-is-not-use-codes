"""Rebuild arm summaries from the archived Figure 3 workbook, after SHA-256 verification."""
import argparse
import csv
import hashlib
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent
SOURCE = ("https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-78833-x/"
          "MediaObjects/41467_2026_78833_MOESM4_ESM.xlsx")
SHA256 = "2a8ec14da0d420386d96cd1d269c3f6627dd67bd751eb90d980f36ab79e6e599"
CATEGORIES = {"No use","<1 h/day","1-4 h/day","4-8 h/day",">8 h/day"}
GROUP_SIZES = {"Physician-supported":107, "Remote-supported":107, "Self-fitting":108}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, help="Previously downloaded publisher file")
    args = parser.parse_args()
    if args.workbook:
        data = args.workbook.read_bytes()
    else:
        with urlopen(SOURCE, timeout=90) as response:
            data = response.read()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("Publisher workbook differs from the audited version.")
    book = load_workbook(BytesIO(data), read_only=True, data_only=True)
    questionnaire = {}
    for group, visit, category, count, percent in list(book["Figure 3 (b)"].values)[1:]:
        assert group in GROUP_SIZES and category in CATEGORIES and count >= 0
        assert abs(count / GROUP_SIZES[group]*100 - percent) < 1e-7
        categories = questionnaire.setdefault((group,visit), {})
        assert category not in categories
        categories[category] = count
    rows = []
    for group, mean, lower, upper, n, visit in list(book["Figure 3 (a)"].values)[1:]:
        counts = questionnaire[(group,visit)]
        assert sum(counts.values()) == n
        regular = counts["4-8 h/day"] + counts[">8 h/day"]
        # Figure 1 records one death in the self-fitting arm by month three.
        death = int(group == "Self-fitting" and visit in {"3-Month","12-Month"})
        rows.append([group, int(visit.split("-")[0]), GROUP_SIZES[group], n, death, regular,
                     mean,lower,upper])
    assert len(rows) == 9
    with (ROOT/"arm_summaries.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["arm","month","randomized","observed","known_deaths",
                         "regular_wear_reports","power_on_mean","power_on_ci_lo","power_on_ci_hi"])
        writer.writerows(rows)
if __name__ == "__main__":
    main()
