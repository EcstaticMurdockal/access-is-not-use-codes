"""Rebuild the HC 392 paired-provider waiting-figure audit using Python's standard library."""

import csv
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from statistics import mean, median

BASE = Path(__file__).resolve().parent
PERIODS = ("2004-05", "2005-06", "Current")
AMBIGUOUS = {"Healthcare", "University Hospitals"}
RAW_SHA256 = "5f4a5e13050cfa4f4a8a37cf0c02a626d42f0b21f0ffb2a38c5eb3af06383ea8"


class TableRows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = []
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag == "td":
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == "td":
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr":
            self.rows.append(self.row)


def parse_panel(html, table_name, expected_label):
    body = html.split("><B>Table " + table_name + "<BR>", 1)[1].split("</TABLE>", 1)[0]
    parser = TableRows()
    parser.feed(body)
    rows = parser.rows
    if rows[:2] != [["", expected_label], ["Trust", *PERIODS]] or rows[-1][0] != "Average":
        raise ValueError(f"Unexpected header/footer of table {table_name}")
    sites = {}
    for name, *values in rows[2:-1]:
        if name in sites or len(values) != len(PERIODS):
            raise ValueError(f"Duplicate provider or wrong number of columns: {name}")
        if any(v != "*" and re.fullmatch(r"\d+(?:\.\d+)?", v) is None for v in values):
            raise ValueError(f"Unrecognized source entry for {name}: {values}")
        sites[name] = [None if v == "*" else float(v) for v in values]
    return sites


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def period_summary(records, sites, label):
    output = []
    for period in PERIODS:
        sample = [r for r in records if r["period"] == period and r["reporting_label"] in sites]
        pairs = [r for r in sample if r["gap_weeks"] is not None]
        diff = [r["gap_weeks"] for r in pairs]
        missing_new = sum(r["first_fit_weeks"] is None for r in sample)
        missing_review = sum(r["reassessment_weeks"] is None for r in sample)
        output.append({
            "sample": label, "period": period, "eligible_labels": len(sample), "paired": len(pairs),
            "first_fit_unavailable": missing_new, "reassessment_unavailable": missing_review,
            "either_unavailable": len(sample) - len(pairs),
            "mean_first_fit_weeks": round(mean(r["first_fit_weeks"] for r in pairs), 4),
            "mean_reassessment_weeks": round(mean(r["reassessment_weeks"] for r in pairs), 4),
            "mean_gap_weeks": round(mean(diff), 4), "median_gap_weeks": median(diff),
            "reassessment_longer": sum(d > 0 for d in diff), "equal": diff.count(0),
            "reassessment_shorter": sum(d < 0 for d in diff),
        })
    return output


def write_current_table(path, summaries):
    """Write the appendix rows in presentation order from the same paired summaries."""
    labels = {
        "named_exact": "Named exact matches",
        "balanced_named_exact": "Complete in all periods",
        "no_explicit_child_label": "Exclude named children's services",
        "balanced_no_explicit_child_label": "Complete in all periods, excluding named children's services",
        "exclude_barnsley": "Exclude Barnsley",
        "all_exact": "Include two ambiguous names",
        "named_plus_warwickshire_crosswalk": "Include Warwickshire match",
    }
    current = {row["sample"]: row for row in summaries if row["period"] == "Current"}
    with path.open("w", encoding="utf-8") as stream:
        print(r"""\begin{tabularx}{\linewidth}{@{}Xrrrrrr@{}}\toprule
& & \multicolumn{2}{c}{Gap (weeks)} & \multicolumn{3}{c}{Reassessment wait}\\
\cmidrule(lr){3-4}\cmidrule(l){5-7}
Reporting units & Pairs & Mean & Median & Longer & Equal & Shorter\\\midrule""", file=stream)
        for sample, label in labels.items():
            row = current[sample]
            cells = (label, str(row["paired"]), f"{row['mean_gap_weeks']:.2f}",
                     f"{row['median_gap_weeks']:g}", str(row["reassessment_longer"]),
                     str(row["equal"]), str(row["reassessment_shorter"]))
            print(" & ".join(cells) + r"\\", file=stream)
        print(r"\bottomrule", file=stream)
        print(r"\end{tabularx}", file=stream)


def main():
    raw = (BASE / "raw" / "shapps.html").read_bytes()
    if hashlib.sha256(raw).hexdigest() != RAW_SHA256:
        raise ValueError("Unexpected source vintage")
    html = raw.decode("latin1")
    first = parse_panel(html, "2a", "First Fitting Hearing Aid")
    review = parse_panel(html, "2b", "Reassessment")
    overlap = first.keys() & review.keys()
    named = overlap - AMBIGUOUS
    balanced = {s for s in named if None not in first[s] + review[s]}
    output = BASE / "results"
    output.mkdir(exist_ok=True)
    rows = []
    for site in sorted(first.keys() | review.keys()):
        for i, period in enumerate(PERIODS):
            f = first[site][i] if site in first else None
            r = review[site][i] if site in review else None
            rows.append({
                "reporting_label": site, "period": period, "listed_first": int(site in first),
                "listed_reassessment": int(site in review), "named_exact_match": int(site in named),
                "balanced_primary": int(site in balanced), "first_fit_weeks": f,
                "reassessment_weeks": r, "gap_weeks": None if r is None or f is None else round(r - f, 2),
            })
    write_csv(output / "provider_waits.csv", rows[0].keys(), rows)
    samples = [
        ("named_exact", named), ("balanced_named_exact", balanced), ("all_exact", overlap),
        ("no_explicit_child_label", {x for x in named if "child" not in x.lower()}),
        ("balanced_no_explicit_child_label", {x for x in balanced if "child" not in x.lower()}),
        ("exclude_barnsley", named - {"Barnsley Hospital"}),
    ]
    summaries = [s for label, sites in samples for s in period_summary(rows, sites, label)]

    # Table 3a identifies the 73-week first-fit entry as Coventry and Warwickshire.
    # Its shortened Table 2a label is deliberately not pooled in the primary sample.
    if "University Hospitals Coventry and Warwickshire" not in html.split("><B>Table 3a<BR>", 1)[1].split("</TABLE>", 1)[0]:
        raise ValueError("Missing external crosswalk check in table 3a")
    if first["Warwickshire"] != [None, None, 73.0]:
        raise ValueError("Warwickshire crosswalk conflict with table 3a")
    alias = "University Hospitals Coventry and Warwickshire"
    with_alias = [r.copy() for r in rows]
    for r in with_alias:
        if r["reporting_label"] == alias:
            f = first["Warwickshire"][PERIODS.index(r["period"])]
            r["first_fit_weeks"] = f
            r["gap_weeks"] = None if f is None or r["reassessment_weeks"] is None else r["reassessment_weeks"] - f
    summaries.extend(period_summary(with_alias, named | {alias}, "named_plus_warwickshire_crosswalk"))
    write_csv(output / "paired_summaries.csv", summaries[0].keys(), summaries)
    write_current_table(output / "current_pairs_table.tex", summaries)
    audit = {
        "table_2a_provider_rows": len(first), "table_2b_provider_rows": len(review),
        "exact_label_intersection": len(overlap), "primary_candidate_labels": len(named),
        "six_numeric_cells_primary": len(balanced), "ambiguous_labels": sorted(AMBIGUOUS),
        "first_table_only": sorted(first.keys() - review.keys()),
        "reassessment_table_only": sorted(review.keys() - first.keys()),
        "explicit_child_labels_in_primary": sorted(x for x in named if "child" in x.lower()),
    }
    (output / "matching_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit))


if __name__ == "__main__":
    main()
