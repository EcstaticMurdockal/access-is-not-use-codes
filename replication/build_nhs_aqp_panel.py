#!/usr/bin/env python3
"""Download and standardize NHS Direct Access Audiology CCG-month files.

This script is a data-feasibility audit, not a causal estimator. By default it
builds the treatment-status window that can be audited against Monitor
(April 2013--July 2014). A longer outcome panel can be requested explicitly,
but it must not be interpreted causally until later AQP histories and workbook
schema changes have been reconstructed.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import html.parser
import re
import time
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import pandas as pd


DATA_PAGE = (
    "https://www.england.nhs.uk/statistics/statistical-work-areas/"
    "direct-access-audiology/daa-data/"
)

# Provisional Monitor-reported dates, not validated treatment timing.
# The downstream diagnostic excludes Hounslow using contemporaneous evidence.
COHORTS = [
    ("NHS North Norfolk CCG", "2013-05-01"),
    ("NHS South Norfolk CCG", "2013-05-01"),
    ("NHS Luton CCG", "2013-06-01"),
    ("NHS Wirral CCG", "2013-07-01"),
    ("NHS Brent CCG", "2013-11-01"),
    ("NHS Ealing CCG", "2013-11-01"),
    ("NHS Harrow CCG", "2013-11-01"),
    ("NHS Hillingdon CCG", "2013-11-01"),
    ("NHS Hounslow CCG", "2013-11-01"),
    ("NHS West London (K&C & QPP) CCG", "2013-11-01"),
    ("NHS City and Hackney CCG", "2014-04-01"),
    ("NHS East Lancashire CCG", "2014-04-01"),
    ("NHS Eastern Cheshire CCG", "2014-04-01"),
    ("NHS Fylde & Wyre CCG", "2014-04-01"),
    ("NHS North Kirklees CCG", "2014-04-01"),
    ("NHS Ashford CCG", "2014-07-01"),
    ("NHS Canterbury and Coastal CCG", "2014-07-01"),
    ("NHS South Kent Coast CCG", "2014-07-01"),
]

# Monitor and NHS England use different display names for this commissioner.
# Code 08Y is the stable join key in the audited source workbooks.
MONITOR_TO_NHS_NAME = {
    "NHS WEST LONDON K C QPP CCG": "NHS WEST LONDON CCG"
}


def normalize_name(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = text.upper().replace("&AMP;", "&")
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def archive_links(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    class LinkParser(html.parser.HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.current_href: str | None = None
            self.current_text: list[str] = []
            self.links: list[tuple[str, str]] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag.lower() == "a":
                self.current_href = dict(attrs).get("href")
                self.current_text = []

        def handle_data(self, data: str) -> None:
            if self.current_href is not None:
                self.current_text.append(data)

        def handle_endtag(self, tag: str) -> None:
            if tag.lower() == "a" and self.current_href is not None:
                self.links.append((" ".join(self.current_text), self.current_href))
                self.current_href = None
                self.current_text = []

    request = Request(DATA_PAGE, headers={"User-Agent": "academic-reproducibility-audit/1.0"})
    with urlopen(request, timeout=60) as response:
        page = response.read().decode("utf-8", errors="replace")
    parser = LinkParser()
    parser.feed(page)
    records = []
    for raw_text, href in parser.links:
        text = " ".join(raw_text.split())
        if "Commissioner & Provider View" not in text:
            continue
        if "Incomplete Pathways" in text:
            outcome = "incomplete"
        elif "Completed Pathways" in text:
            outcome = "completed"
        else:
            continue
        match = re.search(r"\b([A-Z][a-z]{2})(\d{2})\b", text)
        if not match:
            continue
        month = pd.to_datetime(
            f"20{match.group(2)}-{match.group(1)}-01", format="%Y-%b-%d"
        )
        if not (start <= month <= end):
            continue
        records.append(
            {
                "month": month,
                "outcome": outcome,
                "link_text": text,
                "url": urljoin(DATA_PAGE, href),
                "is_revised": "revised" in text.lower(),
            }
        )
    links = pd.DataFrame(records)
    if links.empty:
        raise RuntimeError("No official workbook links found")
    # Prefer a revised version if the archive contains more than one link for a cell.
    links = links.sort_values(["month", "outcome", "is_revised"])
    links = links.drop_duplicates(["month", "outcome"], keep="last")
    return links.sort_values(["month", "outcome"]).reset_index(drop=True)


def download_files(links: pd.DataFrame, raw_dir: Path) -> pd.DataFrame:
    raw_dir.mkdir(parents=True, exist_ok=True)
    rows = list(links.itertuples(index=False))

    def fetch(row: object) -> dict[str, object]:
        suffix = Path(row.url.split("?")[0]).suffix or ".xls"
        filename = f"{row.month:%Y-%m}_{row.outcome}{suffix}"
        path = raw_dir / filename
        if not path.exists() or path.stat().st_size == 0:
            request = Request(row.url, headers={"User-Agent": "academic-reproducibility-audit/1.0"})
            with urlopen(request, timeout=90) as response:
                path.write_bytes(response.read())
            time.sleep(0.05)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return {
            **row._asdict(),
            "local_file": str(path),
            "bytes": path.stat().st_size,
            "sha256": digest,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        output = list(executor.map(fetch, rows))
    return pd.DataFrame(output)


def extract_ccg(path: Path, month: pd.Timestamp, outcome: str) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="CCG", header=None)
    header_candidates = []
    for index, row in raw.iterrows():
        values = {str(v).strip() for v in row.dropna().tolist()}
        if "Commissioner" in values and "Code" in values:
            header_candidates.append(index)
    if not header_candidates:
        raise RuntimeError(f"Could not locate CCG header in {path}")
    header_row = header_candidates[0]
    headers = []
    for col, value in enumerate(raw.iloc[header_row].tolist()):
        label = "" if pd.isna(value) else str(value).strip()
        headers.append(label or f"blank_{col}")
    frame = raw.iloc[header_row + 1 :].copy()
    frame.columns = headers
    frame = frame.loc[frame["Commissioner"].notna()].copy()
    frame = frame.loc[~frame["Commissioner"].astype(str).str.contains("England", case=False)]
    frame["month"] = month
    frame["outcome"] = outcome
    frame["commissioner_norm"] = frame["Commissioner"].map(normalize_name)
    frame["code"] = frame["Code"].astype(str).str.strip()
    # Retain source columns verbatim; downstream code can select stable measures.
    return frame


def attach_treatment(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cohorts = pd.DataFrame(COHORTS, columns=["monitor_name", "treatment_date"])
    cohorts["treatment_date"] = pd.to_datetime(cohorts["treatment_date"])
    cohorts["commissioner_norm"] = cohorts["monitor_name"].map(normalize_name)
    cohorts["commissioner_norm"] = cohorts["commissioner_norm"].replace(
        MONITOR_TO_NHS_NAME
    )

    observed = set(panel["commissioner_norm"].dropna())
    cohorts["exact_name_observed"] = cohorts["commissioner_norm"].isin(observed)
    matches = []
    for row in cohorts.itertuples(index=False):
        subset = panel.loc[panel["commissioner_norm"] == row.commissioner_norm]
        matches.append(
            {
                "monitor_name": row.monitor_name,
                "treatment_date": row.treatment_date,
                "commissioner_norm": row.commissioner_norm,
                "exact_name_observed": row.exact_name_observed,
                "codes": ";".join(sorted(set(subset["code"].dropna()))),
                "first_month": subset["month"].min() if not subset.empty else pd.NaT,
                "last_month": subset["month"].max() if not subset.empty else pd.NaT,
                "months_completed": subset.loc[subset["outcome"] == "completed", "month"].nunique(),
                "months_incomplete": subset.loc[subset["outcome"] == "incomplete", "month"].nunique(),
            }
        )
    match_table = pd.DataFrame(matches)
    treatment_map = cohorts.set_index("commissioner_norm")["treatment_date"]
    panel["treatment_date"] = panel["commissioner_norm"].map(treatment_map)
    panel["event_month"] = (
        (panel["month"].dt.year - panel["treatment_date"].dt.year) * 12
        + panel["month"].dt.month
        - panel["treatment_date"].dt.month
    )
    panel["late_aqp_cohort"] = panel["treatment_date"].notna()
    panel["primary_aqp_cohort"] = panel["treatment_date"].isin(
        [pd.Timestamp("2013-11-01"), pd.Timestamp("2014-04-01")]
    )
    return panel, match_table


def add_auditable_outcomes(panel: pd.DataFrame) -> pd.DataFrame:
    """Construct threshold outcomes from source bins without midpoint assumptions."""
    frame = panel.copy()
    weekly = []
    for column in frame.columns:
        match = re.fullmatch(r">(\d+)-(\d+)", str(column).strip())
        if match:
            weekly.append((column, int(match.group(1))))
    top = next((c for c in frame.columns if normalize_name(c) == "52 PLUS"), None)
    for column, _ in weekly:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0)
    if top is not None:
        frame[top] = pd.to_numeric(frame[top], errors="coerce").fillna(0)
    total_col = next(
        (c for c in frame.columns if normalize_name(c) == "TOTAL ALL"), None
    )
    if total_col is not None:
        frame["total_all_numeric"] = pd.to_numeric(
            frame[total_col], errors="coerce"
        )
    over6 = [c for c, lower in weekly if lower >= 6]
    over18 = [c for c, lower in weekly if lower >= 18]
    if top is not None:
        over6.append(top)
        over18.append(top)
    frame["count_over_6_weeks"] = frame[over6].sum(axis=1, min_count=1)
    frame["count_over_18_weeks"] = frame[over18].sum(axis=1, min_count=1)
    denom = frame.get("total_all_numeric")
    if denom is not None:
        positive = denom.where(denom > 0)
        frame["share_over_6_weeks"] = frame["count_over_6_weeks"] / positive
        frame["share_over_18_weeks"] = frame["count_over_18_weeks"] / positive
    return frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parent / "nhs_aqp_data"
    )
    parser.add_argument("--offline", action="store_true", help="Use supplied manifest and raw workbooks; no downloads")
    parser.add_argument("--start", default="2013-04-01")
    parser.add_argument("--end", default="2014-07-01")
    args = parser.parse_args()
    root = args.root
    raw_dir = root / "raw"
    root.mkdir(parents=True, exist_ok=True)

    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end)
    if end < start:
        raise ValueError("--end must be on or after --start")
    if args.offline:
        manifest = pd.read_csv(root / "download_manifest.csv", parse_dates=["month"])
        manifest = manifest.loc[manifest["month"].between(start, end)].copy()
        expected = len(pd.period_range(start, end, freq="M")) * 2
        if len(manifest) != expected or manifest.duplicated(["month", "outcome"]).any():
            raise RuntimeError("Incomplete or duplicate workbook manifest")
        manifest["local_file"] = [str(raw_dir / Path(x).name) for x in manifest["local_file"]]
        for row in manifest.itertuples(index=False):
            if hashlib.sha256(Path(row.local_file).read_bytes()).hexdigest() != row.sha256:
                raise RuntimeError("Raw workbook hash mismatch: " + row.local_file)
        links = manifest
    else:
        links = archive_links(start, end)
        manifest = download_files(links, raw_dir)
    frames = []
    errors = []
    for row in manifest.itertuples(index=False):
        try:
            frames.append(extract_ccg(Path(row.local_file), row.month, row.outcome))
        except Exception as exc:  # Preserve failures for audit rather than silently dropping.
            errors.append({"month": row.month, "outcome": row.outcome, "file": row.local_file, "error": repr(exc)})
    if not frames:
        raise RuntimeError("No CCG workbooks parsed")
    if errors:
        pd.DataFrame(errors).to_csv(root / "parse_errors.csv", index=False)
        raise RuntimeError("Workbook parsing failed; no partial panel is published")
    panel = pd.concat(frames, ignore_index=True, sort=False)
    panel, matches = attach_treatment(panel)
    panel = add_auditable_outcomes(panel)

    manifest["local_file"] = ["raw/" + Path(x).name for x in manifest["local_file"]]
    manifest.to_csv(root / "download_manifest.csv", index=False)
    panel.to_csv(root / "ccg_month_panel.csv", index=False)
    matches.to_csv(root / "late_aqp_cohort_audit.csv", index=False)
    pd.DataFrame(errors).to_csv(root / "parse_errors.csv", index=False)

    summary = pd.DataFrame(
        [
            {
                "archive_cells_expected": len(pd.period_range(start, end, freq="M")) * 2,
                "archive_cells_found": len(links),
                "first_month": links["month"].min(),
                "last_month": links["month"].max(),
                "parsed_workbooks": len(frames),
                "parse_errors": len(errors),
                "panel_rows": len(panel),
                "distinct_normalized_ccgs": panel["commissioner_norm"].nunique(),
                "late_cohorts_exactly_observed": int(matches["exact_name_observed"].sum()),
                "late_cohorts_total": len(matches),
            }
        ]
    )
    summary.to_csv(root / "feasibility_summary.csv", index=False)
    print(summary.to_string(index=False))
    print("\nLate-adopter audit:")
    print(matches.to_string(index=False))
    if errors:
        print("\nParse errors:")
        print(pd.DataFrame(errors).to_string(index=False))


if __name__ == "__main__":
    main()
