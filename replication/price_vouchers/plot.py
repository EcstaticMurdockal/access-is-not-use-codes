"""Draw simultaneous confidence intervals for the three reported PRICE contrasts."""
import argparse
import json
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
from matplotlib import pyplot as plt, font_manager

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--arial-dir", type=Path)
args = parser.parse_args()
if args.arial_dir:
    for path in args.arial_dir.glob("*"):
        if path.suffix.lower() == ".ttf":
            font_manager.fontManager.addfont(str(path))
font_manager.findfont("Arial", fallback_to_default=False)
mpl.rcParams.update({"font.family": "Arial", "font.size": 9, "pdf.fonttype": 42})
results = json.loads((root / "results.json").read_text())
series = [
    ("Paid purchase", results["Paid purchase"]["simultaneous_three_contrasts"], "#367FB0"),
    ("Observed wear", results["Observed wear"]["simultaneous_three_contrasts"], "#448269"),
    ("Purchase effect minus wear effect", results["paired_difference_simultaneous_three"], "#93619D"),
]
fig, ax = plt.subplots(figsize=(7.05, 2.15))
fig.subplots_adjust(left=.31, right=.975, top=.91, bottom=.29)
ax.axvline(0, color="black", linewidth=.7)
for idx, (label, row, color) in enumerate(series):
    y = 2 - idx
    lo, effect, hi = (row[key] for key in ("low_pp", "rd_pp", "high_pp"))
    ax.errorbar(effect, y, xerr=[[effect-lo], [hi-effect]], fmt="o", color=color, capsize=3.6,
                linewidth=1.6, markersize=5.2)
ax.set_yticks([2,1,0], labels=[e[0] for e in series])
ax.set_ylim(-.52,2.52)
ax.set_xlim(-30,40)
ax.set_xticks(range(-30,41,10))
ax.set_xlabel("Upgrade offer minus free-only offer (percentage points)")
ax.spines[["top","right","left"]].set_visible(False)
ax.tick_params(axis="y", length=0, pad=9)
ax.grid(axis="x", color="#DBE7EF", linewidth=.55)
ax.set_axisbelow(True)
fig.savefig(root / "price_contrasts.pdf")
