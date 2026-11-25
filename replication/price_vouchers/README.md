# Secondary analysis of the PRICE randomized eyeglass trial

Wang X, Congdon N, Ma Y, et al. PLoS ONE 12 (2017), e0187808. DOI 10.1371/journal.pone.0187808. The investigators ran the trial and collected the data. This module calculates an exploratory contrast from their individual-level archive, comparing the two paid-upgrade menus with the free-only menu. The equally weighted mix of the two upgrade prices and the paired comparison of effects were chosen for this secondary analysis after the original results were public.

## Reproduce

With Python 3.11, install the packages in requirements.txt, then run:

```sh
python -m pip install -r requirements.txt
python analyze.py
python plot.py
```

The plot requires a locally available licensed Arial font. Pass `--arial-dir DIRECTORY` if it is installed outside the usual font path. The numerical analysis has no font requirement.

The source is the [Stanford REAP project archive](https://sccei.fsi.stanford.edu/reap/research/seeing_is_learning), under **Access our data → PRICE study → PRICE Dta and Do.zip**. Its [public folder](https://app.box.com/s/pscwad5h7mdxdh1w5ytvjmjq3gp9phgu) supplies the file directly. The script checks the SHA-256 digest before reading the six fields used for the analysis from `data for imputation.dta`. If the direct download no longer works, download the archive from the study page and use `python analyze.py --archive "PRICE Dta and Do.zip"`. The workbook name denotes the authors' pre-imputation input. Raw records and child identifiers are excluded from this supplement. Output consists of aggregate statistics only.

## Design and measures

Treatment was assigned by school before refraction, stratified by county, school size and number failing screening. The study authors allocated ten additional schools directly to the prescription-only control. We exclude the entire prescription-only arm. The analysis population comprises 625 eligible children in 90 voucher-arm schools with complete outcomes for 617 children. Both upgrade arms offered the same free prescription glasses as the free-only arm, plus the option of buying scratch-resistant lenses and a different frame. Families redeemed their vouchers at the county hospital. Outcomes are purchase of any spectacles using project records and reports of outside purchase, and wear directly observed during an unannounced visit at six months. A paid purchase differs from receipt of free glasses.

For each binary outcome we contrast half the sum of the student means in the $15 and $30 upgrade arms with the free-only arm mean. The coefficient on the paired outcome (purchase indicator minus wear indicator) measures the difference between these assignment effects and preserves their covariance. It is not a proportion of pupils who bought glasses but never wore them. Reported confidence intervals use a school-cluster sandwich covariance, CR1 finite-sample factor and Student t(89) critical values. We report pointwise 95% intervals, Bonferroni intervals for the two outcome effects, and Bonferroni intervals for all three displayed contrasts. These intervals apply to the three listed contrasts and do not account for choosing this secondary analysis after the trial was published. This is model-assisted large-cluster inference, not an exact randomization test. The public analysis file lacks the original randomization block identifier.

Sensitivity results include covariate-adjusted contrasts (county fixed effects and whether a child brought spectacles to the baseline screening), equal weighting of schools, each upgrade price separately, and the range of unadjusted contrasts across all binary completions of the eight missing outcomes. The completion ranges are deterministic sensitivity intervals for the realized sample with no adjustment for sampling variation. Analyses retain original school assignment regardless of voucher redemption. Results identify a program-offer comparison for these students under the randomization and follow-up assumptions; no service capacity, untreated incumbent outcomes, population price elasticity or welfare value is estimated.
