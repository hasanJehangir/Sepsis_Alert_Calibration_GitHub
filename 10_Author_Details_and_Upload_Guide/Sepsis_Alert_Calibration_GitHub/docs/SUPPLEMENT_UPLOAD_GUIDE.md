# Saved sepsis outputs: upload and author-declaration guide

Prepared: 6 October 2026. Author: Hasan Jehangir. Email: hasanjehangir6@gmail.com.

Repository: https://github.com/hasanJehangir/Sepsis_Alert_Calibration_GitHub

## What you are receiving

These files supplement the source-only package already uploaded to GitHub.
They contain the archived fitted models, predictions, derived arrays, result
tables and data-derived figures. They are recovered study outputs, not outputs
from newly trained models or a new independent-cohort experiment.

- Seven saved `.joblib` models: six primary models and one historical pilot.
- Sixty-five CSV tables, including pilot, primary, follow-up, external and
  manuscript presentation tables. Duplicated presentation inputs are intentional.
- Thirteen PNG images and nine PDFs, including vector plots, the current
  manuscript, the supplement and historical drafts.
- Thirty-one `.npz` prediction archives, nine `.npy` arrays and 157 compressed
  cached arrays needed for the recorded numerical reproduction workflows.
- An author/contact patch, complete-package integrity manifest and this guide.

No raw clinical input tables are supplied in these supplement downloads. The
public-input acquisition scripts already in the repository obtain them when
needed. Preserve the database attribution and licenses recorded in
`LICENSES_AND_DATA.md` and `stage4/DATA_ATTRIBUTION.md`.

## Download all ten archives

| Archive | Contents |
| --- | --- |
| `01_Saved_Models.zip` | Six primary fitted models and historical pilot model |
| `02_Result_Tables.zip` | All 65 CSV result tables |
| `03_Figures_and_Manuscripts.zip` | All PNG/PDF figures, current article and supplement, historical drafts |
| `04_Predictions_and_Arrays_Part1.zip` | Prediction/array part 1 |
| `05_Predictions_and_Arrays_Part2.zip` | Prediction/array part 2 |
| `06_Predictions_and_Arrays_Part3.zip` | Prediction/array part 3 |
| `07_Predictions_and_Arrays_Part4.zip` | Prediction/array part 4 |
| `08_Predictions_and_Arrays_Part5.zip` | Prediction/array part 5 |
| `09_Predictions_and_Arrays_Part6.zip` | Prediction/array part 6 |
| `10_Author_Details_and_Upload_Guide.zip` | Updated email, repository link, declaration guidance, article source and integrity manifest |

Every archive is an ordinary ZIP that can be extracted independently. These
are not binary split volumes. Extract all ten into the SAME parent folder.
They merge into one `Sepsis_Alert_Calibration_GitHub` directory. Apply archive
10 last and allow it to replace the older README, contact metadata and article
source. Keep the existing source files already downloaded/uploaded.

## Upload while retaining folder paths

The most convenient option for these roughly 300 additional files is GitHub
Desktop. Clone your existing repository, open its local folder, and copy the
CONTENTS of the extracted `Sepsis_Alert_Calibration_GitHub` folder into that
checkout. Merge matching directories and replace the files in archive 10.
Review the changes, commit them and push to `main`. Do not create another
`Sepsis_Alert_Calibration_GitHub` folder inside the checkout.

For browser upload, each archive has fewer than 100 files, but extraction
alone does not guarantee correct paths in GitHub's browser uploader. Navigate
to the corresponding destination directory before adding its files. For
example, the six primary models belong in `stage2/results/`; the pilot model
belongs in `results/`. Do not flatten all extracted files into the root.
If your browser does not preserve dragged directory paths, use GitHub Desktop.

Do not upload the ZIPs alone as replacements for the extracted model and
prediction files: the scripts open the original paths, not archive files.

After uploading, check that these paths exist:

- `stage2/results/A_hgb_model.joblib`
- `stage2/results/B_hgb_model.joblib`
- `stage2/results/main_metrics.csv`
- `publication/figures/transport.pdf`
- `publication/Sepsis_Alert_Transport_Manuscript.pdf`
- `docs/SUPPLEMENT_UPLOAD_GUIDE.md`

If running locally, use Python 3.12 and the pinned dependencies. The initial
integrity check is:

```bash
python -m pip install -r requirements_complete.txt
python verify_repository.py
```

Missing raw clinical inputs are recorded as pending by this file check. That
does not mean the retained model/results supplement is missing. Follow-up
reproduction from the retained primary predictions is:

```bash
python reproduce.py --stage followup
```

See the root README for both external runs and the much slower full primary
training workflow. Run the integrity check before regenerating outputs, as
regeneration changes the bytes checked by the manifest.

## Where to get the two remaining declarations

### 1. Competing interests: completed by the author(s)

You supply this declaration. It is not an outside certificate. Use the target
journal's disclosure form or the ICMJE form if the journal accepts it:

https://www.icmje.org/disclosure-of-interest/

Each author should disclose relevant financial and non-financial relationships.
No external funding is already confirmed, but this alone does not establish
that there are no competing interests. Only if it is true after checking, use:

> The author declares no competing interests.

For multiple authors, each needs to complete the journal's required disclosure.
Doctors who provided feedback are not automatically coauthors. Their consent
to acknowledgement and any qualifying contributions must be documented.

Current package status: competing-interest statement remains pending. Nothing
has been submitted or signed on your behalf.

### 2. Ethics/review applicability: institutional route or applicable policy

First ask your former UET supervisor or the Office of Research, Innovation and
Commercialization to direct you to the responsible ethics body or policy.
The official UET page lists:

- Director office: diroric@uetpeshawar.edu.pk
- General research office: oric@uetpeshawar.edu.pk
- Telephone: +92-91-9222132
- Official source: https://www.uetpeshawar.edu.pk/oric/contactus.php

Being a UET graduate does not itself establish that UET has jurisdiction over
your independent project. Ask who has authority to determine whether this
specific secondary analysis requires review, is not subject to review under
the applicable policy, or can receive an exemption. Obtain the relevant written
determination or policy basis where applicable. A clinician's favorable
scientific review is not an ethics committee determination.

If UET cannot review an independent alumnus's project, ask the target journal
which documentation it accepts for a public, de-identified secondary analysis.
Do not invent an approval number or describe a source database's consent waiver
as approval of your own study. A new approval certificate is not necessarily
required for every such study; the applicable basis must be established.

Elsevier's policy requires an ethics statement and an explanation where
approval is not required or an exemption applies:

https://www.elsevier.com/about/policies-and-standards/research-ethics

### Draft ethics inquiry: send yourself after reviewing

To: diroric@uetpeshawar.edu.pk

Subject: Ethics-review applicability for secondary analysis of public de-identified datasets

Dear ORIC Team,

I am Hasan Jehangir, a BS in Data Science graduate of UET Peshawar, currently
conducting independent research. I have completed a retrospective computational
study titled "Admission-level false-alert calibration and warning timing in
cross-hospital sepsis prediction: a reproducible retrospective evaluation."
It uses only public, de-identified PhysioNet Challenge 2019 and eICU-CRD demo
records, together with publicly available YAIB-derived demo labels. There was
no participant recruitment, contact, intervention or access to identity keys.

Could you direct me to the responsible ethics committee or applicable policy
and advise whether this secondary analysis requires review, is outside the
scope of review, or is eligible for an exemption? If UET can make this
determination for an independent alumnus's project, please advise how to
obtain a written determination or policy reference. Otherwise, please advise
which route is appropriate.

I can provide the manuscript, protocol, dataset links and licensing information.
Dataset sources are:
https://physionet.org/content/challenge-2019/1.0.0/
https://physionet.org/content/eicu-crd-demo/2.0.1/

Regards,
Hasan Jehangir
hasanjehangir6@gmail.com

## What has and has not changed

The author email and public repository link have been added to the contact
metadata and manuscript. Funding remains "This research received no external
funding." Scientific findings, fitted models, predictions, numerical tables
and data-derived figure files are unchanged. The article PDF is recompiled
to include the confirmed contact information.

The original scientific locks and source input receipts are retained. The new
repository manifest describes the combined source-plus-supplement package.
The source-only manifest remains a historical record of the earlier upload.

This packaging check does not repeat model training, establish ethical
approval, conduct human review or guarantee journal acceptance. The article
still needs truthful competing-interest and ethics statements, final author
contributions and final author review before submission.
