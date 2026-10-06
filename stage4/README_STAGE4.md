# External demo evaluation and actual-human-review handoff

Read `External_Validation_Report.md` first. External scoring is complete, detection is weak, cross-resource institution/patient independence is unverified, and actual human review is pending. CAPMI was not used. The unchanged prior manuscript is included for review.

## Reproduce locally

Extract the ZIP. Use Python 3.12 and run from the extracted `Sepsis_Alert_Calibration` directory:

```bash
python -m pip install -r stage4/requirements_stage4.txt
python stage4/run_reproduction.py
```

The wrapper verifies every packaged file against `stage4/package_manifest.json`, tests the adapter, and reruns both external studies in separate temporary copies. It compares their numerical tables and all 24 prediction vectors to the archived outputs. It preserves both original completion records and both protocol locks. Its result and logs are written to `stage4/reproduction/`.

Do not rerun the two drivers consecutively in the same folder: the amended lock deliberately verifies the original completion record, which a baseline rerun would replace with a new timestamp. Use the wrapper above. The source models are never trained or changed.

Read the saved report to inspect recorded results. To regenerate the report/figures in a working copy without rerunning scoring:

```bash
python stage4/report_external.py
```

The full package integrity check expects a pristine extraction. If you edit packaged files or regenerate figures, extract a fresh copy before running that check. Reproduction logs themselves are outside the manifest and can be overwritten by subsequent checks.

The full original Challenge-data analysis needs the earlier Stage 3 project package and its data acquisition workflow. This package supplies its frozen models, manuscript, numerical tables and audit evidence, and completely reproduces the **external demo** evaluation.

## Colab

Open the supplied `Sepsis_Stage4_Colab.ipynb` in Colab and run its cells. Upload this package ZIP when prompted. The notebook checks the archive hash, extracts the project, installs pinned packages, calls the same isolated-copy reproduction wrapper, and downloads the verification record. Python 3.12 is the verified local environment. If dependencies cannot be installed in a different Colab runtime, use the local workflow above. The notebook was validated here but was not executed in a signed-in Colab session.

## Human review

Give `Human_Review_Packet.md`, the report, the source manuscript and complete results to a named critical-care/sepsis clinician and a human methods reviewer. All reviewer assessment/signature fields are blank. Review aids include all 17 test cases and 40 negatives selected without looking at model scores. They are pre-onset predictor timelines, not complete diagnostic charts or a Sepsis-3 adjudication dataset.

## Package structure

- `stage4/results/`: unchanged initial external run (180 comparisons).
- `stage4/results_amended/`: post-test chart-harmonization amendment (180 comparisons).
- `stage4/all_external_*.csv`: both runs together without winner selection.
- `stage4/review/`: numerical audits, documentation discrepancy, case index, timelines, key and blank forms.
- `stage4/data/`: checksum-verified open raw eICU inputs and pinned YAIB demo labels.
- `stage2/results/`: six frozen source models, their feature indices and source thresholds.
- `stage3/`: original follow-up helper/configuration and numerical results.
- `stage4/reference/`: unchanged current manuscript PDF; no redistributed full-text third-party articles.

Original and amended completion timestamps naturally differ on reproduction. They are not numerical outcomes and are excluded from output-table comparison. Every frozen input and archived source model must match exactly.

## Dataset rights and attribution

Public eICU Demo data and YAIB derived demo databases are under Open Database License 1.0. Preserve attribution, license and applicable share-alike requirements for database adaptations. Do not treat the YAIB code's MIT license as permission to relicense the data. See `stage4/data/eicu/LICENSE.txt` and `DATA_ATTRIBUTION.md`. No credentialed full-database records, CAPMI data or personal reviewer contact details are included.
