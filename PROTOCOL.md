# Patient-level false-alert calibration for cross-hospital sepsis warning

Status: development protocol, restored 29 September 2026 after the first pilot results were known. This is not a public preregistration. The restoration and rerun do not constitute independent replication. The 37,336 records outside the development pilot have not been loaded by the pilot program.

## Independence and intended contribution

This is a new ICU sepsis project. It does not use CAPMI's code, manuscript, checkpoints, results, or private data. The research question, clinical outcome, public dataset, and evaluation are separate.

**Question:** How does the unit of threshold calibration (an individual hour versus the maximum score within a nonseptic patient's observed stay) affect patient false-alert probability, warning timing, and transfer between hospitals? Can a separate, small sample of completed local admissions improve calibration after transfer?

The quantile formula is standard split-conformal calibration, not a new algorithm. The difference between hourly and patient metrics, sepsis alarm reduction, and conformal methods in healthcare are already studied. The candidate contribution is a reproducible joint evaluation of calibration unit, hospital transfer, local calibration sample size, observation duration, and the timing of the first alert. Novelty remains provisional and requires a deeper comparison with the closest literature before submission.

## Data and development split

- Public PhysioNet/CinC Challenge 2019, version 1.0.0, DOI: https://doi.org/10.13026/v64v-d857.
- Hospital A: 20,336 released records; hospital B: 20,000 released records. Hospital names are not inferred.
- Within each hospital, order filenames by SHA-256 of `20260929|{site}|{filename}`. The first 1,500 per hospital form the development pilot. Their later reuse in any final test is prohibited.
- Pilot A: first 60% training, next 20% calibration, last 20% evaluation. Pilot B: first 20% calibration, remaining 80% evaluation. Roles are assigned before applying exclusions.
- Remaining 37,336 files receive separate 60% training, 20% calibration, 20% test roles in the manifest. The pilot program downloads and opens only the 3,000 development records. A final protocol must be locked before accessing the reserved test records.
- Subject-level files are the available grouping unit. Cross-file repeated admissions cannot be excluded without an original patient identifier; this is a limitation.
- No prevalence balancing or test-set oversampling.

## Cohort and labels

- Adults aged 18 or older; at least six recorded ICU hours; contiguous hourly `ICULOS` values and binary, monotone sepsis labels.
- Begin scoring at ICU hour 6.
- Released `SepsisLabel` is already shifted six hours before the challenge sepsis onset. For positive stays, reconstruct onset as first positive-label hour plus six. Do not shift the prediction labels again.
- Exclude positive stays whose first positive label occurs at or before hour 6: these provide insufficient uncontaminated observation and can be left-censored. Exclude reconstructed onset after the last recorded hour.
- Positive stays are evaluated only before reconstructed onset. Nonseptic stays are evaluated throughout their eligible observed record.
- These exclusions define a later-onset sepsis cohort, not all ICU sepsis. End-of-record negatives may also be affected by censoring. Labels are retrospective challenge labels, not independently adjudicated prospective diagnoses.

## Features and model

- At each hour, use 34 current/last-observed physiological variables, four contextual variables (`Age`, `Gender`, `HospAdmTime`, current `ICULOS`), measurement indicators, capped time since measurement, six-hour trailing means of seven vital signs, and their change from six hours earlier: 120 inputs.
- Forward fill only. No backward fill, whole-stay summaries, future measurements, future length of stay, or outcome indicators as inputs. Exclude `Unit1` and `Unit2`.
- A fixed histogram gradient boosting classifier is fit only on A pilot training hours, predicting the provided six-hour warning labels. Parameters are documented in `experiment.py`. There is no tuning against evaluation outcomes.
- Missingness and current ICU time can encode care-process differences. Their removal must be an explicit confirmatory ablation, not an assumed solution to shift.

## Calibration and policies

Let alpha = 0.10. With n nonseptic calibration units and scalar scores s, choose the k-th smallest score, where k = ceil((n+1)(1-alpha)). If k exceeds n, use an infinite threshold. Trigger only when the risk score is strictly greater than the threshold.

1. **Source hourly:** each eligible hour from a nonseptic A calibration stay is a calibration unit. This is an intentionally conventional comparator. Its hourly rank rule has no independent-hour exchangeability guarantee within longitudinal stays.
2. **Source patient:** the maximum risk score across each nonseptic A calibration stay is a calibration unit.
3. **Target patient:** the same patient-maximum rule, using only the disjoint B calibration stays, with the A model frozen. Retrospectively known nonseptic status is available after these admissions finish; this is not an outcome-free online adaptation method.

The nominal 10% targets refer to different events for policies 1 and 2. Lower patient false-alert rates at policy 2 are partly expected from using the relevant unit; they are not evidence of improved discrimination or a novel mathematical result.

For patient-level calibration, a finite-sample **marginal** false-alert guarantee requires exchangeable completed nonseptic calibration and test records, the same observation horizon and scoring procedure, and independence from model fitting. It does not guarantee that a particular evaluation sample or fixed fitted threshold has a false-alert rate below 10%. It does not survive arbitrary hospital or temporal shift. The claim concerns nonseptic patient false alerts, not sepsis sensitivity, precision, or clinical safety. Hospital-stratified local calibration restores no guarantee if future local admissions themselves shift.

## Development endpoints

- Patient false-alert rate: fraction of nonseptic patients with at least one threshold crossing during the eligible record; exact two-sided 95% binomial interval.
- Six-hour-window sensitivity: fraction of septic patients with any crossing in [onset-6, onset). Crossings earlier in the stay do not disqualify this metric.
- Timely first-alert sensitivity: fraction of septic patients whose first eligible crossing occurs in that same six-hour window.
- Premature first-alert fraction: fraction of septic patients whose first crossing precedes that window. “Premature” means outside this protocol's window, not proven clinical harm or absence of usefulness.
- Hourly false-positive rate, AUROC, average precision, and Brier score are descriptive secondary measures. They do not account for patient-level clustering and receive no misleading independent-hour confidence intervals.
- No refractory period or repeat-alert policy is simulated. The official Challenge utility score is not implemented, so these results are not comparable with Challenge leaderboard scores.

## Confirmatory study to lock before reserved test access

1. Fit both a transparent regularized logistic baseline and a tree model; train and tune only within each source training partition, grouped by patient. Preserve all development exclusions and report their impact.
2. Evaluate both A-to-B and B-to-A transfers, with held-out same-site comparisons. Separate fitting, calibration, and test admissions by manifest role.
3. Compare source hourly, source patient, and target patient thresholds. Include a simple empirical patient-maximum quantile comparator to expose whether any benefit is just the calibration unit, rather than the finite-sample rank correction.
4. Evaluate local calibration budgets of 100, 250, and 500 completed admissions, using prespecified repeated random samples without using test outcomes. Report the resulting number of eligible nonseptic calibration stays. Use 20 fixed seeds, 20261001 through 20261020, rather than selecting the best sample.
5. Separate natural-duration stays from fixed 24-, 48-, and 72-hour observation policies. Apply identical horizon/censoring definitions to the calibration and test units; a whole-stay threshold cannot be casually claimed to control a different horizon. Stratify duration as a diagnostic, without conditioning a guarantee on it.
6. Report patient false-alert rate and both sensitivity definitions together. Add sensitivity-matched and false-alert-matched comparisons on calibration data where feasible; do not choose a favorable operating point using test labels. Timing and workload trade-offs are central, not auxiliary.
7. Use exact binomial intervals for individual proportions; patient-paired bootstrap intervals for differences between policies on the same test cohort. Include calibration-sample variability separately. Avoid treating hours as independent samples.
8. Ablate measurement indicators/time-since-measurement and current ICU hour. Inspect sex and age strata if event counts support estimation; do not make small-subgroup fairness claims.
9. Audit label reconstruction, any duplicated trajectories, onset exclusions, end-of-stay censoring, feature causality, train/calibration/test separation, and site-specific prevalence before reporting final results.
10. Record every change prompted by this pilot. Freeze a versioned analysis plan before final test access. If the combined contribution remains covered by prior work or timing stays poor, report that honestly and reconsider the study's scope; do not rename known methods or hide unfavorable results.

## Go/no-go and publication

The development pilot already shows poor timely-first-alert sensitivity. A lower false-alert rate alone is insufficient for claiming an improved early-warning system. A rigorous calibration/transport audit might still be valuable, but acceptance or Q1 suitability is not established.

Free publication may be possible through a journal's subscription/traditional route; this is different from free open access. Journal scope, current quartile database/category/year, submission rules, and optional charges must be checked at submission. No journal can be promised to accept and publish this work within two to three months. No manuscript is submitted by this project package.

## Reproducibility and provenance

The implementation, environment pins, deterministic file manifest, raw pilot data hashes, model, hourly predictions, cohort exclusions, and machine-readable metrics are retained. Tests cover temporal causality, rank behavior, threshold ties, patient versus hourly endpoints, pilot isolation, and the released label shift.

The first pilot completed before a temporary runtime reset. Code was restored from logged implementation and rerun on the same fixed sample. This file was reconstructed after the first results were known; its present hash is recorded by the rerun. It must never be described as a prospectively registered pilot protocol.
