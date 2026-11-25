"""Run on the supplied analysis_panel.csv with NumPy and SciPy."""
import argparse
import csv
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.stats import t, ttest_ind

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("panel", type=Path)
args = parser.parse_args()
states = defaultdict(dict)
treated = set()
with args.panel.open() as f:
    for row in csv.DictReader(f):
        s = row["state"]
        states[s][int(row["YEAR"])] = np.log(float(row["OP_VISITS_PER_1000_BENES"]))
        if int(row["treated"]): treated.add(s)
assert len(states) == 25 and len(treated) == 9
years = list(range(2009, 2019))
assert all(sorted(v) == years for v in states.values())
controls = sorted(set(states) - treated)
def mean(series, group): return np.mean([series[s] for s in group])
change = {s: np.mean([v[y] for y in years[5:]]) - np.mean([v[y] for y in years[:5]]) for s,v in states.items()}
beta = mean(change, treated) - mean(change, controls)
def group_meat(group):
    return sum((change[s]-mean(change,group))**2 for s in group)/len(group)**2
n, k, g = 250, 35, 25
se = np.sqrt(g/(g-1)*(n-1)/(n-k)*(group_meat(treated)+group_meat(controls)))
q=t.ppf(.975,24)
print("Two-period beta:",beta,"CR1 se:",se,"95% percent interval:", 100*np.expm1([beta-q*se,beta+q*se]))
sample1=[change[s] for s in sorted(treated)]
sample2=[change[s] for s in controls]
welch=ttest_ind(sample1,sample2,equal_var=False)
print("Welch clustered-change check: beta, df, two-sided p, 95% interval (%):", beta, welch.df, welch.pvalue,100*np.expm1(welch.confidence_interval()))
# Descriptive scale for a persistent untreated linear differential drift over all ten years.
span = np.mean(years[5:])-np.mean(years[:5])
print("Break-even untreated differential trend (log points x 100/year):",100*beta/span)
for delta in [-.005,0,.005]:
    print("Hypothetical annual drift:",delta,"adjusted estimate and CI, percent:",100*np.expm1(np.array([beta,beta-q*se,beta+q*se])-span*delta))
