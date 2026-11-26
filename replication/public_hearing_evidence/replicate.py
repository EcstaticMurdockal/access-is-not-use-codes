"""Recompute the tables from the included public source inputs."""
import argparse
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--extended", action="store_true", help="include the Korean survey and NHS checks")
args = parser.parse_args()
paths = ["minato/reproduce.py", "france/reproduce.py", "peer/decompose_visits.py",
         "incumbent_support/recompute.py"]
if args.extended:
    paths.extend(["korea/compare_usage.py", "staffs/analyse.py"])
for relative in paths:
    script = root / relative
    subprocess.run([sys.executable, str(script)], cwd=script.parent, check=True)
    print("Recomputed", relative, flush=True)
