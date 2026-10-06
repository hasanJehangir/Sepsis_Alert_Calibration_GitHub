# Reproduce the exploratory alert-policy follow-up

The standalone `Sepsis_Stage3_Research_Package.zip` includes the exact frozen predictions, scoring hours, calibration/test roles and previously computed locked results. It contains no new raw patient cohort, no CAPMI material and no full-text copies of third-party articles. The earlier Stage 2 package remains the separate source for raw-data preparation and fitted models.

## Run locally

Use Python 3.12 in a fresh environment, unzip the package and change into `Sepsis_Alert_Calibration`:

```bash
python -m pip install -r requirements.txt
python -m pytest -q stage3/tests
python stage3/run_followup.py
python stage3/report_followup.py
```

The runner verifies the original input hashes before computing. Successful completion gives 660 policy-level rows and 144 paired endpoint comparisons in `stage3/results`. The output completion timestamp changes when you rerun; this does not create a new independent validation. The six checks test rule behavior, and actual-data assertions verify first-crossing invariance and matching with the original hourly anchors. Internet is needed only to install dependencies; exact input files are already packaged.

`stage3/build_manuscript.py` recreates the LaTeX source and tables from retained locked/follow-up CSV files. Building the PDF additionally requires a LaTeX installation with `pdflatex`. Run the builder from the project root, then run `pdflatex` twice on `Sepsis_Calibration_Manuscript_Draft.tex` from `stage3/manuscript`. The supplied PDF is already compiled and visually checked.

## Run in Google Colab

Open the supplied `Sepsis_Stage3_Colab.ipynb` using Colab's **File > Upload notebook**. Run its cells in order. Upload the supplied standalone ZIP when prompted. A CPU runtime is sufficient because this follow-up evaluates frozen predictions and does not train models. The notebook validates package hashes, installs dependencies, checks the rules, runs the comparison and offers the result files for download.

The notebook has been structurally validated and all Python code cells compile. It has not been executed in a signed-in Colab session. Colab's Python version, package availability or interface may differ; the cell commands report actual failures rather than silently proceeding. You do not need to connect Google Drive to reproduce these frozen-input results. Keep a copy of the ZIP and notebook before starting.

## Package provenance

`PACKAGE_MANIFEST.json` records included-file sizes and SHA-256 digests. `stage3/followup_lock.json` records the protocol/config/input digests established before the follow-up computations. Its creation followed inspection of Stage 2 test outcomes, so it is an exploratory local lock, not a prospective preregistration. `stage3/results/completed.json` records the original run signature, versions and checks. The archive includes the unchanged Stage 2 main metrics, cohort and completion metadata required for anchor checks.

Do not alter a frozen input to bypass a failed hash check. Diagnose whether the wrong package was uploaded or a file was edited. Reproduction of a previous result is distinct from validation on a new independent cohort.
