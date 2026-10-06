"""Verify the combined package and original frozen inputs without running models."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(with_data=False):
    errors = []
    checked = 0
    pending_downloads = []
    def check(name, expected):
        nonlocal checked
        p = ROOT / name
        if not p.is_file() or digest(p) != expected:
            errors.append(name)
        checked += 1
    manifest = json.loads((ROOT / "REPOSITORY_MANIFEST.json").read_text())
    for name, row in manifest["files"].items():
        check(name, row["sha256"])
    for name in ["stage3/followup_lock.json", "stage4/external_lock.json", "stage4/external_amended_lock.json"]:
        for relative, expected in json.loads((ROOT / name).read_text())["inputs"].items():
            if relative.startswith("stage4/data/") and not (ROOT / relative).exists() and not with_data:
                pending_downloads.append(relative)
            else:
                check(relative, expected)
    lock = json.loads((ROOT / "stage2/protocol_lock.json").read_text())
    for name, key in [("manifest.json", "manifest_sha256"), ("stage2/STAGE2_PROTOCOL.md", "protocol_sha256"), ("stage2/study_config.json", "config_sha256"), ("experiment.py", "pilot_code_sha256")]:
        check(name, lock[key])
    for relative, row in json.loads((ROOT / "stage4/package_manifest.json").read_text())["files"].items():
        if relative.startswith("stage4/data/") and not (ROOT / relative).exists() and not with_data:
            pending_downloads.append(relative)
        else:
            check(relative, row["sha256"])
    report = {"status": "PASS" if not errors else "FAIL", "hash_checks": checked,
              "errors": sorted(set(errors)), "public_inputs_pending_download": sorted(set(pending_downloads)),
              "scope": "File integrity and frozen-input checks, not clinical validation."}
    print(json.dumps(report, indent=2))
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-data", action="store_true", help="Require all public external inputs to be present")
    args = parser.parse_args()
    verify(args.with_data)
