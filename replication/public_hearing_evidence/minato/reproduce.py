"""Recompute sharp bounds from Minato City's published fiscal-year survey margins."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
numeric = [
    "mailed", "respondents", "no_prior_use", "prior_use", "prior_item_missing",
    "contact_yes", "contact_no", "contact_item_missing",
]
with (ROOT / "source_counts.csv").open() as source:
    cohorts = []
    for row in csv.DictReader(source):
        for key in numeric:
            row[key] = int(row[key]) if row[key] else None
        assert row["mailed"] >= row["respondents"] > 0
        assert sum(row[k] for k in numeric[-3:]) == row["respondents"]
        if row["no_prior_use"] is not None:
            assert sum(row[k] for k in numeric[2:5]) == row["respondents"]
        cohorts.append(row)


def tabulate(label, rows):
    mailed = sum(r["mailed"] for r in rows)
    responded = sum(r["respondents"] for r in rows)
    yes = sum(r["contact_yes"] for r in rows)
    output = {
        "purchase_fy": label, "mailed": mailed, "responded": responded,
        "reported_professional_contact": yes,
        "contact_pct_respondents": f"{100 * yes/responded:.2f}",
    }
    if any(r["no_prior_use"] is None for r in rows):
        return output
    first = sum(r["no_prior_use"] for r in rows)
    lo = sum(max(0, r["no_prior_use"] + r["contact_yes"] - r["respondents"]) for r in rows)
    hi = sum(min(r["no_prior_use"], r["contact_yes"]) for r in rows)
    # Worst-case for the consultation rate among all prior nonusers:
    # Place every survey nonrespondent in that group with no consultation.
    # In these cohorts every survey non-yes can already be assigned to a
    # confirmed prior nonuser when constructing the lower overlap. Adding
    # respondents with unknown prior status then cannot further lower the rate.
    assert all(r["no_prior_use"] + r["contact_yes"] >= r["respondents"] for r in rows)
    assert hi == first
    unknown_framed_people = mailed - responded
    output.update({
        "confirmed_no_prior_use": first,
        "both_affirmed_low": lo, "both_affirmed_high": hi,
        "contact_pct_confirmed_no_prior_low": f"{100 * lo/first:.2f}",
        "contact_pct_confirmed_no_prior_high": f"{100 * hi/first:.2f}",
        "at_least_pct_of_all_mailed_with_both": f"{100 * lo/mailed:.2f}",
        "worst_case_contact_pct_all_mailed_prior_nonusers": f"{100 * lo/(first+unknown_framed_people):.2f}",
    })
    return output


rows = [tabulate(c["purchase_fy"], [c]) for c in cohorts]
rows += [tabulate("2022-23", [c for c in cohorts if c["no_prior_use"] is not None]),
         tabulate("2022-24", cohorts)]
with (ROOT / "results.csv").open("w", newline="") as destination:
    writer = csv.DictWriter(destination, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
