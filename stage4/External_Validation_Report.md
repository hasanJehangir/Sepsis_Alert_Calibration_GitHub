# External cohort evaluation and review status

The frozen Challenge-trained models were evaluated on an open eICU demo cohort, with all results retained. **Detection was weak. This is supplementary external evidence, not verified independent-cohort clinical validation. Human review has not occurred.** Neither a clinical benefit nor a high-performing deployable sepsis system is supported.

## Completed work

Six original models were scored without refitting, feature redesign or changing the source thresholds. Two prespecified numeric-unit variants, three threshold conditions and five alert rules produced 180 comparisons in the initial run. A documented post-result measurement amendment produced another 180 comparisons on exactly the same cohort. Neither run replaces the other. CAPMI materials were not accessed or reused. The existing manuscript and locked Challenge results remain unchanged.

The original external protocol was locally locked before reading external outcome values; this is not public preregistration. The amended run was planned after initial test results were inspected and is exploratory. Both locks, input hashes, original outcomes, amendment rationale and code are supplied.

## Cohort and comparability

The source is the openly released [eICU-CRD Demo v2.0.1](https://physionet.org/content/eicu-crd-demo/2.0.1/), with benchmark labels from [YAIB](https://github.com/rvandewater/YAIB), pinned to commit `0d1d39a131a65f453aeb019828394396d6bfd171`. Dataset access and reuse are governed by ODbL 1.0. The public demo is intended to illustrate reproducible processing and does not substitute for validating on the full database.

The benchmark provides 896 eligible stay identifiers. An outcome-blind hash chose one stay per person (677 people), followed by the fixed source eligibility rules (656 people; 21 early/left-censored exclusions). Person hashes assigned 195 people to calibration (8 cases, 187 negatives) and 461 to test (17 cases, 444 negatives), with zero person overlap between those roles. There are 28,045 total scoring hours and 19,645 test hours. All 17 test cases have six positive pre-event scoring hours; hourly prevalence is 102/19,645 = 0.519%.

No record was reseeded or moved to obtain favorable prevalence or performance. Observation ends at the earlier of discharge, the published label grid endpoint and 168 hours. Adults are scored after six complete ICU hours and strictly before reconstructed onset for cases. Early-onset sepsis is outside this estimand. YAIB upstream exclusions, including observation adequacy and hospital selection, can bias the sample.

**Cross-resource hospital/patient independence cannot be verified from deidentified public identifiers.** Calibration and test people are disjoint within this demo, but their hospitals are not held out from one another. The raw checksum-verified release contains 186 hospital surrogate IDs, whereas its overview describes 20 hospitals. Every patient ID joins to the hospital table; this discrepancy remains unresolved. No verified clinical hospital count is claimed.

## Target and measurement differences

YAIB's modified `sep3_alt` target uses an antibiotic-based suspected-infection proxy and a SOFA-change window that differs from the Challenge definition. Imported positive labels span an event-centered ±6-hour window, rather than the Challenge's persistent shifted label. We reconstruct the benchmark event grid from the first positive hour +6 and retain only pre-event scores. Positive blocks were checked for continuity and width. These are operational benchmark labels, **not clinician-adjudicated diagnoses or an independently recalculated Sepsis-3 reference standard**.

Raw eICU measurements were rebuilt causally: no future filling; an event is first used after its complete hourly bin; laboratory corrections use the later result/revision offset. Periodic `sao2` is mapped to peripheral O2Sat, with arterial SaO2 coming separately from laboratory O2 saturation. Noninvasive and invasive blood pressures share source channels. These choices and offset assumptions require clinical review.

Challenge's printed Lactate/Magnesium units conflict with the usual scale of their released numeric values. Both the native-numeric mapping and a prespecified variant masking those two channels are reported. No conversion was selected by test performance. Missing channels are passed through the original training-fitted processing. The reduced HGB removes explicit observation flags/ages and ICU duration; it is not entirely free of missingness information.

The initial adapter omitted nursing-chart temperature and respiratory-chart FiO2. Amendment 01 adds explicit C/F temperatures (C wins a same-time duplicate) and explicitly labeled FiO2 fields, using the later event/entry offset. Directly observed scoring rows changed as follows; these are **measurement frequencies before forward filling**, not patient coverage:

| Channel | Initial | Amended exploratory |
| --- | --- | --- |
| Temp | 579/28,045 (2.1%) | 7025/28,045 (25.0%) |
| FiO2 | 343/28,045 (1.2%) | 3907/28,045 (13.9%) |

This is a substantive post-test data harmonization amendment. It does not make the amended cohort unseen or confirmatory.

## Patient-level results

The table below reports the original full HGB anchors, using native numeric units, for both sources and both runs. The local patient threshold targets a nominal 10% false-alert probability using maxima from 187 negative calibration people, a finite-sample order statistic and a strict `score > threshold` crossing. This target is not an external-shift guarantee and is not achieved exactly in every test cell. Source patient thresholds are carried over unchanged.

| Run | Frozen model | Threshold | False-alert patients: k/n; % (95% CI) | Any alert in 6 h: k/n; % (95% CI) | First alert in 6 h: k/n; % (95% CI) |
| --- | --- | --- | --- | --- | --- |
| Initial | A → demo | Source patient | 122/444; 27.5% (23.4–31.9) | 3/17; 17.6% (3.8–43.4) | 0/17; 0.0% (0.0–19.5) |
| Initial | A → demo | Local patient | 42/444; 9.5% (6.9–12.6) | 1/17; 5.9% (0.1–28.7) | 1/17; 5.9% (0.1–28.7) |
| Initial | B → demo | Source patient | 122/444; 27.5% (23.4–31.9) | 4/17; 23.5% (6.8–49.9) | 1/17; 5.9% (0.1–28.7) |
| Initial | B → demo | Local patient | 37/444; 8.3% (5.9–11.3) | 0/17; 0.0% (0.0–19.5) | 0/17; 0.0% (0.0–19.5) |
| Amended exploratory | A → demo | Source patient | 128/444; 28.8% (24.7–33.3) | 5/17; 29.4% (10.3–56.0) | 2/17; 11.8% (1.5–36.4) |
| Amended exploratory | A → demo | Local patient | 47/444; 10.6% (7.9–13.8) | 0/17; 0.0% (0.0–19.5) | 0/17; 0.0% (0.0–19.5) |
| Amended exploratory | B → demo | Source patient | 131/444; 29.5% (25.3–34.0) | 6/17; 35.3% (14.2–61.7) | 3/17; 17.6% (3.8–43.4) |
| Amended exploratory | B → demo | Local patient | 38/444; 8.6% (6.1–11.6) | 1/17; 5.9% (0.1–28.7) | 1/17; 5.9% (0.1–28.7) |

The initial full HGB models alerted 122/444 negative patients with either source threshold. In the amended run this increased to 128/444 and 131/444. Local calibration reduced those amended counts to 47/444 and 38/444, with any alert in the final six hours in 0/17 and 1/17 cases. These observations show a burden/detection trade-off; they do not establish effective sepsis detection. With 17 cases, one detected case is 5.9 percentage points. Zero successes still has an exact upper 95% limit of 19.5%.

![Full HGB external results with exact patient intervals](figures/external_hgb_results.png)

All six models and both input variants are also reported through discrimination measures. AP should be compared with the 0.00519 hourly prevalence. No hour-level confidence interval is supplied because repeated hours are correlated within patients.

| Run | Source | Model | AUROC native | AUROC masked | AP native | AP masked |
| --- | --- | --- | --- | --- | --- | --- |
| Initial | A | Logistic | 0.504 | 0.491 | 0.0050 | 0.0049 |
| Initial | A | HGB full | 0.566 | 0.551 | 0.0063 | 0.0061 |
| Initial | A | HGB reduced | 0.627 | 0.616 | 0.0099 | 0.0072 |
| Initial | B | Logistic | 0.456 | 0.453 | 0.0046 | 0.0045 |
| Initial | B | HGB full | 0.519 | 0.525 | 0.0051 | 0.0051 |
| Initial | B | HGB reduced | 0.596 | 0.600 | 0.0062 | 0.0065 |
| Amended exploratory | A | Logistic | 0.543 | 0.533 | 0.0055 | 0.0054 |
| Amended exploratory | A | HGB full | 0.586 | 0.581 | 0.0059 | 0.0058 |
| Amended exploratory | A | HGB reduced | 0.644 | 0.635 | 0.0084 | 0.0071 |
| Amended exploratory | B | Logistic | 0.476 | 0.476 | 0.0048 | 0.0047 |
| Amended exploratory | B | HGB full | 0.545 | 0.551 | 0.0055 | 0.0056 |
| Amended exploratory | B | HGB reduced | 0.602 | 0.604 | 0.0062 | 0.0064 |

The complete CSV retains all 360 policy comparisons, including source hourly thresholds, admission single alerts, four/six-hour silencing and the three-of-five rule. Do not choose a model, rule, unit variant or run using these test outcomes and then describe its score as confirmatory. Single alerts and silencing preserve admission-level false-alert and first-alert outcomes at a shared threshold while reducing emitted alerts. Their clinical acceptability is unreviewed.

Exact binomial intervals describe the selected patient counts. They do not adjust for hospital clustering, label error, selection bias, multiplicity or cross-resource overlap. Differences between runs are descriptive, not independent-sample treatment effects. There is no simulated clinical utility claim.

## Automated audit versus human review

The earlier numerical audit recomputed seven patient proportions and exact intervals in 288 Stage 2 and 660 Stage 3 rows, checked 1,254,335 scoring hours and verified 48 fixed hourly anchors. All 17 recorded checks passed. The external audit separately checked proportions/intervals, fixed-threshold policy invariants, person separation, pre-onset scoring, cohort identity across the two runs and frozen source/input hashes: all 27 recorded checks passed. Eight external adapter tests passed. These checks improve arithmetic and implementation confidence; **they are AI-assisted audits, not an independent human peer review**.

Review status:

| Requirement | Status |
| --- | --- |
| Public external scoring | Completed; weak results, limited demo |
| Verified institution/patient nonoverlap | Not established |
| Matching clinical target / adjudication | Not established |
| Clinician review | Pending; no reviewer has signed |
| Statistical human review | Pending; no reviewer has signed |
| Original numerical audit | Passed automated checks |
| Submission readiness | Not ready to claim independent clinical validation |

## Next actions for a defensible paper

Give `Human_Review_Packet.md`, this report, the unchanged manuscript and complete results to a critical-care/sepsis clinician and a statistician. Resolve target mapping, source units, chart-time assumptions, early-onset selection, institution independence and what constitutes an actionable first alert. Record their actual comments and decisions.

For stronger independent evidence, obtain authorized access to a genuinely separate institution/resource, such as HiRID or AmsterdamUMCdb. Credentialing and data-use agreements must be completed by the researcher. Fix mappings and target before examining that cohort's outcomes, then repeat the frozen transport and calibration evaluation with a new protocol. This cannot be replaced by connecting Colab alone.

The paper can report transport failure and alert burden cautiously; these results do not support a claim of model superiority, improved patient outcomes or clinical deployment. Publication, Q1 classification, zero cost and a two–three month publication timeline are not guaranteed by this evaluation.

## Reproducibility and attribution

The package includes public raw data, licenses, pinned benchmark inputs, six frozen models, original and amended protocols/locks, code, tests, complete external results and audit records. Both runs were repeated from an extracted package in isolated copies: all 18 numerical tables, 24 prediction vectors and eight feature/hour/label arrays matched exactly (50 comparisons). The verification record is supplied. `README_STAGE4.md` and the Colab notebook provide execution steps. The notebook is schema/code checked; a signed-in Colab session was not run here.

Dataset: Johnson A, Pollard T, Badawi O, Raffa J. eICU-CRD Demo v2.0.1 (2021), DOI [10.13026/4mxk-na84](https://doi.org/10.13026/4mxk-na84). Parent database: Pollard et al. Scientific Data (2018), DOI [10.1038/sdata.2018.178](https://doi.org/10.1038/sdata.2018.178).

Benchmark: van de Water et al. YAIB: Yet Another ICU Benchmark. ICLR 2024; [arXiv:2306.05109](https://arxiv.org/abs/2306.05109). Benchmark repository code is MIT; derived datasets are ODbL, not relicensed as MIT by this package.

Measurement documentation: [patient](https://eicu.mit.edu/eicutables/patient/), [lab](https://eicu.mit.edu/eicutables/lab/), [vitalPeriodic](https://eicu.mit.edu/eicutables/vitalperiodic/), [nurseCharting](https://eicu.mit.edu/eicutables/nursecharting/), [respiratoryCharting](https://eicu.mit.edu/eicutables/respiratorycharting/). Original target: [Challenge 2019](https://physionet.org/content/challenge-2019/1.0.0/). Access: [HiRID](https://physionet.org/content/hirid/1.1.1/), [AmsterdamUMCdb](https://github.com/AmsterdamUMC/AmsterdamUMCdb).
