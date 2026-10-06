# Patient-level false-alert calibration for cross-hospital sepsis warning

**Research development brief for Hasan Jehangir · 29 September 2026**

**Status:** independent code and a real 3,000-record development pilot are complete. This is not a completed manuscript, a validated clinical system, or an accepted/published paper. No CAPMI code, results, manuscript, or checkpoints were used.

## The project in plain language

A model may appear to make few false predictions per hour while still alerting on many patients during a long admission. This project calibrates a threshold using the highest predicted risk within each nonseptic patient's observed stay. It asks whether that threshold controls the patient-level alert burden, how it changes after moving to another hospital, and how much separate local calibration data is needed.

The attraction is practical: public data, modest CPU requirements, a clearly measurable workload outcome, and reusable analysis code. The difficulty is scientific: the broad idea is established, and a lower false-alert rate can simply reflect a higher threshold that also misses sepsis. The study must measure those trade-offs and establish a narrower contribution.

## Candidate gap and closest prior work

**Candidate question:** Under cross-hospital transfer, how do calibration unit, local sample size, and observation duration jointly affect nonseptic patient false-alert probability and the timing of sepsis warnings?

This is an inference from the work reviewed, not proof that nobody has studied the combination. The current code tests only one transfer direction and one local calibration sample. It does not yet establish the proposed gap or satisfy it.

| Prior work | What is already covered | What this study would have to add |
| --- | --- | --- |
| Gupta et al., *SepsisAI*, PLOS Digital Health, 2024, [DOI](https://doi.org/10.1371/journal.pdig.0000569) | LSTM sepsis prediction with warning/alert logic designed to reduce false alarms using the same public dataset. | A calibration-unit and hospital-transfer study with explicit patient error targets, small local calibration budgets, and comparable timing/workload endpoints. Do not claim that false-alarm reduction itself is new. |
| Do et al., JMIR, 2026, [DOI](https://doi.org/10.2196/72083) | Evaluation strategy, observation length, and onset distribution materially change sepsis performance estimates; this is particularly close prior work. | A prespecified source-versus-local calibration experiment, with finite-sample patient thresholds and local-sample variability. Do not present the hour-versus-stay metric mismatch as a discovery. |
| Shashikumar et al., COMPOSER, npj Digital Medicine, 2021, [DOI](https://doi.org/10.1038/s41746-021-00504-6) | Sepsis prediction with conformal reasoning about unfamiliar inputs and abstention. | Evaluate patient-maximum alert calibration and its transport limits; do not claim to introduce conformal methods to sepsis. |
| You et al., *Missingness-Aware Conformal Prediction Under Cross-Hospital Distribution Shift*, 2026, [arXiv](https://arxiv.org/abs/2609.30781) | A recent preprint examining missingness groups and cross-hospital conformal behavior for mortality. | A longitudinal sepsis alert target, with admission-level burden and timing. This preprint is not peer-reviewed evidence of clinical effectiveness. |
| Angelopoulos and Bates, *A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification*, [arXiv](https://arxiv.org/abs/2107.07511) | Standard conformal rank calibration and the importance of exchangeability. | Application-specific evidence and an honest transport audit, not a new quantile formula. |

The intended paper is a methodological evaluation of alarm calibration. A generic classifier with slightly better AUROC is unlikely to distinguish it. Before submission, the literature review must extend to patient-level risk control, sequential alarm policies, nonparametric tolerance limits, and calibration under shift. No exhaustive review or “first-ever” claim is warranted now.

## What was actually done

The source is the public [PhysioNet/CinC Challenge 2019, version 1.0.0](https://physionet.org/content/challenge-2019/1.0.0/), containing 40,336 subject records from two released hospital datasets. Dataset attribution and CC BY 4.0 terms are in `DATA_NOTICE.md`.

Exactly 1,500 filenames per hospital were selected by a fixed hash before label inspection. Of the 3,000 records, 2,936 met the cohort rules. Sixty-one early/left-censored sepsis records and three nonadult records were excluded. The pilot therefore concerns later-onset adult ICU sepsis under this protocol, not every ICU admission.

| Hospital and role | Eligible patients | Septic patients |
| --- | ---: | ---: |
| A training | 883 | 71 |
| A calibration | 295 | 14 |
| A evaluation | 288 | 14 |
| B calibration | 294 | 10 |
| B evaluation | 1,176 | 40 |

A fixed histogram gradient boosting classifier was fit on A training data. Features use information available by each hour. A, B, fitting, calibration, and evaluation roles are disjoint at the released subject-file level. The remaining **37,336 records were not opened**. The raw data, model, hourly predictions, exclusions, split manifest, and numerical results are included in the project archive.

The dataset's positive labels already start six hours before onset. The implementation reconstructs onset once, removes post-onset hours, and distinguishes any crossing in the six-hour warning window from a first alert in that window. This distinction is tested in code and matters greatly to the interpretation.

## Actual hospital-B pilot findings

These are measured development results from 1,136 nonseptic and 40 septic patients. All policies use the same hospital-A model.

| Calibration policy | Nonseptic patients with any alert | 95% exact interval | Any crossing in the six-hour window | First alert in that window |
| --- | ---: | ---: | ---: | ---: |
| Source hourly | 490/1,136 = **43.1%** | 40.2–46.1% | 30/40 = **75.0%** | 2/40 = **5.0%** |
| Source patient | 151/1,136 = **13.3%** | 11.4–15.4% | 23/40 = **57.5%** | 2/40 = **5.0%** |
| Local patient | 148/1,136 = **13.0%** | 11.1–15.1% | 23/40 = **57.5%** | 2/40 = **5.0%** |

The 95% intervals for six-hour-window sensitivity are 58.8–87.3% for source hourly and 40.9–73.0% for either patient policy. The small number of sepsis cases makes estimates imprecise. These are individual-proportion intervals, not intervals for paired policy differences.

![Hospital-B pilot trade-offs](results/pilot_comparison.png)

On the smaller A evaluation cohort, the false-alert rate changed from 43.4% (119/274) to 12.8% (35/274), while window detection changed from 9/14 to 7/14. Neither policy produced a first alert in the intended window for any of those 14 cases. Full metrics are in `results/pilot_results.json`.

**What the results support:** calibration unit strongly changes measured patient alarm burden for this development model. **What they do not support:** improved discrimination, a clinically effective warning system, reliable 10% error control after hospital transfer, or a clear benefit of local recalibration. Local calibration changes the false-alert count by only three patients here.

The model's early threshold crossings explain why “any crossing in the warning window” and “first alert in the warning window” disagree. An alert earlier than six hours is outside our target window; it is not automatically clinically useless. A clinically justified alert policy and timing definition require further work. Raising the threshold reduces false alerts but also reduces detections, so the headline decrease cannot be presented without the sensitivity trade-off.

## Why a 10% target can yield 13% observed error

The source hourly threshold targets a different event from a patient-maximum threshold. A 10% hourly false-positive rate does not imply a 10% chance of at least one alert over an admission.

The patient order-statistic guarantee is marginal over exchangeable calibration and test records. It is not a guarantee for every realized calibration sample, and it is not valid under arbitrary hospital shift. Fixed-horizon policies also require matching calibration/test observation definitions. Thus neither the observed excess nor its binomial interval should be interpreted as proof for or against a universal conformal guarantee.

## The next experiments required for a paper

1. Freeze the confirmatory plan before opening reserved test records; retain the entire pilot as development data.
2. Train a logistic baseline and a tree model; evaluate A-to-B and B-to-A transfer with source-site controls.
3. Compare patient calibration against hourly calibration and a simple empirical patient-maximum quantile, so standard rank correction is not misrepresented as an algorithmic innovation.
4. Use local calibration budgets of 100, 250, and 500 completed admissions across 20 fixed samples. Separate sampling variability from test uncertainty.
5. Compare natural-duration observations with consistent 24-, 48-, and 72-hour policies. Report alert timing, sensitivity, and patient burden together; include calibrated operating-point comparisons.
6. Audit onset exclusions, censoring, duplicates, and measurement-process features. Quantify paired policy differences using patient-level resampling.
7. Reassess the contribution against the closest papers. A negative or null adaptation result must remain visible. If the contribution is too weak, redirect the research before drafting an overstated paper.

The full experiment runner and those confirmatory results are not included yet. The current notebook reproduces the pilot only. A practical working target is roughly two to three weeks for this next research stage and a draft, conditional on results and review; that is a work estimate, not a journal publication promise.

## Free publication and the two-to-three-month requirement

An appropriate journal cannot be selected solely by fast first-decision statistics. A first decision may be a desk rejection; acceptance and online publication are separate milestones.

**Computer Methods and Programs in Biomedicine** is a possible scope candidate for a sufficiently developed methods study. Its [official insights page](https://www.sciencedirect.com/journal/computer-methods-and-programs-in-biomedicine/about/insights) lists a subscription route without an author publication fee. That is not free open access. The indexed publisher timing available during this research was approximately 98 days to a decision after review and 163 days to acceptance, so it does not support a reliable two-to-three-month publication promise. Access to the full metrics page was intermittent; these timing numbers need a fresh check at submission.

This journal's current Q1 status has **not** been verified against a specified category, year, and ranking database in this project. Do not treat it as a confirmed match for every requirement. Also distinguish it from *Computer Methods and Programs in Biomedicine Update*, a separate journal. A final journal shortlist remains open until contribution, journal quartile, fees, and realistic timing can all be assessed together.

No paper has been submitted. Nothing in the pilot establishes likely acceptance. The project can be prepared quickly; a free Q1 acceptance and actual publication within two to three months cannot responsibly be guaranteed.

## Reproducibility and current files

The code ran successfully on Python 3.12 with pinned CPU dependencies. Six tests passed, covering causal features, rank behavior, ties, endpoint definitions, pilot isolation, and label shifting/truncation. After a temporary runtime reset, the restored pipeline reproduced every earlier threshold and event count exactly. That is a reproducibility check on the same sample, not independent validation. The current protocol was restored after results were known and is explicitly not a prospective preregistration.

- `Sepsis_Alert_Project.ipynb`: self-contained Colab pilot workflow; CPU runtime, no Drive connection needed.
- `Sepsis_Alert_Project.zip`: source code, protocol, tests, fixed split manifest, public pilot data, model, measured results, and figure.
- `README.md`: local execution and output descriptions.

All values in this brief are derived from the accompanying measured pilot outputs. This report makes no clinical-use claim and does not replace the full research study.
