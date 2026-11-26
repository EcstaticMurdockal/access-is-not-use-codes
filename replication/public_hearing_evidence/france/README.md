# France's 100 % Santé reform and hearing-aid purchase histories

The French Court of Accounts used national SNDS claims to count individuals who purchased hearing aids. Page 27 gives the percentage with a hearing-aid claim during the previous eight years. Footnote 42 identifies the coverage group. Table 6 on page 28 gives the number of purchasing patients in each group. [Cour des comptes, *La réforme du 100 % santé*, July 2022, pp. 27–28](https://www.ccomptes.fr/system/files/2022-07/20220728-100-pourcent-sante.pdf).

| Purchasing patients outside the low-income CSS scheme | 2018 | 2021 | Change |
|---|---:|---:|---:|
| All purchasers, thousands | 431 | 725 | +294 |
| With a claim in the previous eight years, % | 72 | 48 | −24 pp |
| Without a claim in the previous eight years, thousands, reconstructed | 120.68 | 377.00 | +256.32 |
| With a claim in the previous eight years, thousands, reconstructed | 310.32 | 348.00 | +37.68 |

Multiplying 431,000 by 28% gives approximately 121,000 purchasers with no purchase recorded in the previous eight years in 2018. The same calculation gives 377,000 in 2021. This increase accounts for about 87% of the net growth in purchasing patients outside CSS. It demonstrates how much of the observed expansion came from this particular claims-history group. It does not identify the proportion of reform-induced purchases, service hours, or lifetime first purchases. The figures count people, not devices, clinic visits or ears.

**Rounding.** Both inputs were published rounded. If patient counts are rounded to the nearest thousand and percentages to the nearest whole percentage point, the net increase in the group with no recent recorded purchase lies between 250,140 and 262,500. Its share of total growth lies between 85.06% and 89.32%. These are arithmetic bounds on rounding only. An optional sensitivity in `results.json` asks what fraction of 2021 purchasers with no recent claim would have to be repeat purchasers before the increase in lifetime first purchasers could disappear, assuming this fraction was zero in 2018 and all lifetime first purchases are in the no-recent-claim group. The break-even point is about 68%. Neither prior purchase outside the claims window nor prior purchase outside the reimbursement system was observed.

**Limits.** The no-recent-claim percentage is among purchasing patients. There is no at-risk population denominator or control group with credible parallel trends. The reform was phased in and coincided with COVID-19. Within the same national report, the proportion of audioprosthetists declaring any follow-up increased from 5.6% in 2020 to 48.8% in 2021. Follow-up declarations did not carry a separate tariff. The Court cautioned that reporting changes could account for the increase. Table 7 therefore cannot supply incumbent patients' actual appointment time. Under the source's coverage labels, the CSS subgroup also changed. Its growth is reported separately and should not be used as an untreated group.

**Reproduction.** `receipt_history.csv` transcribes the four counts and percentages. Run `python3 reproduce.py` from this directory. The program uses the Python standard library, checks both group-level decompositions, and writes `results.json`. To audit the count denominator, read the main text on page 27 together with footnote 42 and the subgroup rows in Table 6. The public inputs support the arithmetic above, not a reconstruction of individual SNDS histories.
