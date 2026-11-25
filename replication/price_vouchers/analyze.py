"""Reanalyse the three randomly assigned free-voucher arms of PRICE."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

import numpy as np
import pandas as pd
from scipy.stats import t

SOURCE = ("https://app.box.com/index.php?rm=box_download_shared_file"
          "&shared_name=pscwad5h7mdxdh1w5ytvjmjq3gp9phgu&file_id=f_194275533900")
HASH = "6f6cc75208c3665cd64379c4093f1e96b8b6e9cf65f0cd3bd328ebc8390c707a"
FIELDS = ["school_code", "county", "glass_type", "glass_buy2", "wear_glasses2", "glass_have_bl"]
OUTCOMES = {"Paid purchase": "glass_buy2", "Observed wear": "wear_glasses2"}
CONTRAST = np.array([-1., .5, .5])

def read_trial(archive):
    raw = Path(archive).read_bytes() if archive else urllib.request.urlopen(SOURCE, timeout=120).read()
    if hashlib.sha256(raw).hexdigest() != HASH:
        raise ValueError("PRICE archive checksum mismatch")
    with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
        with zipped.open("data for imputation.dta") as handle:
            data = pd.read_stata(io.BytesIO(handle.read()), columns=FIELDS, convert_categoricals=False)
    if len(data) != 882 or data.groupby("school_code").glass_type.nunique().max() != 1:
        raise ValueError("Unexpected assigned sample")
    data = data.loc[data.glass_type.isin([1, 2, 3])].copy()
    expected = [(253, 252, 32, 80), (187, 183, 39, 43), (185, 182, 38, 32)]
    actual = [(len(g), g.glass_buy2.count(), g.glass_buy2.sum(), g.wear_glasses2.sum())
              for _, g in data.groupby("glass_type")]
    if actual != expected or not data.glass_buy2.isna().equals(data.wear_glasses2.isna()):
        raise ValueError("Source outcomes disagree with published Table 2")
    return data

def fit(data, y, adjusted=False, contrast=CONTRAST, family_size=1):
    obs = data.dropna(subset=[y]).copy()
    groups = pd.Categorical(obs.school_code).codes
    n_school = len(np.unique(groups))
    design = np.asarray(pd.get_dummies(obs.glass_type).reindex(columns=[1, 2, 3],fill_value=0),dtype=float)
    if adjusted:
        county = pd.get_dummies(obs.county,drop_first=True).to_numpy(dtype=float)
        design = np.column_stack([design, county, obs.glass_have_bl])
    X = design
    response = obs[y].to_numpy()
    if np.linalg.matrix_rank(X) < X.shape[1]:
        raise ValueError("Singular design")
    bread = np.linalg.inv(X.T @ X)
    beta = bread @ X.T @ response
    scores = np.zeros((n_school,X.shape[1]))
    np.add.at(scores, groups, X*(response-X@beta)[:,None])
    cov = (bread @ scores.T @ scores @ bread) * n_school/(n_school-1) * (len(obs)-1)/(len(obs)-X.shape[1])
    c = np.pad(contrast, (0,X.shape[1]-3))
    estimate, se = c@beta, np.sqrt(c@cov@c)
    critical = t.ppf(1 - 0.05 / (2 * family_size), n_school - 1)
    return {"n":len(obs),"schools":n_school,"rd_pp":100*estimate,"se_pp":100*se,
            "low_pp":100*(estimate-critical*se),"high_pp":100*(estimate+critical*se),
            "p_two_sided":2*t.sf(abs(estimate/se),n_school-1)}

def missing_bounds(data, name):
    arms = data.groupby("glass_type")[name].agg(["size","count","sum"])
    minimum = arms["sum"]/arms["size"]
    maximum = (arms["sum"]+arms["size"]-arms["count"])/arms["size"]
    return [100*(-maximum.iloc[0]+minimum.iloc[1:].mean()),100*(-minimum.iloc[0]+maximum.iloc[1:].mean())]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive",type=Path,help="existing verified source zip; otherwise downloaded in memory")
    parser.add_argument("--output",type=Path,default=Path(__file__).with_name("results.json"))
    args = parser.parse_args()
    trial = read_trial(args.archive)
    out = {}
    for label, variable in OUTCOMES.items():
        school = trial.groupby(["school_code","glass_type"],as_index=False)[variable].mean()
        out[label] = {
            "arms": [{"arm":int(arm), "n":len(g),"schools":int(g.school_code.nunique()),
                      "seen":int(g[variable].count()),"yes":int(g[variable].sum())} for arm,g in trial.groupby("glass_type")],
            "available_case":fit(trial,variable),
            "simultaneous_two_outcomes":fit(trial,variable,family_size=2),
            "simultaneous_three_contrasts":fit(trial,variable,family_size=3),
            "county_and_baseline_possession":fit(trial,variable,adjusted=True),
            "equal_school_weight":fit(school,variable),
            "completion_bounds_pp":missing_bounds(trial,variable),
            "fifteen_vs_free":fit(trial,variable,contrast=np.array([-1,1,0])),
            "thirty_vs_free":fit(trial,variable,contrast=np.array([-1,0,1])),
            "thirty_vs_fifteen":fit(trial,variable,contrast=np.array([0,-1,1])),
        }
    trial["purchase_minus_wear"] = trial.glass_buy2-trial.wear_glasses2
    out["paired_difference_in_outcome_effects"] = fit(trial,"purchase_minus_wear")
    out["paired_difference_adjusted"] = fit(trial,"purchase_minus_wear",adjusted=True)
    out["paired_difference_simultaneous_three"] = fit(trial,"purchase_minus_wear",family_size=3)
    args.output.write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
if __name__ == "__main__":
    main()
