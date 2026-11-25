"""Estimate unadjusted assignment contrasts in Jiang et al., Figure 3."""
import csv
from math import sqrt
from pathlib import Path
from scipy.stats import norm, t

ROOT = Path(__file__).resolve().parent
WEIGHTS = {"Support mixture":[.5,.5,-1], "Physician vs self":[1,0,-1],
           "Remote vs self":[0,1,-1]}
ARMS = ["Physician-supported","Remote-supported","Self-fitting"]
Z = norm.ppf(.975)


def weighted_sum(weights, values):
    return sum(w*x for w,x in zip(weights,values))


def binomial_contrast(weights, successes, totals):
    rates = [x/n for x,n in zip(successes,totals)]
    var = sum(w*w*p*(1-p)/(n-1) for w,p,n in zip(weights,rates,totals))
    return weighted_sum(weights,rates),sqrt(var)


def summarize(cells, weights):
    n = [int(c["observed"]) for c in cells]
    full = [int(c["randomized"]) for c in cells]
    deaths = [int(c["known_deaths"]) for c in cells]
    yes = [int(c["regular_wear_reports"]) for c in cells]
    unknown = [N-k-d for N,k,d in zip(full,n,deaths)]
    estimate,se = binomial_contrast(weights,yes,n)
    worst = [x + (m if w < 0 else 0) for x,m,w in zip(yes,unknown,weights)]
    best = [x + (m if w > 0 else 0) for x,m,w in zip(yes,unknown,weights)]
    lo, se_lo = binomial_contrast(weights,worst,full)
    hi, se_hi = binomial_contrast(weights,best,full)
    assert lo <= hi
    # Bonferroni combination of two 97.5% one-sided normal endpoint limits.
    bin_values = [estimate,estimate-Z*se,estimate+Z*se,lo,hi,lo-Z*se_lo,hi+Z*se_hi]
    means = [float(c["power_on_mean"]) for c in cells]
    # Figure 3(a) used t intervals. Recover each cell's SE directly from interval width.
    terms = [(w*(float(c["power_on_ci_hi"])-float(c["power_on_ci_lo"])) /
              (2*t.ppf(.975,k-1)))**2 for w,c,k in zip(weights,cells,n)]
    var = sum(terms)
    df = var**2/sum(v**2/(k-1) for v,k in zip(terms,n))
    est = weighted_sum(weights,means)
    radius = t.ppf(.975,df)*sqrt(var)
    return [100*v for v in bin_values] + [est,est-radius,est+radius]


def main():
    with (ROOT/"arm_summaries.csv").open() as file:
        data = {(int(r["month"]),r["arm"]):r for r in csv.DictReader(file)}
    with (ROOT/"results.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["month","contrast","respondent_diff_pp","respondent_ci_lo","respondent_ci_hi",
                         "min_sample_diff","max_sample_diff","outer95_lo","outer95_hi",
                         "power_on_diff_h","power_on_ci_lo","power_on_ci_hi"])
        for month in [1,3,12]:
            cells = [data[month,a] for a in ARMS]
            for name,weights in WEIGHTS.items():
                writer.writerow([month,name,*(round(x,5) for x in summarize(cells,weights))])
if __name__ == "__main__":
    main()
