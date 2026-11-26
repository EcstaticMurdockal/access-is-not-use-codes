# Access Is Not Use — public evidence supplement

From this directory run:

    python replicate.py

The four analyses described in the paper use Python 3.9+ and only the standard library. No network connection or patient-level records are required. Each source file and each calculation has a short README in its folder. The code overwrites only the derived tables inside these folders.

| Folder | Input | Output |
| --- | --- | --- |
| minato | Minato City post-purchase questionnaires, questions 1 and 4 (published totals) | results.csv: overlap and nonresponse bounds |
| france | Cour des comptes table 6 and accompanying claims-history text | results.json: decomposition and rounding sensitivity |
| peer | Liu et al. table 3, U.S. randomized screening arms | visit_contrasts.csv: total, first and additional visits per 100 |
| incumbent_support | Malmberg et al. table 2, published means by arm | contrasts.csv: raw questionnaire score changes |

The extended checks record two alternative sources examined in this search. The Korean survey comparison is descriptive. The North Staffordshire check compares audited numbers of actual fittings with NHS counts of completed care pathways. Neither identifies displacement of existing patients. To rerun them as well, install xlrd 2.0.1 and run:

    python -m pip install xlrd==2.0.1
    python replicate.py --extended

The archived NHS inputs are included. The additional download script and its separate dependencies are only for obtaining fresh copies. All other inputs are small transcriptions of public tables, linked to their primary sources in the folder READMEs. Source strata and contrasts should be interpreted in their original populations. The numeric results derive from separate studies and cannot be multiplied to estimate a subsidy spillover.
