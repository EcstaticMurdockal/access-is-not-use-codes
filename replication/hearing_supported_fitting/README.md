# Supported versus self-fitting hearing aids in a randomized trial in China

Jiang F, Chen S, Dayimu A, et al. A randomized trial of supported versus self-fitting over-the-counter hearing aids in older adults. Nature Communications (2026). https://doi.org/10.1038/s41467-026-78833-x

## Reproduce

Python 3 with SciPy and openpyxl is sufficient. Run the following commands in this directory.

    python extract.py
    python reanalyze.py

The first command downloads the publisher's source workbook and checks SHA-256 before reading the Figure 3(a) and Figure 3(b) worksheets. An existing publisher file can be supplied with --workbook PATH. The small arm_summaries.csv is sufficient to regenerate results.csv offline. Randomization denominators and the one death in the self-fitting group by three months are transcribed from Figure 1 of the article. The source workbook contains figure-level summaries. Individual records require a research proposal and a signed data access agreement according to the paper. The code introduces no simulated participants.

Source workbook: https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-78833-x/MediaObjects/41467_2026_78833_MOESM4_ESM.xlsx

## Outcomes and interpretation

Arm assignment was randomized among 322 older adults in ten Chinese community health centres. Both active assignments include fitting and support. The composite endpoint is being alive and reporting wear in either the “4–8 h/day” or “>8 h/day” category of IOI-HA item 1. Known death is coded zero. We use source categories directly because assignment of exactly four hours cannot be recovered from the grouped questionnaire. The publication's primary outcome was APHAB benefit. This secondary reanalysis selects the three-month visit that matches the study's primary follow-up. It compares a 50:50 mixture of physician and remote-audiologist support with self-fitting. Equal weights apply to the two support arms even when their follow-up rates differ.

The observed-case difference uses available responses in each arm. The full-assignment sample completion range places all unknown supported responses low and all unknown control responses high for its lower endpoint, then reverses the assignments for its upper endpoint. The control death remains zero. A sample bound is a descriptive property of the trial's observed allocation. For sampling uncertainty, the code combines the lower and upper endpoint estimates with two 97.5% one-sided unadjusted normal limits (Bonferroni); the resulting outer region is approximate. Standard errors assume independent arm samples, and arm-level summaries preclude adjustment for city, centre, or baseline covariates. Where fewer participants attend, the resulting range can be wide.

Figure 3(a) measures device-logged powered-on hours during the follow-up interval. Powered-on time can differ from time worn, and the questionnaire refers to reported daily wear. The code reconstructs the arm-specific sampling variance from the paper's t-based confidence intervals and uses a Welch–Satterthwaite interval for the weighted difference. These hours are available for follow-up participants only. The two outcomes cover different units and reporting windows. The interval columns in results.csv are pointwise, with no multiplicity control across separate outcomes, visits, or pathways. They complement the authors' prespecified analysis and are secondary estimates from their trial. The trial records neither the exposure of untreated incumbent patients nor a provider capacity shock.
