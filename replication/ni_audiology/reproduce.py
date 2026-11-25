"""Rebuild the May 2026 NI hearing-aid review queue table (standard library only)."""

import csv
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

BASE = Path(__file__).resolve().parent
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
TRUSTS = {"Belfast", "Northern", "South Eastern", "Southern", "Western"}


def main():
    document = ET.parse(BASE / "raw" / "aqw44550_answer.xml")
    record = ET.parse(BASE / "raw" / "aqw44550_record.xml").find("Question")
    if record is None or record.findtext("Reference") != "AQW 44550/22-27":
        raise ValueError("Unexpected Assembly question reference")
    root = document.find(".//w:tbl", NS)
    if root is None:
        raise ValueError("Missing Assembly answer table")
    table = []
    for row in root.findall("w:tr", NS):
        cells = [
            "".join(t.text or "" for t in cell.findall(".//w:t", NS)).strip()
            for cell in row.findall("w:tc", NS)
        ]
        if any(cells):
            table.append(cells)
    if table[0] != ["HSC Trust", "Number of patients waiting for hearing aid review appointment"]:
        raise ValueError("Unexpected source column definitions")

    counts = [(trust, int(count.replace(",", ""))) for trust, count in table[1:]]
    if len(counts) != len(TRUSTS) or {trust for trust, _ in counts} != TRUSTS:
        raise ValueError("Duplicate or missing Trust")

    plain = record.findtext("AnswerPlainText", "")
    figure_table = plain.split("review appointmentBelfast", 1)
    if len(figure_table) != 2:
        raise ValueError("Missing expected plain-text table marker")
    flattened = "Belfast" + figure_table[1].split("Source:", 1)[0]
    for trust, count in counts:
        match = re.search(re.escape(trust) + r"([\d,]+)", flattened)
        if match is None or int(match[1].replace(",", "")) != count:
            raise ValueError(f"Assembly representations disagree for {trust}")
    if "HSC Trust audiology Departments (May 2026)" not in plain:
        raise ValueError("Unexpected data supplier or reporting month")
    out = BASE / "results"
    out.mkdir(exist_ok=True)
    with (out / "ni_hearing_aid_review_queue.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["report_month", "hsc_trust", "people_waiting_for_hearing_aid_review"])
        writer.writerows(("2026-05", trust, count) for trust, count in counts)
    summary = {
        "assembly_question": record.findtext("Reference"),
        "answer_date": record.findtext("AnsweredOnDate")[:10],
        "report_month": "2026-05",
        "trusts_reporting": len(counts),
        "sum_of_reported_trust_counts": sum(count for _, count in counts),
    }
    (out / "ni_hearing_aid_review_queue.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
