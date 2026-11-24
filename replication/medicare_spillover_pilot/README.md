# Exploratory Medicare spillover analysis

This module estimates a policy reduced form using public CMS state-year aggregates, with a supplementary Census SAHIE insurance-coverage check. It is an exploratory extension, **not a validated hearing-aid crowd-out estimate** and not a new randomized experiment. The primary result is statistically indistinguishable from zero. Do not describe this as proof of no effect.

## Reproduce from source

From this directory, with Python 3.11 or later:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python download_inputs.py
python analyze.py
python coverage_check.py
```

Windows activation: `.venv\Scripts\activate`. The downloader requires internet access, obtains CMS and Census public files, and verifies every SHA-256 against `source_manifest.json`; changed releases fail rather than silently replacing inputs. Original downloads total about 190 MB, and the expanded historical workbook needs additional space. Once downloaded, both analyses run offline. XLSX loading may take a minute.

`analysis_panel.csv` is the 250-row state-year estimation panel. `results.json` contains all four outcomes and specified sensitivity checks. `event_study.csv` includes every event year and pointwise intervals. `leave_one_state_out.csv` reports all 25 exclusions. `coverage_panel.csv` and `coverage_results.json` report the supplementary coverage check. These are generated from public inputs, not copied coefficients from another study.

Read `ANALYSIS_PLAN.md` for sample exclusions, main outcome, checks and analysis timing. The plan is internal, not preregistered. Only the coverage check was added after inspecting the primary estimates. The implementation uses state/year fixed effects and state-cluster CR1 covariance with t(G−1) inference; it also verifies the main coefficient against the balanced-panel difference-in-differences identity. With nine treated states, inference is approximate.

CMS labels the older age stratum `>65` and the newer stratum `>=65`; CMS documentation defines this stratum as age 65 and older. Hospital-outpatient visits are used to avoid the physician-service BETOS/RBCS classification change at 2014. Repeated populations are not a fixed cohort; dual eligibility and Medicare Advantage selection may change. Coverage expansion is a state policy choice, not randomized assignment. Parallel trends, no differential co-interventions and adequate control comparability remain substantive identifying assumptions. Geographic aggregates do not identify common provider networks, support minutes, hearing-aid use or pure capacity-mediated effects. SAHIE is model-based, with upstream estimation uncertainty not propagated in these regressions.

Policy chronology sources:
- https://www.kff.org/affordable-care-act/state-indicator/state-activity-around-expanding-medicaid-under-the-affordable-care-act/
- https://www.everycrsreport.com/files/20141230_R43564_c2bea7a5ad4031f362bfb1e26f60313c753c7711.html
- https://www.minneapolisfed.org/institute/working-papers/-/media/files/institute/working-papers/wp19-09.pdf

These exclusions intentionally remove broad pre-existing and early-expansion coverage states as well as mid-year/late adopters. They do not imply remaining states had no pre-2014 adult benefits. No manuscript or author/cover files belong in this module.

## Manuscript figure

`event_study.pdf` is a vector figure with embedded Arial fonts, generated from `event_study.csv`. To regenerate, install matplotlib and Arial, then run `python make_event_pdf.py`; alternatively supply `--arial-dir /path/to/Arial/fonts`. The script fails rather than silently substituting a different font. Font files are not redistributed. The normalized 2013 reference is an open marker, and intervals are pointwise rather than simultaneous.
