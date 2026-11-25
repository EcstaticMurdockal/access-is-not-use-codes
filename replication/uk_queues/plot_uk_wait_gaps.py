"""Plot the two reported wait figures for each named, matched provider label.

Run after the UK HC 392 transcription. Pass the generated CSV and desired PDF.
Requires matplotlib. Arial is used when installed, with Liberation Sans as the
metrically compatible fallback. All displayed marks and text remain vector.
"""
import argparse
import os
import csv
from decimal import Decimal
from pathlib import Path
from statistics import median

import matplotlib as mpl
mpl.use("Agg")
from matplotlib import font_manager
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter


def read_pairs(path):
    with path.open(newline="", encoding="utf-8") as stream:
        current = [row for row in csv.DictReader(stream)
                   if row["period"] == "Current" and row["named_exact_match"] == "1"]
    if len({r["reporting_label"] for r in current}) != len(current):
        raise ValueError("Duplicate named reporting label in the source period")
    gaps = []
    for row in current:
        if not row["first_fit_weeks"] or not row["reassessment_weeks"]:
            continue
        gap = Decimal(row["reassessment_weeks"]) - Decimal(row["first_fit_weeks"])
        if gap != Decimal(row["gap_weeks"]):
            raise ValueError(f"Source difference disagrees for {row['reporting_label']}")
        gaps.append(gap)
    gaps.sort()
    checks = (len(current), len(gaps), sum(x < 0 for x in gaps),
              gaps.count(0), sum(x > 0 for x in gaps), median(gaps), gaps[0], gaps[-1])
    if checks != (90, 83, 13, 21, 49, 3, -29, 188):
        raise ValueError(f"HC 392 sample checks failed: {checks}")
    return gaps


def paper_font():
    if font_dir := os.environ.get("PAPER_ARIAL_DIR"):
        for font in Path(font_dir).iterdir():
            if font.suffix.lower() == ".ttf":
                font_manager.fontManager.addfont(str(font))
    for name in ("Arial", "Liberation Sans", "DejaVu Sans"):
        try:
            font_manager.findfont(name, fallback_to_default=False)
        except ValueError:
            continue
        return name


def draw(gaps, destination):
    mpl.rcParams.update({"font.family": paper_font(), "font.size": 8,
                         "pdf.fonttype": 42, "ps.fonttype": 42,
                         "axes.linewidth": 0.55, "axes.unicode_minus": True})
    fig, ax = plt.subplots(figsize=(6.48, 2.52))
    fig.subplots_adjust(left=.105, right=.98, bottom=.245, top=.82)
    gaps = [float(value) for value in gaps]
    negative = sum(g < 0 for g in gaps)
    equal = gaps.count(0)
    groups = [
        (0, negative, "Shorter", "#A45438", "#F2B293"),
        (negative, negative + equal, "Equal", "#576582", "#BDCBE6"),
        (negative + equal, len(gaps), "Longer", "#357554", "#8DC8A8"),
    ]
    for start, stop, name, edge, fill in groups:
        ranks = range(start + 1, stop + 1)
        ax.scatter(ranks, gaps[start:stop], s=12, marker="o", linewidths=.52,
                   facecolors=fill, edgecolors=edge, zorder=3)
        # Keep counts with their rank intervals, independent of the plotting scale.
        ax.plot([start + .65, stop + .35], [1.04, 1.04], clip_on=False,
                transform=ax.get_xaxis_transform(), color=fill, lw=2.5,
                solid_capstyle="butt")
        ax.text((start + 1 + stop) / 2, 1.088, f"{name} ({stop-start})",
                transform=ax.get_xaxis_transform(), ha="center", va="bottom",
                fontsize=8.4, fontweight="bold")

    ax.axhline(0, color="#403D32", lw=.7, zorder=1)
    for y in (50, 100, 150, 200):
        ax.axhline(y, lw=.44, color="#E5EAEC", zorder=0)
    # Label the literal observed midrank; the marker is not displaced.
    middle = (len(gaps) + 1) // 2
    ax.annotate("Median +3", (middle, median(gaps)), (middle - 2, 42),
                fontsize=8, ha="center", va="center",
                arrowprops={"arrowstyle": "-", "color": "#525249",
                            "linewidth": .6, "shrinkA": 2.5, "shrinkB": 3})
    ax.annotate("−29", (1, gaps[0]), (6.2, -28),
                fontsize=7.7, ha="left", va="center",
                arrowprops={"arrowstyle": "-", "color": "#A45438",
                            "linewidth": .5, "shrinkA": 2, "shrinkB": 3})
    ax.annotate("+188", (len(gaps), gaps[-1]), xytext=(-6, -1),
                textcoords="offset points", fontsize=7.7, va="center", ha="right")
    ax.set(xlim=(0, len(gaps)+1), ylim=(-39, 203),
           xticks=[1, 20, 40, 60, 83], yticks=[0, 50, 100, 150, 200])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.0f}"))
    ax.set_xlabel("Reporting sites, ordered by the difference in reported waits", labelpad=4.4)
    ax.set_ylabel("Reassessment minus first-fitting\nreported wait (weeks)", labelpad=5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#697477")
    ax.tick_params(length=2.3, width=.55, color="#697477", labelcolor="black",
                   labelsize=7.6, pad=2.5)
    fig.savefig(destination, facecolor="white", metadata={"CreationDate": None})
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="provider_waits.csv from reproduce.py")
    parser.add_argument("pdf", type=Path, help="destination PDF")
    args = parser.parse_args()
    draw(read_pairs(args.csv), args.pdf)


if __name__ == "__main__":
    main()
