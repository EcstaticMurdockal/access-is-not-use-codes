# CMS cross-population spillover pilot: analysis plan
Written before estimating treatment effects, 24 November 2026. This is an internal analysis plan, not a registered pre-analysis plan.

Question: did January 2014 adult Medicaid expansion change hospital-outpatient visits among Medicare beneficiaries aged 65 and older? This is a policy reduced form in repeated aggregate populations, not a fixed-incumbent cohort or an isolated congestion parameter.

Data: official CMS Geographic Variation historical 2007–2013 XLSX and 2014–2024 CSV. Analysis 2009–2018, avoiding pandemic years and later-adopter contamination. State aggregation and inference at the policy state level. No county pseudo-replication.

Main conservative cohort: AR KY MD NV NM ND OR RI WV. These adopted January 2014. Exclude early or broad pre-existing adult coverage states AZ CA CO CT DE DC HI IL IA MA MN NJ NY OH VT WA; late/mid-year adopters AK IN LA ME MI MT NH PA VA; WI because its separate 2014 eligibility change makes it unsuitable as an untreated state. Controls: AL FL GA ID KS MS MO NE NC OK SC SD TN TX UT WY, none expanded through 2018. Some states had limited earlier adult benefits: this is an incremental expansion comparison, not no-coverage versus coverage.

Primary outcome: log hospital outpatient visits per 1,000 Medicare beneficiaries aged 65+. Physician E&M events are not primary because CMS changes BETOS to RBCS classification at 2014. Secondary outcomes, all reported: inpatient stays, emergency visits, home-health visits per 1,000. These do not measure hearing-aid use or waiting time.

Main specification: state and year fixed effects, treated×post2014, equal state weights. CR1 state-cluster covariance with t(G−1) intervals. Event-study coefficients for every year with 2013 reference, joint pre-period Wald F approximation; failure to reject is not proof of parallel trends. Diagnostics: 2009–2013 placebo with 2012 pseudo-intervention; 2011–2018 window; baseline-2013 Medicare-population weights; leave-one-state-out coefficient range. Secondary outcomes descriptive exploratory without selective reporting.

Composition diagnostics: Medicare beneficiary numbers, mean age, female share, dual-eligible share, and MA participation where harmonizable; do not add post-treatment values as main controls. Check sources and units before pooling. A differential pretrend, denominator break, or unstable result prevents presenting pilot as established causality. Even a stable reduced form does not prove the fixed-K mechanism; alternative network, reimbursement, composition and state policy channels remain.

Supplementary check added after seeing the Medicare estimates: estimate the policy's insurance-coverage change among ages 18–64 using Census SAHIE, for all incomes and ≤138% poverty. The ACS API redirected to a missing-key page, so the public SAHIE download is used instead. This is a model-based coverage measure and a policy relevance check, not an instrumented estimate of service congestion. All selected income groups will be reported.
