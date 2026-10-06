# Human review packet — pending actual review

**No clinician or statistician has reviewed or approved this study.** This packet contains real results, a completed AI-assisted audit and blank reviewer forms. It is a handoff for human work, not a completed human review or an ethics approval. The source manuscript is an unchanged draft.

## Material to read

1. `External_Validation_Report.md`: both external runs, counts, exact intervals and limits.
2. `reference/Sepsis_Calibration_Manuscript_Draft.pdf`: existing 11-page manuscript, not yet revised to incorporate the demo evaluation.
3. `EXTERNAL_PROTOCOL.md`, `external_lock.json`, `AMENDMENT_01_CHARTED_MEASUREMENTS.md`, `external_amended_lock.json`: original plan and explicit post-test amendment.
4. `all_external_policy_metrics.csv`, `all_external_discrimination.csv`: all 360 comparisons and all model/unit variants.
5. `review/independent_numerical_audit.csv`, `review/external_numerical_audit.csv`, `test_results.txt`: automated audit evidence; the filename “independent” refers to a separate arithmetic implementation, not a human reviewer.
6. `review/clinical_case_index.csv`, `review/case_input_timelines.csv.gz`, `review/case_reference_key.csv`, `review/human_case_review_form.csv`: case-level review aids.

The case aids include all 17 test positives and 40 test negatives sampled by a fixed hash independent of model scores. They are an audit sample, not a prevalence estimate or a representative clinical cohort. Rows have neutral review IDs and the benchmark label/onset key is stored separately. No formal blinded review has been performed. Timelines show available predictor values at scoring hours: `*_observed_in_hour` is a new measurement in that hour, and `*_last_available` includes forward-carried values. They stop before the reconstructed event for cases. These materials do not include complete antibiotic/culture, vasopressor, GCS and urine-output evidence, and cannot establish clinical Sepsis-3 adjudication. Consult the public raw sources and obtain additional authorized evidence before making that claim.

## Clinical questions requiring a sepsis/critical-care clinician

| Priority | Finding | Concrete review request | Current decision |
| --- | --- | --- | --- |
| Blocking | eICU benchmark uses modified suspected infection and SOFA timing; Challenge has a different target | Compare definitions and cohort-generation code. Decide whether to call this only a label-shift transport experiment; specify an appropriate matched clinical target for a new cohort. | Pending |
| Blocking | Onset is reconstructed as the first positive published grid hour +6 | Check event-window construction, integer-hour alignment and censoring assumptions. Do not certify a true bedside onset from this formula alone. | Pending |
| Blocking | Challenge printed Lactate/Magnesium units conflict with numeric scales | Resolve original data units using primary provenance. Review native/masked sensitivity results. Do not infer the correct conversion from better model performance. | Pending |
| Blocking | Public IDs cannot prove nonoverlap with Challenge; overview says 20 hospitals but released tables contain 186 surrogate IDs | Seek authoritative clarification and choose a verifiably separate institution if needed. Do not certify independence or a clinical hospital count based on these IDs. | Pending |
| Major | Early-onset cases are excluded; observation capped at 168 hours | State which clinical population and decision point this represents. Assess selection and length-of-stay effects. | Pending |
| Major | Temperature comes from probes and nursing charts; arterial/noninvasive BP share channels; FiO2 percentages/fractions are harmonized | Check unit conversions, semantic equivalence, implausible values and effect of measurement frequency. Review the amendment before endorsing mapping. | Pending |
| Major | Lab revision/entry offsets used as availability proxies | Decide whether “available to a real-time model” is defensible; identify any source-time ambiguity that should limit claims. | Pending |
| Major | Full HGB with local calibration detects 0/17 and 1/17 cases in amended native-unit evaluation | Decide whether any useful clinical detection claim is supported. Current evidence supports cautious reporting of transport failure, not deployment. | Pending |
| Major | Silencing reduces emitted alerts but preserves first alert/admission outcomes at shared thresholds | Define an actionable episode, acceptable repeat-alert policy and whether an alert far before the event is useful or a nuisance. Clinical utility is not measured here. | Pending |

For a true diagnosis review, write a separate adjudication protocol specifying the infection/SOFA reference standard, available clinical records, event-time tolerance, uncertain cases, reviewer disagreement procedure and assessment masked to model output where feasible. This packet does not establish inter-rater reliability; two actual assessors would be required to measure it.

## Statistical questions requiring a human methods reviewer

| Issue | Evidence supplied | Requested decision |
| --- | --- | --- |
| Train/calibration/test leakage | Source models/hash locks unchanged; demo selection one stay per person; no calibration/test person overlap | Verify splits and explicitly limit cross-resource/hospital independence claims. |
| Multiple measurements and censoring | Raw availability code, offset tests, pre-onset timelines, no future feature dependence | Check temporal alignment and whether censoring and the label grid select easy/hard cases. |
| Patient intervals | Exact binomial counts and separate recomputation; only 17 test cases | Assess uncertainty, hospital correlation and whether any stronger inference is justified. |
| Local calibration | 187 negative calibration people, fixed 10% target, strict crossing, no model refit | Verify order-statistic rank and discuss exchangeability limits. Do not interpret a nominal target as a transport guarantee. |
| Hourly metrics | 19,645 correlated test hours; positive prevalence 0.519% | Verify AUROC/AP/Brier and recommend patient-cluster uncertainty only if needed. |
| Multiplicity and exploration | 180 original plus 180 post-test amended rows; all models/variants retained | Keep exploratory designation. A favorable cell is not a prospectively selected winner. |
| Original study claims | 288 main and 660 follow-up rows audited; 48 anchors reproduced | Inspect manuscript framing, weak novelty, causal/clinical claims and scientific rationale beyond arithmetic. |
| Reproducibility | Code, tests, raw public inputs, 6 frozen models, manifests, notebook | Independently run the package and record actual results and deviations. |

## Manuscript recommendations from the AI-assisted audit

These are proposed edits for review, not human reviewer conclusions:

- Retain the study as an empirical analysis of transport, admission-level false alerts, alert burden and timing.
- Add the limited demo results as supplementary evidence with target mismatch and nonoverlap uncertainty disclosed.
- Report the original and chart-amended results together; mark the amendment post-test exploratory.
- Retain detection failures and all unit/model variants. Avoid claims of clinical effectiveness, superior prediction, diagnosis validation or guaranteed false-alert control under distribution shift.
- Preserve the distinction between any timely crossing and a timely **first** alert. Silencing effects on emitted counts cannot alone establish patient benefit.
- Resolve author list, affiliation, funding, conflicts, data-use/ethics wording and AI assistance with the actual authors and responsible institution. No declarations have been assumed or signed here.
- A Q1 editorial decision and a two–three month publication are not demonstrated by this review preparation.

## Clinician response form

Name and qualifications: ____________________

Affiliation: ____________________

Date and conflicts of interest: ____________________

Files and cases actually reviewed: ____________________

Label/target/onset judgement, with evidence: ____________________

Unit and availability judgement, with required changes: ____________________

Clinically defensible claims and claims to remove: ____________________

Decision (choose and explain): revise / suitable for the stated limited research scope / insufficient evidence: ____________________

Reviewer attestation: I performed the review described above; this form does not imply clinical deployment approval or institutional ethics approval.

Signature or verifiable written acknowledgement: ____________________

## Statistical response form

Name and methods qualifications: ____________________

Affiliation, date and conflicts: ____________________

Files/code actually examined or executed: ____________________

Reproducibility result and deviations: ____________________

Comments on selection, independence, uncertainty, multiplicity and estimands: ____________________

Required corrections and decision: ____________________

Signature or verifiable written acknowledgement: ____________________

## Completion record

| Milestone | Status | Evidence needed to close it |
| --- | --- | --- |
| External demo scoring | Complete | Supplied code and results |
| Automated numerical review | Complete | Supplied audit logs |
| Human clinical review | Pending | Actual completed clinician response |
| Human statistical review | Pending | Actual completed methods response |
| Matching clinical label/adjudication | Pending | Agreed standard and authorized supporting records |
| Verifiable independent cohort | Pending | Source institution/time/population and nonoverlap evidence |
| Manuscript integration | Pending human decisions | Revised text accurately reflecting accepted limits |

The project owner should provide an actual clinician/methods reviewer or return their completed forms. No reviewer has been contacted. If the owner authorizes communication to a named reviewer, identity and recipient details must be verified before sending. Credentialed datasets require the researcher's own approved access and data-use agreement; Colab access supplies compute, not data authorization or human judgement.
