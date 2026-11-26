# North Staffordshire audiology eligibility and the measurement of uptake

North Staffordshire restricted NHS funding for some adults with age-related hearing loss on 1 October 2015. Adults with mild hearing loss were generally affected. Those with moderate loss remained eligible if it affected daily functioning. Exemptions applied. For existing NHS aid users the policy did not apply until the end of their three-year pathway, at which point eligibility was reassessed. Neither the rule nor its timing is interchangeable with an unconditional price change.

## What the local service counted

The commissioner's first complete six-month comparison used October–March in consecutive years. The local table explicitly labels **people assessed** and **people fitted**. It does not report a patient linkage between rows, separate first-time from replacement fittings, or identify old users' delivered aftercare. 'Fitted per 100 assessed' is a ratio of period counts. It is a conditional patient probability only if a source establishes that the same assessment cohort generates the fittings.

| Local administrative count | Before (October 2014–March 2015) | After (October 2015–March 2016) | Difference |
|---|---:|---:|---:|
| People assessed | 1,873 | 1,974 | +101 |
| People fitted | 1,226 | 1,223 | −3 |
| People fitted per 100 assessed | 65.46 | 61.96 | −3.50 |

126 people were recorded as ineligible in the later half-year. The comparable count for the previous year was not supplied. The 2016 report also presents a distinct provider subsample. Neither the ineligible count nor that subsample measures counterfactual first-time fittings lost. Some patients could have bought privately, been ineligible under either regime, or received a replacement. The six-month comparison alone cannot establish how many people would have received devices without the rule.

[Commissioner activity table, section 8, and provider subsample, sections 12–16](https://staffordshire.moderngov.co.uk/documents/s88242/Hearing%20Aid%20Policy%20Review%20North%20Staffordshire%20CCG%20final.pdf) · [Eligibility criteria and three-year transition](https://staffordshire.moderngov.co.uk/documents/s139869/HOSC%20briefing_hearing%20aids_Sept%202020.pdf)

## Independent check of the proposed national data proxy

We extracted every monthly completed-pathway workbook from October 2013 through September 2016 for North Staffordshire and the five other local commissioners named by the subsequent policy-alignment report. The comparison group was specified by geography. Each commissioner's counts enter the pooled denominator at their actual volumes. The dataset has 36 months and 216 commissioner-months with a complete number of recorded pathways in each. We compare October–March with the same months a year earlier, then repeat the comparison one year before the new rule and across complete 12-month periods.

| Period | North Staffordshire completed pathways | Five neighbours combined | Relative change in volume* |
|---|---:|---:|---:|
| Six-month placebo, before the policy | 333 → 375 | 3,859 → 3,779 | +15.00% |
| Six-month policy window | 375 → 451 | 3,779 → 3,453 | +31.62% |
| Twelve-month placebo, before the policy | 763 → 781 | 7,660 → 7,467 | +5.00% |
| First full year of the policy | 781 → 1,039 | 7,467 → 7,817 | +27.08% |

*100 × [(target post / target pre) / (neighbours post / neighbours pre) − 1]. The placebo's first six months end in March 2015, the month the policy was approved. The twelve-month baseline and placebo include the period before the October implementation when providers had notice. These are descriptive checks. No randomization-based interval or causal coefficient is claimed.

National DAA pathway completions in these periods increased substantially while the local count of patients fitted was almost flat. The counts have different provider/pathway coverage and definitions. The archived national rules cover new referrals and returning users seeking reassessment; clocks may stop at fitting, reprogramming, referral to a consultant or a decision against treatment. A 31.62% relative change in this measure cannot identify induced first-time users. Waiting times for this mixed population cannot stand for the aftercare delivered to pre-policy hearing-aid recipients. The placebo also indicates that the two series were already evolving differently. Neither series, separately or together, supplies the study's proposed causal estimate.

[National workbook archive](https://www.england.nhs.uk/statistics/statistical-work-areas/direct-access-audiology/daa-data/) · [NHS audiology clock rules, paragraphs 1, 10–11](https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2013/04/Audiology-clock-rules-20110413-final.doc) · [2022 policy-alignment report, §§4.4–4.6, comparison geography](https://staffordshire.moderngov.co.uk/documents/s167817/08%20-%20Clinical%20Policy%20Alignment.pdf)

## Conditions for a new patient-level analysis

A viable design could restrict incumbent outcomes to users whose direct funding and aftercare entitlement did not change. Dates of prior fitting, pathway expiry and exemption status are needed to identify them. Compare completed checks/reprogramming, including people with zero contacts, across receiving practices with different pre-specified policy exposure. Obtain separate practice-level counts of first-ever fittings and replacements; validate the actual change in entrant load before estimating displacement. Check pre-trends, capacity, reporting changes and shared practices across commissioner boundaries. The September 2022 removal decision is another prospective opportunity, but the local public report's 343 patients were assessed and deemed ineligible in February 2021–January 2022; they were not counted as post-reform first-time recipients. Provider implementation dates and clinical records would be needed. This audit does not imply records are currently accessible.

[2022 policy decision](https://staffsstoke.icb.nhs.uk/our-work/transformation/difficult-decisions/clinical-policy-alignment-update-september-2022/)

## Reproduction

Use Python 3.10 or later, with `lxml` and `xlrd` installed. Run `python get_data.py` then `python analyse.py`. When all monthly XLS workbooks and the manifest are present, `python analyse.py` works offline. Inputs include `committee_counts.csv` (transcribed from the 2016 activity table) and the 36 workbooks listed with SHA-256 hashes in `workbooks.csv`. The source archive and clock-rules document are in `raw/`. Outputs are `six_ccg_months.csv`, `local_results.csv`, `geographic_checks.csv` (also includes each comparison CCG individually and the share of known-start pathways taking more than six weeks), and `pooled_checks.csv`. The extractor verifies workbook dates, recorded row counts, waiting-time bins and monthly source identifiers.
