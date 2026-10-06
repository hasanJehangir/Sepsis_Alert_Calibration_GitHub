"""Run original study drivers in copies and compare results with the archive.

Download raw Challenge data into data/ before --stage primary. Download external
inputs with download_external_data.py before --stage external. Archived outputs
and protocol locks are retained unchanged in the repository.
"""
from pathlib import Path
import argparse
import datetime
import json
import shutil
import subprocess
import sys
import tempfile
import pandas as pd

ROOT = Path(__file__).resolve().parent


def run(stage):
    output = ROOT / "reproductions" / stage
    output.mkdir(parents=True, exist_ok=True)
    comparisons = []
    with tempfile.TemporaryDirectory(prefix="sepsis-reproduce-") as temp:
        copy = Path(temp) / "project"
        shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "reproductions", "*.download-part"))
        if stage == "followup":
            command = [sys.executable, "stage3/run_followup.py"]
            relative = "stage3/results"
            tables = ["policy_metrics.csv", "cross_hospital_local10.csv", "paired_policy_differences.csv", "invariance_audit.csv"]
        elif stage == "external":
            command = [sys.executable, "stage4/run_reproduction.py"]
            relative = None
            tables = []
        else:
            # Prepared arrays were too large for the original result archive.
            # Rebuild from all 40,336 downloaded public files in this copy.
            command = [sys.executable, "stage2/run_stage2.py", "--stage", "all"]
            relative = "stage2/results"
            tables = ["cohort_counts.csv", "discrimination.csv", "main_metrics.csv", "paired_differences.csv", "budget_summary.csv", "thresholds.csv"]
        result = subprocess.run(command, cwd=copy, capture_output=True, text=True)
        (output / "run.log").write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError("Reproduction failed; see " + str(output / "run.log"))
        for name in tables:
            expected = pd.read_csv(ROOT / relative / name)
            actual = pd.read_csv(copy / relative / name)
            pd.testing.assert_frame_equal(expected, actual, check_exact=True)
            comparisons.append({"file": relative + "/" + name, "exact_dataframe_match": True})
        if stage == "external":
            record = json.loads((copy / "stage4/reproduction/verification.json").read_text())
            comparisons = record["comparisons"]
        record = {
            "stage": stage,
            "completed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "status": "REPRODUCED_EXACTLY",
            "comparisons": comparisons,
            "archived_outputs_overwritten": False,
            "clinical_validation_claimed": False,
        }
        (output / "verification.json").write_text(json.dumps(record, indent=2))
    print("Verified", stage, "without overwriting archived study results.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["primary", "followup", "external"], default="followup")
    args = parser.parse_args()
    run(args.stage)
