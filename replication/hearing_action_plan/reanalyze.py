"""Reproduce six-week factorial contrasts from Ismail et al. (2022), Tables 3 and 4."""
import csv
from pathlib import Path
from math import sqrt
from scipy.stats import t

ROOT = Path(__file__).resolve().parent
WEIGHTS = {
    "Plan, averaged over prompt assignment": [-0.5, -0.5, 0.5, 0.5],
    "Prompt, averaged over plan assignment": [-0.5, 0.5, -0.5, 0.5],
    "Interaction (difference in plan effects)": [1, -1, -1, 1],
    "Plan without prompt": [-1, 0, 1, 0],
    "Plan with prompt": [0, -1, 0, 1],
}
OUTCOMES = {"questionnaire": 100, "logged": 24}


def observed_total_range(n, rounded_mean, measure):
    # The self-report total is uniquely identified because each individual response
    # lies on a 0, 25, 50, 75, 100 grid and only the mean was rounded.
    if measure == "questionnaire":
        candidates = [25*k for k in range(4*n + 1)
                      if abs(25*k/n - rounded_mean) <= 0.05 + 1e-9]
        if len(candidates) != 1:
            raise ValueError("Published questionnaire mean does not identify one total.")
        return candidates[0], candidates[0]
    # For the continuous log outcome, allow for publication rounding of the mean.
    return (rounded_mean - 0.05)*n, (rounded_mean + 0.05)*n


def contrast(arms, outcome, weights):
    high = OUTCOMES[outcome]
    estimates, variance_terms, sample_sizes = [], [], []
    lower_terms, upper_terms = [], []
    for arm, weight in zip(arms, weights):
        n = int(arm[f"{outcome}_n"])
        randomized = int(arm["randomized"])
        published_mean = float(arm[f"{outcome}_mean"])
        sd = float(arm[f"{outcome}_sd"])
        total_lo, total_hi = observed_total_range(n, published_mean, outcome)
        mean = (total_lo + total_hi)/(2*n)
        estimates.append(weight * mean)
        variance_terms.append((weight * sd)**2/n)
        sample_sizes.append(n)
        # The endpoint ranges bound all observed-assignment means over any
        # admissible completion. They do not quantify sampling uncertainty.
        arm_lo = total_lo/randomized
        arm_hi = (total_hi + (randomized - n)*high)/randomized
        lower_terms.append(min(weight*arm_lo, weight*arm_hi))
        upper_terms.append(max(weight*arm_lo, weight*arm_hi))
    estimate = sum(estimates)
    variance = sum(variance_terms)
    degrees = variance**2/sum(term**2/(n - 1)
                              for term, n in zip(variance_terms, sample_sizes))
    radius = t.ppf(0.975, degrees)*sqrt(variance)
    return [estimate, estimate - radius, estimate + radius,
            sum(lower_terms), sum(upper_terms)]


def write_tipping_analysis(arms):
    total = [0.0, 0.0]
    missing = [0, 0]
    assigned = [0, 0]
    for arm in arms:
        plan = int(arm["plan"])
        n = int(arm["questionnaire_n"])
        full = int(arm["randomized"])
        lo, hi = observed_total_range(n, float(arm["questionnaire_mean"]), "questionnaire")
        assert lo == hi
        total[plan] += lo
        missing[plan] += full - n
        assigned[plan] += full
    assert assigned[0] == assigned[1] and missing[1] > 0
    delta = total[1] - total[0]
    # A zero full-assignment contrast requires treated and untreated totals to match.
    threshold = (100 * missing[0] - delta)/missing[1]
    with (ROOT / "tipping.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["observed_sum_no_plan", "observed_sum_plan", "missing_no_plan",
                         "missing_plan", "max_plan_missing_mean_at_zero_if_no_plan_missing_mean_is_100"])
        writer.writerow([total[0], total[1], missing[0], missing[1], round(threshold,5)])


def main():
    with (ROOT / "arms.csv").open() as file:
        arms = sorted(csv.DictReader(file), key=lambda a: (int(a['plan']), int(a['prompt'])))
    if [(int(a["plan"]), int(a["prompt"])) for a in arms] != [(0,0),(0,1),(1,0),(1,1)]:
        raise ValueError("Each factorial cell must occur once.")
    write_tipping_analysis(arms)
    records = {}
    with (ROOT / "contrasts.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["outcome", "contrast", "complete_case", "ci_lower", "ci_upper",
                         "completion_lower", "completion_upper"])
        for measure in OUTCOMES:
            for label, weights in WEIGHTS.items():
                values = contrast(arms, measure, weights)
                writer.writerow([measure, label, *(f"{v:.5f}" for v in values)])
                count = sum(int(arm[f"{measure}_n"]) for arm, weight in zip(arms, weights) if weight)
                records[(measure, label)] = (count, values)
    write_table(records)


def write_table(records):
    average = "Plan, averaged over prompt assignment"
    interaction = "Interaction (difference in plan effects)"
    first = records["logged", "Plan without prompt"][1][0]
    second = records["logged", "Plan with prompt"][1][0]
    assert abs(records["logged", average][1][0] - (first + second)/2) < 1e-10
    assert abs(records["logged", interaction][1][0] - (second - first)) < 1e-10
    rows = [
        ("Use in difficult situations (pp)", "questionnaire", average),
        ("Device on (h/day), averaged", "logged", average),
        (r"\quad Plan without a reminder", "logged", "Plan without prompt"),
        (r"\quad Plan with a reminder", "logged", "Plan with prompt"),
        (r"\quad Interaction (with minus without)", "logged", interaction),
    ]
    lines = [r'\begin{tabularx}{\linewidth}{@{}Xrcc@{}}\toprule',
             r'Six-week contrast & Observed & Estimate [95\% CI] & Completion range\\\midrule']
    for title, outcome, contrast_name in rows:
        count, (estimate, lo, hi, completion_lo, completion_hi) = records[outcome, contrast_name]
        lines.append(f"{title} & {count} & ${estimate:.2f}\\ [{lo:.2f},{hi:.2f}]$ & "
                     f"$[{completion_lo:.2f},{completion_hi:.2f}]$" + r'\\')
    lines.extend([r'\bottomrule',r'\end{tabularx}'])
    (ROOT / "contrasts_table.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
