# Stage-three follow-up: alert rules and workload targets

Completed 2026-09-30T19:43:30.462140+00:00. These are computed exploratory results using the same stage-two test records, which had already been examined. No model was retrained; no CAPMI material was used.

The run retained 660 policy-level rows and 144 paired endpoint comparisons, covering six frozen source/model combinations, both test hospitals, five alert rules, fixed threshold references, and patient targets of 5%, 10%, and 20%. Six new implementation checks and all actual-data invariance/anchor checks passed.

## What the benchmark changes

**Repeat-alert suppression reduces alert emissions, not the number of admissions experiencing their first alert at the same threshold.** In full-feature boosting at the local 10% target, four-hour suppression reduced nonseptic emissions by 68.3% (A → B) and 57.5% (B → A). Admission false-alert and first-window-alert counts were unchanged, as required by the rule.

Any emitted alert in the six-hour window fell from 44.8% to 43.5% in A → B and from 36.2% to 34.6% in B → A. With single-alert evaluation, that endpoint equaled first-window sensitivity: 5.2% and 7.7%. Retaining only the first alert changes what counts as later detection.

**Three-of-five is not a demonstrated improvement at matched targets.** For full-feature boosting, local first-window sensitivity changed from 5.2% to 7.8% in A → B but from 7.7% to 5.4% in B → A. Both paired intervals included zero. Mean nonseptic emissions/admission increased in both directions after recalibration. Its per-hour eligibility is reevaluated without a reset, so repeated eligible hours can emit repeated alerts. This is an explicitly defined policy adaptation, not a claim about the full published SepsisAI implementation.

## All models: separately calibrated local 10% admission target

| Transfer | Model | Alert rule | Nonseptic admissions alerted | Emissions/100 negative hours | Any window alert | First window alert |
| --- | --- | --- | --- | --- | --- | --- |
| A → B | Gradient boosting | Hourly | 10.4% | 3.690 | 44.8% | 5.2% |
| A → B | Gradient boosting | Single | 10.4% | 0.326 | 5.2% | 5.2% |
| A → B | Gradient boosting | Silence 4 h | 10.4% | 1.170 | 43.5% | 5.2% |
| A → B | Gradient boosting | Silence 6 h | 10.4% | 0.867 | 43.5% | 5.2% |
| A → B | Gradient boosting | Three of five | 10.7% | 4.639 | 45.5% | 7.8% |
| A → B | Logistic regression | Hourly | 10.4% | 3.240 | 31.8% | 6.5% |
| A → B | Logistic regression | Single | 10.4% | 0.325 | 6.5% | 6.5% |
| A → B | Logistic regression | Silence 4 h | 10.4% | 1.204 | 30.5% | 6.5% |
| A → B | Logistic regression | Silence 6 h | 10.4% | 0.920 | 28.6% | 6.5% |
| A → B | Logistic regression | Three of five | 10.6% | 5.050 | 35.7% | 5.8% |
| A → B | Boosting, reduced | Hourly | 10.5% | 2.963 | 24.0% | 5.8% |
| A → B | Boosting, reduced | Single | 10.5% | 0.328 | 5.8% | 5.8% |
| A → B | Boosting, reduced | Silence 4 h | 10.5% | 1.022 | 22.7% | 5.8% |
| A → B | Boosting, reduced | Silence 6 h | 10.5% | 0.791 | 23.4% | 5.8% |
| A → B | Boosting, reduced | Three of five | 10.3% | 4.383 | 26.6% | 5.8% |
| B → A | Gradient boosting | Hourly | 11.1% | 1.542 | 36.2% | 7.7% |
| B → A | Gradient boosting | Single | 11.1% | 0.338 | 7.7% | 7.7% |
| B → A | Gradient boosting | Silence 4 h | 11.1% | 0.655 | 34.6% | 7.7% |
| B → A | Gradient boosting | Silence 6 h | 11.1% | 0.546 | 33.8% | 7.7% |
| B → A | Gradient boosting | Three of five | 11.7% | 2.590 | 37.7% | 5.4% |
| B → A | Logistic regression | Hourly | 10.2% | 0.747 | 22.7% | 5.4% |
| B → A | Logistic regression | Single | 10.2% | 0.310 | 5.4% | 5.4% |
| B → A | Logistic regression | Silence 4 h | 10.2% | 0.510 | 22.3% | 5.4% |
| B → A | Logistic regression | Silence 6 h | 10.2% | 0.454 | 20.8% | 5.4% |
| B → A | Logistic regression | Three of five | 10.5% | 3.136 | 31.5% | 5.8% |
| B → A | Boosting, reduced | Hourly | 10.5% | 2.386 | 14.2% | 3.8% |
| B → A | Boosting, reduced | Single | 10.5% | 0.320 | 3.8% | 3.8% |
| B → A | Boosting, reduced | Silence 4 h | 10.5% | 0.846 | 13.5% | 3.8% |
| B → A | Boosting, reduced | Silence 6 h | 10.5% | 0.675 | 13.1% | 3.8% |
| B → A | Boosting, reduced | Three of five | 10.3% | 3.415 | 16.2% | 4.6% |

![Repeated alert burden](results/alert_burden.png)

![Workload and detection](results/workload_detection.png)

Exact binomial intervals and numerators/denominators are retained in `policy_metrics.csv`. The 2,000-draw paired bootstrap is conditional on the model and thresholds, excludes calibration uncertainty, and has no multiplicity correction. Alert-rate denominators are observed pre-onset/negative scoring hours, not a prospectively sampled clinical population.

## Literature scope

Policy structures are grounded in Gupta et al. (2024), doi:10.1371/journal.pdig.0000569; Do et al. (2026), doi:10.2196/72083; Shashikumar et al. (2021), doi:10.1038/s41746-021-00504-6; and Moor et al. (2023), doi:10.1016/j.eclinm.2023.102124. Their complete models and reported percentages are not reproduced. See `FOLLOWUP_PROTOCOL.md` for exact boundaries and adaptation details.

## Manuscript decision

A research manuscript draft now combines the locked calibration/transport study with a separately identified exploratory policy section. The data support an evaluation of asymmetric threshold transport and distinctions between alert burden, admissions alerted, and detection timing. They do not establish a new conformal algorithm or superior clinical warning system.

External validation is not completed. Approved access to another cohort was not supplied, and no restricted patient dataset was accessed. Before calling a new cohort independent, audit hospital/patient overlap and harmonize variables, sepsis labels, and the scoring timeline. Ethics, authorship, affiliations, funding, conflicts, and AI-use disclosures require author review. Current Q1 category/year and realistic journal timing remain publication checks, not guarantees.

## Reproduce

From the project root, install the pinned original requirements, run `python3 -m pytest -q stage3/tests`, then `python3 stage3/run_followup.py` and `python3 stage3/report_followup.py`. The standalone stage-three package contains the exact frozen predictions, scoring hours, and required stage-two metadata. It requires no internet after installing dependencies. When using the original full stage-two archive instead, `--restore-hours` reconstructs the omitted scoring-hour cache from public records and verifies its original hash.
