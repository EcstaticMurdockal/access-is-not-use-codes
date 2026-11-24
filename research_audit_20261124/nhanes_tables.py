#!/usr/bin/env python3
"""Render all audited NHANES specifications and three main-text contrasts."""
from pathlib import Path
import json
R=Path(__file__).resolve().parent
labels=['Primary adjustment','Testing <5 years','Unadjusted','Age and sex only','Wearing at least 8 hours/day','Categorical age','Quadratic PTA added','Education and income added','Testing <5 years; education/income','Primary adjustment; same complete cases','Ever-tested participants only','Restricted to age 70--79','Full-design degrees of freedom']
a=json.loads((R/'nhanes_sensitivity_results.json').read_text())['specifications'];assert len(a)==len(labels)==13
for filename,indices in [('nhanes_all_specs_table.tex',range(13)),('nhanes_key_specs_table.tex',[0,1,7])]:
 lines=[r'\begin{tabular}{@{}lrrr@{}}',r'\toprule',r'Specification & $n$ & Odds ratio (95\% CI) & $p$\\',r'\midrule']
 for i in indices:
  v=a[i];label=labels[i].replace('<',r'$<$')
  lines.append(f"{label} & {v['n']} & {v['odds_ratio']:.2f} ({v['ci95_low']:.2f}--{v['ci95_high']:.2f}) & {v['p_value']:.3f}"+r'\\')
 lines += [r'\bottomrule',r'\end{tabular}']
 (R/filename).write_text('\n'.join(lines)+'\n')
