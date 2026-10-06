# Sepsis false-alert calibration and warning timing

Reproducible code accompanying **Admission-level false-alert calibration and
warning timing in cross-hospital sepsis prediction: a reproducible retrospective
evaluation**, by Hasan Jehangir (manuscript, not an accepted publication).

The project examines admission-level false-alert exposure, threshold transport,
repeat-warning burden and first-warning timing. It includes the primary locked
Challenge analysis, exploratory alert-policy follow-up, and both the initial
and post-test amended eICU public-demo evaluations. No CAPMI material was used.

**Scope:** retrospective evaluation research. The external demo contains only
17 test cases and yields weak case detection. Cross-resource hospital/person
independence is unverified. This repository does not establish clinical efficacy,
prospective patient benefit or a deployable medical warning system.

## Contents

| Location | Purpose |
| --- | --- |
| experiment.py, download_data.py | Original pilot feature logic and public Challenge acquisition |
| manifest.json | Original deterministic roles for all 40,336 released records |
| stage2/ | Locked primary cohort construction, training, evaluation and audit |
| stage2/results/ | Six fitted models, predictions, calibration summaries and recorded results |
| stage3/ | Exploratory alert-policy rules and all 660 recorded comparisons |
| stage4/ | Original and amended external adapters, both runs, review aids and locks |
| publication/ | Updated article, supplement, references, tables and data-derived figures |
| download_external_data.py | Checksum-verified acquisition of exact public external inputs |
| reproduce.py | Reproduction in copies; archived outputs stay unchanged |
| verify_repository.py | Packaged-file checks and original frozen-input verification |
| ETHICS_AND_AUTHOR_STATEMENTS.md | Confirmed funding/education and ethics completion guidance |
| GITHUB_UPLOAD_GUIDE.md | Upload instructions for Windows/GitHub Desktop |
| Sepsis_Reproduction_Colab.ipynb | Combined reproduction notebook |

Some earlier reports and review forms are retained byte-for-byte because the
original package manifest verifies them. They describe the status at their
original creation. The current article is publication/Sepsis_Alert_Transport_Manuscript.pdf.
The current author-reported review and submission state are explained in
ETHICS_AND_AUTHOR_STATEMENTS.md and the publication README. Do not interpret
historical pending-review fields as a new assessment of the doctors' feedback.

## Environment

Python **3.12** was used for the recorded analysis and package verification.
Use a virtual environment and install the combined pinned dependencies:

```bash
python -m pip install -r requirements_complete.txt
python verify_repository.py
python -m pytest -q tests stage2/tests stage3/tests stage4/tests
```

Pinned dependencies are important for the saved scikit-learn models and exact
numerical comparisons. Review code before running it. The included joblib
models were recovered from the original study archives.

## Fast reproduction from retained predictions

No raw input download or new training is needed to reproduce the follow-up:

```bash
python reproduce.py --stage followup
```

The wrapper compares four result tables exactly and writes its log and
verification record to reproductions/followup/. It does not overwrite the
archived protocol locks or result completion records.

To reproduce manuscript assets and audit its numerical claims:

```bash
python publication/build_assets.py
python publication/audit_manuscript.py
```

Compiling the manuscript additionally requires pdfLaTeX and BibTeX; see the
publication README. The already compiled article and supplement are included.
The repository integrity check is for the supplied bytes; run it before
regenerating presentation files or creating new execution records.

## Reproduce both external evaluations

Restore the exact public inputs recorded in the original receipts:

```bash
python download_external_data.py
python download_external_data.py --check
python reproduce.py --stage external
```

Downloads resume by verifying existing files and are checked against the
recorded SHA-256 digests. The pinned YAIB commit is
0d1d39a131a65f453aeb019828394396d6bfd171. An original Stage 4 archive can also
restore the same inputs offline with --source-archive PATH_TO_STAGE4_ZIP.

The external wrapper calls the original isolated-copy verifier and compares
both runs' tables, all 24 prediction vectors and feature arrays. Models are
not refitted. Do not call run_external.py and run_external_v2.py consecutively
in the original result directory: that would change completion metadata
referenced by the amended lock. Use reproduce.py instead.

## Full primary analysis from public raw records

Acquire both the pilot records needed for duplicate screening and the reserved
records. Downloading many small files and rebuilding/training arrays is much
slower than reproducing from the retained outputs. Provide enough local disk
for raw files, temporary copies and disk-backed feature arrays.

```bash
python download_data.py
python download_data.py --full
python reproduce.py --stage primary
```

This runs the unchanged primary driver in a temporary copy and compares six
primary output tables with the original archive. Original timestamps and model
files are preserved in the repository. The assembly verification did not repeat
all primary fitting; it verified the original locks, existing tests and output
consistency. Read docs/VERIFICATION_REPORT.md for the checks actually performed.

## Data and provenance

Raw clinical tables are omitted from this GitHub package and downloaded from
PhysioNet and the pinned YAIB repository. Frozen predictions and derived study
outputs are included to support exact reproduction; they derive from the public
releases. Preserve data attribution and the relevant database licenses. See
LICENSES_AND_DATA.md and stage4/DATA_ATTRIBUTION.md.

Original protocol locks are local hashes, not public prospective
preregistration. The Stage 3 follow-up used already examined primary tests.
The external amendment used already examined external tests. Both external
runs remain available; no favorable run was selected as the final result.

REPOSITORY_MANIFEST.json records this combined package. The older
stage4/package_manifest.json still describes the original external archive and
is used after public input restoration. Older PACKAGE_MANIFEST.json and
ARCHIVE_INVENTORY.json, if present, describe the earlier archives, not this
combined repository.

## Author and submission statements

Hasan Jehangir is displayed as an independent researcher in Pakistan, with
educational background BS in Data Science, University of Engineering and
Technology, Peshawar. A current UET research appointment or university approval
is not asserted. **This research received no external funding.**

Corresponding email: **hasanjehangir6@gmail.com**. Public source repository: https://github.com/hasanJehangir/Sepsis_Alert_Calibration_GitHub.
Competing interests, final author contributions and the applicable ethics basis
still require completion. The frozen-output supplement must be uploaded to
the repository before its retained-output reproduction commands are usable.
Positive clinician/statistical feedback was reported by the author; it is not
an experimental clinician evaluation or independent label adjudication.
The manuscript discloses AI assistance. Journal acceptance is not guaranteed.

## Completing the source-only GitHub upload

See `docs/SUPPLEMENT_UPLOAD_GUIDE.md` for the ten supplement archives, exact
folder placement and remaining author declarations. Extract all archives into
the same parent folder, and merge their contents into the existing checkout.
Upload extracted files with their existing paths, rather than uploading ZIPs
as substitutes for the files referenced by the analysis scripts.
