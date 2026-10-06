# Stage 2: locked analysis specification

Prepared 29 September 2026 after the 3,000-record pilot and before loading any reserved records. This is a timestamped local analysis specification, not an independently registered protocol. CAPMI material is excluded.

## Purpose and interpretation

Evaluate transport of a fixed admission-level false-alert target between hospitals, local calibration sample requirements, observation caps, and timing trade-offs. This is an application and evaluation of established threshold-calibration methods. Neither conformal prediction for sepsis nor reducing sepsis false alarms is novel. The combined study's contribution remains provisional. Primary hypotheses are descriptive comparisons, with all outcomes retained irrespective of direction.

## Data partitions and audit

Use the original 40,336-file manifest. Exclude all 3,000 pilot files from all stage-2 fitting, calibration, and testing. The other 37,336 records retain their original per-site 60% train / 20% calibration / 20% test hash partitions. No repartitioning by outcome. The pilot cohort/exclusion rules and causal features in `experiment.py` are unchanged.

Detect exact duplicated raw records using SHA-256 before model fitting. Exclude reserved records that exactly match any pilot record. For duplicates among remaining reserved records retain one deterministically in priority order train, calibration, test, then site/name; log every exclusion. This does not identify different admissions for the same real person or near-duplicate trajectories. Check subject-file disjointness and raw-file hashes. No real hospital identities are inferred.

The primary cohort is adults with later-onset sepsis under the original pilot rules. The released labels already precede reconstructed onset by six hours. Exclude onset after the last observed hour; score hours >=6 and strictly before onset. No post-onset training or testing. Preserve natural prevalence. Nonseptic status means no positive challenge label in the released record, not absence of subsequent disease after discharge.

## Models and fitting

Fit independently on each source hospital's reserved training partition; evaluate both hospitals' reserved test partitions. All preprocessing is fit on training data only. No hyperparameter search, test-driven selection, or selection of a best seed.

1. Logistic regression: median imputation with empty features retained, standard scaling, L2 penalty, C=1, LBFGS, maximum 1,000 iterations, tolerance 1e-5. No class weighting or resampling. Store convergence status; if it does not converge, report the limitation rather than silently tuning.
2. Histogram gradient boosting: 200 iterations, learning rate 0.07, 15 leaves, minimum 40 samples per leaf, L2 regularization 1, early stopping disabled, seed 20260929. This doubles the pilot's fixed iteration budget and is chosen before reserved-data access.
3. Prespecified feature ablation: the same gradient boosting model, removing the 34 measurement flags, 34 elapsed-measurement-time features, and current ICU hour. Retain 51 inputs. This removes explicit observation-process features but cannot remove all missingness information, including native missing-value handling and imputed trajectories.

Training rows are hourly observations, without patient reweighting. Thus long stays contribute more training rows; this is a limitation. The study varies thresholds for a frozen model, not the model after local calibration.

## Calibration

Target alpha=0.10. Source and target calibration pools are disjoint from fitting and evaluation. Completed calibration admissions have retrospective labels available; this is not outcome-free or online adaptation.

- Source hourly: finite rank of all eligible nonseptic source calibration hourly scores.
- Source patient: finite rank of one maximum score per nonseptic source calibration stay.
- Source empirical patient: ordinary inverted-CDF empirical 90th percentile of the same patient maxima (rank ceil(0.9*n)), exposing the role of calibration unit versus rank correction.
- Target patient, all: finite rank of nonseptic target calibration maxima.
- Target empirical patient, all: ordinary empirical quantile on that same target pool.
- Target patient budgets 100, 250, 500: sample that many eligible completed target calibration admissions without replacement, then retain the nonseptic ones for calibration. Count and report both admissions sampled and negative calibration patients. Twenty fixed seeds: 20261001 through 20261020. Use a common permutation for nested budgets within each seed. Retain every sample result and sampled identifier list.

Finite rank is ceil((n+1)*(1-alpha)); a rank above n yields infinity. Threshold crossings use strictly greater than, retaining conservative tie handling. The hourly comparator has longitudinal dependence and is not asserted to have an independent-hour guarantee. The patient finite-sample guarantee is marginal over exchangeable patient draws, not conditional on an arbitrary fitted threshold, and does not apply under arbitrary hospital or future temporal shift.

## Observation policies

Primary: all eligible observed pre-onset hours for positive stays and eligible observed hours for nonseptic stays. Secondary: administrative caps at ICU hours 24, 48, and 72, including recorded scores up to and including the cap. Earlier discharge retains its shorter available observation period; these are capped-record policies, not guaranteed complete fixed follow-up.

For each cap, recalibrate every policy using equally capped negative trajectories. For six-hour and twelve-hour case sensitivity, include only positive stays with reconstructed onset at or before the cap; later-onset positives are counted separately and excluded from that cap's case denominator, not relabeled negative. Negative calibration and test subjects remain patients without sepsis anywhere in the observed record. This conditional case/control definition is retrospective and must not be interpreted as prospective population precision. The primary natural-duration endpoints remain unchanged.

## Endpoints and uncertainty

Primary reporting pairs (a) nonseptic patients receiving at least one alert and (b) sensitivity for any crossing within [onset-6, onset). Timely-first-alert sensitivity in that same six-hour window is reported alongside both. Also report first alerts earlier than the window, missed cases, hourly false-positive fraction, hourly AUROC/AP, and Brier score. Native model scores are not asserted to be probability-calibrated.

Prespecified timing diagnostics: any crossing and first alert within [onset-12, onset), and the lead-time distribution among alerted positive stays. These do not replace the six-hour primary window and are motivated by the poor timing seen in the pilot. No clinical benefit is inferred from an earlier alert alone. No refractory-period, intervention, or clinician-response simulation is included.

For individual patient proportions, use exact two-sided 95% binomial intervals. For primary natural-duration policy differences, use 2,000 patient-paired bootstrap draws, stratified by outcome, with seed 20260929. Compare source patient versus source hourly and target patient (all calibration admissions) versus source patient on the same test subjects. Estimate false-alert, window-sensitivity, and first-alert differences; intervals are descriptive, without multiplicity adjustment.

For the 20 local-calibration samples at each budget, report the median, minimum, maximum, and 5th/95th percentiles of test performance. These are conditional resampling variability summaries, not 95% population confidence intervals or independent external replications. Each sample's binomial interval is conditional on its threshold. The all-calibration paired bootstrap does not include calibration-threshold uncertainty.

The target patient empirical and finite-rank policies use almost the same operating point. Compare them explicitly, avoiding attribution of a large gain to a one-rank correction. Source-hourly and source-patient nominal 10% targets concern different events. A false-alert reduction therefore does not establish an improvement in discrimination.

For additional fair operating-point context, select a source threshold achieving at least 80% empirical six-hour-window case sensitivity on source calibration patients, using the highest representable threshold that retains that fraction (ties handled with nextafter toward minus infinity). Apply it unchanged to both test sites. This is a descriptive sensitivity-target comparator, not a guarantee. It is fit separately for each observation cap. If too few positive calibration cases are available, report counts and limitations.

## Analysis boundaries

Report each source direction and model independently; do not pool hospital rates to conceal opposing shifts. No model or threshold is selected using test outcomes. Do not use subgroup, cap, or budget results to redefine a favorable primary endpoint. Age/sex subgroup investigation and comparison with published alert-policy implementations are future work, not claimed completed by this runner. The official Challenge utility is not used; comparisons with its leaderboard or other papers' reported percentages are invalid without aligned definitions.

If timing remains weak, local adaptation is inconsistent, or the contribution is already covered, recommend reframing or stopping the current method claim. Do not fabricate a positive result or proceed directly to submission. Remaining limitations include two public historical hospitals, retrospective labels, no prospective clinical evaluation, and unknown related admissions. A paper may need clinical input and an additional dataset.

## Provenance

The runner records this protocol's hash, input-manifest hash, code hashes, dependency versions, raw-file hashes, wall time, model convergence, and split counts. A `protocol_lock.json` is written before downloading reserved records. Bug fixes after that lock must be recorded separately; no change may be disguised as a pre-test decision. All output tables retain numeric counts as well as proportions.
