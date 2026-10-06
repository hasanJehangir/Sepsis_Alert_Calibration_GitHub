# Stage-two findings: sepsis alert calibration across hospitals

**For Hasan Jehangir.** Completed 2026-09-30T00:19:28.071926+00:00. Actual computed results; all 3,000 pilot files were excluded from this stage. No CAPMI material was used.

## Main finding and decision

**Continue as a calibration/transport evaluation; do not submit the current study as a new superior early-warning method.** Full-feature gradient boosting’s source patient threshold alerted 7.5% of nonseptic test admissions in A → B, versus 31.2% in B → A. The same directional over-/under-target pattern appears in all three prespecified model variants. This is evidence about these two released hospitals, not a guarantee about other deployments.

Using the separate local calibration pool moved those rates to 10.4% and 11.1%. In B → A it also reduced six-hour-window case detection from 58.8% to 36.2%. In A → B local calibration increased both false alerts and detection slightly. Local calibration therefore changes an operating point; it does not provide a uniform benefit.

With local thresholds, any six-hour-window crossing occurred in 44.8% of A → B cases and 36.2% of B → A cases, while the **first** crossing occurred in that window in only 5.2% and 7.7%. Earlier first alerts account for 44.8% and 40.4% of cases. An earlier alert can still be clinically relevant; this experiment has no clinician-response or intervention evidence to decide that.

Changing the calibration unit from hours to admissions substantially changes workload (for example, B → A false alerts fell from 60.3% to 31.2%). By comparison, the finite-sample one-rank correction versus the empirical patient quantile changed the full-calibration natural-duration false-alert rates by at most 0.06 percentage points. Large workload reductions must not be attributed to a new conformal algorithm.

The defensible candidate manuscript question is: **How reliably do admission-level workload targets transfer, and what detection cost and calibration-sample variability follow from restoring them locally?** Close prior literature still makes novelty provisional. A protocol-aligned published-policy benchmark and an additional independent cohort are the next scientific priorities; these have not been completed here.

## Completion and sample accounting

The runner considered 37,336 reserved files, included 36,658 records and 1,254,335 pre-onset/negative scoring hours, and excluded 678 records. It fitted six source/model combinations and computed 3,168 policy-level result rows. All model, direction, cap, and calibration-sample outcomes are retained.

| Hospital | Role | Patients | Septic patients |
| --- | --- | --- | --- |
| A | calibration | 3693 | 271 |
| A | test | 3682 | 260 |
| A | train | 11113 | 778 |
| B | calibration | 3636 | 141 |
| B | test | 3627 | 154 |
| B | train | 10907 | 457 |

| Exclusion reason | Count |
| --- | --- |
| early_or_left_censored_onset | 644 |
| not_adult | 19 |
| onset_beyond_observed_record | 15 |

Model fits reporting convergence: 6/6. Details and warnings are retained in each model-info file. The plan was locally locked on 29 September before reserved data were downloaded; it was not publicly preregistered.

Verification: 14 implementation checks passed. An independent direct-crossing calculation matched all 72 natural-duration main-policy rows (504 endpoint-count checks and 144 hourly denominator/crossing checks). Pilot overlap was zero, cohort hashes were unique, and original manifest roles were preserved. This audit does not independently validate raw preprocessing or all capped/budget rows.

## Main cross-hospital results — natural-duration records

| Transfer | Model | Threshold calibration | Nonseptic patients alerted | Any alert in six-hour window | First alert in six-hour window |
| --- | --- | --- | --- | --- | --- |
| A → B | Gradient boosting | Source hourly | 794/3473 (22.9%) | 86/154 (55.8%) | 15/154 (9.7%) |
| A → B | Gradient boosting | Source patient | 261/3473 (7.5%) | 66/154 (42.9%) | 8/154 (5.2%) |
| A → B | Gradient boosting | Local patient (all) | 362/3473 (10.4%) | 69/154 (44.8%) | 8/154 (5.2%) |
| A → B | Logistic regression | Source hourly | 744/3473 (21.4%) | 72/154 (46.8%) | 7/154 (4.5%) |
| A → B | Logistic regression | Source patient | 298/3473 (8.6%) | 45/154 (29.2%) | 10/154 (6.5%) |
| A → B | Logistic regression | Local patient (all) | 361/3473 (10.4%) | 49/154 (31.8%) | 10/154 (6.5%) |
| A → B | Boosting, reduced features | Source hourly | 535/3473 (15.4%) | 49/154 (31.8%) | 12/154 (7.8%) |
| A → B | Boosting, reduced features | Source patient | 202/3473 (5.8%) | 25/154 (16.2%) | 5/154 (3.2%) |
| A → B | Boosting, reduced features | Local patient (all) | 364/3473 (10.5%) | 37/154 (24.0%) | 9/154 (5.8%) |
| B → A | Gradient boosting | Source hourly | 2064/3422 (60.3%) | 216/260 (83.1%) | 27/260 (10.4%) |
| B → A | Gradient boosting | Source patient | 1066/3422 (31.2%) | 153/260 (58.8%) | 19/260 (7.3%) |
| B → A | Gradient boosting | Local patient (all) | 380/3422 (11.1%) | 94/260 (36.2%) | 20/260 (7.7%) |
| B → A | Logistic regression | Source hourly | 2155/3422 (63.0%) | 188/260 (72.3%) | 11/260 (4.2%) |
| B → A | Logistic regression | Source patient | 1674/3422 (48.9%) | 151/260 (58.1%) | 17/260 (6.5%) |
| B → A | Logistic regression | Local patient (all) | 349/3422 (10.2%) | 59/260 (22.7%) | 14/260 (5.4%) |
| B → A | Boosting, reduced features | Source hourly | 1967/3422 (57.5%) | 194/260 (74.6%) | 20/260 (7.7%) |
| B → A | Boosting, reduced features | Source patient | 1096/3422 (32.0%) | 125/260 (48.1%) | 20/260 (7.7%) |
| B → A | Boosting, reduced features | Local patient (all) | 360/3422 (10.5%) | 37/260 (14.2%) | 10/260 (3.8%) |

These policies use the same fitted model within each transfer/model combination. Changing thresholds does not improve score discrimination. Hourly and patient calibration target different error events, so the false-alert reduction must be interpreted with the loss or gain in detection. Exact binomial intervals for every endpoint are in `results/main_metrics.csv`.

![Workload and detection trade-offs](results/transfer_comparison.png)

## Patient-paired comparisons

Differences below are percentage points, policy 1 minus policy 0. Negative false-alert differences mean fewer nonseptic patients alerted; positive sensitivity differences mean more cases detected. These are 2,000-draw paired bootstrap intervals conditional on the fitted thresholds, without multiplicity adjustment or calibration-threshold uncertainty.

| Transfer | Comparison | Endpoint | Difference, pp | 95% interval, pp | Patients |
| --- | --- | --- | --- | --- | --- |
| A → B | patient_minus_hourly | false_alert | -15.35 | [-16.53, -14.11] | 3473 |
| A → B | patient_minus_hourly | window6 | -12.99 | [-18.18, -7.79] | 154 |
| A → B | patient_minus_hourly | first6 | -4.55 | [-9.09, -0.65] | 154 |
| A → B | local_minus_source_patient | false_alert | +2.91 | [+2.39, +3.48] | 3473 |
| A → B | local_minus_source_patient | window6 | +1.95 | [+0.00, +4.55] | 154 |
| A → B | local_minus_source_patient | first6 | +0.00 | [-2.60, +2.60] | 154 |
| B → A | patient_minus_hourly | false_alert | -29.16 | [-30.63, -27.62] | 3422 |
| B → A | patient_minus_hourly | window6 | -24.23 | [-29.62, -19.23] | 260 |
| B → A | patient_minus_hourly | first6 | -3.08 | [-7.69, +1.15] | 260 |
| B → A | local_minus_source_patient | false_alert | -20.05 | [-21.36, -18.64] | 3422 |
| B → A | local_minus_source_patient | window6 | -22.69 | [-28.08, -17.69] | 260 |
| B → A | local_minus_source_patient | first6 | +0.38 | [-3.85, +4.62] | 260 |

## Local calibration budgets

The following table shows full-feature gradient boosting. Each budget samples completed admissions, then uses only nonseptic admissions for the threshold. Results summarize 20 fixed nested samples, on the same held-out test patients. The 5th–95th percentiles describe conditional calibration-sample variation, not population confidence intervals.

| Transfer | Admissions sampled | Median patient false alerts | 5th–95th percentiles | Median window detection | Median timely first alert |
| --- | --- | --- | --- | --- | --- |
| A → B | 100 | 8.4% | 6.7%–17.0% | 42.9% | 5.5% |
| A → B | 250 | 10.4% | 7.6%–12.3% | 44.8% | 5.2% |
| A → B | 500 | 10.4% | 8.8%–11.6% | 44.8% | 5.2% |
| B → A | 100 | 9.7% | 6.5%–14.3% | 33.7% | 7.7% |
| B → A | 250 | 10.2% | 8.2%–12.9% | 34.2% | 7.7% |
| B → A | 500 | 10.9% | 9.5%–13.0% | 35.4% | 7.7% |

![Calibration-budget variation](results/calibration_budgets.png)

The per-draw negative calibration counts and outcomes are in `all_metrics.csv`; all sampled IDs are in `calibration_samples.json`. Increasing sample size may stabilize a threshold without improving discrimination. Twenty samples from one calibration pool are not 20 external replications.

## Observation caps and additional timing diagnostics

Caps at ICU hours 24, 48, and 72 use separately recalibrated, equally capped negative trajectories. Early discharge retains shorter follow-up. Positive cases with onset after the cap are excluded from that cap’s case denominator and are never relabeled negative. Differences across caps also reflect different case cohorts.

| Transfer | Cap, h | Nonseptic | Cases evaluated | Later cases omitted | Patient false alerts | Window detection | Timely first alert |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A → B | 24 | 3471 | 38 | 116 | 9.9% | 15.8% | 13.2% |
| A → B | 48 | 3473 | 76 | 78 | 10.3% | 14.5% | 7.9% |
| A → B | 72 | 3473 | 103 | 51 | 10.4% | 19.4% | 6.8% |
| B → A | 24 | 3419 | 68 | 192 | 11.5% | 11.8% | 7.4% |
| B → A | 48 | 3422 | 133 | 127 | 11.3% | 11.3% | 7.5% |
| B → A | 72 | 3422 | 179 | 81 | 11.1% | 18.4% | 11.2% |

The twelve-hour diagnostic was specified after the pilot but before reserved-data analysis. Only available scores starting at ICU hour 6 can contribute; some early-onset cases have incomplete twelve-hour observation. It does not replace the six-hour primary target.

| Transfer | Policy | First alert in 6 h | First alert in 12 h | First alert earlier than 6 h |
| --- | --- | --- | --- | --- |
| A → B | Source hourly | 9.7% | 15.6% | 55.2% |
| A → B | Source patient | 5.2% | 9.1% | 39.6% |
| A → B | Local patient (all) | 5.2% | 11.7% | 44.8% |
| B → A | Source hourly | 10.4% | 21.9% | 75.0% |
| B → A | Source patient | 7.3% | 15.8% | 58.1% |
| B → A | Local patient (all) | 7.7% | 11.2% | 40.4% |

An early alert outside the chosen window is not automatically useless or harmful. Clinical interpretation requires a clinically justified workflow and prospective study. No repeat-alert silencing, intervention effect, or official Challenge utility score is simulated.

## Discrimination and feature ablation

| Transfer | Model | Hourly AUROC | Hourly AP | Brier | Positive-hour prevalence |
| --- | --- | --- | --- | --- | --- |
| A → B | Logistic regression | 0.731 | 0.031 | 0.0075 | 0.8% |
| A → B | Gradient boosting | 0.751 | 0.037 | 0.0084 | 0.8% |
| A → B | Boosting, reduced features | 0.713 | 0.021 | 0.0076 | 0.8% |
| B → A | Logistic regression | 0.697 | 0.043 | 0.0122 | 1.2% |
| B → A | Gradient boosting | 0.777 | 0.058 | 0.0123 | 1.2% |
| B → A | Boosting, reduced features | 0.701 | 0.027 | 0.0126 | 1.2% |

The reduced-feature tree model omits explicit measurement indicators, time since measurement, and current ICU hour. Native missing values and observed trajectories still carry care-process information. This ablation cannot establish causality or remove all site information. Hourly metrics receive no misleading independent-hour confidence intervals.

## Research and manuscript decision

The completed stage provides a reproducible empirical calibration/transport audit. It does not establish a new conformal algorithm, a clinically effective early-warning system, or a paper ready for a Q1 journal. `NOVELTY_AUDIT.md` documents close work on conformal sepsis prediction, international transfer, first-alert evaluation, and evaluation-strategy effects.

Before submission, the strongest defensible direction is an evaluation paper about workload targets and threshold transport. It requires a more complete comparison with published alert policies and preferably another independently defined cohort or clinical collaborator. A headline that only says “false alerts were reduced” would overstate the contribution. If timing remains poor or local effects disagree across directions, those findings must remain central.

Limitations: only two historical public hospitals; retrospective challenge labels; later-onset exclusions and end-of-record censoring; unknown repeated admissions beyond exact raw duplicates; no patient-weighted training; fixed model parameters; small case counts for some caps; calibration-sample variation conditional on one pool; no prospective clinical or intervention validation. Hourly scores are serially dependent; an hourly threshold does not imply an admission-level error guarantee. Patient rank guarantees require exchangeability and do not guarantee 10% error after arbitrary hospital or temporal shift.

## Reproduce and continue

Use `Sepsis_Stage2.ipynb` for the complete CPU workflow, or follow `README_STAGE2.md`. The source, trained models, hourly scores, subject statistics, sample IDs, and all result tables are retained. No paid API or GPU is needed. A fresh download requires internet access.

The execution service interrupted the first download; the recovered runner and locked specification were unchanged, and downloading resumed from saved records. Research computation occurs during active runs; no claim is made that experiments continued during the inactivity gap.

Free subscription publication may be available at suitable journals, but fees, current category/year quartile, scope, and actual acceptance timelines must be verified at submission. Neither Q1 acceptance nor actual publication within two to three months is guaranteed. No manuscript has been submitted.
