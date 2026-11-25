"""Verify two-site audiology queue transcription against the provider PDF.

Run python verify_lewisham_queues.py or append --ocr for a second extraction
using pdftoppm and Tesseract. The default run requires Python 3 and pdftotext.
"""
import argparse
import csv
import hashlib
import re
import subprocess
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "lewisham_june2007.pdf"
DIGEST = "5fa7938a2c6b3bcf314a92665e531998b24218e441c24c086bb3ca20df1f0f39"
PATTERN = re.compile(
    r"(First Fittings|Reviews)(?: \(existing analogue users\))? (QMH|Lewisham) "
    r"[-–—] (\d+) weeks (?:with|and) (\d+) patients on the list compared to "
    r"(?:a )?(sixteen|21) month wait and (around )?(\d+) patients a year ago\."
)
COLUMNS = ("site", "episode", "earlier_time", "earlier_count",
           "earlier_count_approximate", "earlier_wait_months", "later_time",
           "later_count", "later_wait_weeks")


def extract(text):
    site_names = {"QMH": "Queen Mary's Hospital Sidcup", "Lewisham": "University Hospital Lewisham"}
    episodes = {"First Fittings": "First fitting", "Reviews": "Review of existing analogue user"}
    records = []
    for episode, site, weeks, current, months, around, earlier in PATTERN.findall(" ".join(text.split())):
        records.append(dict(zip(COLUMNS, (site_names[site], episodes[episode],
            "A year before report", earlier, "yes" if around else "no",
            "16" if months == "sixteen" else months, "Current at report", current, weeks))))
    if len(records) != 4:
        raise ValueError(f"Expected four site-episode comparisons, found {len(records)}")
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ocr", action="store_true", help="also verify a raster reading of page 3")
    args = parser.parse_args()
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != DIGEST:
        raise ValueError("Source checksum differs from the archived source version")
    with (BASE / "lewisham_queue_transcription.csv").open(newline="") as table:
        expected = list(csv.DictReader(table))
    text = subprocess.check_output(["pdftotext", "-layout", "-f", "3", "-l", "3", SOURCE, "-"], text=True)
    if extract(text) != expected:
        raise ValueError("PDF text and hand transcription differ")
    if args.ocr:
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "page3"
            subprocess.run(["pdftoppm", "-r", "245", "-gray", "-png", "-singlefile",
                            "-f", "3", "-l", "3", SOURCE, image], check=True)
            ocr = subprocess.check_output(["tesseract", image.with_suffix(".png"), "stdout"],
                                          text=True, stderr=subprocess.DEVNULL)
            if extract(ocr) != expected:
                raise ValueError("Raster reading and hand transcription differ")
    print("Verified four site-by-episode comparisons on physical PDF page 3.")
    for episode in dict.fromkeys(row["episode"] for row in expected):
        rows = [r for r in expected if r["episode"] == episode]
        earlier = sum(int(r["earlier_count"]) for r in rows)
        later = sum(int(r["later_count"]) for r in rows)
        print(f"{episode}: approximately {earlier:,} earlier, {later:,} current.")


if __name__ == "__main__":
    main()
