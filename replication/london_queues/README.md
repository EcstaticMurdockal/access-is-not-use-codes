# First-fitting and review queues in south-east London

Gary Mepham, Senior Chief Audiologist, The Lewisham Hospital NHS Trust, *Audiology Service at University Hospital Lewisham*, June 2007, Appendix A to the Healthier Communities Select Committee papers (11 July 2007). [Source PDF](https://lewisham.moderngov.co.uk/Data/Healthier%20Communities%20Select%20Committee/20070711/Agenda/dfb5b29c7bc640a4aa57daf83e2768064AppendixAAudiologyserviceatUHLJune2007.PDF)

Physical PDF page 2 dates the start of the digital service to April 2004 at Lewisham and July 2004 at Queen Mary’s Hospital in Sidcup. These dates precede both observations. The provider describes extra demand from existing analogue users seeking digital replacements. Physical PDF pages 2–3 describe a locum working two days per week at Queen Mary's, a change in staff duties, and reallocation of clinic slots. Physical PDF page 3 reports four paired observations. Each uses the same wording, “a year ago,” for the comparison period. The source file title specifies June 2007, but neither snapshot has a precise census date. The report does not confirm synchronised data collection on the same day at the two sites. In the CSV, “no” in the approximation field means that the source did not qualify the published count as approximate.

Measures are patients on each waiting list and waits as reported, with no definition that they are medians, means or maximums. Keep the original units. Existing-user reviews in this comparison concern analogue-to-digital reassessment, not routine repair or a delivered maintenance contact. The June 2007 report does not publish entries, completions, withdrawals, idle slots or individual use outcomes. Aggregate only within episode, retaining “approximately” for earlier totals. Conditions changed at both sites. The two sets of observations describe queue contraction after rollout and during service reorganisation, with no separate effect attributable to extra staff, upgrades, or first-time entrants. The December 2007 and March 2008 figures in the conclusion are targets, not observations.

The four CSV records were manually transcribed from the report, then compared with its text layer and with an independent OCR of the rasterised third page. From this directory:

```sh
python verify_lewisham_queues.py --ocr
```

Without `--ocr`, only Python 3 and Poppler's `pdftotext` are required. The OCR option also requires `pdftoppm` and Tesseract (English language). The script checks the original PDF's SHA-256 fingerprint, tests all site, episode, count, period and wait fields, and prints the site totals. If the original PDF is not included with a distribution, download the linked document as `lewisham_june2007.pdf` before running the script.
