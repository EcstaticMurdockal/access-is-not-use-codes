"""Rebuild the baseline analyses and the final manuscript's supplementary numerical results."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
MODULES = ROOT / "replication"

def run(script, *args):
    script = Path(script)
    subprocess.run([sys.executable, str(script), *map(str, args)], cwd=script.parent, check=True)

def main():
    run(ROOT / "reproduce_all.py", "--analysis-only")
    run(MODULES / "model_checks" / "check_revision.py")
    run(MODULES / "model_checks" / "policy_incidence.py")
    run(MODULES / "model_checks" / "ranking_bounds.py")
    cms = MODULES / "medicare_spillover_pilot"
    run(cms / "download_inputs.py")
    run(cms / "analyze.py")
    run(cms / "coverage_check.py")
    run(MODULES / "clean_reproduction" / "verify_outputs.py", "--base", ROOT, "--cms", cms,
        "--current-supplement")
    for script in ("hearing_action_plan/reanalyze.py", "hearing_supported_fitting/extract.py",
                   "hearing_supported_fitting/reanalyze.py", "price_vouchers/analyze.py",
                   "incumbent_time/compare_hours.py", "uk_queues/reproduce.py",
                   "london_queues/verify_lewisham_queues.py", "ni_audiology/reproduce.py",
                   "korea_registration/standardize.py", "booking_release/check_appointment_release.py"):
        run(MODULES / script)
    run(MODULES / "measurement_checks/nhanes_multidevice.py", ROOT)
    run(MODULES / "measurement_checks/cms_checks.py", cms / "analysis_panel.csv")
    import json
    solver = MODULES / "pool_response/verify_pool_response.py"
    solution = subprocess.check_output([sys.executable, solver], cwd=solver.parent, text=True)
    (solver.parent / "pool_results.json").write_text(json.dumps(json.loads(solution), indent=2)+"\n")
    print("Completed the baseline pipeline and all final supplementary numerical analyses.")

if __name__ == "__main__":
    main()
