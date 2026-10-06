"""Acquire the exact public external inputs recorded in the study's receipts.

No clinical tables are embedded in this script. Receipt SHA-256 digests are
verified before bytes are installed. Original study locks are never rewritten.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "stage4" / "data"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def acquire(check=False, source_archive=None):
    receipt = json.loads((ROOT / "stage4/amended_download_receipt.json").read_text())
    archive = zipfile.ZipFile(source_archive) if source_archive else None
    try:
        for row in receipt["files"]:
            target = (DATA / row["file"]).resolve()
            if not target.is_relative_to(DATA.resolve()):
                raise ValueError("Invalid receipt destination")
            if target.exists() and digest(target) == row["sha256"]:
                print("Verified:", row["file"], flush=True)
                continue
            if check:
                raise RuntimeError("Missing or changed external input: " + row["file"])
            target.parent.mkdir(parents=True, exist_ok=True)
            temp = target.with_name(target.name + ".download-part")
            try:
                if archive:
                    name = "Sepsis_Alert_Calibration/stage4/data/" + row["file"]
                    with archive.open(name) as src, temp.open("wb") as dst:
                        for chunk in iter(lambda: src.read(1024 * 1024), b""):
                            dst.write(chunk)
                else:
                    for attempt in range(3):
                        try:
                            request = urllib.request.Request(row["url"], headers={"User-Agent": "Sepsis-reproducibility/1.0"})
                            with urllib.request.urlopen(request, timeout=90) as src, temp.open("wb") as dst:
                                for chunk in iter(lambda: src.read(1024 * 1024), b""):
                                    dst.write(chunk)
                            break
                        except urllib.error.HTTPError as exc:
                            if exc.code in (401, 403) or attempt == 2:
                                raise
                            time.sleep(attempt + 1)
                        except (urllib.error.URLError, TimeoutError, OSError):
                            if attempt == 2:
                                raise
                            time.sleep(attempt + 1)
                if temp.stat().st_size != row["bytes"] or digest(temp) != row["sha256"]:
                    raise RuntimeError("Receipt mismatch: " + row["file"])
                os.replace(temp, target)
                print("Restored and verified:", row["file"], flush=True)
            finally:
                temp.unlink(missing_ok=True)
    finally:
        if archive:
            archive.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify existing inputs without downloading")
    parser.add_argument("--source-archive", type=Path, help="Offline restoration from the original Stage 4 ZIP")
    args = parser.parse_args()
    try:
        acquire(args.check, args.source_archive)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
