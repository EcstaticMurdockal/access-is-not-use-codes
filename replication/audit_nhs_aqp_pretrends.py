#!/usr/bin/env python3
"""Pre-trend feasibility audit for the NHS adult-hearing AQP design.

This script does not estimate a treatment effect. It checks whether the two
potentially usable late-adopter cohorts have visibly different pre-treatment
trends from CCGs classified as non-choice in Monitor Annex 1. Monitor status is
a research snapshot, not a longitudinal treatment registry; that limitation is
preserved in every output.
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from math import erfc, sqrt


ROOT = Path(__file__).resolve().parent
PANEL = ROOT / "nhs_aqp_data" / "ccg_month_panel.csv"
MONITOR_TEXT = ROOT / "monitor_aqp_annexes.txt"
OUT = ROOT / "nhs_aqp_pretrend_audit"

# Local primary evidence states that Hounslow's adult-audiology AQP contract
# was live from November 2012, so it is already treated when this panel begins.
KNOWN_PRETREATED_CODES = {"07Y"}


ALIASES = {
    "NHS BARKING DAGENHAM CCG": "NHS BARKING AND DAGENHAM CCG",
    "NHS BIRMINGHAM CROSS CITY CCG": "NHS BIRMINGHAM CROSSCITY CCG",
    "NHS BRIGHTON HOVE CCG": "NHS BRIGHTON AND HOVE CCG",
    "NHS CASTLE POINT RAYLEIGH AND ROCHFORD CCG": "NHS CASTLE POINT AND ROCHFORD CCG",
    "NHS GREAT YARMOUTH WAVENEY CCG": "NHS GREAT YARMOUTH AND WAVENEY CCG",
    "NHS HASTINGS ROTHER CCG": "NHS HASTINGS AND ROTHER CCG",
    "NHS HEYWOOD MIDDLETON ROCHDALE CCG": "NHS HEYWOOD MIDDLETON AND ROCHDALE CCG",
    "NHS KERNOW": "NHS KERNOW CCG",
    "NHS MANSFIELD ASHFIELD CCG": "NHS MANSFIELD AND ASHFIELD CCG",
    "NHS NORTH EAST WEST DEVON CCG": "NHS NORTHERN EASTERN AND WESTERN DEVON CCG",
    "NHS NOTTINGHAM NORTH EAST CCG": "NHS NOTTINGHAM NORTH AND EAST CCG",
    "NHS SOUTH EAST STAFFS AND SEISDON AND PENINSULAR CCG": "NHS SOUTH EAST STAFFORDSHIRE AND SEISDON PENINSULA CCG",
    "NHS TELFORD WREKIN CCG": "NHS TELFORD AND WREKIN CCG",
    "NHS WEST LONDON K C QPP CCG": "NHS WEST LONDON CCG",
}


def norm(value: object) -> str:
    text = "" if pd.isna(value) else str(value).upper().replace("&AMP;", "&")
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def monitor_status() -> pd.DataFrame:
    rows = []
    for line in MONITOR_TEXT.read_text(errors="replace").splitlines():
        match = re.match(r"^\s*(NHS .+?(?: CCG|Kernow))\s{2,}(yes|no)\s{2,}(.*)$", line)
        if not match:
            continue
        name, status, date = match.groups()
        name_norm = ALIASES.get(norm(name), norm(name))
        rows.append({"monitor_name": name.strip(), "name_norm": name_norm,
                     "monitor_choice": status, "monitor_date_text": date.strip()})
    # Two source-table rows wrap across lines in pdftotext and are supplied
    # explicitly rather than silently discarded by the line parser.
    rows.extend([
        {"monitor_name": "NHS Kernow", "name_norm": "NHS KERNOW CCG",
         "monitor_choice": "yes", "monitor_date_text": "01/04/2013"},
        {"monitor_name": "NHS South East Staffs and Seisdon and Peninsular CCG",
         "name_norm": "NHS SOUTH EAST STAFFORDSHIRE AND SEISDON PENINSULA CCG",
         "monitor_choice": "yes", "monitor_date_text": "01/11/2012"},
    ])
    frame = pd.DataFrame(rows).drop_duplicates("name_norm", keep="last")
    return frame


def fit_pretrend(data: pd.DataFrame, outcome: str) -> dict[str, float]:
    d = data[["code", "month", "treated", "time_index", outcome]].dropna().copy()
    interaction = (d["treated"] * d["time_index"]).rename("treated_time")
    unit = pd.get_dummies(d["code"].astype(str), prefix="u", drop_first=True, dtype=float)
    month = pd.get_dummies(d["month"].astype(str), prefix="m", drop_first=True, dtype=float)
    xdf = pd.concat([
        pd.Series(1.0, index=d.index, name="intercept"), unit, month, interaction
    ], axis=1)
    X = xdf.to_numpy(dtype=float)
    y = d[outcome].to_numpy(dtype=float)
    inv = np.linalg.pinv(X.T @ X)
    coef = inv @ X.T @ y
    resid = y - X @ coef
    groups = d["code"].astype(str).to_numpy()
    meat = np.zeros((X.shape[1], X.shape[1]))
    for group in np.unique(groups):
        mask = groups == group
        score = X[mask].T @ resid[mask]
        meat += np.outer(score, score)
    n, k = X.shape
    G = len(np.unique(groups))
    cr1 = (G / (G - 1)) * ((n - 1) / max(n - k, 1))
    vcov = cr1 * inv @ meat @ inv
    idx = xdf.columns.get_loc("treated_time")
    beta = float(coef[idx])
    se = float(np.sqrt(max(vcov[idx, idx], 0)))
    z = abs(beta / se) if se > 0 else np.inf
    p = float(erfc(z / sqrt(2)))  # normal reference; few-cluster caveat retained
    return {"beta": beta, "se": se, "ci_low": beta - 1.96 * se,
            "ci_high": beta + 1.96 * se, "p": p, "n": len(d),
            "clusters": G}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(PANEL, parse_dates=["month", "treatment_date"], low_memory=False)
    panel["name_norm"] = panel["commissioner_norm"].map(norm)
    status = monitor_status()
    merged = panel.merge(status, on="name_norm", how="left", validate="many_to_one")
    crosswalk = (
        merged[["code", "Commissioner", "name_norm", "monitor_choice", "monitor_date_text"]]
        .drop_duplicates().sort_values("code")
    )
    crosswalk.to_csv(OUT / "monitor_status_crosswalk.csv", index=False)

    audits = []
    leave_one = []
    outcomes = ["share_over_6_weeks", "share_over_18_weeks",
                "count_over_6_weeks", "count_over_18_weeks",
                "total_all_numeric"]
    cohort_dates = [pd.Timestamp("2013-11-01"), pd.Timestamp("2014-04-01")]
    incomplete = merged.loc[merged["outcome"].eq("incomplete")].copy()

    for cohort_date in cohort_dates:
        treated_codes = sorted(
            code for code in incomplete.loc[
                incomplete["treatment_date"].eq(cohort_date), "code"
            ].unique() if code not in KNOWN_PRETREATED_CODES
        )
        pre = incomplete.loc[incomplete["month"].lt(cohort_date)].copy()
        pre = pre.loc[~pre["code"].isin(KNOWN_PRETREATED_CODES)].copy()
        pre = pre.loc[pre["code"].isin(treated_codes) | pre["monitor_choice"].eq("no")].copy()
        pre["treated"] = pre["code"].isin(treated_codes).astype(int)
        pre["time_index"] = (pre["month"].dt.year - pre["month"].dt.year.min()) * 12 + pre["month"].dt.month

        for outcome in outcomes:
            result = fit_pretrend(pre, outcome)
            audits.append({"cohort_date": cohort_date.date(), "outcome": outcome,
                           "treated_ccgs": len(treated_codes),
                           "control_ccgs": pre.loc[pre.treated.eq(0), "code"].nunique(), **result})
            for dropped in treated_codes:
                subset = pre.loc[pre["code"].ne(dropped)]
                loo = fit_pretrend(subset, outcome)
                leave_one.append({"cohort_date": cohort_date.date(), "outcome": outcome,
                                  "dropped_treated_ccg": dropped, **loo})

        plot_data = pre.groupby(["month", "treated"], as_index=False).apply(
            lambda x: pd.Series({
                "share_over_6_weeks": np.average(
                    x["share_over_6_weeks"].fillna(0),
                    weights=x["total_all_numeric"].clip(lower=1)
                ),
                "share_over_18_weeks": np.average(
                    x["share_over_18_weeks"].fillna(0),
                    weights=x["total_all_numeric"].clip(lower=1)
                ),
            }), include_groups=False
        ).reset_index(drop=True)
        plot_data.to_csv(OUT / f"raw_pretrend_{cohort_date:%Y_%m}.csv", index=False)
        fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharex=True)
        for ax, outcome, title in zip(
            axes,
            ["share_over_6_weeks", "share_over_18_weeks"],
            ["Incomplete share >6 weeks", "Incomplete share >18 weeks"],
        ):
            for treated, group in plot_data.groupby("treated"):
                ax.plot(group["month"], group[outcome], marker="o",
                        label="late-adopter cohort" if treated else "Monitor non-choice")
            ax.set_title(title)
            ax.set_ylabel("weighted share")
            ax.tick_params(axis="x", rotation=45)
            ax.grid(alpha=.25)
        axes[0].legend(frameon=False)
        fig.suptitle(f"Raw pre-treatment trends: {cohort_date:%Y-%m} cohort")
        fig.tight_layout()
        fig.savefig(OUT / f"raw_pretrend_{cohort_date:%Y_%m}.png", dpi=180)
        plt.close(fig)

    audit = pd.DataFrame(audits)
    loo = pd.DataFrame(leave_one)
    audit.to_csv(OUT / "pretrend_slope_audit.csv", index=False)
    loo.to_csv(OUT / "leave_one_treated_out.csv", index=False)

    loo_summary = loo.groupby(["cohort_date", "outcome"]).agg(
        loo_beta_min=("beta", "min"), loo_beta_max=("beta", "max"),
        loo_p_min=("p", "min"), loo_p_max=("p", "max")
    ).reset_index()
    report = audit.merge(loo_summary, on=["cohort_date", "outcome"], how="left")
    report.to_csv(OUT / "pretrend_acceptance_table.csv", index=False)

    summary = pd.DataFrame([{
        "monitor_rows_parsed": len(status),
        "monitor_no_rows": int(status.monitor_choice.eq("no").sum()),
        "panel_ccgs_with_monitor_status": int(crosswalk.monitor_choice.notna().sum()),
        "panel_ccgs_without_monitor_status": int(crosswalk.monitor_choice.isna().sum()),
        "warning": "Monitor status is a research snapshot, not a longitudinal registry."
    }])
    summary.to_csv(OUT / "audit_summary.csv", index=False)
    print(summary.to_string(index=False))
    print(report.to_string(index=False))


if __name__ == "__main__":
    main()
