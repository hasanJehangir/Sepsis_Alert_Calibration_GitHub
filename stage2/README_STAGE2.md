# Stage 2 — full hospital-transfer study

This extends the independent sepsis pilot. It uses the other 37,336 manifest records, with all 3,000 pilot records excluded from stage-2 fitting, calibration, and testing. Read `STAGE2_PROTOCOL.md` and `NOVELTY_AUDIT.md` before interpreting the results.

From the main `Sepsis_Alert_Calibration` folder, with Python 3.12 and the pinned requirements installed:

```bash
python3 -m pytest -q tests stage2/tests
python3 download_data.py
python3 download_data.py --full
python3 stage2/run_stage2.py --stage all
python3 stage2/audit_results.py
python3 stage2/report_stage2.py
```

The complete results archive includes the public dataset files, so the two downloader commands can be skipped there. They are needed for a fresh source-only or notebook run.

The runner supports `--stage prepare`, `--stage train`, and `--stage evaluate` separately. Completed feature/model checkpoints are reused only when code, protocol, config, and dependency signatures match. Do not delete mismatch checks to reuse stale models. Preserve a prior run and use a clean copy when deliberately changing an experiment, documenting that previously examined test outcomes are no longer unseen.

The original `protocol_lock.json` records the plan before reserved-data download in this session. It is not a public preregistration. Reproducing this package later does not constitute a new prospectively registered study.

## Main outputs

- `results/completed.json`: completion, cohort, environment, and provenance.
- `results/cohort_counts.csv` and `exclusions.csv`: actual sample accounting and exclusion reasons.
- `results/main_metrics.csv`: all prespecified full-calibration and sensitivity-target policies.
- `results/all_metrics.csv`: those policies plus every local-budget draw.
- `results/budget_summary.csv`: conditional variation over the 20 calibration samples, not population confidence intervals.
- `results/paired_differences.csv`: descriptive 2,000-draw patient-paired bootstrap differences.
- `results/first_alert_timing.csv`: first-alert lead time per positive case under the main natural-duration policies.
- `results/*_scores.csv.gz`: per-patient sufficient statistics for threshold endpoints, including calibration and test roles.
- `results/*_predictions.npz`: packed hourly probabilities for each fitted model; training positions are NaN by design.
- `results/cohort.csv`: row offsets linking those probability arrays to patients.
- `results/*_model.joblib` and `*_model_info.json`: fitted classifiers, feature columns, convergence, and fit provenance.
- `results/discrimination.csv`: hourly AUROC, average precision, Brier score, and label prevalence. No independent-hour confidence intervals are claimed.
- `results/independent_audit.json`: a second direct calculation of first crossings and endpoint counts for all 72 natural-duration main-policy rows, plus split and pilot-overlap checks. This does not independently validate the entire preprocessing or every capped/budget row.

`cache/x.npy`, `cache/hours.npy`, and `cache/labels.npy` are rebuildable intermediate feature arrays. They are omitted from the shareable results archive. Public PSV files, source hashes, and the preprocessing implementation let you rebuild them.

The study is retrospective research. Its results do not establish clinical benefit or a new method, and journal acceptance is not guaranteed. The original pilot remains preserved separately.
