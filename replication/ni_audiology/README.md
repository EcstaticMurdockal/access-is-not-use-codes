# Review queues among Northern Ireland hearing-aid recipients

Five Health and Social Care (HSC) Trust audiology departments reported the number of people waiting for a review after issue of an HSC hearing aid. The Minister of Health supplied the counts in Northern Ireland Assembly written answer AQW 44550/22–27, dated 27 May 2026. The source identifies May 2026 and does not specify a single census day.

## Reproduce

Run `python3 reproduce.py` here with Python 3.9 or newer. All dependencies belong to the Python standard library. The script reads the official answer’s WordprocessingML table, checks each Trust and each count against the official plain-text record, and writes the five counts and their sum to `results/`. It can run offline.

| Snapshot | Official source | SHA-256 |
|---|---|---|
| raw/aqw44550_answer.xml | [Written answer, Open XML](https://data.niassembly.gov.uk/questions.asmx/GetWrittenAnswerOpenXml?documentId=481151) | 4aca4bda6c0ec8bf759b9521316e585036377edf7a1f4cca746be4acc3028aac |
| raw/aqw44550_record.xml | [Question details with plain-text answer](https://data.niassembly.gov.uk/questions.asmx/GetQuestionDetails?documentId=481151) | b9ba271affbfbe612ebf03b71ac06d8c54be4567489a8a88252e96ef8975b2ec |

For visual verification see the [printable parliamentary answer](https://aims.niassembly.gov.uk/questions/printquestionsummary.aspx?docid=481151). The two official files contain different representations of the same return. Source attribution: Northern Ireland Assembly, Department of Health, and HSC Trust audiology departments. Source files retrieved 25 November 2026.

## Interpretation

The sum is 7,849 reported review waiters across five Trusts. The source separately mentions booked appointments in Belfast (250) and Northern (61). We use the tabulated counts as given and do not add or subtract those booking notes. The minister attributes some variation in waiting numbers to long-term audiology vacancies. The answer distinguishes repairs from routine review and instructs patients with broken devices to contact their audiology department.

The release does not report the size of the population of hearing-aid recipients, new fittings or referrals over the same interval, waiting duration, scheduled versus delivered clinician time, or device use. The counts therefore support a description of a queued incumbent cohort. They cannot calibrate per-user demand, compare Trust performance, or estimate an effect of new fittings on existing users. No person-level linkage or cross-Trust deduplication is released.
