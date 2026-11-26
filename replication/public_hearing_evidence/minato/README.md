# Tokyo's Minato City · Aftercare among purchasers with no previous hearing-aid use

The ward bought down the price of a hearing aid for eligible residents. The official program links consultation with a hearing-aid physician and a certified hearing-aid technician. Separately incurred repair and maintenance charges after purchase are excluded under the currently posted rules. The question analyzed below covers a consultation **after** purchase about use or readjustment, with either a hearing-aid physician or a hearing-aid technician. Neither the financing of the consultation nor the number of minutes appears in the reports. [Official program and index of all three surveys](https://www.city.minato.tokyo.jp/zaitakushien/koureisya/hoctyouki/hotyoukijyosei.html).

The municipal surveys went to recipients of a subsidized purchase in the stated Japanese fiscal year who had neither died nor moved out by mailing. FY2022 purchasers were contacted in October–November 2023, FY2023 purchasers in August 2024 and FY2024 purchasers in September 2025. The observation window thus varies by purchase date. No record is provided for otherwise similar residents who bought devices without the program. [FY2022, Questions 1 and 4](https://www.city.minato.tokyo.jp/documents/122393/r4hp.pdf) · [FY2023, Questions 1 and 4](https://www.city.minato.tokyo.jp/documents/122393/hp.pdf) · [FY2024, Question 3, page 1](https://www.city.minato.tokyo.jp/documents/122393/r6hp.pdf).

## A count the published margins can establish

In FY2022, 208 of 382 respondents reported no hearing-aid use before the program. Separately, 316 respondents reported at least one post-purchase professional consultation about use or readjustment. Only 66 respondents could have been outside the second group, including those who skipped the question. At least 208 − 66 = **142** of the confirmed previous nonusers must therefore have consulted. Nobody needs to assume that beginners seek care as often as experienced users.

| Purchase fiscal year | Mailed | Replied | Reported no previous use | Reported consultation | Possible overlap among recorded answers |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2022 | 495 | 382 | 208 | 316 | 142–208 |
| 2023 | 426 | 330 | 211 | 269 | 150–211 |
| 2024 | 406 | 311 | Question omitted | 254 | Unavailable |

Across the first two purchase cohorts, **at least 292 of the 419 confirmed previous nonusers (69.69%) reported a professional consultation**. The statement applies to respondents who reported no prior use. If all 209 people who did not reply had never previously used an aid and had no consultation, the conservative lower limit among *all prior nonusers mailed* drops to **46.50%**. Independently of prior-use status, at least 292/921, or **31.70% of everyone mailed in the first two cohorts**, both had no prior use and consulted, based on reported answers. In FY2024 the ward asked about consultation only, so it supplies an independent rate for all respondents and no new subgroup bound.

These endpoints are exact logical ranges for margins, not sampling confidence intervals. They assume the reported answers themselves are accurate. The overlap is not individually observed. Prior nonuse describes experience, not lifetime purchase history. The respondents acquired a subsidized aid, but the numbers do not identify how many purchases were induced by the subsidy. A consultation may be by a different professional or facility. Results give no comparison of treatment for a clinic's pre-existing users in the presence and absence of new users.

## Reproduction

With Python 3, run `python reproduce.py` beside `source_counts.csv` to reconstruct `results.csv`. Each survey item sums to the response total, including blanks. The additional 2023 link in the source CSV is the municipality's searchable copy of its FY2023 report. For each cohort with both questions the code evaluates `max(0, no_prior_use + contact_yes - respondents)` and `min(no_prior_use, contact_yes)`. Both endpoints are attainable by matching answer categories. Summing the year-specific endpoints preserves the separate survey margins.
