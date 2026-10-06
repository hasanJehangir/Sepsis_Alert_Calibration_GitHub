# Submission readiness and the next research step

Prepared 30 September 2026. The computational study and exploratory follow-up are complete. The manuscript is a research draft for human review, not a submitted or accepted paper. CAPMI is excluded.

## Completed deliverables

- Reserved cohort: 36,658 eligible admissions; pilot records excluded; six independently fitted source/model combinations.
- Locked calibration/transport study: natural-duration and capped observation, empirical-quantile comparators, local calibration budgets, exact patient intervals and paired comparisons.
- Exploratory follow-up: 660 policy-level rows, 144 paired endpoint comparisons, five alert rules, source/local nominal targets of 5%, 10% and 20%.
- Implementation verification: 14 earlier checks, six additional checks, direct-crossing anchor audit and actual-data invariance assertions passed.
- Journal-neutral manuscript PDF and editable LaTeX source, six data-derived tables and three manuscript figures.
- Standalone reproduction package containing exact frozen predictions and required metadata. It does not require CAPMI or any credentialed dataset.

## What the findings support

The paper evaluates asymmetric transport of admission-level thresholds and distinguishes patients receiving alerts from repeated emissions and first-warning timing. Four-hour silencing reduced full-feature boosting nonseptic emissions by 68.3% and 57.5% in the two transfer directions, preserving the first crossing. This does not mean 68.3% or 57.5% fewer patients received alerts. Three-of-five aggregation did not show a consistent first-window advantage at the matched local target; both paired intervals included zero, and recurrent emissions increased.

Do not describe this as a new conformal algorithm, a clinically validated warning system, or a reproduction of the published SepsisAI/COMPOSER models. Earlier warnings may have clinical value; the six-hour first-warning endpoint does not establish their utility.

## Remaining work, in priority order

| Step | Concrete action | Completion criterion |
| --- | --- | --- |
| Independent cohort | Obtain authorized, de-identified data from hospitals/people not overlapping the challenge resource. Audit overlap before calling it external. | Access and provenance verified; hospital/patient overlap assessment documented. |
| External specification | Harmonize variables, units, hourly aggregation, sepsis/onset definition and censoring. Freeze extraction and scoring rules before examining outcomes. | Written protocol and input/schema checks reviewed; no use of outcome information in feature generation. |
| Frozen-model evaluation | Evaluate the preserved source models without refitting as the transfer test. If local calibration is feasible, split a separate completed-admission calibration pool and keep evaluation admissions disjoint. | Actual results with admission exposure, emissions and timing, including unfavorable findings. |
| Scientific review | Have a sepsis/critical-care collaborator inspect label definitions, warning windows and clinical interpretation; perform a focused comparison with the closest evaluation papers. | Documented methods review and a defensible, specific contribution statement. |
| Author verification | Confirm authors, affiliations, contributions, institution-specific ethics determination, funding, conflicts and AI-use disclosure. | Every eventual author verifies the statements and takes responsibility for the work. |
| Journal selection | Confirm ranking system, subject category and year; recheck fees, scope, article type and full submission-to-publication timing. | Evidence that matches the exact journal and route; no reliance on first-decision speed as acceptance speed. |
| Final submission package | Apply the chosen journal's current format; establish a shareable code/results archive; complete cover letter and declarations. | Reviewed, complete submission files. |

The manuscript could eventually be submitted without an extra cohort if a suitable editor finds its evaluation contribution sufficient. That is an editorial possibility, not evidence that the current draft will meet a Q1 journal's novelty requirements. Independent validation is the highest-value next research step; rerunning the same examined test set cannot create it.

## What to provide next

Provide the approved cohort's name/source and a de-identified schema or public documentation first. Do not send passwords, access tokens, identifying patient records or data your agreement does not allow to be shared. If processing must remain in your authorized Colab/account environment, the extraction and validation code can be designed to run there and export only permitted aggregate results.

No external cohort was accessed during this work. No ethics approval, author declaration, manuscript submission or journal acceptance has been invented.
