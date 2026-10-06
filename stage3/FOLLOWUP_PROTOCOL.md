# Stage 3: exploratory alert-policy follow-up

Written after all stage-two test outcomes were examined and before calculating these additional policies. This is an exploratory follow-up, not a new unseen test or public preregistration. Stage-two files and their locked specification are preserved. CAPMI is excluded.

## Question

For a frozen hourly model, distinguish the number of repeated alerts from the number of nonseptic admissions alerted, and quantify the detection/timing cost of temporal alert rules at comparable admission-level false-alert targets.

## Literature-grounded rules and scope of reproduction

1. **Hourly:** issue an alert whenever the current score is strictly greater than the threshold.
2. **Single:** retain only the first eligible alert per admission. Single-alert evaluation is used by Moor et al., doi:10.1016/j.eclinm.2023.102124.
3. **Silence 4 h:** after an emitted alert at hour t, the next eligible emission is at hour >= t+4. A four-hour suppression rule appears in Do et al., doi:10.2196/72083.
4. **Silence 6 h:** the same rule with next emission at hour >= t+6. Six-hour suppression appears in COMPOSER, doi:10.1038/s41746-021-00504-6.
5. **Three of five:** an hour is eligible if at least three scores in the inclusive five-hour window [t-4,t] exceed the threshold. Partial startup windows may qualify once three observations exist. Emit an alert at every eligible hour; do not invent a reset or clinician response. This adapts the warning-count rule of Gupta et al., doi:10.1371/journal.pdig.0000569.

Only alert-rule structures are adapted. We do not reproduce the published models, feature sets, training, patient sampling, outcome windows, or reported performance. Suppression boundaries are explicitly defined here where paper descriptions are not sufficient to identify a unique implementation. COMPOSER's original warning window differs from ours. A threshold of 0.5 is included only as a reference: unbalanced-training scores are not interchangeable with scores from another model.

## Inputs and cohort

Use only the completed stage-two cohort, six frozen prediction arrays, scoring hours, and calibration/test roles. No retraining, repartitioning, new label definition, positive-class balancing, or test-driven policy selection. Evaluate both test sites for each model/source, retaining internal controls and both hospital transfers. The natural-duration stage-two cohort is primary for this follow-up. Scoring starts at ICU hour 6 and stops before reconstructed onset for cases, or at observed record end for nonseptic controls. Outcomes are retrospective challenge labels, and missing later outcomes remain a limitation.

## Threshold conditions

**Fixed thresholds:** apply stage-two source-hourly, source-patient, all-local-patient, and source-80%-window-sensitivity thresholds, plus 0.5, unchanged to every alert rule. These isolate rule effects at a common underlying threshold. The 80% label describes the stage-two calibration criterion, not achieved test sensitivity or the sensitivity of a suppressed/aggregated rule.

**Matched admission targets:** alpha=0.05, 0.10, 0.20, using separate source or test-site calibration pools and only nonseptic admissions. For hourly/single/silence rules, admission score is the maximum hourly risk because all preserve the first crossing. For three-of-five, transform each hour to the third-largest available score in its last five hours; the admission score is the maximum of those values. Fewer than three observations give -infinity (the policy cannot alert). Apply the standard rank ceil((n+1)*(1-alpha)) to admission scores; rank > n gives +infinity. Reject NaNs, permit structural -infinity, and cross strictly greater than the threshold. Record structural ineligibility counts. Calibration is performed on completed, separately labeled admissions, not prospective outcome-free adaptation.

These transformations are standard order statistics, not a new algorithm. A finite-sample exchangeability statement does not imply error control under hospital shift. No policy is selected based on the displayed test frontier.

## Endpoints

- Fraction of nonseptic admissions receiving >=1 emitted alert, with exact 95% binomial intervals.
- Mean emitted alerts per nonseptic admission, and emitted nonseptic alerts per 100 observed scoring hours. Report numerator and denominator, avoiding an independent-hour confidence interval.
- Any emitted alert in [onset-6,onset), and first emitted alert in that window, with exact binomial intervals.
- First alert earlier than that window, first alert in the available 12-hour window, any pre-onset alert, and first-alert lead-time median/IQR conditional on alerting.

Count emissions rather than all underlying threshold exceedances for suppressed rules. A single-alert policy may miss a later warning-window alert after an early first emission. Earlier alerts are not automatically clinically useless. No treatment benefit, prospective PPV, intervention effect, alert-level decision curve, or official Challenge utility score is inferred from these truncated records.

For the matched **local alpha=0.10** comparison, compare each of three-of-five, silence-4h, and silence-6h with hourly, on the same test admissions. Use 2,000 paired patient-bootstrap draws (multinomial over the exact per-admission delta values), stratified by outcome, for patient false-alert rate, window sensitivity, first-window sensitivity, and mean negative alerts/admission. These are descriptive intervals conditional on model and thresholds; they exclude calibration uncertainty and multiplicity correction. Retain all directions/models, not only favorable results.

## Verification and provenance

Test strict crossings, rolling-window/startup behavior, causality, suppression boundaries, single-alert behavior, and structural ineligibility. On actual outputs assert that hourly, single, and suppression rules have identical patient false-alert and first-alert counts at a shared threshold; also assert matched patient thresholds are equal for those rules. The single rule must issue at most one alert/admission and its any-window count must equal its first-window count. Counts and burden under suppression cannot exceed hourly emissions. Compare hourly fixed anchors with all original natural-duration stage-two counts.

Hash inputs, code, config and protocol; record stage-two provenance, environment, tests, and result counts. An implementation correction must be logged; do not disguise post-result changes as prior decisions. External validation remains unperformed until an appropriately authorized, nonoverlapping cohort is obtained and its labels/features are harmonized. Any manuscript must mark this section as exploratory.
