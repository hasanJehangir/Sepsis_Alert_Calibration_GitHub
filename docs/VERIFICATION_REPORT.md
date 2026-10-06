# Combined package verification - 6 October 2026

- Original Stage 3 and Stage 4 frozen-input and package hashes: 196 checks,
  all matched after public input restoration from the original Stage 4 archive.
- Original pilot, primary, follow-up and external test suites: **28 passed**.
- Follow-up rerun: all 660 comparisons recomputed. Four retained output tables
  matched exactly, including paired differences and invariance checks.
- External rerun: both initial and amended evaluations reproduced exactly.
  The wrapper checked 18 output tables, 24 prediction vectors and 8 feature/time/
  label arrays against saved outputs. The external adapter's 8 tests also passed
  inside the reproduction copy.
- Manuscript presentation/numerical audit: **58 checks passed** after compilation.
- Article and supplement compiled successfully with resolved references and
  no fatal, undefined-reference or overfull-box errors.
- Updated article title/education page and declaration pages were rendered and
  visually checked. No clipping or overlap was observed.
- Combined Colab notebook schema validated; all cell code syntax parsed. It was
  not executed in a signed-in Colab session.
- External input acquisition helper tested by restoring the receipt-matched
  files from the original Stage 4 archive. Live remote downloads were not
  repeated during assembly.
- Full primary model training was not repeated during this packaging task.
  The unchanged training source, model artifacts, configurations, manifests,
  locks and saved outputs are supplied with a from-raw reproduction command.

The package verifies computational reproduction, not clinician adjudication,
ethics approval, clinical utility, independent statistical peer review or journal
acceptance. The author's positive clinician/statistical feedback is separately
reported as such.
