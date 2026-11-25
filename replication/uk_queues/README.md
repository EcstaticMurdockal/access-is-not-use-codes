# First-fitting and reassessment waits in the digital hearing-aid transition

The House of Commons Health Committee published Trust-level hearing-aid waiting-time figures submitted by Grant Shapps MP on 8 February 2007, following Freedom of Information requests. The source gives separate values for first fitting and reassessment in 2004–05, 2005–06 and a period marked “Current.” The submission does not date the last observation precisely. Some providers are specifically paediatric.

**Source**: House of Commons Health Committee, *Audiology Services*, HC 392, Session 2006–07, written evidence AUDIO 30, Tables 2a and 2b, Ev 108–111. [Original HTML and tables](https://publications.parliament.uk/pa/cm200607/cmselect/cmhealth/392/392we44.htm) · [Printed volume](https://publications.parliament.uk/pa/cm200607/cmselect/cmhealth/392/392.pdf) · [Committee discussion, paras 39–42](https://publications.parliament.uk/pa/cm200607/cmselect/cmhealth/392/39205.htm). The archived HTML was retrieved 25 November 2026; SHA-256 5f4a5e13050cfa4f4a8a37cf0c02a626d42f0b21f0ffb2a38c5eb3af06383ea8. Contains Parliamentary information licensed under the [Open Parliament Licence v3.0](https://www.parliament.uk/site-information/copyright-parliament/open-parliament-licence/).

## Reproduce

Run `python3 reproduce.py` from this directory using Python 3.9 or newer. Only Python standard-library modules are used. The script verifies the source hash, reads the original HTML offline and writes the following four files.

| Output | Content |
|---|---|
| results/provider_waits.csv | Union of source labels × three periods, source-table inclusion flags, reported waits in weeks, signed paired difference and sample flags |
| results/paired_summaries.csv | Count with either measure missing, paired count, means, median paired difference and counts by sign, for each period and sensitivity specification |
| results/current_pairs_table.tex | Manuscript appendix rows generated from the seven final-period sample definitions in paired_summaries.csv |
| results/matching_audit.json | Counts of source rows, unmatched or ambiguous labels, and explicit paediatric providers |

## Matching and arithmetic

Each row in each source table represents one reporting Trust or named site. Each table has 93 rows, excluding its average. Ninety-two labels appear identically in both. Excluding the two underspecified labels “Healthcare” and “University Hospitals” leaves 90 candidates. Each sample uses only numerical values for both pathways in the same period, giving 68, 73 and 83 pairs. A star is unavailable. The source has no ranges in these table cells. One explicit zero for Royal Liverpool Children's is retained.

Every reporting unit has equal weight. For each unit, the gap is its reported reassessment wait minus its reported first-fitting wait. Arithmetic mean and median use these paired differences. The 65 balanced providers supply both figures in all three periods. Sensitivity outputs also show exact matching including the two ambiguous labels, exclusion of explicitly paediatric labels, exclusion of Barnsley, and a supplementary Warwickshire name match. Table 3a identifies the 73-week “Warwickshire” first-fit entry as University Hospitals Coventry and Warwickshire. The main comparison leaves that abbreviated first-fit name unmatched. Five of the 90 candidate names explicitly identify children's services. Three of them have a complete final-period pair. Their exclusion leaves 80 units, with a mean gap of 28.30 weeks and a median of 7.5. The other names do not establish patient ages.

| Period | Pairs | Mean difference (weeks) | Median difference (weeks) | Longer / tied / shorter |
|---|---:|---:|---:|---:|
| 2004–05 | 68 | 10.64 | 0 | 33 / 22 / 13 |
| 2005–06 | 73 | 16.05 | 1 | 38 / 26 / 9 |
| Current at submission | 83 | 27.29 | 3 | 49 / 21 / 13 |

In the balanced 65, the respective mean differences were 11.64, 16.73 and 22.72 weeks and the medians were 2, 1 and 1. Across providers, markedly longer reported reassessment waits at a subset of sites raise the mean. Some providers report identical values on both pathways.

The numerical and missing-value fields of all 186 provider rows (558 observations) were compared against the printed PDF’s two tables. They agree. The averages printed in the source’s Table 1 differ from the “Average” rows in Tables 2a/2b. The source gives no reconciliation. The reported results use the tabulated provider rows directly and a documented common sample.

## Interpretation

This is a provider-level description of reported wait figures. The committee's discussion of digital modernisation describes an influx of existing users seeking upgrades. Reassessment in this setting can include upgrading an analogue device. The historical rollout also affected first fittings, and available data do not isolate the two demand shocks.

The FOI submission does not document standardised clock start/end, a common statistic across providers, complete response coverage, or weights from patient counts. The label “Current” does not give a harmonised census date. One concrete reason for caution is that Barnsley’s separate submission in the same volume (Ev 112) describes distinct waits to assessment and then fitting, whereas Table 2a gives a single value. The unweighted summaries cannot be read as the delay for a typical patient, the frequency of follow-up, clinician time, a service-use outcome, the effect of a subsidy, or a causal crowd-out estimate.

## Manuscript figure

From this directory run `python plot_uk_wait_gaps.py results/provider_waits.csv ../../figures/uk_wait_gaps.pdf` with Matplotlib installed. It checks all 83 plotted differences, the direction counts, the median and both extremes. The published figure uses Arial. Set `PAPER_ARIAL_DIR` to a directory with locally licensed Arial TTF files if the typeface is outside the system font search path. The script uses Liberation Sans or DejaVu Sans when Arial is unavailable.
