# Access Is Not Use — finals replication

Version v1.4.0 contains the numerical results, data, code and figure sources for the finals manuscript. RESULTS_MAP.csv identifies the inputs, outputs and rebuilding commands for the figures and tables. Download the release archive or clone the matching tag:

    git clone --branch v1.4.0 --depth 1 https://github.com/EcstaticMurdockal/access-is-not-use-codes.git
    cd access-is-not-use-codes

## Reproduce the numerical results

Create and activate a Python 3.12 virtual environment. From the extracted archive root, run:

```sh
python -m pip install -r requirements-finals.txt
python run_finals_replication.py
```

The full command uses public downloads for the CMS, Census, PRICE and Jiang inputs (about 200 MB). SHA-256 checks identify exact releases. The PRICE workbook stays in memory and only aggregate results are written. The CMS and Census raw files are cached under their module. The code stops if any stage fails. `RESULTS_MAP.csv` links the figures and tables to their inputs, scripts and outputs. Each empirical module has its own README. For baseline computations using the included data, run `python reproduce_all.py --analysis-only`. To regenerate the eyeglass and Medicare plots, use the plot commands in their READMEs with an installed copy of Arial.

The complete numerical pipeline was rerun from an extracted release. See `replication/clean_reproduction/2026-11-25-validation.json` for input treatment, checks, and new result hashes. The waiting-list and registration analyses and the booking checks run offline. From the archive root, run the scripts below with Python 3. The Lewisham PDF check requires Poppler's pdftotext. The parliamentary return is archived as HTML and requires only the Python standard library. Each module README identifies its source, population and unit. To regenerate the signed wait-gap figure, run the plot command in replication/uk_queues/README.md.

    python replication/uk_queues/reproduce.py
    python replication/london_queues/verify_lewisham_queues.py
    python replication/ni_audiology/reproduce.py
    python replication/korea_registration/standardize.py
    python replication/booking_release/check_appointment_release.py

The proof checks cover the constrained optimum, cross-group adoption, buyer surplus, one-sided capacity responses, individual use and benefit, and the open-ended device-age stock. The `targeted_buyer_surplus` result re-solves the market after small subsidy increases. In the three Appendix A.3 examples the adoption derivative is 5/12 throughout and the target group's surplus derivatives are -1/16, 0 and 1/16, per unit increase in the subsidy rate. Run the checks independently with the Python standard library. The baseline model runner also compares its actual age projections to the cohort ledger.

    python replication/model_checks/check_revision.py

The policy ranking bounds use the same two-group reference equilibrium. Run `python replication/model_checks/ranking_bounds.py` to rebuild `ranking_bounds.json` and `ranking_bounds_table.tex` in that directory. The script checks a ranking reversal by solving policy changes under two valuation distributions. The midpoint bid is a sensitivity assumption. At fixed cost and policy responses, changing the external-benefit weight from 0.50 to 0.40 changes the H lower bound from +0.048864 to −0.003505. The break-even value is stored under gaps.H.lower_bound_zero_eta in ranking_bounds.json. To reproduce the linked clinical-pool example, run `python replication/pool_response/verify_pool_response.py`. It prints the exact and numerical responses for additive and complementary care. The full runner saves them in `pool_results.json`.

To reproduce the equal-outlay comparison in the paper, run the following command from the archive root after installing the listed dependencies:

    python replication/model_checks/policy_incidence.py

This writes `policy_incidence.json`, `incumbent_valuation_table.tex` (panel A) and `policy_incidence_table.tex` (panel B) next to the script. The JSON field `lost_follow_up` reports displaced minutes by incumbent group, private values in model money per minute, and the components of net welfare per marginal dollar of the group-H subsidy. One effective unit is displayed as ten minutes for illustration. It compares two group subsidies, a purchase of clinical capacity, and a subsidy coupled with enough capacity to preserve support. The JSON also gives the distribution of losses under pooling and reservation, the break-even cost of capacity and the break-even welfare weight. All values are illustrative. The checks independently re-solve each policy for the same small positive budgets.


The clean-run record and verification scripts are in `replication/clean_reproduction/`. Its dated validation record documents the audited baseline and Medicare outputs and the source download checks. The additional trial analyses use the external studies' randomized assignments. The Norwegian analysis uses published coefficients. HSP series are transcribed.

## Match paper notation to output fields

In `verification_results.json`, the row of `group_results` with `w_L = 0.2` is the worked two-group example. The eligible population is normalized to one, `w_H = 1`, and `K = 0.3`. Add `n_L` and `n_H` to recover total adoption (0.421). Weight them by `w_L` and `w_H` before adding to obtain load (0.259). The output `h` is service per load unit (1.160). Multiplying it by the corresponding group weight gives service per adopter (0.232 and 1.160). These are rounded illustrative model outputs.

| Output fields | Interpretation |
| --- | --- |
| `C_L` and `C_H` in each `group_results` row | Loss of gross benefit across existing users per additional entrant from the indicated group, holding capacity and the other group mass fixed. |
| `W_sL` and `W_sH` in each `group_results` row | Marginal welfare per unit increase in the specified group subsidy rate. A per-budget-dollar comparison also requires the marginal change in public outlay. |
| `device_policy_episode_check.levels.refit_hazards` | Age-specific refitting probabilities, written as σ in the paper. |
| `illustrative_units` in `replication/booking_release/checks.json` | `rostered` and `booked` are available time and time reserved for new users. `new_users` and `incumbents` are time delivered to the two cohorts. |

In this archive the final entry of `device_age_aggregation_checks` → `next_stock_by_age` includes survivors already in the open-ended class. In both four-bin examples, 0.1392 enter that class and 0.0684 remain there, for a total of 0.2076. The earlier v1.3.1 calculation recorded only the 0.1392 entering. This changes those two projected terminal values in `verification_results.json`. The current-period allocation and empirical results are the same.

After a run from the extracted archive, the following command compares the current numerical files to their expected hashes. The default comparison without the last flag remains available for the published base tag.

    python replication/clean_reproduction/verify_outputs.py --base . --cms replication/medicare_spillover_pilot --current-supplement

## Run only the offline baseline

The historical baseline can be inspected at tag v1.3.1. The following commands run this subset from the current v1.4.0 checkout. MANIFEST_SHA256.json records the pre-run release files.

Use Python **3.12** (tested patch version 3.12.14). Create an isolated environment:

```sh
python -m venv .venv
```

Activate on macOS/Linux with `source .venv/bin/activate`, or on Windows PowerShell with `.venv\Scripts\Activate.ps1`. Then:

```sh
python -m pip install -r requirements-tested.txt
python reproduce_all.py --analysis-only
```

Dependency installation requires internet access. The supplied-data analyses run offline. The runner first verifies source-data hashes, reconstructs the AQP panel from 32 XLS workbooks, and executes the model, NHANES, sensitivity, and AQP diagnostic scripts. Failures stop execution with a nonzero exit code. Inspect `reproduction_run/report.json` and the numbered logs. Generated results are overwritten when rerun; source inputs are not.

### What counts as success

- `reproduction_run/report.json`: `status` is `passed`.
- NHANES final primary sample: **197**; adjusted odds ratio **2.816264656159935**, absolute tolerance **1e-8**.
- Generalized model audit: **1,495 accepted** configurations out of 1,500, **zero sign failures**; seed **20261124**. Skipped cases are reported, not counted as successful tests.
- `replication/nhs_aqp_data/ccg_month_panel.csv`: **6,754 rows, 76 columns**, reconstructed from all 32 supplied workbooks.
- Individual scripts write their detailed results listed in `RESULTS_MAP.csv`.

The output report contains actual elapsed times and environment versions. Numerical agreement is the test target; timestamps, operating systems and fonts may change PDF bytes.

## Optional figure regeneration

`python reproduce_all.py` and `python reproduce_all.py --analysis-only` both run the baseline numerical analyses. To also regenerate programmatic figures, use:

```sh
python reproduce_all.py --figures
```

Figure regeneration requires licensed Arial, XeLaTeX, TikZ, standalone and fontspec. Arial must be discoverable by both Matplotlib and XeLaTeX; font files are not redistributed. The builder checks fonts before overwriting supplied plots. The mechanism diagram is rebuilt from tikz/model_mechanism_illustrated.tex. Its typeset PDF and a PNG preview are included.

A fresh-directory numerical run is recorded under `validation/`. Dependency installation has not been independently tested in a new virtual environment on every operating system. For the subsequent same-host validation of the 11 programmatic baseline figures, see the records under `replication/clean_reproduction/`.

The manuscript, its LaTeX text, and its cover are not distributed in this code repository. Paper compilation is outside this package's scope.

## Navigate the results

`RESULTS_MAP.csv` covers the 12 baseline figures and three additional figures in the finals manuscript (Medicare event study, school voucher trial and English wait distributions). It gives the source, output path and applicable command for each figure and computational result family. Static conceptual/evidence tables and proofs are authored in the manuscript with citations; they are not estimated outputs. The paper appendices contain proofs, empirical sensitivity, algorithms and replication instructions; consult the current paper for appendix numbering.

## Source data and limitations
NHANES P_DEMO, P_AUQ and P_AUX are public CDC 2017–March 2020 pre-pandemic data. Source URLs and SHA-256 hashes are in data_provenance.json. AUQ144=1 is less than ONE year since specialist testing; AUQ153=3 or4 means at least four hours/day. The five-year alternative uses AUQ144=1 or2. The primary OR is a selected-user cross-sectional association, not a service or congestion effect.

HSP CSVs are manual transcriptions of cited official statistics. The HSP plot reads the transcribed CSV directly; it is not an automated download from the official source. The package includes all 32 original NHS workbooks and their source-URL/hash manifest. replication/build_nhs_aqp_panel.py --offline reconstructs ccg_month_panel.csv before the diagnostic script runs. The reconstructed 6,754-row, 76-column CSV matched the earlier panel byte for byte. Provisional Monitor treatment dates remain disputed; reproducible outcomes do not validate treatment timing.

MANIFEST_SHA256.json records all distributed files except itself; data_provenance.json identifies immutable inputs. Outputs may be overwritten by reproduction. PDF bytes can differ because of timestamps/font/rendering versions; numerical validation uses tolerances. The baseline calculations run offline with the supplied public inputs once dependencies are installed. The full numerical run uses the additional public inputs listed above. External articles cited in the paper are not all archived here.


## Scientific scope and reuse

The core model concerns a selected locally substitutable post-fitting support pool, `K = K^A`, not total health-system capacity. Institutional roles and separate task pools are described in the manuscript. Broader applications require the stated complementarity, congestion, allocation and valuation assumptions; they do not inherit hearing-aid estimates. NHANES associations, HSP administrative counts, and AQP diagnostics do not identify the complete congestion mechanism.

Third-party data retain their source terms; source URLs and hashes do not confer a new license. No blanket license for third-party data, fonts, or artwork is granted by this release. Code is made available for inspection and replication; a separate open-source license has not been designated.

For errors, open a GitHub issue with the release tag, command, Python/package versions, and the relevant non-sensitive error log. Do not upload credentials or private records.

## Matched-baseline institutional check (v1.3.1)

`research_audit_20261124/reserved_capacity.py` compares pooled support with group-reserved capacity. Group reservation shares are set once from the reference equilibrium and held fixed during subsidy perturbations. All five institutional rules have the same baseline adoption and delivered support. The code verifies the analytical response matrix, the resource identity, the pooled limit and the fully reserved limit. It writes CSV/JSON results and the generated table. Within-group congestion persists at full reservation. These are illustrative local comparative statics, not an estimated institutional effect.

## Local supply-response boundary

`research_audit_20261124/supply_response.py` holds the reference equilibrium fixed and varies the local response of capacity to a group subsidy. Contraction, partial expansion, exact offset and stronger expansion are checked using analytic, centered-difference and feasible right derivatives. This is a conditional comparative-static check, not an estimated supply function or welfare ranking.

## Influence diagnostics

`research_audit_20261124/nhanes_influence.py` refits the primary model after each participant deletion and each contributing masked-PSU exclusion (240 fits). Outputs include every deletion and survey-weight concentration. Deletion ranges are not confidence intervals; weights are not recalibrated. This check does not address unmeasured confounding or selection into current use.

## Exploratory policy-spillover extension

The [Medicare spillover pilot](replication/medicare_spillover_pilot/README.md) contains a separate public-data state-level DiD analysis and a Census insurance-coverage check. The full v1.4.0 runner includes this module. The offline baseline command omits it. The primary utilization estimate is imprecise and indistinguishable from zero; this is not a validated hearing-aid congestion estimate. Source downloads, hashes, commands, all outcomes and diagnostics are provided.
