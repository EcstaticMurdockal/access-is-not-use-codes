#!/usr/bin/env python3
"""Reproduce the semifinal NHANES access--use analysis from public XPT files.

Data: NHANES 2017--March 2020 pre-pandemic P_DEMO, P_AUQ, and P_AUX.
The implementation follows the operational definitions and Taylor-linearized
survey variance algorithm printed in the semifinal manuscript appendix.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit, logit
from scipy.stats import t


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "nhanes_raw"
OUT = ROOT / "nhanes_reproduction_results.json"


def valid_threshold(s: pd.Series) -> pd.Series:
    return s.where(np.isfinite(s) & s.between(-10, 110))


def ear_pta(df: pd.DataFrame, side: str) -> pd.Series:
    one_a = valid_threshold(df[f"AUXU1K1{side}"])
    one_b = valid_threshold(df[f"AUXU1K2{side}"])
    one = one_a.fillna(one_b)
    parts = pd.concat(
        [
            valid_threshold(df[f"AUXU500{side}"]),
            one,
            valid_threshold(df[f"AUXU2K{side}"]),
            valid_threshold(df[f"AUXU4K{side}"]),
        ],
        axis=1,
    )
    return parts.mean(axis=1, skipna=False)


def psu_covariance(df: pd.DataFrame, influence: np.ndarray) -> np.ndarray:
    """Taylor with-replacement covariance using the complete sampled PSU frame."""
    k = influence.shape[1]
    temp = df[["SDMVSTRA", "SDMVPSU"]].copy()
    for j in range(k):
        temp[f"u{j}"] = influence[:, j]
    grouped = temp.groupby(["SDMVSTRA", "SDMVPSU"], sort=True).sum(numeric_only=True)
    cov = np.zeros((k, k))
    for _, block in grouped.groupby(level=0, sort=True):
        u = block[[f"u{j}" for j in range(k)]].to_numpy()
        m = u.shape[0]
        centered = u - u.mean(axis=0, keepdims=True)
        cov += (m / (m - 1.0)) * centered.T @ centered
    return cov


def contributing_df(df: pd.DataFrame, domain: np.ndarray) -> int:
    pairs = df.loc[domain, ["SDMVSTRA", "SDMVPSU"]].drop_duplicates()
    return int(len(pairs) - pairs["SDMVSTRA"].nunique())


def survey_logit(df: pd.DataFrame, domain: np.ndarray, y: np.ndarray, X: np.ndarray):
    w = df["WTMECPRP"].to_numpy()[domain].astype(float)
    w /= w.mean()
    yy = y[domain].astype(float)
    xx = X[domain].astype(float)
    beta = np.zeros(xx.shape[1])
    beta[0] = logit(np.average(yy, weights=w))
    converged = False
    for iteration in range(200):
        p = expit(xx @ beta)
        A = xx.T @ ((w * p * (1 - p))[:, None] * xx)
        score = xx.T @ (w * (yy - p))
        delta = np.linalg.solve(A, score)
        beta += delta
        if np.max(np.abs(delta)) < 1e-10:
            converged = True
            break
    p = expit(xx @ beta)
    A = xx.T @ ((w * p * (1 - p))[:, None] * xx)
    Ainv = np.linalg.inv(A)
    u_domain = ((w * (yy - p))[:, None] * xx) @ Ainv.T
    influence = np.zeros((len(df), xx.shape[1]))
    influence[domain] = u_domain
    cov = psu_covariance(df, influence)
    design_df = contributing_df(df, domain)
    residual_df = design_df - (np.linalg.matrix_rank(xx) - 1)
    se = np.sqrt(np.diag(cov))
    return beta, se, design_df, residual_df, converged, iteration + 1


def weighted_prevalence(df: pd.DataFrame, domain: np.ndarray, y: np.ndarray) -> float:
    w = df["WTMECPRP"].to_numpy()[domain]
    return float(np.average(y[domain], weights=w))


def main() -> None:
    demo = pd.read_sas(RAW / "P_DEMO.xpt", format="xport")
    auq = pd.read_sas(RAW / "P_AUQ.xpt", format="xport")
    aux = pd.read_sas(RAW / "P_AUX.xpt", format="xport")
    assert demo["SEQN"].is_unique and auq["SEQN"].is_unique and aux["SEQN"].is_unique
    d = demo.merge(auq, on="SEQN", how="left", validate="one_to_one")
    d = d.merge(aux, on="SEQN", how="left", validate="one_to_one")

    d["pta_r"] = ear_pta(d, "R")
    d["pta_l"] = ear_pta(d, "L")
    d["pta"] = d[["pta_r", "pta_l"]].min(axis=1, skipna=False)
    examined = d["RIDSTATR"].eq(2) & d["WTMECPRP"].gt(0)
    # The complete examined PSU frame is retained for domain variance estimation.
    frame = d.loc[examined].copy().reset_index(drop=True)
    base = frame["RIDAGEYR"].ge(70) & frame["pta"].notna()
    current_device = frame["AUQ147"].eq(1)
    hearing_aid = current_device & frame["AUQ149A"].eq(1)
    valid_wearing = frame["AUQ153"].isin([1, 2, 3, 4, 5])
    ha = base & hearing_aid & valid_wearing
    primary = ha & frame["AUQ144"].isin([1, 2, 3, 4, 5])

    # CDC AUQ144=1: less than one year; AUQ153 codes3/4: at least4 hours/day.
    recent = frame["AUQ144"].eq(1).to_numpy(dtype=float)
    regular = frame["AUQ153"].isin([3, 4]).to_numpy(dtype=float)
    female = frame["RIAGENDR"].eq(2).to_numpy(dtype=float)
    X = np.column_stack(
        [
            np.ones(len(frame)),
            recent,
            frame["pta"].to_numpy(dtype=float),
            frame["RIDAGEYR"].to_numpy(dtype=float),
            female,
        ]
    )
    domain = primary.to_numpy() & np.isfinite(X).all(axis=1)
    beta, se, design_df, residual_df, conv, iterations = survey_logit(
        frame, domain, regular, X
    )
    crit = t.ppf(0.975, residual_df)
    z = beta[1] / se[1]
    p_value = 2 * t.sf(abs(z), residual_df)
    or_est = math.exp(beta[1])
    ci = [math.exp(beta[1] - crit * se[1]), math.exp(beta[1] + crit * se[1])]

    recent_domain = domain & (recent == 1)
    earlier_domain = domain & (recent == 0)
    counts_153 = (
        frame.loc[ha, "AUQ153"].value_counts().sort_index().astype(int).to_dict()
    )
    counts_144 = (
        frame.loc[ha, "AUQ144"].value_counts().sort_index().astype(int).to_dict()
    )
    out = {
        "operational_definitions": {"recent_test": "AUQ144=1: less than one year ago", "regular_wearing": "AUQ153=3 or4: at least four hours/day"},
        "source_rows": {"P_DEMO": len(demo), "P_AUQ": len(auq), "P_AUX": len(aux)},
        "design": {
            "strata": int(frame["SDMVSTRA"].nunique()),
            "psus": int(frame[["SDMVSTRA", "SDMVPSU"]].drop_duplicates().shape[0]),
            "full_design_df": int(
                frame[["SDMVSTRA", "SDMVPSU"]].drop_duplicates().shape[0]
                - frame["SDMVSTRA"].nunique()
            ),
        },
        "sample_flow": {
            "examined_age_70_plus": int((frame["RIDAGEYR"] >= 70).sum()),
            "base_complete_bilateral_audiometry": int(base.sum()),
            "base_current_device": int((base & current_device).sum()),
            "base_current_hearing_aid_valid_wearing": int(ha.sum()),
            "primary_known_test_recency": int(domain.sum()),
        },
        "raw_counts": {
            "AUQ153_among_current_hearing_aid_users": {str(k): int(v) for k, v in counts_153.items()},
            "AUQ144_among_current_hearing_aid_users": {str(k): int(v) for k, v in counts_144.items()},
        },
        "weighted_regular_wearing": {
            "recent_test": weighted_prevalence(frame, recent_domain, regular),
            "earlier_or_never": weighted_prevalence(frame, earlier_domain, regular),
            "unadjusted_difference": weighted_prevalence(frame, recent_domain, regular)
            - weighted_prevalence(frame, earlier_domain, regular),
        },
        "primary_adjusted_logit": {
            "covariates": ["intercept", "recent_test", "better_ear_pta", "recorded_age", "female"],
            "converged": conv,
            "iterations": iterations,
            "beta_recent": float(beta[1]),
            "se_recent": float(se[1]),
            "odds_ratio": or_est,
            "ci_95": ci,
            "t_stat": float(z),
            "p_value": float(p_value),
            "domain_df": design_df,
            "residual_df": residual_df,
        },
    }
    def json_default(obj):
        if isinstance(obj, np.generic):
            return obj.item()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    rendered = json.dumps(out, indent=2, ensure_ascii=False, default=json_default)
    OUT.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
