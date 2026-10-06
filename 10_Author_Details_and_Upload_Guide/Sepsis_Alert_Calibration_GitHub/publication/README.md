# Publication manuscript and LaTeX package

Main source: `Sepsis_Alert_Transport_Manuscript.tex`.

Supplement source: `Supplementary_Material.tex`.

The main article contains a structured abstract, introduction with a focused related-work subsection, methods, results, discussion, expanded conclusion, declarations, four editable tables, three data-derived figures and 21 authenticated references. The supplement adds seven tables, one study-flow figure, detailed methods and mapping audits. All plotted points and generated numerical tables use the retained CSV results; no model was retrained for manuscript preparation.

## Compile

Upload the complete ZIP contents to Overleaf. Choose `Sepsis_Alert_Transport_Manuscript.tex` as the main document and pdfLaTeX as the compiler. For the supplement, change the main document to `Supplementary_Material.tex`. The official Elsevier `elsarticle` class and numerical bibliography style are included, together with their source and license notices.

Locally:

```bash
pdflatex Sepsis_Alert_Transport_Manuscript.tex
bibtex Sepsis_Alert_Transport_Manuscript
pdflatex Sepsis_Alert_Transport_Manuscript.tex
pdflatex Sepsis_Alert_Transport_Manuscript.tex

pdflatex Supplementary_Material.tex
bibtex Supplementary_Material
pdflatex Supplementary_Material.tex
pdflatex Supplementary_Material.tex
```

To regenerate numerical tables and scientific figures from the supplied result CSVs, run `python3 build_assets.py` with pandas, numpy and matplotlib installed. `audit_manuscript.py` additionally uses scipy. `requirements_presentation.txt` records versions used for this presentation build; they are distinct from the retained original model-training environment.

## Scientific scope

This is an evaluation of admission-level false-alert calibration and warning-policy trade-offs, with a limited external public-demo check. It does not claim a novel conformal algorithm, verified hospital-independent clinical validation, prospective benefit, or reproduction/superiority of another named clinical system. The original external run and the post-test chart-mapping amendment are both reported.

This publication subdirectory regenerates presentation assets. The combined repository includes the complete original analysis source, frozen models, predictions, raw-input receipts and protocol locks. Raw clinical inputs are acquired separately using the root download scripts. See the root README for reproduction commands. The package's `result_provenance.json` records hashes of the exact CSV inputs used here. No CAPMI code, data, results, models or manuscript was used.

## Author details to finish before submission

The scientific text and LaTeX have been finalized around the available evidence. The following information cannot be supplied authentically from the current record and is deliberately flagged in the article:

1. Final author list and contributions. Corresponding email is completed as hasanjehangir6@gmail.com. The author is displayed as an independent researcher; his confirmed BS in Data Science at UET Peshawar is stated as education.
2. The responsible institution's ethics/consent determination, if applicable to this public-data analysis. No approval or exemption has been invented.
3. Competing-interest declarations from each author. Funding is completed as "This research received no external funding," based on the author's confirmation on 6 October 2026.
4. The public source repository is https://github.com/hasanJehangir/Sepsis_Alert_Calibration_GitHub. Upload the frozen-output supplement before claiming that this repository contains the complete retained outputs. An archived release DOI remains optional and has not been invented.
5. Human author review of the complete text, code and results, followed by the journal's required AI-assistance disclosure. The package truthfully documents assistance without asserting that this final version has already been reviewed by the author.

The user reports positive review by Dr. Sohaib Ali and Dr. Hasnain Ali Shah and reports statistical review with no issues. This feedback is accepted as author-reported. The record does not contain their itemized comments, qualifications, review dates, statistical responsibilities or explicit acknowledgement-name permissions. The main article uses an anonymous feedback statement; the supplement records the reported names and limited scope. Do not add reviewers as coauthors solely because they approved the project. Confirm whether their names should appear in the submitted supplement/acknowledgements, and document eligible contributions accurately.

## Target and length

Recommended first target: **Computer Methods and Programs in Biomedicine**, using the **fee-free subscription route**. See `Journal_Recommendation.md` for official sources, ranking year, realistic timing and editorial limitations. See `Word_Count_Report.md` for section-level counts and their convention. The supplemental literature comparison is contextual, not a systematic review.

## References and figure files

`references.bib` supplies numbered in-text citations. `Reference_Verification.json` records verified DOI/title/year metadata and primary-source locations. Figures are available as embedded-font vector PDFs and 220 dpi PNG previews. Data charts are generated from observed results, not illustrative or synthetic numerical examples.

`audit_manuscript.py` checks denominators, counts, exact binomial intervals, key claims, citations and preserved result identities. Its report is `Manuscript_Audit.json`. Visual PDF review is documented separately in `PDF_QA_Report.md`.
