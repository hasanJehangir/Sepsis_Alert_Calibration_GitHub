# Literature and novelty audit — 29 September 2026

This was a targeted literature search and comparison, not a systematic review. It identifies substantial overlap and does not establish that the proposed combination has never been studied. Search phrases included sepsis/conformal/false alarms, patient-level/conformal/alert, and sepsis/calibration/hospital. Retrieval quality varied; primary papers were preferred over generic search snippets.

## Closest evidence

| Primary source | Existing contribution | Implication for this project |
| --- | --- | --- |
| Shashikumar et al. (2021), COMPOSER, [doi:10.1038/s41746-021-00504-6](https://doi.org/10.1038/s41746-021-00504-6) | Sepsis prediction with conformal reasoning about unfamiliar inputs and abstention. | Conformal sepsis prediction and generalization-aware false-alarm reduction are established. |
| Moor et al. (2023), *Predicting sepsis using deep learning across international sites*, [doi:10.1016/j.eclinm.2023.102124](https://doi.org/10.1016/j.eclinm.2023.102124) | International external validation, patient-focused single-alert evaluation, and adaptation using a small target-site subset. Full text examined. | Neither hospital transfer, first-alert timing, nor small-sample adaptation is novel by itself. Their model fine-tuning differs from our frozen-model threshold-only budget experiment, but that distinction alone may be insufficient for a paper. |
| Gupta et al. (2024), SepsisAI, [doi:10.1371/journal.pdig.0000569](https://doi.org/10.1371/journal.pdig.0000569) | Sepsis warning/alert logic and false-alarm reduction on the PhysioNet Challenge data. | A new classifier plus reduced false alarms is a crowded claim; a fair protocol-aligned comparison is needed. |
| *Time-series deep learning and conformal prediction for improved sepsis diagnosis in primarily Non-ICU hospitalized patients* (2025), [doi:10.1016/j.compbiomed.2025.110497](https://doi.org/10.1016/j.compbiomed.2025.110497), [PubMed](https://pubmed.ncbi.nlm.nih.gov/40450820/) | Time-series prediction combined with conformal prediction and external validation, with reported false-alarm reductions. | This is another close precedent. The published abstract and indexed methods were available; direct full-text retrieval failed in this session. No claim that all its experiments have been ruled out. |
| Do et al. (2026), *The Impact of Evaluation Strategy on Sepsis Prediction Model Performance Metrics in Intensive Care Data*, [doi:10.2196/72083](https://doi.org/10.2196/72083) | Demonstrates effects of evaluation strategy, observation duration, and onset distribution; also evaluates hourly alerts, silencing, and calibration. Full text examined. | Hour-versus-patient metric differences and length-of-observation effects cannot be sold as a discovery. Our contribution would need to be the controlled threshold-transport and calibration-budget audit. |
| You et al. (2026 preprint), [arXiv:2609.30781](https://arxiv.org/abs/2609.30781) | Missingness-aware conformal calibration under cross-hospital mortality-prediction shift. | Local/group calibration and the failure of pooled metrics to describe individual hospitals are also active topics. Not peer-reviewed clinical evidence. |

## What remains a candidate contribution

A reproducible **frozen-model calibration transport audit** that separates:

- the calibration unit (hour versus whole observed admission);
- the standard finite-sample rank correction versus an ordinary empirical patient quantile;
- two hospital-transfer directions and explicit observation-process features;
- completed-admission calibration budgets of 100/250/500 across fixed repeated samples;
- false-alert probability, any crossing in the warning window, and the first alert in that window;
- natural-duration versus identically capped calibration and test trajectories.

This is a candidate empirical contribution. The quantile formula and its exchangeability requirement are standard. Without clear findings and stronger comparison to prior alert-policy work, the contribution may be too incremental for a Q1 journal. The present study has only two released historical hospitals and no prospective clinical evaluation.

## Claims to avoid

Do not claim a new conformal algorithm, the first sepsis uncertainty model, the first cross-hospital evaluation, guaranteed 10% error after arbitrary shift, superior clinical outcomes, or an accepted paper. Do not compare our percentages directly with publications using different outcome windows, prevalence balancing, alert suppression, or case selection. Do not claim the gap has been proved absent merely because a search found no exact phrase match.

## Decision rule

Complete the locked experiment and inspect every model and transfer direction. If improvements consist only of raising a threshold and sacrificing detections, frame the output as a calibration/workload trade-off rather than an improved prediction algorithm. If transport and local-budget findings are unstable or timing remains weak, recommend further methodology or a different question before manuscript submission.
